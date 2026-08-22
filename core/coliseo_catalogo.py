"""Catálogo Bybit para mega Coliseo / teatro Beru rango.

TradeFi (acciones, etc.) vive en category=linear con symbolType=stock|commodity.
No hay category API separada 'tradefi'.
"""
from __future__ import annotations

from typing import Any


def _session():
    from pybit.unified_trading import HTTP

    return HTTP(testnet=False)


def discover_linear_perpetual_usdt(
    *,
    incluir_futures: bool = False,
    solo_tradefi: bool = False,
    excluir_tradefi: bool = False,
) -> list[dict[str, Any]]:
    """Un Santo = baseCoin · LinearPerpetual USDT (sin duplicar LTC en 5 disfraces)."""
    session = _session()
    resp = session.get_instruments_info(category="linear", limit=1000)
    lst = (resp.get("result") or {}).get("list") or []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    allowed_types = ("LinearPerpetual",) if not incluir_futures else ("LinearPerpetual", "LinearFutures")

    for row in lst:
        if row.get("status") != "Trading":
            continue
        if row.get("contractType") not in allowed_types:
            continue
        if str(row.get("quoteCoin") or "").upper() != "USDT":
            continue
        sym = str(row.get("symbol") or "")
        base = str(row.get("baseCoin") or "").upper()
        if not base or not sym:
            continue
        sym_type = str(row.get("symbolType") or "crypto").lower()
        is_tradefi = sym_type in ("stock", "commodity", "fx")
        if solo_tradefi and not is_tradefi:
            continue
        if excluir_tradefi and is_tradefi:
            continue
        # Futures dated: base puede repetirse (XAUTUSDT-28AUG26) — clave única = symbol
        if incluir_futures and row.get("contractType") == "LinearFutures":
            key = sym.upper()
            base_key = f"{base}@{sym}"
        else:
            key = base
            base_key = base
            if key in seen:
                continue
            seen.add(key)
        out.append(
            {
                "base": base if not incluir_futures or row.get("contractType") != "LinearFutures" else base_key,
                "symbol": sym,
                "symbol_type": sym_type,
                "tradefi": is_tradefi,
                "contract_type": str(row.get("contractType") or ""),
                "ck": f"{base_key}@linear",
            }
        )
    out.sort(key=lambda x: (not x.get("tradefi"), str(x.get("base"))))
    return out


def resumen_catalogo(rows: list[dict[str, Any]]) -> dict[str, int]:
    n_tf = sum(1 for r in rows if r.get("tradefi"))
    n_crypto = len(rows) - n_tf
    types: dict[str, int] = {}
    for r in rows:
        t = str(r.get("symbol_type") or "crypto")
        types[t] = types.get(t, 0) + 1
    return {"total": len(rows), "tradefi": n_tf, "crypto": n_crypto, "por_tipo": types}
