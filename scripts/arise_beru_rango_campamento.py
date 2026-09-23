#!/usr/bin/env python3
"""
Arise Beru rango — CAMPAMENTO (varios Santos, 1 cuartel).

Un Python · un Tank · un Bridge WS · un Tusk/Bellion · N Berus (1 vivo c/u).

  python scripts/arise_beru_rango_campamento.py --santos BTC,ETH,SOL,XRP,DOGE --manos-go
  python scripts/arise_beru_rango_campamento.py --santos A,B,C,D,E --perfil piedra --manos-go --continuar
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
    ap = argparse.ArgumentParser(description="Arise Beru rango campamento (WS compartido)")
    ap.add_argument(
        "--santos",
        required=True,
        help="CSV de Santos del campamento (ej. BTC,ETH,SOL,XRP,DOGE)",
    )
    ap.add_argument("--manos-go", action="store_true")
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_BERU_RANGO_MANOS_SEGUNDOS", "0") or 0),
    )
    ap.add_argument(
        "--latido",
        type=float,
        default=float(os.getenv("BERU_RANGO_LATIDO_LENTO_S", "1.5") or 1.5),
    )
    ap.add_argument("--continuar", action="store_true")
    ap.add_argument("--desde-cero", action="store_true")
    ap.add_argument(
        "--mercado",
        default=os.getenv("BERU_RANGO_MERCADO", "linear"),
        choices=("linear", "inverse"),
    )
    ap.add_argument(
        "--perfil",
        default=os.getenv("BERU_RANGO_PERFIL", "piedra"),
        choices=("normal", "feria", "piedra", "btc_inverso"),
    )
    ap.add_argument("--camp-id", default="", help="Id de escuadrón (bitácora)")
    return ap.parse_args()


ARGS = _parse_args()
_GO = bool(ARGS.manos_go) or (
    os.getenv("ARISE_BERU_RANGO_MANOS_GO", "").lower() in ("1", "true", "yes")
)
if not _GO:
    print("[CAMP] FALLO: falta --manos-go", flush=True)
    raise SystemExit(2)

_SANTOS = [a.strip().upper() for a in str(ARGS.santos or "").split(",") if a.strip()]
if len(_SANTOS) < 2:
    print("[CAMP] FALLO: campamento necesita ≥2 Santos", flush=True)
    raise SystemExit(2)

_MERCADO = str(ARGS.mercado or "linear").lower()
_PERFIL = str(ARGS.perfil or "piedra").lower()
_CAMP_ID = str(ARGS.camp_id or "").strip() or f"CAMP_{'_'.join(_SANTOS[:3])}"

os.environ["BERU_RANGO_MANOS"] = "true"
os.environ["BERU_RANGO_HILO"] = "true"
os.environ["BERU_RANGO_ACTIVO"] = _SANTOS[0]
os.environ["BERU_RANGO_MERCADO"] = _MERCADO
os.environ["BERU_RANGO_PERFIL"] = _PERFIL
os.environ["BERU_RANGO_FLACO"] = "false"
# Monarca 2026-09-22: Red expansiva ON en flota piedra.
os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
os.environ.setdefault("BRIDGE_WS_SUBSCRIBE_BOOKS", "false")
os.environ.setdefault("BERU_MAR", "okx")
os.environ.setdefault("BINANCE_REF_ENABLED", "false")
os.environ["MODO_SIMULACION"] = "false"
os.environ["ARISE_BERU_RANGO_PERMITIR_MANOS"] = "true"
if _MERCADO == "inverse":
    os.environ["BRIDGE_WS_SOLO_INVERSE"] = "true"
    os.environ["BRIDGE_WS_SOLO_LINEAR"] = "false"
    os.environ["BRIDGE_WS_PUBLIC_TRADES_INVERSE"] = "true"
else:
    os.environ["BRIDGE_WS_SOLO_LINEAR"] = "true"
    os.environ["BRIDGE_WS_SOLO_INVERSE"] = "false"
    os.environ["BRIDGE_WS_PUBLIC_TRADES_LINEAR"] = "true"

import core.config as config  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from core.beru_bridge import crear_beru_bridge, credenciales_ok, nombre_mar  # noqa: E402
from core import beru_rango_ojos  # noqa: E402
from core import beru_rango_panel  # noqa: E402
from core import beru_rango_paths  # noqa: E402
from core import beru_rango_checkpoint as checkpoint  # noqa: E402
from core import beru_rango_campamento as campmod  # noqa: E402
from core.beru_rango_altar_espera import parchar_espera_piso_sello  # noqa: E402
from generales.beru_rango import BeruRango  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402

parchar_espera_piso_sello(BeruRango)

MERCADO = beru_rango_ojos.mercado_norm(_MERCADO)
PERFIL = beru_rango_ojos.perfil_norm(_PERFIL)


def _configurar_runtime() -> None:
    config.BERU_RANGO_MERCADO = MERCADO
    config.aplicar_perfil_beru_rango(PERFIL)
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = False
    config.BERU_RANGO_MANOS = True
    config.BERU_RANGO_HILO = True
    config.MODO_SIMULACION = False
    config.BRIDGE_WS_BASES = list(_SANTOS)
    config.BERU_RANGO_FLACO = False
    if MERCADO == "inverse":
        config.BRIDGE_WS_SOLO_INVERSE = True
        config.BRIDGE_WS_SOLO_LINEAR = False
        config.BRIDGE_WS_PUBLIC_TRADES_INVERSE = True
    else:
        config.BRIDGE_WS_SOLO_LINEAR = True
        config.BRIDGE_WS_SOLO_INVERSE = False
        config.BRIDGE_WS_PUBLIC_TRADES_LINEAR = True


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
    print(f"\n[CAMP] Corte por tiempo ({segundos:.0f}s)", flush=True)
    shutdown_event.set()


async def _muleta_rest(bridge, tank, activos: list[str]):
    await asyncio.sleep(3.0)
    while True:
        try:
            if beru_rango_ojos.muleta_rest_necesaria(tank):
                beru_rango_ojos.inyectar_precios_rest(
                    bridge, tank, activos, mercado=MERCADO,
                )
        except Exception as exc:
            print(f"[CAMP] muleta REST: {exc}", flush=True)
        await asyncio.sleep(beru_rango_ojos.rest_intervalo_s())


def _append_evento(activo: str, row: dict[str, Any]) -> None:
    path = beru_rango_paths.eventos_manos(activo, MERCADO, PERFIL)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


async def _hilo_beru(
    beru_g: BeruRango,
    shutdown_event: asyncio.Event,
    latido_lento_s: float,
    contadores: dict[str, Any],
    activo: str,
    tusk=None,
    *,
    stacks: dict[str, Any] | None = None,
    prioridad: Any = None,
):
    from core import beru_rango as cerebro

    await asyncio.sleep(2.0)
    while not shutdown_event.is_set():
        try:
            async def _un_pulso() -> None:
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
                    row = {
                        "ts": time.time(),
                        "camp": _CAMP_ID,
                        "activo": activo,
                        "evento": ev,
                        "detalle": r,
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
                    _append_evento(activo, row)
                    print(f"[CAMP] {activo} → {ev}", flush=True)

            if prioridad is not None:
                async with prioridad.turno(beru_g):
                    await _un_pulso()
            else:
                await _un_pulso()
        except Exception as exc:
            print(f"[CAMP] pulso {activo}: {exc}", flush=True)
            contadores["errores"] = int(contadores.get("errores") or 0) + 1
        try:
            wait_s = cerebro.latido_sugerido_s(
                beru_g.vivo,
                beru_rango_ojos.last_desde_tank(beru_g.tank, activo, MERCADO),
                lento_s=latido_lento_s,
            )
        except Exception:
            wait_s = max(0.2, float(latido_lento_s or 1.5))
        wait_s = campmod.wait_con_prioridad_caza(
            wait_s, beru_g, stacks, lento_s=latido_lento_s,
        )
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=wait_s)
            break
        except asyncio.TimeoutError:
            pass


async def _cronica_camp(
    stacks: dict[str, Any],
    intervalo_s: float = 60.0,
):
    """Crónica del escuadrón — cada minuto (ligera)."""
    from core import beru_rango as cerebro

    await asyncio.sleep(6.0)
    while True:
        bits = []
        for act, st in sorted(stacks.items()):
            beru_g = st["beru"]
            tank = st["tank"]
            px = beru_rango_ojos.last_desde_tank(tank, act, MERCADO)
            snap = beru_g.snapshot()
            vivo = snap.get("vivo") or {}
            try:
                lat = cerebro.latido_sugerido_s(beru_g.vivo, px)
            except Exception:
                lat = 1.5
            bits.append(
                f"{act}:{vivo.get('estado') or '—'}@{px}·lat={lat:.1f}s"
            )
        rio = "WS" if beru_rango_ojos.rio_ws_vivo(next(iter(stacks.values()))["tank"]) else "muleta"
        print(f"[CAMP {_CAMP_ID}] río={rio} · " + " | ".join(bits), flush=True)
        await asyncio.sleep(intervalo_s)


def _escribir_informe_santo(
    *,
    activo: str,
    contadores: dict[str, Any],
    beru_g: BeruRango,
    tank,
    ts0: float,
    tusk=None,
) -> Path:
    path = beru_rango_paths.informe_manos(activo, MERCADO, PERFIL)
    last = beru_rango_ojos.last_desde_tank(tank, activo, MERCADO)
    informe = {
        "ts": time.time(),
        "duracion_s": round(time.time() - ts0, 1),
        "manos": True,
        "campamento": _CAMP_ID,
        "mercado": MERCADO,
        "perfil_beru": PERFIL,
        "activo": activo,
        "santos_camp": list(_SANTOS),
        "contadores": contadores,
        "last": last,
        "snapshot": beru_g.snapshot(),
        "posicion": beru_rango_panel.posicion_desde_tusk(tusk, activo, MERCADO),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


async def _autosello_camp(stacks: dict[str, Any], contadores: dict[str, Any], tusk, ts0: float):
    await asyncio.sleep(12.0)
    while True:
        for act, st in list(stacks.items()):
            try:
                _escribir_informe_santo(
                    activo=act,
                    contadores=contadores,
                    beru_g=st["beru"],
                    tank=st["tank"],
                    ts0=ts0,
                    tusk=tusk,
                )
            except Exception as exc:
                print(f"[CAMP] autosello {act}: {exc}", flush=True)
        try:
            from core import beru_rango_balanza as balanza

            snap = balanza.sellar_balanza()
            print(f"[CAMP] balanza · {snap.get('frase')}", flush=True)
        except Exception as exc:
            print(f"[CAMP] balanza: {exc}", flush=True)
        await asyncio.sleep(30.0)


async def _limpiar_huerfanos(bridge, *, activo: str, previo: dict[str, Any] | None) -> None:
    from core import beru_rango_altar as altar
    from core.models import BeruShip

    vivo = ((previo or {}).get("snapshot") or {}).get("vivo") or {}
    link = str(vivo.get("altar_link_id") or "")
    oid = str(vivo.get("altar_order_id") or "")
    if not link and not oid:
        return
    fantasma = BeruShip(
        uid=str(vivo.get("uid") or f"HUERFANO_{activo}"),
        centro_local=float(vivo.get("cero") or 0) or 1.0,
        masa=0.0,
        direccion=str(vivo.get("direccion") or ""),
        estado="ACECHANDO",
        modo_combate="RANGO",
        frente_asignado=f"{activo}USDT_LINEAL",
    )
    fantasma.altar_link_id = link
    fantasma.altar_order_id = oid
    await altar.cancelar_pendiente(bridge, fantasma, activo=activo, motivo="WAKE_FRESCO")


async def _wake_santo(
    *,
    act: str,
    bridge,
    tank,
    tusk,
    bellion,
    continuar: bool,
    desde_cero: bool,
    contadores: dict[str, Any],
) -> BeruRango | None:
    from core import beru_rango as cerebro
    from core import beru_rango_altar as altar
    from core import beru_leverage as blev
    from core import lote_okx

    # Causa raiz: nunca pelear sin piso OKX real (tick inventado = tumor Oz).
    piso = lote_okx.asegurar_piso_okx(act)
    if not lote_okx.floor_completo(act):
        print(f"[CAMP] {act} SIN PISO OKX — skip (sync minimos)", flush=True)
        return None
    print(
        f"[CAMP] piso {act}: tick={piso.get('tickSz')} ctVal={piso.get('ctVal')}",
        flush=True,
    )

    lev_out = await blev.forzar_max_leverage_activo(bridge, bellion, act)
    if lev_out.get("ok"):
        print(f"[CAMP] apalanc {act}: OK", flush=True)
    elif not lev_out.get("omitido"):
        print(f"[CAMP] apalanc {act} aviso: {lev_out.get('avisos') or lev_out}", flush=True)

    beru_rango_ojos.inyectar_precios_rest(bridge, tank, [act], mercado=MERCADO)
    try:
        if hasattr(bridge, "get_positions"):
            await tusk.reconciliar_con_exchange(bridge, activo=act)
    except Exception as exc:
        print(f"[CAMP] reconcilia {act}: {exc}", flush=True)

    beru_g = BeruRango(tusk, bellion, tank, bridge=bridge)
    px = beru_rango_ojos.last_desde_tank(tank, act, MERCADO)
    if px <= 0:
        for _ in range(20):
            await asyncio.sleep(0.8)
            beru_rango_ojos.inyectar_precios_rest(bridge, tank, [act], mercado=MERCADO)
            px = beru_rango_ojos.last_desde_tank(tank, act, MERCADO)
            if px > 0:
                break
    if px <= 0:
        print(f"[CAMP] {act} sin precio — se salta", flush=True)
        contadores["errores"] = int(contadores.get("errores") or 0) + 1
        return None

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
    print(f"[CAMP] {act} checkpoint {plan.modo} · {plan.nota}", flush=True)

    ev_path = beru_rango_paths.eventos_manos(act, MERCADO, PERFIL)
    ev_path.parent.mkdir(parents=True, exist_ok=True)
    if plan.modo == "SEMILLA" or not ev_path.is_file():
        ev_path.write_text("", encoding="utf-8")

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
        try:
            await tusk.reconciliar_con_exchange(bridge, activo=act)
        except Exception:
            pass
        try:
            reeng = await altar.reenganchar_o_rearmar(
                bridge, beru_g.vivo, activo=act,
            )
            print(f"[CAMP] {act} CONTINUAR_CAZA reeng={getattr(reeng, 'exito', None)}", flush=True)
        except Exception as exc:
            print(f"[CAMP] {act} CONTINUAR_CAZA: {exc}", flush=True)
    elif plan.modo in ("CONTINUAR_ACECHO", "ACECHO_AJUSTE", "SEMBRAR_POS") and beru_g.vivo is not None:
        estado_prev = str(vivo_prev.get("estado") or "").upper()
        limpiar_prev = plan.modo != "CONTINUAR_ACECHO" or estado_prev == "ACECHANDO"
        if limpiar_prev:
            try:
                await _limpiar_huerfanos(bridge, activo=act, previo=prev)
            except Exception as exc:
                print(f"[CAMP] limpia {act}: {exc}", flush=True)
        checkpoint.aplicar_plan(beru_g.vivo, plan)
        tag = plan.modo[:8]
        beru_g.vivo.uid = (
            f"RANGO_{act}_{tag}_{int(vivo_prev.get('escalones_red') or 0)}_"
            f"{uuid.uuid4().hex[:6]}"
        )
    else:
        try:
            await _limpiar_huerfanos(bridge, activo=act, previo=prev)
        except Exception:
            pass

    snap0 = beru_g.snapshot()
    if not snap0.get("manos"):
        print(f"[CAMP] {act} manos OFF tras wake — skip", flush=True)
        return None
    print(
        f"[CAMP] Wake {act} estado={((snap0.get('vivo') or {}).get('estado'))} · manos=ON",
        flush=True,
    )
    return beru_g


async def ritual(
    *,
    activos: list[str],
    segundos: float,
    latido_s: float,
    continuar: bool,
    desde_cero: bool,
) -> None:
    acts = [str(a).upper() for a in activos if str(a).strip()]
    _configurar_runtime()
    if not credenciales_ok():
        raise RuntimeError(f"Sin credenciales {nombre_mar()}")

    print("\n" + "═" * 56)
    print(f"    ARISE CAMPAMENTO {_CAMP_ID}")
    print(f"    Santos ({len(acts)}): {', '.join(acts)}")
    print(f"    Mar={nombre_mar()} perfil={PERFIL} mercado={MERCADO} · WS ON · books OFF")
    print("═" * 56)

    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    contadores: dict[str, Any] = {
        "eventos": 0, "errores": 0, "por_evento": {}, "por_santo": {},
    }
    ts0 = time.time()
    stacks: dict[str, Any] = {}

    try:
        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
        bridge = crear_beru_bridge(tank, tusk, bellion, ws_bases=list(acts))
        if not getattr(bridge, "session", None):
            raise RuntimeError("Bridge sin sesión HTTP")

        tank.expandir_frentes(beru_rango_ojos.frentes_ojo_tank(acts, MERCADO))
        beru_rango_ojos.inyectar_precios_rest(bridge, tank, acts, mercado=MERCADO)

        for act in acts:
            beru_g = await _wake_santo(
                act=act,
                bridge=bridge,
                tank=tank,
                tusk=tusk,
                bellion=bellion,
                continuar=continuar,
                desde_cero=desde_cero,
                contadores=contadores,
            )
            if beru_g is None:
                continue
            stacks[act] = {"beru": beru_g, "tank": tank, "bridge": bridge}

        if not stacks:
            raise RuntimeError("Campamento vacío — ningún Santo despertó")

        print(
            f"\n[CAMP] Vivos {len(stacks)}/{len(acts)} · río WS compartido · "
            f"prioridad CAZA · Ctrl+C sella.\n",
            flush=True,
        )

        prioridad = campmod.CampPrioridadCaza()
        coros = [
            tank.vigilar_aguas(),
            bridge.conectar(),
            _muleta_rest(bridge, tank, list(stacks.keys())),
            _cronica_camp(stacks),
            _autosello_camp(stacks, contadores, tusk, ts0),
            _corte_tiempo(shutdown_event, segundos),
        ]
        if getattr(config, "TUSK_TESORERIA_ACTIVA", True):
            coros.append(tusk.hilo_reconciliacion(bridge))
        for act, st in stacks.items():
            coros.append(
                _hilo_beru(
                    st["beru"], shutdown_event, latido_s, contadores, act, tusk,
                    stacks=stacks, prioridad=prioridad,
                )
            )

        tasks = [asyncio.create_task(c) for c in coros]
        await shutdown_event.wait()
        print("\n[CAMP] Sellando escuadrón…", flush=True)
        from core import beru_rango_altar as altar

        for act, st in stacks.items():
            beru_g = st["beru"]
            path = _escribir_informe_santo(
                activo=act,
                contadores=contadores,
                beru_g=beru_g,
                tank=tank,
                ts0=ts0,
                tusk=tusk,
            )
            try:
                est = str(getattr(beru_g.vivo, "estado", "") or "") if beru_g.vivo else ""
                if beru_g.vivo is not None and est != "CAZANDO":
                    await altar.cancelar_pendiente(
                        bridge, beru_g.vivo, activo=act, motivo="SUCESION",
                    )
            except Exception as exc:
                print(f"[CAMP] limpia {act}: {exc}", flush=True)
            print(f"[CAMP] sello {act}: {path.name}", flush=True)

        await bellion.anotar(
            "BERU_RANGO", "SUCESION",
            f"Campamento {_CAMP_ID} sellado · {list(stacks.keys())}",
        )
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"[CAMP] DONE {_CAMP_ID} eventos={contadores.get('eventos')}", flush=True)
    except Exception:
        print("\n[!] ERROR ARISE CAMPAMENTO:")
        traceback.print_exc()
        raise


def main() -> int:
    if bool(ARGS.desde_cero) and bool(ARGS.continuar):
        print("[CAMP] --desde-cero gana sobre --continuar", flush=True)
    asyncio.run(
        ritual(
            activos=list(_SANTOS),
            segundos=float(ARGS.segundos or 0),
            latido_s=float(ARGS.latido or 1.5),
            continuar=bool(ARGS.continuar),
            desde_cero=bool(ARGS.desde_cero),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
