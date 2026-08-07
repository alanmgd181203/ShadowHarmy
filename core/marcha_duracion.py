"""Marcha personalizada por duración — calibra umbral por par para ~T días.

Una de las dos marchas operativas (junto a asalto): el Monarca escribe T;
cada base del lote ajusta umbral para que el engorde dure ~T.
Reajuste vivo si adelanta/atrasa.
Persiste: data/marcha_umbrales_custom.json
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

import core.config as config
from core import kaiser_sesgo_index as ksi
from core.kaiser_samples import load_samples
from core.manto_frecuencia import EDGE_MANTO, PLAZOS_S, fees_be_activo

REUSO_CALIBRACION_S = 3600.0  # <1h reusa si mismos días/equity


def _ruta_base() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ruta_umbrales() -> str:
    return os.path.join(_ruta_base(), "data", "marcha_umbrales_custom.json")


def cargar_umbrales() -> dict[str, Any]:
    ruta = _ruta_umbrales()
    if not os.path.exists(ruta):
        return {"duracion_dias": None, "equity_usd": None, "calibrado_ts": 0, "por_base": {}}
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"duracion_dias": None, "equity_usd": None, "calibrado_ts": 0, "por_base": {}}
        data.setdefault("por_base", {})
        return data
    except (json.JSONDecodeError, OSError, TypeError):
        return {"duracion_dias": None, "equity_usd": None, "calibrado_ts": 0, "por_base": {}}


def guardar_umbrales(payload: dict[str, Any]) -> dict[str, Any]:
    ruta = _ruta_umbrales()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    out = dict(payload)
    out["ts"] = time.time()
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    if os.path.exists(ruta):
        os.remove(ruta)
    os.rename(tmp, ruta)
    return out


def ops_por_hora_umbral(
    base: str,
    umbral_pct: float,
    *,
    ahora: float | None = None,
) -> float | None:
    """Tasa horaria de muestras cuyo exceso vs cero ≥ umbral_pct."""
    bu = (base or "").upper()
    ahora = ahora if ahora is not None else time.time()
    segs = PLAZOS_S["corto"]
    samples = load_samples(bu, EDGE_MANTO, since_ts=ahora - segs)
    min_n = int(getattr(config, "MANTO_FREQ_MIN_MUESTRAS", 20) or 20)
    if len(samples) < min_n:
        return None
    cero_info = ksi.cero_estructural_manto(bu)
    cero = cero_info.get("cero_pct") if cero_info.get("ok") else None
    above = 0
    u = max(0.0, float(umbral_pct))
    for s in samples:
        if ksi.usar_cero_en_manto() and cero is not None:
            signed = float(s.get("signed_pct") if s.get("signed_pct") is not None else s.get("abs_pct") or 0)
            exceso = abs(ksi.exceso_vs_cero(signed, cero))
        else:
            exceso = float(s.get("abs_pct") or 0)
        if exceso + 1e-15 >= u:
            above += 1
    horas = segs / 3600.0
    if horas <= 0:
        return None
    return round(above / horas, 4)


def eta_con_umbral(
    base: str,
    meta_usd: float,
    umbral_pct: float,
    *,
    mordida_usd: float | None = None,
    ahora: float | None = None,
) -> dict[str, Any]:
    if mordida_usd is None:
        mordida_usd = float(getattr(config, "MANTO_FREQ_MORDIDA_USD", 5.0) or 5.0)
    mordida = max(float(mordida_usd), 1.0)
    meta = max(float(meta_usd), 0.0)
    bocados = meta / mordida if meta > 0 else 0.0
    rate = ops_por_hora_umbral(base, umbral_pct, ahora=ahora)
    out: dict[str, Any] = {
        "base": (base or "").upper(),
        "umbral_pct": round(float(umbral_pct), 6),
        "meta_usd": round(meta, 4),
        "mordida_usd": round(mordida, 4),
        "bocados_est": round(bocados, 2),
        "ops_por_hora": rate,
        "eta_h": None,
        "ok": False,
        "motivo": "ok",
    }
    if rate is None or rate <= 0:
        out["motivo"] = "sin_tasa" if rate is None else "tasa_cero"
        return out
    if bocados <= 0:
        out["ok"] = True
        out["eta_h"] = 0.0
        out["motivo"] = "meta_cero"
        return out
    out["eta_h"] = round(bocados / rate, 2)
    out["ok"] = True
    return out


def calibrar_umbral_para_eta(
    base: str,
    meta_usd: float,
    eta_h_target: float,
    *,
    ahora: float | None = None,
) -> dict[str, Any]:
    """Busca umbral tal que ETA ≈ eta_h_target (binario entre ~0 y ~2×fees)."""
    fees = fees_be_activo(base)
    lo = 0.0
    hi = max(fees * 2.0, 0.05)
    target = max(float(eta_h_target), 0.01)
    best_u = fees * 0.5
    best_eta = None
    for _ in range(18):
        mid = (lo + hi) / 2.0
        et = eta_con_umbral(base, meta_usd, mid, ahora=ahora)
        eta = et.get("eta_h")
        if eta is None:
            # sin tasa → umbral más bajo (más ops)
            hi = mid
            continue
        best_u = mid
        best_eta = float(eta)
        if eta > target * 1.05:
            hi = mid  # demasiado lento → bajar umbral
        elif eta < target * 0.95:
            lo = mid  # demasiado rápido → subir umbral
        else:
            break
    return {
        "base": (base or "").upper(),
        "umbral_pct": round(best_u, 6),
        "eta_h_est": best_eta,
        "eta_h_target": round(target, 2),
        "fees_be_pct": round(fees, 6),
        "ok": best_eta is not None,
    }


def reajustar_umbral(
    base: str,
    *,
    progreso_frac: float | None = None,
    tiempo_frac: float | None = None,
    umbral_actual: float | None = None,
) -> float:
    """
    Atrasado (progreso < tiempo) → bajar umbral.
    Adelantado (progreso > tiempo) → subir umbral.
    Sin fracciones → deja umbral actual.
    """
    store = cargar_umbrales()
    row = (store.get("por_base") or {}).get((base or "").upper()) or {}
    u0 = float(umbral_actual if umbral_actual is not None else row.get("umbral_pct") or 0.0)
    if progreso_frac is None or tiempo_frac is None:
        return u0
    fees = fees_be_activo(base)
    piso = 0.0
    techo = max(fees * 2.0, 0.05)
    diff = float(progreso_frac) - float(tiempo_frac)
    # ±20% del umbral por unidad de desfase relativo
    factor = 1.0 + max(-0.4, min(0.4, diff * 0.5))
    return max(piso, min(techo, u0 * factor))


def _mismo_calibrado(store: dict, dias: float, equity: float) -> bool:
    if float(store.get("calibrado_ts") or 0) <= 0:
        return False
    if time.time() - float(store["calibrado_ts"]) > REUSO_CALIBRACION_S:
        return False
    try:
        same_d = abs(float(store.get("duracion_dias") or 0) - float(dias)) < 1e-6
        same_e = abs(float(store.get("equity_usd") or 0) - float(equity)) < 0.5
    except (TypeError, ValueError):
        return False
    return same_d and same_e and bool(store.get("por_base"))


def calibrar_lote(
    metas_por_base: dict[str, float],
    duracion_dias: float,
    equity_usd: float,
    *,
    ahora: float | None = None,
    forzar: bool = False,
) -> dict[str, Any]:
    """Calibra umbral de cada par del lote para ETA ≈ duracion_dias."""
    dias = float(duracion_dias)
    if dias <= 0:
        raise ValueError("duracion_dias debe ser > 0")
    eq = max(0.0, float(equity_usd))
    store = cargar_umbrales()
    if not forzar and _mismo_calibrado(store, dias, eq):
        return store

    eta_target_h = dias * 24.0
    por_base: dict[str, Any] = {}
    ahora = ahora if ahora is not None else time.time()
    for base, meta in (metas_por_base or {}).items():
        cal = calibrar_umbral_para_eta(base, float(meta), eta_target_h, ahora=ahora)
        por_base[(base or "").upper()] = {
            "umbral_pct": cal["umbral_pct"],
            "eta_h_est": cal.get("eta_h_est"),
            "eta_h_target": eta_target_h,
            "meta_usd": round(float(meta), 4),
            "ok": bool(cal.get("ok")),
        }

    payload = {
        "duracion_dias": dias,
        "equity_usd": eq,
        "calibrado_ts": ahora,
        "eta_h_target": eta_target_h,
        "por_base": por_base,
    }
    return guardar_umbrales(payload)


def umbral_activo(
    base: str,
    *,
    reajustar: bool = True,
    progreso_frac: float | None = None,
    tiempo_frac: float | None = None,
) -> dict[str, Any]:
    """Umbral vigente del par en marcha personalizado."""
    bu = (base or "").upper()
    store = cargar_umbrales()
    row = (store.get("por_base") or {}).get(bu) or {}
    u = float(row.get("umbral_pct") or 0.0)
    if reajustar and (progreso_frac is not None or tiempo_frac is not None):
        u = reajustar_umbral(
            bu,
            progreso_frac=progreso_frac,
            tiempo_frac=tiempo_frac,
            umbral_actual=u,
        )
    fees = fees_be_activo(bu)
    return {
        "base": bu,
        "umbral_pct": round(u, 6),
        "fees_be_pct": round(fees, 6),
        "duracion_dias": store.get("duracion_dias"),
        "eta_h_est": row.get("eta_h_est"),
        "ok": bool(row) or u > 0,
        "modo": "personalizado",
        "force_market": False,
    }
