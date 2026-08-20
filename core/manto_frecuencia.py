"""Igris de baja — stub vacío para módulos marcha legacy."""
from __future__ import annotations

EDGE_MANTO = "lineal_vs_inverse"
PLAZOS_S = (3 * 86400, 30 * 86400, 365 * 86400)


def fees_be_activo(activo: str) -> float:
    _ = activo
    return 0.11


def eta_despliegue_horas(*args, **kwargs) -> float:
    _ = args, kwargs
    return 0.0


def snapshot_ranking(**kwargs) -> dict:
    _ = kwargs
    return {"de_baja": True, "filas": []}
