#!/usr/bin/env python3
"""
Smoke Tusk tesorería — core/tusk_tesoreria.py

  A) MNT + hedge 50x → IM ~2% dentro del colchón 5% → O2 = equity×0.95
  B) Si ya_reservado > colchón, no se resta extra
  C) estados + Tusk.actualizar_nav_real

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


def test_mnt_hedge_dentro_colchon() -> None:
    # $1500 equity, IM hedge $30 (2%), disponible 1470, reserva 5% → colchón $75
    # extra = 75-30 = 45 · O2 = 1470-45 = 1425 (= equity×0.95)
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
    _assert(abs(snap["colchon_objetivo_usd"] - 75.0) < 0.05, "colchon 75")
    _assert(abs(snap["ya_reservado_usd"] - 30.0) < 0.05, "ya 30")
    _assert(abs(snap["extra_colchon_usd"] - 45.0) < 0.05, "extra 45")
    _assert(abs(snap["oxigeno_guerra_usd"] - 1425.0) < 0.05, f"ox {snap['oxigeno_guerra_usd']}")
    # No double-count: must NOT be 1470*0.95 = 1396.5
    _assert(snap["oxigeno_guerra_usd"] > 1400.0, "no double count")
    print("  A) hedge dentro del colchon OK")


def test_hedge_come_mas_que_colchon() -> None:
    # ya_reservado 100 > colchón 75 → O2 = disponible (sin extra)
    o2 = tt.oxigeno_guerra_usd(1500.0, 1400.0, reserva_pct=0.05)
    _assert(abs(o2["colchon_objetivo_usd"] - 75.0) < 0.01, "colchon")
    _assert(abs(o2["ya_reservado_usd"] - 100.0) < 0.01, "ya")
    _assert(o2["extra_colchon_usd"] == 0.0, "extra 0")
    _assert(abs(o2["oxigeno_guerra_usd"] - 1400.0) < 0.01, "ox=disp")
    print("  B) hedge > colchon OK")


def test_estados() -> None:
    _assert(tt.estado_tesoreria(equity=100, disponible=80, mm_rate=0.1) == "sana", "sana")
    _assert(tt.estado_tesoreria(equity=100, disponible=30, mm_rate=0.2) == "justa", "justa")
    _assert(tt.estado_tesoreria(equity=100, disponible=10, mm_rate=0.9) == "ahogada", "ahogada")
    print("  C) estados OK")


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
    ox = float(tusk.masa_autorizada)
    _assert(abs(ox - 1425.0) < 0.1, f"masa auth 1425, got {ox}")
    print("  D) tusk NAV OK")


def main() -> None:
    print("Smoke Tusk tesorería (colchón)")
    test_mnt_hedge_dentro_colchon()
    test_hedge_come_mas_que_colchon()
    test_estados()
    asyncio.run(test_tusk_nav())
    print("PASS 4/4")


if __name__ == "__main__":
    main()
