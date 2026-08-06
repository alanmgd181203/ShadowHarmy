#!/usr/bin/env python3
"""
4.0.3 — Igris live parcial: manos sueltas, ojos con libros.

Despierta: Tusk (oxígeno) · Tank (orderbook real) · Kaiser · Igris (manto).
NO despierta: Greed · Beru.
Manos reales: ON (MODO_SIMULACION=False).
Bóveda manos Convert: OFF (TUSK_BOVEDA_MANOS no se enciende).
Books: ON (BRIDGE_WS_SUBSCRIBE_BOOKS=true) — no ojos estrechos de la sim.

  python scripts/arise_igris.py --solo-ojos --segundos 90
  python scripts/arise_igris.py --segundos 90
  python scripts/arise_igris.py --durar-hasta 2026-08-05T18:30:00 --permitir-mainnet-manos

ABORTA mainnet manos sin --permitir-mainnet-manos / ARISE_IGRIS_PERMITIR_MAINNET.
Respeta marcha en data/marcha_despliegue.json.
Reporte: data/arise_igris_report.json · logs: data/logs/arise_igris/
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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# --- Sesión 4.0.3 (antes de importar config) — no reescribe .env ---
os.environ["ARISE_IGRIS_LIVE"] = "true"
os.environ["MODO_SIMULACION"] = "False"
os.environ["BRIDGE_WS_SUBSCRIBE_BOOKS"] = "true"
os.environ.setdefault("TUSK_BOVEDA_MANOS", "false")
os.environ.setdefault("ARENA_IGRIS_ACTIVA", "false")
os.environ.setdefault("ARENA_IGRIS_FILLS_VIRTUALES", "false")
os.environ.setdefault("GREED_KAISER_ENABLED", "false")
os.environ.setdefault("GREED_VIP_ENABLED", "false")
os.environ.setdefault("GREED_BASIS_HOLD_ENABLED", "false")
os.environ.setdefault("GREED_MULTICRUCE_ENABLED", "false")
os.environ.setdefault("SAFE_MODE", "true")
os.environ.setdefault("IGRIS_EVENT_DRIVEN", "true")
os.environ.setdefault("IGRIS_BOOTSTRAP_ON_START", "false")
# Canal paralelo: manto dual ETH exclusivo; MNT colateral intocable
os.environ.setdefault("TICKER_BASE", "ETH")
os.environ.setdefault("IGRIS_ACTIVOS_EXCLUSIVOS", "ETH")
os.environ.setdefault("IGRIS_PROTEGER_BASES", "MNT")
os.environ.setdefault("IGRIS_PROTEGER_SYMBOLS", "MNTUSD")
# Con books reales: puerta §E no debe depender del ticker sintético
os.environ.setdefault("IGRIS_TICKER_PUERTA_SI_SIN_LIBRO", "false")
os.environ.setdefault("BYBIT_RECV_WINDOW_MS", "60000")
os.environ.setdefault("BRIDGE_WS_FORCE_IPV4", "true")
# No forzar MODO_TESTNET: respeta .env / entorno

import core.config as config  # noqa: E402

config.MODO_SIMULACION = False
config.ARISE_IGRIS_LIVE = True
config.BRIDGE_WS_SUBSCRIBE_BOOKS = True
if hasattr(config, "TUSK_BOVEDA_MANOS"):
    config.TUSK_BOVEDA_MANOS = False
config.ARENA_IGRIS_ACTIVA = False
if hasattr(config, "ARENA_IGRIS_FILLS_VIRTUALES"):
    config.ARENA_IGRIS_FILLS_VIRTUALES = False
config.GREED_KAISER_ENABLED = False
config.GREED_VIP_ENABLED = False
config.GREED_BASIS_HOLD_ENABLED = False
config.GREED_MULTICRUCE_ENABLED = False
config.SAFE_MODE = True
config.IGRIS_EVENT_DRIVEN = True
if hasattr(config, "IGRIS_BOOTSTRAP_ON_START"):
    config.IGRIS_BOOTSTRAP_ON_START = False
config.IGRIS_TICKER_PUERTA_SI_SIN_LIBRO = "false"
config.BYBIT_RECV_WINDOW_MS = int(float(os.getenv("BYBIT_RECV_WINDOW_MS", "60000") or 60000))
if hasattr(config, "BRIDGE_WS_FORCE_IPV4"):
    config.BRIDGE_WS_FORCE_IPV4 = True
# Frente de combate: ETH dual; MNT fuera del canal
config.TICKER_BASE = "ETH"
config.SIMBOLO_LINEAR = "ETHUSDT"
config.FRENTE_PRINCIPAL = "ETHUSDT_LINEAL"
config.IGRIS_ACTIVOS_EXCLUSIVOS = ["ETH"]
config.IGRIS_PROTEGER_BASES = ["MNT"]
config.IGRIS_PROTEGER_SYMBOLS = ["MNTUSD"]

from core.bellion import BellionAuditor  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from core.dashboard import PanelDeControl  # noqa: E402
from generales.igris import IgrisEscudo  # noqa: E402
from generales.kaiser import KaiserVocero  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402

LOG_DIR = ROOT / "data" / "logs" / "arise_igris"
REPORT_PATH = ROOT / "data" / "arise_igris_report.json"
HEARTBEAT_PATH = LOG_DIR / "heartbeat.json"


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")


def _parse_deadline(raw: str) -> float | None:
    s = (raw or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return None


def _segundos_desde_flags(
    *,
    segundos: float,
    horas: float,
    durar_hasta: str,
) -> float:
    """Devuelve segundos de corte (>0) o 0 = sin corte por tiempo."""
    dl = _parse_deadline(durar_hasta)
    if dl is not None:
        remaining = dl - time.time()
        if remaining <= 0:
            raise SystemExit(f"ABORT: --durar-hasta ya pasó ({durar_hasta})")
        return remaining
    if horas and horas > 0:
        return float(horas) * 3600.0
    return float(segundos or 0)


def _aplicar_ojos_abiertos(tusk) -> list[str]:
    """Canal paralelo ETH: libros solo del manto dual (MNT colateral no opera)."""
    out = ["ETH"]
    config.TICKER_BASE = "ETH"
    config.BRIDGE_WS_BASES = out
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = True
    # Solo ETH: no ahogar el calentamiento con 13 orderbooks
    config.BRIDGE_WS_BOOKS_BASES = ["ETH"]
    config.IGRIS_ACTIVOS_EXCLUSIVOS = ["ETH"]
    print("[OJOS] Canal paralelo ETH exclusivo · books=ON · MNT protegido (colateral)")
    print(f"[OJOS] Bases: {', '.join(out)} · books={config.BRIDGE_WS_BOOKS_BASES}")
    return out


def _libros_eth(tank) -> dict:
    """Evidencia de libros en frentes ETH (bids/asks + edad)."""
    from core import igris_despliegue as ides
    from core import igris_ojos as ojos

    frentes = ("ETHUSDT_LINEAL", "ETHUSD_INVERSE")
    detalle = {}
    ok_alguno = False
    stale_alguno = False
    for f in frentes:
        bids, asks = ides.libro_tank(tank, f)
        n_b, n_a = len(bids or []), len(asks or [])
        meta = ojos.meta_libro(tank, f)
        detalle[f] = {
            "bids": n_b,
            "asks": n_a,
            "edad_s": meta.get("edad_s"),
            "stale": meta.get("stale"),
        }
        if n_b > 0 and n_a > 0:
            ok_alguno = True
        if meta.get("stale"):
            stale_alguno = True
    return {"ok": ok_alguno and not stale_alguno, "frentes": detalle, "stale": stale_alguno}


def _escribir_heartbeat(msg: str, extra: dict | None = None) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.time(),
        "iso": datetime.now().isoformat(timespec="seconds"),
        "msg": msg,
        "pid": os.getpid(),
    }
    if extra:
        payload.update(extra)
    try:
        HEARTBEAT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _snapshot_cierre(tusk, igris, *, solo_ojos: bool, libros: dict | None) -> dict:
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
        "checklist": "4.0.3",
        "sim": False,
        "manos_reales": not solo_ojos,
        "solo_ojos": solo_ojos,
        "books_on": True,
        "libros_eth": libros,
        "testnet": bool(getattr(config, "TESTNET", True)),
        "marcha_id": mid,
        "marcha_payload": {
            "fill_ratio": payload.get("fill_ratio"),
            "reserva_pasos": payload.get("reserva_pasos"),
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
        "greed_hibernado": True,
        "beru_hibernado": True,
        "boveda_manos": False,
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


async def _cronica(tusk, tank, intervalo_s: float = 30.0):
    await asyncio.sleep(10)
    from core import pase_director as pd

    while True:
        mid = pd.cargar_marcha()
        eq = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
        tes = getattr(tusk, "tesoreria", None) or {}
        lib = _libros_eth(tank)
        n_pesos = sum(
            float(p.get("long") or 0) + float(p.get("short") or 0)
            for p in (getattr(tusk, "pesos", {}) or {}).values()
        )
        print(
            f"[LIVE] marcha={mid} | equity={eq:.2f} | O2={tes.get('oxigeno_guerra_usd')} | "
            f"masa_auth={getattr(tusk, 'masa_autorizada', None)} | pesos≈{n_pesos:.4f} | "
            f"books_eth={lib.get('ok')} stale={lib.get('stale')} | "
            f"SIM={config.MODO_SIMULACION} | TN={config.TESTNET}"
        )
        _escribir_heartbeat(
            "cronica",
            {
                "marcha": mid,
                "equity": eq,
                "books_eth": lib.get("ok"),
                "books_stale": lib.get("stale"),
                "libros_eth": lib.get("frentes"),
                "ciclos": int(time.time()),
            },
        )
        await asyncio.sleep(intervalo_s)


async def _esperar_ojos_y_libros(
    tank,
    *,
    timeout_s: float = 120.0,
    shutdown_event: asyncio.Event | None = None,
) -> tuple[bool, bool, dict]:
    """Calentamiento: Tank VERDE + libros ETH (bids/asks)."""
    base = str(getattr(config, "TICKER_BASE", "ETH") or "ETH").upper()
    keys = (f"{base}USDT_LINEAL", f"{base}USD_INVERSE", "ETHUSDT_LINEAL", "ETHUSD_INVERSE")
    t0 = time.time()
    print(f"[OJOS] Calentamiento VERDE + libros ETH (hasta {timeout_s:.0f}s)…")
    verde_ok = False
    libros: dict = {"ok": False, "frentes": {}}
    while time.time() - t0 < timeout_s:
        if shutdown_event is not None and shutdown_event.is_set():
            print("[OJOS] Calentamiento abortado (apagado).")
            return False, False, libros
        try:
            tank._auditar_semaforos()
        except Exception:
            pass
        lider = None
        try:
            lider = tank._obtener_lider_verde()
        except Exception:
            lider = None
        if lider and getattr(lider, "estado_foco", "") == "VERDE":
            px = lider.precios_con_reflejo() or {}
            if any(float(px.get(k) or 0) > 0 for k in keys):
                verde_ok = True
        libros = _libros_eth(tank)
        if verde_ok and libros.get("ok"):
            print(
                f"[OJOS] VERDE+libros OK lat={getattr(lider, 'latencia_ms', 0):.0f}ms · "
                f"{libros.get('frentes')}"
            )
            return True, True, libros
        await asyncio.sleep(1.0)
    print(
        f"[OJOS] Timeout calentamiento — verde={verde_ok} libros={libros.get('ok')} "
        f"detalle={libros.get('frentes')}"
    )
    return verde_ok, bool(libros.get("ok")), libros


async def _apagado(
    shutdown_event,
    bellion,
    tusk,
    igris,
    started: float,
    tasks: list,
    *,
    solo_ojos: bool,
    libros_ref: dict,
):
    await shutdown_event.wait()
    snap = _snapshot_cierre(tusk, igris, solo_ojos=solo_ojos, libros=libros_ref.get("libros"))
    snap["duracion_s"] = round(time.time() - started, 1)
    snap["veredicto_calentamiento"] = libros_ref.get("veredicto")
    try:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / "ultimo_reporte.json").write_text(
            json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n[LIVE] Reporte → {REPORT_PATH}")
        print(
            f"[LIVE] marcha={snap.get('marcha_id')} | meta_restante="
            f"{(snap.get('meta_engorde') or {}).get('restante_usd')} | "
            f"ventana={(snap.get('ventana_manto') or {}).get('estado')} | "
            f"books={(snap.get('libros_eth') or {}).get('ok')}"
        )
    except OSError as e:
        print(f"[LIVE] No se pudo escribir reporte: {e}")
    _escribir_heartbeat("sellado", {"sellado": True})
    try:
        await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
        await bellion.anotar(
            "BELLION",
            "SUCESION",
            "Ritual Igris LIVE 4.0.3 sellado — Greed/Beru hibernados.",
        )
    except Exception as e:
        print(f"[LIVE] Aviso sucesión: {e}")
    for t in tasks:
        if not t.done():
            t.cancel()
    # WS Bridge a veces no suelta el handshake — no dejar zombie tras sello
    async def _salida_dura():
        await asyncio.sleep(6)
        print("[LIVE] Salida dura tras sello (WS no cede).")
        os._exit(0)

    asyncio.create_task(_salida_dura())


async def _corte_tiempo(shutdown_event, segundos: float):
    if segundos <= 0:
        return
    await asyncio.sleep(segundos)
    print(f"\n[LIVE] Corte por tiempo ({segundos:.0f}s) — sellando…")
    shutdown_event.set()


def _senales(loop, shutdown_event):
    def _handler(sig, frame):
        loop.call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handler)


def _gate_seguridad(*, solo_ojos: bool, permitir_mainnet: bool) -> None:
    if not config.API_KEY or not config.API_SECRET:
        raise SystemExit("ABORT: faltan BYBIT_API_KEY / BYBIT_API_SECRET en .env")
    if config.MODO_SIMULACION:
        raise SystemExit("ABORT: MODO_SIMULACION debe ser False en 4.0.3")
    # Mainnet manos: exige bandera explícita (ojos-solo pueden mirar mainnet WS)
    if not bool(getattr(config, "TESTNET", True)) and not solo_ojos:
        if not permitir_mainnet:
            raise SystemExit(
                "ABORT: manos mainnet sin flag de seguridad.\n"
                "  Usa --permitir-mainnet-manos o ARISE_IGRIS_PERMITIR_MAINNET=true\n"
                "  (preferible: MODO_TESTNET=True en campo de entrenamiento)."
            )
        print("[SEGURIDAD] Mainnet manos AUTORIZADAS por flag explícito.")
    elif bool(getattr(config, "TESTNET", True)):
        print("[SEGURIDAD] Campo de entrenamiento (testnet) — manos DEMO.")


async def ritual_igris_live(
    *,
    segundos: float = 0.0,
    solo_ojos: bool = False,
    permitir_mainnet: bool = False,
):
    from core import pase_director as pd

    _gate_seguridad(solo_ojos=solo_ojos, permitir_mainnet=permitir_mainnet)

    mid = pd.cargar_marcha()
    perfil = pd.perfil_marcha(mid)
    modo = "SOLO OJOS (sin Igris manos)" if solo_ojos else "MANOS SUELTAS (Igris manto)"
    print("\n" + "═" * 52)
    print("    4.0.3  RITUAL IGRIS LIVE (parcial)")
    print("    Kaiser · Tank · Tusk · Igris")
    print(f"    {modo}")
    print("    Canal ETH exclusivo · MNTUSD colateral intocable")
    print("    Greed / Beru hibernados · bóveda Convert OFF")
    print(f"    Books ON · TESTNET={config.TESTNET} · SIM={config.MODO_SIMULACION}")
    print(f"    Marcha: {mid} · fill={perfil.get('fill_ratio')} · reserva={perfil.get('reserva_pasos')}")
    print("═" * 52)

    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    started = time.time()
    running: list[asyncio.Task] = []
    libros_ref: dict = {"libros": None, "veredicto": None}
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _escribir_heartbeat("arranque", {"solo_ojos": solo_ojos, "marcha": mid})

    try:
        api_key = getattr(config, "API_KEY", None)
        api_secret = getattr(config, "API_SECRET", None)

        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
        bridge = BybitBridge(tank, tusk, bellion, api_key, api_secret)
        binance_ref = None
        if getattr(config, "BINANCE_REF_ENABLED", True):
            try:
                from core.binance_ref import BinanceRefBridge

                binance_ref = BinanceRefBridge(tank, bellion)
            except Exception as e:
                print(f"[OJOS] Binance ref omitido: {e}")

        estado_prev = bellion.cargar_estado()
        if estado_prev:
            tusk.restaurar_desde_bellion(estado_prev.get("boveda", {}))
            print("[BELLION] Recovery: bóveda restaurada.")

        _aplicar_ojos_abiertos(tusk)

        kaiser = KaiserVocero(tank, bellion)
        igris = IgrisEscudo(tusk, tank, bellion, bridge=bridge, kaiser=kaiser)

        from core.validacion import advertir_gates

        advertir_gates()

        panel = PanelDeControl(tusk, igris, tank)

        print("\n[TUSK] Oxígeno real → masa_autorizada (Convert ritual OFF).")
        print("[TANK] Ojos abiertos con orderbook.")
        print("[GREED/BERU] Hibernados.")
        if solo_ojos:
            print("[IGRIS] Hibernado (--solo-ojos).")
        print("Ctrl+C para sellar.\n")

        await bellion.anotar(
            "IGRIS",
            "LIVE_START",
            f"4.0.3 arranque · marcha={mid} · solo_ojos={solo_ojos} · "
            f"testnet={config.TESTNET} · books=ON · sin Greed/Beru",
        )

        def _spawn(coro):
            t = asyncio.create_task(coro)
            running.append(t)
            return t

        _spawn(tusk.latido_persistencia([]))
        _spawn(tusk.hilo_reconciliacion(bridge))
        _spawn(tank.vigilar_aguas())
        _spawn(bridge.conectar())
        _spawn(bridge.hilo_sincronizacion_nav())
        _spawn(_refrescar_panel(panel))
        _spawn(_publicar_estado(bellion, tusk, igris, tank, kaiser))
        _spawn(_cronica(tusk, tank))
        _spawn(
            _apagado(
                shutdown_event,
                bellion,
                tusk,
                igris,
                started,
                running,
                solo_ojos=solo_ojos,
                libros_ref=libros_ref,
            )
        )

        verde_ok, libros_ok, libros = await _esperar_ojos_y_libros(
            tank,
            timeout_s=float(os.getenv("ARISE_IGRIS_CALENTAMIENTO_S", "300") or 300),
            shutdown_event=shutdown_event,
        )
        libros_ref["libros"] = libros
        if verde_ok and libros_ok:
            libros_ref["veredicto"] = "OJOS_Y_LIBROS_OK"
        elif verde_ok:
            libros_ref["veredicto"] = "VERDE_SIN_LIBROS"
        else:
            libros_ref["veredicto"] = "OJOS_DEBILES"

        _escribir_heartbeat(
            "post_calentamiento",
            {"veredicto": libros_ref["veredicto"], "libros": libros},
        )

        if shutdown_event.is_set():
            for t in running:
                t.cancel()
            await asyncio.gather(*running, return_exceptions=True)
            return

        if not libros_ok:
            await bellion.anotar(
                "TANK",
                "LIBROS_AUSENTES",
                f"4.0.3 sin evidencia books ETH: {libros}",
            )
            print("[!] BLOQUEO: sin libros ETH (bids/asks). No se suelta Igris.")
            print("[!] Documentando y sellando — no zombie.")
            # Escribir reporte de bloqueo y salir limpio
            snap = _snapshot_cierre(tusk, igris, solo_ojos=True, libros=libros)
            snap["duracion_s"] = round(time.time() - started, 1)
            snap["veredicto_calentamiento"] = libros_ref["veredicto"]
            snap["bloqueo"] = "sin_libros_eth"
            REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            REPORT_PATH.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
            _escribir_heartbeat("bloqueo_sin_libros", {"sellado": True, "bloqueo": True})
            shutdown_event.set()
            for t in running:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*running, return_exceptions=True)
            raise SystemExit(2)

        # Tras ojos+libros: Kaiser / sentidos
        _spawn(kaiser.vigilar_indicadores())
        _spawn(bridge.hilo_sentidos_extra())
        if binance_ref:
            _spawn(binance_ref.conectar())

        if segundos > 0:
            _spawn(_corte_tiempo(shutdown_event, segundos))

        if solo_ojos:
            print("[OJOS] Smoke solo-ojos — Igris no arranca. Observando libros…")
            await bellion.anotar("IGRIS", "SOLO_OJOS", "calentamiento OK · sin manos Igris")
        else:
            print("[IGRIS] vigilar_manto_operativo — manos reales ON.")
            if not verde_ok:
                await bellion.anotar("TANK", "OJOS_DEBILES", "Igris arranca con verde flojo.")
            _spawn(igris.vigilar_manto_operativo())

        await asyncio.gather(*running, return_exceptions=True)

    except SystemExit:
        raise
    except Exception:
        print("\n[!] ERROR EN RITUAL IGRIS LIVE:")
        traceback.print_exc()
        for t in running:
            t.cancel()
        raise


def main():
    ap = argparse.ArgumentParser(description="4.0.3 Igris live parcial — books ON, manos sueltas")
    ap.add_argument("--segundos", type=float, default=0.0, help="Corte tras N s (post-arranque total)")
    ap.add_argument("--horas", type=float, default=0.0, help="Duración en horas")
    ap.add_argument(
        "--durar-hasta",
        type=str,
        default="",
        help="Deadline local YYYY-MM-DDTHH:MM:SS",
    )
    ap.add_argument(
        "--solo-ojos",
        action="store_true",
        help="Calentamiento books sin Igris manos (smoke)",
    )
    ap.add_argument(
        "--permitir-mainnet-manos",
        action="store_true",
        help="Obligatorio si MODO_TESTNET=False y se sueltan manos Igris",
    )
    args = ap.parse_args()

    permitir = args.permitir_mainnet_manos or _truthy(os.getenv("ARISE_IGRIS_PERMITIR_MAINNET"))
    try:
        seg = _segundos_desde_flags(
            segundos=args.segundos,
            horas=args.horas,
            durar_hasta=args.durar_hasta,
        )
    except SystemExit as e:
        print(e)
        raise SystemExit(2) from e

    # Default smoke-friendly si no hay duración (guardián suele pasar deadline)
    if seg <= 0 and not args.durar_hasta and args.horas <= 0 and args.segundos <= 0:
        print("[LIVE] Sin duración: corre hasta Ctrl+C (guardián debe pasar --durar-hasta).")

    asyncio.run(
        ritual_igris_live(
            segundos=seg,
            solo_ojos=args.solo_ojos,
            permitir_mainnet=permitir,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        code = int(e.code) if isinstance(e.code, int) else (1 if e.code else 0)
        raise SystemExit(code)
