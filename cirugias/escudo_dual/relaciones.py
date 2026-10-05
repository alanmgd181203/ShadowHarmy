"""Las dos relaciones. Paso 1. El escudo vivo no lee esto.

La marea es una: las altcoins, sin el rey y sin la reina.
Se compara con cada metal por separado.

La relación es cuánto se sacude la marea partido por cuánto se
sacude el metal. La más chica pide menos capa, porque el metal
pega más fuerte. No quiere decir que se parezca más.

No se restan las sacudidas. No se aprieta a uno. Si no hay
datos, no habla: no se inventa un uno a uno.
"""
from __future__ import annotations

from typing import Sequence

_EPS = 1e-12


def relacion(marea: Sequence[float], metal: Sequence[float]) -> float | None:
    """Sacudida de la marea / sacudida del metal. None si no se puede medir."""
    if not marea or not metal:
        return None
    niveles_marea, niveles_metal = _mismo_tramo(marea, metal)
    saltos_marea = _saltos(niveles_marea)
    saltos_metal = _saltos(niveles_metal)
    saltos_marea, saltos_metal = _mismo_tramo(saltos_marea, saltos_metal)
    if len(saltos_marea) < 2 or len(saltos_metal) < 2:
        return None
    sacudida_metal = _sacudida(saltos_metal)
    if sacudida_metal <= _EPS:
        return None
    return _sacudida(saltos_marea) / sacudida_metal


def las_dos(
    marea: Sequence[float],
    rey: Sequence[float],
    reina: Sequence[float],
) -> dict[str, float | None]:
    """Cada metal contra la misma marea. Uno puede callar y el otro no."""
    return {
        "rey": relacion(marea, rey),
        "reina": relacion(marea, reina),
    }


def _mismo_tramo(
    a: Sequence[float], b: Sequence[float]
) -> tuple[list[float], list[float]]:
    n = min(len(a), len(b))
    return list(a)[-n:], list(b)[-n:]


def _saltos(niveles: Sequence[float]) -> list[float]:
    """De un precio al siguiente. Un precio muerto o vacío no entra."""
    out: list[float] = []
    for i in range(1, len(niveles)):
        antes = float(niveles[i - 1])
        ahora = float(niveles[i])
        if antes <= 0 or ahora <= 0:
            continue
        out.append((ahora / antes) - 1.0)
    return out


def _sacudida(saltos: Sequence[float]) -> float:
    """Qué tan bravos fueron los saltos. Con menos de dos, no hay medida."""
    n = len(saltos)
    if n < 2:
        return 0.0
    media = sum(saltos) / n
    var = sum((x - media) ** 2 for x in saltos) / (n - 1)
    if var <= 0:
        return 0.0
    return var ** 0.5
