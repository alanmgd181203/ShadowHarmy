#!/usr/bin/env python3
"""
Ritual de ojos — Tusk + Tank + Kaiser (sin disparos).

Despierta bóveda real (tesorería UTA / oxígeno de guerra), ojos de mercado (Tank)
e indicadores (Kaiser). NO arranca Igris manto, Greed ni Beru.

  python scripts/arise_ojos_tusk.py
  python scripts/arise_ojos_tusk.py --segundos 120

Panel (otra terminal): streamlit run panel.py
Mirar: estado_vivo.tusk_tesoreria · kaiser_digest · matriz Tank.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Marca de ritual (config la lee tras import)
os.environ.setdefault("ARISE_OJOS_TUSK", "true")
# Sin manos: si .env tenía sim=false por error, este ritual fuerza sim salvo override
if os.getenv("ARISE_OJOS_PERMITIR_MANOS", "").lower() not in ("1", "true", "yes"):
    os.environ["MODO_SIMULACION"] = "true"
# Ojos flacos por defecto (Santos last price · sin orderbook) — override: ARISE_OJOS_COMPLETOS=true
if os.getenv("ARISE_OJOS_COMPLETOS", "").lower() not in ("1", "true", "yes"):
    os.environ.setdefault("BRIDGE_WS_SUBSCRIBE_BOOKS", "false")

import core.config as config  # noqa: E402
from core import ojos_estrechos  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from core.dashboard import PanelDeControl  # noqa: E402
from generales.kaiser import KaiserVocero  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402


async def _publicar_estado(bellion, tusk, igris, tank, kaiser):
    await asyncio.sleep(2)
    while True:
        await bellion.publicar_estado_vivo(tusk, None, igris, tank, kaiser=kaiser)
        await asyncio.sleep(1)


async def _refrescar_panel(panel):
    while True:
        panel.refrescar()
        await asyncio.sleep(1)


async def _cronica_tesoreria(tusk, intervalo_s: float = 15.0):
    """Imprime en consola lo que Tusk ve de la bóveda (cada N s)."""
    await asyncio.sleep(8)
    while True:
        tes = getattr(tusk, "tesoreria", None) or {}
        if not tes:
            print("[TUSK] Tesorería aún vacía — esperando Bridge NAV…")
        else:
            eq = tes.get("equity_usd")
            disp = tes.get("disponible_usd")
            o2 = tes.get("oxigeno_guerra_usd")
            est = tes.get("estado")
            mnt = tes.get("mnt_usd")
            hedges = tes.get("hedge_shorts") or []
            n_h = len(hedges) if isinstance(hedges, list) else 0
            print(
                f"[TUSK] equity={eq} | disp={disp} | O2 guerra={o2} | "
                f"estado={est} | MNT≈{mnt} | hedges={n_h} | "
                f"masa_autorizada={getattr(tusk, 'masa_autorizada', None)}"
            )
        await asyncio.sleep(intervalo_s)


async def _apagado(shutdown_event, bellion, tusk):
    await shutdown_event.wait()
    await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
    await bellion.anotar(
        "BELLION", "SUCESION",
        "Ritual ojos sellado — Tusk/Tank/Kaiser vuelven a sombra (sin disparos).",
    )


def _senales(loop, shutdown_event):
    def _handler(sig, frame):
        loop.call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handler)


async def _corte_tiempo(shutdown_event, segundos: float):
    if segundos <= 0:
        return
    await asyncio.sleep(segundos)
    print(f"\n[OJOS] Corte por tiempo ({segundos:.0f}s) — sellando…")
    shutdown_event.set()


async def ritual_ojos(segundos: float = 0.0):
    print("\n" + "═" * 48)
    print("    RITUAL DE OJOS — Tusk · Tank · Kaiser")
    print("    Sin Igris / Greed / Beru (no disparos)")
    print(f"    FASE: {config.FASE_ACTUAL} | SIM={config.MODO_SIMULACION}")
    print("═" * 48)

    # Tank estrecho: Santos last price · sin orderbook (hasta Greed / orden Monarca)
    if os.getenv("ARISE_OJOS_COMPLETOS", "").lower() not in ("1", "true", "yes"):
        bases = ojos_estrechos.aplicar_ojos_last_price_santos()
        print(
            f"[OJOS] Estrechos · {len(bases)} Santos · books=OFF · "
            f"Binance ref={'ON' if getattr(config, 'BINANCE_REF_ENABLED', False) else 'OFF'}"
        )
        print(f"[OJOS] Bases: {', '.join(bases)}")
    else:
        print("[OJOS] Modo COMPLETOS (catálogo ancho) — ARISE_OJOS_COMPLETOS")

    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)

    try:
        api_key = getattr(config, "API_KEY", None)
        api_secret = getattr(config, "API_SECRET", None)

        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
        bridge = BybitBridge(tank, tusk, bellion, api_key, api_secret)
        binance_ref = None
        if getattr(config, "BINANCE_REF_ENABLED", True):
            from core.binance_ref import BinanceRefBridge
            binance_ref = BinanceRefBridge(tank, bellion)

        estado_prev = bellion.cargar_estado()
        if estado_prev:
            tusk.restaurar_desde_bellion(estado_prev.get("boveda", {}))
            print("[BELLION] Recovery: bóveda restaurada.")

        kaiser = KaiserVocero(tank, bellion)
        # Igris solo para banda/snapshot en estado_vivo — SIN vigilar_manto_operativo
        igris = None  # Igris de baja

        from core.validacion import advertir_gates
        advertir_gates()

        panel = PanelDeControl(tusk, igris, tank)

        print("\n[TUSK] Tesorería UTA → oxígeno de guerra (masa_autorizada).")
        print("[TANK] Ojos last price Santos (sin muros / sin Greed).")
        print("[KAISER] Indicadores / perfiles — sin cola a Greed viva.")
        print("[IGRIS/GREED/BERU] Hibernados en este ritual.")
        print("Ctrl+C para sellar.\n")

        coros = [
            tusk.latido_persistencia([]),
            tusk.hilo_reconciliacion(bridge),
            tank.vigilar_aguas(),
            bridge.conectar(),
            bridge.hilo_sentidos_extra(),
            bridge.hilo_sincronizacion_nav(),
            kaiser.vigilar_indicadores(),
            _refrescar_panel(panel),
            _publicar_estado(bellion, tusk, igris, tank, kaiser),
            _cronica_tesoreria(tusk),
            _corte_tiempo(shutdown_event, segundos),
        ]
        if binance_ref:
            coros.append(binance_ref.conectar())

        tasks = [asyncio.create_task(c) for c in coros]
        # Apagado limpio: al corte/señal cancela el río (evita cuelgue eterno)
        await shutdown_event.wait()
        print("\n[OJOS] Sellando ojos…")
        await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
        await bellion.anotar(
            "BELLION", "SUCESION",
            "Ritual ojos sellado — Tusk/Tank/Kaiser vuelven a sombra (sin disparos).",
        )
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    except Exception:
        print("\n[!] ERROR EN RITUAL DE OJOS:")
        traceback.print_exc()
        raise


def main():
    ap = argparse.ArgumentParser(description="Ritual ojos Tusk+Tank+Kaiser (sin disparos)")
    ap.add_argument(
        "--segundos", type=float, default=float(os.getenv("ARISE_OJOS_SEGUNDOS", "0") or 0),
        help="Si >0, corta el ritual tras N segundos (útil para smoke vivo).",
    )
    args = ap.parse_args()
    # Config ya importada; refuerza flags leídos
    if not getattr(config, "TUSK_TESORERIA_ACTIVA", True):
        print("[!] TUSK_TESORERIA_ACTIVA=false — activa en .env para ver oxígeno real.")
    # Forzar sim en runtime (dotenv a veces pisa el environ previo)
    if os.getenv("ARISE_OJOS_PERMITIR_MANOS", "").lower() not in ("1", "true", "yes"):
        config.MODO_SIMULACION = True
    asyncio.run(ritual_ojos(segundos=args.segundos))


if __name__ == "__main__":
    main()
