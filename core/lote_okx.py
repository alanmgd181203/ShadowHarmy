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


def _ruta_raiz() -> str:
  return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ruta_bd() -> str:
  override = getattr(config, "OKX_PARAMETROS_PATH", None)
  if override:
    return str(override)
  root = _ruta_raiz()
  minimos = os.path.join(root, "data", "okx_minimos_orden.json")
  if os.path.exists(minimos):
    return minimos
  return os.path.join(root, "data", "okx_parametros_mercado.json")


def _ruta_bd_reserva() -> str:
  """Catálogo amplio: rellena Santos que no están en minimos_orden."""
  return os.path.join(_ruta_raiz(), "data", "okx_parametros_mercado.json")


def _leer_json_bd(ruta: str) -> dict[str, Any]:
  if not ruta or not os.path.exists(ruta):
    return {"activos": {}, "meta": {}}
  try:
    with open(ruta, encoding="utf-8") as f:
      data = json.load(f)
  except (OSError, json.JSONDecodeError):
    return {"activos": {}, "meta": {}}
  if not isinstance(data, dict):
    return {"activos": {}, "meta": {}}
  if not isinstance(data.get("activos"), dict):
    data["activos"] = {}
  return data


@lru_cache(maxsize=1)
def _cargar_bd() -> dict[str, Any]:
  """Minimos manda; parametros_mercado completa huecos (NEAR, etc.)."""
  primaria = _leer_json_bd(_ruta_bd())
  reserva_path = _ruta_bd_reserva()
  if os.path.normpath(reserva_path) == os.path.normpath(_ruta_bd()):
    return primaria
  reserva = _leer_json_bd(reserva_path)
  unidos = dict(reserva.get("activos") or {})
  unidos.update(primaria.get("activos") or {})  # minimos pisa
  meta = dict(reserva.get("meta") or {})
  meta.update(primaria.get("meta") or {})
  meta["fuente_lote"] = "minimos+parametros"
  return {"activos": unidos, "meta": meta}


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
  Puerta: sin piso real en BD → ``sin_piso_real``. Si ese contrato mínimo
  supera ``masa_armar_max`` → ``ticket_min_sobre_techo`` (anti-HANMI $196).
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
      # Puerta: sin piso real no inventar minSz=1 (tumor HANMI $196).
      base = ""
      try:
        from core import beru_mar as _bm

        base = _bm.base_desde_frente(frente)
      except Exception:
        base = str(frente or "").replace("USDT_LINEAL", "").upper()
      if base and not floor_completo(base):
        return {
          "ok": False,
          "motivo": "sin_piso_real",
          "qty": 0.0,
          "notional_usd": 0.0,
          "deuda_usd": round(objetivo, 6),
          "instId": f.get("instId"),
          "paso_usd": paso_usd,
          "min_usd": round(min_sz * ct * px, 6) if px > 0 else 0.0,
        }
      qty = _redondear_paso(min_sz, lot, "ceil")
      notional = qty * ct * px if qty > 0 else 0.0
      deuda = max(0.0, objetivo - notional)
      # Candado no basta: el ticket mínimo no puede saltarse el techo al armar.
      techo = 0.0
      try:
        from core import beru_rango as _br

        techo = float(_br.masa_armar_max_usd() or 0)
      except Exception:
        techo = 0.0
      if techo > 0 and notional > techo + 1e-9:
        return {
          "ok": False,
          "motivo": "ticket_min_sobre_techo",
          "qty": 0.0,
          "notional_usd": 0.0,
          "deuda_usd": round(objetivo, 6),
          "instId": f.get("instId"),
          "paso_usd": paso_usd,
          "min_usd": round(notional, 6),
          "techo_usd": techo,
        }
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


def floor_completo(activo: str) -> bool:
  """True si el santo tiene piso real en BD (no inventado)."""
  base = str(activo or "").upper()
  if not base:
    return False
  row = (_cargar_bd().get("activos") or {}).get(base) or {}
  if not row:
    return False
  return (
    _f(row.get("ctVal")) > 0
    and _f(row.get("lotSz")) > 0
    and _f(row.get("tickSz")) > 0
    and _f(row.get("minSz")) > 0
  )


def asegurar_piso_okx(activo: str) -> dict[str, Any]:
  """Garantiza piso OKX en BD: lee disco o pide instrumentos públicos.

  Evita tick/lot inventados (tumor Oz). Si la casa no lista el SWAP, devuelve
  lo que haya (floor_completo=False) para que el campamento haga skip.
  """
  base = str(activo or "").upper()
  if floor_completo(base):
    return pierna_activo(base)

  inst = beru_mar.activo_a_inst_id(base)
  try:
    from core import okx_rest

    rows = okx_rest.get_public(
      "/api/v5/public/instruments",
      params={"instType": "SWAP", "instId": inst},
    ) or []
  except Exception:
    rows = []
  fila = rows[0] if rows and isinstance(rows[0], dict) else None
  if not fila:
    return pierna_activo(base)

  min_sz = _f(fila.get("minSz"), 1.0)
  lot_sz = _f(fila.get("lotSz"), 1.0)
  ct_val = _f(fila.get("ctVal"), 1.0)
  tick = _f(fila.get("tickSz"), 0.01)
  if min_sz <= 0 or lot_sz <= 0 or ct_val <= 0 or tick <= 0:
    return pierna_activo(base)

  # Precio ref (opcional) para min_usd_est
  px = 0.0
  try:
    from core import okx_rest

    tks = okx_rest.get_public(
      "/api/v5/market/ticker",
      params={"instId": inst},
    ) or []
    if tks and isinstance(tks[0], dict):
      px = _f(tks[0].get("last") or tks[0].get("lastPx"))
  except Exception:
    px = 0.0
  min_usd = min_sz * ct_val * px if px > 0 else float(
    getattr(config, "MIN_ORDER_USD_DEFAULT", 1.0) or 1.0
  )

  nuevo = {
    "instId": inst,
    "frente": f"{base}USDT_LINEAL",
    "minSz": min_sz,
    "lotSz": lot_sz,
    "ctVal": ct_val,
    "tickSz": tick,
    "min_usd_est": round(min_usd, 6),
    "precio_ref": px or None,
  }

  # Persistir en BD de minimos para no martillar la API en cada wake.
  ruta = _ruta_bd()
  try:
    bd = _cargar_bd()
    activos = dict(bd.get("activos") or {})
    activos[base] = nuevo
    meta = dict(bd.get("meta") or {})
    meta["n_activos"] = len(activos)
    out = {"meta": meta, "activos": activos}
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
      json.dump(out, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ruta)
  except OSError:
    pass
  invalidar_cache_bd()
  return pierna_activo(base)
