"""Beru wake — semilla cazadora continua.

El wake fija el 0 local con el precio del momento. El plantador hidrata el
metro (0 del manto) desde el promedio L+S de Igris. Capitán Normal / Vacío
de Adán 1,1 % · manos aparte (BERU_MANOS).
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core.models import BeruShip


def wake_reset_0_activo() -> bool:
    return False


def manos_beru_activas() -> bool:
    """Órdenes spot reales solo si BERU_MANOS=true (default OFF = cableado dormido)."""
    return bool(getattr(config, "BERU_MANOS", False))


def manos_fantasma_activas() -> bool:
    """Nivel 2: registra disparos sin place_order (BERU_MANOS_FANTASMA)."""
    return bool(getattr(config, "BERU_MANOS_FANTASMA", False))


def _lista_activos(raw: str) -> list[str]:
    out: list[str] = []
    for part in str(raw or "").split(","):
        u = part.strip().upper()
        if u and u not in out:
            out.append(u)
    return out


def activos_manos_reales() -> list[str]:
    """Santos con Hoz en Bybit. Vacío = ley global (todos o ninguno)."""
    return _lista_activos(getattr(config, "BERU_MANOS_ACTIVOS", "") or "")


def manos_reales_de_activo(activo: str) -> bool:
    """¿Este Santo planta carta real? El resto puede seguir en fantasma."""
    if not manos_beru_activas():
        return False
    act = str(activo or "").upper()
    if not act:
        return False
    listed = activos_manos_reales()
    if listed:
        return act in listed
    return not manos_fantasma_activas()


def tier_manos_exigido(activo: str) -> str | None:
    """Uniforme mínimo al nacer con manos reales. AUTO/vacío = el manto dicta."""
    act = str(activo or "").upper()
    if act not in activos_manos_reales():
        return None
    tid = str(getattr(config, "BERU_MANOS_EXIGIR_TIER", "") or "").upper().strip()
    if tid in ("", "NONE", "AUTO", "NO", "OFF"):
        return None
    return tid


def ensayo_nivel3_activo() -> bool:
    """Nivel 3: manos chiquitas reales con techos (BERU_ENSAYO_NIVEL3)."""
    return bool(getattr(config, "BERU_ENSAYO_NIVEL3", False))


def siembra_sin_candado_pase() -> bool:
    """Fantasma o ensayo nivel 3: Santos elegidos sin esperar sellos Igris."""
    return manos_fantasma_activas() or ensayo_nivel3_activo()


def siembra_flota_activa() -> bool:
    return bool(getattr(config, "BERU_SIEMBRA_FLOTA", True))


def adn_capitan_wake():
    """Wake fuerza Normal 1,1 % — no Ansiedad 1,2 %."""
    from generales.capitanes import CapitanAnsiedad, CapitanNormal

    modo = str(getattr(config, "BERU_CAPITAN_WAKE", "NORMAL") or "NORMAL").upper()
    if modo in ("ANSIEDAD", "ANXIETY", "1.2", "012"):
        return CapitanAnsiedad
    return CapitanNormal


def vacio_wake_pct() -> float:
    adn = adn_capitan_wake()
    return float(getattr(adn, "vacio_adan", 0.011) or 0.011)


def centros_al_wake(precio_actual: float) -> tuple[float, float]:
    """0 local = spot de wake; el manto lo rellena el plantador desde Tusk."""
    px = float(precio_actual or 0.0)
    if px <= 0:
        return 0.0, 0.0
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
    tusk=None,
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
        if pd.beru_puede_cazar(
            act,
            float(equity_usd),
            pasos_logrados=pasos_logrados,
            tusk=tusk,
        ):
            ok.append(act)
    return ok


def tier_siembra_activo(
    activo: str,
    *,
    tusk=None,
    pasos_logrados: list[int] | None = None,
) -> str | None:
    """Uniforme del Beru según el mayor grado sostenido por su manto."""
    from core import beru_capital as bc
    from core import pase_director as pd

    if (
        siembra_sin_candado_pase()
        or not pd.director_activo()
        or getattr(config, "LIVE_BERU_TESTNET", False)
    ):
        grado = None
        if tusk is not None:
            grado = pd.grado_beru_para_caza(
                activo,
                tusk=tusk,
                pasos_logrados=pasos_logrados,
            )
        if grado:
            return bc.tier_id_desde_grado(grado)
        return str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1") or "PROTO1").upper()
    grado = pd.grado_beru_para_caza(
        activo,
        tusk=tusk,
        pasos_logrados=pasos_logrados,
    )
    return bc.tier_id_desde_grado(grado) if grado else None


def crear_semilla_wake(
    activo: str,
    precio_nuevo_0: float,
    *,
    tier_id: str | None = None,
    generacion: int = 1,
    uid: str | None = None,
) -> BeruShip:
    """Semilla continua: masa 0; 0 local = wake; el metro Igris lo inyecta el plantador."""
    act = str(activo or "").upper()
    cl, cm = centros_al_wake(precio_nuevo_0)
    adn = adn_capitan_wake()
    tid = str(tier_id or getattr(config, "BERU_TIER_DEFAULT", "PROTO1") or "PROTO1")
    uid_f = uid or f"BERU_SEM_{act}_{time.time_ns()}"
    return BeruShip(
        uid=uid_f,
        centro_local=cl,
        centro_manto=cm,
        ancla_tramo=cl,
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        generacion=int(generacion),
        adn_capitan=adn,
        tier_id=tid,
        modo_combate="CAZA",
        ciclo_infinito=False,
        neg_post_cazador=False,
        es_super_beru=False,
        masa_congelada=0.0,
        sangre_vista_dentro=True,
    )


def aplicar_centro_manto_wake(semilla: BeruShip, precio_actual: float, tusk_centro: float = 0.0) -> BeruShip:
    """Metro = Tusk. 0 local de acecho = precio de wake. Sin manto no hay semilla."""
    px = float(precio_actual or 0.0)
    centro = float(tusk_centro or 0.0)
    semilla.centro_manto = centro
    if px > 0:
        semilla.centro_local = px
        semilla.ancla_tramo = px
    semilla.sangre_vista_dentro = True
    return semilla


def manto_bellion_usable(tusk, activo: str) -> bool:
    """¿Hay metro L+S en Bellion/Tusk para sembrar sin reconcile live?"""
    from core import beru_cazador as bc

    return bc.manto_vivo(tusk, activo)


def resumen_cableado() -> dict[str, Any]:
    from core import beru_ley
    from core import beru_fantasma
    from core import beru_ensayo

    base = {
        "wake_reset_0": wake_reset_0_activo(),
        "siembra_flota": siembra_flota_activa(),
        "capitan_wake": str(getattr(config, "BERU_CAPITAN_WAKE", "NORMAL")),
        "vacio_pct": round(vacio_wake_pct() * 100, 4),
        "sangre_pct": round(float(
            getattr(config, "BERU_LLAMADO_SANGRE_PCT", 0.011) or 0.011
        ) * 100, 4),
        "manos": manos_beru_activas(),
        "manos_fantasma": manos_fantasma_activas(),
        "manos_activos": activos_manos_reales(),
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
