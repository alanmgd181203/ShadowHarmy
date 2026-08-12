#!/usr/bin/env python3
"""Ritual Beru — manos fantasma (nivel 2 ensayo).

Ojos reales Bybit (Tank/Bridge) · Beru late · Igris/Greed dormidos.
CERO place_order: cada disparo se imprime y va a data/logs/beru_fantasma/disparos.jsonl.

  python scripts/arise_beru_fantasma.py --segundos 1200
  python scripts/arise_beru_fantasma.py --segundos 600 --activos ADA,BCH,MNT

Ctrl+C sella. No toca el manto de futuros.
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

# Candados ritual (antes de importar config)
os.environ["ARISE_BERU_FANTASMA"] = "true"
os.environ["MODO_SIMULACION"] = "true"          # nunca place_order real
os.environ["BERU_MANOS_FANTASMA"] = "true"
os.environ["BERU_HILO_ENABLED"] = "true"
os.environ["BERU_MANOS"] = "false"               # manos reales OFF
os.environ["BERU_ENGORDE_PERMITIDO"] = "false"
os.environ["BERU_NEUTRO_MARGEN"] = "true"
os.environ["BERU_SPOT_MARGEN_ENABLED"] = "false"
os.environ["BERU_WAKE_RESET_0"] = "true"
os.environ["BERU_CAPITAN_WAKE"] = "NORMAL"
os.environ.setdefault("BERU_SIEMBRA_FLOTA", "true")
os.environ.setdefault("ARISE_BERU_ARMADO", "true")
# Ojos estrechos: sin trinidad completa (11 shards / 1390 tickers ahogan handshake)
os.environ.setdefault("BRIDGE_WS_SUBSCRIBE_BOOKS", "false")
os.environ.setdefault("BINANCE_REF_ENABLED", "false")
os.environ.setdefault("KAISER_BACKFILL_ON_START", "false")
os.environ.setdefault("BRIDGE_WS_STAGGER_S", "0.7")
os.environ.setdefault("BRIDGE_WS_FORCE_IPV4", "true")
os.environ.setdefault("BRIDGE_WS_PROXY", "direct")
os.environ.setdefault("BYBIT_RECV_WINDOW_MS", "60000")

import core.config as config  # noqa: E402

config.BRIDGE_WS_SUBSCRIBE_BOOKS = False
if hasattr(config, "BINANCE_REF_ENABLED"):
    config.BINANCE_REF_ENABLED = False
if hasattr(config, "KAISER_BACKFILL_ON_START"):
    config.KAISER_BACKFILL_ON_START = False
config.BRIDGE_WS_STAGGER_S = float(os.getenv("BRIDGE_WS_STAGGER_S", "0.7") or 0.7)
if hasattr(config, "BRIDGE_WS_FORCE_IPV4"):
    config.BRIDGE_WS_FORCE_IPV4 = True
if hasattr(config, "BRIDGE_WS_PROXY"):
    config.BRIDGE_WS_PROXY = os.getenv("BRIDGE_WS_PROXY", "direct") or "direct"
config.BYBIT_RECV_WINDOW_MS = int(float(os.getenv("BYBIT_RECV_WINDOW_MS", "60000") or 60000))

from core import beru_fantasma  # noqa: E402
from core import beru_wake  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from core.dashboard import PanelDeControl  # noqa: E402
from generales.beru import BeruCazador  # noqa: E402
from generales.igris import IgrisEscudo  # noqa: E402
from generales.kaiser import KaiserVocero  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402

HB_PATH = ROOT / "data" / "logs" / "beru_fantasma" / "heartbeat.json"
REPORT_PATH = ROOT / "data" / "logs" / "beru_fantasma" / "ultimo_informe.json"


def _escribir_hb(msg: str, extra: dict | None = None) -> None:
    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "msg": msg,
        "fantasma": True,
        "sim": bool(config.MODO_SIMULACION),
        "manos": bool(config.BERU_MANOS),
        "manos_fantasma": bool(config.BERU_MANOS_FANTASMA),
        "hilo": bool(config.BERU_HILO_ENABLED),
    }
    if extra:
        payload.update(extra)
    HB_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


async def _publicar_estado(bellion, tusk, igris, tank, kaiser, beru):
    await asyncio.sleep(2)
    while True:
        await bellion.publicar_estado_vivo(
            tusk, list(beru.legion), igris, tank, kaiser=kaiser,
        )
        await asyncio.sleep(1)


async def _refrescar_panel(panel):
    while True:
        panel.refrescar()
        await asyncio.sleep(1)


async def _cronica_legion(beru: BeruCazador, intervalo_s: float = 20.0):
    await asyncio.sleep(10)
    while True:
        n = len(beru.legion)
        estados: dict[str, int] = {}
        for b in beru.legion:
            est = str(getattr(b, "estado", "?") or "?")
            estados[est] = estados.get(est, 0) + 1
        px = beru._precio_casa()
        casa = beru._activo_casa()
        print(
            f"[BERU] casa={casa} px={px:.6g} | legión={n} | estados={estados} | "
            f"fantasma={beru._manos_fantasma()}",
            flush=True,
        )
        _escribir_hb(
            "cronica",
            {"casa": casa, "precio": px, "n_legion": n, "estados": estados},
        )
        await asyncio.sleep(intervalo_s)


async def _rellenar_precios_flota(beru: BeruCazador, activos: list[str]) -> dict[str, float]:
    """Espera ojos y arma mapa precio por Santo para siembra flota."""
    out: dict[str, float] = {}
    for _ in range(60):
        for act in activos:
            px = beru._precio_de_activo(act)
            if px > 0:
                out[act] = px
        if len(out) >= max(1, min(3, len(activos))):
            break
        await asyncio.sleep(2)
    return out


async def _apagado(shutdown_event, bellion, tusk, beru, started: float, tasks: list):
    await shutdown_event.wait()
    leg = []
    try:
        for b in beru.legion:
            leg.append({
                "uid": getattr(b, "uid", ""),
                "estado": getattr(b, "estado", ""),
                "direccion": getattr(b, "direccion", ""),
                "masa": float(getattr(b, "masa", 0) or 0),
                "centro_local": float(getattr(b, "centro_local", 0) or 0),
                "activo": beru._activo_de_barco(b),
            })
    except Exception:
        pass
    informe = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duracion_s": round(time.time() - started, 1),
        "cableado": beru_wake.resumen_cableado(),
        "legion": leg,
        "log_disparos": str(beru_fantasma.LOG_PATH),
        "veredicto": "fantasma_sellado — cero órdenes reales",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
    await bellion.anotar(
        "BELLION", "SUCESION",
        "Ritual Beru fantasma sellado — Igris/Greed no dispararon; manos reales OFF.",
    )
    n_disp = 0
    try:
        if beru_fantasma.LOG_PATH.exists():
            n_disp = sum(1 for _ in beru_fantasma.LOG_PATH.open(encoding="utf-8"))
    except Exception:
        pass
    print(
        f"\n[BERU_FANTASMA] Sellado · disparos en bitácora≈{n_disp} · "
        f"informe={REPORT_PATH}",
        flush=True,
    )
    _escribir_hb("sellado", {"n_disparos": n_disp})
    for t in tasks:
        cur = asyncio.current_task()
        if t is not None and t is not cur and not t.done():
            t.cancel()


async def _corte_tiempo(shutdown_event, segundos: float):
    if segundos <= 0:
        return
    await asyncio.sleep(segundos)
    print(f"\n[BERU_FANTASMA] Corte por tiempo ({segundos:.0f}s) — sellando…", flush=True)
    shutdown_event.set()


async def _muleta_ojos_rest(bridge, tank, activos: list[str], shutdown_event):
    """Si el torrente WS muere, rellena precios spot por REST (público vía sesión)."""
    from core import beru_ojos

    await asyncio.sleep(8)
    while not shutdown_event.is_set():
        if beru_ojos.rest_fallback_activo():
            try:
                precios = await asyncio.to_thread(
                    beru_ojos.inyectar_precios_rest, bridge, tank, activos,
                )
                if precios:
                    bits = ",".join(f"{k}={v:.6g}" for k, v in precios.items())
                    print(f"[OJOS_REST] muleta tickers: {bits}", flush=True)
            except Exception as e:
                print(f"[OJOS_REST] fallo: {e}", flush=True)
        try:
            await asyncio.wait_for(
                shutdown_event.wait(),
                timeout=beru_ojos.rest_intervalo_s(),
            )
            break
        except asyncio.TimeoutError:
            continue


def _senales(loop, shutdown_event):
    def _handler(sig, frame):
        loop.call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handler)


def _aplicar_activos(activos: list[str]) -> None:
    config.BERU_FANTASMA_ACTIVOS = ",".join(activos)
    # Flota solo ensayo (temporal en proceso)
    config.ACTIVOS_BERU_FLOTA = list(activos)
    # Semilla = primer Santo con manto (o primero de lista)
    config.BERU_ACTIVO_SEMILLA = activos[0]
    config.TICKER_BASE = activos[0]
    frentes = beru_fantasma.ampliar_ojos_spot(activos)
    bases = beru_fantasma.estrechar_ojos_bridge(activos)
    print(f"[OJOS] Spot vigilancia: {frentes}", flush=True)
    print(
        f"[OJOS] Modo estrecho: {len(bases)} bases · books=OFF · Binance ref OFF · "
        f"bases={','.join(bases)}",
        flush=True,
    )


async def ritual(segundos: float, activos: list[str]):
    print("\n" + "═" * 52)
    print("    RITUAL BERU — MANOS FANTASMA (nivel 2)")
    print("    Ojos Bybit ON · disparos solo bitácora · Igris OFF")
    print(f"    SIM={config.MODO_SIMULACION} | FANTASMA={config.BERU_MANOS_FANTASMA}")
    print(f"    MANOS_REALES={config.BERU_MANOS} | HILO={config.BERU_HILO_ENABLED}")
    print(f"    Santos: {','.join(activos)}")
    print("═" * 52)

    if config.BERU_MANOS and not config.MODO_SIMULACION:
        raise SystemExit("ABORT: manos reales + sim off — este ritual es solo fantasma.")
    if not config.MODO_SIMULACION:
        # Refuerzo: nunca salir de sim en este script
        config.MODO_SIMULACION = True
        print("[!] Forzado MODO_SIMULACION=true (candado ritual).", flush=True)

    _aplicar_activos(activos)
    started = time.time()
    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    _escribir_hb("arranque", {"activos": activos})

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
            print("[BELLION] Recovery: bóveda restaurada.", flush=True)

        kaiser = KaiserVocero(tank, bellion)
        # Igris solo snapshot — SIN vigilar_manto
        igris = IgrisEscudo(tusk, tank, bellion, bridge=bridge, kaiser=kaiser)
        beru = BeruCazador(tusk, bellion, tank, bridge=bridge, kaiser=kaiser)

        from core.validacion import advertir_gates
        advertir_gates()
        panel = PanelDeControl(tusk, igris, tank)

        print("\n[TUSK] Tesorería / oxígeno (solo lectura).", flush=True)
        print("[TANK] Ojos vivos Santos del manto.", flush=True)
        print("[BERU] Hilo ON · manos fantasma · engorde OFF · neutro ON.", flush=True)
        print("[IGRIS/GREED] Hibernados.", flush=True)
        print(f"[BITÁCORA] {beru_fantasma.LOG_PATH}", flush=True)
        print("Ctrl+C para sellar.\n", flush=True)

        beru_fantasma.registrar(
            "RITUAL_START",
            detalle="manos fantasma — cero órdenes reales",
            activos=activos,
            cableado=beru_wake.resumen_cableado(),
        )

        running: list[asyncio.Task] = []

        def _spawn(coro):
            t = asyncio.create_task(coro)
            running.append(t)
            return t

        _spawn(tusk.latido_persistencia(beru.legion))
        _spawn(tusk.hilo_reconciliacion(bridge))
        _spawn(tank.vigilar_aguas())
        _spawn(bridge.conectar())
        _spawn(bridge.hilo_sentidos_extra())
        _spawn(bridge.hilo_sincronizacion_nav())
        _spawn(kaiser.vigilar_indicadores())
        _spawn(beru.hilo_beru_berserker())
        _spawn(_refrescar_panel(panel))
        _spawn(_publicar_estado(bellion, tusk, igris, tank, kaiser, beru))
        _spawn(_cronica_legion(beru))
        _spawn(_muleta_ojos_rest(bridge, tank, activos, shutdown_event))
        _spawn(_apagado(shutdown_event, bellion, tusk, beru, started, running))
        if segundos > 0:
            _spawn(_corte_tiempo(shutdown_event, segundos))
        if binance_ref:
            _spawn(binance_ref.conectar())

        # Siembra asistida tras calentar ojos (precios reales por Santo)
        async def _siembra_asistida():
            await asyncio.sleep(25)
            if shutdown_event.is_set():
                return
            precios = await _rellenar_precios_flota(beru, activos)
            print(f"[BERU] Precios ojos para siembra: {precios}", flush=True)
            if not precios:
                print("[BERU] Sin precios aún — reintento en 20s…", flush=True)
                await asyncio.sleep(20)
                if shutdown_event.is_set():
                    return
                precios = await _rellenar_precios_flota(beru, activos)
                print(f"[BERU] Precios ojos (2º): {precios}", flush=True)
            if precios:
                if not beru.legion:
                    beru._flota_sembrada = False
                n = beru.despertar_flota_reset_0(precios)
                beru_fantasma.registrar(
                    "SIEMBRA_FLOTA",
                    detalle=f"semillas={n}",
                    precios=precios,
                )
                print(f"[BERU] Flota sembrada n={n} legión={len(beru.legion)}", flush=True)
            else:
                print(
                    "[BERU] Aviso: sin precio en ojos — Beru acecha a ciegas hasta que late Tank.",
                    flush=True,
                )

        _spawn(_siembra_asistida())
        await asyncio.gather(*running, return_exceptions=True)

    except Exception:
        print("\n[!] ERROR EN RITUAL BERU FANTASMA:")
        traceback.print_exc()
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description="Beru manos fantasma — ojos reales, cero órdenes")
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_BERU_FANTASMA_S", "1200") or 1200),
        help="Duración del ensayo (default 20 min). 0 = hasta Ctrl+C.",
    )
    ap.add_argument(
        "--activos",
        default=os.getenv("BERU_FANTASMA_ACTIVOS", "ADA,BCH,MNT"),
        help="Santos del manto a vigilar (coma).",
    )
    args = ap.parse_args()
    activos = [a.strip().upper() for a in str(args.activos).split(",") if a.strip()]
    if not activos:
        activos = ["ADA", "BCH", "MNT"]
    asyncio.run(ritual(segundos=float(args.segundos or 0), activos=activos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
