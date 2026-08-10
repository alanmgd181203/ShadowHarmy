"""Ventana 48–52 / long-primero — doctrina 21 checkpoint 3.5.8c (2026-07-17).

Sustituye la banda simétrica que se estrecha con margen % como ley de equilibrio L/S.
Piezas de ranking (meta bloque, mitad engorde) siguen en códice hasta fusión.
"""
from __future__ import annotations

from typing import Any

import core.config as config

# Ratio = USD_long / (USD_long + USD_short)  — por barco
LONG_MAX = 0.52
LONG_MIN_HARD = 0.48
LONG_MIN_SHORT_GORDO = 0.49  # short ≤ 51% en crecimiento


def ventana_activa() -> bool:
    return bool(getattr(config, "MANTO_VENTANA_4852_ACTIVA", True))


def long_max() -> float:
    return float(getattr(config, "MANTO_VENTANA_LONG_MAX", LONG_MAX))


def long_min_hard() -> float:
    return float(getattr(config, "MANTO_VENTANA_LONG_MIN", LONG_MIN_HARD))


def long_min_operativo() -> float:
    """Piso en crecimiento (short gordo más apretado)."""
    return float(getattr(config, "MANTO_VENTANA_LONG_MIN_CORRECCION", LONG_MIN_SHORT_GORDO))


def banda_crecimiento() -> tuple[float, float]:
    """(min, max) ratio long operativo — 49%–52% en crecimiento."""
    return (long_min_operativo(), long_max())


def banda_hard() -> tuple[float, float]:
    """Candado absoluto 48%–52%."""
    return (long_min_hard(), long_max())


def ratio_long_usd(usd_long: float, usd_short: float) -> float:
    total = float(usd_long) + float(usd_short)
    if total <= 0:
        return 0.5
    return float(usd_long) / total


def usd_lineal_desde_qty(qty: float, precio_entrada: float) -> float:
    """Lineal cotiza en moneda → USD @ entrada (nunca mark)."""
    if qty <= 0 or precio_entrada <= 0:
        return 0.0
    return float(qty) * float(precio_entrada)


def usd_frente_desde_qty(frente: str, qty: float, precio_entrada: float) -> float:
    """Qty de exchange → USD notional (inverse = contratos USD; lineal = qty×px)."""
    q = float(qty)
    if q <= 0:
        return 0.0
    px = float(precio_entrada or 0)
    try:
        from core import lote_bybit as lote

        filt = lote.filtros_lote(frente)
        return float(lote.qty_a_usd(q, px if px > 0 else 1.0, filt))
    except Exception:
        fu = str(frente or "").upper()
        if "INVERSE" in fu or (fu.endswith("USD") and "USDT" not in fu and "USDC" not in fu):
            return q  # inverse: cada contrato ≈ $1
        return usd_lineal_desde_qty(q, px) if px > 0 else q


def usd_piernas_desde_pesos(pesos: dict | None) -> tuple[float, float]:
    """
    USD long/short ya desplegados @ precio medio de entrada (no mark vivo).
    Respeta unidad por frente (inverse ≠ qty×precio).
    """
    usd_l = 0.0
    usd_s = 0.0
    for frente, p in (pesos or {}).items():
        if not isinstance(p, dict):
            continue
        ml = float(p.get("long") or 0)
        ms = float(p.get("short") or 0)
        px_l = float(p.get("precio_medio_long") or 0)
        px_s = float(p.get("precio_medio_short") or 0)
        if ml > 0:
            usd_l += usd_frente_desde_qty(str(frente), ml, px_l)
        if ms > 0:
            usd_s += usd_frente_desde_qty(str(frente), ms, px_s)
    return usd_l, usd_s


def clasificar_ratio(ratio: float) -> str:
    """OK | LONG_EXCEDIDO | SHORT_EXCEDIDO | FUERA_HARD."""
    r = float(ratio)
    lo_h, hi = banda_hard()
    lo_op, _ = banda_crecimiento()
    if r > hi:
        return "LONG_EXCEDIDO"
    if r < lo_h:
        return "FUERA_HARD"
    if r < lo_op:
        return "SHORT_EXCEDIDO"
    return "OK"


def dentro_ventana(ratio: float, *, operativo: bool = True) -> bool:
    r = float(ratio)
    lo_h, hi = banda_hard()
    if r > hi or r < lo_h:
        return False
    if operativo and r < long_min_operativo():
        return False
    return True


def verificar_post_maniobra(usd_long: float, usd_short: float, *, operativo: bool = True) -> bool:
    if float(usd_long) + float(usd_short) <= 0:
        return True
    return dentro_ventana(ratio_long_usd(usd_long, usd_short), operativo=operativo)


def direccion_correccion(ratio: float) -> str | None:
    """LONG = falta long / SHORT = falta short. None si OK."""
    c = clasificar_ratio(ratio)
    if c == "LONG_EXCEDIDO":
        return "SHORT"
    if c in ("SHORT_EXCEDIDO", "FUERA_HARD"):
        return "LONG"
    return None


def direccion_engorde_preferida(usd_long: float, usd_short: float) -> str:
    """Long-primero: si empatados o short arriba → LONG; si long arriba (sin romper) → SHORT."""
    r = ratio_long_usd(usd_long, usd_short)
    if usd_long <= 0 and usd_short <= 0:
        return "LONG"
    corr = direccion_correccion(r)
    if corr:
        return corr
    # Dentro de ventana: preferir empujar hacia 50 con sesgo long
    if r <= 0.50:
        return "LONG"
    return "SHORT"


def acoplar_pierna_usd(
    usd_propuesto: float,
    usd_otra: float,
    *,
    propuesta_es_long: bool,
) -> float:
    """
    Si el fill rompería la ventana, recorta la pierna en USD (doctrina: acoplar la de dólares).
    Devuelve el USD máximo permitido para la pierna propuesta.
    """
    if usd_propuesto <= 0:
        return 0.0
    otra = max(0.0, float(usd_otra))
    prop = float(usd_propuesto)
    lo, hi = banda_crecimiento()

    if propuesta_es_long:
        # long / (long+otra) <= hi  → long <= hi/(1-hi) * otra
        # long / (long+otra) >= lo  → long >= lo/(1-lo) * otra
        if otra <= 0:
            return prop  # primera sangre
        max_l = (hi / (1.0 - hi)) * otra if hi < 1 else prop
        min_l = (lo / (1.0 - lo)) * otra if lo < 1 else 0.0
        return max(min_l, min(prop, max_l))
    # propuesta short
    if otra <= 0:
        return prop
    # long fijo = otra; short = prop
    # otra/(otra+short) <= hi → short >= otra*(1-hi)/hi
    # otra/(otra+short) >= lo → short <= otra*(1-lo)/lo
    min_s = (otra * (1.0 - hi) / hi) if hi > 0 else 0.0
    max_s = (otra * (1.0 - lo) / lo) if lo > 0 else prop
    return max(min_s, min(prop, max_s))


def resumen_barco(usd_long: float, usd_short: float) -> dict[str, Any]:
    r = ratio_long_usd(usd_long, usd_short)
    lo, hi = banda_crecimiento()
    return {
        "ratio_long": round(r, 6),
        "pct_long": round(r * 100, 4),
        "pct_short": round((1.0 - r) * 100, 4),
        "banda_min": lo,
        "banda_max": hi,
        "estado": clasificar_ratio(r),
        "ok": dentro_ventana(r),
        "usd_long": round(float(usd_long), 4),
        "usd_short": round(float(usd_short), 4),
        "base_ratio": "desplegado_actual_usd_entrada",
        "ley": "ventana_48_52_long_primero",
    }
