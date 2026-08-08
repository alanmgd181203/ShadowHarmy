#!/usr/bin/env python3
"""Smoke frío — G_min variable por Santo (mock archivo) + capital Soldado escala."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc
from core import beru_cazador
from core import g_min as gm
import core.config as config


def _escribir_mock(path: Path, eth_g: float, btc_g: float = 5.0) -> None:
    payload = {
        "meta": {"fuente": "mock_smoke", "piso_configurable": 1.0},
        "activos": {
            "ETH": {
                "spot_usdt": {"min_usd_est": eth_g, "minNotional": eth_g},
                "linear": {"min_usd_est": 5.0},
                "inverse": {"min_usd_est": 1.0},
                "G_min": eth_g,
                "G_min_fuente": "spot_usdt",
            },
            "BTC": {
                "spot_usdt": {"min_usd_est": btc_g, "minNotional": btc_g},
                "linear": {"min_usd_est": 5.0},
                "G_min": btc_g,
                "G_min_fuente": "spot_usdt",
            },
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_lectura_por_activo_mock():
    with tempfile.TemporaryDirectory() as td:
        mock = Path(td) / "bybit_minimos_orden.json"
        _escribir_mock(mock, eth_g=1.0, btc_g=5.0)
        old = gm.PATH_MINIMOS
        try:
            gm.PATH_MINIMOS = mock
            gm.invalidar_cache()
            assert abs(gm.g_min_usd("ETH") - 1.0) < 1e-9
            assert abs(gm.g_min_usd("BTC") - 5.0) < 1e-9
            det = gm.detalle_g_min("ETH")
            assert det["hay_dato_archivo"] is True
            assert det["fuente_pierna"] == "spot_usdt"
            print("  lectura mock ETH=1 BTC=5 OK")
        finally:
            gm.PATH_MINIMOS = old
            gm.invalidar_cache()


def test_soldado_escala_con_gmin():
    """Soldado ETH con G_min=1 debe ser ~1/5 del capital con G_min=5 (mismo lev)."""
    with tempfile.TemporaryDirectory() as td:
        mock = Path(td) / "bybit_minimos_orden.json"
        old_path = gm.PATH_MINIMOS
        old_mordida = config.BERU_CAZADOR_MORDIDA_USD
        try:
            config.BERU_CAZADOR_MORDIDA_USD = 0.0  # auto G_min
            gm.PATH_MINIMOS = mock

            _escribir_mock(mock, eth_g=5.0)
            gm.invalidar_cache()
            x5 = bc.costo_base_x("ETH")
            assert abs(bc.g_min_usd("ETH") - 5.0) < 1e-9

            _escribir_mock(mock, eth_g=1.0)
            gm.invalidar_cache()
            x1 = bc.costo_base_x("ETH")
            assert abs(bc.g_min_usd("ETH") - 1.0) < 1e-9
            # ceil: X(1) ≈ X(5)/5 (±1 por redondeo)
            assert x1 < x5
            assert abs(x1 * 5 - x5) <= 2, (x1, x5)
            assert abs(beru_cazador.mordida_usd("ETH") - 1.0) < 1e-9
            print(f"  Soldado ETH escala: G_min5->X={x5} · G_min1->X={x1} OK")
        finally:
            gm.PATH_MINIMOS = old_path
            config.BERU_CAZADOR_MORDIDA_USD = old_mordida
            gm.invalidar_cache()


def test_override_mordida():
    old = config.BERU_CAZADOR_MORDIDA_USD
    try:
        config.BERU_CAZADOR_MORDIDA_USD = 20.0
        assert abs(beru_cazador.mordida_usd("ETH") - 20.0) < 1e-9
        print("  override mordida $20 OK")
    finally:
        config.BERU_CAZADOR_MORDIDA_USD = old


def test_piso_configurable():
    with tempfile.TemporaryDirectory() as td:
        mock = Path(td) / "bybit_minimos_orden.json"
        payload = {
            "meta": {},
            "activos": {
                "ETH": {
                    "spot_usdt": {"min_usd_est": 0.5},
                    "G_min": 0.5,
                    "G_min_fuente": "spot_usdt",
                }
            },
        }
        mock.write_text(json.dumps(payload), encoding="utf-8")
        old_path = gm.PATH_MINIMOS
        old_piso = config.G_MIN_USD_PISO
        try:
            config.G_MIN_USD_PISO = 1.0
            gm.PATH_MINIMOS = mock
            gm.invalidar_cache()
            assert abs(gm.g_min_usd("ETH") - 1.0) < 1e-9
            print("  piso 1.0 sobre bruto 0.5 OK")
        finally:
            gm.PATH_MINIMOS = old_path
            config.G_MIN_USD_PISO = old_piso
            gm.invalidar_cache()


def main():
    print("[SMOKE] G_min variable por Santo")
    test_lectura_por_activo_mock()
    test_soldado_escala_con_gmin()
    test_override_mordida()
    test_piso_configurable()
    print("OK g_min variable smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
