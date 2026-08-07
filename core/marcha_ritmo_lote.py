"""Ritmo de lote — módulo legado (fuera del altar operativo).

Sello 2 marchas: solo asalto + personalizado. `tactico` / `marcha_forzada`
se normalizan a asalto en pase_director; este módulo queda inactivo
(aplica_marcha → False). Código retenido por compat ETA/JSON viejos.
Persiste: data/marcha_ritmo_lote.json
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from core import marcha_duracion as md
from core.manto_frecuencia import eta_despliegue_horas, fees_be_activo

# Vacío a propósito: marchas de ritmo ya no son operativas
MARCHAS_RITMO = frozenset()


def _pd():
    from core import pase_director as pd
    return pd


def _ruta_base() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ruta() -> str:
    return os.path.join(_ruta_base(), "data", "marcha_ritmo_lote.json")


def cargar() -> dict[str, Any]:
    ruta = _ruta()
    if not os.path.exists(ruta):
        return {"marcha_id": None, "reloj_eta_h": None, "por_base": {}, "ts": 0}
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"marcha_id": None, "reloj_eta_h": None, "por_base": {}, "ts": 0}
        data.setdefault("por_base", {})
        return data
    except (json.JSONDecodeError, OSError, TypeError):
        return {"marcha_id": None, "reloj_eta_h": None, "por_base": {}, "ts": 0}


def guardar(payload: dict[str, Any]) -> dict[str, Any]:
    ruta = _ruta()
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


def aplica_marcha(marcha_id: str | None) -> bool:
    try:
        mid = _pd().normalizar_marcha(marcha_id)
    except Exception:
        mid = (marcha_id or "").strip().lower()
    return mid in MARCHAS_RITMO


def _piso_techo(marcha_id: str, fees: float) -> tuple[float, float]:
    pd = _pd()
    mid = pd.normalizar_marcha(marcha_id)
    perfil = pd.MARCHAS[mid]
    mult = float(perfil.get("umbral_fees_mult") or 0.0)
    piso = fees * mult
    # Legado: techos táctico/forzada ya no aplican (mid operativo es asalto/personalizado)
    techo = fees * 1.5
    return piso, max(techo, piso)


def estimar_reloj_lote(
    bases_meta: dict[str, float],
    marcha_id: str,
    *,
    ahora: float | None = None,
) -> dict[str, Any]:
    """Reloj = max ETA @ umbral-base (marcha) del lote."""
    mid = _pd().normalizar_marcha(marcha_id)
    if mid not in MARCHAS_RITMO:
        return {"ok": False, "motivo": "marcha_sin_ritmo", "reloj_eta_h": None, "etas": {}}
    etas: dict[str, Any] = {}
    reloj = 0.0
    ok_any = False
    for base, meta in (bases_meta or {}).items():
        et = eta_despliegue_horas(base, float(meta), marcha_id=mid, ahora=ahora)
        etas[(base or "").upper()] = et
        if et.get("ok") and et.get("eta_h") is not None:
            ok_any = True
            reloj = max(reloj, float(et["eta_h"]))
    return {
        "ok": ok_any,
        "marcha_id": mid,
        "reloj_eta_h": round(reloj, 2) if ok_any else None,
        "etas": etas,
    }


def umbral_ritmo_par(
    base: str,
    marcha_id: str,
    *,
    meta_usd: float,
    reloj_eta_h: float | None,
    ahora: float | None = None,
    tiempo_frac: float | None = None,
) -> dict[str, Any]:
    """
    Si el par va adelantado (ETA < reloj), endurece umbral.
    Con el tiempo (tiempo_frac→1) afloja hacia el piso.
    """
    mid = _pd().normalizar_marcha(marcha_id)
    bu = (base or "").upper()
    fees = fees_be_activo(bu)
    piso, techo = _piso_techo(mid, fees)
    u = piso
    motivo = "piso"

    if reloj_eta_h and reloj_eta_h > 0 and meta_usd > 0:
        et = eta_despliegue_horas(bu, float(meta_usd), marcha_id=mid, ahora=ahora)
        eta_par = et.get("eta_h")
        if et.get("ok") and eta_par is not None and float(eta_par) + 1e-9 < float(reloj_eta_h):
            cal = md.calibrar_umbral_para_eta(bu, float(meta_usd), float(reloj_eta_h), ahora=ahora)
            if cal.get("ok"):
                u = max(piso, min(techo, float(cal["umbral_pct"])))
                motivo = "adelantado_endurece"
            else:
                ratio = float(eta_par) / float(reloj_eta_h)
                u = piso + (techo - piso) * max(0.0, min(1.0, 1.0 - ratio))
                motivo = "adelantado_nudge"

    if tiempo_frac is not None:
        tf = max(0.0, min(1.0, float(tiempo_frac)))
        u = piso + (u - piso) * (1.0 - tf)

    return {
        "base": bu,
        "marcha_id": mid,
        "umbral_pct": round(u, 6),
        "piso_pct": round(piso, 6),
        "techo_pct": round(techo, 6),
        "reloj_eta_h": reloj_eta_h,
        "motivo": motivo,
        "force_market": False,
        "modo_paciencia": f"ritmo_lote_{mid}",
    }


def sincronizar_lote(
    bases_meta: dict[str, float],
    marcha_id: str,
    *,
    ahora: float | None = None,
    tiempo_frac: float | None = None,
) -> dict[str, Any]:
    mid = _pd().normalizar_marcha(marcha_id)
    if mid not in MARCHAS_RITMO:
        return {"ok": False, "motivo": "marcha_sin_ritmo"}
    clock = estimar_reloj_lote(bases_meta, mid, ahora=ahora)
    por_base: dict[str, Any] = {}
    for base, meta in (bases_meta or {}).items():
        por_base[(base or "").upper()] = umbral_ritmo_par(
            base,
            mid,
            meta_usd=float(meta),
            reloj_eta_h=clock.get("reloj_eta_h"),
            ahora=ahora,
            tiempo_frac=tiempo_frac,
        )
    payload = {
        "marcha_id": mid,
        "reloj_eta_h": clock.get("reloj_eta_h"),
        "por_base": por_base,
        "ok": bool(clock.get("ok")),
    }
    return guardar(payload)


def umbral_activo(base: str, marcha_id: str | None = None) -> dict[str, Any] | None:
    """Lee umbral endurecido persistido; None si no aplica."""
    store = cargar()
    mid = _pd().normalizar_marcha(marcha_id or store.get("marcha_id"))
    if mid not in MARCHAS_RITMO:
        return None
    row = (store.get("por_base") or {}).get((base or "").upper())
    if not row:
        return None
    return dict(row)
