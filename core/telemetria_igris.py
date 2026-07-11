"""Telemetría de posiciones Igris — solo lectura para panel (sin lógica operativa)."""
from __future__ import annotations

from typing import Any

import core.config as config


def _leg_vacia() -> dict[str, Any]:
    return {
        "symbol": None,
        "size": None,
        "avg_price": None,
        "margen_usado_pct": None,
        "impacto_1pct_usd": None,
    }


def _construir_pierna(
    symbol: str | None,
    size: float,
    avg_price: float,
    position_im: float | None,
    equity_usd: float,
) -> dict[str, Any]:
    if size <= 0 or avg_price <= 0:
        return _leg_vacia()
    im = position_im if position_im is not None and position_im > 0 else None
    margen_pct = (im / equity_usd * 100.0) if im is not None and equity_usd > 0 else None
    impacto = size * avg_price * 0.01
    return {
        "symbol": symbol,
        "size": round(size, 8),
        "avg_price": round(avg_price, 8),
        "margen_usado_pct": round(margen_pct, 4) if margen_pct is not None else None,
        "impacto_1pct_usd": round(impacto, 4),
    }


def _notional(size: float, avg_price: float, position_value: float | None) -> float:
    if position_value and position_value > 0:
        return position_value
    return size * avg_price if size > 0 and avg_price > 0 else 0.0


def _elegir_pierna(posiciones: list[dict], side: str) -> dict[str, Any]:
    """side: Buy (long) o Sell (short)."""
    candidatas = [p for p in posiciones if p.get("side") == side and float(p.get("size") or 0) > 0]
    if not candidatas:
        return _leg_vacia()
    mejor = max(
        candidatas,
        key=lambda p: _notional(
            float(p.get("size") or 0),
            float(p.get("avgPrice") or 0),
            float(p.get("positionValue") or 0) if p.get("positionValue") not in ("", None) else None,
        ),
    )
    size = float(mejor.get("size") or 0)
    avg = float(mejor.get("avgPrice") or 0)
    im_raw = mejor.get("positionIM", "")
    im = float(im_raw) if im_raw not in ("", None) else None
    return {
        "symbol": mejor.get("symbol"),
        "size": size,
        "avg_price": avg,
        "position_im": im,
        "_obj": mejor,
    }


def telemetria_desde_exchange(posiciones: list[dict], equity_usd: float) -> dict[str, Any]:
    long_raw = _elegir_pierna(posiciones, "Buy")
    short_raw = _elegir_pierna(posiciones, "Sell")
    par = (
        short_raw.get("symbol")
        or long_raw.get("symbol")
        or getattr(config, "SIMBOLO_LINEAR", "BTCUSDT")
    )
    return {
        "par": par,
        "fuente": "exchange",
        "long": _construir_pierna(
            long_raw.get("symbol"),
            float(long_raw.get("size") or 0),
            float(long_raw.get("avg_price") or 0),
            long_raw.get("position_im"),
            equity_usd,
        ),
        "short": _construir_pierna(
            short_raw.get("symbol"),
            float(short_raw.get("size") or 0),
            float(short_raw.get("avg_price") or 0),
            short_raw.get("position_im"),
            equity_usd,
        ),
    }


def telemetria_desde_pesos(pesos: dict, equity_usd: float) -> dict[str, Any]:
    """Fallback lectura interna (sim / antes de primer poll exchange)."""
    from core import igris_manto as im
    from core import mercado

    if not pesos:
        return {"par": getattr(config, "SIMBOLO_LINEAR", "BTCUSDT"), "fuente": "interno", "long": _leg_vacia(), "short": _leg_vacia()}

    frente_dom = max(
        pesos.keys(),
        key=lambda f: float(pesos[f].get("long") or 0) + float(pesos[f].get("short") or 0),
    )
    pf = im.asegurar_peso(pesos, frente_dom)
    par = mercado.frente_a_symbol(frente_dom)

    fl, fs = im.frentes_bootstrap()
    pf_long = im.asegurar_peso(pesos, fl) if float(pesos.get(fl, {}).get("long") or 0) > 0 else pf
    pf_short = im.asegurar_peso(pesos, fs) if float(pesos.get(fs, {}).get("short") or 0) > 0 else pf

    sym_long = mercado.frente_a_symbol(fl if float(pesos.get(fl, {}).get("long") or 0) > 0 else frente_dom)
    sym_short = mercado.frente_a_symbol(fs if float(pesos.get(fs, {}).get("short") or 0) > 0 else frente_dom)

    size_l = float(pf_long.get("long") or 0)
    size_s = float(pf_short.get("short") or 0)
    px_l = float(pf_long.get("precio_medio_long") or 0)
    px_s = float(pf_short.get("precio_medio_short") or 0)

    return {
        "par": par,
        "fuente": "interno",
        "long": _construir_pierna(sym_long, size_l, px_l, None, equity_usd),
        "short": _construir_pierna(sym_short, size_s, px_s, None, equity_usd),
    }
