"""Tusk bóveda MNT — checkpoint doctrinal (cálculo frío, sin manos).

Escenario ideal: Funding→UTA → descuento MNT → lotes spot+short inverso →
capital de mando desde el short · foto inauguración spot/inverso.

Manos (Convert, transfer, shorts): SOLO si TUSK_BOVEDA_MANOS=true (default false).
Este módulo no llama Bridge ni coloca órdenes.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

import core.config as config

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RUTA_INAUG = os.path.join(_ROOT, "data", "tusk_boveda_inauguracion.json")


def manos_permitidas() -> bool:
    """Candado duro: el ritual no ejecuta salvo flag explícito."""
    return bool(getattr(config, "TUSK_BOVEDA_MANOS", False))


def doctrina_activa() -> bool:
    return bool(getattr(config, "TUSK_BOVEDA_MNT_DOCTRINA", True))


def plan_ritual_ideal() -> dict[str, Any]:
    """Fases del escenario ideal — especificación, no ejecución."""
    return {
        "escenario": "ideal_cuenta_nueva_o_capital_suelto",
        "manos": "OFF_por_default",
        "fases": [
            {
                "n": 0,
                "id": "reset_si_sucio",
                "desc": (
                    "Si bóveda sucia/heredada: sanear capa bóveda a cero "
                    "(peaje OK) y luego ritual ideal — ley Monarca 2026-08-02"
                ),
            },
            {"n": 1, "id": "funding_a_uta", "desc": "Mover capital de Funding a Trading unificado"},
            {"n": 2, "id": "activar_descuento_mnt", "desc": "Activar descuento tarifa MNT / colateral"},
            {
                "n": 3,
                "id": "mejor_camino",
                "desc": (
                    "Convert solo si buena oportunidad; si no, todo por spot: "
                    "crypto→USDT o USDC (mejor peaje/spread)→MNT"
                ),
            },
            {"n": 4, "id": "lote_semilla", "desc": "1–5% o mínimo → mejor camino → MNT spot"},
            {"n": 5, "id": "short_inverso_par", "desc": "Short inverso MNT ≈ spot del lote"},
            {"n": 6, "id": "cascada_poquitos", "desc": "Repetir a poquitos con la misma ley de camino"},
            {"n": 7, "id": "sesgo_spot", "desc": "Tolerancia con preferencia a más spot que short"},
            {"n": 8, "id": "sellar_inauguracion", "desc": "Foto precios spot/inverso + capital_mando"},
            {
                "n": 9,
                "id": "potencia_pase",
                "desc": "Con capital_mando, preguntar al pase hasta qué paso/rango hay potencia (antes de manto/Beru)",
            },
            {"n": 10, "id": "mantenimiento_fees", "desc": "Reponer spot cuando fees desgasten (futuro)"},
        ],
        "meta_final": (
            "Máximo capital útil en MNT spot como colateral + short inverso "
            "casi 1:1 (sesgo spot). Capital de mando = short×entrada → potencia pase."
        ),
        "manos_ley": (
            "Convert solo si buena oportunidad; si no, todo por spot "
            "(crypto→USDT|USDC→MNT). Manos OFF hasta orden Monarca."
        ),
        "ley_reset_sucio": (
            "Estado sucio/heredado → sanear bóveda a cero (fees=peaje) → ritual ideal. "
            "No catalogar todas las rarezas ahora. Excepción solo con orden Monarca."
        ),
        "no_fundir_manos_aun": True,
    }


def _f(x: Any, default: float = 0.0) -> float:
    try:
        if x in ("", None):
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def capital_mando_desde_hedge(
    hedges: list[dict[str, Any]] | None,
    *,
    preferir_inverse: bool = True,
) -> dict[str, Any]:
    """Capital de mando = size × precio_entrada (avg) del short MNT.

    Doctrina: lo más seguro tras preparar la bóveda (post-fees), antes de manto/Beru.
    """
    hedges = [h for h in (hedges or []) if str(h.get("base") or "").upper() == "MNT"]
    if not hedges:
        return {
            "ok": False,
            "motivo": "sin_hedge_mnt",
            "capital_mando_usd": 0.0,
            "size_mnt": 0.0,
            "precio_entrada": None,
            "fuente": None,
        }

    if preferir_inverse:
        inv = [
            h for h in hedges
            if "inverse" in str(h.get("category") or "").lower()
            or (
                str(h.get("symbol") or "").upper().endswith("USD")
                and not str(h.get("symbol") or "").upper().endswith(("USDT", "USDC"))
            )
        ]
        candidatos = inv if inv else hedges
    else:
        candidatos = hedges

    size_total = 0.0
    mando = 0.0
    fuente = None
    px_ref = None
    for h in candidatos:
        size = abs(_f(h.get("size")))
        avg = _f(h.get("avg_price") or h.get("avgPrice"))
        mark = _f(h.get("mark_price") or h.get("markPrice"))
        notional = _f(h.get("notional_usd"))
        if avg > 0 and size > 0:
            pieza = size * avg
            px = avg
            fu = "size_x_avg"
        elif notional > 0:
            pieza = notional
            px = (notional / size) if size > 0 else mark
            fu = "notional_position_value"
        elif mark > 0 and size > 0:
            pieza = size * mark
            px = mark
            fu = "size_x_mark"
        else:
            continue
        size_total += size
        mando += pieza
        fuente = fu
        px_ref = px

    if mando <= 0:
        return {
            "ok": False,
            "motivo": "hedge_sin_precio",
            "capital_mando_usd": 0.0,
            "size_mnt": size_total,
            "precio_entrada": None,
            "fuente": None,
        }

    return {
        "ok": True,
        "motivo": "ok",
        "capital_mando_usd": round(mando, 4),
        "size_mnt": round(size_total, 8),
        "precio_entrada": round(px_ref, 8) if px_ref else None,
        "fuente": fuente,
        "n_posiciones": len(candidatos),
    }


def foto_precios_mnt(
    *,
    spot_mark: float | None,
    inverse_mark: float | None,
    inverse_avg: float | None = None,
    spot_avg: float | None = None,
) -> dict[str, Any]:
    """Spread vivo spot vs inverso (base para inauguración / vigilancia)."""
    sm = _f(spot_mark) if spot_mark is not None else None
    im = _f(inverse_mark) if inverse_mark is not None else None
    if sm is not None and sm <= 0:
        sm = None
    if im is not None and im <= 0:
        im = None
    spread = None
    spread_pct = None
    if sm is not None and im is not None:
        spread = round(sm - im, 8)
        mid = (sm + im) / 2.0
        spread_pct = round((spread / mid) * 100.0, 6) if mid > 0 else None
    return {
        "spot_mark": sm,
        "spot_avg": _f(spot_avg) if spot_avg else None,
        "inverse_mark": im,
        "inverse_avg": _f(inverse_avg) if inverse_avg else None,
        "spread_spot_menos_inverse": spread,
        "spread_pct": spread_pct,
        "ts": time.time(),
    }


def equilibrio_spot_short(
    mnt_spot_usd: float,
    short_notional_usd: float,
    *,
    tolerancia_pct: float | None = None,
) -> dict[str, Any]:
    """¿Spot y short casi parejos? Sesgo doctrinal: preferir más spot."""
    tol = tolerancia_pct
    if tol is None:
        tol = float(getattr(config, "TUSK_BOVEDA_EQUILIBRIO_TOL_PCT", 0.03) or 0.03)
    spot = max(0.0, float(mnt_spot_usd))
    short = max(0.0, float(short_notional_usd))
    if spot <= 0 and short <= 0:
        return {
            "ok": False,
            "motivo": "sin_piernas",
            "ratio_spot_sobre_short": None,
            "sesgo": "ninguno",
            "dentro_tolerancia": False,
            "tolerancia_pct": tol,
        }
    if short <= 0:
        return {
            "ok": True,
            "motivo": "solo_spot",
            "ratio_spot_sobre_short": None,
            "sesgo": "solo_spot",
            "dentro_tolerancia": False,
            "tolerancia_pct": tol,
        }
    ratio = spot / short
    # Dentro de tolerancia alrededor de 1.0; sesgo spot = ratio >= 1
    bajo = 1.0 - tol
    alto = 1.0 + tol * 2  # más holgura arriba (más spot OK)
    dentro = bajo <= ratio <= alto
    if ratio > 1.0 + 1e-9:
        sesgo = "favor_spot"
    elif ratio < 1.0 - 1e-9:
        sesgo = "favor_short"
    else:
        sesgo = "parejo"
    return {
        "ok": True,
        "motivo": "ok",
        "ratio_spot_sobre_short": round(ratio, 6),
        "sesgo": sesgo,
        "dentro_tolerancia": dentro,
        "tolerancia_pct": tol,
        "spot_usd": round(spot, 4),
        "short_usd": round(short, 4),
        "delta_usd": round(spot - short, 4),
    }


def enriquecer_hedges_desde_raw(posiciones: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Igual espíritu que parse_hedge_shorts pero con avg/mark para capital_mando."""
    from core import tusk_tesoreria as tt

    base = tt.parse_hedge_shorts(posiciones)
    # Reinyectar avg/mark desde raw por symbol
    by_sym = {}
    for p in posiciones or []:
        sym = str(p.get("symbol") or "").upper()
        if sym:
            by_sym[sym] = p
    out = []
    for h in base:
        raw = by_sym.get(str(h.get("symbol") or "").upper()) or {}
        row = dict(h)
        row["avg_price"] = _f(raw.get("avgPrice")) or None
        row["mark_price"] = _f(raw.get("markPrice")) or None
        if not row.get("category"):
            row["category"] = str(raw.get("category") or raw.get("_category") or "")
        out.append(row)
    return out


def potencia_pase_desde_mando(capital_mando_usd: float) -> dict[str, Any]:
    """Con capital de mando, ¿hasta qué paso del pase hay potencia? (frío)."""
    from core import pase_director as pd

    eq = max(0.0, float(capital_mando_usd or 0))
    n = pd.potencia_n(eq)
    pasos = pd.pasos_en_potencia(eq)
    ultimo = pasos[-1] if pasos else None
    return {
        "capital_usado_usd": round(eq, 4),
        "potencia_n": n,
        "ultimo_paso": (
            {
                "n": int(ultimo["n"]),
                "activo": ultimo.get("activo"),
                "grado": ultimo.get("grado"),
                "acum_usd": ultimo.get("acum_usd"),
            }
            if ultimo
            else None
        ),
        "n_pasos_en_potencia": len(pasos),
        "nota": (
            "Solo lectura: no despliega manto. "
            "Ej. ~100 USD → potencia hasta paso 4 (acum 96)."
        ),
    }


def construir_bloque_boveda_mnt(
    *,
    mnt_usd: float,
    hedges: list[dict[str, Any]] | None,
    spot_mark: float | None = None,
    equity_vivo: float | None = None,
) -> dict[str, Any]:
    """Bloque para estado_vivo / tesorería — solo lectura."""
    hedges = list(hedges or [])
    mando = capital_mando_desde_hedge(hedges)
    short_usd = sum(_f(h.get("notional_usd")) for h in hedges if str(h.get("base") or "").upper() == "MNT")
    if mando.get("ok") and mando["capital_mando_usd"] > 0:
        short_ref = float(mando["capital_mando_usd"])
    else:
        short_ref = short_usd

    # Precios desde hedges si no vienen
    inv_mark = None
    inv_avg = None
    for h in hedges:
        if str(h.get("base") or "").upper() != "MNT":
            continue
        if h.get("mark_price"):
            inv_mark = _f(h["mark_price"])
        if h.get("avg_price"):
            inv_avg = _f(h["avg_price"])
        break

    foto = foto_precios_mnt(
        spot_mark=spot_mark,
        inverse_mark=inv_mark,
        inverse_avg=inv_avg,
    )
    eq = equilibrio_spot_short(float(mnt_usd or 0), short_ref)
    inaug = cargar_inauguracion()
    capital_para_pase = float(mando["capital_mando_usd"]) if mando.get("ok") else 0.0
    potencia = potencia_pase_desde_mando(capital_para_pase)

    return {
        "doctrina": "CHECKPOINT_TUSK_BOVEDA_MNT",
        "manos_permitidas": manos_permitidas(),
        "manos_nota": (
            "Ritual de preparación NO ejecuta órdenes (TUSK_BOVEDA_MANOS=false)."
            if not manos_permitidas()
            else "MANOS ON — peligro; solo con orden Monarca."
        ),
        "plan_ideal": plan_ritual_ideal(),
        "capital_mando": mando,
        "potencia_pase": potencia,
        "equity_vivo_usd": round(float(equity_vivo), 4) if equity_vivo is not None else None,
        "equilibrio": eq,
        "foto_viva": foto,
        "inauguracion": inaug,
        "nota_monarca": (
            "Capital de mando = short×entrada tras preparar bóveda. "
            "Con ese número → potencia_pase (qué pasos caben). "
            "Equity vivo puede ser un poco mayor (sesgo spot). "
            "Manos del ritual OFF. Casos especiales: siguiente pergamino."
        ),
    }


def cargar_inauguracion() -> dict[str, Any] | None:
    if not os.path.exists(_RUTA_INAUG):
        return None
    try:
        with open(_RUTA_INAUG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def sellar_inauguracion(payload: dict[str, Any]) -> dict[str, Any]:
    """Persiste foto de inauguración. No dispara órdenes. No auto-llamar desde arise."""
    os.makedirs(os.path.dirname(_RUTA_INAUG), exist_ok=True)
    data = {
        "ts": time.time(),
        "sellado": True,
        "manos_eran": manos_permitidas(),
        **payload,
    }
    tmp = _RUTA_INAUG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    if os.path.exists(_RUTA_INAUG):
        os.remove(_RUTA_INAUG)
    os.rename(tmp, _RUTA_INAUG)
    return data
