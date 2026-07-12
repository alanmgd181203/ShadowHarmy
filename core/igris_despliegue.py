"""
Igris — despliegue paciente del manto §E (inverse LONG + lineal SHORT).

Reglas: Ask/Bid reales (no mid), umbral = break-even fees,
urgencia que degrada el umbral, fragmentación en micro-mordidas.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core import ancla


def libro_tank(tank, frente: str) -> tuple[list, list]:
    libros = getattr(tank, "libros", None) or {}
    libro = libros.get(frente) or {}
    return list(libro.get("bids") or []), list(libro.get("asks") or [])


def best_ask(asks: list) -> float:
    for row in asks or []:
        try:
            p, q = float(row[0]), float(row[1])
        except (IndexError, TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            return p
    return 0.0


def best_bid(bids: list) -> float:
    for row in bids or []:
        try:
            p, q = float(row[0]), float(row[1])
        except (IndexError, TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            return p
    return 0.0


def spread_ejecutable_pct(ask_long: float, bid_short: float) -> float:
    """
    Spread a favor en puntos porcentuales (misma unidad que ANCLA_FEE_*_PCT).
    Long se compra al Ask; Short se vende al Bid.
    Positivo = Long más barato que Short (asimetría a favor).
    """
    if ask_long <= 0 or bid_short <= 0:
        return float("-inf")
    mid = (ask_long + bid_short) / 2.0
    if mid <= 0:
        return float("-inf")
    return (bid_short - ask_long) / mid * 100.0


def fees_break_even_pct(frente_long: str, frente_short: str) -> float:
    fees = ancla.fees_total_cruce(frente_long, frente_short)
    return ancla.neto_minimo_requerido(fees)


def factor_urgencia(t0: float, ahora: float | None = None) -> float:
    """0 = paciencia plena (break-even); 1 = holgura máxima tras tau horas."""
    ahora = ahora if ahora is not None else time.time()
    tau_h = float(getattr(config, "IGRIS_URGENCIA_TAU_HORAS", 8.0) or 8.0)
    if tau_h <= 0:
        return 1.0
    edad_h = max(0.0, (ahora - float(t0 or ahora)) / 3600.0)
    return min(1.0, edad_h / tau_h)


def umbral_urgencia_pct(fees_be: float, t0: float, ahora: float | None = None) -> dict[str, float]:
    """
    umbral = fees_be - factor * (fees_be + holgura_max)

    Al inicio exige cubrir fees; con el tiempo permite ligero spread negativo.
    """
    ahora = ahora if ahora is not None else time.time()
    holgura = float(getattr(config, "IGRIS_URGENCIA_HOLGURA_MAX_PCT", 0.05) or 0.0)
    factor = factor_urgencia(t0, ahora)
    umbral = fees_be - factor * (fees_be + holgura)
    edad_h = max(0.0, (ahora - float(t0 or ahora)) / 3600.0)
    return {
        "umbral_pct": round(umbral, 6),
        "fees_be_pct": round(fees_be, 6),
        "factor": round(factor, 4),
        "edad_h": round(edad_h, 4),
        "holgura_max_pct": holgura,
    }


def micro_usd_disponible(
    *,
    bids_long: list,
    asks_long: list,
    bids_short: list,
    asks_short: list,
    frente_long: str,
    frente_short: str,
    restante_usd: float,
) -> dict[str, Any]:
    """Techo de micro-mordida en USD: min(restante, libro Ask L, libro Bid S, cap)."""
    prof_l = ancla.profundidad_usd_libro(bids_long, asks_long, frente_long)
    prof_s = ancla.profundidad_usd_libro(bids_short, asks_short, frente_short)
    techo_ask = float(prof_l.get("ask_usd") or 0)
    techo_bid = float(prof_s.get("bid_usd") or 0)
    cap = float(getattr(config, "IGRIS_MICRO_MAX_USD", 25.0) or 25.0)
    min_par = ancla.min_order_usd_cruce([frente_long, frente_short])
    bruto = min(float(restante_usd), techo_ask, techo_bid, cap) if restante_usd > 0 else 0.0
    if bruto + 1e-9 < min_par:
        return {
            "ok": False,
            "motivo": "bajo_min_order_o_sin_libro",
            "micro_usd": 0.0,
            "min_par_usd": min_par,
            "techo_ask_usd": techo_ask,
            "techo_bid_usd": techo_bid,
        }
    return {
        "ok": True,
        "motivo": "OK",
        "micro_usd": round(bruto, 4),
        "min_par_usd": min_par,
        "techo_ask_usd": techo_ask,
        "techo_bid_usd": techo_bid,
    }


def masa_desde_usd(usd: float, precio: float) -> float:
    if usd <= 0 or precio <= 0:
        return 0.0
    return usd / precio


def evaluar_puerta_se(
    tank,
    frente_long: str,
    frente_short: str,
    *,
    t0_paciencia: float,
    restante_usd: float,
    ahora: float | None = None,
) -> dict[str, Any]:
    """
    Puerta de disparo §E: libros reales, umbral fees±urgencia, micro-mordida.
    """
    ahora = ahora if ahora is not None else time.time()
    bids_l, asks_l = libro_tank(tank, frente_long)
    bids_s, asks_s = libro_tank(tank, frente_short)
    ask_l = best_ask(asks_l)
    bid_s = best_bid(bids_s)

    if ask_l <= 0 or bid_s <= 0:
        return {
            "ok": False,
            "motivo": "sin_ask_bid_libro",
            "ask_long": ask_l,
            "bid_short": bid_s,
        }

    spread = spread_ejecutable_pct(ask_l, bid_s)
    fees_be = fees_break_even_pct(frente_long, frente_short)
    urg = umbral_urgencia_pct(fees_be, t0_paciencia, ahora)
    umbral = urg["umbral_pct"]

    if spread < umbral:
        return {
            "ok": False,
            "motivo": "spread_bajo_umbral",
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            **urg,
        }

    micro = micro_usd_disponible(
        bids_long=bids_l,
        asks_long=asks_l,
        bids_short=bids_s,
        asks_short=asks_s,
        frente_long=frente_long,
        frente_short=frente_short,
        restante_usd=restante_usd,
    )
    if not micro["ok"]:
        return {
            "ok": False,
            "motivo": micro["motivo"],
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            **urg,
            **micro,
        }

    # Misma masa en ambas piernas (contabilidad Tusk histórica); ref = mid Ask/Bid
    precio_ref = (ask_l + bid_s) / 2.0
    masa = masa_desde_usd(micro["micro_usd"], precio_ref)
    if masa <= 0:
        return {
            "ok": False,
            "motivo": "masa_micro_cero",
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            **urg,
        }

    return {
        "ok": True,
        "motivo": "OK",
        "ask_long": ask_l,
        "bid_short": bid_s,
        "precio_ref": precio_ref,
        "spread_pct": round(spread, 6),
        "micro_usd": micro["micro_usd"],
        "masa": masa,
        "min_par_usd": micro["min_par_usd"],
        "techo_ask_usd": micro["techo_ask_usd"],
        "techo_bid_usd": micro["techo_bid_usd"],
        **urg,
    }
