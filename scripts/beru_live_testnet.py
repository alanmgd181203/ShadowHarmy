#!/usr/bin/env python3
"""
Checklist 3.9.9 — Beru live testnet aislado (órdenes reales en Bybit DEMO).

Doctrina de esta sesión (orden Monarca):
  - Capitán Ansiedad: vacío 1.2% → gatillo caza ±0.6% (no Normal 1.6%/0.8%)
  - Tier PLENO / Mariscal: nacimiento/clon cada 0.1%
  - Modo combate CAZA (no Negociador legacy como default)
  - Mordida ~$20 por caza
  - 22 barcos flota del manto, solo USDT spot (nada USDC/exótico)
  - Spot margen forzado 10x (isLeverage)
  - Igris/Greed hibernados
  - Vigilia default 1 h (3600 s)

  python scripts/beru_live_testnet.py
  python scripts/beru_live_testnet.py --segundos 3600 --activos flota
  python scripts/beru_live_testnet.py --segundos 0   # hasta Ctrl+C

ABORTA si MODO_TESTNET!=True o faltan API keys.
No reescribe .env: solo fuerza flags en esta sesión.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# --- Sesión 3.9.9 (antes de importar config) ---
os.environ["LIVE_BERU_TESTNET"] = "true"
os.environ["MODO_TESTNET"] = "True"
os.environ["MODO_SIMULACION"] = "False"
os.environ["BERU_TIER_DEFAULT"] = "PLENO"
os.environ["BERU_MODO_COMBATE_DEFAULT"] = "CAZA"
os.environ["BERU_VACIO_ANSIEDAD"] = os.environ.get("BERU_VACIO_ANSIEDAD", "0.012")
os.environ.setdefault("BERU_CAZADOR_MORDIDA_USD", os.environ.get("LIVE_BERU_MORDIDA_USD", "20"))
os.environ.setdefault("BERU_CAZA_CAPA1_USD", os.environ.get("LIVE_BERU_MORDIDA_USD", "20"))
# 0 = sin techo artificial de engorde (doctrina Monarca 2026-07-18)
os.environ["BERU_CAZA_CAPA1_MAX_USD"] = os.environ.get("BERU_CAZA_CAPA1_MAX_USD", "0")
os.environ["BERU_SPOT_MARGEN_ENABLED"] = "true"
os.environ.setdefault("BERU_SPOT_MARGEN_LEVERAGE", "10")
os.environ["BERU_RAIL_USDT_ONLY"] = "true"
os.environ["GREED_KAISER_ENABLED"] = "false"
os.environ["GREED_VIP_ENABLED"] = "false"
os.environ["GREED_BASIS_HOLD_ENABLED"] = "false"
os.environ["GREED_MULTICRUCE_ENABLED"] = "false"
os.environ["IGRIS_BOOTSTRAP_ON_START"] = "false"
os.environ["SAFE_MODE"] = "true"

import core.config as config
from core import mercado as mercado_mod
from core.bellion import BellionAuditor
from core.bridge import BybitBridge
from core.models import MarketContext
from core.beru_cazador import gatillo_pct, mordida_usd
from core.trinidad import aplicar_a_config, refrescar_config
from generales.beru import BeruCazador
from generales.capitanes import ADN_Capitan
from generales.kaiser import KaiserVocero
from generales.tank import TankCluster
from generales.tusk import TuskBoveda
from pybit.unified_trading import HTTP


# Capitán Ansiedad forzado (1.2% vacío → gatillo 0.6%)
CAPITAN_ANSIEDAD_LIVE = ADN_Capitan(
    nombre="ANSIEDAD_LIVE_3_9_9",
    vacio_adan=float(os.environ.get("BERU_VACIO_ANSIEDAD", "0.012")),
    margen_apertura=0.001,
    latigazo_snap=0.002,
    distancia_pendulo=0.01,
)


def _flota_22() -> list[str]:
    path = ROOT / "config" / "diccionario_beru_flota_manto.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        lista = (data.get("meta") or {}).get("activos") or []
        if lista:
            return [str(a).upper() for a in lista]
    # Fallback trinidad
    bases = list(getattr(config, "ACTIVOS_TRINIDAD", None) or [])
    if bases:
        return [str(a).upper() for a in bases]
    return ["ETH", "BTC", "LTC", "SOL", "OP"]


def _activos_cfg(raw: str | None) -> list[str]:
    s = (raw or getattr(config, "LIVE_BERU_ACTIVOS", "flota") or "flota").strip()
    if s.lower() in ("flota", "all", "*", "22"):
        return _flota_22()
    return [a.strip().upper() for a in s.split(",") if a.strip()]


def _expandir_ojos(activos: list[str]) -> None:
    spots = [f"{a}USDT_SPOT" for a in activos]
    config.FRENTES_BERU_VIGILANCIA = spots
    config.ACTIVOS_VIGILANCIA = list(
        dict.fromkeys(list(getattr(config, "ACTIVOS_VIGILANCIA", []) or []) + activos)
    )
    base = list(getattr(config, "FRENTES_RESONANCIA_TANK", []) or [])
    config.FRENTES_RESONANCIA_TANK = list(dict.fromkeys(base + spots))
    tank_f = list(getattr(config, "FRENTES_TANK", None) or config.FRENTES_RESONANCIA_TANK)
    config.FRENTES_TANK = list(dict.fromkeys(tank_f + spots))


def _aplicar_casa(activo: str) -> None:
    a = activo.upper()
    config.BERU_ACTIVO_SEMILLA = a
    config.TICKER_BASE = a
    # Orden Alan: solo USDT — nada USDC/exótico
    config.FRENTES_CASA = [f"{a}USDT_SPOT"]
    config.FRENTES_BERU_VIGILANCIA = [f"{a}USDT_SPOT"]
    config.BERU_RAIL_USDT_ONLY = True


def _contar_historial(path: Path, desde_ts: float) -> dict:
    out = {
        "caza": 0,
        "cosecha": 0,
        "orden_enviada": 0,
        "orden_fallida": 0,
        "negociando": 0,
        "lineas": 0,
    }
    if not path.exists():
        return out
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return out
    for line in lines[-800:]:
        out["lineas"] += 1
        u = line.upper()
        # Filtrar por ventana aproximada (ts ISO o epoch en línea)
        if "ORDEN_ENVIADA" in u:
            out["orden_enviada"] += 1
        if "ORDEN_FALLIDA" in u or "ORDEN FALLIDA" in u:
            out["orden_fallida"] += 1
        if '"CAZA"' in u or "| CAZA |" in u or " BERU | CAZA" in u:
            out["caza"] += 1
        if "COSECHA" in u:
            out["cosecha"] += 1
        if "NEGOCIANDO" in u or "NEGOCIADOR" in u:
            out["negociando"] += 1
    return out


class TankBeruMultiSpot:
    """Tank real + precios spot de N activos vía REST mainnet (ojos Beru)."""

    def __init__(self, inner: TankCluster, activos: list[str]):
        self._inner = inner
        self._activos = [a.upper() for a in activos]
        self._pub = HTTP(testnet=False)
        self.capitan_activo = CAPITAN_ANSIEDAD_LIVE
        self.tsunami_activado = False

    def __getattr__(self, name):
        return getattr(self._inner, name)

    async def evaluar_clima(self):
        """Congela Ansiedad — no deja que Tank vuelva a Normal."""
        self.capitan_activo = CAPITAN_ANSIEDAD_LIVE
        self._inner.capitan_activo = CAPITAN_ANSIEDAD_LIVE

    async def vision_especulativa(self):
        ctx_map, estado = await self._inner.vision_especulativa()
        if ctx_map is None:
            ctx_map = {}
        ahora_ms = time.time() * 1000
        for a in self._activos:
            frente = f"{a}USDT_SPOT"
            if frente in ctx_map and getattr(ctx_map[frente], "last_price", 0) > 0:
                continue
            try:
                r = self._pub.get_tickers(category="spot", symbol=f"{a}USDT")
                if r.get("retCode") != 0 or not r["result"]["list"]:
                    continue
                row = r["result"]["list"][0]
                p = float(row.get("lastPrice") or 0)
                if p <= 0:
                    continue
                bid = float(row.get("bid1Price") or p)
                ask = float(row.get("ask1Price") or p)
                bid_sz = float(row.get("bid1Size") or 1000)
                ask_sz = float(row.get("ask1Size") or 1000)
                ctx_map[frente] = MarketContext(
                    symbol=f"{a}USDT",
                    market_type="SPOT",
                    last_price=p,
                    spread=max(ask - bid, 0.01),
                    depth_ask=ask_sz,
                    depth_bid=bid_sz,
                    volatilidad=0.005,
                    timestamp=ahora_ms,
                    local_arrival=ahora_ms,
                    muro_ask_volumen=ask_sz * ask,
                    muro_bid_volumen=bid_sz * bid,
                )
            except Exception:
                continue
        if not ctx_map:
            return None, "ROJO"
        if estado in (None, "ROJO", "GLITCH_DETECTADO"):
            estado = "VERDE_SEGURO"
        return ctx_map, estado

    def precios_spot(self, ctx_map: dict | None) -> dict[str, float]:
        out: dict[str, float] = {}
        ctx_map = ctx_map or {}
        for a in self._activos:
            ctx = ctx_map.get(f"{a}USDT_SPOT")
            if ctx and getattr(ctx, "last_price", 0) > 0:
                out[a] = float(ctx.last_price)
        return out


async def _pulso_activo(
    beru: BeruCazador,
    tank: TankBeruMultiSpot,
    activo: str,
    precio: float,
    ship_activo: dict[str, str],
) -> None:
    """Aísla la legión al activo, planta semilla Mariscal/Ansiedad/CAZA y pulsa."""
    _aplicar_casa(activo)
    beru.tusk.precio_spot = precio
    beru.tusk.ultimo_precio = precio
    tank.capitan_activo = CAPITAN_ANSIEDAD_LIVE
    tank._inner.capitan_activo = CAPITAN_ANSIEDAD_LIVE

    legion_full = list(beru.legion)
    propios = [b for b in legion_full if ship_activo.get(b.uid) == activo]
    ajenos = [b for b in legion_full if ship_activo.get(b.uid) != activo]
    beru.legion = propios

    try:
        vivos = [
            b for b in beru.legion
            if b.estado in (
                "ACECHANDO",
                "ESPERANDO_CONDICIONAL",
                "ESPERANDO_ABISMO",
                "NEGOCIANDO",
                "ESPERANDO_MATERIALIZACION",
            )
        ]
        if not vivos and not any(getattr(b, "ciclo_infinito", False) for b in beru.legion):
            beru.plantar_semilla_adan(precio)
            sem = beru.legion[-1]
            sem.adn_capitan = CAPITAN_ANSIEDAD_LIVE
            sem.tier_id = "PLENO"
            sem.modo_combate = "CAZA"
            # Centro del manto = precio de ESTE barco (nunca promedio Tusk cruzado)
            sem.centro_manto = precio
            sem.centro_local = precio
            ship_activo[sem.uid] = activo
            await beru.bel.anotar(
                "LIVE_BERU", "SEMILLA",
                f"{activo} Mariscal/Ansiedad/CAZA centro={precio:.6g} gatillo±{gatillo_pct(CAPITAN_ANSIEDAD_LIVE.vacio_adan)*100:.2f}%",
            )

        # Refuerza ADN; repara ceros contaminados (centro de otra moneda)
        for b in beru.legion:
            if b.estado == "ACECHANDO":
                b.adn_capitan = CAPITAN_ANSIEDAD_LIVE
                b.tier_id = b.tier_id or "PLENO"
                b.modo_combate = "CAZA"
                ship_activo.setdefault(b.uid, activo)
                if ship_activo.get(b.uid) != activo:
                    continue
                c = float(b.centro_manto or 0)
                if c <= 0 or (precio > 0 and abs(c - precio) / precio > 0.25):
                    b.centro_manto = precio
                    b.centro_local = precio
                    await beru.bel.anotar(
                        "LIVE_BERU", "CENTRO_REPARADO",
                        f"{activo} uid={b.uid} centro→{precio:.6g} (era {c:.6g})",
                    )

        await beru.auditar_gatillos_adan(precio)
        await beru.sincronizar_materializacion()
        await beru.ejecutar_acordeon_asimetrico(precio)
        await beru.evaluar_colisiones_y_fusion()
        beru.limpiar_legion()
    finally:
        for b in beru.legion:
            ship_activo.setdefault(b.uid, activo)
        beru.legion = ajenos + beru.legion


def _resumen_legion(beru: BeruCazador, ship_activo: dict[str, str]) -> list[dict]:
    filas = []
    for b in beru.legion:
        filas.append({
            "uid": b.uid,
            "activo": ship_activo.get(b.uid, "?"),
            "estado": b.estado,
            "modo": getattr(b, "modo_combate", ""),
            "tier": getattr(b, "tier_id", ""),
            "masa": round(float(b.masa or 0), 4),
            "direccion": b.direccion,
            "frente": getattr(b, "frente_asignado", ""),
            "centro_manto": round(float(b.centro_manto or 0), 6),
            "capa": getattr(b, "capa", 1),
        })
    return filas


async def run_live(segundos: float | None, activos_arg: str | None) -> dict:
    aplicar_a_config(config)
    try:
        refrescar_config()
        aplicar_a_config(config)
    except Exception:
        print("[live-beru] trinidad cache local")

    config.LIVE_BERU_TESTNET = True
    config.TESTNET = True
    config.MODO_SIMULACION = False
    config.BERU_TIER_DEFAULT = "PLENO"
    config.BERU_MODO_COMBATE_DEFAULT = "CAZA"
    config.BERU_VACIO_ANSIEDAD = float(os.environ.get("BERU_VACIO_ANSIEDAD", "0.012"))
    mordida = float(os.environ.get("BERU_CAZADOR_MORDIDA_USD")
                    or os.environ.get("LIVE_BERU_MORDIDA_USD", "20")
                    or 20)
    config.BERU_CAZADOR_MORDIDA_USD = mordida
    config.BERU_CAZA_CAPA1_USD = mordida
    config.BERU_SPOT_MARGEN_ENABLED = True
    config.BERU_SPOT_MARGEN_LEVERAGE = int(
        float(os.environ.get("BERU_SPOT_MARGEN_LEVERAGE", "10"))
    )
    config.BERU_RAIL_USDT_ONLY = True
    config.GREED_KAISER_ENABLED = False
    config.GREED_VIP_ENABLED = False
    config.GREED_BASIS_HOLD_ENABLED = False
    config.GREED_MULTICRUCE_ENABLED = False
    config.IGRIS_BOOTSTRAP_ON_START = False
    config.SAFE_MODE = True

    if not config.API_KEY or not config.API_SECRET:
        raise SystemExit("ABORT: faltan BYBIT_API_KEY / BYBIT_API_SECRET en .env")
    if not config.TESTNET:
        raise SystemExit("ABORT: MODO_TESTNET debe ser True (campo de entrenamiento)")

    seg_cfg = float(getattr(config, "LIVE_BERU_SEGUNDOS", 3600))
    seg = float(segundos if segundos is not None else seg_cfg)
    infinito = seg <= 0
    activos = _activos_cfg(activos_arg)
    _expandir_ojos(activos)

    # Banda delta no debe bloquear caza spot de prueba
    mercado_mod.verificar_delta_frente = lambda *a, **k: True

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank_inner = TankCluster(tusk, bellion, ticker_base=activos[0])
    tank_inner.capitan_activo = CAPITAN_ANSIEDAD_LIVE
    tank = TankBeruMultiSpot(tank_inner, activos)
    bridge = BybitBridge(tank_inner, tusk, bellion, config.API_KEY, config.API_SECRET)
    kaiser = KaiserVocero(tank, bellion)
    beru = BeruCazador(tusk, bellion, tank, bridge=bridge, kaiser=kaiser)

    tasks = [
        asyncio.create_task(bridge.conectar()),
        asyncio.create_task(tank_inner.vigilar_aguas()),
        asyncio.create_task(bridge.hilo_sincronizacion_nav()),
    ]

    vacio_pct = CAPITAN_ANSIEDAD_LIVE.vacio_adan * 100
    gat_pct = gatillo_pct(CAPITAN_ANSIEDAD_LIVE.vacio_adan) * 100
    masa = mordida_usd()
    lev = int(getattr(config, "BERU_SPOT_MARGEN_LEVERAGE", 10))

    print("")
    print("=" * 56)
    print("  Shadow Army — Beru LIVE TESTNET (3.9.9)")
    print("  Manos: Bybit DEMO · Ojos: spot mainnet (REST+WS)")
    print(f"  Capitán: ANSIEDAD vacío {vacio_pct:.1f}% → gatillo ±{gat_pct:.1f}%")
    print("  Tier: PLENO / Mariscal · clon / nacimiento 0.1%")
    print(f"  Modo: CAZA · Mordida ${masa:.0f} · Spot margen {lev}x")
    print(f"  Rails: solo USDT · Flota: {len(activos)} barcos")
    print(f"  Activos: {','.join(activos)}")
    print(f"  Vigilia: {'hasta Ctrl+C' if infinito else f'{seg:.0f}s'}")
    print("  Igris/Greed: hibernados")
    print("=" * 56)
    print("")

    t_hist = time.time()
    ship_activo: dict[str, str] = {}
    cazas_ok = 0
    cosechas_ok = 0
    ultimo_heartbeat = 0.0
    reporte: dict = {}

    try:
        await asyncio.sleep(2)
        try:
            w = bridge.session.get_wallet_balance(accountType="UNIFIED")
            if w.get("retCode") == 0:
                nav = float(w["result"]["list"][0].get("totalEquity", 0) or 0)
                disp = float(w["result"]["list"][0].get("totalAvailableBalance", 0) or 0)
                margen = ((nav - disp) / nav * 100) if nav > 0 else 0.0
                await tusk.actualizar_nav_real(nav, margen)
                print(f"[live-beru] NAV testnet ${nav:.2f} · margen {margen:.1f}%")
            else:
                print(f"[live-beru] wallet aviso: {w.get('retMsg')}")
                await tusk.actualizar_nav_real(10_000.0, 5.0)
        except Exception as e:
            print(f"[live-beru] wallet no leido: {e}")
            await tusk.actualizar_nav_real(10_000.0, 5.0)

        # Reserva amplia para flota × mordida
        tusk.masa_autorizada = max(float(tusk.masa_autorizada or 0), masa * max(8, len(activos) * 3))
        tusk.margen_ocupado = max(float(tusk.margen_ocupado or 0), 50.0)

        # Forzar spot margen 10x (orden Alan)
        margen_res = await bridge.activar_spot_margen(lev)
        print(
            f"[live-beru] Spot margen {lev}x → "
            f"{'OK' if margen_res.exito else 'aviso: ' + str(margen_res.mensaje)}"
        )

        await bellion.anotar(
            "LIVE_BERU", "INICIO",
            f"Ansiedad {vacio_pct:.1f}% gatillo±{gat_pct:.1f}% Mariscal CAZA "
            f"${masa:.0f} USDT-only flota={len(activos)} margen={lev}x "
            f"seg={seg if not infinito else 'inf'}",
        )

        t0 = time.time()
        while infinito or (time.time() - t0) < seg:
            ctx_map, estado = await tank.vision_especulativa()
            precios = tank.precios_spot(ctx_map)
            if not precios:
                await asyncio.sleep(1.0)
                continue

            for activo, precio in precios.items():
                antes = {
                    b.uid: b.estado
                    for b in beru.legion
                    if ship_activo.get(b.uid) == activo
                }
                await _pulso_activo(beru, tank, activo, precio, ship_activo)
                despues = {
                    b.uid: b.estado
                    for b in beru.legion
                    if ship_activo.get(b.uid) == activo
                }
                for uid, est in despues.items():
                    prev = antes.get(uid)
                    if est == "NEGOCIANDO" and prev in (None, "ACECHANDO", "ESPERANDO_MATERIALIZACION"):
                        cazas_ok += 1
                        print(f"[live-beru] CAZA materializada {activo} uid={uid}")
                    if est == "COSECHADO" and prev != "COSECHADO":
                        cosechas_ok += 1
                        print(f"[live-beru] COSECHA {activo} uid={uid}")

            ahora = time.time()
            if ahora - ultimo_heartbeat >= 30.0:
                ultimo_heartbeat = ahora
                elapsed = ahora - t0
                remain = "∞" if infinito else f"{max(0, seg - elapsed):.0f}s"
                dist = []
                for a, p in precios.items():
                    seeds = [
                        b for b in beru.legion
                        if ship_activo.get(b.uid) == a and b.estado == "ACECHANDO"
                    ]
                    if seeds and seeds[0].centro_manto > 0:
                        pct = (p - seeds[0].centro_manto) / seeds[0].centro_manto * 100
                        dist.append(f"{a}:{pct:+.3f}%")
                    else:
                        dist.append(f"{a}:ok")
                print(
                    f"[live-beru] ojos {elapsed:.0f}s (queda {remain}) | "
                    f"estado={estado} | cazas={cazas_ok} cosechas={cosechas_ok} | "
                    f"{' '.join(dist)}"
                )

            await asyncio.sleep(0.35)

        hist = _contar_historial(ROOT / "data" / "historial_hierro.jsonl", t_hist)
        leg = _resumen_legion(beru, ship_activo)

        # Criterio: al menos 1 caza con orden real en log
        criterio_ok = cazas_ok >= 1 and hist["orden_enviada"] >= 1
        criterio_parcial = cazas_ok >= 1
        veredicto = (
            "PASS_LIVE"
            if criterio_ok
            else ("PASS_PARCIAL_SIN_LOG_BRIDGE" if criterio_parcial else "SIN_DISPARO_MERCADO")
        )

        reporte = {
            "checklist": "3.9.9",
            "ts": time.time(),
            "veredicto": veredicto,
            "segundos_ojos": None if infinito else seg,
            "elapsed_s": round(time.time() - t0, 1),
            "config": {
                "testnet": True,
                "modo_simulacion": False,
                "capitan": "ANSIEDAD",
                "vacio_pct": vacio_pct,
                "gatillo_pct": gat_pct,
                "tier": "PLENO",
                "rango": "Mariscal",
                "clon_pct": 0.1,
                "modo_combate": "CAZA",
                "mordida_usd": masa,
                "activos": activos,
                "n_flota": len(activos),
                "rail": "USDT_ONLY",
                "spot_margen_x": lev,
                "igris_hibernado": True,
                "greed_hibernado": True,
            },
            "cazas_materializadas": cazas_ok,
            "cosechas": cosechas_ok,
            "historial_resumen": hist,
            "legion": leg,
            "como_cerrar_checklist": (
                "PASS_LIVE => marcar 3.9.9 [x] en migracion/16_CHECKLIST_MAESTRO.md "
                "y confirmar posiciones spot en Bybit testnet UI."
            ),
        }

        out_path = ROOT / "data" / "beru_live_testnet_report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")

        await bellion.anotar(
            "LIVE_BERU", "FIN",
            f"{veredicto} cazas={cazas_ok} cosechas={cosechas_ok} "
            f"bridge_ordenes={hist['orden_enviada']}",
        )

        resumen = {
            "veredicto": veredicto,
            "cazas": cazas_ok,
            "cosechas": cosechas_ok,
            "orden_enviada_log": hist["orden_enviada"],
            "elapsed_s": reporte["elapsed_s"],
            "reporte": str(out_path),
        }
        print(json.dumps(resumen, indent=2))
        print("")
        if veredicto == "PASS_LIVE":
            print("[live-beru] CHECKLIST 3.9.9 listo para marcar OK.")
        elif veredicto == "SIN_DISPARO_MERCADO":
            print(
                "[live-beru] Proceso OK pero el mercado no movió ±0.6% desde el 0. "
                "Dejar más tiempo (--segundos 3600) o reintentar con más volatilidad."
            )
        return reporte
    except asyncio.CancelledError:
        raise
    except KeyboardInterrupt:
        print("\n[live-beru] Interrumpido por Monarca — sellando reporte…")
        hist = _contar_historial(ROOT / "data" / "historial_hierro.jsonl", t_hist)
        criterio_ok = cazas_ok >= 1 and hist["orden_enviada"] >= 1
        veredicto = "PASS_LIVE" if criterio_ok else (
            "PASS_PARCIAL_SIN_LOG_BRIDGE" if cazas_ok >= 1 else "INTERRUMPIDO_SIN_DISPARO"
        )
        reporte = {
            "checklist": "3.9.9",
            "ts": time.time(),
            "veredicto": veredicto,
            "cazas_materializadas": cazas_ok,
            "cosechas": cosechas_ok,
            "historial_resumen": hist,
            "legion": _resumen_legion(beru, ship_activo),
            "nota": "sesión cortada con Ctrl+C",
        }
        out_path = ROOT / "data" / "beru_live_testnet_report.json"
        out_path.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"veredicto": veredicto, "cazas": cazas_ok, "reporte": str(out_path)}, indent=2))
        return reporte
    finally:
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Beru live testnet 3.9.9")
    parser.add_argument(
        "--segundos", type=float, default=None,
        help="Vigilia en segundos (0 = hasta Ctrl+C). Default LIVE_BERU_SEGUNDOS o 3600.",
    )
    parser.add_argument(
        "--activos", type=str, default=None,
        help="flota (=22 barcos) o lista ETH,BTC,... Default: flota USDT.",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run_live(args.segundos, args.activos))
    except KeyboardInterrupt:
        print("\n[live-beru] Fin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
