"""Libro / Ask-Bid — helpers compartidos (ex-Igris despliegue).

Igris de baja 2026-08-20. Quedan solo ojos de muro para Greed y lecturas.
"""
from __future__ import annotations

from typing import Any

import core.config as config
from core import ancla


def precio_ticker_frente(tank, frente: str) -> float:
    frentes: dict = {}
    lider = None
    if hasattr(tank, "_obtener_lider_verde"):
        try:
            lider = tank._obtener_lider_verde()
        except Exception:
            lider = None
    if lider is None and hasattr(tank, "nodos"):
        try:
            nodos = list(getattr(tank, "nodos") or [])
            nodos.sort(key=lambda n: getattr(n, "ultima_actualizacion", 0), reverse=True)
            lider = nodos[0] if nodos else None
        except Exception:
            lider = None
    if lider is not None:
        if hasattr(lider, "precios_con_reflejo"):
            try:
                frentes = dict(lider.precios_con_reflejo() or {})
            except Exception:
                frentes = dict(getattr(lider, "precios", {}) or {})
        else:
            frentes = dict(getattr(lider, "precios", {}) or {})
    if not frentes and hasattr(tank, "precios"):
        frentes = dict(getattr(tank, "precios") or {})
    return float(frentes.get(frente) or 0.0)


def libro_tank(tank, frente: str) -> tuple[list, list]:
    libros = ancla.libros_desde_lider(tank) if tank is not None else {}
    libro = dict(libros.get(frente) or {})
    return list(libro.get("bids") or []), list(libro.get("asks") or [])


def best_ask(asks: list) -> float:
    if not asks:
        return 0.0
    try:
        return float(asks[0][0])
    except (TypeError, ValueError, IndexError):
        return 0.0


def best_bid(bids: list) -> float:
    if not bids:
        return 0.0
    try:
        return float(bids[0][0])
    except (TypeError, ValueError, IndexError):
        return 0.0


def spread_ejecutable_pct(ask_long: float, bid_short: float) -> float:
    a = float(ask_long or 0)
    b = float(bid_short or 0)
    if a <= 0 or b <= 0:
        return float("-inf")
    return (b - a) / a * 100.0


def fees_break_even_pct(frente_long: str, frente_short: str) -> float:
    _ = frente_long, frente_short
    return float(getattr(config, "FEES_BREAK_EVEN_DEFAULT_PCT", 0.11) or 0.11)
