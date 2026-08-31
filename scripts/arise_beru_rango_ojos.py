#!/usr/bin/env python3
"""
Ritual de ojos Beru rango — flota lineal USDT, sin manos.

Multi-Santo sin fila del Beru viejo:
  · cada Santo tiene su propio Bridge (HTTP) + Tank + WS
  · sellos/eventos por carpeta data/beru/rango/{ACTIVO}/
  · panel rango_vivo.json fusiona (no pisa otros procesos)

  python scripts/arise_beru_rango_ojos.py --santos WLD,ONDO,UNI
  python scripts/arise_beru_rango_ojos.py --activo HYPE --segundos 60

Manos OFF siempre en este ritual.
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
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Candados del ritual (antes de importar config)
os.environ["BERU_RANGO_MANOS"] = "false"
os.environ.setdefault("BERU_RANGO_HILO", "true")
os.environ["BRIDGE_WS_SOLO_LINEAR"] = "true"
os.environ["BRIDGE_WS_PUBLIC_TRADES_LINEAR"] = "true"
os.environ.setdefault("BRIDGE_WS_SUBSCRIBE_BOOKS", "false")
os.environ.setdefault("BINANCE_REF_ENABLED", "false")
if os.getenv("ARISE_BERU_RANGO_PERMITIR_MANOS", "").lower() not in ("1", "true", "yes"):
    os.environ["MODO_SIMULACION"] = "true"

import core.config as config  # noqa: E402
from core import beru_rango_ojos  # noqa: E402
from core import beru_rango_panel  # noqa: E402
from core import beru_rango_paths  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from generales.beru_rango import BeruRango  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402

SANTOS_RANGO_19: tuple[str, ...] = (
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "LTC", "AAVE", "HYPE",
    "MNT", "AVAX", "LINK", "NEAR", "OP", "SUI", "UNI", "XLM", "FIL",
)


def santos_rango_default() -> list[str]:
    raw = str(os.getenv("BERU_RANGO_SANTOS", "") or "").strip()
    if raw:
        return [a.strip().upper() for a in raw.split(",") if a.strip()]
    return list(SANTOS_RANGO_19)


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
    print(f"\n[RANGO] Corte por tiempo ({segundos:.0f}s) — sellando…")
    shutdown_event.set()


def _append_evento(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


async def _muleta_rest(bridge, tank, activo: str):
    """Muleta REST de ESTE Santo con SU bridge — no comparte cola."""
    await asyncio.sleep(2.0 + (hash(activo) % 7) * 0.15)
    while True:
        try:
            if beru_rango_ojos.muleta_rest_necesaria(tank):
                beru_rango_ojos.inyectar_precios_rest(bridge, tank, [activo])
        except Exception as exc:
            print(f"[RANGO] {activo} muleta REST: {exc}", flush=True)
        await asyncio.sleep(beru_rango_ojos.rest_intervalo_s())


async def _hilo_santo(
    *,
    activo: str,
    beru_g: BeruRango,
    shutdown_event: asyncio.Event,
    latido_lento_s: float,
    contadores: dict[str, Any],
    eventos_path: Path,
):
    from core import beru_rango as cerebro

    await asyncio.sleep(1.5)
    while not shutdown_event.is_set():
        wait_s = max(0.2, float(latido_lento_s or 1.5))
        try:
            lat = beru_rango_ojos.latido_lineal_desde_tank(beru_g.tank, activo)
            px = float(lat.get("last") or 0) or beru_rango_ojos.last_lineal_desde_tank(
                beru_g.tank, activo
            )
            if px <= 0 and beru_g.bridge is not None:
                beru_rango_ojos.inyectar_precios_rest(
                    beru_g.bridge, beru_g.tank, [activo]
                )
                lat = beru_rango_ojos.latido_lineal_desde_tank(beru_g.tank, activo)
                px = float(lat.get("last") or 0) or beru_rango_ojos.last_lineal_desde_tank(
                    beru_g.tank, activo
                )
            r = await beru_g.pulso(
                precio=px if px > 0 else None,
                latido=lat if px > 0 else None,
            )
            ev = str((r or {}).get("evento") or (r or {}).get("motivo") or "")
            if ev and ev not in ("ACECHO", "CAZA"):
                row = {
                    "ts": time.time(),
                    "activo": activo,
                    "evento": ev,
                    "detalle": r,
                    "pid": os.getpid(),
                }
                contadores["eventos"] = int(contadores.get("eventos") or 0) + 1
                contadores.setdefault("por_evento", {})
                contadores["por_evento"][ev] = int(
                    contadores["por_evento"].get(ev, 0)
                ) + 1
                contadores.setdefault("por_santo", {})
                contadores["por_santo"][activo] = int(
                    contadores["por_santo"].get(activo, 0)
                ) + 1
                _append_evento(eventos_path, row)
                _append_evento(beru_rango_paths.flota_ojos_eventos(), row)
                print(f"[RANGO] {activo} → {ev}", flush=True)
            px = float(px or 0) or beru_rango_ojos.last_lineal_desde_tank(
                beru_g.tank, activo
            )
            try:
                wait_s = cerebro.latido_sugerido_s(
                    beru_g.vivo, px, lento_s=latido_lento_s
                )
            except Exception:
                wait_s = max(0.2, float(latido_lento_s or 1.5))
            try:
                beru_rango_panel.publicar(
                    snapshot=beru_g.snapshot(),
                    last=float(px or 0),
                    activo=activo,
                    merge=True,
                )
            except Exception:
                pass
        except Exception as exc:
            print(f"[RANGO] {activo} pulso error: {exc}", flush=True)
            contadores["errores"] = int(contadores.get("errores") or 0) + 1
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=wait_s)
            break
        except asyncio.TimeoutError:
            pass


async def _cronica_santo(
    *,
    activo: str,
    tank,
    beru_g: BeruRango,
    intervalo_s: float = 15.0,
):
    await asyncio.sleep(5.0 + (hash(activo) % 5) * 0.4)
    while True:
        px = beru_rango_ojos.last_lineal_desde_tank(tank, activo)
        rio = "WS" if beru_rango_ojos.rio_ws_vivo(tank) else "ciego/muleta"
        vivo = (beru_g.snapshot().get("vivo") or {})
        est = str(vivo.get("estado") or "—")
        print(
            f"[RANGO] {activo}USDT_LINEAL last={px} · río={rio} · "
            f"estado={est} · manos=OFF · pid={os.getpid()} · bridge=PROPIO",
            flush=True,
        )
        try:
            beru_rango_panel.publicar(
                snapshot=beru_g.snapshot(),
                last=float(px or 0),
                activo=activo,
                merge=True,
            )
        except Exception as exc:
            print(f"[RANGO] {activo} panel: {exc}", flush=True)
        await asyncio.sleep(intervalo_s)


def _escribir_informe_santo(
    *,
    activo: str,
    contadores: dict[str, Any],
    beru_g: BeruRango,
    tank,
    ts0: float,
    eventos_path: Path,
) -> Path:
    path = beru_rango_paths.ojos_informe(activo)
    informe = {
        "ts": time.time(),
        "duracion_s": round(time.time() - ts0, 1),
        "manos": False,
        "mercado": "linear",
        "activo": activo,
        "pid": os.getpid(),
        "bridge": "propio",
        "contadores": {
            "eventos": contadores.get("eventos"),
            "errores": contadores.get("errores"),
            "por_evento": contadores.get("por_evento"),
            "por_santo": {activo: (contadores.get("por_santo") or {}).get(activo, 0)},
        },
        "last_lineal": beru_rango_ojos.last_lineal_desde_tank(tank, activo),
        "snapshot": beru_g.snapshot(),
        "eventos_path": str(eventos_path),
    }
    path.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


async def _marcha_santo(
    *,
    activo: str,
    shutdown_event: asyncio.Event,
    latido_s: float,
    contadores: dict[str, Any],
    bellion: BellionAuditor,
    tusk: TuskBoveda,
    api_key,
    api_secret,
    stacks: dict[str, Any],
) -> None:
    """Un Santo = un Bridge + un Tank + un cerebro. Sin fila compartida."""
    act = str(activo).upper()
    config.BRIDGE_WS_SOLO_LINEAR = True
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = False
    config.BRIDGE_WS_PUBLIC_TRADES_LINEAR = True

    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    # Bridge propio: HTTP + WS solo de este Santo (sin fila / sin pisar bases globales).
    bridge = BybitBridge(
        tank, tusk, bellion, api_key, api_secret, ws_bases=[act],
    )
    tank.expandir_frentes(beru_rango_ojos.frentes_lineal_tank([act]))
    beru_rango_ojos.inyectar_precios_rest(bridge, tank, [act])

    eventos_path = beru_rango_paths.ojos_eventos(act)
    eventos_path.parent.mkdir(parents=True, exist_ok=True)
    eventos_path.write_text("", encoding="utf-8")

    beru_g = BeruRango(tusk, bellion, tank, bridge=bridge)
    px = beru_rango_ojos.last_lineal_desde_tank(tank, act)
    if px <= 0:
        for _ in range(4):
            await asyncio.sleep(0.35)
            beru_rango_ojos.inyectar_precios_rest(bridge, tank, [act])
            px = beru_rango_ojos.last_lineal_desde_tank(tank, act)
            if px > 0:
                break
    if px <= 0:
        print(f"[RANGO] {act} sin last lineal al wake — se salta", flush=True)
        contadores["errores"] = int(contadores.get("errores") or 0) + 1
        return

    await beru_g.despertar(precio=px, activo=act)
    snap = beru_g.snapshot()
    if snap.get("manos"):
        raise RuntimeError(f"{act}: manos ON en ritual ojos — abort")

    stacks[act] = {
        "tank": tank,
        "bridge": bridge,
        "beru": beru_g,
        "eventos_path": eventos_path,
        "ts0": time.time(),
    }
    print(
        f"[RANGO] Wake {act} 0={px} · manos=OFF · bridge=PROPIO · "
        f"pid={os.getpid()}",
        flush=True,
    )
    try:
        beru_rango_panel.publicar(
            snapshot=snap, last=float(px), activo=act, merge=True,
        )
    except Exception as exc:
        print(f"[RANGO] {act} panel al wake: {exc} — sigue el ritual", flush=True)

    tasks = [
        asyncio.create_task(tank.vigilar_aguas()),
        asyncio.create_task(bridge.conectar()),
        asyncio.create_task(_muleta_rest(bridge, tank, act)),
        asyncio.create_task(
            _hilo_santo(
                activo=act,
                beru_g=beru_g,
                shutdown_event=shutdown_event,
                latido_lento_s=latido_s,
                contadores=contadores,
                eventos_path=eventos_path,
            )
        ),
        asyncio.create_task(
            _cronica_santo(activo=act, tank=tank, beru_g=beru_g)
        ),
    ]
    try:
        await shutdown_event.wait()
    finally:
        path = _escribir_informe_santo(
            activo=act,
            contadores=contadores,
            beru_g=beru_g,
            tank=tank,
            ts0=float(stacks[act]["ts0"]),
            eventos_path=eventos_path,
        )
        try:
            beru_rango_panel.retirar_activo(act)
        except Exception:
            pass
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"[RANGO] Sello {act}: {path}", flush=True)


async def ritual(
    *,
    activos: list[str],
    segundos: float,
    latido_s: float,
) -> dict[str, Any]:
    acts = [str(a).upper() for a in activos if str(a).strip()]
    if not acts:
        raise ValueError("sin Santos")

    config.BERU_RANGO_MANOS = False
    config.MODO_SIMULACION = True  # ritual ojos: nunca órdenes reales
    config.BRIDGE_WS_SOLO_LINEAR = True
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = False
    config.BRIDGE_WS_PUBLIC_TRADES_LINEAR = True
    if hasattr(config, "BINANCE_REF_ENABLED"):
        config.BINANCE_REF_ENABLED = False

    print("\n" + "═" * 56)
    print("    RITUAL OJOS — Beru rango MULTI (lineal USDT)")
    print(f"    Santos: {len(acts)} · manos OFF · bridge PROPIO por Santo")
    print(f"    {', '.join(acts)}")
    print(f"    FASE: {config.FASE_ACTUAL} | SIM={config.MODO_SIMULACION}")
    print("    Oído: tratos públicos ON (mecha trato a trato) · libros OFF")
    print("═" * 56)

    beru_rango_paths.flota_ojos_eventos().parent.mkdir(parents=True, exist_ok=True)
    beru_rango_paths.flota_ojos_eventos().write_text("", encoding="utf-8")

    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    contadores: dict[str, Any] = {
        "eventos": 0, "errores": 0, "por_evento": {}, "por_santo": {},
    }
    ts0 = time.time()
    stacks: dict[str, Any] = {}

    try:
        api_key = getattr(config, "API_KEY", None)
        api_secret = getattr(config, "API_SECRET", None)
        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)

        print(
            f"\n[RANGO] Levantando {len(acts)} puentes independientes "
            f"(sin fila compartida)…",
            flush=True,
        )

        marchas = [
            asyncio.create_task(
                _marcha_santo(
                    activo=act,
                    shutdown_event=shutdown_event,
                    latido_s=latido_s,
                    contadores=contadores,
                    bellion=bellion,
                    tusk=tusk,
                    api_key=api_key,
                    api_secret=api_secret,
                    stacks=stacks,
                )
            )
            for act in acts
        ]
        corte = asyncio.create_task(_corte_tiempo(shutdown_event, segundos))

        print(
            f"[RANGO] Flota multi {len(acts)} · cada uno pide a la API · "
            f"sin disparos. Ctrl+C sella.\n",
            flush=True,
        )

        await shutdown_event.wait()
        print("\n[RANGO] Sellando flota…", flush=True)
        await asyncio.gather(*marchas, return_exceptions=True)
        corte.cancel()

        flota_path = beru_rango_paths.flota_ojos_informe()
        flota_path.write_text(
            json.dumps(
                {
                    "ts": time.time(),
                    "duracion_s": round(time.time() - ts0, 1),
                    "manos": False,
                    "santos": acts,
                    "vivos": list(stacks.keys()),
                    "contadores": contadores,
                    "pid": os.getpid(),
                    "arquitectura": "bridge_propio_por_santo",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        # Espejo legacy resumen
        beru_rango_paths.LEGACY_OJOS_INFORME.parent.mkdir(parents=True, exist_ok=True)
        beru_rango_paths.LEGACY_OJOS_INFORME.write_text(
            flota_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        await bellion.anotar(
            "BERU_RANGO", "SUCESION",
            f"Ritual ojos multi sellado · {len(stacks)} Santos · sin manos · {flota_path}",
        )
        print(
            f"[RANGO] Informe flota: {flota_path} · eventos={contadores.get('eventos')} · "
            f"errores={contadores.get('errores')}",
            flush=True,
        )
        print(f"[RANGO] Por evento: {contadores.get('por_evento')}", flush=True)
        print(f"[RANGO] Por santo: {contadores.get('por_santo')}", flush=True)
        return {"ok": True, "informe": str(flota_path), "contadores": contadores}

    except Exception:
        print("\n[!] ERROR EN RITUAL OJOS BERU RANGO MULTI:")
        traceback.print_exc()
        raise


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Ojos Beru rango multi-Santo (bridge propio, sin manos)"
    )
    ap.add_argument("--activo", default="", help="Un solo Santo")
    ap.add_argument(
        "--santos",
        default="",
        help="CSV de Santos (override). Vacío = 19 Santos.",
    )
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_BERU_RANGO_SEGUNDOS", "0") or 0),
        help="Si >0, corta tras N segundos",
    )
    ap.add_argument(
        "--latido",
        type=float,
        default=float(os.getenv("BERU_RANGO_LATIDO_LENTO_S", "1.5") or 1.5),
        help="Latido LENTO (s); cerca de oreja/cazando acelera",
    )
    args = ap.parse_args()

    if str(args.activo or "").strip():
        activos = [str(args.activo).upper()]
    elif str(args.santos or "").strip():
        activos = [a.strip().upper() for a in str(args.santos).split(",") if a.strip()]
    else:
        activos = santos_rango_default()

    asyncio.run(
        ritual(
            activos=activos,
            segundos=float(args.segundos or 0),
            latido_s=float(args.latido or 1.5),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
