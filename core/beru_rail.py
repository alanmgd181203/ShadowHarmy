"""Beru — elegir mejor rail spot frente a stables (USDT/USDC/USDE/USD1)."""
from __future__ import annotations

from typing import Any

import core.config as config


STABLE_QUOTES = ("USDT", "USDC", "USDE", "USD1")


def _quotes_activos() -> tuple[str, ...]:
    """USDT-only si BERU_RAIL_USDT_ONLY; si no, todos los stables conocidos."""
    if getattr(config, "BERU_RAIL_USDT_ONLY", False):
        return ("USDT",)
    return STABLE_QUOTES


def activo_semilla() -> str:
    return str(getattr(config, "BERU_ACTIVO_SEMILLA", "") or config.TICKER_BASE).upper()


def frentes_casa_estables(base: str | None = None) -> list[str]:
    """Spot del activo semilla frente a stables."""
    b = (base or activo_semilla()).upper()
    quotes = _quotes_activos()
    out: list[str] = []
    seen: set[str] = set()
    for q in quotes:
        f = f"{b}{q}_SPOT"
        if f not in seen:
            out.append(f)
            seen.add(f)
    for p in getattr(config, "SPOT_ALL_PARES", []) or []:
        bc = str(p.get("baseCoin") or "").upper()
        qc = str(p.get("quoteCoin") or "").upper()
        if bc == b and qc in quotes:
            frente = str(p.get("frente") or f"{bc}{qc}_SPOT")
            if frente not in seen:
                out.append(frente)
                seen.add(frente)
    # Fallback config legacy — filtrar a quotes activos
    for f in getattr(config, "FRENTES_CASA", []) or []:
        if not f.startswith(b) or f in seen:
            continue
        if quotes == ("USDT",) and "USDT" not in f.split("_")[0]:
            continue
        out.append(f)
        seen.add(f)
    return out


def _fee_pct_estimado(frente: str) -> float:
    """Fee spot taker aproximado (%)."""
    if "USDC" in frente.split("_")[0]:
        return float(getattr(config, "BERU_RAIL_FEE_USDC_PCT", 0.10))
    return float(getattr(config, "BERU_RAIL_FEE_USDT_PCT", 0.10))


def _score_rail(
    frente: str,
    ctx,
    *,
    masa: float,
    is_long: bool,
    liquidez: dict | None = None,
) -> tuple[float, dict[str, Any]]:
    """Precio efectivo + metadata; menor = mejor compra, mayor = mejor venta."""
    if not ctx or ctx.last_price <= 0:
        return (float("inf") if is_long else float("-inf")), {"ok": False}

    muro = ctx.muro_ask_volumen if is_long else ctx.muro_bid_volumen
    penalidad_muro = 0.0001 if muro > (masa * 10) else 0.0015
    fee = _fee_pct_estimado(frente) / 100.0
    slip = float((liquidez or {}).get("slippage_pct") or 0) / 100.0

    if is_long:
        p_ef = ctx.last_price * (1.0 + penalidad_muro + fee + slip)
    else:
        p_ef = ctx.last_price * (1.0 - penalidad_muro - fee - slip)

    meta = {
        "ok": True,
        "frente": frente,
        "precio": ctx.last_price,
        "penalidad_muro": penalidad_muro,
        "fee_pct": fee * 100,
        "slippage_pct": slip * 100,
        "entrada_max_usd": (liquidez or {}).get("entrada_maxima_usd"),
        "entrada_segura_usd": (liquidez or {}).get("entrada_segura_usd"),
    }
    return p_ef, meta


def elegir_mejor_rail(
    ctx_map: dict,
    masa: float,
    is_long: bool,
    *,
    base: str | None = None,
    libros: dict | None = None,
    kaiser=None,
) -> tuple[str, float, dict[str, Any]]:
    """
    Elige la mejor oveja entre rebaños stable (USDT/USDC/USDE/USD1).
    Si hay Kaiser+Ancla, prioriza liquidez viable sobre precio bruto.
    """
    from core import ancla

    b = (base or activo_semilla()).upper()
    frentes = frentes_casa_estables(b)
    libros = libros or {}
    candidatos: list[tuple[float, str, dict]] = []

    for f in frentes:
        ctx = ctx_map.get(f)
        liq = None
        if libros.get(f) and kaiser is not None:
            try:
                liq = kaiser.consultar_liquidez({
                    "general": "BERU",
                    "masa": masa,
                    "frente": f,
                    "direccion": "LONG" if is_long else "SHORT",
                })
            except Exception:
                liq = None
        elif libros.get(f):
            libro = libros[f]
            lado = "BUY" if is_long else "SELL"
            try:
                info = ancla.entrada_maxima_desde_libro(
                    libro.get("bids") or [],
                    libro.get("asks") or [],
                    f,
                    lado,
                )
                max_u = float(info.get("entrada_maxima_usd") or 0)
                if max_u > 0 and max_u < masa:
                    continue
                liq = {"entrada_maxima_usd": max_u, "slippage_pct": 0}
            except Exception:
                pass

        p_ef, meta = _score_rail(f, ctx, masa=masa, is_long=is_long, liquidez=liq)
        if not meta.get("ok"):
            continue
        candidatos.append((p_ef, f, meta))

    if not candidatos:
        fallback = frentes[0] if frentes else f"{b}USDT_SPOT"
        return fallback, 0.0, {"ok": False, "frente": fallback, "motivo": "SIN_CANDIDATOS"}

    if is_long:
        p_ef, frente, meta = min(candidatos, key=lambda x: x[0])
    else:
        p_ef, frente, meta = max(candidatos, key=lambda x: x[0])

    meta["candidatos"] = len(candidatos)
    meta["frentes_evaluados"] = [c[1] for c in candidatos]
    return frente, p_ef, meta
