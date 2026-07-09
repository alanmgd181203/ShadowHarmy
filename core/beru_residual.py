"""Red residual — memoria de clonación tras cosecha en La Hoz."""
from __future__ import annotations

from dataclasses import dataclass

from core import beru_cazador


@dataclass
class RedResidual:
    """Red flotante que dispara Capa N+1 al ser tocada por el precio."""
    precio: float
    direccion: str
    centro_manto: float
    tier_id: str
    capa_origen: int
    activa: bool = True


def registrar_desde_barco(beru, red_precio: float) -> RedResidual | None:
    if red_precio <= 0:
        return None
    return RedResidual(
        precio=red_precio,
        direccion=beru.direccion,
        centro_manto=float(getattr(beru, "centro_manto", 0) or 0),
        tier_id=str(getattr(beru, "tier_id", "") or ""),
        capa_origen=int(getattr(beru, "capa", 1) or 1),
    )


def toca_residual(precio: float, residual: RedResidual) -> bool:
    if not residual.activa or residual.precio <= 0:
        return False
    return beru_cazador.toca_red(precio, residual.direccion, residual.precio)
