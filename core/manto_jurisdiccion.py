"""Jurisdicción del manto — Igris orquesta, Greed ejecuta (doctrina Monarca 2026-07-11)."""
from __future__ import annotations

from typing import Any

import core.config as config

ORDEN_RESTAURAR_MANTO = "RESTAURAR_MANTO"
ORDEN_PODA_EMERGENCIA = "PODA_EMERGENCIA"


def piso_ideal() -> float:
    return float(getattr(config, "RANGO_PISO_IDEAL", 85.0))


def techo_ideal() -> float:
    return float(getattr(config, "RANGO_OBJETIVO_MARGEN", 90.0))


def muro_marcial() -> float:
    return float(getattr(config, "MURO_LEY_MARCIAL", 95.0))


def en_zona_ideal(margen_pct: float) -> bool:
    return piso_ideal() <= float(margen_pct) <= techo_ideal()


def bajo_piso(margen_pct: float) -> bool:
    return float(margen_pct) < piso_ideal()


def sobre_muro(margen_pct: float) -> bool:
    return float(margen_pct) >= muro_marcial()


def greed_es_ejecutor() -> bool:
    return bool(getattr(config, "GREED_MANTO_EJECUTOR", True))


def igris_yield_activo() -> bool:
    return bool(getattr(config, "IGRIS_YIELD_EN_ZONA_IDEAL", True))


def asegurar_cola(tusk) -> list:
    cola = getattr(tusk, "cola_ordenes_manto", None)
    if cola is None:
        tusk.cola_ordenes_manto = []
        cola = tusk.cola_ordenes_manto
    return cola


def emitir_orden_manto(tusk, tipo: str, **payload) -> dict[str, Any]:
    """Igris → Greed: orden interna (no toca el exchange)."""
    orden = {"tipo": tipo, "ts": __import__("time").time(), **payload}
    asegurar_cola(tusk).append(orden)
    return orden


def consumir_ordenes_manto(tusk) -> list[dict[str, Any]]:
    cola = asegurar_cola(tusk)
    out = list(cola)
    cola.clear()
    return out
