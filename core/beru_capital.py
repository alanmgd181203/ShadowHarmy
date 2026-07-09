"""Beru — capital mínimo manto por tier Proto/Pleno."""
from __future__ import annotations

from typing import Any

import core.config as config
from core import beru_tier


def apalancamiento_linear_max(asset: str) -> float:
    mp = getattr(config, "MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET", {}) or {}
    default = float(getattr(config, "MANTO_LEVERAGE_DEFAULT", 25.0))
    return float(mp.get(asset.upper(), default))


def apalancamiento_inverse_max(asset: str) -> float:
    mp = getattr(config, "MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET", {}) or {}
    default = float(getattr(config, "MANTO_LEVERAGE_DEFAULT", 25.0))
    return float(mp.get(asset.upper(), default))


def apalancamiento_manto_promedio(asset: str) -> float:
    li = apalancamiento_linear_max(asset)
    inv = apalancamiento_inverse_max(asset)
    return (li + inv) / 2.0


def notional_por_pierna_objetivo() -> float:
    pnl = float(getattr(config, "BERU_PNL_OBJETIVO_POR_1PCT_USD", 50.0))
    return pnl / 0.01


def margen_manto_pleno(asset: str) -> float:
    """Margen L+S Beru pleno (paso 0,1 % simétrico)."""
    lev = max(apalancamiento_manto_promedio(asset), 1.0)
    return round(2.0 * notional_por_pierna_objetivo() / lev, 2)


def margen_manto_por_tier(asset: str, tier_id: str | None = None) -> float:
    tier = beru_tier.tier_por_id(tier_id)
    return round(margen_manto_pleno(asset) / tier.escala_manto, 2)


def margen_manto_beru_100(asset: str) -> float:
    """Alias — margen tier activo por config."""
    return margen_manto_por_tier(asset, getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))


def pnl_por_1pct_con_margen(asset: str, margen_manto_usd: float) -> float:
    lev = max(apalancamiento_manto_promedio(asset), 1.0)
    por_pierna = max(margen_manto_usd, 0) / 2.0
    notional = por_pierna * lev
    return round(notional * 0.01, 2)


def equity_minima_recomendada(
    asset: str,
    *,
    tier_id: str | None = None,
    incluir_spot_beru: bool = False,
) -> float:
    base = margen_manto_por_tier(asset, tier_id)
    if incluir_spot_beru:
        base += float(getattr(config, "BERU_SPOT_COLCHON_USD", 0.0))
    return round(base, 2)


def fila_capital(asset: str, tier_id: str | None = None) -> dict[str, Any]:
    tid = tier_id or str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))
    tier = beru_tier.tier_por_id(tid)
    lev_p = apalancamiento_manto_promedio(asset)
    manto_pleno = margen_manto_pleno(asset)
    manto_tier = margen_manto_por_tier(asset, tid)
    return {
        "activo": asset.upper(),
        "tier": tier.id,
        "tier_nombre": tier.nombre,
        "lev_promedio": round(lev_p, 2),
        "margen_manto_pleno_usd": manto_pleno,
        "margen_manto_tier_usd": manto_tier,
        "equity_min_usd": equity_minima_recomendada(asset, tier_id=tid),
        "es_semilla": asset.upper() == str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH")).upper(),
    }


def tabla_flota_beru(activos: list[str] | None = None) -> list[dict[str, Any]]:
    catalogo = activos or list(getattr(config, "ACTIVOS_BERU_FLOTA", []) or [])
    tiers = list(beru_tier.BERU_TIERS.keys())
    out: list[dict[str, Any]] = []
    for a in catalogo:
        for tid in tiers:
            out.append(fila_capital(a, tid))
    return out


def resumen_capital() -> dict[str, Any]:
    semilla = str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH")).upper()
    tier_id = str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))
    tier = beru_tier.tier_por_id(tier_id)
    ini = fila_capital(semilla, tier_id)
    return {
        "activo_semilla": semilla,
        "tier_activo": tier_id,
        "modo_combate_default": beru_tier.modo_combate_default(),
        "pnl_objetivo_1pct_usd": float(getattr(config, "BERU_PNL_OBJETIVO_POR_1PCT_USD", 50.0)),
        "semilla": ini,
        "tiers": beru_tier.resumen_tiers(),
        "flota_por_tier": [fila_capital(semilla, t) for t in beru_tier.BERU_TIERS],
        "capitanes": {
            "ansiedad_vacio_pct": float(getattr(config, "BERU_VACIO_ANSIEDAD", 0.012)) * 100,
            "normal_vacio_pct": float(getattr(config, "BERU_VACIO_NORMAL", 0.016)) * 100,
        },
    }


def construir_greed_leverage_por_frente() -> dict[str, float]:
    out: dict[str, float] = {}
    activos = set(getattr(config, "MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET", {}) or {})
    activos |= set(getattr(config, "MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET", {}) or {})
    for a in activos:
        out[f"{a}USDT_LINEAL"] = apalancamiento_linear_max(a)
        out[f"{a}USDC_LINEAL"] = apalancamiento_linear_max(a)
        out[f"{a}USD_INVERSE"] = apalancamiento_inverse_max(a)
    return out
