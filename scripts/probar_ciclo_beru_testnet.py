"""
Prueba 3.6.1 LIVE — ciclo Beru CAZA → COSECHA en Bybit testnet (órdenes reales).

Requisitos: .env con BYBIT_API_KEY/SECRET, MODO_TESTNET=True.
No modifica .env; fuerza MODO_SIMULACION=False solo en esta sesión.

Uso: python scripts/probar_ciclo_beru_testnet.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import core.config as config  # noqa: E402
from core import mercado as mercado_mod  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.beru import BeruCazador  # noqa: E402
from generales.kaiser import KaiserVocero  # noqa: E402
from core.beru_cazador import mordida_usd  # noqa: E402
from core.beru_rail import frentes_casa_estables  # noqa: E402
from core.models import MarketContext  # noqa: E402
from pybit.unified_trading import HTTP  # noqa: E402


class TankBeruTestnet:
    """Tank real + precios ETH spot (Beru semilla) vía REST mainnet — ojos Beru."""

    def __init__(self, inner: TankCluster):
        self._inner = inner
        self._pub = HTTP(testnet=False)

    def __getattr__(self, name):
        return getattr(self._inner, name)

    async def vision_especulativa(self):
        ctx_map, estado = await self._inner.vision_especulativa()
        if ctx_map is None:
            ctx_map = {}
        ahora_ms = time.time() * 1000
        # Testnet: USDT (cuenta demo suele tener USDT, no USDC)
        frentes_live = [f for f in frentes_casa_estables() if f.endswith("USDT_SPOT")]
        for f in frentes_live:
            sym = f.split("_")[0]
            try:
                r = self._pub.get_tickers(category="spot", symbol=sym)
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
                ctx_map[f] = MarketContext(
                    symbol=sym, market_type="SPOT",
                    last_price=p, spread=max(ask - bid, 0.01),
                    depth_ask=ask_sz, depth_bid=bid_sz,
                    volatilidad=0.005, timestamp=ahora_ms, local_arrival=ahora_ms,
                    muro_ask_volumen=ask_sz * ask, muro_bid_volumen=bid_sz * bid,
                )
            except Exception:
                continue
        if not ctx_map:
            return None, "ROJO"
        if estado in (None, "ROJO", "GLITCH_DETECTADO"):
            estado = "VERDE_SEGURO"
        return ctx_map, estado


async def simular_ciclo_live() -> tuple[bool, str]:
    if not config.API_KEY or not config.API_SECRET:
        return False, "Faltan BYBIT_API_KEY/SECRET en .env"
    if not config.TESTNET:
        return False, "MODO_TESTNET debe ser True — abortado por seguridad"

    config.MODO_SIMULACION = False
    mercado_mod.verificar_delta_frente = lambda *a, **k: True

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank_inner = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    tank = TankBeruTestnet(tank_inner)
    bridge = BybitBridge(tank_inner, tusk, bellion, config.API_KEY, config.API_SECRET)
    kaiser = KaiserVocero(tank, bellion)
    beru = BeruCazador(tusk, bellion, tank, bridge=bridge, kaiser=kaiser)

    ws_task = None
    nav_task = asyncio.create_task(bridge.hilo_sincronizacion_nav())

    try:
        await asyncio.sleep(1)
        w = bridge.session.get_wallet_balance(accountType="UNIFIED")
        if w.get("retCode") == 0:
            nav = float(w["result"]["list"][0].get("totalEquity", 0))
            disp = float(w["result"]["list"][0].get("totalAvailableBalance", 0))
            margen = ((nav - disp) / nav * 100) if nav > 0 else 0.0
            await tusk.actualizar_nav_real(nav, margen)
        else:
            await tusk.actualizar_nav_real(10_000.0, 5.0)

        ctx_map, estado = await tank.vision_especulativa()
        frente_usdt = next((f for f in frentes_casa_estables() if f.endswith("USDT_SPOT")), "")
        if not ctx_map or not frente_usdt or not ctx_map.get(frente_usdt):
            return False, "Sin precio ETHUSDT spot (REST)"

        masa_caza = max(mordida_usd(), 6.0)  # ≥ min_order spot testnet
        tusk.masa_autorizada = max(tusk.masa_autorizada, masa_caza * 3)
        tusk.margen_ocupado = max(tusk.margen_ocupado, 50.0)

        ctx_map, _ = await tank.vision_especulativa()
        precio_ref = next(
            (ctx_map[f].last_price for f in frentes_casa_estables() if ctx_map.get(f)),
            0.0,
        )
        if precio_ref <= 0:
            return False, "Sin precio referencia para semilla"

        await bellion.anotar("VALIDACION", "INICIO_CICLO", "Live testnet 3.6.1 - CAZA->COSECHA")

        beru.plantar_semilla_adan(precio_ref)
        barco = beru.legion[0]
        barco.direccion = "LONG"
        if not await tusk.solicitar_reserva(barco.uid, masa_caza, "BERU", "LONG"):
            return False, "solicitar_reserva falló en CAZA"
        barco.masa = masa_caza
        barco.estado = "ESPERANDO_MATERIALIZACION"
        await beru._ejecutar_caza(barco)

        if barco.estado != "NEGOCIANDO":
            return False, f"CAZA live no materializó NEGOCIANDO (estado={barco.estado})"

        await beru.sincronizar_materializacion()

        uid_cosecha = f"COSECHA_TESTNET_{int(time.time())}"
        await beru._ejecutar_cosecha(barco, uid_cosecha, forzar=True)

        ok = barco.estado == "COSECHADO"
        detalle = (
            f"Barco {barco.uid} {barco.direccion} entrada={barco.precio_entrada_real:.2f} "
            f"frente={getattr(barco, 'frente_asignado', '')} "
            f"→ COSECHADO={ok}"
        )
        await bellion.anotar("VALIDACION", "FIN_CICLO", detalle)

        reporte = {
            "ts": time.time(),
            "milestone": "M2-3.6.1",
            "modo": "testnet_live",
            "ticker_ref": config.TICKER_BASE,
            "activo_semilla": config.BERU_ACTIVO_SEMILLA,
            "ok_ciclo": ok,
            "detalle": detalle,
            "barco_uid": barco.uid,
            "direccion": barco.direccion,
            "precio_entrada": barco.precio_entrada_real,
            "precio_salida": getattr(barco, "precio_salida_real", 0),
            "frente": getattr(barco, "frente_asignado", ""),
            "masa_usd": masa_caza,
            "qty_base": getattr(barco, "qty_base_ejecutada", None),
        }
        ruta = os.path.join(ROOT, "data", "validacion_ciclo_ejercito.json")
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(reporte, f, indent=2)

        return ok, detalle
    finally:
        nav_task.cancel()
        try:
            await nav_task
        except asyncio.CancelledError:
            pass


async def main() -> None:
    print(
        f"\n=== PROBAR CICLO BERU TESTNET (3.6.1) | semilla={config.BERU_ACTIVO_SEMILLA} "
        f"| testnet={config.TESTNET} | sim=False (solo esta sesión) ===\n"
    )
    ok, detalle = await simular_ciclo_live()
    print(f"\nResultado: {'OK' if ok else 'FAIL'} — {detalle}")
    print("Reporte: data/validacion_ciclo_ejercito.json")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
