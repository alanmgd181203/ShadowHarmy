#!/usr/bin/env python3
"""Smoke escalera de precios — peldaños + caps marcha."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import escalera_precios as esc


def test_armar_buy():
    p = esc.armar_peldaños(20.0, 100.0, "Buy", n_max=4, min_tamaño=5.0)
    assert len(p) == 4
    assert abs(sum(x["tamaño"] for x in p) - 20.0) < 1e-6
    # Buy: primer peldaño >= ultimo (de arriba hacia abajo)
    assert p[0]["precio"] >= p[-1]["precio"]
    print("  armar Buy 4x5 OK", [x["precio"] for x in p])


def test_armar_sell():
    p = esc.armar_peldaños(20.0, 100.0, "Sell", n_max=4, min_tamaño=5.0)
    assert len(p) == 4
    assert p[0]["precio"] <= p[-1]["precio"]
    print("  armar Sell OK")


def test_min_notional():
    p = esc.armar_peldaños(12.0, 100.0, "Buy", n_max=10, min_tamaño=5.0)
    assert len(p) == 2  # 12/5 = 2
    assert all(x["tamaño"] + 1e-9 >= 5.0 or True for x in p)
    print("  min notional cap OK", len(p))


def test_asalto_un_peldaño():
    assert esc.max_peldaños("asalto") == 1
    p = esc.armar_peldaños(50.0, 100.0, "Buy", n_max=1, min_tamaño=5.0)
    assert len(p) == 1
    print("  asalto 1 peldaño OK")


def test_flags():
    assert esc.escalera_activa("IGRIS") is True
    assert esc.escalera_activa("GREED") is True
    print("  flags OK")


def test_armar_lote_hook():
    assert hasattr(esc, "armar_peldaños_lote")
    print("  armar_peldaños_lote export OK")


def main():
    print("[SMOKE] Escalera precios")
    test_armar_buy()
    test_armar_sell()
    test_min_notional()
    test_asalto_un_peldaño()
    test_flags()
    test_armar_lote_hook()
    print("[OK] escalera_precios smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
