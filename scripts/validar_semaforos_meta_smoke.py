#!/usr/bin/env python3
"""Smoke luces matriz Kaiser 3.7.P1 + meta engorde pase → Igris."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import kaiser_indicators as ki
from core import pase_director as pd


def test_luces_matriz():
    umbral = 0.25
    snap = {
        "filas": [
            {"base": "AAA", "tipo": "spot_vs_perp", "spread_pct": 0.10},
            {"base": "BBB", "tipo": "lineal_vs_inverse", "spread_pct": 0.30},
            {"base": "CCC", "tipo": "usdt_vs_usdc", "spread_pct": 0.60},
        ]
    }
    luces = ki.luces_matriz(snap)
    assert luces[0]["luz"] == "VERDE"
    assert luces[1]["luz"] == "AMARILLO"
    assert luces[2]["luz"] == "ROJO"
    assert luces[1]["destinatario"] == "IGRIS"
    assert luces[2]["destinatario"] == "GREED"
    alertas = ki.interpretar_matriz(snap)
    assert len(alertas) == 2  # solo ≥ umbral
    assert alertas[0]["datos"]["luz"] in ("AMARILLO", "ROJO")
    print("  luces matriz V/A/R OK", [x["luz"] for x in luces])


def test_meta_engorde():
    class FakeTusk:
        pesos = {}

    # Equity con potencia ≥1, sin notional → restante = delta * fill
    eq = 14.0
    plan = pd.plan_lote(eq, marcha_id="tactico", pasos_logrados=[])
    assert plan["foco"]["activo"] == "ETH"
    fill = float(plan["fill_ratio"])
    need = float(plan["foco"]["delta_usd"])
    meta = pd.meta_engorde_usd(eq, "ETH", tusk=FakeTusk(), marcha_id="tactico", pasos_logrados=[])
    assert meta["ok"] is True
    assert abs(meta["need_usd"] - need) < 1e-6
    assert abs(meta["restante_usd"] - need * fill) < 1e-6
    assert meta["mitad_alcanzada"] is False

    # Simular manto ya cubierto
    class FullTusk:
        pesos = {
            "ETHUSD_INVERSE": {"long": need * fill, "precio_medio_long": 1.0},
            "ETHUSDT_LINEAL": {"short": 0.0, "precio_medio_short": 1.0},
        }

    # notional = masa * px; long masa = need*fill with px=1 → have = need*fill
    meta2 = pd.meta_engorde_usd(eq, "ETH", tusk=FullTusk(), marcha_id="tactico", pasos_logrados=[])
    assert meta2["restante_usd"] <= 1e-6
    print("  meta_engorde OK", meta["restante_usd"], "->", meta2["restante_usd"])


def main():
    print("[SMOKE] 3.7.P1 luces + meta engorde pase")
    test_luces_matriz()
    test_meta_engorde()
    print("[OK] semaforos_meta smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
