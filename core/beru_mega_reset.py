"""Reset Mega Beru — toque de red: nuevo 0 de precio + semilla con masa 0."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.models import BeruShip
    from generales.capitanes import ADN_Capitan


def crear_semilla_reinicio(
    precio_nuevo_0: float,
    *,
    direccion: str,
    tier_id: str,
    adn_capitan: ADN_Capitan,
    generacion: int,
    uid: str,
) -> BeruShip:
    """Beru nuevo en el 0 recalibrado; capital 0 — pide reserva a Tusk al gatillar."""
    from core.models import BeruShip

    return BeruShip(
        uid=uid,
        centro_local=precio_nuevo_0,
        centro_manto=precio_nuevo_0,
        masa=0.0,
        direccion=direccion,
        estado="ACECHANDO",
        generacion=generacion,
        adn_capitan=adn_capitan,
        tier_id=tier_id,
        modo_combate="CAZA",
        ciclo_infinito=False,
        neg_post_cazador=False,
        es_super_beru=False,
        masa_congelada=0.0,
    )


def debe_resetear_por_red(beru: BeruShip) -> bool:
    """Solo Mega Beru negociando con red activa dispara reset (no flip normal)."""
    return (
        bool(getattr(beru, "es_super_beru", False))
        and getattr(beru, "ciclo_infinito", False)
        and beru.estado == "NEGOCIANDO"
        and str(getattr(beru, "modo_combate", "")).upper() == "NEGOCIADOR"
        and float(getattr(beru, "neg_red_pct", 0) or 0) != 0.0
    )
