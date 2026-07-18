#!/usr/bin/env python3
"""Base de parametros Bybit vivos: apalancamiento max + minimos de orden.

Fuente: GET /v5/market/instruments-info (+ tickers para USD).
Escrita por Jess sync / Kaiser refresh → data/bybit_parametros_mercado.json

Unidades:
  - linear / spot: minOrderQty suele ser fraccion de moneda → min_usd ≈ qty * precio
  - inverse: minOrderQty suele cotizar en USD de contrato → min_usd ≈ qty
  - piso_manto_usd = max(min_usd_linear, min_usd_inverse)  # limitante Igris L+S
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.bybit.com"
DB_PATH = ROOT / "data" / "bybit_parametros_mercado.json"


def get_json(path: str, *, timeout: float = 60) -> dict[str, Any]:
    url = f"{API}{path}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ShadowHarmy-ParametrosBybit/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def page_instruments(category: str, *, quote_coin: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cursor = ""
    while True:
        q = f"/v5/market/instruments-info?category={category}&limit=1000"
        if cursor:
            q += f"&cursor={cursor}"
        payload = get_json(q)
        if int(payload.get("retCode") or -1) != 0:
            raise RuntimeError(f"instruments {category}: {payload.get('retMsg')}")
        result = payload.get("result") or {}
        for x in result.get("list") or []:
            if x.get("status") != "Trading":
                continue
            if quote_coin and x.get("quoteCoin") != quote_coin:
                continue
            out.append(x)
        cursor = result.get("nextPageCursor") or ""
        if not cursor:
            break
    return out


def ticker_last(category: str, symbol: str) -> float:
    try:
        data = get_json(f"/v5/market/tickers?category={category}&symbol={symbol}")
    except Exception:
        return 0.0
    lst = (data.get("result") or {}).get("list") or []
    if not lst:
        return 0.0
    row = lst[0]
    for key in ("lastPrice", "markPrice", "indexPrice"):
        try:
            px = float(row.get(key) or 0)
        except (TypeError, ValueError):
            px = 0.0
        if px > 0:
            return px
    return 0.0


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def minimos_de_instrumento(x: dict[str, Any], category: str, precio: float = 0.0) -> dict[str, Any]:
    """Extrae minimos reales + estimacion USD."""
    lot = x.get("lotSizeFilter") or {}
    min_qty = _f(lot.get("minOrderQty"))
    qty_step = _f(lot.get("qtyStep") or lot.get("basePrecision"))
    min_notional = _f(lot.get("minNotionalValue") or lot.get("minOrderAmt"))
    unidad = "usd_contrato" if category == "inverse" else "base_coin"

    if category == "inverse" and min_qty > 0:
        min_usd = min_qty
        como = "minOrderQty_usd_contrato"
    elif min_notional > 0:
        min_usd = min_notional
        como = "minNotionalValue"
    elif min_qty > 0 and precio > 0:
        min_usd = round(min_qty * precio, 6)
        como = "minOrderQty_x_precio"
    elif min_qty > 0:
        min_usd = None
        como = "minOrderQty_sin_precio"
    else:
        min_usd = None
        como = "desconocido"

    return {
        "symbol": x.get("symbol"),
        "category": category,
        "baseCoin": x.get("baseCoin"),
        "quoteCoin": x.get("quoteCoin"),
        "unidad_min_qty": unidad,
        "minOrderQty": min_qty or None,
        "qtyStep": qty_step or None,
        "minNotionalValue": min_notional or None,
        "precio_ref": precio or None,
        "min_usd_est": min_usd,
        "min_usd_como": como,
        "maxLeverage": (x.get("leverageFilter") or {}).get("maxLeverage"),
        "tickSize": (x.get("priceFilter") or {}).get("tickSize"),
    }


def slim_instrument(x: dict[str, Any]) -> dict[str, Any]:
    lf = x.get("leverageFilter") or {}
    lot = x.get("lotSizeFilter") or {}
    price = x.get("priceFilter") or {}
    return {
        "symbol": x.get("symbol"),
        "baseCoin": x.get("baseCoin"),
        "quoteCoin": x.get("quoteCoin"),
        "contractType": x.get("contractType"),
        "status": x.get("status"),
        "maxLeverage": lf.get("maxLeverage"),
        "minLeverage": lf.get("minLeverage"),
        "leverageStep": lf.get("leverageStep"),
        "minOrderQty": lot.get("minOrderQty"),
        "qtyStep": lot.get("qtyStep"),
        "maxOrderQty": lot.get("maxOrderQty"),
        "minNotionalValue": lot.get("minNotionalValue") or lot.get("minOrderAmt"),
        "tickSize": price.get("tickSize"),
        "deliveryFeeRate": x.get("deliveryFeeRate"),
        "fundingInterval": x.get("fundingInterval"),
        "unifiedMarginTrade": x.get("unifiedMarginTrade"),
        "marginTrading": x.get("marginTrading"),
    }


def _index_by_base(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for x in items:
        base = str(x.get("baseCoin") or "").upper()
        if base and base not in idx:
            idx[base] = x
    return idx


def construir_base_parametros(
    *,
    linear: list[dict[str, Any]],
    inverse: list[dict[str, Any]],
    spot_usdt: list[dict[str, Any]],
    spot_usdc: list[dict[str, Any]],
    fetch_prices: bool = True,
) -> dict[str, Any]:
    """Arma la BD: por baseCoin, piernas linear/inverse/spot + piso_manto."""
    lin_idx = _index_by_base(linear)
    inv_idx = _index_by_base(inverse)
    spot_u_idx = _index_by_base(spot_usdt)
    spot_c_idx = _index_by_base(spot_usdc)
    bases = sorted(set(lin_idx) | set(inv_idx) | set(spot_u_idx) | set(spot_c_idx))

    activos: dict[str, Any] = {}
    for base in bases:
        lin = lin_idx.get(base)
        inv = inv_idx.get(base)
        su = spot_u_idx.get(base)
        sc = spot_c_idx.get(base)

        px_lin = ticker_last("linear", str(lin["symbol"])) if (fetch_prices and lin) else 0.0
        px_inv = ticker_last("inverse", str(inv["symbol"])) if (fetch_prices and inv) else 0.0
        px_su = ticker_last("spot", str(su["symbol"])) if (fetch_prices and su) else 0.0
        px_sc = ticker_last("spot", str(sc["symbol"])) if (fetch_prices and sc) else 0.0

        row_lin = minimos_de_instrumento(lin, "linear", px_lin) if lin else None
        row_inv = minimos_de_instrumento(inv, "inverse", px_inv) if inv else None
        row_su = minimos_de_instrumento(su, "spot", px_su) if su else None
        row_sc = minimos_de_instrumento(sc, "spot", px_sc) if sc else None

        mins = [m for m in (row_lin, row_inv) if m and m.get("min_usd_est")]
        piso_manto = max(m["min_usd_est"] for m in mins) if mins else None

        activos[base] = {
            "linear": row_lin,
            "inverse": row_inv,
            "spot_usdt": row_su,
            "spot_usdc": row_sc,
            "max_leverage_linear": row_lin.get("maxLeverage") if row_lin else None,
            "max_leverage_inverse": row_inv.get("maxLeverage") if row_inv else None,
            "piso_manto_usd": piso_manto,
            "en_flota_manto": bool(lin and inv),
        }

    return {
        "meta": {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "fuente": "Bybit instruments-info + tickers",
            "n_bases": len(activos),
            "n_linear": len(linear),
            "n_inverse": len(inverse),
            "n_spot_usdt": len(spot_usdt),
            "n_spot_usdc": len(spot_usdc),
            "nota_unidades": (
                "linear/spot: min qty en moneda base; inverse: min qty suele ser USD contrato. "
                "piso_manto_usd = max(min_usd linear, min_usd inverse) para Igris L+S."
            ),
        },
        "activos": activos,
    }


def guardar_base(db: dict[str, Any], path: Path = DB_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def cargar_base(path: Path = DB_PATH) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
