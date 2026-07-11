#!/usr/bin/env python3
"""Smoke plan crecimiento — motor dinámico X/A_base + niveles Monarca."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import plan_crecimiento as pc
from core import beru_capital as bc


def test_niveles():
    casos = [
        (15, "ASPIRANTE", ["ETH"]),
        (100, "RECLUTA", ["ETH"]),
        (500, "SOLDADO", ["ETH", "SOL", "FIL", "LTC"]),
        (2500, "CAPITAN"),
        (15000, "GENERAL"),
        (150000, "SENOR_SOMBRAS"),
    ]
    for item in casos:
        eq, nivel = item[0], item[1]
        r = pc.nivel_por_equity(eq)
        assert r["nivel"] == nivel, (eq, r)
        if len(item) > 2:
            assert r["cazas_desbloqueadas"] == item[2], (eq, r)
    print("  niveles por equity OK")


def test_tiers_beru_motor():
    """Tiers desde rangos X (ceil ETH: Soldado 14–27 … Mariscal 112)."""
    r = bc.rangos_activo("ETH")
    x = r["X"]
    assert pc.tier_beru_instantaneo(x) == "BERUBBY"
    assert pc.tier_beru_instantaneo(2 * x) == "PROTO2"
    assert pc.tier_beru_instantaneo(4 * x) == "PROTO1"
    assert pc.tier_beru_instantaneo(8 * x) == "PLENO"
    nv = pc.nivel_por_equity(2 * x)
    assert nv.get("costo_base_X") == x
    assert nv.get("grado_beru") == "CAPITAN"
    print("  tiers Beru motor X OK", f"X={x}")


def test_presupuesto():
    p = pc.presupuesto_objetivo(150)
    assert abs(p["manto_pct"] - 0.95) < 1e-6
    assert abs(p["colchon_pct"] - 0.05) < 1e-6
    assert p["beru_pct"] == 0.0
    assert p["margen_objetivo_pct"] == 93.0
    print("  presupuesto 95/5 OK")


def test_botin_greed():
    b = pc.reparto_botin_greed(100)
    assert b["greed_retiene_usd"] == 50
    assert b["ejercito_usd"] == 50
    print("  botin Greed 50/50 OK")


def test_convivencia():
    prio = pc.prioridad_convivencia()
    assert prio[0].startswith("BERU")
    print("  prioridad Beru primero OK")


def test_resumen():
    r = pc.resumen_plan(500)
    assert r["nivel"] == "SOLDADO"
    assert "doctrina_multi_beru" in r
    assert r["concentracion_max_pct"] == 0.20
    print("  resumen OK", r["nivel_titulo"], "cazas", r["cazas_max"])


def main():
    print("[SMOKE] Plan crecimiento — motor 5 reglas")
    test_niveles()
    test_tiers_beru_motor()
    test_presupuesto()
    test_botin_greed()
    test_convivencia()
    test_resumen()
    print("[OK] plan_crecimiento smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
