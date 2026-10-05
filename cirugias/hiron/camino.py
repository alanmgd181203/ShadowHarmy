"""Paso 7 en seco. El cazador vivo no lee esto.

Aquí no hay una regla nueva. Junta las que ya estaban y mira
si, puestas en orden, hacen lo que cada una decía sola.

El cierre de Hiron solo vale si el viaje sigue vivo y el precio
quieto es el de este viaje. Un guardián viejo no cierra la bolsa nueva.
"""
from __future__ import annotations

from cirugias.hiron.guardian import Hiron
from cirugias.hiron.masacre_precio import Sello
from cirugias.hiron.viaje import Viaje


def cierre(guardian: Hiron, viaje: Viaje, sello: Sello) -> float | None:
    """Monedas de este viaje, si Hiron ya tocó y el sello es el suyo.

    None si el viaje murió, si el sello es de otro viaje, o si todavía
    no tocó. No devuelve cero para decir «no toques»: cero es bolsa vacía.
    """
    if not viaje.vivo():
        return None
    if guardian.lado != viaje.lado:
        return None
    precio = sello.precio(viaje.lado)
    if precio is None or guardian.meta <= 0:
        return None
    if abs(guardian.meta - float(precio)) > float(precio) * 1e-9:
        return None
    return guardian.a_cerrar(viaje.cantidad)
