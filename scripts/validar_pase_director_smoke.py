#!/usr/bin/env python3
"""Smoke director del pase — potencia, lote/reserva, umbrales marcha."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import pase_director as pd


def test_potencia():
    assert pd.potencia_n(13) == 0
    assert pd.potencia_n(14) == 1
    assert pd.potencia_n(123) == 5
    assert pd.potencia_n(1500) == 28  # ADA Caballero acum 1471; 1500 < 1513 → 28
    assert pd.potencia_n(3161) == 52
    print("  potencia OK")


def test_lote_forzada():
    # 10 pasos potencia (~277 AVAX Soldado), reserva 2 → lote 8
    eq = 277.0
    assert pd.potencia_n(eq) == 10
    plan = pd.plan_lote(eq, marcha_id="marcha_forzada", pasos_logrados=[])
    assert plan["reserva_pasos"] == 2
    assert plan["lote_techo_n"] == 8
    assert len(plan["lote"]) == 8
    assert len(plan["cola_fina"]) == 2
    assert len(plan["trabajo"]) == 8
    assert plan["foco"]["n"] == 1
    # Llenar lote → cola uno a uno
    plan2 = pd.plan_lote(eq, marcha_id="marcha_forzada", pasos_logrados=list(range(1, 9)))
    assert plan2["lote_lleno"] is True
    assert len(plan2["trabajo"]) == 1
    assert plan2["foco"]["n"] == 9
    print("  lote forzada 10->8+cola OK")


def test_umbrales():
    fees = 0.10
    t = pd.umbral_por_marcha(fees, marcha_id="tactico")
    assert abs(t["umbral_pct"] - 0.10) < 1e-9
    assert t["force_market"] is False
    f = pd.umbral_por_marcha(fees, marcha_id="marcha_forzada", t0_paciencia=None)
    assert abs(f["umbral_pct"] - 0.05) < 1e-9
    a = pd.umbral_por_marcha(fees, marcha_id="asalto")
    assert a["umbral_pct"] == 0.0
    assert a["force_market"] is True
    print("  umbrales marcha OK")


def test_beru_gate():
    assert pd.beru_puede_cazar("ETH", 100, pasos_logrados=[]) is False
    assert pd.beru_puede_cazar("ETH", 100, pasos_logrados=[1]) is True
    assert pd.beru_puede_cazar("HYPE", 100, pasos_logrados=[1]) is False
    print("  beru gate OK")


def test_persist_marcha():
    pd.guardar_marcha("tactico")
    assert pd.cargar_marcha() == "tactico"
    assert pd.perfil_marcha()["id"] == "tactico"
    pd.guardar_marcha("marcha_forzada")
    assert pd.cargar_marcha() == "marcha_forzada"
    assert pd.perfil_marcha()["id"] == "marcha_forzada"
    print("  persist marcha OK")


def test_resumen():
    r = pd.resumen_director(411)
    assert r["potencia_n"] == 13
    assert r["marcha_id"] in pd.MARCHAS
    print("  resumen OK", r["marcha_titulo"], "potencia", r["potencia_n"])


def main():
    print("[SMOKE] Pase director")
    test_potencia()
    test_lote_forzada()
    test_umbrales()
    test_beru_gate()
    test_persist_marcha()
    test_resumen()
    print("[OK] pase_director smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
