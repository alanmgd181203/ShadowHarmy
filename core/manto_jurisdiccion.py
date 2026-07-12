"""Jurisdicción del manto — Igris gobierna L/S de principio a fin (doctrina 2026-07-12).

Greed ya no ejecuta ni vigila el escudo. Horizonte operativo = muro 95%
(reserva oxígeno 5% vía MONARCA_RESERVA_PCT / colchón Tusk).
"""
from __future__ import annotations

from typing import Any

import core.config as config

# Legacy order types — conservados por compat lectura; Igris ya no emite a Greed
ORDEN_RESTAURAR_MANTO = "RESTAURAR_MANTO"
ORDEN_PODA_EMERGENCIA = "PODA_EMERGENCIA"


def piso_ideal() -> float:
    """Bajo este margen Igris sigue desplegando (ahora alineado al muro 95%)."""
    return float(getattr(config, "RANGO_PISO_IDEAL", 95.0))


def techo_ideal() -> float:
    return float(getattr(config, "RANGO_OBJETIVO_MARGEN", 95.0))


def muro_marcial() -> float:
    return float(getattr(config, "MURO_LEY_MARCIAL", 95.0))


def en_zona_ideal(margen_pct: float) -> bool:
    """Zona alta: cerca del muro sin excederlo (oxígeno ≥5%)."""
    m = float(margen_pct)
    techo = techo_ideal()
    return (techo - 2.0) <= m < muro_marcial()


def bajo_piso(margen_pct: float) -> bool:
    return float(margen_pct) < piso_ideal()


def sobre_muro(margen_pct: float) -> bool:
    return float(margen_pct) >= muro_marcial()


def greed_es_ejecutor() -> bool:
    """Doctrina 2026-07-12: Greed fuera del manto."""
    return False


def igris_yield_activo() -> bool:
    """Doctrina 2026-07-12: sin traspaso de mando."""
    return False


def asegurar_cola(tusk) -> list:
    cola = getattr(tusk, "cola_ordenes_manto", None)
    if cola is None:
        tusk.cola_ordenes_manto = []
        cola = tusk.cola_ordenes_manto
    return cola


def emitir_orden_manto(tusk, tipo: str, **payload) -> dict[str, Any]:
    """Deprecated — Greed ya no consume órdenes de manto. No-op seguro."""
    return {"tipo": tipo, "ts": __import__("time").time(), "ignorada": True, **payload}


def consumir_ordenes_manto(tusk) -> list[dict[str, Any]]:
    """Deprecated — vacía cola residual sin ejecutar."""
    cola = asegurar_cola(tusk)
    out = list(cola)
    cola.clear()
    return out
