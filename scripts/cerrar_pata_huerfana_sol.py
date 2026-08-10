#!/usr/bin/env python3
"""Cierra short lineal SOL huérfano (sin L inverso) en mainnet.

Uso:
  .venv/bin/python3 scripts/cerrar_pata_huerfana_sol.py --confirmar-go --permitir-mainnet
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("MODO_TESTNET", "False")
os.environ.setdefault("MODO_SIMULACION", "False")

import core.config as config
from pybit.unified_trading import HTTP

SYM = "SOLUSDT"
CAT = "linear"


def main() -> int:
    ap = argparse.ArgumentParser(description="Cerrar short SOLUSDT huérfano")
    ap.add_argument("--confirmar-go", action="store_true")
    ap.add_argument("--permitir-mainnet", action="store_true")
    args = ap.parse_args()
    if not args.confirmar_go or not args.permitir_mainnet:
        print("ABORT: exige --confirmar-go --permitir-mainnet")
        return 2
    if config.TESTNET or getattr(config, "MODO_TESTNET", False):
        print("ABORT: este ritual es mainnet (testnet activo)")
        return 2
    if not config.API_KEY or not config.API_SECRET:
        print("ABORT: sin API keys")
        return 2

    session = HTTP(
        testnet=False,
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
    )
    r = session.get_positions(category=CAT, symbol=SYM)
    if r.get("retCode") != 0:
        print("FAIL get_positions", r.get("retMsg"))
        return 1
    rows = [x for x in (r.get("result") or {}).get("list") or [] if float(x.get("size") or 0) > 0]
    if not rows:
        print("OK ya limpio: sin posición SOLUSDT")
        return 0

    ok = fail = 0
    for row in rows:
        side = str(row.get("side") or "")
        qty = float(row.get("size") or 0)
        if qty <= 0:
            continue
        # Solo cerramos short (Sell) huérfano — Buy reduceOnly
        if side.lower() not in ("sell", "short"):
            print(f"SKIP no-short {side} size={qty}")
            continue
        close_side = "Buy"
        params = {
            "category": CAT,
            "symbol": SYM,
            "side": close_side,
            "orderType": "Market",
            "qty": str(qty),
            "reduceOnly": True,
            "orderLinkId": f"SA-SOLFIX-{int(time.time() * 1000) % 10_000_000}",
        }
        print(f"CERRAR {CAT} {SYM}: short {qty} → {close_side} Market reduceOnly")
        out = session.place_order(**params)
        if out.get("retCode") == 0:
            print(f"  OK orderId={((out.get('result') or {}).get('orderId'))}")
            ok += 1
        else:
            print(f"  FAIL {out.get('retMsg')}")
            fail += 1

    time.sleep(1.2)
    r2 = session.get_positions(category=CAT, symbol=SYM)
    restos = [
        x for x in (r2.get("result") or {}).get("list") or [] if float(x.get("size") or 0) > 0
    ]
    for x in restos:
        print(f"RESTO {SYM}: side={x.get('side')} size={x.get('size')}")
    if restos:
        print(f"RADAR_CON_RESTOS ok={ok} fail={fail}")
        return 2
    print(f"RADAR_LIMPIO ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
