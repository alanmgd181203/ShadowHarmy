#!/usr/bin/env python3
"""Smoke Beru capital — fricción directa (sin ×8 sobre X)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc
from core import beru_tier
import core.config as config


def test_eth_btc_friccion_directa():
    # Pin G_min=5 para aritmética legado (smoke aislado del sync vivo)
    from core import g_min as gm

    old_path = gm.PATH_MINIMOS
    import tempfile, json
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as td:
        mock = P(td) / "bybit_minimos_orden.json"
        mock.write_text(
            json.dumps({
                "meta": {},
                "activos": {
                    "ETH": {"G_min": 5.0, "G_min_fuente": "mock", "spot_usdt": {"min_usd_est": 5.0}},
                    "BTC": {"G_min": 5.0, "G_min_fuente": "mock", "spot_usdt": {"min_usd_est": 5.0}},
                },
            }),
            encoding="utf-8",
        )
        gm.PATH_MINIMOS = mock
        gm.invalidar_cache()
        # G_min=5, lev=100 → Soldado ceil 14 · Capitán round 26 · General 53 · Mariscal 105
        for asset in ("ETH", "BTC"):
            r = bc.rangos_activo(asset)
            assert r["X"] == 14
            assert r["SOLDADO"] == (14, 25)
            assert r["CAPITAN"] == (26, 52)
            assert r["GENERAL"] == (53, 104)
            assert r["MARISCAL"] == 105
            assert r["costos_friccion"]["MARISCAL"] == 105
            assert (1.0 - r["margen_volumen_base_usd"] / r["X"]) >= 0.05 - 1e-9
        print("  ETH/BTC Mariscal=105 (friccion 0.1% directa) OK · reserva>=5%")
        gm.PATH_MINIMOS = old_path
        gm.invalidar_cache()


def test_sin_escalares_sobre_x():
    r = bc.rangos_activo("BTC")
    assert r["MARISCAL"] != 8 * r["X"]
    assert r["CAPITAN"][0] != 2 * r["X"]
    print("  prohibido 2X/4X/8X: OK")


def test_friccion_ley():
    assert abs(bc.friccion_grado_pct("SOLDADO") - 0.008) < 1e-9
    assert abs(bc.friccion_grado_pct("CAPITAN") - 0.004) < 1e-9
    assert abs(bc.friccion_grado_pct("GENERAL") - 0.002) < 1e-9
    assert abs(bc.friccion_grado_pct("MARISCAL") - 0.001) < 1e-9
    print("  fricción 0.8/0.4/0.2/0.1 OK")


def test_grado_por_equity():
    from core import g_min as gm
    import tempfile, json
    from pathlib import Path as P

    old_path = gm.PATH_MINIMOS
    with tempfile.TemporaryDirectory() as td:
        mock = P(td) / "bybit_minimos_orden.json"
        mock.write_text(
            json.dumps({
                "meta": {},
                "activos": {"ETH": {"G_min": 5.0, "spot_usdt": {"min_usd_est": 5.0}}},
            }),
            encoding="utf-8",
        )
        gm.PATH_MINIMOS = mock
        gm.invalidar_cache()
        assert bc.grado_en_rango(10, "ETH") == "BLOQUEADO"
        assert bc.grado_en_rango(20, "ETH") == "SOLDADO"
        assert bc.grado_en_rango(30, "ETH") == "CAPITAN"
        assert bc.grado_en_rango(60, "ETH") == "GENERAL"
        assert bc.grado_en_rango(105, "ETH") == "MARISCAL"
        print("  grados por equity OK")
        gm.PATH_MINIMOS = old_path
        gm.invalidar_cache()


def test_cola_graduacion():
    from core import g_min as gm
    import tempfile, json
    from pathlib import Path as P

    old_path = gm.PATH_MINIMOS
    with tempfile.TemporaryDirectory() as td:
        mock = P(td) / "bybit_minimos_orden.json"
        mock.write_text(
            json.dumps({
                "meta": {},
                "activos": {
                    "ETH": {"G_min": 5.0, "spot_usdt": {"min_usd_est": 5.0}},
                    "SOL": {"G_min": 5.0, "spot_usdt": {"min_usd_est": 5.0}},
                },
            }),
            encoding="utf-8",
        )
        gm.PATH_MINIMOS = mock
        gm.invalidar_cache()
        cola = bc.cola_activos_con_a_base(["ETH", "SOL"])
        assert cola[0]["A_base"] == 0
        assert cola[1]["A_base"] == cola[0]["A_base_siguiente"] == 105
        print("  cola A_base ETH->SOL OK", f"SOL X={cola[1]['X']} A_base={cola[1]['A_base']}")
        gm.PATH_MINIMOS = old_path
        gm.invalidar_cache()


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


def test_im_pierna_a_pierna_sin_promedio():
    """LINK Mariscal: IM = 5000/20 + 5000/50 = 350 (no 10000/35)."""
    det = bc.margen_piernas_para_friccion("LINK", bc.friccion_grado_pct("MARISCAL"))
    assert abs(det["im_inverse_usd"] - 250.0) < 1e-6
    assert abs(det["im_linear_usd"] - 100.0) < 1e-6
    assert abs(det["im_total_usd"] - 350.0) < 1e-6
    assert bc.costo_grado("LINK", "MARISCAL") == 368  # 350/0.95
    print("  IM pierna-a-pierna LINK Mariscal=350 OK")


def test_im_avax_op_tabla():
    """AVAX/OP Mariscal: IM = pierna/lev_inv + pierna/lev_lin (tabla)."""
    for asset in ("AVAX", "OP", "LINK"):
        fric = bc.friccion_grado_pct("MARISCAL")
        det = bc.margen_piernas_para_friccion(asset, fric)
        pierna = float(det["notional_pierna_usd"])
        expect = pierna / float(det["lev_inverse"]) + pierna / float(det["lev_linear"])
        assert abs(float(det["im_total_usd"]) - expect) < 1e-6
        print(f"  IM tabla {asset}={expect:.1f} OK")


def main():
    print("[SMOKE] Beru capital — fricción directa")
    test_eth_btc_friccion_directa()
    test_sin_escalares_sobre_x()
    test_friccion_ley()
    test_grado_por_equity()
    test_cola_graduacion()
    test_telemetria_cero()
    test_capitanes_config()
    test_tiers_pasos()
    test_im_pierna_a_pierna_sin_promedio()
    test_im_avax_op_tabla()
    print("OK beru capital smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
