#!/usr/bin/env python3
"""Smoke Beru rail — elegir frente stable."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import time
from core.models import MarketContext
from core import beru_rail as br


def _ctx(symbol: str, price: float, *, ask_vol=100.0, bid_vol=100.0) -> MarketContext:
    now = time.time()
    return MarketContext(
        symbol=symbol, market_type="spot", last_price=price,
        spread=0.0, depth_ask=1.0, depth_bid=1.0,
        volatilidad=0.0, timestamp=now, local_arrival=now,
        muro_ask_volumen=ask_vol, muro_bid_volumen=bid_vol,
    )


def test_frentes_estables():
    frentes = br.frentes_casa_estables("ETH")
    assert "ETHUSDT_SPOT" in frentes
    assert "ETHUSDC_SPOT" in frentes
    print("  frentes ETH", frentes)


def test_elige_usdt_mas_barato_long():
    ctx = {
        "ETHUSDT_SPOT": _ctx("ETHUSDT", 3000),
        "ETHUSDC_SPOT": _ctx("ETHUSDC", 2990),
    }
    f, p, meta = br.elegir_mejor_rail(ctx, masa=10, is_long=True)
    assert f == "ETHUSDC_SPOT"
    assert p > 0
    assert meta.get("candidatos") == 2
    print("  long elige USDC OK", f, round(p, 2))


def test_elige_usdt_mas_caro_short():
    ctx = {
        "ETHUSDT_SPOT": _ctx("ETHUSDT", 3000),
        "ETHUSDC_SPOT": _ctx("ETHUSDC", 2990),
    }
    f, p, meta = br.elegir_mejor_rail(ctx, masa=10, is_long=False)
    assert f == "ETHUSDT_SPOT"
    print("  short elige USDT OK", f)


def main():
    test_frentes_estables()
    test_elige_usdt_mas_barato_long()
    test_elige_usdt_mas_caro_short()
    print("OK beru rail smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
