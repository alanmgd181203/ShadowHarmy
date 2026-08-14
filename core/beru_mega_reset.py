"""Mega Beru — purga de negociadores atrasados. NO mueve el 0 del manto.

El 0 absoluto es el que plantó Igris. Beru siempre mide % contra ese centro.
Tras Mega: limpia / suelta masa · nace cazador que acecha sangre en
(pct_purga ± 0.9%) sobre el MISMO centro_manto — nunca rebasea a +0.9% local.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from core import beru_cazador

if TYPE_CHECKING:
    from core.models import BeruShip
    from generales.capitanes import ADN_Capitan


def crear_semilla_post_purga(
    centro_manto_igris: float,
    *,
    pct_purga: float,
    direccion: str,
    tier_id: str,
    adn_capitan: ADN_Capitan,
    generacion: int,
    uid: str,
) -> BeruShip:
    """Semilla post-Mega: mismo 0 de Igris; sangre en |pct_purga|+0.9% absoluto."""
    from core.models import BeruShip

    signo = 1 if pct_purga >= 0 else -1
    if pct_purga == 0:
        signo = 1 if direccion == "SHORT" else -1
    piso = signo * (abs(pct_purga) + beru_cazador.llamado_sangre_pct())

    return BeruShip(
        uid=uid,
        centro_local=centro_manto_igris,
        centro_manto=centro_manto_igris,  # NUNCA precio vivo
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
        piso_sangre_pct=piso,
    )


def crear_semilla_reinicio(
    precio_o_centro: float,
    *,
    direccion: str,
    tier_id: str,
    adn_capitan: ADN_Capitan,
    generacion: int,
    uid: str,
    pct_purga: float = 0.0,
    centro_manto_igris: float | None = None,
) -> BeruShip:
    """Compat: si pasan centro_manto_igris, no rebasea el 0."""
    centro = float(centro_manto_igris) if centro_manto_igris and centro_manto_igris > 0 else float(precio_o_centro)
    # Si solo pasan precio vivo sin centro igris, aún así NO usar precio como 0 nuevo:
    # pct_purga debe venir; centro debe ser el manto. Legacy smoke: centro=precio → documentar.
    return crear_semilla_post_purga(
        centro,
        pct_purga=pct_purga,
        direccion=direccion,
        tier_id=tier_id,
        adn_capitan=adn_capitan,
        generacion=generacion,
        uid=uid,
    )


def debe_purgar_mega(beru: BeruShip) -> bool:
    """Mega terminó trailing → purga (no nuevo 0)."""
    return (
        bool(getattr(beru, "es_super_beru", False))
        and beru.estado == "NEGOCIANDO"
        and str(getattr(beru, "modo_combate", "")).upper() == "NEGOCIADOR"
        and float(getattr(beru, "neg_oz_pct", 0) or 0) != 0.0
    )


def debe_resetear_por_negociacion_mega(beru: BeruShip) -> bool:
    return debe_purgar_mega(beru)


def debe_resetear_por_red(beru: BeruShip) -> bool:
    return debe_purgar_mega(beru)


def sangre_abs_desde_purga(pct_purga: float) -> float:
    """Ej.: purga +30% → sangre +30.9% sobre el 0 de Igris."""
    signo = 1 if pct_purga >= 0 else -1
    if pct_purga == 0:
        return beru_cazador.llamado_sangre_pct()
    return signo * (abs(pct_purga) + beru_cazador.llamado_sangre_pct())
