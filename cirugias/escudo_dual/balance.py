"""Cuánto entra de verdad. El escudo vivo no lee esto.

La relación se redondea a la décima. No se le resta y no se
la obliga a uno.

Si la cubierta se quedó corta, el faltante entra en el momento.
Si sobra, no se corta. Al engordar, ese sobrante ya cuenta:
solo entra lo que todavía falte.
"""
from __future__ import annotations

_EPS = 1e-9


def redondear(relacion: float | None) -> float | None:
    """A la décima. 1,63 se queda en 1,6. No pasa a 1,4 ni a 1."""
    if relacion is None:
        return None
    r = float(relacion)
    if r <= _EPS:
        return None
    return round(r, 1)


def faltante(cubierta: float, meta: float) -> float:
    """Lo que falta para la meta. Cero si ya se pasó."""
    return max(0.0, float(meta or 0) - float(cubierta or 0))


def cuanto_entra(pedido: float, cubierta: float, meta: float) -> float:
    """El engorde, ya descontado el sobrante. Nunca más que el pedido."""
    pedido_f = max(0.0, float(pedido or 0))
    sobra = max(0.0, float(cubierta or 0) - float(meta or 0))
    return max(0.0, pedido_f - sobra)
