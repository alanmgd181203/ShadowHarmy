#!/usr/bin/env python3
"""
4.0.2 — Simulación Igris: manos atadas, manos ilusorias.

Despierta: Tusk (oxígeno real) · Tank · Kaiser · Igris (manto).
NO despierta: Greed · Beru.
Manos reales: OFF (MODO_SIMULACION=True → fills ilusorios en Igris).
Bóveda manos: OFF (TUSK_BOVEDA_MANOS no se enciende).

  python scripts/arise_igris_sim.py
  python scripts/arise_igris_sim.py --segundos 90

Respeta marcha en data/marcha_despliegue.json (sello mega-pre-Igris).
Reporte: data/arise_igris_sim_report.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
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

# Marca de ritual — antes de importar config
os.environ["ARISE_IGRIS_SIM"] = "true"
os.environ["MODO_SIMULACION"] = "true"  # manos reales atadas
os.environ.setdefault("TUSK_BOVEDA_MANOS", "false")
# Sin arena forzada: usamos doctrina completa + fills por MODO_SIMULACION
os.environ.setdefault("ARENA_IGRIS_ACTIVA", "false")

import core.config as config  # noqa: E402

config.MODO_SIMULACION = True
config.ARISE_IGRIS_SIM = True
if hasattr(config, "TUSK_BOVEDA_MANOS"):
    config.TUSK_BOVEDA_MANOS = False

from core.bellion import BellionAuditor  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from core.dashboard import PanelDeControl  # noqa: E402
from generales.igris import IgrisEscudo  # noqa: E402
from generales.kaiser import KaiserVocero  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402


def _report_path() -> Path:
    return ROOT / "data" / "arise_igris_sim_report.json"


def _snapshot_cierre(tusk, igris) -> dict:
    from core import pase_director as pd
    from core import manto_ventana as mv

    eq = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
    mid = pd.cargar_marcha()
    payload = pd.cargar_marcha_payload() or {}
    plan = pd.plan_lote(eq, marcha_id=mid) if eq > 0 else {}
    meta = pd.meta_engorde_usd(eq, tusk=tusk, marcha_id=mid) if eq > 0 else {}
    usd_l, usd_s = mv.usd_piernas_desde_pesos(getattr(tusk, "pesos", {}) or {})
    ventana = mv.resumen_barco(usd_l, usd_s)
    return {
        "ts": time.time(),
        "sim": True,
        "manos_reales": False,
        "manos_ilusorias": True,
        "marcha_id": mid,
        "marcha_payload": {
            "fill_ratio": payload.get("fill_ratio"),
            "reserva_pasos": payload.get("reserva_pasos"),
            "duracion_dias": payload.get("duracion_dias"),
            "titulo": payload.get("titulo"),
        },
        "equity_usd": round(eq, 4),
        "masa_autorizada": float(getattr(tusk, "masa_autorizada", 0) or 0),
        "plan": {
            "potencia_n": plan.get("potencia_n"),
            "foco": plan.get("foco"),
            "activos_trabajo": plan.get("activos_trabajo"),
            "fill_ratio": plan.get("fill_ratio"),
            "reserva_pasos": plan.get("reserva_pasos"),
        },
        "meta_engorde": meta,
        "ventana_manto": ventana,
        "n_frentes_peso": len(getattr(tusk, "pesos", {}) or {}),
    }


async def _publicar_estado(bellion, tusk, igris, tank, kaiser):
    await asyncio.sleep(2)
    while True:
        await bellion.publicar_estado_vivo(tusk, None, igris, tank, kaiser=kaiser)
        await asyncio.sleep(1)


async def _refrescar_panel(panel):
    while True:
        panel.refrescar()
        await asyncio.sleep(1)


async def _cronica(tusk, intervalo_s: float = 20.0):
    await asyncio.sleep(10)
    from core import pase_director as pd

    while True:
        mid = pd.cargar_marcha()
        eq = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
        tes = getattr(tusk, "tesoreria", None) or {}
        n_pesos = sum(
            float(p.get("long") or 0) + float(p.get("short") or 0)
            for p in (getattr(tusk, "pesos", {}) or {}).values()
        )
        print(
            f"[SIM] marcha={mid} | equity={eq:.2f} | O2={tes.get('oxigeno_guerra_usd')} | "
            f"masa_auth={getattr(tusk, 'masa_autorizada', None)} | pesos_masa≈{n_pesos:.4f} | "
            f"SIM={config.MODO_SIMULACION}"
        )
        await asyncio.sleep(intervalo_s)


async def _apagado(shutdown_event, bellion, tusk, igris, started: float):
    await shutdown_event.wait()
    snap = _snapshot_cierre(tusk, igris)
    snap["duracion_s"] = round(time.time() - started, 1)
    try:
        _report_path().parent.mkdir(parents=True, exist_ok=True)
        _report_path().write_text(json.dumps(snap, indent=2), encoding="utf-8")
        print(f"\n[SIM] Reporte → {_report_path()}")
        print(
            f"[SIM] marcha={snap.get('marcha_id')} | meta_restante="
            f"{(snap.get('meta_engorde') or {}).get('restante_usd')} | "
            f"ventana={(snap.get('ventana_manto') or {}).get('estado')}"
        )
    except OSError as e:
        print(f"[SIM] No se pudo escribir reporte: {e}")
    await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
    await bellion.anotar(
        "BELLION", "SUCESION",
        "Ritual Igris SIM sellado — manos reales nunca se soltaron.",
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
    print(f"\n[SIM] Corte por tiempo ({segundos:.0f}s) — sellando…")
    shutdown_event.set()


async def ritual_igris_sim(segundos: float = 0.0):
    from core import pase_director as pd

    mid = pd.cargar_marcha()
    perfil = pd.perfil_marcha(mid)
    print("\n" + "═" * 52)
    print("    4.0.2  RITUAL IGRIS SIM")
    print("    Kaiser · Tank · Tusk · Igris")
    print("    Manos reales ATADAS · fills ILUSORIOS")
    print("    Greed / Beru hibernados · bóveda manos OFF")
    print(f"    FASE: {config.FASE_ACTUAL} | SIM={config.MODO_SIMULACION}")
    print(f"    Marcha: {mid} · fill={perfil.get('fill_ratio')} · reserva={perfil.get('reserva_pasos')}")
    print("═" * 52)

    if not config.MODO_SIMULACION:
        raise RuntimeError("Abort: MODO_SIMULACION debe ser True en 4.0.2")

    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    started = time.time()

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
            print("[BELLION] Recovery: bóveda restaurada (pesos/sim heredados).")

        kaiser = KaiserVocero(tank, bellion)
        igris = IgrisEscudo(tusk, tank, bellion, bridge=bridge, kaiser=kaiser)
        # Sin Greed: no asignar igris.greed

        from core.validacion import advertir_gates
        advertir_gates()

        panel = PanelDeControl(tusk, igris, tank)

        print("\n[TUSK] Oxígeno de guerra real → masa_autorizada (manos bóveda OFF).")
        print("[TANK/KAISER] Ojos vivos (VIP OK).")
        print("[IGRIS] vigilar_manto_operativo — engorde/ventana con fills ilusorios.")
        print("[GREED/BERU] Hibernados.")
        print("Ctrl+C para sellar.\n")

        await bellion.anotar(
            "IGRIS", "SIM_START",
            f"4.0.2 arranque · marcha={mid} · SIM=True · sin Greed/Beru",
        )

        tareas = [
            tusk.latido_persistencia([]),
            tusk.hilo_reconciliacion(bridge),
            tank.vigilar_aguas(),
            bridge.conectar(),
            bridge.hilo_sentidos_extra(),
            bridge.hilo_sincronizacion_nav(),
            kaiser.vigilar_indicadores(),
            igris.vigilar_manto_operativo(),
            _refrescar_panel(panel),
            _publicar_estado(bellion, tusk, igris, tank, kaiser),
            _cronica(tusk),
            _apagado(shutdown_event, bellion, tusk, igris, started),
            _corte_tiempo(shutdown_event, segundos),
        ]
        if binance_ref:
            tareas.append(binance_ref.conectar())

        await asyncio.gather(*tareas)

    except Exception:
        print("\n[!] ERROR EN RITUAL IGRIS SIM:")
        traceback.print_exc()
        raise


def main():
    ap = argparse.ArgumentParser(description="4.0.2 Igris sim — manos atadas, fills ilusorios")
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_IGRIS_SIM_SEGUNDOS", "0") or 0),
        help="Si >0, corta tras N segundos.",
    )
    args = ap.parse_args()
    asyncio.run(ritual_igris_sim(segundos=args.segundos))


if __name__ == "__main__":
    main()
