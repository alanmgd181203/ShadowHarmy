#!/usr/bin/env python3
"""
Smoke Sub-Santuario Igris — core/igris_asset_detail.py

Verifica:
  A) Estado cero (reposo) — todos 0 / NEUTRO / REPOSO
  B) Simulador con piernas L/S — tamaños, ancla, 1%, desequilibrio
  C) Optimización Igris vs baseline
  D) Fase CRECIMIENTO / REDUCCION
  E) desde_estado_vivo con pesos vacíos y con pesos

Uso: python scripts/validar_igris_asset_detail_smoke.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import igris_asset_detail as ad  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_cero() -> None:
    s = ad.snapshot_cero("BTC")
    _assert(s["symbol"] == "BTC", "symbol")
    _assert(s["fuente"] == "cero", "fuente cero")
    _assert(s["long"]["size_usd"] == 0 and s["short"]["size_usd"] == 0, "sizes 0")
    _assert(s["global"]["entry_avg"] == 0, "ancla 0")
    _assert(s["desequilibrio"]["beneficio"] == "NEUTRO", "neutro")
    _assert(s["fase_manto"]["estado"] == "REPOSO", "reposo")
    _assert(s["long"]["leverage_max"] > 0, "lev max long catalogado")
    _assert(s["short"]["leverage_max"] > 0, "lev max short catalogado")
    _assert(s["long"]["leverage_actual"] is None, "lev actual no inventado")
    print("  A) estado cero OK")


def test_simulador_piernas() -> None:
    pesos = {
        "BTCUSD_INVERSE": {
            "long": 1000.0,
            "short": 0.0,
            "precio_medio_long": 100.0,
            "precio_medio_short": 0.0,
        },
        "BTCUSDT_LINEAL": {
            "long": 0.0,
            "short": 1000.0,
            "precio_medio_long": 0.0,
            "precio_medio_short": 99.5,
        },
    }
    marks = {"BTCUSD_INVERSE": 100.2, "BTCUSDT_LINEAL": 99.8}
    s = ad.construir_asset_detail(
        "BTC",
        pesos=pesos,
        marks=marks,
        igris_bloque={"fase_margen": "EXPANSION", "accion_heuristica": "ENGORDAR_MANTO"},
        progresion={"grado_beru": "CAPITAN", "rango_ejercito": "Nivel 2 / Aprendiz"},
        margen_im={"long": 10.0, "short": 9.9},
        fees_paid={"long": 0.12, "short": 0.11},
        leverage_actual={"long": 50, "short": 25},
    )
    _assert(s["fuente"] == "pesos", "fuente pesos")
    _assert(abs(s["long"]["size_usd"] - 1000) < 1e-6, "long usd")
    _assert(abs(s["short"]["size_usd"] - 1000) < 1e-6, "short usd")
    _assert(abs(s["long"]["size_base"] - 10.0) < 1e-6, "long base 1000/100")
    _assert(abs(s["short"]["entry_price"] - 99.5) < 1e-6, "short entry")
    _assert(abs(s["global"]["margen_usd"] - 19.9) < 1e-6, "margen conjunto")
    _assert(abs(s["global"]["impacto_1pct_usd"] - 20.0) < 1e-6, "1% global 10+10")
    _assert(abs(s["long"]["impacto_1pct_usd"] - 10.0) < 1e-6, "1% long")
    _assert(s["desequilibrio"]["puntos"] != 0, "delta mark")
    _assert(s["fase_manto"]["estado"] == "CRECIMIENTO", "crecimiento")
    _assert(s["fase_manto"]["grado_beru"] == "CAPITAN", "grado")
    _assert(s["long"]["leverage_actual"] == 50, "lev actual long")
    _assert(abs(s["global"]["fees_paid_usd"] - 0.23) < 1e-6, "fees suma")
    # Ancla = promedio ponderado 100 y 99.5 con masas iguales → 99.75
    _assert(abs(s["global"]["entry_avg"] - 99.75) < 1e-6, f"ancla {s['global']['entry_avg']}")
    print("  B) simulador piernas OK")


def test_optimizacion() -> None:
    pesos = {
        "ETHUSD_INVERSE": {
            "long": 500.0, "short": 0.0,
            "precio_medio_long": 3000.0, "precio_medio_short": 0.0,
        },
        "ETHUSDT_LINEAL": {
            "long": 0.0, "short": 500.0,
            "precio_medio_long": 0.0, "precio_medio_short": 3010.0,
        },
    }
    s = ad.construir_asset_detail(
        "ETH",
        pesos=pesos,
        baselines={"long": 3010.0, "short": 3000.0},
    )
    # LONG mejoró: baseline 3010 → 3000 = +10 pts
    _assert(s["optimizacion_igris"]["mejora_pts_long"] > 0, "mejora long")
    # SHORT mejoró: baseline 3000 → 3010 = +10 pts (short quiere vender más alto)
    _assert(s["optimizacion_igris"]["mejora_pts_short"] > 0, "mejora short")
    print("  C) optimización Igris OK")


def test_reduccion() -> None:
    pesos = {
        "LTCUSD_INVERSE": {"long": 100.0, "short": 0.0, "precio_medio_long": 80.0, "precio_medio_short": 0},
        "LTCUSDT_LINEAL": {"long": 0.0, "short": 100.0, "precio_medio_long": 0, "precio_medio_short": 80.0},
    }
    s = ad.construir_asset_detail(
        "LTC",
        pesos=pesos,
        igris_bloque={"fase_margen": "LEY_MARCIAL", "accion_heuristica": "PODAR_MANTO"},
    )
    _assert(s["fase_manto"]["estado"] == "REDUCCION", "reduccion")
    print("  D) fase reducción OK")


def test_estado_vivo() -> None:
    vacio = ad.desde_estado_vivo("SOL", {})
    _assert(vacio["fuente"] == "cero", "vivo vacío → cero")
    snap = {
        "pesos_por_frente": {
            "SOLUSD_INVERSE": {
                "long": 200.0, "short": 0, "precio_medio_long": 150.0, "precio_medio_short": 0,
                "baseline_long": 152.0, "baseline_short": 0,
                "fees_paid_long": 0.05, "fees_paid_short": 0,
            },
            "SOLUSDT_LINEAL": {
                "long": 0, "short": 200.0, "precio_medio_long": 0, "precio_medio_short": 149.0,
                "baseline_long": 0, "baseline_short": 148.0,
                "fees_paid_long": 0, "fees_paid_short": 0.04,
            },
        },
        "igris": {"fase_margen": "TERRENO_CAZA", "accion_heuristica": "VIGILAR_IGRIS"},
        "grado_beru": "SOLDADO",
        "rango_ejercito": "Nivel 1 / Aspirante",
        "inverse_perp": {"detalle": {"SOLUSD_INVERSE": {"precio": 150.5}}},
        "linear_perp": {"detalle": {"SOLUSDT_LINEAL": {"precio": 149.8}}},
        "igris_posiciones": {
            "fuente": "exchange",
            "por_activo": {
                "SOL": {
                    "long": {
                        "symbol": "SOLUSD",
                        "frente": "SOLUSD_INVERSE",
                        "margen_usd": 4.0,
                        "leverage": 10.0,
                        "mark_price": 150.5,
                    },
                    "short": {
                        "symbol": "SOLUSDT",
                        "frente": "SOLUSDT_LINEAL",
                        "margen_usd": 3.5,
                        "leverage": 5.0,
                        "mark_price": 149.8,
                    },
                }
            },
        },
    }
    s = ad.desde_estado_vivo("SOL", snap)
    _assert(s["fuente"] == "pesos", "vivo con pesos")
    _assert(s["global"]["size_usd_total"] == 400.0, "total")
    _assert(s["fase_manto"]["grado_beru"] == "SOLDADO", "grado desde snap")
    _assert(abs(s["global"]["margen_usd"] - 7.5) < 1e-6, f"margen bridge {s['global']['margen_usd']}")
    _assert(s["long"]["leverage_actual"] == 10.0, "lev long bridge")
    _assert(s["short"]["leverage_actual"] == 5.0, "lev short bridge")
    _assert(abs(s["long"]["mark_price"] - 150.5) < 1e-6, "mark tank/bridge")
    _assert(abs(s["global"]["fees_paid_usd"] - 0.09) < 1e-6, "fees pesos")
    _assert(s["long"]["entry_baseline"] == 152.0, "baseline long")
    _assert(s["optimizacion_igris"]["mejora_pts_long"] > 0, "mejora vs baseline")
    _assert(s["desequilibrio"]["beneficio"] in ("FAVOR", "CONTRA", "NEUTRO"), "beneficio")
    print("  E) desde_estado_vivo OK (Bridge+Tank+baseline)")


def test_telemetria_enrich() -> None:
    from core import telemetria_igris as ti

    posiciones = [
        {
            "symbol": "BTCUSD",
            "side": "Buy",
            "size": "0.01",
            "avgPrice": "100000",
            "positionIM": "20",
            "leverage": "50",
            "markPrice": "100100",
            "positionValue": "1000",
        },
        {
            "symbol": "BTCUSDT",
            "side": "Sell",
            "size": "0.01",
            "avgPrice": "99900",
            "positionIM": "19.5",
            "leverage": "25",
            "markPrice": "99950",
            "positionValue": "999",
        },
    ]
    t = ti.telemetria_desde_exchange(posiciones, equity_usd=1000.0)
    _assert(t["fuente"] == "exchange", "fuente exchange")
    _assert(t["long"]["margen_usd"] == 20.0, "IM long publicado")
    _assert(t["long"]["leverage"] == 50.0, "lev long")
    _assert("BTC" in t["por_activo"], "por_activo BTC")
    _assert(t["por_activo"]["BTC"]["short"]["leverage"] == 25.0, "lev short por activo")
    print("  F) telemetria enrich OK")


def main() -> int:
    print("validar_igris_asset_detail_smoke:")
    test_cero()
    test_simulador_piernas()
    test_optimizacion()
    test_reduccion()
    test_estado_vivo()
    test_telemetria_enrich()
    print("OK (6 escenarios)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
