#!/usr/bin/env python3
"""Activa modo bidireccional (Both Sides) en MNT inverso + lineal — bóveda ≠ manto."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core.bellion import BellionAuditor
from core.bridge import BybitBridge
from core.mnt_manto_hedge import asegurar_hedge_bases_boveda, pares_hedge_boveda
from generales.tank import TankCluster
from generales.tusk import TuskBoveda


def _leer_modo(session, symbol: str, category: str) -> dict:
    """Infiere hedge: positionIdx 1/2 en posiciones abiertas ⇒ Both Sides."""
    out: dict = {"symbol": symbol, "category": category, "rows": []}
    try:
        r = session.get_positions(category=category, symbol=symbol)
        lista = ((r.get("result") or {}).get("list") or []) if isinstance(r, dict) else []
        for row in lista:
            sz = float(row.get("size") or 0)
            idx = int(float(row.get("positionIdx") or 0))
            if sz > 0 or idx != 0:
                out["rows"].append(
                    {
                        "side": row.get("side"),
                        "size": sz,
                        "positionIdx": idx,
                    }
                )
        idxs = {int(x["positionIdx"]) for x in out["rows"]}
        # Con short bóveda: idx 2 = hedge sell. idx 0 = one-way.
        if any(i in (1, 2) for i in idxs):
            out["modo"] = "hedge"
        elif out["rows"]:
            out["modo"] = "one_way_o_inierto"
        else:
            out["modo"] = "sin_posicion"
    except Exception as e:
        out["error"] = str(e)
        out["modo"] = "error"
    return out


async def main() -> int:
    config.IGRIS_MNT_HEDGE_OBLIGATORIO = True
    bel = BellionAuditor()
    tusk = TuskBoveda(bel)
    tank = TankCluster(tusk, bel, ticker_base=getattr(config, "TICKER_BASE", "ETHUSDT"))
    bridge = BybitBridge(
        tank, tusk, bel,
        getattr(config, "API_KEY", None),
        getattr(config, "API_SECRET", None),
    )
    if not getattr(bridge, "session", None):
        print("FAIL: sin sesión API")
        return 2

    print("Pares a forzar:", pares_hedge_boveda())
    print("--- antes ---")
    for sym, cat in pares_hedge_boveda():
        print(json.dumps(_leer_modo(bridge.session, sym, cat), ensure_ascii=False))

    res = await asegurar_hedge_bases_boveda(bridge)
    print("--- switch ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("--- despues ---")
    for sym, cat in pares_hedge_boveda():
        print(json.dumps(_leer_modo(bridge.session, sym, cat), ensure_ascii=False))

    return 0 if res.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
