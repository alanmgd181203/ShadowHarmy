"""Lotes OKX SWAP — minSz, lotSz, ctVal desde BD sync."""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from typing import Any, Literal

import core.config as config
from core import beru_mar

ModoRedondeo = Literal["floor", "ceil"]


def _ruta_bd() -> str:
  override = getattr(config, "OKX_PARAMETROS_PATH", None)
  if override:
    return str(override)
  root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  minimos = os.path.join(root, "data", "okx_minimos_orden.json")
  if os.path.exists(minimos):
    return minimos
  return os.path.join(root, "data", "okx_parametros_mercado.json")


@lru_cache(maxsize=1)
def _cargar_bd() -> dict[str, Any]:
  ruta = _ruta_bd()
  if not os.path.exists(ruta):
    return {"activos": {}, "meta": {}}
  try:
    with open(ruta, encoding="utf-8") as f:
      return json.load(f)
  except (OSError, json.JSONDecodeError):
    return {"activos": {}, "meta": {}}


def invalidar_cache_bd() -> None:
  _cargar_bd.cache_clear()


def _f(x: Any, default: float = 0.0) -> float:
  try:
    v = float(x)
  except (TypeError, ValueError):
    return default
  return v if v > 0 else default


def pierna_activo(activo: str) -> dict[str, Any]:
  base = str(activo or "").upper()
  bd = _cargar_bd()
  row = (bd.get("activos") or {}).get(base) or {}
  if row:
    return dict(row)
  return {
    "instId": beru_mar.activo_a_inst_id(base),
    "minSz": 1.0,
    "lotSz": 1.0,
    "ctVal": 1.0,
    "tickSz": 0.01,
    "min_usd_est": float(getattr(config, "MIN_ORDER_USD_DEFAULT", 1.0) or 1.0),
  }


def filtros_lote(frente: str) -> dict[str, Any]:
  base = beru_mar.base_desde_frente(frente)
  p = pierna_activo(base)
  return {
    "instId": p.get("instId") or beru_mar.activo_a_inst_id(base),
    "minSz": _f(p.get("minSz"), 1.0),
    "lotSz": _f(p.get("lotSz"), 1.0),
    "ctVal": _f(p.get("ctVal"), 1.0),
    "tickSz": _f(p.get("tickSz"), 0.01),
    "min_usd_est": _f(p.get("min_usd_est"), float(getattr(config, "MIN_ORDER_USD_DEFAULT", 1.0) or 1.0)),
  }


def _redondear_paso(val: float, paso: float, modo: ModoRedondeo) -> float:
  """Floor verdadero: si no alcanza 1 paso → 0 (nunca inventa un lote mínimo).

  Tumor histórico: ``else paso`` / ``max(paso, …)`` forzaba 1 lotSz aunque el
  notional doctrinal no cubriera ese contrato → mini-orden fantasma + bajo_min.
  """
  if paso <= 0:
    return float(val or 0)
  v = float(val or 0)
  if v <= 0:
    return 0.0
  n = v / paso
  if modo == "ceil":
    n = math.ceil(n - 1e-12)
  else:
    n = math.floor(n + 1e-12)
  if n <= 0:
    return 0.0
  return n * paso


def cuantizar_precio(precio: float, frente: str) -> float:
  tick = filtros_lote(frente).get("tickSz") or 0.01
  return _redondear_paso(float(precio or 0), float(tick), "floor")


def cuantizar_qty(
  qty: float,
  frente: str,
  *,
  modo: ModoRedondeo = "floor",
) -> float:
  """Contratos SWAP en múltiplo de lotSz (sin polvo float)."""
  f = filtros_lote(frente)
  step = float(f.get("lotSz") or 1.0)
  min_q = float(f.get("minSz") or step)
  q = float(qty or 0)
  if q <= 0 or step <= 0:
    return 0.0
  out = _redondear_paso(q, step, modo)
  if out > 0 and out + 1e-12 < min_q:
    if q + 1e-12 >= min_q:
      out = _redondear_paso(min_q, step, "ceil")
    else:
      return 0.0
  dec = max(0, min(12, -int(math.floor(math.log10(step))) if step < 1 else 0))
  return round(out, dec + 2)


def sz_okx_str(qty: float, frente: str) -> str:
  """String OKX sin artefactos float (0.41, no 0.41000000000000003)."""
  q = cuantizar_qty(qty, frente, modo="floor")
  if q <= 0:
    return "0"
  step = float(filtros_lote(frente).get("lotSz") or 1.0)
  if step >= 1 and abs(step - round(step)) < 1e-12:
    return str(int(round(q)))
  dec = max(0, min(12, -int(math.floor(math.log10(step))) if step < 1 else 0))
  s = f"{q:.{dec}f}"
  if "." in s:
    s = s.rstrip("0").rstrip(".")
  return s or "0"


def masa_a_contratos(masa_usd: float, precio: float, frente: str) -> float:
  f = filtros_lote(frente)
  ct = float(f.get("ctVal") or 1.0)
  px = float(precio or 0)
  if px <= 0 or ct <= 0:
    return 0.0
  # notional ≈ sz * ctVal * px
  return float(masa_usd or 0) / (ct * px)


def asegurar_qty_min_notional(
  qty_contratos: float,
  precio: float,
  frente: str,
  *,
  mode: ModoRedondeo = "ceil",
) -> dict[str, Any]:
  f = filtros_lote(frente)
  lot = float(f.get("lotSz") or 1.0)
  min_sz = float(f.get("minSz") or lot)
  ct = float(f.get("ctVal") or 1.0)
  px = float(precio or 0)
  min_usd = float(f.get("min_usd_est") or 1.0)

  qty = _redondear_paso(float(qty_contratos or 0), lot, mode)
  if qty < min_sz:
    qty = _redondear_paso(min_sz, lot, "ceil")

  notional = qty * ct * px if px > 0 else 0.0
  if px > 0 and notional < min_usd:
    need = masa_a_contratos(min_usd, px, frente)
    qty = _redondear_paso(max(qty, need), lot, "ceil")
    notional = qty * ct * px

  if qty <= 0:
    return {"ok": False, "motivo": "qty_cero", "qty": 0.0}
  return {
    "ok": True,
    "qty": qty,
    "notional_usd": round(notional, 6),
    "instId": f.get("instId"),
  }


def paso_notional_usd(precio: float, frente: str) -> float:
  """Notional USD de un paso lotSz (una fracción mínima del par)."""
  f = filtros_lote(frente)
  lot = float(f.get("lotSz") or 1.0)
  ct = float(f.get("ctVal") or 1.0)
  px = float(precio or 0)
  if px <= 0 or lot <= 0:
    return 0.0
  return lot * ct * px


def masa_a_qty_piso_deuda(
  masa_objetivo: float,
  precio: float,
  frente: str,
  *,
  ticket_min_si_cero: bool = False,
) -> dict[str, Any]:
  """Una sola Oz = floor(suma doctrinal completa).

  Cerebro lleva el total ($2,45). Mar recibe solo el piso en contratos.
  Deuda = objetivo − notional (cola en cabeza). Si ni 1 minSz cabe → ok=False
  ``qty_cero_deuda`` (esperar engorde; no inventar mini-orden).

  ``ticket_min_si_cero``: solo al disparar Market cuando la Oz ya tocó y el
  floor sigue en 0 — un contrato minSz (no engorde a pedazos).
  """
  f = filtros_lote(frente)
  lot = float(f.get("lotSz") or 1.0)
  min_sz = float(f.get("minSz") or lot)
  ct = float(f.get("ctVal") or 1.0)
  px = float(precio or 0)
  objetivo = max(0.0, float(masa_objetivo or 0))
  paso_usd = round(paso_notional_usd(px, frente), 6)

  if px <= 0 or objetivo <= 0:
    return {
      "ok": False,
      "motivo": "masa_o_precio_cero",
      "qty": 0.0,
      "notional_usd": 0.0,
      "deuda_usd": round(objetivo, 6),
      "paso_usd": paso_usd,
    }

  bruto = masa_a_contratos(objetivo, px, frente)
  qty = _redondear_paso(bruto, lot, "floor")
  if qty + 1e-12 < min_sz:
    qty = 0.0
  notional = qty * ct * px if qty > 0 else 0.0
  deuda = max(0.0, objetivo - notional)

  if qty <= 0:
    if ticket_min_si_cero and objetivo > 0:
      qty = _redondear_paso(min_sz, lot, "ceil")
      notional = qty * ct * px if qty > 0 else 0.0
      deuda = max(0.0, objetivo - notional)
      if qty > 0:
        return {
          "ok": True,
          "qty": qty,
          "notional_usd": round(notional, 6),
          "deuda_usd": round(deuda, 6),
          "instId": f.get("instId"),
          "paso_usd": paso_usd,
          "ticket_min": True,
        }
    return {
      "ok": False,
      "motivo": "qty_cero_deuda",
      "qty": 0.0,
      "notional_usd": 0.0,
      "deuda_usd": round(objetivo, 6),
      "instId": f.get("instId"),
      "paso_usd": paso_usd,
      "min_usd": float(f.get("min_usd_est") or 0),
    }
  return {
    "ok": True,
    "qty": qty,
    "notional_usd": round(notional, 6),
    "deuda_usd": round(deuda, 6),
    "instId": f.get("instId"),
    "paso_usd": paso_usd,
  }
