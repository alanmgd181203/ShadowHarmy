#!/usr/bin/env python3
"""
Smoke Tusk tesorería — core/tusk_tesoreria.py

  A) MNT + hedge 50x → IM ~2%, oxígeno ≈ disponible × (1−reserva)
  B) estado sana/justa/ahogada
  C) Tusk.actualizar_nav_real con wallet_account

Uso: python scripts/validar_tusk_tesoreria_smoke.py
"""
from __future__ import annotations

import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import tusk_tesoreria as tt  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_mnt_hedge() -> None:
    # $1500 equity, $1500 MNT, short $1500 @ 50x → IM $30, disponible ~1470
    snap = tt.tesoreria_simulada(
        1500.0,
        disponible=1470.0,
        mnt_usd=1500.0,
        hedge_notional=1500.0,
        hedge_im=30.0,
        leverage=50.0,
    )
    _assert(snap["mnt_usd"] == 1500.0, "mnt")
    _assert(abs(snap["im_hedge_usd"] - 30.0) < 0.01, f"im {snap['im_hedge_usd']}")
    _assert(snap["hedge_match_ok"] is True, "match")
    res = snap["reserva_monarca_pct"]
    ox = 1470.0 * (1.0 - res)
    _assert(abs(snap["oxigeno_guerra_usd"] - ox) < 0.05, f"ox {snap['oxigeno_guerra_usd']} vs {ox}")
    _assert(snap["estado"] in ("sana", "justa"), snap["estado"])
    print("  A) MNT+hedge OK")


def test_estados() -> None:
    _assert(tt.estado_tesoreria(equity=100, disponible=80, mm_rate=0.1) == "sana", "sana")
    _assert(tt.estado_tesoreria(equity=100, disponible=30, mm_rate=0.2) == "justa", "justa")
    _assert(tt.estado_tesoreria(equity=100, disponible=10, mm_rate=0.9) == "ahogada", "ahogada")
    print("  B) estados OK")


async def test_tusk_nav() -> None:
    bel = BellionAuditor()
    tusk = TuskBoveda(bel)
    account = {
        "totalEquity": 1500.0,
        "totalAvailableBalance": 1470.0,
        "totalInitialMargin": 30.0,
        "totalMaintenanceMargin": 15.0,
        "accountMMRate": 0.01,
        "accountIMRate": 0.02,
        "coin": [
            {"coin": "MNT", "usdValue": 1500, "equity": 1500, "walletBalance": 1500},
        ],
    }
    posiciones = [{
        "symbol": "MNTUSDT", "side": "Sell", "size": 100, "positionValue": 1500,
        "positionIM": 30, "leverage": 50, "unrealisedPnl": 0, "liqPrice": 2.0,
        "_category": "linear",
    }]
    await tusk.actualizar_nav_real(
        1500.0, 2.0,
        total_maintenance_margin=15.0,
        account_mm_rate=0.01,
        disponible_uta=1470.0,
        wallet_account=account,
        posiciones=posiciones,
    )
    _assert(tusk.tesoreria is not None, "tesoreria")
    _assert(tusk.tesoreria.get("hedge_match_ok") is True, "match tusk")
    ox = float(tusk.masa_autorizada)
    _assert(ox > 1000, f"masa auth should be oxygen ~1396 not escalon/10, got {ox}")
    snap = tusk.snapshot_tesoreria()
    _assert(snap.get("oxigeno_guerra_usd", 0) > 1000, "snapshot ox")
    print("  C) tusk NAV OK")


def main() -> None:
    print("Smoke Tusk tesorería")
    test_mnt_hedge()
    test_estados()
    asyncio.run(test_tusk_nav())
    print("PASS 3/3")


if __name__ == "__main__":
    main()
