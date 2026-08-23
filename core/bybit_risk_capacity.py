"""Bybit risk tiers — leverage útil que sí soporta el manto objetivo.

``maxLeverage`` del catálogo solo describe el primer tier. No garantiza que
ese leverage admita el nocional completo de una pierna. Esta capa selecciona
el mayor leverage cuyo ``riskLimitValue`` conserva holgura para la meta.
"""
from __future__ import annotations

from typing import Any, Iterable


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def normalizar_tiers(
    rows: Iterable[dict[str, Any]] | None,
    *,
    capacity_multiplier: float = 1.0,
) -> list[dict[str, float | int]]:
    """Limpia tiers y convierte su límite a USD.

    En lineales, ``riskLimitValue`` ya está en USDT. En inversos está en la
    moneda base (BTC, ETH, MNT...), así que se multiplica por el last price.
    """
    out: list[dict[str, float | int]] = []
    multiplier = max(0.0, _float(capacity_multiplier))
    for row in rows or []:
        leverage = _float(row.get("maxLeverage"))
        capacidad_nativa = _float(row.get("riskLimitValue"))
        if leverage <= 0 or capacidad_nativa <= 0 or multiplier <= 0:
            continue
        try:
            tier_id = int(row.get("id") or 0)
        except (TypeError, ValueError):
            tier_id = 0
        out.append({
            "id": tier_id,
            "max_leverage": leverage,
            "risk_limit_native": capacidad_nativa,
            "risk_limit_usd": capacidad_nativa * multiplier,
        })
    return sorted(
        out,
        key=lambda row: (-float(row["max_leverage"]), float(row["risk_limit_usd"])),
    )


def leverage_util_para_nocional(
    tiers: Iterable[dict[str, Any]] | None,
    nocional_objetivo_usd: float,
    *,
    headroom_pct: float = 0.80,
    capacity_multiplier: float = 1.0,
) -> dict[str, Any]:
    """Mayor leverage con capacidad holgada para una pierna completa.

    Ejemplo MNT inverso vivo (precio auditado ~$0.4327):
    - 50x: 5.000 MNT ≈ $2.163; no soporta la pierna Mariscal.
    - 40x: 25.000 MNT ≈ $10.817; sí la soporta con 20% de aire.
    """
    objetivo = max(0.0, _float(nocional_objetivo_usd))
    headroom = min(1.0, max(0.01, _float(headroom_pct)))
    clean = normalizar_tiers(tiers, capacity_multiplier=capacity_multiplier)
    for tier in clean:
        limite = float(tier["risk_limit_usd"])
        capacidad_segura = limite * headroom
        if capacidad_segura + 1e-9 >= objetivo:
            return {
                "ok": True,
                "leverage_util": float(tier["max_leverage"]),
                "tier_id": int(tier["id"]),
                "risk_limit_usd": limite,
                "risk_limit_native": float(tier["risk_limit_native"]),
                "capacity_multiplier": max(0.0, _float(capacity_multiplier)),
                "capacidad_segura_usd": capacidad_segura,
                "nocional_objetivo_usd": objetivo,
                "headroom_pct": headroom,
                "uso_risk_limit_pct": (objetivo / limite if limite > 0 else 0.0),
                "motivo": "tier_con_holgura",
            }
    return {
        "ok": False,
        "leverage_util": 0.0,
        "tier_id": None,
        "risk_limit_usd": 0.0,
        "risk_limit_native": 0.0,
        "capacity_multiplier": max(0.0, _float(capacity_multiplier)),
        "capacidad_segura_usd": 0.0,
        "nocional_objetivo_usd": objetivo,
        "headroom_pct": headroom,
        "uso_risk_limit_pct": None,
        "motivo": "ningun_tier_soporta_objetivo",
    }
