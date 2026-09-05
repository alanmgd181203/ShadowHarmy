#!/usr/bin/env python3
"""
Arise Beru rango — UN Santo lineal con manos (prueba chiquita).

Candados (todos obligatorios para disparar):
  · --manos-go  (o ARISE_BERU_RANGO_MANOS_GO=true)
  · BERU_RANGO_MANOS=true (lo setea este ritual)
  · API Bybit cargada · MODO_SIMULACION=false

Checkpoint (por defecto):
  · Sello fresco → continúa donde quedó
  · Sello viejo → mismo lado, 0 = last
  · Sin sello + posición → siembra acecho post-Oz
  · --desde-cero → semilla forzada

Ejemplo HYPE:
  python scripts/arise_beru_rango_manos.py --activo HYPE --manos-go
  python scripts/arise_beru_rango_manos.py --activo HYPE --manos-go --segundos 3600
  python scripts/arise_beru_rango_manos.py --activo HYPE --manos-go --continuar
  python scripts/arise_beru_rango_manos.py --activo HYPE --manos-go --desde-cero

Ctrl+C sella. Informe:
  normal:  data/beru/rango/{ACTIVO}/manos_informe.json
  feria:   data/beru/rango/{ACTIVO}/manos_feria_informe.json
  inverse: data/beru/rango/{ACTIVO}/manos_inverso_informe.json
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
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _parse_args():
    ap = argparse.ArgumentParser(description="Arise Beru rango manos (1 Santo, bridge propio)")
    ap.add_argument("--activo", default="HYPE", help="Santo lineal USDT (default HYPE)")
    ap.add_argument(
        "--manos-go",
        action="store_true",
        help="GO explícito del Monarca: permite manos reales",
    )
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_BERU_RANGO_MANOS_SEGUNDOS", "0") or 0),
        help="Si >0, corta tras N segundos",
    )
    ap.add_argument(
        "--latido",
        type=float,
        default=float(os.getenv("BERU_RANGO_LATIDO_LENTO_S", "1.5") or 1.5),
        help="Latido LENTO (s) lejos de orejas; cerca/cazando usa latido rápido",
    )
    ap.add_argument(
        "--continuar",
        action="store_true",
        help="Fuerza retomar sello si existe (compat; el default ya es checkpoint)",
    )
    ap.add_argument(
        "--desde-cero",
        action="store_true",
        help="Ignora sello y posición: wake semilla (Vacío ±1,2 sin Red)",
    )
    ap.add_argument(
        "--mercado",
        default=os.getenv("BERU_RANGO_MERCADO", "linear"),
        choices=("linear", "inverse"),
        help="Rail: linear (USDT) o inverse (USD)",
    )
    ap.add_argument(
        "--perfil",
        default=os.getenv("BERU_RANGO_PERFIL", "normal"),
        choices=("normal", "feria", "piedra"),
        help="Geometría: normal · feria (±2,4%%) · piedra (OKX micro)",
    )
    return ap.parse_args()


ARGS = _parse_args()
_GO = bool(ARGS.manos_go) or (
    os.getenv("ARISE_BERU_RANGO_MANOS_GO", "").lower() in ("1", "true", "yes")
)
if not _GO:
    print(
        "[RANGO] FALLO: falta --manos-go (o ARISE_BERU_RANGO_MANOS_GO=true). "
        "Sin GO no hay manos.",
        flush=True,
    )
    raise SystemExit(2)

# Candados de combate (antes de importar config)
_MERCADO = str(getattr(ARGS, "mercado", None) or os.getenv("BERU_RANGO_MERCADO", "linear")).lower()
_PERFIL = str(getattr(ARGS, "perfil", None) or os.getenv("BERU_RANGO_PERFIL", "normal")).lower()
os.environ["BERU_RANGO_MANOS"] = "true"
os.environ["BERU_RANGO_HILO"] = "true"
os.environ["BERU_RANGO_ACTIVO"] = str(ARGS.activo or "HYPE").upper()
os.environ["BERU_RANGO_MERCADO"] = _MERCADO
os.environ["BERU_RANGO_PERFIL"] = _PERFIL
if _MERCADO == "inverse":
    os.environ["BRIDGE_WS_SOLO_INVERSE"] = "true"
    os.environ["BRIDGE_WS_SOLO_LINEAR"] = "false"
    os.environ["BRIDGE_WS_PUBLIC_TRADES_INVERSE"] = "true"
    os.environ["BRIDGE_WS_PUBLIC_TRADES_LINEAR"] = "false"
else:
    os.environ["BRIDGE_WS_SOLO_LINEAR"] = "true"
    os.environ["BRIDGE_WS_SOLO_INVERSE"] = "false"
    os.environ["BRIDGE_WS_PUBLIC_TRADES_LINEAR"] = "true"
os.environ.setdefault("BRIDGE_WS_SUBSCRIBE_BOOKS", "false")
os.environ.setdefault("BERU_MAR", "okx")
os.environ.setdefault("BINANCE_REF_ENABLED", "false")
os.environ["MODO_SIMULACION"] = "false"
os.environ["ARISE_BERU_RANGO_PERMITIR_MANOS"] = "true"

import core.config as config  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from core.beru_bridge import crear_beru_bridge, credenciales_ok, nombre_mar  # noqa: E402
from core import beru_rango_ojos  # noqa: E402
from core import beru_rango_panel  # noqa: E402
from core import beru_rango_paths  # noqa: E402
from core import beru_rango_checkpoint as checkpoint  # noqa: E402
from generales.beru_rango import BeruRango  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402

from core.beru_rango_altar_espera import parchar_espera_piso_sello  # noqa: E402

parchar_espera_piso_sello(BeruRango)

_ACT = str(ARGS.activo or "HYPE").upper()
MERCADO = beru_rango_ojos.mercado_norm(_MERCADO)
PERFIL = beru_rango_ojos.perfil_norm(_PERFIL)
INFORME_PATH = beru_rango_paths.informe_manos(_ACT, MERCADO, PERFIL)
EVENTOS_PATH = beru_rango_paths.eventos_manos(_ACT, MERCADO, PERFIL)
LEGACY_INFORME = beru_rango_paths.LEGACY_MANOS_INFORME
LEGACY_EVENTOS = beru_rango_paths.LEGACY_MANOS_EVENTOS


def _sello_aislado() -> bool:
    """No publicar al panel legacy ni espejo lineal normal."""
    return MERCADO == "inverse" or PERFIL in ("feria", "piedra")


def _configurar_mercado_runtime() -> None:
    config.BERU_RANGO_MERCADO = MERCADO
    config.aplicar_perfil_beru_rango(PERFIL)
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = False
    if MERCADO == "inverse":
        config.BRIDGE_WS_SOLO_INVERSE = True
        config.BRIDGE_WS_SOLO_LINEAR = False
        config.BRIDGE_WS_PUBLIC_TRADES_INVERSE = True
        config.BRIDGE_WS_PUBLIC_TRADES_LINEAR = False
    else:
        config.BRIDGE_WS_SOLO_LINEAR = True
        config.BRIDGE_WS_SOLO_INVERSE = False
        config.BRIDGE_WS_PUBLIC_TRADES_LINEAR = True
        config.BRIDGE_WS_PUBLIC_TRADES_INVERSE = False


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
    print(f"\n[RANGO] Corte por tiempo ({segundos:.0f}s) — sellando…", flush=True)
    shutdown_event.set()


async def _muleta_rest(bridge, tank, activo: str):
    await asyncio.sleep(3.0)
    while True:
        try:
            if beru_rango_ojos.muleta_rest_necesaria(tank):
                beru_rango_ojos.inyectar_precios_rest(
                    bridge, tank, [activo], mercado=MERCADO,
                )
        except Exception as exc:
            print(f"[RANGO] muleta REST: {exc}", flush=True)
        await asyncio.sleep(beru_rango_ojos.rest_intervalo_s())


def _append_evento(row: dict[str, Any]) -> None:
    EVENTOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with EVENTOS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)
    # Espejo legacy para vigilancias / panel viejo (no borra otros Santos).
    try:
        LEGACY_EVENTOS.parent.mkdir(parents=True, exist_ok=True)
        with LEGACY_EVENTOS.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass


async def _hilo_beru(
    beru_g: BeruRango,
    shutdown_event: asyncio.Event,
    latido_lento_s: float,
    contadores: dict[str, Any],
    activo: str,
    tusk=None,
):
    from core import beru_rango as cerebro

    def _registrar_pulso_exc(exc: BaseException) -> None:
        msg = str(exc)
        low = msg.lower()
        es_aviso = (
            "beru_rango_altar:" in low
            and any(
                t in low
                for t in (
                    "bajo_min_usd",
                    "qty_cero",
                    "qty_cero_deuda",
                    "masa_o_precio_cero",
                    "lote_lineal_invalido",
                )
            )
        )
        if es_aviso:
            contadores.setdefault("avisos", 0)
            contadores["avisos"] = int(contadores.get("avisos") or 0) + 1
            contadores.setdefault("por_aviso", {})
            clave = msg.split("(")[0].strip()[:80]
            contadores["por_aviso"][clave] = int(
                contadores["por_aviso"].get(clave, 0)
            ) + 1
            return
        print(f"[RANGO] pulso error: {exc}", flush=True)
        contadores["errores"] = int(contadores.get("errores") or 0) + 1

    await asyncio.sleep(2.0)
    while not shutdown_event.is_set():
        try:
            lat = beru_rango_ojos.latido_desde_tank(beru_g.tank, activo, MERCADO)
            px = float(lat.get("last") or 0) or beru_rango_ojos.last_desde_tank(
                beru_g.tank, activo, MERCADO
            )
            if px <= 0:
                beru_rango_ojos.inyectar_precios_rest(
                    beru_g.bridge, beru_g.tank, [activo], mercado=MERCADO,
                )
                lat = beru_rango_ojos.latido_desde_tank(beru_g.tank, activo, MERCADO)
                px = float(lat.get("last") or 0) or beru_rango_ojos.last_desde_tank(
                    beru_g.tank, activo, MERCADO
                )
            r = await beru_g.pulso(
                precio=px if px > 0 else None,
                latido=lat if px > 0 else None,
            )
            ev = str((r or {}).get("evento") or (r or {}).get("motivo") or "")
            if ev and ev not in ("ACECHO", "CAZA"):
                row = {"ts": time.time(), "activo": activo, "evento": ev, "detalle": r}
                contadores["eventos"] = int(contadores.get("eventos") or 0) + 1
                contadores.setdefault("por_evento", {})
                contadores["por_evento"][ev] = int(
                    contadores["por_evento"].get(ev, 0)
                ) + 1
                _append_evento(row)
                print(f"[RANGO] {activo} → {ev} {r}", flush=True)
        except Exception as exc:
            _registrar_pulso_exc(exc)
        px = beru_rango_ojos.last_desde_tank(beru_g.tank, activo, MERCADO)
        # Caza: no sellar panel en el latido 0.1s (candado disco).
        # La crónica (~10s) mantiene la foto. Acecho sí publica (latido lento).
        estado = ""
        try:
            estado = str(getattr(getattr(beru_g, "vivo", None), "estado", "") or "")
        except Exception:
            estado = ""
        if estado != "CAZANDO" and not _sello_aislado():
            try:
                beru_rango_panel.publicar(
                    snapshot=beru_g.snapshot(),
                    last=float(px or 0),
                    activo=activo,
                    merge=True,
                    tusk=tusk,
                )
            except Exception:
                pass
        try:
            wait_s = cerebro.latido_sugerido_s(
                beru_g.vivo, px, lento_s=latido_lento_s,
            )
        except Exception:
            wait_s = max(0.2, float(latido_lento_s or 1.5))
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=wait_s)
            break
        except asyncio.TimeoutError:
            pass


async def _cronica(
    tank, beru_g: BeruRango, activo: str, tusk=None, intervalo_s: float = 10.0,
):
    from core import beru_rango as cerebro

    await asyncio.sleep(4.0)
    while True:
        px = beru_rango_ojos.last_desde_tank(tank, activo, MERCADO)
        snap = beru_g.snapshot()
        vivo = snap.get("vivo") or {}
        rio = "WS" if beru_rango_ojos.rio_ws_vivo(tank) else "ciego/muleta"
        try:
            lat = cerebro.latido_sugerido_s(beru_g.vivo, px)
        except Exception:
            lat = 1.5
        pos = beru_rango_panel.posicion_desde_tusk(tusk, activo, MERCADO) if tusk else []
        pos_txt = " · ".join(
            f"{p['lado']} {p['qty']:.6g}@{p['precio']}" for p in pos
        ) or "flat"
        suf = "USD_INVERSE" if MERCADO == "inverse" else "USDT_LINEAL"
        print(
            f"[RANGO] {activo}{suf} last={px} · río={rio} · mercado={MERCADO} · "
            f"estado={vivo.get('estado') or '—'} · dir={vivo.get('direccion') or '—'} · "
            f"0={vivo.get('cero') or '—'} · Oz={vivo.get('oz') or '—'} · "
            f"Red={vivo.get('red') or '—'} · manos={'ON' if snap.get('manos') else 'OFF'} · "
            f"pos={pos_txt} · latido={lat:.2f}s",
            flush=True,
        )
        if not _sello_aislado():
            try:
                beru_rango_panel.publicar(
                    snapshot=snap,
                    last=float(px or 0),
                    activo=activo,
                    merge=True,
                    tusk=tusk,
                )
            except Exception as exc:
                print(f"[RANGO] panel foto: {exc}", flush=True)
        await asyncio.sleep(intervalo_s)


async def _autosello(
    *,
    activo: str,
    contadores: dict[str, Any],
    beru_g: BeruRango,
    tank,
    ts0: float,
    tusk=None,
    intervalo_s: float = 15.0,
):
    """Sella caza+altar cada poco — reinicio/continuar sin Oz huérfana."""
    await asyncio.sleep(8.0)
    while True:
        try:
            path = _escribir_informe(
                activo=activo,
                contadores=contadores,
                beru_g=beru_g,
                tank=tank,
                ts0=ts0,
                tusk=tusk,
            )
            vivo = ((beru_g.snapshot() or {}).get("vivo") or {})
            print(
                f"[RANGO] autosello {activo} · {vivo.get('estado')} · "
                f"Oz={vivo.get('oz')} link={vivo.get('altar_link_id') or '—'} · {path.name}",
                flush=True,
            )
        except Exception as exc:
            print(f"[RANGO] autosello: {exc}", flush=True)
        await asyncio.sleep(intervalo_s)


def _escribir_informe(
    *,
    activo: str,
    contadores: dict[str, Any],
    beru_g: BeruRango,
    tank,
    ts0: float,
    tusk=None,
) -> Path:
    last = beru_rango_ojos.last_desde_tank(tank, activo, MERCADO)
    informe = {
        "ts": time.time(),
        "duracion_s": round(time.time() - ts0, 1),
        "manos": True,
        "mercado": MERCADO,
        "perfil_beru": PERFIL,
        "activo": activo,
        "contadores": contadores,
        "last": last,
        "snapshot": beru_g.snapshot(),
        "eventos_path": str(EVENTOS_PATH),
        "posicion": beru_rango_panel.posicion_desde_tusk(
            tusk or getattr(tank, "tusk", None), activo, MERCADO,
        ),
    }
    if MERCADO == "inverse":
        informe["last_inverse"] = last
    else:
        informe["last_lineal"] = last
    INFORME_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(informe, ensure_ascii=False, indent=2)
    INFORME_PATH.write_text(raw, encoding="utf-8")
    # Espejo legacy solo si no pisa sello de otro Santo (lineal).
    try:
        if not _sello_aislado():
            LEGACY_INFORME.parent.mkdir(parents=True, exist_ok=True)
            ok_legacy = True
            if LEGACY_INFORME.is_file():
                try:
                    prev_leg = json.loads(LEGACY_INFORME.read_text(encoding="utf-8"))
                    prev_act = str(prev_leg.get("activo") or "").upper()
                    if prev_act and prev_act != str(activo).upper():
                        ok_legacy = False
                except Exception:
                    pass
            if ok_legacy:
                LEGACY_INFORME.write_text(raw, encoding="utf-8")
    except Exception:
        pass
    try:
        if not _sello_aislado():
            beru_rango_panel.publicar(
                snapshot=informe.get("snapshot") or {},
                last=float(informe.get("last") or informe.get("last_lineal") or 0),
                activo=activo,
                merge=True,
                tusk=tusk or getattr(tank, "tusk", None),
            )
    except Exception:
        pass
    return INFORME_PATH


async def _limpiar_huerfanos_altar(bridge, *, activo: str, previo: dict[str, Any] | None) -> None:
    """Wake fresco: cancela Stop del sello previo si quedó colgado."""
    from core import beru_rango_altar as altar
    from core.models import BeruShip

    vivo = ((previo or {}).get("snapshot") or {}).get("vivo") or {}
    link = str(vivo.get("altar_link_id") or "")
    oid = str(vivo.get("altar_order_id") or "")
    if not link and not oid:
        return
    fantasma = BeruShip(uid="LIMPIA", centro_local=1.0, masa=0.0, direccion="", estado="ACECHANDO")
    fantasma.altar_link_id = link
    fantasma.altar_order_id = oid
    await altar.cancelar_pendiente(bridge, fantasma, activo=activo, motivo="WAKE_FRESCO")


def _cargar_continuar(activo: str) -> dict[str, Any]:
    data = checkpoint.leer_sello(activo, mercado=MERCADO, perfil=PERFIL)
    if data is None:
        path = beru_rango_paths.resolver_manos_informe(activo, MERCADO, PERFIL)
        raise RuntimeError(f"Sin informe para continuar: {path}")
    return data


async def ritual(
    *,
    activo: str,
    segundos: float,
    latido_s: float,
    continuar: bool = False,
    desde_cero: bool = False,
) -> None:
    act = str(activo or "HYPE").upper()
    _configurar_mercado_runtime()
    config.BERU_RANGO_ACTIVO = act
    config.BERU_RANGO_MANOS = True
    config.BERU_RANGO_HILO = True
    config.MODO_SIMULACION = False
    config.BRIDGE_WS_BASES = [act]
    if hasattr(config, "BINANCE_REF_ENABLED"):
        config.BINANCE_REF_ENABLED = False

    if not credenciales_ok():
        raise RuntimeError(f"Sin credenciales {nombre_mar()} — no se puede arise con manos")

    suf = "USD_INVERSE" if MERCADO == "inverse" else "USDT_LINEAL"
    print("\n" + "═" * 56)
    print("    ARISE BERU RANGO — MANOS ON")
    print(f"    Mar: {nombre_mar()} · Santo: {act}{suf} · mercado={MERCADO} · perfil={PERFIL} · "
          f"Vacío ±{getattr(config, 'BERU_RANGO_VACIO_PCT', 0.012)*100:.1f}% · "
          f"masa ${getattr(config, 'BERU_RANGO_MASA_USD', 5)} · Red ${getattr(config, 'BERU_RANGO_MASA_RED_USD', 5)}")
    print(f"    FASE: {config.FASE_ACTUAL} | SIM={config.MODO_SIMULACION} | TESTNET={config.TESTNET}")
    print("═" * 56)

    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    contadores: dict[str, Any] = {"eventos": 0, "errores": 0, "avisos": 0, "por_evento": {}}
    ts0 = time.time()

    try:
        from core import beru_rango as cerebro
        from core import beru_rango_altar as altar

        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
        bridge = crear_beru_bridge(tank, tusk, bellion, ws_bases=[act])
        if not getattr(bridge, "session", None):
            raise RuntimeError(f"Bridge {nombre_mar()} sin sesión HTTP — abort manos")

        from core import beru_leverage as blev

        lev_out = await blev.forzar_max_leverage_activo(bridge, bellion, act)
        if lev_out.get("omitido"):
            print(f"[RANGO] apalanc {act}: omitido (IGRIS_FORCE_MAX_LEVERAGE off)", flush=True)
        elif lev_out.get("ok"):
            piernas = lev_out.get("piernas") or []
            tops = [
                f"{p.get('symbol')}={p.get('aplicado')}x"
                for p in piernas
                if p.get("aplicado")
            ]
            print(f"[RANGO] apalanc máx {act}: {', '.join(tops) or 'OK'}", flush=True)
        else:
            print(f"[RANGO] apalanc {act} AVISO: {lev_out.get('avisos') or lev_out}", flush=True)

        tank.expandir_frentes(beru_rango_ojos.frentes_ojo_tank([act], MERCADO))
        beru_rango_ojos.inyectar_precios_rest(bridge, tank, [act], mercado=MERCADO)
        try:
            if hasattr(bridge, "get_positions"):
                await tusk.reconciliar_con_exchange(bridge, activo=act)
        except Exception as exc:
            print(f"[RANGO] reconciliación previa: {exc}", flush=True)

        beru_g = BeruRango(tusk, bellion, tank, bridge=bridge)
        px = beru_rango_ojos.last_desde_tank(tank, act, MERCADO)
        if px <= 0:
            for _ in range(30):
                await asyncio.sleep(1.0)
                beru_rango_ojos.inyectar_precios_rest(bridge, tank, [act], mercado=MERCADO)
                px = beru_rango_ojos.last_desde_tank(tank, act, MERCADO)
                if px > 0:
                    break
        if px <= 0:
            raise RuntimeError(f"Sin last {MERCADO} {act} para wake")

        posiciones = beru_rango_panel.posicion_desde_tusk(tusk, act, MERCADO)
        plan = checkpoint.decidir_arranque(
            activo=act,
            last=px,
            posiciones=posiciones,
            forzar_semilla=bool(desde_cero),
            forzar_continuar=bool(continuar) and not desde_cero,
            mercado=MERCADO,
            perfil=PERFIL,
        )
        prev = plan.sello
        vivo_prev = plan.vivo
        retoma = plan.modo != "SEMILLA"

        print(
            f"[RANGO] Checkpoint {plan.modo} · {plan.nota} · "
            f"edad={plan.edad_s if plan.edad_s < 1e17 else '—'}s · "
            f"pos={len(posiciones)}",
            flush=True,
        )
        if retoma:
            print(
                f"    → 0={plan.cero} · Red={plan.red or '—'} · sangre={plan.sangre_lado or '—'} · "
                f"hoz={plan.hoz_dir or '—'} · estado_sello={vivo_prev.get('estado') or '—'}",
                flush=True,
            )

        EVENTOS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not retoma:
            EVENTOS_PATH.write_text("", encoding="utf-8")
        elif not EVENTOS_PATH.is_file():
            EVENTOS_PATH.write_text("", encoding="utf-8")

        if retoma and prev is not None:
            contadores["por_evento"] = dict(
                ((prev or {}).get("contadores") or {}).get("por_evento") or {}
            )
            contadores["eventos"] = int(
                ((prev or {}).get("contadores") or {}).get("eventos") or 0
            )

        await beru_g.despertar(precio=px, activo=act)

        if plan.modo == "CONTINUAR_CAZA" and beru_g.vivo is not None:
            cerebro.restaurar_caza_trailing(
                beru_g.vivo,
                cero=float(vivo_prev.get("cero") or 0),
                direccion=str(vivo_prev.get("direccion") or ""),
                oz=float(vivo_prev.get("oz") or 0),
                trail_extremo=float(vivo_prev.get("trail_extremo") or 0),
                masa=float(vivo_prev.get("masa") or 0),
                altar_link_id=str(vivo_prev.get("altar_link_id") or ""),
                altar_order_id=str(vivo_prev.get("altar_order_id") or ""),
                altar_trigger_price=float(vivo_prev.get("altar_trigger_price") or 0),
                altar_revision=int(vivo_prev.get("altar_revision") or 0),
                sangre_lado=str(vivo_prev.get("sangre_lado") or ""),
                escalones_red=int(vivo_prev.get("escalones_red") or 0),
                cosechas=int(vivo_prev.get("cosechas") or 0),
                uid=str(vivo_prev.get("uid") or ""),
                saco_long=float(vivo_prev.get("saco_long") or 0),
                saco_short=float(vivo_prev.get("saco_short") or 0),
                ultima_hoz_direccion=str(vivo_prev.get("ultima_hoz_direccion") or ""),
                oz_despliegue=float(vivo_prev.get("oz_despliegue") or 0),
            )
            if not beru_g.vivo.uid:
                beru_g.vivo.uid = (
                    f"RANGO_{act}_CAZA_{int(vivo_prev.get('escalones_red') or 0)}_"
                    f"{uuid.uuid4().hex[:6]}"
                )
            # Baseline pierna = casa ahora (si no, el primer delta contaría toda la pierna).
            try:
                await tusk.reconciliar_con_exchange(bridge, activo=act)
            except Exception:
                pass
            d_hunt = str(getattr(beru_g.vivo, "direccion", "") or "").upper()
            for row in beru_rango_panel.posicion_desde_tusk(tusk, act, MERCADO):
                if str(row.get("lado") or "").upper() == d_hunt:
                    beru_g.vivo.pierna_snap_usd = float(row.get("masa_usd") or 0)
                    beru_g.vivo.pierna_snap_lado = d_hunt
                    break
            print(
                f"    → saco L={float(getattr(beru_g.vivo,'saco_long_usd',0) or 0):.2f} "
                f"S={float(getattr(beru_g.vivo,'saco_short_usd',0) or 0):.2f} "
                f"snap={float(getattr(beru_g.vivo,'pierna_snap_usd',0) or 0):.2f}",
                flush=True,
            )
            try:
                reeng = await altar.reenganchar_o_rearmar(
                    bridge, beru_g.vivo, activo=act,
                )
            except ValueError as exc:
                print(f"[RANGO] CONTINUAR_CAZA espera piso {act}: {exc}", flush=True)
                reeng = None
            await bellion.anotar(
                "BERU_RANGO", "CONTINUAR_CAZA",
                f"{beru_g.vivo.uid} dir={beru_g.vivo.direccion} "
                f"Oz={beru_g.vivo.oz_adan} link={beru_g.vivo.altar_link_id} "
                f"reeng={getattr(reeng, 'exito', None)} · {plan.nota}",
            )
        elif plan.modo in ("CONTINUAR_ACECHO", "ACECHO_AJUSTE", "SEMBRAR_POS") and beru_g.vivo is not None:
            # Acecho/caza abandonada: cancela Stop colgado del sello previo.
            estado_prev = str(vivo_prev.get("estado") or "").upper()
            limpiar_prev = plan.modo != "CONTINUAR_ACECHO" or estado_prev == "ACECHANDO"
            if limpiar_prev:
                try:
                    await _limpiar_huerfanos_altar(bridge, activo=act, previo=prev)
                except Exception as exc:
                    print(f"[RANGO] limpia Stop al continuar: {exc}", flush=True)
            checkpoint.aplicar_plan(beru_g.vivo, plan)
            tag = {
                "CONTINUAR_ACECHO": "CONTINUAR",
                "ACECHO_AJUSTE": "CONTINUAR_AJUSTE",
                "SEMBRAR_POS": "SEMBRAR_POS",
            }.get(plan.modo, "CONTINUAR")
            beru_g.vivo.uid = (
                f"RANGO_{act}_{tag[:8]}_{int(vivo_prev.get('escalones_red') or 0)}_"
                f"{uuid.uuid4().hex[:6]}"
            )
            await bellion.anotar(
                "BERU_RANGO", tag,
                f"{beru_g.vivo.uid} 0={beru_g.vivo.centro_local} "
                f"Red={beru_g.vivo.red_adan} sangre={beru_g.vivo.sangre_lado} · {plan.nota}",
            )
        else:
            try:
                await _limpiar_huerfanos_altar(bridge, activo=act, previo=prev)
            except Exception as exc:
                print(f"[RANGO] limpieza huérfanos: {exc}", flush=True)

        snap0 = beru_g.snapshot()
        vivo0 = snap0.get("vivo") or {}
        print(
            f"[RANGO] Wake {act} 0={vivo0.get('cero') or px} · "
            f"Red={vivo0.get('red') or '—'} · sangre={vivo0.get('sangre_lado') or '—'} · "
            f"estado={vivo0.get('estado') or '—'} · Oz={vivo0.get('oz') or '—'} · "
            f"manos={snap0.get('manos')} · bridge=ON · {plan.modo}",
            flush=True,
        )
        if not snap0.get("manos"):
            raise RuntimeError("Manos no activas tras wake — abort")

        print("\n[RANGO] Hilo vivo · Stop/amend/Market permitidos · Ctrl+C sella.\n", flush=True)

        coros = [
            tank.vigilar_aguas(),
            bridge.conectar(),
            _muleta_rest(bridge, tank, act),
            _hilo_beru(beru_g, shutdown_event, latido_s, contadores, act, tusk),
            _cronica(tank, beru_g, act, tusk),
            _autosello(
                activo=act,
                contadores=contadores,
                beru_g=beru_g,
                tank=tank,
                ts0=ts0,
                tusk=tusk,
            ),
            _corte_tiempo(shutdown_event, segundos),
        ]
        if getattr(config, "TUSK_TESORERIA_ACTIVA", True):
            coros.append(tusk.hilo_reconciliacion(bridge))

        tasks = [asyncio.create_task(c) for c in coros]
        await shutdown_event.wait()
        print("\n[RANGO] Sellando…", flush=True)
        path = _escribir_informe(
            activo=act, contadores=contadores, beru_g=beru_g, tank=tank, ts0=ts0,
            tusk=tusk,
        )
        try:
            est = str(getattr(beru_g.vivo, "estado", "") or "") if beru_g.vivo else ""
            if beru_g.vivo is not None and est != "CAZANDO":
                await altar.cancelar_pendiente(
                    bridge, beru_g.vivo, activo=act, motivo="SUCESION",
                )
            elif est == "CAZANDO":
                print(
                    f"[RANGO] CAZANDO al sello — Stop queda vivo · "
                    f"link={getattr(beru_g.vivo, 'altar_link_id', '')} · checkpoint lo retoma",
                    flush=True,
                )
        except Exception as exc:
            print(f"[RANGO] limpieza salida: {exc}", flush=True)
        await bellion.anotar(
            "BERU_RANGO", "SUCESION",
            f"Arise manos sellado · {act} · {path}",
        )
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print(
            f"[RANGO] Informe: {path} · eventos={contadores.get('eventos')} · "
            f"{contadores.get('por_evento')}",
            flush=True,
        )
    except Exception:
        print("\n[!] ERROR ARISE BERU RANGO MANOS:")
        traceback.print_exc()
        raise


def main() -> int:
    if bool(ARGS.desde_cero) and bool(ARGS.continuar):
        print("[RANGO] --desde-cero gana sobre --continuar", flush=True)
    asyncio.run(
        ritual(
            activo=str(ARGS.activo).upper(),
            segundos=float(ARGS.segundos or 0),
            latido_s=float(ARGS.latido or 1),
            continuar=bool(ARGS.continuar),
            desde_cero=bool(ARGS.desde_cero),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
