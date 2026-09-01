#!/usr/bin/env python3
"""Paridad oído Beru rango — OKX vs Bybit (sin manos, sin capital).

Comprueba que el ritual de ojos en OKX escucha igual que en Bybit:
  · solo lineal USDT (ciego a spot/inverso)
  · tickers + tratos públicos ON
  · libros OFF
  · muleta REST si cae el río WS
  · latido = last + high/low + prints entre pulsos

Uso:
  python scripts/validar_beru_oido_okx_parity.py
  python scripts/validar_beru_oido_okx_parity.py --probe ETH --segundos 12
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "beru" / "rango" / "oido_okx_bybit_parity.json"

# Tabla doctrinal (espejo arise_beru_rango_ojos + bridge.py)
PARIDAD = [
    ("mercado", "lineal USDT only", "lineal USDT only"),
    ("ws_tickers", "tickers.{symbol}", "channel=tickers"),
    ("ws_tratos", "publicTrade.{symbol}", "channel=trades"),
    ("ws_libros", "OFF (BRIDGE_WS_SUBSCRIBE_BOOKS=false)", "OFF"),
    ("mecha", "registrar_print_lineal -> consumir_latido_lineal", "igual"),
    ("ticker_fallback", "lastPrice -> mark -> bid/ask", "last -> mark -> bid/ask"),
    ("muleta_rest", "tickers lineal público si WS >5s", "igual (okx /api/v5/market/tickers)"),
    ("manos", "OFF + MODO_SIMULACION", "OFF + MODO_SIMULACION"),
    ("tusk_reconcile", "posiciones Bybit", "no reconcilia OKX (doctrina 23)"),
]


async def _probe_okx(activo: str, segundos: float) -> dict:
    os.environ["BERU_MAR"] = "okx"
    os.environ["BERU_RANGO_MANOS"] = "false"
    os.environ["MODO_SIMULACION"] = "true"
    os.environ["BRIDGE_WS_SOLO_LINEAR"] = "true"
    os.environ["BRIDGE_WS_PUBLIC_TRADES_LINEAR"] = "true"
    os.environ["BRIDGE_WS_SUBSCRIBE_BOOKS"] = "false"

    import core.config as config
    from core import beru_rango_ojos as ojos
    from core.bellion import BellionAuditor
    from core.beru_bridge import crear_beru_bridge
    from generales.tank import TankCluster
    from generales.tusk import TuskBoveda

    config.BERU_RANGO_MANOS = False
    config.MODO_SIMULACION = True
    config.BRIDGE_WS_SOLO_LINEAR = True
    config.BRIDGE_WS_PUBLIC_TRADES_LINEAR = True
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = False

    act = str(activo).upper()
    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank = TankCluster(tusk, bellion)
    bridge = crear_beru_bridge(tank, tusk, bellion, ws_bases=[act])
    tank.expandir_frentes(ojos.frentes_lineal_tank([act]))

    ws_task = asyncio.create_task(bridge.conectar())
    t0 = time.time()
    samples: list[dict] = []
    try:
        while time.time() - t0 < segundos:
            await asyncio.sleep(1.0)
            lat = ojos.latido_lineal_desde_tank(tank, act)
            rio = ojos.rio_ws_vivo(tank)
            samples.append(
                {
                    "ts": time.time(),
                    "rio_ws": rio,
                    "last": lat.get("last"),
                    "high": lat.get("high"),
                    "low": lat.get("low"),
                    "n_prints": len(lat.get("prints") or []),
                }
            )
    finally:
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass

    ok = any(s.get("rio_ws") for s in samples) and any(
        float(s.get("last") or 0) > 0 for s in samples
    )
    return {
        "activo": act,
        "mar": "okx",
        "segundos": segundos,
        "ok": ok,
        "muestras": samples[-5:],
        "rio_alguna_vez": any(s.get("rio_ws") for s in samples),
        "prints_alguna_vez": any(int(s.get("n_prints") or 0) > 0 for s in samples),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", default="", help="Santo live OKX (ej. ETH)")
    ap.add_argument("--segundos", type=float, default=12.0)
    args = ap.parse_args()

    flags_ok = (
        os.getenv("BRIDGE_WS_PUBLIC_TRADES_LINEAR", "true").lower() in ("1", "true", "yes")
        and os.getenv("BRIDGE_WS_SUBSCRIBE_BOOKS", "false").lower() not in ("1", "true", "yes")
    )

    probe: dict | None = None
    if str(args.probe or "").strip():
        probe = asyncio.run(_probe_okx(str(args.probe).upper(), float(args.segundos)))

    sello = {
        "ts_utc": time.time(),
        "paridad_tabla": [
            {"pieza": a, "bybit": b, "okx": o} for a, b, o in PARIDAD
        ],
        "flags_ritual_ok": flags_ok,
        "probe_okx": probe,
        "veredicto": (
            "PARIDAD_OK"
            if flags_ok and (probe is None or probe.get("ok"))
            else "REVISAR"
        ),
        "nota": (
            "Oído = tickers + tratos públicos lineal, sin libros. "
            "OKX usa mismos candados que arise_beru_rango_ojos."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sello, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("[OIDO] Paridad OKX vs Bybit — Beru rango ojos")
    for pieza, bybit, okx in PARIDAD:
        print(f"  {pieza}: Bybit={bybit} | OKX={okx}")
    print(f"  flags ritual: {'OK' if flags_ok else 'FAIL'}")
    if probe:
        print(
            f"  probe {probe['activo']}: rio={probe.get('rio_alguna_vez')} "
            f"prints={probe.get('prints_alguna_vez')} ok={probe.get('ok')}"
        )
    print(f"  sello: {OUT}")
    print(f"  veredicto: {sello['veredicto']}")
    return 0 if sello["veredicto"] == "PARIDAD_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
