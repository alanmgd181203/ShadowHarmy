#!/usr/bin/env python3
"""Smoke Ancla — walk orderbook sintético sin WS."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import ancla


def _libro_ltc():
    asks = [[100.0, 10.0], [100.05, 20.0], [100.10, 50.0]]
    bids = [[99.95, 15.0], [99.90, 25.0], [99.85, 40.0]]
    return {"bids": bids, "asks": asks, "ts": 1.0}


def test_compra_notional():
    fill = ancla.simular_compra_notional_usd(_libro_ltc()["asks"], 500.0)
    assert fill["llenado_usd"] > 400
    assert fill["slippage_pct"] >= 0
    print("  compra OK:", fill["llenado_usd"], "USD slip", fill["slippage_pct"], "%")


def test_entrada_maxima():
    libro = _libro_ltc()
    info = ancla.entrada_maxima_desde_libro(
        libro["bids"], libro["asks"], "LTCUSDT_LINEAL", "BUY", spread_bruto_pct=0.35,
    )
    assert info["entrada_maxima_usd"] > 0
    print("  max OK:", info["entrada_maxima_usd"], "USD")


def test_arbitraje_usdt_usdc():
    libros = {
        "LTCUSDT_SPOT": _libro_ltc(),
        "LTCUSDC_SPOT": {
            "bids": [[100.08, 12.0], [100.04, 30.0]],
            "asks": [[100.12, 12.0], [100.16, 30.0]],
            "ts": 1.0,
        },
    }
    row = {
        "base": "LTC",
        "tipo": "usdt_vs_usdc",
        "spread_pct": 0.45,
        "precio_usdt": 100.0,
        "precio_usdc": 100.45,
    }
    ev = ancla.evaluar_fila_matriz(row, libros, tank_semaforo="VERDE", pipeline_ms=100)
    assert ev is not None
    assert ev["entrada_maxima_usd"] > 0
    assert ev.get("fees_total_pct") is not None
    assert ancla.cumple_regla_neto_vs_fees(
        ev["regalo_neto_pct_est"], ev["fees_total_pct"],
    )
    print("  arbitraje OK: max", ev["entrada_maxima_usd"], "neto", ev["regalo_neto_pct_est"], "%")


def test_consulta_intencion():
    libros = {"BTCUSDT_LINEAL": _libro_ltc()}
    r = ancla.consultar_liquidez_intencion(
        {"general": "GREED", "masa": 200, "frente": "BTCUSDT_LINEAL", "direccion": "LONG"},
        libros,
        tank_semaforo="VERDE",
    )
    assert r["ok"]
    print("  intención OK: max", r["entrada_maxima_usd"], "viable", r.get("masa_viable"))


def test_min_order_par():
    import core.config as config
    config.MIN_ORDER_USD_BY_FRENTE = {
        "LTCUSDT_SPOT": 5.0,
        "LTCUSDC_SPOT": 10.0,
    }
    libros = {
        "LTCUSDT_SPOT": {
            "bids": [[100.0, 0.05]],
            "asks": [[100.05, 0.05]],
            "ts": 1.0,
        },
        "LTCUSDC_SPOT": _libro_ltc(),
    }
    row = {
        "base": "LTC",
        "tipo": "usdt_vs_usdc",
        "spread_pct": 0.28,
        "precio_usdt": 100.0,
        "precio_usdc": 100.12,
    }
    ev = ancla.evaluar_fila_matriz(row, libros, tank_semaforo="VERDE", pipeline_ms=100)
    # Muro fino: max < min cruce (10 USD en USDC leg)
    assert ev is None or ev["entrada_maxima_usd"] >= ev.get("min_order_usd_cruce", 5)
    print("  min_order OK")


def test_reglas_neto_vs_fees():
    assert ancla.cumple_regla_neto_vs_fees(0.20, 0.10)
    assert not ancla.cumple_regla_neto_vs_fees(0.09, 0.10)
    op = {"entrada_maxima_usd": 100, "min_order_usd_cruce": 5,
          "regalo_neto_pct_est": 0.15, "fees_total_pct": 0.10}
    ok, _ = ancla.cumple_reglas_alerta_greed(
        op, pipeline_ms=200, tank_semaforo="VERDE", spread_estable=True,
    )
    assert ok
    ok2, mot = ancla.cumple_reglas_alerta_greed(
        op, pipeline_ms=600, tank_semaforo="VERDE", spread_estable=True,
    )
    assert not ok2 and "PIPELINE" in mot
    print("  reglas neto/fees OK")


def main():
    test_compra_notional()
    test_entrada_maxima()
    test_arbitraje_usdt_usdc()
    test_consulta_intencion()
    test_min_order_par()
    test_reglas_neto_vs_fees()
    print("OK ancla smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
