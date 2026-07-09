"""Igris — métricas y fase del manto (doctrina 21 §A)."""
from __future__ import annotations

from typing import Any

import core.config as config
from core.kaiser_indicators import interpretar_funding


def fase_margen(margen_pct: float) -> str:
    """Zona operativa según doctrina Monarca (21 §A)."""
    m = float(margen_pct)
    ley = float(getattr(config, "MURO_LEY_MARCIAL", 95.0))
    limpieza = float(getattr(config, "RANGO_LIMPIEZA_MAX", 93.0))
    objetivo = float(getattr(config, "RANGO_OBJETIVO_MARGEN", 90.0))
    piso = float(getattr(config, "RANGO_PISO_IDEAL", 85.0))
    expansion = float(getattr(config, "RANGO_EXPANSION_MIN", 80.0))

    if m >= ley:
        return "LEY_MARCIAL"
    if m > limpieza:
        return "PRE_PODA"
    if m >= objetivo:
        return "ALTA_PRESION"
    if m >= piso:
        return "IDEAL"
    if m >= expansion:
        return "TERRENO_CAZA"
    return "EXPANSION"


def delta_en_banda(ratio_long: float, banda_min: float, banda_max: float) -> bool:
    return float(banda_min) <= float(ratio_long) <= float(banda_max)


def resumen_manto(
    *,
    margen_ocupado_pct: float,
    peso_long: float,
    peso_short: float,
    banda_min: float,
    banda_max: float,
) -> dict[str, Any]:
    masa = float(peso_long) + float(peso_short)
    ratio = (float(peso_long) / masa) if masa > 0 else 0.5
    fase = fase_margen(margen_ocupado_pct)
    en_banda = delta_en_banda(ratio, banda_min, banda_max)
    accion_sugerida = _accion_heuristica(fase, masa, en_banda, peso_long, peso_short)
    return {
        "fase_margen": fase,
        "masa_bruta": round(masa, 6),
        "ratio_long": round(ratio, 4),
        "delta_en_banda": en_banda,
        "banda_min": banda_min,
        "banda_max": banda_max,
        "accion_heuristica": accion_sugerida,
        "umbrales": {
            "expansion_max": float(getattr(config, "RANGO_EXPANSION_MIN", 80.0)),
            "piso_ideal": float(getattr(config, "RANGO_PISO_IDEAL", 85.0)),
            "objetivo_margen": float(getattr(config, "RANGO_OBJETIVO_MARGEN", 90.0)),
            "limpieza_desde": float(getattr(config, "RANGO_LIMPIEZA_MAX", 93.0)),
            "ley_marcial_desde": float(getattr(config, "MURO_LEY_MARCIAL", 95.0)),
        },
        "frentes_manto": list(getattr(config, "FRENTES_MANTO_ALL", []) or []),
    }


def _accion_heuristica(
    fase: str,
    masa_bruta: float,
    en_banda: bool,
    peso_l: float,
    peso_s: float,
) -> str:
    if fase == "LEY_MARCIAL":
        return "PODAR_MANTO"
    if fase == "PRE_PODA" and peso_l > 0 and peso_s > 0:
        return "LIMPIAR_ESPEJOS"
    if masa_bruta <= 0 and fase in ("EXPANSION", "TERRENO_CAZA"):
        return "BOOTSTRAP_MANTO"
    if not en_banda and masa_bruta > 0:
        return "REBALANCEO_IGRIS"
    if fase == "EXPANSION":
        return "ENGORDAR_MANTO"
    if fase in ("ALTA_PRESION", "IDEAL", "TERRENO_CAZA"):
        return "VIGILAR_GREED"
    return "VIGILAR"


def funding_vigilancia(snapshot_funding: dict | None) -> list[dict[str, Any]]:
    """Lectura pasiva Kaiser/Tank — log y panel; sin maniobra automática."""
    out: list[dict[str, Any]] = []
    for alerta in interpretar_funding(snapshot_funding or {}):
        if "IGRIS" not in (alerta.get("destinatarios") or []):
            continue
        out.append({
            "tipo": alerta.get("tipo"),
            "base": alerta.get("base"),
            "mensaje": alerta.get("mensaje"),
            "severidad": alerta.get("severidad"),
        })
    return out
