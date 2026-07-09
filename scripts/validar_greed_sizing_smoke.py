#!/usr/bin/env python3
"""Smoke Greed sizing — confianza, techo 1%, mordida."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import greed_mision as mision
from core import greed_sizing as sizing


def test_cap_1pct():
    cap = sizing.cap_notional_1pct_riesgo(100.0, 10.0)
    assert cap == 10.0  # 1% × 100 × 10x
    print("  cap 1% OK:", cap)


def test_techo_real():
    op = {
        "entrada_maxima_usd": 5000,
        "frentes": {"compra": "LTCUSDT_LINEAL", "venta": "LTCUSDC_LINEAL"},
    }
    t = sizing.techo_real_usd(op, equity=100.0, margen_ocupado_pct=20.0)
    assert t["cap_1pct_usd"] == 75.0  # LTC lineal 75x en MANTO_LEVERAGE
    assert t["techo_real_usd"] <= 75.0
    print("  techo real OK:", t["techo_real_usd"])


def test_calor_y_mordida():
    op = {
        "base": "LTC",
        "tipo_spread": "usdt_vs_usdc",
        "entrada_maxima_usd": 2000,
        "min_order_usd_cruce": 5,
        "regalo_neto_pct_est": 0.25,
        "frentes": {"compra": "LTCUSDT_LINEAL", "venta": "LTCUSDC_LINEAL"},
    }
    perfiles = {
        "LTC": {
            "usdt_vs_usdc": {
                "etiquetas_resumen": ["REVIERTE_RAPIDO"],
                "plazos": {
                    "corto": {"etiquetas": ["NEUTRO"], "metricas": {"mean_signed_pct": -0.2}},
                    "mediano": {"etiquetas": ["LONG_FRIENDLY"], "metricas": {"mean_signed_pct": -0.35}},
                    "largo": {"etiquetas": ["NEUTRO"], "metricas": {"mean_signed_pct": -0.1}},
                },
            },
        },
    }
    m = sizing.calcular_mordida(
        op, equity=100.0, margen_ocupado_pct=30.0,
        perfiles=perfiles, tank_semaforo="VERDE", pipeline_ms=150,
        masa_autorizada=50.0,
    )
    assert m["ok"]
    assert m["mordida_usd"] <= m["techo_real_usd"]
    assert m["margen_riesgo_est_usd"] <= 1.01
    print("  mordida OK:", m["mordida_usd"], "calor", m["calor"], "frac", m["fraccion"])


def test_huerfana_sin_perfil():
    op = {
        "base": "WIF",
        "tipo_spread": "perp_vs_index",
        "entrada_maxima_usd": 500,
        "min_order_usd_cruce": 5,
        "frentes": {"compra": "WIFUSDT_LINEAL", "venta": "WIFUSDT_LINEAL"},
    }
    import core.config as config
    config.ACTIVOS_HUERFANOS = ["WIF"]
    m = sizing.calcular_mordida(
        op, equity=200.0, margen_ocupado_pct=10.0,
        perfiles=None, tank_semaforo="VERDE",
    )
    assert m["fraccion"] <= 0.30
    print("  huerfana cap 30% OK:", m["fraccion"])


def test_veto_global():
    pausa, mot = mision.vetos_globales(tank_semaforo="ROJO", margen_ocupado_pct=50, equity=100)
    assert pausa and mot == "TANK_ROJO"
    pausa96, _ = mision.vetos_globales(tank_semaforo="VERDE", margen_ocupado_pct=96, equity=100)
    assert not pausa96
    print("  vetos OK")


def main():
    test_cap_1pct()
    test_techo_real()
    test_calor_y_mordida()
    test_huerfana_sin_perfil()
    test_veto_global()
    print("OK greed sizing smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
