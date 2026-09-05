"""Puente OKX — ojos WS + manos REST para Beru rango (SWAP USDT)."""
from __future__ import annotations

import asyncio
import json
import re
import ssl
import time
import uuid
import websockets

from core import beru_mar
from core import beru_rango_ojos
from core import okx_rest
from core.bridge import OrdenResultado
import core.config as config


def _okx_client_id(cl: str) -> str:
  """OKX clOrdId / algoClOrdId: alfanumérico, máx 32."""
  raw = re.sub(r"[^A-Za-z0-9]", "", str(cl or ""))
  return (raw[:32] if raw else f"BRG{uuid.uuid4().hex[:12]}")


def _map_okx_position_row(row: dict) -> dict | None:
  """Fila OKX SWAP → forma Bybit que Tusk / telemetría ya entienden."""
  try:
    pos_ct = float(row.get("pos") or 0)
  except (TypeError, ValueError):
    pos_ct = 0.0
  if abs(pos_ct) < 1e-12:
    return None
  inst = str(row.get("instId") or "")
  if not inst.endswith("-USDT-SWAP"):
    return None
  act = beru_mar.inst_id_a_activo(inst)
  symbol = f"{act}USDT"
  pos_side = str(row.get("posSide") or "net").lower()
  if pos_side == "short":
    side = "Sell"
    size_ct = abs(pos_ct)
  elif pos_side == "long":
    side = "Buy"
    size_ct = abs(pos_ct)
  elif pos_ct > 0:
    side = "Buy"
    size_ct = pos_ct
  else:
    side = "Sell"
    size_ct = abs(pos_ct)
  from core import lote_okx

  ct = float(lote_okx.filtros_lote(f"{act}USDT_LINEAL").get("ctVal") or 1.0)
  size_base = size_ct * ct
  avg = float(row.get("avgPx") or row.get("markPx") or 0)
  mark = float(row.get("markPx") or avg or 0)
  return {
    "symbol": symbol,
    "side": side,
    "size": str(size_base),
    "avgPrice": str(avg or mark or 0),
    "markPrice": str(mark or avg or 0),
    "leverage": str(row.get("lever") or ""),
    "positionIM": row.get("imr") or row.get("margin") or "",
    "positionValue": str(size_base * avg) if avg > 0 else "",
    "category": "linear",
    "_category": "linear",
  }


def _map_algo_status(state: str) -> str:
  s = str(state or "").lower()
  if s in ("live", "pause"):
    return "Untriggered"
  if s in ("effective", "filled"):
    return "Filled"
  if s in ("canceled", "cancelled"):
    return "Cancelled"
  if s in ("order_failed", "failed"):
    return "Rejected"
  return state or "Unknown"


class OkxBridge:
  """API compatible con el altar Beru (place/amend/cancel/get + WS tickers)."""

  def __init__(self, tank_cluster, tusk, bellion, *, ws_bases=None):
    self.tank = tank_cluster
    self.tusk = tusk
    self.bel = bellion
    if ws_bases is not None:
      self.ws_bases = [str(b).strip().upper() for b in ws_bases if str(b).strip()]
    else:
      self.ws_bases = None
    # Tusk reconciliar mira ``bridge.session`` truthy (get_positions sync).
    self.session = self if okx_rest.credenciales_ok() else None
    self._nav_errores_consecutivos = 0

  def get_positions(self, **kwargs) -> dict:
    """Compat Bybit → OKX SWAP USDT (Tusk / telemetría). Inverse: lista vacía."""
    cat = str(kwargs.get("category") or "linear").lower()
    if cat == "inverse":
      return {"retCode": 0, "retMsg": "OK", "result": {"list": []}}
    if not okx_rest.credenciales_ok():
      return {"retCode": 1, "retMsg": "Sin credenciales OKX", "result": {"list": []}}
    params: dict[str, str] = {"instType": "SWAP"}
    sym = str(kwargs.get("symbol") or "").upper().strip()
    if sym:
      act = sym[:-4] if sym.endswith("USDT") else sym
      params["instId"] = beru_mar.activo_a_inst_id(act)
    try:
      rows = okx_rest.get_private("/api/v5/account/positions", params=params)
    except okx_rest.OkxRestError as exc:
      return {"retCode": 1, "retMsg": str(exc), "result": {"list": []}}
    out: list[dict] = []
    for row in list(rows or []):
      if not isinstance(row, dict):
        continue
      mapped = _map_okx_position_row(row)
      if mapped:
        out.append(mapped)
    return {"retCode": 0, "retMsg": "OK", "result": {"list": out}}

  def get_wallet_balance(self, accountType: str = "UNIFIED") -> dict:
    """Compat mínima Bybit NAV — equity USDT desde balance OKX."""
    _ = accountType
    if not okx_rest.credenciales_ok():
      return {"retCode": 1, "retMsg": "Sin credenciales OKX", "result": {"list": []}}
    try:
      data = okx_rest.get_private("/api/v5/account/balance")
    except okx_rest.OkxRestError as exc:
      return {"retCode": 1, "retMsg": str(exc), "result": {"list": []}}
    rows = list(data or [])
    row0 = rows[0] if rows else {}
    eq = 0.0
    for det in row0.get("details") or []:
      if str(det.get("ccy") or "").upper() == "USDT":
        try:
          eq = float(det.get("eq") or det.get("cashBal") or 0)
        except (TypeError, ValueError):
          eq = 0.0
        break
    if eq <= 0:
      try:
        eq = float(row0.get("totalEq") or 0)
      except (TypeError, ValueError):
        eq = 0.0
    return {
      "retCode": 0,
      "retMsg": "OK",
      "result": {
        "list": [
          {
            "totalEquity": str(eq),
            "coin": [{"coin": "USDT", "equity": str(eq), "walletBalance": str(eq)}],
          }
        ]
      },
    }

  def _inst_ids(self) -> list[str]:
    bases = list(self.ws_bases or [])
    if not bases:
      act = str(getattr(config, "BERU_RANGO_ACTIVO", "ETH") or "ETH")
      bases = [act.upper()]
    return [beru_mar.activo_a_inst_id(b) for b in bases]

  async def conectar(self):
    bases = list(self.ws_bases or [])
    frentes = beru_rango_ojos.frentes_lineal_tank(bases)
    self.tank.expandir_frentes(frentes)
    inst_ids = self._inst_ids()
    await self.bel.anotar(
      "OKX_BRIDGE", "OJOS",
      f"WS tickers SWAP · {len(inst_ids)} inst · bases={','.join(bases) or '—'}",
    )
    await self._loop_ws(inst_ids)

  async def _loop_ws(self, inst_ids: list[str]):
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    url = "wss://ws.okx.com:8443/ws/v5/public"
    backoff = 5.0
    args = [{"channel": "tickers", "instId": iid} for iid in inst_ids]
    sub = {"op": "subscribe", "args": args}
    trades_on = bool(getattr(config, "BRIDGE_WS_PUBLIC_TRADES_LINEAR", False))
    if trades_on:
      sub["args"].extend({"channel": "trades", "instId": iid} for iid in inst_ids)

    while True:
      try:
        async with websockets.connect(url, ssl=ssl_ctx, open_timeout=30) as ws:
          await ws.send(json.dumps(sub))
          async for raw in ws:
            try:
              msg = json.loads(raw)
            except json.JSONDecodeError:
              continue
            if msg.get("event") in ("subscribe", "error"):
              if msg.get("event") == "error":
                await self.bel.anotar("OKX_BRIDGE", "WS_ERROR", str(msg))
              continue
            arg = msg.get("arg") or {}
            ch = str(arg.get("channel") or "")
            data = msg.get("data") or []
            if not data:
              continue
            row = data[0] if isinstance(data, list) else data
            inst = str(row.get("instId") or arg.get("instId") or "")
            act = beru_mar.inst_id_a_activo(inst)
            frente = beru_mar.frente_lineal(act)
            if ch == "tickers":
              try:
                px = float(row.get("last") or row.get("lastPx") or 0)
              except (TypeError, ValueError):
                px = 0.0
              if px <= 0:
                try:
                  px = float(row.get("markPx") or row.get("bidPx") or row.get("askPx") or 0)
                except (TypeError, ValueError):
                  px = 0.0
              if px <= 0:
                continue
              lat = 5.0
              for n in getattr(self.tank, "nodos", None) or []:
                try:
                  n.inyectar_verdad_real(frente, px, lat)
                  if str(getattr(n, "estado_foco", "") or "") in ("CONGELADO", "ROJO", ""):
                    n.estado_foco = "AMARILLO"
                except Exception:
                  pass
              if hasattr(self.tank, "registrar_print_lineal"):
                try:
                  self.tank.registrar_print_lineal(frente, px, fuente_ws=True)
                except Exception:
                  pass
              setattr(self.tank, "ts_rio_lineal_ws", time.time())
            elif ch == "trades":
              try:
                px = float(row.get("px") or 0)
              except (TypeError, ValueError):
                px = 0.0
              if px > 0 and hasattr(self.tank, "registrar_print_lineal"):
                try:
                  self.tank.registrar_print_lineal(frente, px, fuente_ws=True)
                except Exception:
                  pass
      except Exception as exc:
        await self.bel.anotar("OKX_BRIDGE", "WS_RECONNECT", str(exc))
        await asyncio.sleep(backoff)

  def _symbol_to_inst(self, symbol: str) -> str:
    s = str(symbol or "").upper()
    if "-USDT-SWAP" in s:
      return s
    act = beru_mar.inst_id_a_activo(s.replace("USDT", "")) if s.endswith("USDT") else s
    return beru_mar.activo_a_inst_id(act)

  async def set_leverage(self, symbol_or_inst: str, leverage: int, category: str = "linear"):
    inst = self._symbol_to_inst(symbol_or_inst)
    lev = str(int(leverage))
    try:
      data = await asyncio.to_thread(
        okx_rest.post_private,
        "/api/v5/account/set-leverage",
        {"instId": inst, "lever": lev, "mgnMode": "cross"},
      )
      _ = data
      return OrdenResultado(True, mensaje="OK")
    except okx_rest.OkxRestError as exc:
      msg = str(exc)
      if "leverage" in msg.lower() and "same" in msg.lower():
        return OrdenResultado(True, mensaje=msg)
      return OrdenResultado(False, mensaje=msg)

  async def place_order(
    self,
    symbol,
    side,
    qty,
    order_type="Market",
    price=None,
    link_id=None,
    category="linear",
    market_unit=None,
    is_leverage=None,
    position_idx=None,
    reduce_only=None,
    trigger_price=None,
    trigger_direction=None,
    trigger_by=None,
    order_filter=None,
    time_in_force=None,
  ):
    if not self.session:
      return OrdenResultado(False, mensaje="Sin credenciales OKX")
    inst = self._symbol_to_inst(symbol)
    cl = _okx_client_id(str(link_id or f"BRG{uuid.uuid4().hex[:12]}"))
    side_okx = "buy" if str(side).lower().startswith("b") else "sell"
    from core import lote_okx

    act = beru_mar.inst_id_a_activo(inst)
    frente = f"{act}USDT_LINEAL"
    sz = lote_okx.sz_okx_str(float(qty or 0), frente)

    try:
      if trigger_price is not None and str(order_filter or "").lower() in ("stoporder", "stop"):
        from core import lote_okx

        act = beru_mar.inst_id_a_activo(inst)
        trig = lote_okx.cuantizar_precio(float(trigger_price), f"{act}USDT_LINEAL")
        body = {
          "instId": inst,
          "tdMode": "cross",
          "side": side_okx,
          "ordType": "trigger",
          "sz": sz,
          "triggerPx": str(trig),
          "orderPx": "-1",
          "triggerPxType": "last",
          "algoClOrdId": cl,
        }
        data = await asyncio.to_thread(okx_rest.post_private, "/api/v5/trade/order-algo", body)
        rows = list(data or [])
        algo_id = str((rows[0] if rows else {}).get("algoId") or "")
        await self.bel.anotar(
          "OKX_BRIDGE", "TRIGGER_ARMADO",
          f"{side_okx} {sz} {inst} @ {trigger_price} | algo:{algo_id} LINK:{cl}",
        )
        return OrdenResultado(True, order_id=algo_id, link_id=cl, datos={"algoId": algo_id, "orderStatus": "Untriggered"})

      body = {
        "instId": inst,
        "tdMode": "cross",
        "side": side_okx,
        "ordType": "market" if str(order_type).lower() == "market" else "limit",
        "sz": sz,
        "clOrdId": cl,
      }
      if body["ordType"] == "limit" and price is not None:
        body["px"] = str(price)
      data = await asyncio.to_thread(okx_rest.post_private, "/api/v5/trade/order", body)
      rows = list(data or [])
      oid = str((rows[0] if rows else {}).get("ordId") or "")
      await self.bel.anotar(
        "OKX_BRIDGE", "ORDEN_ENVIADA",
        f"{side_okx} {sz} {inst} | ID:{oid} LINK:{cl}",
      )
      return OrdenResultado(True, order_id=oid, link_id=cl, datos=rows[0] if rows else {})
    except okx_rest.OkxRestError as exc:
      await self.bel.anotar("OKX_BRIDGE", "ORDEN_RECHAZADA", f"{exc} | LINK:{cl}")
      return OrdenResultado(False, link_id=cl, mensaje=str(exc))

  async def cancel_order(
    self,
    symbol,
    order_id=None,
    link_id=None,
    category="linear",
    order_filter=None,
  ):
    if not self.session:
      return OrdenResultado(False, mensaje="Sin credenciales OKX")
    inst = self._symbol_to_inst(symbol)
    cl = _okx_client_id(str(link_id or ""))
    try:
      if str(order_filter or "").lower() in ("stoporder", "stop") or str(link_id or "").startswith("BRG"):
        body: dict = {"instId": inst}
        if order_id:
          body["algoId"] = str(order_id)
        elif cl:
          body["algoClOrdId"] = cl
        else:
          return OrdenResultado(False, mensaje="Se requiere algoId o linkId")
        await asyncio.to_thread(okx_rest.post_private, "/api/v5/trade/cancel-algos", [body])
        await self.bel.anotar("OKX_BRIDGE", "ALGO_CANCELADA", f"{inst} {order_id or cl}")
        return OrdenResultado(True, order_id=order_id or "", link_id=cl)
      body = {"instId": inst}
      if order_id:
        body["ordId"] = str(order_id)
      elif cl:
        body["clOrdId"] = cl
      else:
        return OrdenResultado(False, mensaje="Se requiere orderId o linkId")
      await asyncio.to_thread(okx_rest.post_private, "/api/v5/trade/cancel-order", body)
      return OrdenResultado(True, order_id=order_id or "", link_id=cl)
    except okx_rest.OkxRestError as exc:
      msg = str(exc)
      if "51400" in msg or "not exist" in msg.lower() or "already" in msg.lower():
        return OrdenResultado(True, mensaje=msg, link_id=cl)
      return OrdenResultado(False, mensaje=msg, link_id=cl)

  async def amend_order(
    self,
    symbol,
    order_id=None,
    link_id=None,
    new_qty=None,
    new_price=None,
    new_trigger_price=None,
    category="linear",
  ):
    if not self.session:
      return OrdenResultado(False, mensaje="Sin credenciales OKX")
    inst = self._symbol_to_inst(symbol)
    cl = _okx_client_id(str(link_id or ""))
    try:
      body: dict = {"instId": inst}
      if order_id:
        body["algoId"] = str(order_id)
      elif cl:
        body["algoClOrdId"] = cl
      else:
        return OrdenResultado(False, mensaje="Se requiere algoId o linkId")
      if new_trigger_price is not None:
        from core import lote_okx

        act = beru_mar.inst_id_a_activo(inst)
        trig = lote_okx.cuantizar_precio(float(new_trigger_price), f"{act}USDT_LINEAL")
        body["newTriggerPx"] = str(trig)
      if new_qty is not None:
        from core import lote_okx

        act = beru_mar.inst_id_a_activo(inst)
        body["newSz"] = lote_okx.sz_okx_str(float(new_qty), f"{act}USDT_LINEAL")
      if new_price is not None:
        body["newPx"] = str(new_price)
      await asyncio.to_thread(okx_rest.post_private, "/api/v5/trade/amend-algos", body)
      return OrdenResultado(True, order_id=order_id or "", link_id=cl)
    except okx_rest.OkxRestError as exc:
      return OrdenResultado(False, mensaje=str(exc), link_id=cl)

  async def get_order_status(
    self,
    symbol,
    *,
    link_id,
    category="linear",
    order_filter=None,
  ):
    if not link_id:
      return OrdenResultado(False, mensaje="Se requiere linkId")
    inst = self._symbol_to_inst(symbol)
    cl = _okx_client_id(str(link_id))
    try:
      if str(order_filter or "").lower() in ("stoporder", "stop") or str(link_id or "").startswith("BRG"):
        data = await asyncio.to_thread(
          okx_rest.get_private,
          "/api/v5/trade/order-algo",
          params={"instId": inst, "algoClOrdId": cl},
        )
        rows = list(data or [])
        if not rows:
          return OrdenResultado(
            False, link_id=cl, mensaje="orden_no_encontrada",
            datos={"not_found": True},
          )
        row = rows[0]
        st = _map_algo_status(str(row.get("state") or ""))
        return OrdenResultado(
          True,
          order_id=str(row.get("algoId") or ""),
          link_id=cl,
          mensaje=st,
          datos={
            "orderStatus": st,
            "triggerPrice": row.get("triggerPx"),
            "algoId": row.get("algoId"),
          },
        )
      data = await asyncio.to_thread(
        okx_rest.get_private,
        "/api/v5/trade/order",
        params={"instId": inst, "clOrdId": cl},
      )
      rows = list(data or [])
      if not rows:
        return OrdenResultado(False, link_id=cl, mensaje="orden_no_encontrada", datos={"not_found": True})
      row = rows[0]
      st = str(row.get("state") or row.get("status") or "")
      return OrdenResultado(
        True, order_id=str(row.get("ordId") or ""), link_id=cl, mensaje=st,
        datos={"orderStatus": st},
      )
    except okx_rest.OkxRestError as exc:
      msg = str(exc)
      not_found = "51400" in msg or "not exist" in msg.lower()
      return OrdenResultado(
        False, link_id=cl, mensaje=msg,
        datos={"not_found": not_found},
      )
