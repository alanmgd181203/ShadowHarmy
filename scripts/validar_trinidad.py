"""
Validación trinidad — Tank con muros en inverse + USDT linear + spot USDT.
Uso: python scripts/validar_trinidad.py [--segundos 30]
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
parser.add_argument("--segundos", type=int, default=30)
args = parser.parse_args()

import core.config as config  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402


async def main():
    print(f"\n=== VALIDACIÓN TRINIDAD | {len(config.ACTIVOS_TRINIDAD)} activos | {args.segundos}s WS ===\n")

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    bridge = BybitBridge(tank, tusk, bellion)

    task = asyncio.create_task(bridge.conectar())
    await asyncio.sleep(args.segundos)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    snap_tri = tank.snapshot_trinidad()
    snap_usdc = tank.snapshot_usdc_spot()
    snap_usde = tank.snapshot_usde()
    snap_usd1 = tank.snapshot_usd1()
    snap_mnt = tank.snapshot_mnt_spot()
    snap_spot = tank.snapshot_spot_all()
    snap_lin = tank.snapshot_linear_perp()
    snap_inv = tank.snapshot_inverse_perp()
    snap_linf = tank.snapshot_linear_futures()
    snap_invf = tank.snapshot_inverse_futures()
    esperados_tri = snap_tri.get("frentes_esperados", len(config.FRENTES_TRINIDAD))
    esperados_usdc = snap_usdc.get("frentes_esperados", len(config.FRENTES_USDC_SPOT))
    esperados_usde = snap_usde.get("frentes_esperados", len(config.FRENTES_USDE))
    esperados_usd1 = snap_usd1.get("frentes_esperados", len(config.FRENTES_USD1))
    esperados_mnt = snap_mnt.get("frentes_esperados", len(config.FRENTES_MNT_SPOT))
    esperados_spot = snap_spot.get("frentes_esperados", len(config.FRENTES_SPOT_ALL))
    esperados_lin = snap_lin.get("frentes_esperados", len(config.FRENTES_LINEAR_PERP))
    esperados_inv = snap_inv.get("frentes_esperados", len(config.FRENTES_INVERSE_PERP))
    esperados_linf = snap_linf.get("frentes_esperados", len(config.FRENTES_LINEAR_FUTURES))
    esperados_invf = snap_invf.get("frentes_esperados", len(config.FRENTES_INVERSE_FUTURES))

    print(f"\nTRINIDAD: precio {snap_tri.get('frentes_vivos', 0)}/{esperados_tri} | muros {snap_tri.get('muros_vivos', 0)}/{esperados_tri}")
    print(f"USDC SPOT: precio {snap_usdc.get('frentes_vivos', 0)}/{esperados_usdc} | muros {snap_usdc.get('muros_vivos', 0)}/{esperados_usdc}")
    print(f"USDE:      precio {snap_usde.get('frentes_vivos', 0)}/{esperados_usde} | muros {snap_usde.get('muros_vivos', 0)}/{esperados_usde}")
    print(f"USD1:      precio {snap_usd1.get('frentes_vivos', 0)}/{esperados_usd1} | muros {snap_usd1.get('muros_vivos', 0)}/{esperados_usd1}")
    print(f"MNT SPOT:  precio {snap_mnt.get('frentes_vivos', 0)}/{esperados_mnt} | muros {snap_mnt.get('muros_vivos', 0)}/{esperados_mnt}")
    print(f"SPOT ALL:  precio {snap_spot.get('frentes_vivos', 0)}/{esperados_spot} | muros {snap_spot.get('muros_vivos', 0)}/{esperados_spot}")
    print(f"LINEAR:    precio {snap_lin.get('frentes_vivos', 0)}/{esperados_lin} | muros {snap_lin.get('muros_vivos', 0)}/{esperados_lin}")
    print(f"INVERSE:   precio {snap_inv.get('frentes_vivos', 0)}/{esperados_inv} | muros {snap_inv.get('muros_vivos', 0)}/{esperados_inv}")
    print(f"FUT LIN:   precio {snap_linf.get('frentes_vivos', 0)}/{esperados_linf} | muros {snap_linf.get('muros_vivos', 0)}/{esperados_linf}")
    print(f"FUT INV:   precio {snap_invf.get('frentes_vivos', 0)}/{esperados_invf} | muros {snap_invf.get('muros_vivos', 0)}/{esperados_invf}")
    for label, snap, sym, frente in (
        ("spot", snap_spot, "BTCUSDT", "BTCUSDT_SPOT"),
        ("linear", snap_lin, "BTCUSDT", "BTCUSDT_LINEAL"),
        ("linear", snap_lin, "BTCPERP", "BTCPERP_LINEAL"),
        ("inverse", snap_inv, "BTCUSD", "BTCUSD_INVERSE"),
    ):
        d = snap.get("detalle", {}).get(frente, {})
        if d:
            ok = "OK" if d.get("precio", 0) > 0 else "—"
            print(f"  [{ok}] {label} {frente:22} P={d.get('precio', 0):.6f}")

    incompletos = []
    for base, fila in snap_tri.get("detalle", {}).items():
        ok = all(fila[t]["precio"] > 0 for t in ("lineal", "inverse", "spot"))
        muro_ok = all(
            fila[t]["muro_bid"] > 0 or fila[t]["muro_ask"] > 0
            for t in ("lineal", "inverse", "spot")
        )
        marca = "OK" if ok and muro_ok else "WARN"
        if marca != "OK":
            incompletos.append(base)
        if marca != "OK" or base in ("LTC", "BTC", "ETH"):
            print(f"  [{marca}] {base:6} L={fila['lineal']['precio']:.4f} I={fila['inverse']['precio']:.4f} S={fila['spot']['precio']:.4f}")

    ok_tri = snap_tri.get("frentes_vivos", 0) >= int(esperados_tri * 0.9)
    ok_usdc = snap_usdc.get("frentes_vivos", 0) >= int(esperados_usdc * 0.85)
    ok_usde = snap_usde.get("frentes_vivos", 0) >= max(1, esperados_usde - 1)
    ok_usd1 = snap_usd1.get("frentes_vivos", 0) >= max(1, esperados_usd1 - 1)
    ok_mnt = snap_mnt.get("frentes_vivos", 0) >= int(esperados_mnt * 0.85)
    ok_spot = snap_spot.get("frentes_vivos", 0) >= int(esperados_spot * 0.75)
    ok_lin = snap_lin.get("frentes_vivos", 0) >= int(esperados_lin * 0.75)
    ok_inv = snap_inv.get("frentes_vivos", 0) >= int(esperados_inv * 0.85)
    ok_linf = snap_linf.get("frentes_vivos", 0) >= int(esperados_linf * 0.75) if esperados_linf else True
    ok_invf = snap_invf.get("frentes_vivos", 0) >= max(1, esperados_invf - 1) if esperados_invf else True
    ok_global = ok_tri and ok_usdc and ok_usde and ok_usd1 and ok_mnt and ok_spot and ok_lin and ok_inv and ok_linf and ok_invf
    reporte = {
        "ts": time.time(),
        "activos_trinidad": config.ACTIVOS_TRINIDAD,
        "activos_usdc_spot": config.ACTIVOS_USDC_SPOT,
        "usde_pares": config.USDE_PARES,
        "usd1_pares": config.USD1_PARES,
        "mnt_spot_pares": config.MNT_SPOT_PARES,
        "spot_all_count": len(config.SPOT_ALL_PARES),
        "linear_perp_count": len(config.LINEAR_PERP_PARES),
        "inverse_perp_count": len(config.INVERSE_PERP_PARES),
        "linear_futures_count": len(config.LINEAR_FUTURES_PARES),
        "inverse_futures_count": len(config.INVERSE_FUTURES_PARES),
        "trinidad": snap_tri,
        "usdc_spot": snap_usdc,
        "usde": snap_usde,
        "usd1": snap_usd1,
        "mnt_spot": snap_mnt,
        "spot_all": snap_spot,
        "linear_perp": snap_lin,
        "inverse_perp": snap_inv,
        "linear_futures": snap_linf,
        "inverse_futures": snap_invf,
        "ok_trinidad": ok_tri,
        "ok_usdc_spot": ok_usdc,
        "ok_usde": ok_usde,
        "ok_usd1": ok_usd1,
        "ok_mnt_spot": ok_mnt,
        "ok_spot_all": ok_spot,
        "ok_linear_perp": ok_lin,
        "ok_inverse_perp": ok_inv,
        "ok_linear_futures": ok_linf,
        "ok_inverse_futures": ok_invf,
        "ok_global": ok_global,
        "incompletos_trinidad": incompletos,
    }
    ruta = os.path.join(ROOT, "data", "validacion_trinidad.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2)
    print(f"\nReporte: {ruta}")
    print(f"Resultado: {'OK' if ok_global else 'FAIL'}")
    sys.exit(0 if ok_global else 1)


if __name__ == "__main__":
    asyncio.run(main())
