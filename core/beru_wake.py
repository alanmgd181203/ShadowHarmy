"""Beru wake — reset-0 al despertar (ley Monarca 2026-08-11).

Como un Mega-reset de ciclo: el 0 = precio del momento del wake.
Flota (no solo ETH) · Capitán Normal 1,6 % · manos aparte (BERU_MANOS).
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core.models import BeruShip


def wake_reset_0_activo() -> bool:
    return bool(getattr(config, "BERU_WAKE_RESET_0", True))


def manos_beru_activas() -> bool:
    """Órdenes spot reales solo si BERU_MANOS=true (default OFF = cableado dormido)."""
    return bool(getattr(config, "BERU_MANOS", False))


def manos_fantasma_activas() -> bool:
    """Nivel 2: registra disparos sin place_order (BERU_MANOS_FANTASMA)."""
    return bool(getattr(config, "BERU_MANOS_FANTASMA", False))


def ensayo_nivel3_activo() -> bool:
    """Nivel 3: manos chiquitas reales con techos (BERU_ENSAYO_NIVEL3)."""
    return bool(getattr(config, "BERU_ENSAYO_NIVEL3", False))


def siembra_sin_candado_pase() -> bool:
    """Fantasma o ensayo nivel 3: Santos elegidos sin esperar sellos Igris."""
    return manos_fantasma_activas() or ensayo_nivel3_activo()


def siembra_flota_activa() -> bool:
    return bool(getattr(config, "BERU_SIEMBRA_FLOTA", True))


def adn_capitan_wake():
    """Wake fuerza Normal 1,6 % — no Ansiedad 1,2 %."""
    from generales.capitanes import CapitanAnsiedad, CapitanNormal

    modo = str(getattr(config, "BERU_CAPITAN_WAKE", "NORMAL") or "NORMAL").upper()
    if modo in ("ANSIEDAD", "ANXIETY", "1.2", "012"):
        return CapitanAnsiedad
    return CapitanNormal


def vacio_wake_pct() -> float:
    adn = adn_capitan_wake()
    return float(getattr(adn, "vacio_adan", 0.016) or 0.016)


def centros_al_wake(precio_actual: float) -> tuple[float, float]:
    """(centro_local, centro_manto) — ambos = precio si reset-0; si no, manto queda 0 (rellena Tusk)."""
    px = float(precio_actual or 0.0)
    if px <= 0:
        return 0.0, 0.0
    if wake_reset_0_activo():
        return px, px
    return px, 0.0


def catalogo_flota() -> list[str]:
    raw = getattr(config, "ACTIVOS_BERU_FLOTA", None) or []
    out: list[str] = []
    for a in raw:
        u = str(a or "").upper().strip()
        if u and u not in out:
            out.append(u)
    if not out:
        out = [str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH") or "ETH").upper()]
    return out


def activos_siembra_permitidos(
    equity_usd: float,
    *,
    pasos_logrados: list[int] | None = None,
    exigir_candado: bool = True,
) -> list[str]:
    """Santos de la flota donde Beru puede nacer (candado pase si director on).

    Fantasma / ensayo nivel 3: sin candado de pasos — Santos elegidos aunque
    el libro de progreso no marque Mariscal sellado.
    """
    from core import pase_director as pd

    flota = catalogo_flota()
    if siembra_sin_candado_pase():
        return list(flota)
    if not exigir_candado or not pd.director_activo():
        return list(flota)
    ok: list[str] = []
    for act in flota:
        if pd.beru_puede_cazar(act, float(equity_usd), pasos_logrados=pasos_logrados):
            ok.append(act)
    return ok


def crear_semilla_wake(
    activo: str,
    precio_nuevo_0: float,
    *,
    tier_id: str | None = None,
    generacion: int = 1,
    uid: str | None = None,
) -> BeruShip:
    """Semilla post-ciclo: masa 0, ACECHANDO, 0 = precio wake (ambos centros)."""
    act = str(activo or "").upper()
    cl, cm = centros_al_wake(precio_nuevo_0)
    if cm <= 0 and cl > 0:
        # sin flag reset-0: local=precio; manto lo rellena el cazador desde Tusk
        cm = 0.0
    adn = adn_capitan_wake()
    tid = str(tier_id or getattr(config, "BERU_TIER_DEFAULT", "PROTO1") or "PROTO1")
    uid_f = uid or f"BERU_SEM_{act}_{time.time_ns()}"
    return BeruShip(
        uid=uid_f,
        centro_local=cl,
        centro_manto=cm if cm > 0 else cl,  # si reset-0 off y cm=0, al menos local; plantador puede override
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        generacion=int(generacion),
        adn_capitan=adn,
        tier_id=tid,
        modo_combate=str(getattr(config, "BERU_MODO_COMBATE_DEFAULT", "NEGOCIADOR") or "NEGOCIADOR"),
        ciclo_infinito=False,
        neg_post_cazador=False,
        es_super_beru=False,
        masa_congelada=0.0,
    )


def aplicar_centro_manto_wake(semilla: BeruShip, precio_actual: float, tusk_centro: float = 0.0) -> BeruShip:
    """Ajusta centros tras crear: reset-0 → precio; si no → Tusk si hay."""
    cl, cm = centros_al_wake(precio_actual)
    semilla.centro_local = cl
    if wake_reset_0_activo():
        semilla.centro_manto = cm
    else:
        semilla.centro_manto = float(tusk_centro or 0.0) or cl
    return semilla


def resumen_cableado() -> dict[str, Any]:
    from core import beru_ley
    from core import beru_fantasma
    from core import beru_ensayo

    base = {
        "wake_reset_0": wake_reset_0_activo(),
        "siembra_flota": siembra_flota_activa(),
        "capitan_wake": str(getattr(config, "BERU_CAPITAN_WAKE", "NORMAL")),
        "vacio_pct": round(vacio_wake_pct() * 100, 4),
        "manos": manos_beru_activas(),
        "manos_fantasma": manos_fantasma_activas(),
        "ensayo_nivel3": ensayo_nivel3_activo(),
        "hilo_enabled": bool(getattr(config, "BERU_HILO_ENABLED", False)),
        "n_flota_catalogo": len(catalogo_flota()),
    }
    base.update(beru_ley.resumen_ley())
    if manos_fantasma_activas():
        base.update(beru_fantasma.resumen_modo())
    if ensayo_nivel3_activo():
        base.update(beru_ensayo.resumen_modo())
    return base
