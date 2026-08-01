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


def _pares_a_tuples(pares: list[dict]) -> list[tuple[str, str]]:
    out = []
    seen = set()
    for p in pares:
        sym, frente = p["symbol"], p["frente"]
        if frente in seen:
            continue
        seen.add(frente)
        out.append((sym, frente))
    return out


def _feeds_sharded(url: str, tuples: list[tuple[str, str]], label_prefix: str, shard_size: int) -> list[dict]:
    feeds = []
    for i in range(0, max(len(tuples), 1), shard_size):
        chunk = tuples[i : i + shard_size]
        if not chunk:
            break
        feeds.append({
            "url": url,
            "tickers": chunk,
            "books": chunk,
            "label": f"{label_prefix}-{i // shard_size + 1}",
        })
    return feeds


def _feeds_completos():
    """Ojos mainnet: spot + perps + futuros dated Bybit (sharded)."""
    spot_tuples = _pares_a_tuples(getattr(config, "SPOT_ALL_PARES", []))
    linear_tuples = _pares_a_tuples(
        getattr(config, "LINEAR_PERP_PARES", []) + getattr(config, "LINEAR_FUTURES_PARES", [])
    )
    inverse_tuples = _pares_a_tuples(
        getattr(config, "INVERSE_PERP_PARES", []) + getattr(config, "INVERSE_FUTURES_PARES", [])
    )

    spot_shard = getattr(config, "SPOT_WS_SHARD_SIZE", 150)
    deriv_shard = getattr(config, "DERIV_WS_SHARD_SIZE", 150)

    feeds = []
    feeds.extend(_feeds_sharded(
        "wss://stream.bybit.com/v5/public/linear",
        linear_tuples,
        "linear",
        deriv_shard,
    ))
    feeds.extend(_feeds_sharded(
        "wss://stream.bybit.com/v5/public/inverse",
        inverse_tuples,
        "inverse",
        deriv_shard,
    ))
    feeds.extend(_feeds_sharded(
        "wss://stream.bybit.com/v5/public/spot",
        spot_tuples,
        "spot",
        spot_shard,
    ))
    return feeds


class BybitBridge:
    def __init__(self, tank_cluster, tusk, bellion, api_key=None, api_secret=None):
        self.tank = tank_cluster
        self.tusk = tusk
        self.bel = bellion
        self.feeds = _feeds_completos()
        self.session = None

        self._nav_errores_consecutivos = 0
        self._NAV_BACKOFF_MAX = 300

        if api_key and api_secret:
            self.session = HTTP(
                testnet=config.TESTNET,
                api_key=api_key,
                api_secret=api_secret,
            )

    # ================================================================
    # OJOS — WebSocket público (precios + muros mainnet)
    # ================================================================

    async def conectar(self):
        """Refresca trinidad si stale, reconstruye feeds y lanza WS."""
        from core import trinidad

        await trinidad.refrescar_si_stale()
        trinidad.inicializar_config(config)
        self.feeds = _feeds_completos()
        self.tank.expandir_frentes(config.FRENTES_TANK)
        nspot = len(getattr(config, "FRENTES_SPOT_ALL", []))
        nlin = len(getattr(config, "FRENTES_LINEAR_PERP", []))
        nlinf = len(getattr(config, "FRENTES_LINEAR_FUTURES", []))
        ninv = len(getattr(config, "FRENTES_INVERSE_PERP", []))
        ninvf = len(getattr(config, "FRENTES_INVERSE_FUTURES", []))
        nshards = sum(1 for f in self.feeds if f.get("label"))
        await self.bel.anotar(
            "BRIDGE", "TRINIDAD",
            f"Sentidos: {nlin} perp + {nlinf} fut linear | {ninv}+{ninvf} inv | {nspot} spot ({nshards} WS)",
        )

        tareas = [self._loop_feed(feed) for feed in self.feeds]
        await asyncio.gather(*tareas)

    async def _loop_feed(self, feed):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        args = []
        for sym, _ in feed.get("tickers", []):
            args.append(f"tickers.{sym}")
        for sym, _ in feed.get("books", []):
            args.append(f"orderbook.50.{sym}")

        while True:
            try:
                async with websockets.connect(
                    feed["url"], ssl=ssl_context, ping_interval=20, open_timeout=15
                ) as websocket:
                    for i in range(0, len(args), 10):
                        lote = args[i : i + 10]
                        await websocket.send(json.dumps({"op": "subscribe", "args": lote}))
                        await asyncio.sleep(0.08)

                    async for message in websocket:
                        data = json.loads(message)
                        if "data" in data and "topic" in data:
                            await self._procesar_mensaje(data, feed)
                        elif "ret_msg" in data or data.get("op") == "subscribe":
                            for nodo in self.tank.nodos:
                                nodo.ultima_actualizacion = time.time()

            except Exception as e:
                label = feed.get("label") or feed["url"]
                await self.bel.anotar("BRIDGE", "RECONEXIÓN", f"{label}: {str(e)}")
                await asyncio.sleep(5)

    async def _procesar_mensaje(self, payload, feed):
        topic = payload.get("topic", "")
        ts_server = int(payload.get("ts", time.time() * 1000))
        latencia_local = abs((time.time() * 1000) - ts_server)

        frente = None
        if topic.startswith("tickers."):
            sym = topic.split(".", 1)[1]
            frente = self._symbol_a_frente(sym, feed)
            ticker = payload.get("data", {})
            if isinstance(ticker, list):
                ticker = ticker[0] if ticker else {}
            precio_raw = (
                ticker.get("lastPrice")
                or ticker.get("markPrice")
                or ticker.get("bid1Price")
                or ticker.get("ask1Price")
            )
            if precio_raw and frente:
                precio = float(precio_raw)
                for nodo in self.tank.nodos:
                    nodo.ultima_actualizacion = time.time()
                    nodo.latencia_ms = latencia_local
                    nodo.inyectar_verdad_real(frente, precio, latencia_local)
                fr_raw = ticker.get("fundingRate")
                if fr_raw not in (None, ""):
                    try:
                        rate = float(fr_raw)
                        for nodo in self.tank.nodos:
                            nodo.inyectar_funding(frente, rate)
                    except (TypeError, ValueError):
                        pass
                idx_raw = ticker.get("indexPrice")
                if idx_raw not in (None, ""):
                    try:
                        idx = float(idx_raw)
                        for nodo in self.tank.nodos:
                            nodo.inyectar_index(frente, idx)
                    except (TypeError, ValueError):
                        pass

        elif topic.startswith("orderbook."):
            parts = topic.split(".")
            if len(parts) >= 3:
                sym = parts[2]
                frente = self._symbol_a_frente(sym, feed)
                book = payload.get("data", {})
                msg_type = payload.get("type", "snapshot")
                bids = book.get("b", [])
                asks = book.get("a", [])
                if not frente:
                    return
                if msg_type == "snapshot":
                    for nodo in self.tank.nodos:
                        nodo.inyectar_libro_snapshot(frente, bids, asks)
                else:
                    if not bids and not asks:
                        return
                    for nodo in self.tank.nodos:
                        nodo.aplicar_delta_libro(frente, bids, asks)

    def _symbol_a_frente(self, symbol, feed):
        for sym, frente in feed.get("tickers", []) + feed.get("books", []):
            if sym == symbol:
                return frente
        return None

    @staticmethod
    def _sumar_niveles(niveles, top_n=5):
        total = 0.0
        for nivel in niveles[:top_n]:
            try:
                total += float(nivel[1])
            except (IndexError, TypeError, ValueError):
                continue
        return total

    # ================================================================
    # MANOS — Órdenes (testnet por defecto)
    # ================================================================

    def _generar_link_id(self, prefijo="SA"):
        uid = uuid.uuid4().hex[:24]
        return f"{prefijo}-{uid}"

    async def place_order(self, symbol, side, qty, order_type="Market",
                          price=None, link_id=None, category="linear", market_unit=None,
                          is_leverage=None):
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

        if market_unit:
            params["marketUnit"] = market_unit

        # Spot margen: 1 = pedir prestado (isLeverage Bybit V5)
        if is_leverage is not None and category == "spot":
            params["isLeverage"] = int(is_leverage)

        if order_type == "Limit" and price is not None:
            params["price"] = str(price)
            params["timeInForce"] = "GTC"

        try:
            response = self.session.place_order(**params)

            if response.get("retCode") == 0:
                order_id = response["result"].get("orderId", "")
                await self.bel.anotar(
                    "BRIDGE", "ORDEN_ENVIADA",
                    f"{side} {qty} {symbol} @{order_type} | ID:{order_id} LINK:{link_id}",
                )
                return OrdenResultado(True, order_id=order_id, link_id=link_id, datos=response["result"])
            else:
                msg = response.get("retMsg", "Error desconocido")
                await self.bel.anotar("BRIDGE", "ORDEN_RECHAZADA", f"{msg} | LINK:{link_id}")
                return OrdenResultado(False, link_id=link_id, mensaje=msg)

        except Exception as e:
            await self.bel.anotar("BRIDGE", "ORDEN_ERROR", f"{str(e)} | LINK:{link_id}")
            return OrdenResultado(False, link_id=link_id, mensaje=str(e))

    async def activar_spot_margen(self, leverage: int = 10) -> OrdenResultado:
        """Enciende spot margen UTA y fija apalancamiento (hasta 10x)."""
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")
        lev = max(2, min(10, int(leverage)))
        try:
            toggle = self.session.spot_margin_trade_toggle_margin_trade(spotMarginMode="1")
            tcode = toggle.get("retCode")
            tmsg = str(toggle.get("retMsg") or "")
            if tcode not in (0, None) and "already" not in tmsg.lower():
                await self.bel.anotar(
                    "BRIDGE", "SPOT_MARGEN_TOGGLE",
                    f"aviso ret={tcode} {tmsg}",
                )
            set_ok = False
            last_msg = ""
            for try_lev in (lev, 5, 2):
                try:
                    r = self.session.spot_margin_trade_set_leverage(leverage=str(try_lev))
                    if r.get("retCode") == 0:
                        set_ok = True
                        lev = try_lev
                        break
                    last_msg = str(r.get("retMsg") or r)
                except Exception as e:
                    last_msg = str(e)
            if set_ok:
                await self.bel.anotar(
                    "BRIDGE", "SPOT_MARGEN_ON",
                    f"Spot margen activo · leverage {lev}x",
                )
                return OrdenResultado(True, mensaje=f"spot_margen {lev}x")
            await self.bel.anotar(
                "BRIDGE", "SPOT_MARGEN_LEV_FALLIDO",
                f"No se fijó leverage: {last_msg}",
            )
            # Toggle pudo quedar on; seguimos con isLeverage en órdenes
            return OrdenResultado(False, mensaje=last_msg or "leverage fallido")
        except Exception as e:
            await self.bel.anotar("BRIDGE", "SPOT_MARGEN_ERROR", str(e))
            return OrdenResultado(False, mensaje=str(e))

    async def set_leverage(self, symbol, leverage, category="linear"):
        """Fija apalancamiento en Bybit V5 (/v5/position/set-leverage)."""
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")

        lev = str(int(leverage))
        try:
            response = self.session.set_leverage(
                category=category,
                symbol=symbol,
                buyLeverage=lev,
                sellLeverage=lev,
            )
            if response.get("retCode") == 0:
                return OrdenResultado(True, mensaje="OK", datos=response.get("result", {}))

            msg = response.get("retMsg", "Error desconocido")
            if "leverage not modified" in msg.lower():
                return OrdenResultado(True, mensaje=msg, datos=response.get("result", {}))
            await self.bel.anotar("BRIDGE", "LEVERAGE_RECHAZADO", f"{symbol} {lev}x: {msg}")
            return OrdenResultado(False, mensaje=msg)
        except Exception as e:
            err = str(e)
            if "leverage not modified" in err.lower():
                return OrdenResultado(True, mensaje=err)
            await self.bel.anotar("BRIDGE", "LEVERAGE_ERROR", f"{symbol} {lev}x: {err}")
            return OrdenResultado(False, mensaje=err)

    async def cancel_order(self, symbol, order_id=None, link_id=None, category="linear"):
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
            msg = response.get("retMsg", "Error desconocido")
            await self.bel.anotar("BRIDGE", "CANCEL_RECHAZADA", f"{msg} | {order_id or link_id}")
            return OrdenResultado(False, mensaje=msg)
        except Exception as e:
            await self.bel.anotar("BRIDGE", "CANCEL_ERROR", f"{str(e)}")
            return OrdenResultado(False, mensaje=str(e))

    async def amend_order(self, symbol, order_id=None, link_id=None,
                          new_qty=None, new_price=None, category="linear"):
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
                await self.bel.anotar("BRIDGE", "ORDEN_MODIFICADA", f"ID:{order_id or link_id}")
                return OrdenResultado(True, order_id=order_id or "", link_id=link_id or "", datos=response.get("result", {}))
            msg = response.get("retMsg", "Error desconocido")
            return OrdenResultado(False, mensaje=msg)
        except Exception as e:
            return OrdenResultado(False, mensaje=str(e))

    async def esperar_fill(self, symbol, order_id=None, link_id=None,
                           timeout_s=60, intervalo_s=2, category="linear"):
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
                    for orden in response["result"].get("list", []):
                        oid = orden.get("orderId", "")
                        olid = orden.get("orderLinkId", "")
                        if (order_id and oid == order_id) or (link_id and olid == link_id):
                            status = orden.get("orderStatus", "")
                            if status == "Filled":
                                avg_price = float(orden.get("avgPrice", 0) or 0)
                                cum_qty = float(orden.get("cumExecQty", 0) or 0)
                                try:
                                    cum_fee = float(orden.get("cumExecFee") or 0)
                                except (TypeError, ValueError):
                                    cum_fee = 0.0
                                await self.bel.anotar(
                                    "BRIDGE", "FILL_CONFIRMADO",
                                    f"{symbol} {cum_qty}@{avg_price} fee={cum_fee}",
                                )
                                return OrdenResultado(
                                    True, order_id=oid, link_id=olid,
                                    datos={
                                        "avgPrice": avg_price,
                                        "cumExecQty": cum_qty,
                                        "cumExecFee": cum_fee,
                                        "orderStatus": status,
                                    },
                                )
                            elif status in ("Cancelled", "Rejected", "Deactivated"):
                                return OrdenResultado(False, order_id=oid, link_id=olid, mensaje=f"Orden {status}")
            except Exception as e:
                await self.bel.anotar("BRIDGE", "FILL_POLL_ERROR", str(e))
            await asyncio.sleep(intervalo_s)

        await self.bel.anotar("BRIDGE", "FILL_TIMEOUT", f"Timeout {timeout_s}s para {order_id or link_id}")
        return OrdenResultado(False, mensaje=f"Timeout {timeout_s}s sin fill")

    async def hilo_sincronizacion_nav(self):
        if not self.session:
            return

        while True:
            try:
                response = self.session.get_wallet_balance(accountType="UNIFIED")
                if response["retCode"] == 0:
                    data = response["result"]["list"][0]
                    nav_total = float(data.get("totalEquity", 0.0) or 0.0)
                    disponible = float(data.get("totalAvailableBalance", 0.0) or 0.0)
                    margen_ocupado = (
                        ((nav_total - disponible) / nav_total * 100) if nav_total > 0 else 0.0
                    )
                    maint_raw = data.get("totalMaintenanceMargin", "")
                    mm_rate_raw = data.get("accountMMRate", "")
                    total_maint = float(maint_raw) if maint_raw not in ("", None) else None
                    account_mm_rate = float(mm_rate_raw) if mm_rate_raw not in ("", None) else None

                    posiciones = None
                    if getattr(config, "TUSK_TESORERIA_ACTIVA", True) and getattr(
                        config, "TUSK_TESORERIA_FETCH_POS", True
                    ):
                        posiciones = []
                        try:
                            for category, settle in (("linear", "USDT"), ("inverse", None)):
                                kwargs = {"category": category}
                                if settle:
                                    kwargs["settleCoin"] = settle
                                resp = self.session.get_positions(**kwargs)
                                if resp.get("retCode") == 0:
                                    for row in resp.get("result", {}).get("list", []) or []:
                                        row = dict(row)
                                        row["_category"] = category
                                        posiciones.append(row)
                        except Exception as e:
                            await self.bel.anotar(
                                "TUSK", "TESORERIA_POS_ERR", str(e)[:160],
                            )

                    await self.tusk.actualizar_nav_real(
                        nav_total,
                        margen_ocupado,
                        total_maintenance_margin=total_maint,
                        account_mm_rate=account_mm_rate,
                        disponible_uta=disponible,
                        wallet_account=data,
                        posiciones=posiciones,
                    )
                    self._nav_errores_consecutivos = 0
                else:
                    await self.bel.anotar("BRIDGE", "NAV_ERROR_API", response.get("retMsg", "?"))
                    self._nav_errores_consecutivos += 1
            except Exception as e:
                self._nav_errores_consecutivos += 1
                await self.bel.anotar("BRIDGE", "NAV_EXCEPCIÓN", f"Error #{self._nav_errores_consecutivos}: {str(e)}")

            espera = min(30 * (2 ** self._nav_errores_consecutivos), self._NAV_BACKOFF_MAX)
            if self._nav_errores_consecutivos == 0:
                espera = 30
            await asyncio.sleep(espera)

    async def hilo_sentidos_extra(self):
        """Ojos REST: spread producto, alpha, convert — complemento al WS principal."""
        from core.sentidos_extra import SentidosExtraPoller

        poller = SentidosExtraPoller(self.tank, self.bel, session=self.session)
        await asyncio.gather(
            poller.run(),
            poller.run_alpha(),
            poller.run_convert(),
            poller.run_convert_quotes(),
        )
