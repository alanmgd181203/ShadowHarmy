"""
Validación sentidos extra — matriz spreads, funding WS, REST spread/alpha/convert.
Uso: python scripts/validar_sentidos_extra.py [--segundos 45]
"""
import asyncio
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

parser = argparse.ArgumentParser()
parser.add_argument("--segundos", type=int, default=45)
args = parser.parse_args()

import core.config as config  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402


async def main():
    print(f"\n=== VALIDACIÓN SENTIDOS EXTRA | WS {args.segundos}s + REST ===\n")

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    api_key = getattr(config, "API_KEY", None)
    api_secret = getattr(config, "API_SECRET", None)
    bridge = BybitBridge(tank, tusk, bellion, api_key, api_secret)

    tasks = [
        asyncio.create_task(bridge.conectar()),
        asyncio.create_task(bridge.hilo_sentidos_extra()),
        asyncio.create_task(tank.vigilar_aguas()),
    ]
    await asyncio.sleep(args.segundos)
    for t in tasks:
        t.cancel()
    for t in tasks:
        try:
            await t
        except asyncio.CancelledError:
            pass

    snap_mat = tank.snapshot_matriz_spreads()
    snap_fund = tank.snapshot_funding()
    snap_ext = tank.snapshot_sentidos_extra()

    print(f"MATRIZ SPREADS: {snap_mat.get('top_n', 0)} filas | funding {snap_mat.get('funding_vivos', 0)} | index {snap_mat.get('index_vivos', 0)}")
    for row in (snap_mat.get("filas") or [])[:5]:
        print(f"  {row.get('tipo')} {row.get('base')}: {row.get('spread_pct')}%")

    print(f"\nFUNDING WS: {snap_fund.get('vivos', 0)} símbolos")
    for row in (snap_fund.get("top") or [])[:3]:
        print(f"  {row.get('base')}: {row.get('funding_pct')}%")

    sp = snap_ext.get("spread_producto", {})
    al = snap_ext.get("alpha", {})
    cv = snap_ext.get("convert", {})
    print(f"\nSPREAD PRODUCTO: {sp.get('vivos', 0)}/{sp.get('instrumentos', 0)}")
    print(f"ALPHA: {al.get('tokens', 0)} tokens")
    print(f"CONVERT: {cv.get('pares', 0)} pares")
    errs = snap_ext.get("errores", {})
    if errs:
        print("ERRORES REST:", json.dumps(errs, ensure_ascii=True))

    reporte = {
        "ts": time.time(),
        "segundos": args.segundos,
        "matriz_spreads": snap_mat,
        "funding": {"vivos": snap_fund.get("vivos", 0), "top": snap_fund.get("top", [])[:5]},
        "sentidos_extra": snap_ext,
        "ok_matriz": snap_mat.get("top_n", 0) > 0,
        "ok_funding": snap_fund.get("vivos", 0) > 0,
        "ok_spread_producto": sp.get("instrumentos", 0) > 0 or "spread" in errs,
        "ok_alpha": al.get("tokens", 0) > 0 or "alpha" in errs,
        "ok_convert": cv.get("pares", 0) > 0 or "convert" in errs or not api_key,
    }

    out_path = os.path.join(ROOT, "data", "validacion_sentidos_extra.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2)
    print(f"\nReporte: {out_path}")
    print("OK" if reporte["ok_matriz"] else "WARN: matriz vacía (¿WS sin precios trinidad?)")


if __name__ == "__main__":
    asyncio.run(main())
