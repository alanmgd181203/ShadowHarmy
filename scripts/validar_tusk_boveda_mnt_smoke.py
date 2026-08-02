#!/usr/bin/env python3
"""Smoke frío — bóveda MNT checkpoint (sin API, sin manos)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import tusk_boveda_mnt as bm  # noqa: E402
from core import tusk_tesoreria as tt  # noqa: E402
import core.config as config  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    _assert(not bm.manos_permitidas(), "manos deben estar OFF en smoke")
    _assert(bm.doctrina_activa(), "doctrina on")

    plan = bm.plan_ritual_ideal()
    _assert(len(plan["fases"]) >= 9, "fases ritual")
    _assert(plan["fases"][0]["id"] == "funding_a_uta", "fase1")
    _assert(plan["fases"][2]["id"] == "mejor_camino", "fase3 camino")
    _assert("Convert" in plan["fases"][2]["desc"] and "spot" in plan["fases"][2]["desc"], "ley convert/spot")
    _assert(plan.get("no_fundir_manos_aun") is True, "no manos aun")

    pot100 = bm.potencia_pase_desde_mando(100.0)
    _assert(pot100["potencia_n"] == 4, pot100)
    _assert(pot100["ultimo_paso"] and pot100["ultimo_paso"]["n"] == 4, pot100)

    # Short 500 MNT @ 0.20 → capital mando 100
    hedges = [{
        "symbol": "MNTUSD",
        "base": "MNT",
        "side": "SHORT",
        "size": 500.0,
        "avg_price": 0.20,
        "mark_price": 0.201,
        "notional_usd": 100.5,
        "category": "inverse",
    }]
    mando = bm.capital_mando_desde_hedge(hedges)
    _assert(mando["ok"], mando)
    _assert(abs(mando["capital_mando_usd"] - 100.0) < 0.01, f"mando={mando}")
    _assert(mando["fuente"] == "size_x_avg", mando)

    foto = bm.foto_precios_mnt(spot_mark=0.2001, inverse_mark=0.20)
    _assert(foto["spread_spot_menos_inverse"] is not None, "spread")
    _assert(foto["spread_spot_menos_inverse"] > 0, "spot un poco arriba")

    eq = bm.equilibrio_spot_short(100.01, 99.8, tolerancia_pct=0.03)
    _assert(eq["dentro_tolerancia"], eq)
    _assert(eq["sesgo"] == "favor_spot", eq)

    eq2 = bm.equilibrio_spot_short(90.0, 100.0, tolerancia_pct=0.03)
    _assert(eq2["sesgo"] == "favor_short", eq2)
    _assert(not eq2["dentro_tolerancia"], eq2)

    bloque = bm.construir_bloque_boveda_mnt(
        mnt_usd=100.01, hedges=hedges, spot_mark=0.2001, equity_vivo=100.5,
    )
    _assert(bloque["manos_permitidas"] is False, "manos off en bloque")
    _assert(bloque["capital_mando"]["ok"], bloque["capital_mando"])
    _assert(bloque["potencia_pase"]["potencia_n"] == 4, bloque["potencia_pase"])

    # Integración tesorería simulada
    snap = tt.tesoreria_simulada(
        1500.0, disponible=1470.0, mnt_usd=1470.0, hedge_notional=1460.0, hedge_im=30.0,
    )
    # Inyectar avg en hedge del sim
    if snap.get("hedge_shorts"):
        snap["hedge_shorts"][0]["avg_price"] = 0.2
        snap["hedge_shorts"][0]["size"] = 7300.0
        snap["hedge_shorts"][0]["category"] = "inverse"
        snap["hedge_shorts"][0]["symbol"] = "MNTUSD"
    # reconstruir bloque
    if "boveda_mnt" not in snap:
        # tesoreria_simulada llama construir_tesoreria — debe traer boveda_mnt
        pass
    snap2 = tt.construir_tesoreria(
        {
            "totalEquity": 1500,
            "totalAvailableBalance": 1470,
            "totalInitialMargin": 30,
            "totalMaintenanceMargin": 15,
            "accountMMRate": 0.01,
            "accountIMRate": 0.02,
            "coin": [
                {"coin": "MNT", "usdValue": 1470, "equity": 7350, "walletBalance": 7350},
            ],
        },
        posiciones=[{
            "symbol": "MNTUSD",
            "side": "Sell",
            "size": 7300,
            "avgPrice": 0.2,
            "markPrice": 0.201,
            "positionValue": 1467.3,
            "positionIM": 30,
            "leverage": 50,
            "_category": "inverse",
        }],
    )
    _assert("boveda_mnt" in snap2, "falta boveda_mnt")
    _assert(snap2["boveda_mnt"]["manos_permitidas"] is False, "manos")
    _assert(snap2["boveda_mnt"]["capital_mando"]["ok"], snap2["boveda_mnt"]["capital_mando"])
    _assert(
        abs(snap2["boveda_mnt"]["capital_mando"]["capital_mando_usd"] - 1460.0) < 0.05,
        snap2["boveda_mnt"]["capital_mando"],
    )

    print("PASS tusk_boveda_mnt smoke (frío, sin manos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
