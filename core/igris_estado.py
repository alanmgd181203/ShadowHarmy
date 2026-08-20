"""Compatibilidad — Igris de baja. Resumen vacío / funding lectura."""
from __future__ import annotations

from typing import Any


def funding_vigilancia(funding_snap: dict | None) -> dict[str, Any]:
    top = list((funding_snap or {}).get("top") or [])
    extremo = top[0] if top else None
    return {
        "ok": True,
        "extremo": extremo,
        "n": len(top),
    }


def resumen_manto(
    *,
    margen_ocupado_pct: float = 0.0,
    peso_long: float = 0.0,
    peso_short: float = 0.0,
    banda_min: float = 0.0,
    banda_max: float = 0.0,
) -> dict[str, Any]:
    return {
        "de_baja": True,
        "margen_ocupado_pct": float(margen_ocupado_pct or 0),
        "peso_long": float(peso_long or 0),
        "peso_short": float(peso_short or 0),
        "banda_min": float(banda_min or 0),
        "banda_max": float(banda_max or 0),
        "estado": "IGRIS_DE_BAJA",
    }
