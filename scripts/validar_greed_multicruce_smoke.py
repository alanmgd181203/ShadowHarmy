#!/usr/bin/env python3
"""Smoke Greed multicruce — detección triangular + plan."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import greed_multicruce as mc
from core import greed_mision as mision
from core import metaverso_grafo as mv
import core.config as config


def _precios_mnt_eth():
    """ETH/USDT directo vs vía MNT con desvío artificial."""
    return {
        "ETHUSDT_SPOT": 3000.0,
        "ETHMNT_SPOT": 4200.0,
        "MNTUSDT_SPOT": 0.68,
        "USDCUSDT_SPOT": 1.0002,
        "ETHUSDC_SPOT": 2998.0,
        "USDCEUR_SPOT": 0.92,
        "ETHEUR_SPOT": 2780.0,
    }


def test_detecta_via_mnt():
    precios = _precios_mnt_eth()
    # sintético = 4200 * 0.68 = 2856 < 3000 → spread ~4.8%
    filas = mc.calcular_filas_multicruce(precios, umbral_pct=0.1)
    mnt = next((f for f in filas if f["base"] == "ETH" and f["via_quote"] == "MNT"), None)
    assert mnt is not None, filas
    assert mnt["n_piernas"] == 3
    assert len(mnt["piernas"]) == 3
    assert mnt["spread_pct"] > 0.1
    print("  ETH via MNT 3p OK spread", mnt["spread_pct"])


def test_piernas_direccion():
    idx = mc.SpotIndex(_precios_mnt_eth())
    piernas = mc._piernas_via_mnt("ETH", idx, sintetico_barato=True)
    assert piernas[0]["side"] == "Buy"
    assert piernas[-1]["side"] == "Sell"
    print("  piernas MNT dirección OK")


def test_metaverso_rank():
    filas = mc.calcular_filas_multicruce(_precios_mnt_eth(), umbral_pct=0.05)
    ranked = mv.rankear_multicruces(filas, "ETH")
    assert ranked
    assert ranked[0].get("via_quote") in ("MNT", "USDC", "EUR")
    print("  metaverso rank OK", ranked[0]["ruta_id"])


def test_plan_mision():
    op = {
        "base": "ETH",
        "tipo_spread": "multicruce_3p",
        "via_quote": "MNT",
        "entrada_maxima_usd": 500,
        "min_order_usd_cruce": 5,
        "regalo_neto_pct_est": 0.35,
        "piernas": [
            {"frente": "MNTUSDT_SPOT", "side": "Buy"},
            {"frente": "ETHMNT_SPOT", "side": "Buy"},
            {"frente": "ETHUSDT_SPOT", "side": "Sell"},
        ],
        "frentes": {"compra": "MNTUSDT_SPOT", "venta": "ETHUSDT_SPOT", "todos": [
            "MNTUSDT_SPOT", "ETHMNT_SPOT", "ETHUSDT_SPOT",
        ]},
    }
    digest = {
        "metaverso": {"ETH": {"ruta_idonea": {"regalo_neto_pct": 0.3}}},
        "perfiles": {
            "ETH": {
                "usdt_vs_usdc": {
                    "etiquetas_resumen": ["REVIERTE_RAPIDO"],
                    "plazos": {
                        "mediano": {"etiquetas": ["NEUTRO"], "metricas": {"mean_signed_pct": 0.0}},
                    },
                },
            },
        },
        "pipeline": {"total_ms": 120},
    }
    plan = mision.resolver_plan(
        op, digest,
        equity=2000.0,
        margen_ocupado_pct=30.0,
        masa_autorizada=50.0,
        tank_semaforo="VERDE",
    )
    assert plan.get("ok"), plan
    assert plan.get("n_piernas") == 3
    assert plan.get("piernas")
    print("  plan multicruce OK oid", plan["oid"])


def test_config_enabled():
    assert config.GREED_MULTICRUCE_ENABLED
    assert "MNT" in config.GREED_MULTICRUCE_VIA_QUOTES
    print("  config multicruce OK")


def main():
    test_config_enabled()
    test_detecta_via_mnt()
    test_piernas_direccion()
    test_metaverso_rank()
    test_plan_mision()
    print("OK greed multicruce smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
