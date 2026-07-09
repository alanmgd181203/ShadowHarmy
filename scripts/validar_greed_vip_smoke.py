#!/usr/bin/env python3
"""Smoke VIP / Mega VIP — clasificación, techo, escalado."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import greed_vip as vip


def test_clasificacion():
    assert vip.clasificar_modo_vip(0.4) is None
    assert vip.clasificar_modo_vip(0.6) == "VIP"
    assert vip.clasificar_modo_vip(1.2, equity=150) == "MEGA_VIP"
    assert vip.clasificar_modo_vip(1.2, equity=50) == "VIP"
    print("  clasificación OK")


def test_neto_ruta():
    op = {"regalo_neto_pct_est": 0.3}
    ruta = {"regalo_neto_pct": 0.55}
    assert vip.neto_efectivo_ruta(op, ruta) == 0.55
    print("  neto ruta OK")


def test_escalado_sondas():
    plan = {
        "oid": "LTC:usdt_vs_usdc:LTCUSDT_LINEAL",
        "modo_vip": "MEGA_VIP",
        "neto_ruta_pct": 1.1,
        "frente_long": "LTCUSDT_LINEAL",
        "frente_short": "LTCUSDC_LINEAL",
        "base": "LTC",
        "tipo_spread": "usdt_vs_usdc",
        "op": {
            "entrada_maxima_usd": 10000,
            "min_order_usd_cruce": 5,
            "frentes": {"compra": "LTCUSDT_LINEAL", "venta": "LTCUSDC_LINEAL"},
        },
    }
    st = vip.crear_estado_vip(plan, equity=200.0, margen_ocupado_pct=10.0)
    assert st["techo_vip_usd"] >= 5.0
    assert st["techo_mega_usd"] >= st["techo_vip_usd"]
    micro = 5.0
    for i in range(3):
        assert vip.puede_escalar(st)
        st = vip.tras_fill_ok(st, micro, 1.1)
    assert st["mega_desbloqueado"]
    assert vip.techo_activo(st) == st["techo_mega_usd"]
    print("  mega unlock OK:", st["sondas_ok"], "techo", vip.techo_activo(st))


def test_stop_neto():
    assert vip.debe_continuar(0.6)
    assert not vip.debe_continuar(0.4)
    print("  stop neto OK")


def main():
    test_clasificacion()
    test_neto_ruta()
    test_escalado_sondas()
    test_stop_neto()
    print("OK greed vip smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
