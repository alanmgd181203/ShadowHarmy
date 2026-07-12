#!/usr/bin/env python3
"""Genera diccionario estático de costos Beru — Flota del Manto (Inverse ∩ Linear USDT).

No hardcodea el tamaño de la flota: cruza dinámicamente todos los perpetuos
Trading de Bybit en ambas categorías y deja que beru_capital calcule X/grados.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_capital as bc
from core.trinidad import min_order_usd_de_instrumento

API = "https://api.bybit.com"
OUT_PATH = ROOT / "config" / "diccionario_beru_flota_manto.json"


def _get_json(path: str) -> dict[str, Any]:
    url = f"{API}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "ShadowHarmy-BeruDict/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode())


def _page_instruments(category: str, *, quote_coin: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cursor = ""
    while True:
        q = f"/v5/market/instruments-info?category={category}&limit=1000"
        if cursor:
            q += f"&cursor={cursor}"
        payload = _get_json(q)
        result = payload.get("result") or {}
        for x in result.get("list") or []:
            if x.get("status") != "Trading":
                continue
            if quote_coin and x.get("quoteCoin") != quote_coin:
                continue
            ct = str(x.get("contractType") or "")
            if ct and "Perpetual" not in ct:
                continue
            out.append(x)
        cursor = result.get("nextPageCursor") or ""
        if not cursor:
            break
    return out


def _index_by_base(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Un instrumento por baseCoin (el primero Trading/Perpetual visto)."""
    idx: dict[str, dict[str, Any]] = {}
    for x in items:
        base = str(x.get("baseCoin") or "").upper()
        if base and base not in idx:
            idx[base] = x
    return idx


def _max_leverage(instr: dict[str, Any]) -> float:
    lf = instr.get("leverageFilter") or {}
    try:
        lev = float(lf.get("maxLeverage") or 0)
    except (TypeError, ValueError):
        lev = 0.0
    if lev <= 0:
        lev = float(getattr(config, "MANTO_LEVERAGE_DEFAULT", 25.0))
    return lev


def _ticker_last(category: str, symbol: str) -> float:
    try:
        data = _get_json(f"/v5/market/tickers?category={category}&symbol={symbol}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
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


def _g_min_usd(instr: dict[str, Any], category: str, precio: float) -> float:
    enriched = dict(instr)
    if precio > 0:
        enriched["lastPrice"] = precio
    return float(min_order_usd_de_instrumento(enriched, category))


def descubrir_flota_manto() -> tuple[list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    inverse_list = _page_instruments("inverse")
    linear_list = _page_instruments("linear", quote_coin="USDT")
    inv_idx = _index_by_base(inverse_list)
    lin_idx = _index_by_base(linear_list)
    flota = sorted(set(inv_idx) & set(lin_idx))
    return flota, inv_idx, lin_idx


def main() -> int:
    print("=" * 78)
    print("  FLOTA DEL MANTO — Inverse ∩ Linear USDT → motor beru_capital (A_base=0)")
    print("=" * 78)

    flota, inv_idx, lin_idx = descubrir_flota_manto()
    print(f"\n  Inverse perp Trading: {len(inv_idx)} bases")
    print(f"  Linear  USDT Trading: {len(lin_idx)} bases")
    print(f"  Intersección Flota:   {len(flota)} activos (sin tope numérico)\n")
    print(f"  Activos: {', '.join(flota)}\n")

    diccionario: dict[str, Any] = {
        "meta": {
            "fuente": "Bybit public instruments-info",
            "regla": "intersection InversePerpetual ∩ LinearPerpetual USDT",
            "a_base": 0,
            "motor": "core.beru_capital.rangos_activo",
            "n_flota": len(flota),
            "activos": flota,
        },
        "activos": {},
    }

    hdr = (
        f"{'Activo':<8} {'G_min':>8} {'LevI':>6} {'LevL':>6} {'LevAvg':>7} "
        f"{'X':>6} {'Soldado':>14} {'Capitán':>14} {'General':>14} {'Mariscal':>10}"
    )
    print(hdr)
    print("-" * len(hdr))

    for asset in flota:
        inv = inv_idx[asset]
        lin = lin_idx[asset]
        lev_i = _max_leverage(inv)
        lev_l = _max_leverage(lin)
        lev_avg = (lev_i + lev_l) / 2.0

        sym_lin = str(lin.get("symbol") or f"{asset}USDT")
        sym_inv = str(inv.get("symbol") or f"{asset}USD")
        px_lin = _ticker_last("linear", sym_lin)
        px_inv = _ticker_last("inverse", sym_inv)

        g_lin = _g_min_usd(lin, "linear", px_lin)
        g_inv = _g_min_usd(inv, "inverse", px_inv)
        # Conservador: el mayor G_min entre piernas (cubre la pata más cara)
        g_min = max(g_lin, g_inv)

        # Inyección temporal → motor sin reescribir fricción/ceil
        config.G_MIN_USD_BY_ASSET[asset] = g_min
        config.MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET[asset] = lev_l
        config.MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET[asset] = lev_i

        fila = bc.rangos_activo(asset, a_base=0)
        lo_s, hi_s = fila["SOLDADO"]
        lo_c, hi_c = fila["CAPITAN"]
        lo_g, hi_g = fila["GENERAL"]

        entrada = {
            "symbol_linear": sym_lin,
            "symbol_inverse": sym_inv,
            "G_min": round(float(fila["G_min"]), 4),
            "G_min_linear": round(g_lin, 4),
            "G_min_inverse": round(g_inv, 4),
            "precio_linear": px_lin,
            "precio_inverse": px_inv,
            "max_leverage_linear": lev_l,
            "max_leverage_inverse": lev_i,
            "lev_promedio": fila["lev_promedio"],
            "A_base": 0,
            "X": fila["X"],
            "margen_volumen_base_usd": fila["margen_volumen_base_usd"],
            "SOLDADO": list(fila["SOLDADO"]),
            "CAPITAN": list(fila["CAPITAN"]),
            "GENERAL": list(fila["GENERAL"]),
            "MARISCAL": fila["MARISCAL"],
            "friccion": fila["friccion"],
        }
        diccionario["activos"][asset] = entrada

        print(
            f"{asset:<8} {g_min:8.2f} {lev_i:6.0f} {lev_l:6.0f} {lev_avg:7.1f} "
            f"{fila['X']:6d} [{lo_s:>5}-{hi_s:<5}] [{lo_c:>5}-{hi_c:<5}] "
            f"[{lo_g:>5}-{hi_g:<5}] {fila['MARISCAL']:10d}"
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(diccionario, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("-" * len(hdr))
    print(f"\n  OK → {OUT_PATH}")
    print(f"  Flota del Manto: {len(flota)} activos · A_base=0 aislado por moneda\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
