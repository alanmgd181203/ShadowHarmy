import asyncio
import json
import time
import ssl
import uuid
import websockets
from pybit.unified_trading import HTTP
import core.config as config

# === [EL PUENTE DE LA HIDRA: VISIÓN + MANOS] ===


class OrdenResultado:
    """Resultado de una operación enviada al exchange."""
    def __init__(self, exito, order_id="", link_id="", mensaje="", datos=None):
        self.exito = exito
        self.order_id = order_id
        self.link_id = link_id
        self.mensaje = mensaje
        self.datos = datos or {}


class BybitBridge:
    def __init__(self, tank_cluster, tusk, bellion, api_key=None, api_secret=None):
        self.tank = tank_cluster
        self.tusk = tusk
        self.bel = bellion

        # 🌐 Ojos en la Realidad (Mainnet siempre — precios reales)
        self.url = "wss://stream.bybit.com/v5/public/linear"
        self.symbols = ["LTCUSDT"]
        self.session = None

        # Contadores de error para backoff
        self._nav_errores_consecutivos = 0
        self._NAV_BACKOFF_MAX = 300  # 5 min máximo entre reintentos

        if api_key and api_secret:
            # 🛡️ Manos en Testnet (órdenes van aquí)
            self.session = HTTP(
                testnet=config.TESTNET,
                api_key=api_key,
                api_secret=api_secret
            )

    # ================================================================
    # OJOS — WebSocket público (precios mainnet)
    # ================================================================

    async def conectar(self):
        """Mantiene la conexión WebSocket activa con la Mainnet."""
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        while True:
            try:
                async with websockets.connect(self.url, ssl=ssl_context, ping_interval=20) as websocket:
                    sub_msg = json.dumps({"op": "subscribe", "args": [f"tickers.{s}" for s in self.symbols]})
                    await websocket.send(sub_msg)

                    async for message in websocket:
                        data = json.loads(message)
                        if "data" in data:
                            await self._procesar_latido(data)
                        elif "ret_msg" in data or "op" in data:
                            for nodo in self.tank.nodos:
                                nodo.ultima_actualizacion = time.time()

            except Exception as e:
                await self.bel.anotar("BRIDGE", "RECONEXIÓN", f"Error de red: {str(e)}")
                await asyncio.sleep(5)

    async def _procesar_latido(self, payload):
        """Distribuye el precio real de Mainnet a todos los nodos del Tank."""
        ticker = payload.get("data", {})
        precio_raw = ticker.get("lastPrice")

        if not precio_raw:
            return

        precio = float(precio_raw)
        ts_server = int(payload.get("ts", time.time() * 1000))
        latencia_local = abs((time.time() * 1000) - ts_server)

        for nodo in self.tank.nodos:
            nodo.ultima_actualizacion = time.time()
            nodo.latencia_ms = latencia_local
            nodo.p_usdt_lineal = precio

    # ================================================================
    # MANOS — Órdenes (testnet por defecto)
    # ================================================================

    def _generar_link_id(self, prefijo="SA"):
        """Genera orderLinkId único e idempotente (máx 36 chars Bybit)."""
        uid = uuid.uuid4().hex[:24]
        return f"{prefijo}-{uid}"

    async def place_order(self, symbol, side, qty, order_type="Market",
                          price=None, link_id=None, category="linear"):
        """
        Envía una orden al exchange con idempotencia.

        Args:
            symbol: par (e.g. "LTCUSDT")
            side: "Buy" o "Sell"
            qty: cantidad en unidades del activo (str)
            order_type: "Market" o "Limit"
            price: precio límite (solo para Limit)
            link_id: orderLinkId personalizado (se genera si no se pasa)
            category: "linear", "inverse", "spot"

        Returns:
            OrdenResultado con exito, order_id, link_id, mensaje
        """
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")

        if not link_id:
            link_id = self._generar_link_id()

        params = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "orderLinkId": link_id,
        }

        if order_type == "Limit" and price is not None:
            params["price"] = str(price)
            params["timeInForce"] = "GTC"

        try:
            response = self.session.place_order(**params)

            if response.get("retCode") == 0:
                order_id = response["result"].get("orderId", "")
                await self.bel.anotar(
                    "BRIDGE", "ORDEN_ENVIADA",
                    f"{side} {qty} {symbol} @{order_type} | ID:{order_id} LINK:{link_id}"
                )
                return OrdenResultado(True, order_id=order_id, link_id=link_id, datos=response["result"])
            else:
                msg = response.get("retMsg", "Error desconocido")
                await self.bel.anotar("BRIDGE", "ORDEN_RECHAZADA", f"{msg} | LINK:{link_id}")
                return OrdenResultado(False, link_id=link_id, mensaje=msg)

        except Exception as e:
            await self.bel.anotar("BRIDGE", "ORDEN_ERROR", f"{str(e)} | LINK:{link_id}")
            return OrdenResultado(False, link_id=link_id, mensaje=str(e))

    async def cancel_order(self, symbol, order_id=None, link_id=None, category="linear"):
        """
        Cancela una orden abierta por orderId o orderLinkId.
        """
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")

        params = {"category": category, "symbol": symbol}

        if order_id:
            params["orderId"] = order_id
        elif link_id:
            params["orderLinkId"] = link_id
        else:
            return OrdenResultado(False, mensaje="Se requiere orderId o linkId")

        try:
            response = self.session.cancel_order(**params)

            if response.get("retCode") == 0:
                await self.bel.anotar("BRIDGE", "ORDEN_CANCELADA", f"ID:{order_id or link_id} {symbol}")
                return OrdenResultado(True, order_id=order_id or "", link_id=link_id or "", datos=response.get("result", {}))
            else:
                msg = response.get("retMsg", "Error desconocido")
                await self.bel.anotar("BRIDGE", "CANCEL_RECHAZADA", f"{msg} | {order_id or link_id}")
                return OrdenResultado(False, mensaje=msg)

        except Exception as e:
            await self.bel.anotar("BRIDGE", "CANCEL_ERROR", f"{str(e)}")
            return OrdenResultado(False, mensaje=str(e))

    async def amend_order(self, symbol, order_id=None, link_id=None,
                          new_qty=None, new_price=None, category="linear"):
        """
        Modifica una orden abierta (precio y/o cantidad).
        """
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")

        params = {"category": category, "symbol": symbol}

        if order_id:
            params["orderId"] = order_id
        elif link_id:
            params["orderLinkId"] = link_id
        else:
            return OrdenResultado(False, mensaje="Se requiere orderId o linkId")

        if new_qty is not None:
            params["qty"] = str(new_qty)
        if new_price is not None:
            params["price"] = str(new_price)

        try:
            response = self.session.amend_order(**params)

            if response.get("retCode") == 0:
                await self.bel.anotar("BRIDGE", "ORDEN_MODIFICADA", f"ID:{order_id or link_id} → qty:{new_qty} price:{new_price}")
                return OrdenResultado(True, order_id=order_id or "", link_id=link_id or "", datos=response.get("result", {}))
            else:
                msg = response.get("retMsg", "Error desconocido")
                await self.bel.anotar("BRIDGE", "AMEND_RECHAZADA", f"{msg} | {order_id or link_id}")
                return OrdenResultado(False, mensaje=msg)

        except Exception as e:
            await self.bel.anotar("BRIDGE", "AMEND_ERROR", f"{str(e)}")
            return OrdenResultado(False, mensaje=str(e))

    # ================================================================
    # CONFIRMACIÓN DE FILL (REGLA-R07)
    # ================================================================

    async def esperar_fill(self, symbol, order_id=None, link_id=None,
                           timeout_s=60, intervalo_s=2, category="linear"):
        """
        Polling hasta confirmar que la orden se ejecutó (Filled/PartiallyFilled).

        Returns:
            OrdenResultado con exito=True si fill confirmado, False si timeout/error.
            datos incluye: avgPrice, cumExecQty, orderStatus
        """
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")

        inicio = time.time()

        while (time.time() - inicio) < timeout_s:
            try:
                params = {"category": category, "symbol": symbol}
                if order_id:
                    params["orderId"] = order_id
                elif link_id:
                    params["orderLinkId"] = link_id

                response = self.session.get_order_history(**params)

                if response.get("retCode") == 0:
                    ordenes = response["result"].get("list", [])
                    for orden in ordenes:
                        oid = orden.get("orderId", "")
                        olid = orden.get("orderLinkId", "")

                        if (order_id and oid == order_id) or (link_id and olid == link_id):
                            status = orden.get("orderStatus", "")

                            if status == "Filled":
                                avg_price = float(orden.get("avgPrice", 0))
                                cum_qty = float(orden.get("cumExecQty", 0))
                                await self.bel.anotar(
                                    "BRIDGE", "FILL_CONFIRMADO",
                                    f"{symbol} {cum_qty}@{avg_price} | ID:{oid}"
                                )
                                return OrdenResultado(
                                    True, order_id=oid, link_id=olid,
                                    datos={"avgPrice": avg_price, "cumExecQty": cum_qty, "orderStatus": status}
                                )

                            elif status in ("Cancelled", "Rejected", "Deactivated"):
                                await self.bel.anotar(
                                    "BRIDGE", "FILL_FALLIDO",
                                    f"Status={status} | ID:{oid}"
                                )
                                return OrdenResultado(False, order_id=oid, link_id=olid, mensaje=f"Orden {status}")

                            elif status == "PartiallyFilled":
                                cum_qty = float(orden.get("cumExecQty", 0))
                                await self.bel.anotar(
                                    "BRIDGE", "FILL_PARCIAL",
                                    f"{symbol} parcial {cum_qty} | ID:{oid}"
                                )

            except Exception as e:
                await self.bel.anotar("BRIDGE", "FILL_POLL_ERROR", str(e))

            await asyncio.sleep(intervalo_s)

        await self.bel.anotar("BRIDGE", "FILL_TIMEOUT", f"Timeout {timeout_s}s para {order_id or link_id}")
        return OrdenResultado(False, mensaje=f"Timeout {timeout_s}s sin fill")

    # ================================================================
    # NAV — Sincronización de balance (con log y backoff)
    # ================================================================

    async def hilo_sincronizacion_nav(self):
        """Sincroniza el balance y calcula el Oxígeno real de la cuenta."""
        if not self.session:
            return

        while True:
            try:
                response = self.session.get_wallet_balance(accountType="UNIFIED")
                if response['retCode'] == 0:
                    data = response['result']['list'][0]
                    nav_total = float(data.get('totalEquity', 0.0))
                    disponible = float(data.get('totalAvailableBalance', 0.0))

                    margen_ocupado = ((nav_total - disponible) / nav_total * 100) if nav_total > 0 else 0.0
                    await self.tusk.actualizar_nav_real(nav_total, margen_ocupado)

                    self._nav_errores_consecutivos = 0
                else:
                    msg = response.get('retMsg', 'retCode != 0')
                    await self.bel.anotar("BRIDGE", "NAV_ERROR_API", msg)
                    self._nav_errores_consecutivos += 1

            except Exception as e:
                self._nav_errores_consecutivos += 1
                await self.bel.anotar(
                    "BRIDGE", "NAV_EXCEPCIÓN",
                    f"Error #{self._nav_errores_consecutivos}: {str(e)}"
                )

            # Backoff exponencial: 30s base, duplica por cada error, máx 5 min
            espera = min(30 * (2 ** self._nav_errores_consecutivos), self._NAV_BACKOFF_MAX)
            if self._nav_errores_consecutivos == 0:
                espera = 30
            await asyncio.sleep(espera)
