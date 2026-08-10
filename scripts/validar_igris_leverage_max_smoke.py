#!/usr/bin/env python3
"""Smoke: forzar apalancamiento máximo + avisos si Bybit baja el techo."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import igris_leverage as ilev
from core.bridge import OrdenResultado


class _Bel:
    def __init__(self):
        self.logs: list[tuple] = []

    async def anotar(self, quien, tipo, msg):
        self.logs.append((quien, tipo, msg))


class _Bridge:
    def __init__(self, *, fail_above: dict[tuple[str, str], int] | None = None):
        # (symbol, category) → máximo aceptado; > ese valor falla
        self.fail_above = fail_above or {}
        self.calls: list[tuple] = []

    async def set_leverage(self, symbol, leverage, category="linear"):
        lev = int(leverage)
        self.calls.append((symbol, category, lev))
        cap = self.fail_above.get((symbol, category))
        if cap is not None and lev > cap:
            return OrdenResultado(False, mensaje=f"max leverage is {cap}")
        return OrdenResultado(True, mensaje="OK")


def test_escalones():
    e = ilev._escalones_prueba(75)
    assert e[0] == 75
    assert 50 in e and 25 in e


def test_hint():
    assert ilev._parse_hint_max("max leverage is 50") == 50
    assert ilev._parse_hint_max("cannot exceed 20") == 20


async def test_forzar_symbol_aviso():
    config.IGRIS_FORCE_MAX_LEVERAGE = True
    bel = _Bel()
    br = _Bridge(fail_above={("HYPEUSDT", "linear"): 10})
    out = await ilev.forzar_max_en_symbol(
        br, bel, symbol="HYPEUSDT", category="linear", lev_pedido=75, activo="HYPE",
    )
    assert out["ok"] is True
    assert out["pedido"] == 75
    assert out["aplicado"] == 10
    assert any(t == "LEVERAGE_MAX_AVISO" for _, t, _ in bel.logs), bel.logs


async def test_lote_mock():
    config.IGRIS_FORCE_MAX_LEVERAGE = True
    bel = _Bel()
    br = _Bridge()
    out = await ilev.forzar_max_leverage_lote(br, bel, ["ETH", "LINK"])
    assert out["n_ok"] == 2
    assert any(t == "LEVERAGE_MAX_LOTE" for _, t, _ in bel.logs)
    # ETH pide 100x inv+lin
    assert any(c[0] == "ETHUSD" and c[2] == 100 for c in br.calls)
    assert any(c[0] == "ETHUSDT" and c[2] == 100 for c in br.calls)


def main() -> None:
    test_escalones()
    test_hint()
    asyncio.run(test_forzar_symbol_aviso())
    asyncio.run(test_lote_mock())
    print("OK validar_igris_leverage_max_smoke")


if __name__ == "__main__":
    main()
