#!/usr/bin/env python3
"""Ritual Beru — manos chiquitas (nivel 3 ensayo).

Ojos reales Bybit · Beru late · place_order REAL con techos · todo en consola.
Igris/Greed dormidos. Neutro margen · engorde OFF · solo LONG · 1 Santo default.

  python3 scripts/arise_beru_manos_chiquitas.py --segundos 900
  python3 scripts/arise_beru_manos_chiquitas.py --segundos 600 --activos MNT --max-ordenes 1

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

# Candados ritual nivel 3 (antes de importar config)
os.environ["ARISE_BERU_MANOS_CHIQUITAS"] = "true"
os.environ["BERU_ENSAYO_NIVEL3"] = "true"
os.environ["MODO_SIMULACION"] = "false"          # órdenes reales
os.environ["BERU_MANOS_FANTASMA"] = "false"       # si fantasma ON, no place_order
os.environ["BERU_HILO_ENABLED"] = "true"
os.environ["BERU_MANOS"] = "true"                # manos reales ON
os.environ["BERU_ENGORDE_PERMITIDO"] = "false"
os.environ["BERU_NEUTRO_MARGEN"] = "true"
os.environ["BERU_SPOT_MARGEN_ENABLED"] = "false"
os.environ["BERU_WAKE_RESET_0"] = "true"
os.environ["BERU_CAPITAN_WAKE"] = "NORMAL"
os.environ.setdefault("BERU_SIEMBRA_FLOTA", "true")
os.environ.setdefault("ARISE_BERU_ARMADO", "true")
os.environ.setdefault("BERU_ENSAYO_SOLO_LONG", "true")
os.environ.setdefault("BERU_ENSAYO_MAX_ORDENES", "1")
# Mordida = G_min (~$5 MNT) si no override
# Ojos estrechos
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

# Forzar candados en proceso (por si config ya estaba importado en otro sitio)
config.BERU_ENSAYO_NIVEL3 = True
config.MODO_SIMULACION = False
config.BERU_MANOS_FANTASMA = False
config.BERU_MANOS = True
config.BERU_HILO_ENABLED = True
config.BERU_ENGORDE_PERMITIDO = False
config.BERU_NEUTRO_MARGEN = True
config.BERU_SPOT_MARGEN_ENABLED = False

from core import beru_ensayo  # noqa: E402
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

HB_PATH = ROOT / "data" / "logs" / "beru_ensayo" / "heartbeat.json"
REPORT_PATH = ROOT / "data" / "logs" / "beru_ensayo" / "ultimo_informe.json"


def _escribir_hb(msg: str, extra: dict | None = None) -> None:
    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "msg": msg,
        "nivel": 3,
        "sim": bool(config.MODO_SIMULACION),
        "manos": bool(config.BERU_MANOS),
        "manos_fantasma": bool(config.BERU_MANOS_FANTASMA),
        "hilo": bool(config.BERU_HILO_ENABLED),
        "ordenes_ok": beru_ensayo.ordenes_ok(),
        "max_ordenes": beru_ensayo.max_ordenes(),
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


async def _cronica_legion(beru: BeruCazador, intervalo_s: float = 15.0):
    await asyncio.sleep(8)
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
            f"LIVE manos={config.BERU_MANOS} cazas={beru_ensayo.ordenes_ok()}/"
            f"{beru_ensayo.max_ordenes()} solo_long={beru_ensayo.solo_long()}",
            flush=True,
        )
        _escribir_hb(
            "cronica",
            {"casa": casa, "precio": px, "n_legion": n, "estados": estados},
        )
        await asyncio.sleep(intervalo_s)


async def _rellenar_precios_flota(beru: BeruCazador, activos: list[str]) -> dict[str, float]:
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
        "nivel": 3,
        "cableado": beru_wake.resumen_cableado(),
        "ensayo": beru_ensayo.resumen_modo(),
        "legion": leg,
        "log_disparos": str(beru_ensayo.LOG_PATH),
        "veredicto": (
            f"nivel3_sellado — cazas_ok={beru_ensayo.ordenes_ok()} "
            f"max={beru_ensayo.max_ordenes()}"
        ),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
    await bellion.anotar(
        "BELLION", "SUCESION",
        "Ritual Beru nivel 3 sellado — manos chiquitas; Igris/Greed no dispararon.",
    )
    n_disp = 0
    try:
        if beru_ensayo.LOG_PATH.exists():
            n_disp = sum(1 for _ in beru_ensayo.LOG_PATH.open(encoding="utf-8"))
    except Exception:
        pass
    print(
        f"\n[BERU_LIVE] Sellado · cazas_ok={beru_ensayo.ordenes_ok()} · "
        f"líneas bitácora≈{n_disp} · informe={REPORT_PATH}",
        flush=True,
    )
    _escribir_hb("sellado", {"n_lineas": n_disp})
    for t in tasks:
        cur = asyncio.current_task()
        if t is not None and t is not cur and not t.done():
            t.cancel()


async def _corte_tiempo(shutdown_event, segundos: float):
    if segundos <= 0:
        return
    await asyncio.sleep(segundos)
    print(f"\n[BERU_LIVE] Corte por tiempo ({segundos:.0f}s) — sellando…", flush=True)
    shutdown_event.set()


async def _muleta_ojos_rest(bridge, tank, activos: list[str], shutdown_event):
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
    config.BERU_ENSAYO_ACTIVOS = ",".join(activos)
    config.BERU_FANTASMA_ACTIVOS = ",".join(activos)  # ojos helpers reusan lista
    config.ACTIVOS_BERU_FLOTA = list(activos)
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


async def ritual(segundos: float, activos: list[str], max_ordenes: int, solo_long: bool):
    config.BERU_ENSAYO_MAX_ORDENES = max(1, int(max_ordenes))
    config.BERU_ENSAYO_SOLO_LONG = bool(solo_long)
    beru_ensayo.reset_contadores()

    print("\n" + "═" * 52)
    print("    RITUAL BERU — MANOS CHIQUITAS (nivel 3)")
    print("    Órdenes REALES · techo · solo LONG · Igris OFF")
    print(f"    SIM={config.MODO_SIMULACION} | FANTASMA={config.BERU_MANOS_FANTASMA}")
    print(f"    MANOS_REALES={config.BERU_MANOS} | HILO={config.BERU_HILO_ENABLED}")
    print(
        f"    max_cazas={config.BERU_ENSAYO_MAX_ORDENES} | "
        f"solo_long={config.BERU_ENSAYO_SOLO_LONG}",
    )
    print(f"    Santos: {','.join(activos)}")
    print("═" * 52)

    if config.MODO_SIMULACION:
        raise SystemExit("ABORT: SIM no puede estar ON en nivel 3.")
    if config.BERU_MANOS_FANTASMA:
        raise SystemExit("ABORT: fantasma ON bloquearía place_order — apágalo.")
    if not config.BERU_MANOS:
        raise SystemExit("ABORT: manos reales OFF — nivel 3 requiere BERU_MANOS.")
    if not config.BERU_ENSAYO_NIVEL3:
        raise SystemExit("ABORT: BERU_ENSAYO_NIVEL3 debe estar ON.")

    _aplicar_activos(activos)
    started = time.time()
    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    _escribir_hb("arranque", {"activos": activos})

    try:
        api_key = getattr(config, "API_KEY", None)
        api_secret = getattr(config, "API_SECRET", None)
        if not api_key or not api_secret:
            raise SystemExit("ABORT: faltan llaves Bybit — sin manos no hay nivel 3.")

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
        igris = IgrisEscudo(tusk, tank, bellion, bridge=bridge, kaiser=kaiser)
        beru = BeruCazador(tusk, bellion, tank, bridge=bridge, kaiser=kaiser)

        from core.validacion import advertir_gates
        advertir_gates()
        panel = PanelDeControl(tusk, igris, tank)

        print("\n[TUSK] Tesorería / oxígeno.", flush=True)
        print("[TANK] Ojos vivos Santos del ensayo.", flush=True)
        print(
            "[BERU] Hilo ON · MANOS REALES · engorde OFF · neutro ON · "
            f"techo {beru_ensayo.max_ordenes()} caza(s).",
            flush=True,
        )
        print("[IGRIS/GREED] Hibernados.", flush=True)
        print(f"[BITÁCORA] {beru_ensayo.LOG_PATH}", flush=True)
        print("Mira la consola: líneas [BERU_LIVE] = disparos reales.", flush=True)
        print("Ctrl+C para sellar.\n", flush=True)

        beru_ensayo.registrar(
            "RITUAL_START",
            detalle="manos chiquitas — place_order real con techo",
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
                beru_ensayo.registrar(
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
        print("\n[!] ERROR EN RITUAL BERU NIVEL 3:")
        traceback.print_exc()
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description="Beru manos chiquitas — nivel 3 live acotado")
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_BERU_NIVEL3_S", "900") or 900),
        help="Duración del ensayo (default 15 min). 0 = hasta Ctrl+C.",
    )
    ap.add_argument(
        "--activos",
        default=os.getenv("BERU_ENSAYO_ACTIVOS", "MNT"),
        help="Santos a vigilar (coma). Default: MNT.",
    )
    ap.add_argument(
        "--max-ordenes",
        type=int,
        default=int(float(os.getenv("BERU_ENSAYO_MAX_ORDENES", "1") or 1)),
        help="Techo de cazas reales (default 1).",
    )
    ap.add_argument(
        "--solo-long",
        action=argparse.BooleanOptionalAction,
        default=os.getenv("BERU_ENSAYO_SOLO_LONG", "true").lower() == "true",
        help="Solo LONG (default ON). Evita vender sin inventario.",
    )
    args = ap.parse_args()
    activos = [a.strip().upper() for a in str(args.activos).split(",") if a.strip()]
    if not activos:
        activos = ["MNT"]
    asyncio.run(
        ritual(
            segundos=float(args.segundos or 0),
            activos=activos,
            max_ordenes=int(args.max_ordenes or 1),
            solo_long=bool(args.solo_long),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
