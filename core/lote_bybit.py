"""Lotes Bybit — minOrderQty + qtyStep desde BD Jess (sin API en la forja).

Fuente: data/bybit_parametros_mercado.json (ritual México).
Cuantiza cantidades a múltiplos válidos del exchange.
"""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from typing import Any, Literal

import core.config as config
from core import ancla
from core import mercado

ModoRedondeo = Literal["floor", "ceil"]


def _ruta_bd() -> str:
    override = getattr(config, "BYBIT_PARAMETROS_PATH", None)
    if override:
        return str(override)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "bybit_parametros_mercado.json")


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


def base_desde_frente(frente: str) -> str:
    """ETHUSDT_LINEAL → ETH · BTCUSD_INVERSE → BTC."""
    f = (frente or "").upper()
    if "_" in f:
        sym = f.rsplit("_", 1)[0]
    else:
        sym = f
    for suf in ("USDT", "USDC", "USD"):
        if sym.endswith(suf) and len(sym) > len(suf):
            return sym[: -len(suf)]
    return sym


def clave_mercado_desde_frente(frente: str) -> str:
    """linear | inverse | spot_usdt | spot_usdc."""
    f = (frente or "").upper()
    cat = mercado.frente_a_category(f)
    if cat == "inverse" or f.endswith("_INVERSE"):
        return "inverse"
    if f.endswith("_SPOT"):
        if "USDC" in f:
            return "spot_usdc"
        return "spot_usdt"
    if "USDC" in f and cat == "linear":
        return "linear"  # USDC linear vive bajo linear en BD si existe
    return "linear"


def filtros_lote(frente: str) -> dict[str, Any]:
    """
    Filtros de lote para un frente.
    Fallback: min USD Ancla + step desconocido (1.0 o sin step).
    """
    bd = _cargar_bd()
    base = base_desde_frente(frente)
    clave = clave_mercado_desde_frente(frente)
    activo = (bd.get("activos") or {}).get(base) or {}
    row = activo.get(clave) if isinstance(activo.get(clave), dict) else None

    min_usd_ancla = ancla.min_order_usd_frente(frente)
    if not row:
        return {
            "base": base,
            "clave": clave,
            "frente": frente,
            "minOrderQty": 0.0,
            "qtyStep": 0.0,
            "minNotionalValue": min_usd_ancla,
            "min_usd_est": min_usd_ancla,
            "unidad_min_qty": "base_coin" if clave != "inverse" else "usd_contrato",
            "tickSize": None,
            "precio_ref": None,
            "fuente": "fallback_ancla",
            "ok": False,
        }

    min_qty = float(row.get("minOrderQty") or 0)
    step = float(row.get("qtyStep") or 0)
    min_not = float(row.get("minNotionalValue") or 0)
    min_usd = float(row.get("min_usd_est") or min_not or min_usd_ancla or 0)
    return {
        "base": base,
        "clave": clave,
        "frente": (frente or "").upper(),
        "symbol": row.get("symbol"),
        "minOrderQty": min_qty,
        "qtyStep": step,
        "minNotionalValue": min_not,
        "min_usd_est": max(min_usd, min_usd_ancla) if min_usd_ancla else min_usd,
        "unidad_min_qty": row.get("unidad_min_qty") or (
            "usd_contrato" if clave == "inverse" else "base_coin"
        ),
        "tickSize": row.get("tickSize"),
        "precio_ref": row.get("precio_ref"),
        "fuente": "bybit_parametros_mercado",
        "ok": True,
    }


def cuantizar_qty(
    qty: float,
    *,
    min_qty: float,
    qty_step: float,
    mode: ModoRedondeo = "floor",
) -> float:
    """Redondea a múltiplo de qtyStep, ≥ minOrderQty. 0 si no alcanza el mínimo."""
    q = float(qty)
    if q <= 0:
        return 0.0
    step = float(qty_step or 0)
    minimo = float(min_qty or 0)
    if step <= 0:
        if minimo > 0 and q + 1e-15 < minimo:
            return 0.0
        return q
    if mode == "ceil":
        n = math.ceil(q / step - 1e-12)
    else:
        n = math.floor(q / step + 1e-12)
    out = n * step
    if minimo > 0 and out + 1e-15 < minimo:
        if q + 1e-12 >= minimo:
            n_min = math.ceil(minimo / step - 1e-12)
            out = n_min * step
        else:
            return 0.0
    # Evitar polvo float (0.001 * 3 = 0.0030000000004)
    dec = max(0, min(10, -int(math.floor(math.log10(step))) if step < 1 else 0))
    return round(out, dec + 2)


def usd_a_qty(usd: float, precio: float, filtros: dict[str, Any]) -> float:
    """Convierte presupuesto USD → qty de exchange según unidad del contrato."""
    u = float(usd)
    px = float(precio)
    if u <= 0:
        return 0.0
    unidad = str(filtros.get("unidad_min_qty") or "base_coin")
    if unidad == "usd_contrato" or filtros.get("clave") == "inverse":
        return u  # inverse: qty ≈ USD contrato
    if px <= 0:
        return 0.0
    return u / px


def qty_a_usd(qty: float, precio: float, filtros: dict[str, Any]) -> float:
    q = float(qty)
    px = float(precio)
    if q <= 0:
        return 0.0
    unidad = str(filtros.get("unidad_min_qty") or "base_coin")
    if unidad == "usd_contrato" or filtros.get("clave") == "inverse":
        return q
    return q * max(px, 0.0)


def cuantizar_presupuesto_usd(
    usd: float,
    precio: float,
    frente: str,
    *,
    mode: ModoRedondeo = "floor",
) -> dict[str, Any]:
    """USD deseado → qty válida + USD efectivo tras qtyStep."""
    filt = filtros_lote(frente)
    qty_raw = usd_a_qty(usd, precio, filt)
    qty = cuantizar_qty(
        qty_raw,
        min_qty=float(filt.get("minOrderQty") or 0),
        qty_step=float(filt.get("qtyStep") or 0),
        mode=mode,
    )
    usd_eff = qty_a_usd(qty, precio, filt)
    min_not = float(filt.get("minNotionalValue") or 0)
    if min_not > 0 and usd_eff + 1e-9 < min_not and qty > 0:
        # Subir un step hasta cubrir notional si el presupuesto original alcanzaba
        step = float(filt.get("qtyStep") or 0)
        min_q = float(filt.get("minOrderQty") or 0)
        if step > 0 and float(usd) + 1e-9 >= min_not:
            while usd_eff + 1e-9 < min_not:
                qty = cuantizar_qty(qty + step, min_qty=min_q, qty_step=step, mode="floor")
                usd_eff = qty_a_usd(qty, precio, filt)
                if qty <= 0:
                    break
        if usd_eff + 1e-9 < min_not:
            qty, usd_eff = 0.0, 0.0
    return {
        "ok": qty > 0,
        "qty": qty,
        "usd": round(usd_eff, 6),
        "filtros": filt,
    }


def paso_minimo_usd(frente: str, precio: float) -> float:
    """USD de un escalón mínimo válido (1× minOrderQty cuantizado)."""
    filt = filtros_lote(frente)
    min_q = float(filt.get("minOrderQty") or 0)
    step = float(filt.get("qtyStep") or 0)
    q = cuantizar_qty(min_q if min_q > 0 else step, min_qty=min_q, qty_step=step, mode="ceil")
    if q <= 0:
        return float(filt.get("min_usd_est") or ancla.min_order_usd_frente(frente) or 5.0)
    return max(
        qty_a_usd(q, precio, filt),
        float(filt.get("minNotionalValue") or 0),
        float(filt.get("min_usd_est") or 0),
    )
