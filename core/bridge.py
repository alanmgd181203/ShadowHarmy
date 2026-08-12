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


def _base_de_symbol(sym: str) -> str:
    s = str(sym or "").upper()
    for suf in ("USDT", "USDC", "USD"):
        if s.endswith(suf) and len(s) > len(suf):
            return s[: -len(suf)]
    return s


def _filtrar_tuples_por_bases(tuples: list[tuple[str, str]], bases: list[str]) -> list[tuple[str, str]]:
    if not bases:
        return tuples
    allow = {str(b).upper() for b in bases if b}
    return [(sym, frente) for sym, frente in tuples if _base_de_symbol(sym) in allow]


def _feeds_completos():
    """Ojos mainnet: spot + perps + futuros dated Bybit (sharded)."""
    spot_tuples = _pares_a_tuples(getattr(config, "SPOT_ALL_PARES", []))
    linear_tuples = _pares_a_tuples(
        getattr(config, "LINEAR_PERP_PARES", []) + getattr(config, "LINEAR_FUTURES_PARES", [])
    )
    inverse_tuples = _pares_a_tuples(
        getattr(config, "INVERSE_PERP_PARES", []) + getattr(config, "INVERSE_FUTURES_PARES", [])
    )

    bases = list(getattr(config, "BRIDGE_WS_BASES", None) or [])
    if bases:
        spot_tuples = _filtrar_tuples_por_bases(spot_tuples, bases)
        linear_tuples = _filtrar_tuples_por_bases(linear_tuples, bases)
        inverse_tuples = _filtrar_tuples_por_bases(inverse_tuples, bases)

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
            recv = int(getattr(config, "BYBIT_RECV_WINDOW_MS", 60000) or 60000)
            try:
                self.session = HTTP(
                    testnet=False,  # Mundo A abolido — solo mainnet
                    api_key=api_key,
                    api_secret=api_secret,
                    recv_window=recv,
                )
            except TypeError:
                # pybit antiguo sin recv_window en ctor
                self.session = HTTP(
                    testnet=False,
                    api_key=api_key,
                    api_secret=api_secret,
                )
                try:
                    self.session.recv_window = recv
                except Exception:
                    pass

    # ================================================================
    # OJOS — WebSocket público (precios + muros mainnet)
    # ================================================================

    async def conectar(self):
        """Refresca trinidad si stale, reconstruye feeds y lanza WS."""
        from core import trinidad

        await trinidad.refrescar_si_stale()
        trinidad.inicializar_config(config)
        self.feeds = _feeds_completos()
        bases = list(getattr(config, "BRIDGE_WS_BASES", None) or [])
        books_on = bool(getattr(config, "BRIDGE_WS_SUBSCRIBE_BOOKS", True))
        # Expandir solo frentes que vamos a escuchar (menos RAM en Tank).
        if bases:
            frentes = [
                f for f in (getattr(config, "FRENTES_TANK", None) or [])
                if any(f.startswith(f"{b}USD") or f.startswith(f"{b}USDT") or f.startswith(f"{b}USDC") for b in bases)
            ]
            if not frentes:
                frentes = list(getattr(config, "FRENTES_TANK", None) or [])
        else:
            frentes = list(getattr(config, "FRENTES_TANK", None) or [])
        self.tank.expandir_frentes(frentes)
        nspot = len(getattr(config, "FRENTES_SPOT_ALL", []))
        nlin = len(getattr(config, "FRENTES_LINEAR_PERP", []))
        nlinf = len(getattr(config, "FRENTES_LINEAR_FUTURES", []))
        ninv = len(getattr(config, "FRENTES_INVERSE_PERP", []))
        ninvf = len(getattr(config, "FRENTES_INVERSE_FUTURES", []))
        nshards = sum(1 for f in self.feeds if f.get("label"))
        n_tick = sum(len(f.get("tickers") or []) for f in self.feeds)
        modo = "estrecho" if bases or not books_on else "completo"
        await self.bel.anotar(
            "BRIDGE", "TRINIDAD",
            f"Sentidos[{modo}]: catalog {nlin}+{nlinf} lin | {ninv}+{ninvf} inv | {nspot} spot · "
            f"WS {nshards} shards · tickers={n_tick} · books={'ON' if books_on else 'OFF'}"
            + (f" · bases={','.join(bases)}" if bases else ""),
        )

        # Arranque escalonado: con VIP/túnel, abrir 11 WS a la vez agota el handshake.
        stagger = float(getattr(config, "BRIDGE_WS_STAGGER_S", 0.45) or 0.0)
        tareas = [
            self._loop_feed(feed, delay_s=i * stagger)
            for i, feed in enumerate(self.feeds)
        ]
        await asyncio.gather(*tareas)

    async def _loop_feed(self, feed, *, delay_s: float = 0.0):
        if delay_s > 0:
            await asyncio.sleep(delay_s)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        args = []
        for sym, _ in feed.get("tickers", []):
            args.append(f"tickers.{sym}")
        # Muros orderbook: pesados en RAM/red. Ritiales estrechos (Igris sim / lap) pueden apagarlos.
        if getattr(config, "BRIDGE_WS_SUBSCRIBE_BOOKS", True):
            book_bases = [
                str(b).upper()
                for b in (getattr(config, "BRIDGE_WS_BOOKS_BASES", None) or [])
                if b
            ]
            for sym, _ in feed.get("books", []):
                if book_bases:
                    # sym tipo ETHUSDT / ETHUSD — base = letras iniciales
                    base = "".join(ch for ch in str(sym) if ch.isalpha())
                    # quitar quote típico al final
                    for q in ("USDT", "USDC", "USD"):
                        if base.endswith(q) and len(base) > len(q):
                            base = base[: -len(q)]
                            break
                    if base.upper() not in book_bases:
                        continue
                args.append(f"orderbook.50.{sym}")

        open_timeout = float(getattr(config, "BRIDGE_WS_OPEN_TIMEOUT_S", 45) or 45)
        backoff_s = float(getattr(config, "BRIDGE_WS_RECONNECT_S", 5) or 5)
        backoff_max = float(getattr(config, "BRIDGE_WS_RECONNECT_MAX_S", 30) or 30)
        sleep_s = backoff_s

        while True:
            # True solo si el socket abrió y estuvimos dentro del with (sesión viva).
            # Handshake fallido → NO vaciar libros (conserva REST/muleta y fotos previas).
            session_live = False
            try:
                connect_kwargs = dict(
                    ssl=ssl_context,
                    ping_interval=20,
                    open_timeout=open_timeout,
                )
                # Preferir IPv4: en algunas redes/laps el handshake IPv6 a CloudFront muere.
                if getattr(config, "BRIDGE_WS_FORCE_IPV4", True):
                    import socket
                    connect_kwargs["family"] = socket.AF_INET
                async with websockets.connect(
                    feed["url"],
                    **connect_kwargs,
                ) as websocket:
                    session_live = True
                    sleep_s = backoff_s
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
                err = str(e)
                await self.bel.anotar("BRIDGE", "RECONEXIÓN", f"{label}: {err}")
                # Doctrina ojos: solo invalidar si hubo sesión WS viva y se cayó.
                # Handshake timeout / fallo al abrir ≠ foto zombi de este feed.
                if session_live and bool(
                    getattr(config, "BRIDGE_WS_INVALIDAR_ON_DROP", True)
                ):
                    try:
                        from core import igris_ojos as ojos

                        frentes = ojos.frentes_de_feed(feed)
                        n = ojos.invalidar_frentes_tank(self.tank, frentes)
                        await self.bel.anotar(
                            "BRIDGE", "LIBROS_INVALIDADOS",
                            f"{label}: frentes_feed≈{n}/{len(frentes)} · "
                            f"esperando snapshot WS (no wipe global)",
                        )
                    except Exception as e2:
                        await self.bel.anotar(
                            "BRIDGE", "LIBROS_INVALIDADOS", f"aviso: {e2}"
                        )
                else:
                    await self.bel.anotar(
                        "BRIDGE", "RECONEXIÓN_SIN_WIPE",
                        f"{label}: handshake/no-live · libros intactos · "
                        f"reintento {sleep_s:.0f}s",
                    )
                await asyncio.sleep(sleep_s)
                sleep_s = min(sleep_s * 1.5, backoff_max)

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
                        # Sin snapshot (ts=0 post-invalidar): Nodo ignora delta
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
    # MANOS — Órdenes (mainnet; sim = no bridge real)
    # ================================================================

    def _generar_link_id(self, prefijo="SA"):
        uid = uuid.uuid4().hex[:24]
        return f"{prefijo}-{uid}"

    async def asegurar_modo_hedge(
        self, symbol: str, category: str = "inverse",
    ) -> OrdenResultado:
        """Bybit Both Sides (mode=3) — long y short aislados en el mismo símbolo."""
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")
        try:
            response = await asyncio.to_thread(
                self.session.switch_position_mode,
                category=category,
                symbol=symbol,
                mode=3,
            )
            code = response.get("retCode")
            msg = str(response.get("retMsg") or "")
            # 0 OK · ya hedge / sin cambio suele ser 0 o mensaje "not modified"
            if code == 0 or "not modified" in msg.lower() or "same" in msg.lower():
                await self.bel.anotar(
                    "BRIDGE", "HEDGE_ON",
                    f"{symbol} ({category}) modo bidireccional",
                )
                return OrdenResultado(True, mensaje=msg or "hedge")
            # 110025 / position mode not modified — tratar como OK si ya es hedge
            if code in (110025, 34040) or "110025" in msg:
                await self.bel.anotar(
                    "BRIDGE", "HEDGE_YA",
                    f"{symbol}: {msg}",
                )
                return OrdenResultado(True, mensaje=msg)
            await self.bel.anotar(
                "BRIDGE", "HEDGE_FALLIDO",
                f"{symbol} ret={code} {msg}",
            )
            return OrdenResultado(False, mensaje=msg or f"ret={code}")
        except Exception as e:
            await self.bel.anotar("BRIDGE", "HEDGE_ERROR", str(e))
            return OrdenResultado(False, mensaje=str(e))

    async def place_order(self, symbol, side, qty, order_type="Market",
                          price=None, link_id=None, category="linear", market_unit=None,
                          is_leverage=None, position_idx=None, reduce_only=None):
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

        # Hedge: 1 = Buy/long · 2 = Sell/short. Nunca omitir si el símbolo es bidireccional.
        if position_idx is not None:
            params["positionIdx"] = int(position_idx)

        # Abrir manto / bóveda segregada: reduceOnly=False explícito.
        if reduce_only is not None:
            params["reduceOnly"] = bool(reduce_only)

        if order_type == "Limit" and price is not None:
            params["price"] = str(price)
            params["timeInForce"] = "GTC"

        try:
            response = await asyncio.to_thread(self.session.place_order, **params)

            if response.get("retCode") == 0:
                order_id = response["result"].get("orderId", "")
                extra = ""
                if position_idx is not None:
                    extra += f" idx={position_idx}"
                if reduce_only is False:
                    extra += " reduceOnly=0"
                await self.bel.anotar(
                    "BRIDGE", "ORDEN_ENVIADA",
                    f"{side} {qty} {symbol} @{order_type} | ID:{order_id} LINK:{link_id}{extra}",
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

    def _poll_fill_sync(self, symbol, order_id=None, link_id=None, category="linear"):
        """HTTP sync (llamar vía to_thread): open → history → executions."""
        if not self.session:
            return {"ok": False, "mensaje": "Sin sesión API configurada"}

        base = {"category": category, "symbol": symbol}
        if order_id:
            base["orderId"] = order_id
        elif link_id:
            base["orderLinkId"] = link_id
        else:
            return {"ok": False, "mensaje": "Se requiere orderId o linkId"}

        def _match(orden: dict) -> bool:
            oid = orden.get("orderId", "")
            olid = orden.get("orderLinkId", "")
            return bool(
                (order_id and oid == order_id) or (link_id and olid == link_id)
            )

        def _filled_from_orden(orden: dict) -> dict | None:
            status = str(orden.get("orderStatus") or "")
            cum_qty = float(orden.get("cumExecQty") or 0)
            if status == "Filled" or (
                cum_qty > 0 and status in ("Filled", "PartiallyFilledCanceled")
            ):
                try:
                    cum_fee = float(orden.get("cumExecFee") or 0)
                except (TypeError, ValueError):
                    cum_fee = 0.0
                return {
                    "ok": True,
                    "order_id": orden.get("orderId", "") or (order_id or ""),
                    "link_id": orden.get("orderLinkId", "") or (link_id or ""),
                    "avgPrice": float(orden.get("avgPrice", 0) or 0),
                    "cumExecQty": cum_qty,
                    "cumExecFee": cum_fee,
                    "orderStatus": status or "Filled",
                }
            if status in ("Cancelled", "Rejected", "Deactivated") and cum_qty <= 0:
                return {
                    "ok": False,
                    "order_id": orden.get("orderId", ""),
                    "link_id": orden.get("orderLinkId", ""),
                    "mensaje": f"Orden {status}",
                    "terminal": True,
                }
            return None

        # 1) open / realtime (UTA a veces deja fills recientes aquí)
        try:
            r = self.session.get_open_orders(**base)
            if r.get("retCode") == 0:
                for orden in (r.get("result") or {}).get("list") or []:
                    if not _match(orden):
                        continue
                    hit = _filled_from_orden(orden)
                    if hit is not None:
                        return hit
        except Exception as e:
            return {"ok": False, "mensaje": f"open_orders: {e}", "soft": True}

        # 2) order history
        try:
            r = self.session.get_order_history(**base)
            if r.get("retCode") == 0:
                for orden in (r.get("result") or {}).get("list") or []:
                    if not _match(orden):
                        continue
                    hit = _filled_from_orden(orden)
                    if hit is not None:
                        return hit
            else:
                return {
                    "ok": False,
                    "mensaje": f"history ret={r.get('retCode')} {r.get('retMsg')}",
                    "soft": True,
                }
        except Exception as e:
            return {"ok": False, "mensaje": f"history: {e}", "soft": True}

        # 3) executions — Market a menudo aparece aquí antes que en history
        try:
            ex_params = {"category": category, "symbol": symbol, "limit": 20}
            if order_id:
                ex_params["orderId"] = order_id
            r = self.session.get_executions(**ex_params)
            if r.get("retCode") == 0:
                rows = [
                    x for x in ((r.get("result") or {}).get("list") or [])
                    if (order_id and x.get("orderId") == order_id)
                    or (link_id and x.get("orderLinkId") == link_id)
                ]
                if rows:
                    qty = 0.0
                    notional = 0.0
                    fee = 0.0
                    for x in rows:
                        q = float(x.get("execQty") or 0)
                        px = float(x.get("execPrice") or 0)
                        qty += q
                        notional += q * px
                        try:
                            fee += float(x.get("execFee") or 0)
                        except (TypeError, ValueError):
                            pass
                    if qty > 0:
                        return {
                            "ok": True,
                            "order_id": order_id or "",
                            "link_id": link_id or "",
                            "avgPrice": (notional / qty) if qty else 0.0,
                            "cumExecQty": qty,
                            "cumExecFee": fee,
                            "orderStatus": "Filled",
                            "via": "executions",
                        }
        except Exception as e:
            return {"ok": False, "mensaje": f"executions: {e}", "soft": True}

        return {"ok": False, "mensaje": "sin_fill_aun", "soft": True}

    async def esperar_fill(self, symbol, order_id=None, link_id=None,
                           timeout_s=60, intervalo_s=1.0, category="linear"):
        if not self.session:
            return OrdenResultado(False, mensaje="Sin sesión API configurada")

        # HTTP fuera del loop: si bloquea aquí, los ojos (WS) se congelan.
        inicio = time.time()
        ultimo_msg = ""
        while (time.time() - inicio) < timeout_s:
            try:
                pack = await asyncio.to_thread(
                    self._poll_fill_sync, symbol, order_id, link_id, category,
                )
            except Exception as e:
                await self.bel.anotar("BRIDGE", "FILL_POLL_ERROR", str(e))
                await asyncio.sleep(intervalo_s)
                continue

            if pack.get("ok"):
                oid = pack.get("order_id") or (order_id or "")
                olid = pack.get("link_id") or (link_id or "")
                avg_price = float(pack.get("avgPrice") or 0)
                cum_qty = float(pack.get("cumExecQty") or 0)
                cum_fee = float(pack.get("cumExecFee") or 0)
                via = pack.get("via") or "order"
                await self.bel.anotar(
                    "BRIDGE", "FILL_CONFIRMADO",
                    f"{symbol} {cum_qty}@{avg_price} fee={cum_fee}"
                    + (f" via={via}" if via != "order" else ""),
                )
                return OrdenResultado(
                    True, order_id=oid, link_id=olid,
                    datos={
                        "avgPrice": avg_price,
                        "cumExecQty": cum_qty,
                        "cumExecFee": cum_fee,
                        "orderStatus": pack.get("orderStatus") or "Filled",
                    },
                )
            if pack.get("terminal"):
                return OrdenResultado(
                    False,
                    order_id=pack.get("order_id") or "",
                    link_id=pack.get("link_id") or "",
                    mensaje=str(pack.get("mensaje") or "Orden terminal"),
                )
            ultimo_msg = str(pack.get("mensaje") or "")
            if ultimo_msg and "sin_fill" not in ultimo_msg:
                await self.bel.anotar("BRIDGE", "FILL_POLL_ERROR", ultimo_msg[:180])
            await asyncio.sleep(intervalo_s)

        await self.bel.anotar("BRIDGE", "FILL_TIMEOUT", f"Timeout {timeout_s}s para {order_id or link_id}")
        return OrdenResultado(False, mensaje=f"Timeout {timeout_s}s sin fill")

    async def hilo_sincronizacion_nav(self):
        if not self.session:
            return

        while True:
            try:
                # HTTP sync de pybit NO debe correr en el event loop: bloquea handshakes WS (ojos CONGELADOS).
                pack = await asyncio.to_thread(self._fetch_nav_pack_sync)
                if pack.get("error"):
                    self._nav_errores_consecutivos += 1
                    await self.bel.anotar(
                        "BRIDGE", "NAV_EXCEPCIÓN",
                        f"Error #{self._nav_errores_consecutivos}: {pack['error']}",
                    )
                elif pack.get("retCode") == 0:
                    data = pack["account"]
                    nav_total = float(data.get("totalEquity", 0.0) or 0.0)
                    disponible = float(data.get("totalAvailableBalance", 0.0) or 0.0)
                    margen_ocupado = (
                        ((nav_total - disponible) / nav_total * 100) if nav_total > 0 else 0.0
                    )
                    maint_raw = data.get("totalMaintenanceMargin", "")
                    mm_rate_raw = data.get("accountMMRate", "")
                    total_maint = float(maint_raw) if maint_raw not in ("", None) else None
                    account_mm_rate = float(mm_rate_raw) if mm_rate_raw not in ("", None) else None

                    if pack.get("pos_err"):
                        await self.bel.anotar(
                            "TUSK", "TESORERIA_POS_ERR", str(pack["pos_err"])[:160],
                        )

                    await self.tusk.actualizar_nav_real(
                        nav_total,
                        margen_ocupado,
                        total_maintenance_margin=total_maint,
                        account_mm_rate=account_mm_rate,
                        disponible_uta=disponible,
                        wallet_account=data,
                        posiciones=pack.get("posiciones"),
                    )
                    self._nav_errores_consecutivos = 0
                else:
                    await self.bel.anotar("BRIDGE", "NAV_ERROR_API", pack.get("retMsg", "?"))
                    self._nav_errores_consecutivos += 1
            except Exception as e:
                self._nav_errores_consecutivos += 1
                await self.bel.anotar(
                    "BRIDGE", "NAV_EXCEPCIÓN",
                    f"Error #{self._nav_errores_consecutivos}: {str(e)}",
                )

            espera = min(30 * (2 ** self._nav_errores_consecutivos), self._NAV_BACKOFF_MAX)
            if self._nav_errores_consecutivos == 0:
                espera = 30
            await asyncio.sleep(espera)

    def _fetch_nav_pack_sync(self) -> dict:
        """Solo hilo worker: wallet + posiciones. No tocar Tank/Bellion aquí."""
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED")
        except Exception as e:
            return {"error": str(e)}
        if response.get("retCode") != 0:
            return {
                "retCode": response.get("retCode"),
                "retMsg": response.get("retMsg", "?"),
            }
        data = response["result"]["list"][0]
        posiciones = None
        pos_err = None
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
                pos_err = str(e)[:160]
        return {
            "retCode": 0,
            "account": data,
            "posiciones": posiciones,
            "pos_err": pos_err,
        }

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
