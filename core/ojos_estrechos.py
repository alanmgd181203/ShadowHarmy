"""Ojos estrechos — Santos last price, sin orderbook (sello Monarca 2026-08-13).

Tank deja de beber el catálogo entero de Bybit.
Igris Asalto (Market) + Beru hibernado: last price basta.
Spot: mismos Santos (Beru verá last spot; sin muros hasta Greed).
"""
from __future__ import annotations

from typing import Iterable

import core.config as config

# 13 Santos del pase (PASE_BATALLA_13_SANTOS)
SANTOS_PASE: tuple[str, ...] = (
    "MNT", "LINK", "AVAX", "LTC", "HYPE", "BCH", "XRP",
    "SOL", "ETH", "ADA", "AAVE", "FIL", "OP",
)


def bases_santos(extra: Iterable[str] | None = None) -> list[str]:
    """Bases a vigilar: pase + pentiverso + semilla + extras."""
    seen: set[str] = set()
    out: list[str] = []
    for src in (
        SANTOS_PASE,
        getattr(config, "ACTIVOS_PENTIVERSO", None) or [],
        [getattr(config, "TICKER_BASE", None), getattr(config, "BERU_ACTIVO_SEMILLA", None)],
        list(extra or []),
    ):
        for a in src:
            u = str(a or "").strip().upper()
            if u and u not in seen:
                seen.add(u)
                out.append(u)
    return out


def aplicar_ojos_last_price_santos(
    bases: Iterable[str] | None = None,
    *,
    apagar_binance_ref: bool = True,
) -> list[str]:
    """Estrecha Bridge: solo bases dadas · books OFF · sin muros spot/perp.

    Devuelve la lista de bases aplicada.
    """
    out = list(bases) if bases is not None else bases_santos()
    # normalizar
    seen: set[str] = set()
    clean: list[str] = []
    for a in out:
        u = str(a or "").strip().upper()
        if u and u not in seen:
            seen.add(u)
            clean.append(u)
    config.BRIDGE_WS_BASES = clean
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = False
    if hasattr(config, "BRIDGE_WS_BOOKS_BASES"):
        config.BRIDGE_WS_BOOKS_BASES = []
    # Sin Greed: no hace falta segundo mar Binance para este ritual
    if apagar_binance_ref and hasattr(config, "BINANCE_REF_ENABLED"):
        config.BINANCE_REF_ENABLED = False
    return clean
