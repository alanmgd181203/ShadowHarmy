"""Telemetría de posiciones Igris — solo lectura para panel (sin lógica operativa)."""
from __future__ import annotations

from typing import Any

import core.config as config


def _leg_vacia() -> dict[str, Any]:
    return {
        "symbol": None,
        "frente": None,
        "size": None,
        "avg_price": None,
        "mark_price": None,
        "margen_usd": None,
        "margen_usado_pct": None,
        "leverage": None,
        "impacto_1pct_usd": None,
    }


def _f(val: Any) -> float | None:
    if val in ("", None):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _base_de_symbol(symbol: str) -> str:
    s = str(symbol or "").upper()
    for suf in ("USDT", "USDC", "USD"):
        if s.endswith(suf) and len(s) > len(suf):
            return s[: -len(suf)]
    return s or str(getattr(config, "TICKER_BASE", "BTC")).upper()


def _frente_hint(symbol: str, side: str) -> str | None:
    """Heurística frente Shadow Army desde símbolo Bybit."""
    s = str(symbol or "").upper()
    if not s:
        return None
    base = _base_de_symbol(s)
    if s.endswith("USDT") or s.endswith("USDC"):
        settle = "USDT" if s.endswith("USDT") else "USDC"
        return f"{base}{settle}_LINEAL"
    if s.endswith("USD"):
        return f"{base}USD_INVERSE"
    return None


def _notional(size: float, avg_price: float, position_value: float | None) -> float:
    if position_value and position_value > 0:
        return position_value
    return size * avg_price if size > 0 and avg_price > 0 else 0.0


def _leg_desde_pos(pos: dict) -> dict[str, Any]:
    size = float(pos.get("size") or 0)
    avg = float(pos.get("avgPrice") or 0)
    im = _f(pos.get("positionIM"))
    mark = _f(pos.get("markPrice"))
    lev = _f(pos.get("leverage"))
    pv = _f(pos.get("positionValue"))
    symbol = pos.get("symbol")
    side = pos.get("side")
    return {
        "symbol": symbol,
        "frente": _frente_hint(str(symbol or ""), str(side or "")),
        "side": side,
        "size": size,
        "avg_price": avg,
        "mark_price": mark,
        "margen_usd": im,
        "leverage": lev,
        "position_value": pv,
        "_notional": _notional(size, avg, pv),
    }


def _construir_pierna(
    symbol: str | None,
    size: float,
    avg_price: float,
    position_im: float | None,
    equity_usd: float,
    *,
    mark_price: float | None = None,
    leverage: float | None = None,
    frente: str | None = None,
) -> dict[str, Any]:
    if size <= 0 or avg_price <= 0:
        return _leg_vacia()
    im = position_im if position_im is not None and position_im > 0 else None
    margen_pct = (im / equity_usd * 100.0) if im is not None and equity_usd > 0 else None
    # impacto: si size ya es nocional USD (pesos internos), size*0.01; si es qty, size*px*0.01
    # Exchange telemetría usa qty → size * avg * 1%
    impacto = size * avg_price * 0.01
    return {
        "symbol": symbol,
        "frente": frente,
        "size": round(size, 8),
        "avg_price": round(avg_price, 8),
        "mark_price": round(mark_price, 8) if mark_price and mark_price > 0 else None,
        "margen_usd": round(im, 4) if im is not None else None,
        "margen_usado_pct": round(margen_pct, 4) if margen_pct is not None else None,
        "leverage": round(leverage, 2) if leverage is not None and leverage > 0 else None,
        "impacto_1pct_usd": round(impacto, 4),
    }


def _elegir_pierna(posiciones: list[dict], side: str) -> dict[str, Any]:
    """side: Buy (long) o Sell (short)."""
    candidatas = [_leg_desde_pos(p) for p in posiciones if p.get("side") == side and float(p.get("size") or 0) > 0]
    if not candidatas:
        return {}
    return max(candidatas, key=lambda p: float(p.get("_notional") or 0))


def _prefer_leg(existente: dict | None, nueva: dict, *, quiere_inverse: bool) -> dict:
    """Entre dos piernas del mismo lado, prioriza inverse (L) o lineal (S)."""
    if not existente:
        return nueva
    sym_n = str(nueva.get("symbol") or "").upper()
    sym_e = str(existente.get("symbol") or "").upper()
    if quiere_inverse:
        n_inv = sym_n.endswith("USD") and not sym_n.endswith("USDT") and not sym_n.endswith("USDC")
        e_inv = sym_e.endswith("USD") and not sym_e.endswith("USDT") and not sym_e.endswith("USDC")
        if n_inv and not e_inv:
            return nueva
        if e_inv and not n_inv:
            return existente
    else:
        n_lin = sym_n.endswith("USDT") or sym_n.endswith("USDC")
        e_lin = sym_e.endswith("USDT") or sym_e.endswith("USDC")
        if n_lin and not e_lin:
            return nueva
        if e_lin and not n_lin:
            return existente
    if float(nueva.get("_notional") or 0) > float(existente.get("_notional") or 0):
        return nueva
    return existente


def _por_activo_desde_posiciones(posiciones: list[dict], equity_usd: float) -> dict[str, Any]:
    """Mapa BTC → {long, short} con margen/lev/mark del Bridge."""
    buckets: dict[str, dict[str, Any]] = {}
    for raw in posiciones:
        if float(raw.get("size") or 0) <= 0:
            continue
        leg = _leg_desde_pos(raw)
        base = _base_de_symbol(str(leg.get("symbol") or ""))
        side = leg.get("side")
        key = "long" if side == "Buy" else "short" if side == "Sell" else None
        if not key:
            continue
        bucket = buckets.setdefault(base, {})
        quiere_inv = key == "long"
        bucket[key] = _prefer_leg(bucket.get(key), leg, quiere_inverse=quiere_inv)

    out: dict[str, Any] = {}
    for base, legs in buckets.items():
        long_raw = legs.get("long") or {}
        short_raw = legs.get("short") or {}
        out[base] = {
            "long": _construir_pierna(
                long_raw.get("symbol"),
                float(long_raw.get("size") or 0),
                float(long_raw.get("avg_price") or 0),
                long_raw.get("margen_usd"),
                equity_usd,
                mark_price=long_raw.get("mark_price"),
                leverage=long_raw.get("leverage"),
                frente=long_raw.get("frente"),
            ),
            "short": _construir_pierna(
                short_raw.get("symbol"),
                float(short_raw.get("size") or 0),
                float(short_raw.get("avg_price") or 0),
                short_raw.get("margen_usd"),
                equity_usd,
                mark_price=short_raw.get("mark_price"),
                leverage=short_raw.get("leverage"),
                frente=short_raw.get("frente"),
            ),
        }
    return out


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
            long_raw.get("margen_usd"),
            equity_usd,
            mark_price=long_raw.get("mark_price"),
            leverage=long_raw.get("leverage"),
            frente=long_raw.get("frente"),
        ),
        "short": _construir_pierna(
            short_raw.get("symbol"),
            float(short_raw.get("size") or 0),
            float(short_raw.get("avg_price") or 0),
            short_raw.get("margen_usd"),
            equity_usd,
            mark_price=short_raw.get("mark_price"),
            leverage=short_raw.get("leverage"),
            frente=short_raw.get("frente"),
        ),
        "por_activo": _por_activo_desde_posiciones(posiciones, equity_usd),
    }


def telemetria_desde_pesos(pesos: dict, equity_usd: float) -> dict[str, Any]:
    """Fallback lectura interna (sim / antes de primer poll exchange)."""
    from core import igris_manto as im
    from core import mercado

    if not pesos:
        return {
            "par": getattr(config, "SIMBOLO_LINEAR", "BTCUSDT"),
            "fuente": "interno",
            "long": _leg_vacia(),
            "short": _leg_vacia(),
            "por_activo": {},
        }

    frente_dom = max(
        pesos.keys(),
        key=lambda f: float(pesos[f].get("long") or 0) + float(pesos[f].get("short") or 0),
    )
    par = mercado.frente_a_symbol(frente_dom)

    fl, fs = im.frentes_bootstrap()
    pf_long = im.asegurar_peso(pesos, fl) if float(pesos.get(fl, {}).get("long") or 0) > 0 else im.asegurar_peso(pesos, frente_dom)
    pf_short = im.asegurar_peso(pesos, fs) if float(pesos.get(fs, {}).get("short") or 0) > 0 else im.asegurar_peso(pesos, frente_dom)

    sym_long = mercado.frente_a_symbol(fl if float(pesos.get(fl, {}).get("long") or 0) > 0 else frente_dom)
    sym_short = mercado.frente_a_symbol(fs if float(pesos.get(fs, {}).get("short") or 0) > 0 else frente_dom)

    size_l = float(pf_long.get("long") or 0)
    size_s = float(pf_short.get("short") or 0)
    px_l = float(pf_long.get("precio_medio_long") or 0)
    px_s = float(pf_short.get("precio_medio_short") or 0)

    # En pesos, size ya es nocional USD → impacto = size * 1% (sin * precio)
    long_leg = _leg_vacia()
    short_leg = _leg_vacia()
    if size_l > 0 and px_l > 0:
        long_leg = {
            "symbol": sym_long,
            "frente": fl if float(pesos.get(fl, {}).get("long") or 0) > 0 else frente_dom,
            "size": round(size_l / px_l, 8),  # qty aproximada para UI
            "avg_price": round(px_l, 8),
            "mark_price": None,
            "margen_usd": None,
            "margen_usado_pct": None,
            "leverage": None,
            "impacto_1pct_usd": round(size_l * 0.01, 4),
        }
    if size_s > 0 and px_s > 0:
        short_leg = {
            "symbol": sym_short,
            "frente": fs if float(pesos.get(fs, {}).get("short") or 0) > 0 else frente_dom,
            "size": round(size_s / px_s, 8),
            "avg_price": round(px_s, 8),
            "mark_price": None,
            "margen_usd": None,
            "margen_usado_pct": None,
            "leverage": None,
            "impacto_1pct_usd": round(size_s * 0.01, 4),
        }

    por_activo: dict[str, Any] = {}
    bases = {mercado.activo_de_frente(f) for f in pesos}
    for base in bases:
        fl_b, fs_b = im.frentes_bootstrap(base)
        pl = float(pesos.get(fl_b, {}).get("long") or 0)
        ps = float(pesos.get(fs_b, {}).get("short") or 0)
        if pl <= 0 and ps <= 0:
            # sumar cualquier frente del activo
            for frente, p in pesos.items():
                if mercado.activo_de_frente(frente) != base:
                    continue
                pl += float(p.get("long") or 0)
                ps += float(p.get("short") or 0)
        if pl <= 0 and ps <= 0:
            continue
        pml = float(pesos.get(fl_b, {}).get("precio_medio_long") or 0)
        pms = float(pesos.get(fs_b, {}).get("precio_medio_short") or 0)
        L = _leg_vacia()
        S = _leg_vacia()
        if pl > 0 and pml > 0:
            L = {
                "symbol": mercado.frente_a_symbol(fl_b),
                "frente": fl_b,
                "size": round(pl / pml, 8),
                "avg_price": round(pml, 8),
                "mark_price": None,
                "margen_usd": None,
                "margen_usado_pct": None,
                "leverage": None,
                "impacto_1pct_usd": round(pl * 0.01, 4),
            }
        if ps > 0 and pms > 0:
            S = {
                "symbol": mercado.frente_a_symbol(fs_b),
                "frente": fs_b,
                "size": round(ps / pms, 8),
                "avg_price": round(pms, 8),
                "mark_price": None,
                "margen_usd": None,
                "margen_usado_pct": None,
                "leverage": None,
                "impacto_1pct_usd": round(ps * 0.01, 4),
            }
        por_activo[base] = {"long": L, "short": S}

    return {
        "par": par,
        "fuente": "interno",
        "long": long_leg,
        "short": short_leg,
        "por_activo": por_activo,
    }
