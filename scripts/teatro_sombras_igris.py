#!/usr/bin/env python3
"""Teatro de sombras Igris — 1 óptica + 4 marchas de papel.

Laboratorio pre-4.0.3. NO suelta manos. NO es 4×arise peleando por la bóveda.
NO despierta Igris / Greed / Beru reales.

Preparar (sanidad, segundos, siempre sintético):
  python3 scripts/teatro_sombras_igris.py --preparar

GO serio (óptica Tank viva — un Bridge + un Tank, tickers estrechos):
  python3 scripts/teatro_sombras_igris.py --go --optica-tank --horas 8 --intervalo 5

GO demo sin mercado (sintético — default seguro si no pasas --optica-tank):
  python3 scripts/teatro_sombras_igris.py --go --sintetico --segundos 30

Con deadline:
  python3 scripts/teatro_sombras_igris.py --go --optica-tank --durar-hasta 2026-08-05T08:00:00

Libros reales (pesado; default OFF como arise_igris_sim):
  python3 scripts/teatro_sombras_igris.py --go --optica-tank --con-libros --segundos 60

Política óptica (segura):
  · --preparar → siempre sintético
  · --go sin --optica-tank → sintético + aviso (GO serio exige --optica-tank)
  · --go --optica-tank → Tank vivo; si no conecta, ABORTA (no finge mercado)
  · --sintetico gana sobre --optica-tank si ambos

Guardián (solo tras GO explícito): ver scripts/vigilar_teatro_sombras.py
Salida: data/logs/teatro_sombras/
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
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

# Candados de ritual — antes de importar config / Bridge
os.environ.setdefault("MODO_SIMULACION", "true")
os.environ.setdefault("TUSK_BOVEDA_MANOS", "false")
os.environ.setdefault("ARENA_IGRIS_ACTIVA", "false")
os.environ.setdefault("BRIDGE_WS_SUBSCRIBE_BOOKS", "false")
os.environ.setdefault("KAISER_BACKFILL_ON_START", "false")
os.environ.setdefault("BRIDGE_WS_STAGGER_S", "0.7")
os.environ.setdefault("BINANCE_REF_ENABLED", "false")
os.environ.setdefault("BYBIT_RECV_WINDOW_MS", "60000")
os.environ.setdefault("IGRIS_TICKER_PUERTA_SI_SIN_LIBRO", "auto")
os.environ.setdefault("BRIDGE_WS_FORCE_IPV4", "true")

from core import teatro_sombras as ts  # noqa: E402


def _parse_deadline(s: str) -> float:
    raw = (s or "").strip()
    if not raw:
        raise ValueError("durar-hasta vacío")
    try:
        return float(raw)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(raw, fmt).timestamp()
        except ValueError:
            continue
    raise ValueError(f"No entiendo --durar-hasta: {raw}")


class _TuskOpticaStub:
    """Tusk mínimo: Tank necesita actualizar_precios; sin bóveda / sin manos."""

    def __init__(self) -> None:
        self.pesos: dict = {}
        self.masa_bruta = 0.0
        self.masa_bruta_real = 0.0
        self.masa_autorizada = 0.0
        self.tesoreria: dict = {}

    async def actualizar_precios(self, *args, **kwargs) -> None:
        return None


def _candados_config(*, con_libros: bool, bases: list[str]) -> None:
    import core.config as config

    config.MODO_SIMULACION = True
    if hasattr(config, "TUSK_BOVEDA_MANOS"):
        config.TUSK_BOVEDA_MANOS = False
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = bool(con_libros)
    config.KAISER_BACKFILL_ON_START = False
    config.BRIDGE_WS_STAGGER_S = float(os.getenv("BRIDGE_WS_STAGGER_S", "0.7") or 0.7)
    if hasattr(config, "BINANCE_REF_ENABLED"):
        config.BINANCE_REF_ENABLED = False
    if hasattr(config, "BRIDGE_WS_FORCE_IPV4"):
        config.BRIDGE_WS_FORCE_IPV4 = True
    # Ojos estrechos: solo activos del teatro (+ ticker base)
    ticker = str(getattr(config, "TICKER_BASE", None) or bases[0] or "ETH").upper()
    seen: set[str] = set()
    out: list[str] = []
    for b in list(bases) + [ticker, "ETH"]:
        u = str(b).upper()
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    config.BRIDGE_WS_BASES = out
    print(
        f"[teatro/óptica] ojos estrechos: {', '.join(out)} · "
        f"books={'ON' if con_libros else 'OFF'} · "
        f"SIM={config.MODO_SIMULACION} · bóveda_manos=OFF",
        flush=True,
    )


async def _esperar_ojos_verdes(
    tank,
    *,
    activos: list[str],
    timeout_s: float = 60.0,
    stop_event: asyncio.Event | None = None,
) -> bool:
    """Calentamiento: VERDE + precio lineal vivo del primer activo."""
    base = (activos[0] if activos else "ETH").upper()
    keys = (f"{base}USDT_LINEAL", f"{base}USD_INVERSE", "ETHUSDT_LINEAL", "ETHUSD_INVERSE")
    t0 = time.time()
    print(f"[teatro/óptica] calentamiento Tank VERDE (hasta {timeout_s:.0f}s)…", flush=True)
    while time.time() - t0 < timeout_s:
        if stop_event is not None and stop_event.is_set():
            print("[teatro/óptica] calentamiento abortado (apagado).", flush=True)
            return False
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
                print(
                    f"[teatro/óptica] VERDE lat={getattr(lider, 'latencia_ms', 0):.0f}ms · "
                    f"{base}_lin={px.get(f'{base}USDT_LINEAL')} — listo",
                    flush=True,
                )
                return True
        await asyncio.sleep(1.0)
    print("[teatro/óptica] timeout calentamiento — sin precio vivo.", flush=True)
    return False


def _senales(loop: asyncio.AbstractEventLoop, stop_event: asyncio.Event) -> None:
    def _handler(sig, frame):
        print(f"\n[teatro] señal {sig} — apagando óptica…", flush=True)
        loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handler)


async def _apagar_tareas(tasks: list[asyncio.Task]) -> None:
    for t in tasks:
        if not t.done():
            t.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def _go_optica_tank(
    *,
    activos: list[str],
    durar_s: float,
    intervalo_s: float,
    meta_usd: float,
    dias_personalizado: float,
    campo_limpio: bool,
    con_libros: bool,
    calentamiento_s: float = 60.0,
) -> tuple[int, dict | None]:
    """Arranca 1 Bridge + 1 Tank; alimenta las 4 sombras vía vision_desde_tank."""
    import core.config as config
    from core.bellion import BellionAuditor
    from core.bridge import BybitBridge
    from generales.tank import TankCluster

    _candados_config(con_libros=con_libros, bases=activos)
    if not config.MODO_SIMULACION:
        raise RuntimeError("Abort: MODO_SIMULACION debe ser True en teatro")

    stop_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), stop_event)
    tasks: list[asyncio.Task] = []

    bellion = BellionAuditor()
    tusk = _TuskOpticaStub()
    ticker_base = activos[0] if activos else getattr(config, "TICKER_BASE", "ETH")
    tank = TankCluster(tusk, bellion, ticker_base=ticker_base)
    # WS público — sin session privada (no manos)
    bridge = BybitBridge(tank, tusk, bellion, None, None)

    print(
        "[teatro] óptica Tank viva · Igris/Greed/Beru hibernados · manos OFF",
        flush=True,
    )

    try:
        tasks.append(asyncio.create_task(tank.vigilar_aguas(), name="tank.vigilar_aguas"))
        tasks.append(asyncio.create_task(bridge.conectar(), name="bridge.conectar"))

        ojos_ok = await _esperar_ojos_verdes(
            tank,
            activos=activos,
            timeout_s=calentamiento_s,
            stop_event=stop_event,
        )
        if stop_event.is_set():
            print("[teatro] GO cancelado durante calentamiento.", flush=True)
            return 130, None
        if not ojos_ok:
            print(
                "[teatro] ABORT: óptica Tank no conectó. "
                "No hay mercado vivo — no fingimos con sintético bajo --optica-tank. "
                "Reintenta, revisa red, o usa --sintetico para demo.",
                flush=True,
            )
            return 3, None

        def vision_fn():
            sem = "VERDE"
            try:
                lider = tank._obtener_lider_verde()
                if lider is not None:
                    sem = str(getattr(lider, "estado_foco", None) or "VERDE")
            except Exception:
                pass
            return ts.vision_desde_tank(tank, activos=activos, semaforo=sem)

        print(
            f"[teatro] GO · óptica=tank · activos={activos} · durar_s={durar_s:.0f} · "
            f"intervalo={intervalo_s} · books={'ON' if con_libros else 'OFF'}",
            flush=True,
        )
        final = await ts.correr_hasta_async(
            durar_s=durar_s,
            intervalo_s=intervalo_s,
            activos=activos,
            meta_lote_usd=meta_usd,
            dias_personalizado=dias_personalizado,
            vision_fn=vision_fn,
            campo_limpio=campo_limpio,
            stop_event=stop_event,
            meta_extra={"optica": "tank", "books": bool(con_libros)},
        )
        return 0, final
    except Exception:
        print("\n[teatro] ERROR en óptica Tank:", flush=True)
        traceback.print_exc()
        return 1, None
    finally:
        await _apagar_tareas(tasks)
        print("[teatro/óptica] WS cancelados — apagado limpio.", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Teatro de sombras: 4 Igris de papel / 1 óptica (lab, no live)"
    )
    ap.add_argument(
        "--preparar",
        action="store_true",
        help="Dry-run de sanidad (sintético, segundos). No arranca batida larga.",
    )
    ap.add_argument(
        "--go",
        action="store_true",
        help="Orden GO del Monarca: corre el teatro hasta duración/deadline.",
    )
    ap.add_argument("--horas", type=float, default=0.0, help="Duración en horas (con --go)")
    ap.add_argument("--segundos", type=float, default=0.0, help="Duración en segundos (con --go)")
    ap.add_argument(
        "--durar-hasta",
        type=str,
        default="",
        help="Deadline local YYYY-MM-DDTHH:MM:SS (con --go)",
    )
    ap.add_argument("--intervalo", type=float, default=5.0, help="Segundos entre pulsos")
    ap.add_argument("--activo", type=str, default="ETH", help="Santo/foco del teatro")
    ap.add_argument(
        "--activos",
        type=str,
        default="",
        help="Lista CSV de activos (override --activo)",
    )
    ap.add_argument("--meta-usd", type=float, default=50.0, help="Meta de lote papel por sombra")
    ap.add_argument(
        "--dias-personalizado",
        type=float,
        default=ts.DIAS_PERSONALIZADO_DEFAULT,
        help="Calibración T de la sombra personalizado (solo memoria local)",
    )
    ap.add_argument(
        "--optica-tank",
        action="store_true",
        help="GO serio: un Tank+Bridge vivo alimenta las 4 sombras (exige conexión).",
    )
    ap.add_argument(
        "--sintetico",
        action="store_true",
        help="Forzar óptica sintética (demo sin mercado). Default si --go sin --optica-tank.",
    )
    ap.add_argument(
        "--con-libros",
        action="store_true",
        help="Con --optica-tank: suscribir orderbooks (pesado). Default OFF = tickers.",
    )
    ap.add_argument(
        "--calentamiento-s",
        type=float,
        default=60.0,
        help="Segundos máximos esperando Tank VERDE antes de abortar (con --optica-tank).",
    )
    ap.add_argument(
        "--sin-campo-limpio",
        action="store_true",
        help="No borrar decisiones.jsonl al arrancar GO",
    )
    args = ap.parse_args()

    if not args.preparar and not args.go:
        ap.print_help()
        print(
            "\n[teatro] Nada que hacer: usa --preparar (sanidad) o --go (solo tras orden del Monarca).",
            flush=True,
        )
        return 0

    if args.preparar:
        print("[teatro] PREPARAR — dry-run de sanidad (sin WS / sin caffeinate)", flush=True)
        res = ts.preparar(
            activo=args.activo,
            meta_lote_usd=float(args.meta_usd),
            dias_personalizado=float(args.dias_personalizado),
        )
        print(json.dumps({"meta": res.get("meta"), "sombras": res.get("sombras")}, indent=2, ensure_ascii=False))
        print(f"[teatro] sello → {ts.OUT_DIR / 'preparar_sanidad.json'}", flush=True)
        if args.go:
            print("[teatro] AVISO: --preparar tiene prioridad; ignoro --go en esta corrida.", flush=True)
        return 0

    # --go
    activos = [a.strip().upper() for a in (args.activos or "").split(",") if a.strip()]
    if not activos:
        activos = [args.activo.upper()]

    durar_s = 0.0
    if args.durar_hasta:
        deadline = _parse_deadline(args.durar_hasta)
        durar_s = max(1.0, deadline - time.time())
    elif args.segundos > 0:
        durar_s = float(args.segundos)
    elif args.horas > 0:
        durar_s = float(args.horas) * 3600.0
    else:
        print("[teatro] --go exige --horas, --segundos o --durar-hasta", flush=True)
        return 2

    usar_tank = bool(args.optica_tank) and not bool(args.sintetico)
    if args.sintetico and args.optica_tank:
        print(
            "[teatro] AVISO: --sintetico gana sobre --optica-tank (demo forzada).",
            flush=True,
        )

    if usar_tank:
        code, final = asyncio.run(
            _go_optica_tank(
                activos=activos,
                durar_s=durar_s,
                intervalo_s=float(args.intervalo),
                meta_usd=float(args.meta_usd),
                dias_personalizado=float(args.dias_personalizado),
                campo_limpio=not args.sin_campo_limpio,
                con_libros=bool(args.con_libros),
                calentamiento_s=float(args.calentamiento_s),
            )
        )
        if final is not None:
            print(
                json.dumps(
                    {"meta": final.get("meta"), "sombras": final.get("sombras")},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            print(f"[teatro] sello → {ts.OUT_DIR / 'resumen_monarca.json'}", flush=True)
        return code

    # Default seguro: sintético
    print(
        f"[teatro] GO · óptica=sintética · activos={activos} · durar_s={durar_s:.0f} · "
        f"intervalo={args.intervalo}",
        flush=True,
    )
    if not args.sintetico:
        print(
            "[teatro] AVISO: GO sin --optica-tank → demo sintético (seguro). "
            "GO serio del Monarca: añade --optica-tank (1 Bridge + 1 Tank, tickers).",
            flush=True,
        )
    final = ts.correr_hasta(
        durar_s=durar_s,
        intervalo_s=float(args.intervalo),
        activos=activos,
        meta_lote_usd=float(args.meta_usd),
        dias_personalizado=float(args.dias_personalizado),
        vision_fn=None,
        campo_limpio=not args.sin_campo_limpio,
    )
    # anotar óptica en meta del sello ya escrito
    try:
        meta = final.get("meta") or {}
        meta["optica"] = "sintetico"
        final["meta"] = meta
        (ts.OUT_DIR / "resumen_monarca.json").write_text(
            json.dumps(final, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass
    print(json.dumps({"meta": final.get("meta"), "sombras": final.get("sombras")}, indent=2, ensure_ascii=False))
    print(f"[teatro] sello → {ts.OUT_DIR / 'resumen_monarca.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
