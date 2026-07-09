"""Mapa activo canónico — Bybit ↔ Binance (segundo mar, solo referencia)."""
from __future__ import annotations

import core.config as config

# Overrides cuando el ticker Binance no es {BASE}USDT
BINANCE_SPOT_OVERRIDES: dict[str, str] = {
    "1000PEPE": "1000PEPEUSDT",
    "1000BONK": "1000BONKUSDT",
    "1000FLOKI": "1000FLOKIUSDT",
    "1000LUNC": "1000LUNCUSDT",
    "1000RATS": "1000RATSUSDT",
    "1000SATS": "1000SATSUSDT",
    "1000SHIB": "1000SHIBUSDT",
    "1000XEC": "1000XECUSDT",
}


def base_desde_bybit_linear(symbol: str) -> str:
    sym = symbol.upper()
    if sym.endswith("USDT"):
        return sym[:-4]
    if sym.endswith("USDC"):
        return sym[:-4]
    return sym


def binance_spot_symbol(base: str) -> str:
    b = base.upper()
    if b in BINANCE_SPOT_OVERRIDES:
        return BINANCE_SPOT_OVERRIDES[b].lower()
    return f"{b.lower()}usdt"


def bases_vigilancia_binance() -> list[str]:
    """Trinidad + pentiverso + huérfanos (perps sin spot Bybit), cap configurable."""
    trinidad = list(getattr(config, "ACTIVOS_TRINIDAD", []) or [])
    penta = list(getattr(config, "ACTIVOS_PENTIVERSO", []) or [])
    huerfanas = list(getattr(config, "ACTIVOS_HUERFANOS", []) or [])
    cap = getattr(config, "BINANCE_REF_MAX_SYMBOLS", 80)
    out: list[str] = []
    seen: set[str] = set()
    for b in trinidad + penta + huerfanas:
        bu = b.upper()
        if bu in seen:
            continue
        seen.add(bu)
        out.append(bu)
        if len(out) >= cap:
            break
    return out


def pares_binance_vigilancia() -> list[tuple[str, str]]:
    """(base_canonica, stream_binance) ej. ('BTC', 'btcusdt')."""
    return [(b, binance_spot_symbol(b)) for b in bases_vigilancia_binance()]
