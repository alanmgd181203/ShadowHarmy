"""Fachada de lotes Beru — OKX por defecto; Bybit solo si BERU_MAR=bybit."""
from __future__ import annotations

from typing import Any, Literal

from core import beru_mar
from core import lote_bybit
from core import lote_okx

ModoRedondeo = Literal["floor", "ceil"]


def cuantizar_precio(precio: float, frente: str) -> float:
  if beru_mar.es_okx():
    return lote_okx.cuantizar_precio(precio, frente)
  return lote_bybit.cuantizar_precio(precio, frente)


def asegurar_qty_min_notional(
  qty: float,
  precio: float,
  frente: str,
  *,
  mode: ModoRedondeo = "ceil",
) -> dict[str, Any]:
  if beru_mar.es_okx():
    return lote_okx.asegurar_qty_min_notional(qty, precio, frente, mode=mode)
  return lote_bybit.asegurar_qty_min_notional(qty, precio, frente, mode=mode)


def masa_a_qty(masa_usd: float, precio: float, frente: str, *, mode: ModoRedondeo = "ceil") -> dict[str, Any]:
  if beru_mar.es_okx():
    bruto = lote_okx.masa_a_contratos(masa_usd, precio, frente)
  else:
    bruto = float(masa_usd or 0) / float(precio or 1.0)
  return asegurar_qty_min_notional(bruto, precio, frente, mode=mode)


def masa_a_qty_con_deuda(
  masa_doctrinal: float,
  precio: float,
  frente: str,
  *,
  pendiente: float = 0.0,
  usar_floor: bool = False,
  ticket_min_si_cero: bool = False,
) -> dict[str, Any]:
  """Piedra: floor + deuda. Legacy: ceil + piso exchange."""
  objetivo = max(0.0, float(masa_doctrinal or 0) + float(pendiente or 0))
  if usar_floor and beru_mar.es_okx():
    return lote_okx.masa_a_qty_piso_deuda(
      objetivo, precio, frente, ticket_min_si_cero=ticket_min_si_cero,
    )
  pack = masa_a_qty(objetivo, precio, frente, mode="ceil")
  if pack.get("ok"):
    pack = dict(pack)
    pack["deuda_usd"] = max(
      0.0,
      objetivo - float(pack.get("notional_usd") or 0),
    )
  return pack
