"""
Validación M2 (Fase 3.1–3.4): pentiverso dual LTC+BTC, persistencia, snapshot panel.
Uso: python scripts/validar_m2.py [--segundos 20]
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
parser.add_argument("--segundos", type=int, default=25)
args = parser.parse_args()

import core.config as config  # noqa: E402

from core.bellion import BellionAuditor  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402


async def validar_pentiverso(segundos: int):
    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    bridge = BybitBridge(tank, tusk, bellion)

    task = asyncio.create_task(bridge.conectar())
    await asyncio.sleep(segundos)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    tank._auditar_semaforos()
    snap = tank.snapshot_pentiverso()
    ctx_map, estado = await tank.vision_especulativa()

    esperados = config.MARES_PENTIVERSO_ALL
    resultados = {
        "activos": config.ACTIVOS_PENTIVERSO,
        "ticker_ref": config.TICKER_BASE,
        "estado_semaforo": estado,
        "mares": {},
        "mares_con_precio": 0,
        "mares_con_muro": 0,
        "ok_pentiverso": False,
        "ok_muros": False,
    }

    for f in esperados:
        d = snap.get(f, {})
        precio = d.get("precio", 0)
        mb = d.get("muro_bid", 0)
        ma = d.get("muro_ask", 0)
        resultados["mares"][f] = {
            "precio": precio,
            "muro_bid": mb,
            "muro_ask": ma,
            "reflejo_spot": d.get("reflejo_spot", False),
        }
        if precio > 0:
            resultados["mares_con_precio"] += 1
        if mb > 0 or ma > 0:
            resultados["mares_con_muro"] += 1

    # USDC lineal = reflejo spot; cuenta como vivo si reflejo tiene precio
    resultados["ok_pentiverso"] = resultados["mares_con_precio"] == len(esperados)
    resultados["ok_muros"] = resultados["mares_con_muro"] >= max(1, len(esperados) // 2)
    resultados["ctx_map_ok"] = ctx_map is not None and estado not in ("ROJO",)

    return resultados


async def validar_persistencia():
    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tusk.pesos = {"LTCUSDT_LINEAL": {"long": 0.1, "short": 0.1}}
    tusk.masa_autorizada = 42.0

    await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
    cargado = bellion.cargar_estado()

    ok_guardado = os.path.exists(bellion.ruta_estado)
    ok_recovery = (
        cargado is not None
        and cargado.get("boveda", {}).get("masa_autorizada") == 42.0
    )
    return {"ok_sucesion": ok_guardado, "ok_recovery": ok_recovery, "ruta": bellion.ruta_estado}


async def main():
    print(f"\n=== VALIDACIÓN M2 DUAL LTC+BTC | ref={config.TICKER_BASE} | {args.segundos}s WS ===\n")

    pent = await validar_pentiverso(args.segundos)
    pers = await validar_persistencia()

    print("PENTIVERSO (10 mares):")
    for asset in config.ACTIVOS_PENTIVERSO:
        print(f"  --- {asset} ---")
        for f, d in pent["mares"].items():
            if not f.startswith(asset):
                continue
            ref = " (reflejo)" if d.get("reflejo_spot") else ""
            ok = "OK" if d["precio"] > 0 else "FAIL"
            print(
                f"  [{ok}] {f:20} precio={d['precio']:.4f}{ref}  "
                f"muro_b={d['muro_bid']:.2f} muro_a={d['muro_ask']:.2f}"
            )
    print(f"  Semaforo: {pent['estado_semaforo']}")
    print(f"  Mares con precio: {pent['mares_con_precio']}/{len(pent['mares'])}")
    print(f"  Mares con muro:   {pent['mares_con_muro']}/{len(pent['mares'])}")

    print("\nPERSISTENCIA:")
    print(f"  ley_de_sucesion guardó: {'OK' if pers['ok_sucesion'] else 'FAIL'} ({pers['ruta']})")
    print(f"  cargar_estado leyó:     {'OK' if pers['ok_recovery'] else 'FAIL'}")

    reporte = {
        "ts": time.time(),
        "pentiverso": pent,
        "persistencia": pers,
        "fase_3_1_4_ok": pent["ok_pentiverso"],
        "fase_3_1_5_ok": pent["ok_muros"],
        "fase_3_3_ok": pers["ok_sucesion"] and pers["ok_recovery"],
    }

    ruta = os.path.join(ROOT, "data", "validacion_m2.json")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2)
    print(f"\nReporte: {ruta}")

    exit_code = 0 if (pent["ok_pentiverso"] and pers["ok_sucesion"]) else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
