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
  if paso <= 0:
    return val
  n = val / paso
  if modo == "ceil":
    n = math.ceil(n - 1e-12)
  else:
    n = math.floor(n + 1e-12)
  return max(paso, n * paso) if n > 0 else paso


def cuantizar_precio(precio: float, frente: str) -> float:
  tick = filtros_lote(frente).get("tickSz") or 0.01
  return _redondear_paso(float(precio or 0), float(tick), "floor")


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
) -> dict[str, Any]:
  """Floor en lotSz: coloca fracción inferior; deuda = objetivo − notional."""
  f = filtros_lote(frente)
  lot = float(f.get("lotSz") or 1.0)
  min_sz = float(f.get("minSz") or lot)
  ct = float(f.get("ctVal") or 1.0)
  px = float(precio or 0)
  min_usd = float(f.get("min_usd_est") or 1.0)
  objetivo = max(0.0, float(masa_objetivo or 0))

  if px <= 0 or objetivo <= 0:
    return {"ok": False, "motivo": "masa_o_precio_cero", "qty": 0.0, "deuda_usd": objetivo}

  bruto = masa_a_contratos(objetivo, px, frente)
  qty = _redondear_paso(bruto, lot, "floor")
  if qty > 0 and qty < min_sz:
    qty = 0.0
  notional = qty * ct * px if qty > 0 else 0.0
  deuda = max(0.0, objetivo - notional)

  if qty <= 0:
    return {
      "ok": False,
      "motivo": "qty_cero_deuda",
      "qty": 0.0,
      "notional_usd": 0.0,
      "deuda_usd": round(deuda, 6),
      "instId": f.get("instId"),
      "paso_usd": round(paso_notional_usd(px, frente), 6),
    }
  if notional + 1e-9 < min_usd:
    return {
      "ok": False,
      "motivo": "bajo_min_usd",
      "qty": qty,
      "notional_usd": round(notional, 6),
      "deuda_usd": round(deuda, 6),
      "instId": f.get("instId"),
      "min_usd": min_usd,
      "paso_usd": round(paso_notional_usd(px, frente), 6),
    }
  return {
    "ok": True,
    "qty": qty,
    "notional_usd": round(notional, 6),
    "deuda_usd": round(deuda, 6),
    "instId": f.get("instId"),
    "paso_usd": round(paso_notional_usd(px, frente), 6),
  }
