#!/usr/bin/env python3
"""Smoke Beru capital — tiers Proto/Pleno y manto por activo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc
from core import beru_tier
import core.config as config


def test_eth_berubby():
    m = bc.margen_manto_por_tier("ETH", "BERUBBY")
    assert m == 12.5
    print("  ETH BERUBBY manto $12.5 OK")


def test_eth_proto1_default():
    """Arranque Monarca: PROTO1 + ETH semilla → manto ~$50."""
    assert config.BERU_TIER_DEFAULT == "PROTO1"
    m = bc.margen_manto_beru_100("ETH")
    assert m == 50.0
    eq = bc.equity_minima_recomendada("ETH")
    assert eq == 50.0
    print("  ETH PROTO1 manto $50 + equity $50 OK")


def test_eth_pleno():
    m = bc.margen_manto_por_tier("ETH", "PLENO")
    assert m == 100.0
    print("  ETH PLENO manto $100 OK")


def test_wif_proto1():
    m = bc.margen_manto_beru_100("WIF")
    assert m == 250.0  # pleno $500 / escala 2
    print("  WIF PROTO1 manto $250 OK")


def test_capitanes_config():
    assert abs(config.BERU_VACIO_ANSIEDAD - 0.012) < 1e-6
    assert abs(config.BERU_VACIO_NORMAL - 0.016) < 1e-6
    print("  vacios 1.2/1.6 OK")


def test_tiers_pasos():
    t = beru_tier.tier_por_id("PROTO1")
    oz, red = t.pasos("NEGOCIADOR")
    assert abs(oz - 0.002) < 1e-9 and abs(red - 0.001) < 1e-9
    oz_c, red_c = t.pasos("CAZA")
    assert abs(oz_c - 0.001) < 1e-9 and abs(red_c - 0.001) < 1e-9
    assert abs(t.distancia_clon_pct - 0.002) < 1e-9
    pleno = beru_tier.tier_por_id("PLENO")
    assert abs(pleno.distancia_clon_pct - 0.001) < 1e-9
    bb = beru_tier.tier_por_id("BERUBBY")
    assert abs(bb.distancia_clon_pct - 0.008) < 1e-9
    assert bb.oz_tras_toque_red == 0.02
    oz_bb = beru_tier.oz_berubby_tras_toque_red(100.0, "SHORT")
    assert abs(oz_bb - 98.0) < 1e-6
    print("  PROTO1 + BERUBBY pasos OK")


def test_tabla_flota():
    filas = bc.tabla_flota_beru()
    assert len(filas) >= 30  # activos × tiers
    eth_proto = next(f for f in filas if f["activo"] == "ETH" and f["tier"] == "PROTO1")
    assert eth_proto["es_semilla"]
    assert eth_proto["margen_manto_tier_usd"] == 50.0
    print("  flota", len(filas), "filas OK")


def main():
    test_eth_berubby()
    test_eth_proto1_default()
    test_eth_pleno()
    test_wif_proto1()
    test_capitanes_config()
    test_tiers_pasos()
    test_tabla_flota()
    print("OK beru capital smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
