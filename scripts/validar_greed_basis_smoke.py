#!/usr/bin/env python3
"""Smoke Greed basis hold — entrada/salida manto temporal."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import greed_basis as basis
from core import greed_mision as mision
from core import metaverso_grafo as mv
import core.config as config


def _op_eth_spot_perp(spread: float = 0.35, neto: float = 0.22):
    return {
        "base": "ETH",
        "tipo_spread": "spot_vs_perp",
        "spread_bruto_pct": spread,
        "regalo_neto_pct_est": neto,
        "fees_total_pct": 0.04,
        "entrada_maxima_usd": 500,
        "entrada_segura_usd": 200,
        "min_order_usd_cruce": 5,
        "frentes": {
            "compra": "ETHUSDT_SPOT",
            "venta": "ETHUSDT_LINEAL",
            "todos": ["ETHUSDT_SPOT", "ETHUSDT_LINEAL"],
        },
    }


def test_debe_entrar():
    ok, mot = basis.debe_entrar_basis(_op_eth_spot_perp())
    assert ok and mot == "OK", (ok, mot)
    ok2, mot2 = basis.debe_entrar_basis(_op_eth_spot_perp(spread=0.05))
    assert not ok2 and mot2 == "SPREAD_BAJO"
    print("  debe_entrar_basis OK")


def test_piernas():
    entrada, salida = basis.piernas_desde_op(_op_eth_spot_perp())
    assert len(entrada) == 2 and len(salida) == 2
    assert entrada[0]["side"] == "Buy" and salida[0]["side"] == "Sell"
    print("  piernas_desde_op OK")


def test_salida():
    hold = {
        "ts_entrada": time.time() - 10,
        "spread_entrada_pct": 0.35,
    }
    salir, mot = basis.debe_salir_basis(hold, _op_eth_spot_perp(spread=0.02))
    assert salir and mot == "SPREAD_CERRADO"
    hold2 = {**hold, "spread_entrada_pct": 0.40}
    salir2, mot2 = basis.debe_salir_basis(hold2, _op_eth_spot_perp(spread=0.25))
    assert salir2 and mot2 == "OBJETIVO_NETO"
    print("  debe_salir_basis OK")


def test_plan_mision():
    op = _op_eth_spot_perp()
    digest = {
        "metaverso": {"ETH": {"ruta_idonea": {"regalo_neto_pct": 0.2}}},
        "perfiles": {"ETH": {"spot_vs_perp": {"etiquetas_resumen": ["REVIERTE_RAPIDO"]}}},
    }
    plan = mision.resolver_plan(
        op, digest,
        equity=2000,
        margen_ocupado_pct=30,
        masa_autorizada=800,
        tank_semaforo="VERDE",
    )
    assert plan.get("ok"), plan
    assert plan.get("modo") == "BASIS_HOLD"
    assert plan.get("es_basis")
    assert len(plan.get("piernas_entrada") or []) == 2
    print("  resolver_plan BASIS_HOLD OK")


def test_metaverso_rank():
    filas = [
        {"base": "ETH", "tipo": "spot_vs_perp", "spread_pct": 0.32},
        {"base": "ETH", "tipo": "lineal_vs_inverse", "spread_pct": 0.18},
    ]
    ranked = mv.rankear_basis(filas, "ETH")
    assert ranked
    top = ranked[0]
    assert top["tipo_spread"] == "spot_vs_perp"
    assert top.get("modo") == "BASIS_HOLD"
    print("  metaverso rankear_basis OK", top["ruta_id"])


def test_resumen_holds():
    hold = basis.crear_hold(
        {"oid": "BASIS:ETH:spot_vs_perp:ETHUSDT_SPOT", "base": "ETH", "tipo_spread": "spot_vs_perp", "notional_usd": 50},
        _op_eth_spot_perp(),
    )
    res = basis.resumen_holds({"x": hold})
    assert res and res[0]["base"] == "ETH"
    print("  resumen_holds OK")


def main():
    print("[SMOKE] Greed basis hold")
    test_debe_entrar()
    test_piernas()
    test_salida()
    test_plan_mision()
    test_metaverso_rank()
    test_resumen_holds()
    print("[OK] greed_basis smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
