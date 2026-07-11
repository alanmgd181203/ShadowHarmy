#!/usr/bin/env python3
"""Smoke Beru capital — motor 5 Reglas + ceil X (reserva ≥5%)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc
from core import beru_tier
import core.config as config


def test_eth_x_ceil_y_rangos():
    r = bc.rangos_activo("ETH")
    # margen 12.5 / 0.95 ≈ 13.16 → ceil → X=14 · Mariscal=112
    assert r["X"] == 14
    assert r["SOLDADO"] == (14, 27)
    assert r["CAPITAN"] == (28, 55)
    assert r["GENERAL"] == (56, 111)
    assert r["MARISCAL"] == 112
    assert (1.0 - r["margen_volumen_base_usd"] / r["X"]) >= 0.05 - 1e-9
    print("  ETH X=14 (ceil) rangos OK · reserva≥5%")


def test_friccion_ley():
    assert abs(bc.friccion_grado_pct("SOLDADO") - 0.008) < 1e-9
    assert abs(bc.friccion_grado_pct("CAPITAN") - 0.004) < 1e-9
    assert abs(bc.friccion_grado_pct("GENERAL") - 0.002) < 1e-9
    assert abs(bc.friccion_grado_pct("MARISCAL") - 0.001) < 1e-9
    print("  fricción 0.8/0.4/0.2/0.1 OK")


def test_grado_por_equity():
    assert bc.grado_en_rango(10, "ETH") == "BLOQUEADO"
    assert bc.grado_en_rango(20, "ETH") == "SOLDADO"
    assert bc.grado_en_rango(30, "ETH") == "CAPITAN"
    assert bc.grado_en_rango(60, "ETH") == "GENERAL"
    assert bc.grado_en_rango(112, "ETH") == "MARISCAL"
    print("  grados por equity OK")


def test_cola_graduacion():
    cola = bc.cola_activos_con_a_base(["ETH", "SOL"])
    assert cola[0]["A_base"] == 0
    assert cola[1]["A_base"] == cola[0]["A_base_siguiente"] == 112
    print("  cola A_base ETH→SOL OK", f"SOL X={cola[1]['X']}")


def test_telemetria_cero():
    t = bc.telemetria_progresion(0)
    assert t["grado_beru"] == "BLOQUEADO"
    assert "Inanición" in t["rango_ejercito"]
    print("  telemetría $0 Inanición OK")


def test_capitanes_config():
    assert abs(config.BERU_FRICCION_SOLDADO_PCT - 0.008) < 1e-9
    print("  config fricción OK")


def test_tiers_pasos():
    t = beru_tier.tier_por_id("PROTO1")
    oz, red = t.pasos("NEGOCIADOR")
    assert abs(oz - 0.002) < 1e-9
    print("  PROTO1 pasos OK")


def main():
    print("[SMOKE] Beru capital — fricción + ceil")
    test_eth_x_ceil_y_rangos()
    test_friccion_ley()
    test_grado_por_equity()
    test_cola_graduacion()
    test_telemetria_cero()
    test_capitanes_config()
    test_tiers_pasos()
    print("OK beru capital smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
