#!/usr/bin/env python3
"""Smoke Igris — banda delta, fases margen, frentes manto."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import igris_estado as ie
from core import mercado
import core.config as config


def test_fases_margen():
    assert ie.fase_margen(75) == "EXPANSION"
    assert ie.fase_margen(82) == "TERRENO_CAZA"
    assert ie.fase_margen(87) == "IDEAL"
    assert ie.fase_margen(91) == "ALTA_PRESION"
    assert ie.fase_margen(94) == "PRE_PODA"
    assert ie.fase_margen(96) == "LEY_MARCIAL"
    print("  fases margen OK")


def test_banda_delta():
    b_lo = mercado.calcular_banda_delta(50)
    b_hi = mercado.calcular_banda_delta(96)
    assert b_lo[0] < 0.5 < b_lo[1]
    assert b_hi[0] == b_hi[1] == 0.5
    assert mercado.verificar_delta_post_maniobra(50, 50, 50)
    assert not mercado.verificar_delta_post_maniobra(50, 80, 20)
    print("  banda delta OK:", b_lo, "->", b_hi)


def test_resumen_manto():
    r = ie.resumen_manto(
        margen_ocupado_pct=75,
        peso_long=30,
        peso_short=70,
        banda_min=0.45,
        banda_max=0.55,
    )
    assert r["fase_margen"] == "EXPANSION"
    assert r["accion_heuristica"] == "REBALANCEO_IGRIS"
    print("  resumen OK:", r["accion_heuristica"])


def test_frentes_manto():
    frentes = getattr(config, "FRENTES_MANTO_ALL", [])
    assert len(frentes) >= 4
    assert any("LINEAL" in f for f in frentes)
    print("  frentes manto OK:", len(frentes))


def test_bootstrap_se():
    from core import igris_manto as im
    fl, fs = im.frentes_bootstrap("ETH")
    assert fl == "ETHUSD_INVERSE" and fs == "ETHUSDT_LINEAL"
    ctx = {"ETHUSD_INVERSE": {"precio": 3000}, "ETHUSDT_LINEAL": {"precio": 3001}}
    assert im.bootstrap_viable(ctx, "ETH")[0]
    pesos = {}
    im.actualizar_promedio(pesos, fl, "LONG", 1.0, 3000)
    pesos[fl]["long"] += 1.0
    im.actualizar_promedio(pesos, fl, "LONG", 1.0, 3100)
    pesos[fl]["long"] += 1.0
    assert round(pesos[fl]["precio_medio_long"], 2) == 3050.0
    res = im.resumen_promedios(pesos)
    assert res and res[0]["frente"] == fl
    print("  bootstrap §E + promedio OK")


def main():
    test_fases_margen()
    test_banda_delta()
    test_resumen_manto()
    test_frentes_manto()
    test_bootstrap_se()
    print("OK igris smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
