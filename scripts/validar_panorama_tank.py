#!/usr/bin/env python3
"""Valida Fase 1 (desvío índice) y Fase 2 (Binance ref) en Tank — 30–45 s de WS."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.config as config
from core.bellion import BellionAuditor
from core.binance_ref import BinanceRefBridge
from core.bridge import BybitBridge
from core.trinidad import aplicar_a_config, refrescar_config
from generales.tank import TankCluster
from generales.tusk import TuskBoveda


async def main(segundos: float) -> int:
    aplicar_a_config(config)
    try:
        refrescar_config()
        aplicar_a_config(config)
    except Exception:
        print("[warn] refrescar_config omitido — usando cache trinidad local")

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    api_key = getattr(config, "API_KEY", None)
    api_secret = getattr(config, "API_SECRET", None)
    bridge = BybitBridge(tank, tusk, bellion, api_key, api_secret)
    binance = None
    if getattr(config, "BINANCE_REF_ENABLED", True):
        binance = BinanceRefBridge(tank, bellion)

    print(f"Bases huérfanas: {len(getattr(config, 'ACTIVOS_HUERFANOS', []))}")
    print(f"Bases panorama Binance: {len(getattr(config, 'BASES_PANORAMA', []))}")

    t0 = time.time()
    tasks = [
        asyncio.create_task(bridge.conectar()),
        asyncio.create_task(bridge.hilo_sentidos_extra()),
        asyncio.create_task(tank.vigilar_aguas()),
    ]
    if binance:
        tasks.append(asyncio.create_task(binance.conectar()))

    await asyncio.sleep(segundos)
    for t in tasks:
        t.cancel()
    for t in tasks:
        try:
            await t
        except asyncio.CancelledError:
            pass

    dt = time.time() - t0
    desv = tank.snapshot_desvios_indice()
    pano = tank.snapshot_panorama_global()
    matriz = tank.snapshot_matriz_spreads()
    sent = tank.snapshot_sentidos_extra()

    out = {
        "segundos": round(dt, 1),
        "desvios_indice": {
            "top_n": desv.get("top_n", 0),
            "perps_con_indice": desv.get("perps_con_indice", 0),
            "filas_muestra": (desv.get("filas") or [])[:5],
        },
        "panorama_global": {
            "bases_huerfanas": pano.get("bases_huerfanas", 0),
            "refs_binance": pano.get("refs_binance", 0),
            "filas_muestra": (pano.get("filas") or [])[:5],
        },
        "matriz_spreads_top": matriz.get("top_n", 0),
        "convert_quotes": len(sent.get("convert_quotes") or []),
        "errores_sentidos": sent.get("errores", {}),
    }

    path = ROOT / "data" / "validacion_panorama_tank.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=True), encoding="utf-8")

    print(json.dumps(out, indent=2, ensure_ascii=True))
    ok = desv.get("perps_con_indice", 0) > 0 or matriz.get("top_n", 0) > 0
    if binance and pano.get("refs_binance", 0) == 0:
        print("[warn] Binance ref sin ticks — geo/red o bases vacías")
    return 0 if ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--segundos", type=float, default=35.0)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.segundos)))
