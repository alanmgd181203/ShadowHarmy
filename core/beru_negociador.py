"""Beru Negociador — ping-pong 2026-08-13 (cirugía acordeón OFF).

TODOS los grados:
  Tras Hoz del cazador → llamado del oro ±1.6% (SOLO detona).
  Al detonar → UNA trailing con toda la masa (sin acordeón).
  Al llenarse → oro al otro lado del vacío → otra trailing.
  Así hasta Mega / nuevo 0.

Cosechador ya no es vida aparte: es el mismo oficio.
Funeral entre orillas: holgado (1.6% de camino).
"""
from __future__ import annotations

from core import beru_cazador
import core.config as config

FaseNeg = str  # ESPERANDO_ORO | TRAILING_ACTIVA | PING_PONG


def vacio_adan_pct() -> float:
    return float(getattr(config, "BERU_VACIO_NORMAL", 0.016))


def abismo_salida_pct() -> float:
    return float(getattr(config, "BERU_ABISMO_SALIDA_PCT", vacio_adan_pct()))


def abismo_pct(vacio_adan: float | None = None) -> float:
    fijo = abismo_salida_pct()
    if fijo > 0:
        return fijo
    return float(vacio_adan or vacio_adan_pct())


def oz_condicional_pct(ancla_pct: float, vacio: float | None = None) -> float:
    """Llamado del oro: ancla ± 1.6% al otro lado del vacío."""
    abismo = abismo_pct(vacio)
    if ancla_pct > 0:
        return ancla_pct - abismo
    if ancla_pct < 0:
        return ancla_pct + abismo
    return -abismo


def oro_orilla_opuesta(fill_pct: float, vacio: float | None = None) -> float:
    """Tras fill de trailing: nuevo oro al otro lado (ping-pong)."""
    return oz_condicional_pct(fill_pct, vacio)


def paso_trailing_pct() -> float:
    return float(getattr(config, "BERU_NEG_PASO_OZ_PCT", beru_cazador.paso_pct()))


def pasos_negociador(tier_id: str | None = None) -> tuple[float, float]:
    """Compat: una sola trailing — oz y red el mismo paso (sin acordeón 0.05)."""
    _ = tier_id
    p = paso_trailing_pct()
    return p, p


def sincronizar_grid(centro: float, oz_pct: float, red_pct: float) -> tuple[float, float]:
    return beru_cazador.sincronizar_precios_grid(centro, oz_pct, red_pct)


def activar_trailing_unica(oro_pct: float, paso: float | None = None) -> tuple[float, float]:
    """Al detonar oro: UNA trailing en el nivel del oro (misma masa ya congelada).

    neg_oz = gatillo trailing; neg_red = 0 → no hay segunda carta / acordeón.
    """
    _ = paso
    return float(oro_pct), 0.0


def activar_primera_vez(oz_cond_pct: float, paso_oz: float) -> tuple[float, float]:
    """Alias: detonar oro → trailing única (acordeón extirpado)."""
    return activar_trailing_unica(oz_cond_pct, paso_oz)


def mover_trailing(trailing_pct: float, extremo_pct: float, paso: float | None = None) -> float:
    """Persigue el extremo a `paso` detrás (memoria; Bybit trailing = B-TRAIL)."""
    p = paso if paso is not None else paso_trailing_pct()
    if extremo_pct >= trailing_pct:
        # extremo más arriba / más positivo → trailing sube detrás
        return extremo_pct - p if extremo_pct > 0 else extremo_pct + p
    # extremo más abajo
    if extremo_pct < 0:
        return extremo_pct + p
    return extremo_pct - p


def avanzar_toque_oz(
    oz_pct: float,
    red_pct: float,
    paso_oz: float,
    paso_red: float,
) -> tuple[float, float]:
    """LEGADO acordeón — no usar. Ping-pong no avanza dos cartas."""
    _ = paso_red
    return activar_trailing_unica(oz_pct, paso_oz)


def resorte_sexto_toque(oz_pct: float, paso_oz: float) -> tuple[float, float]:
    """LEGADO — acordeón extirpado. Devuelve trailing única."""
    return activar_trailing_unica(oz_pct, paso_oz)


def toques_hasta_resorte() -> int:
    return 0  # sin acordeón


def es_sexto_toque(toques_ciclo: int) -> bool:
    _ = toques_ciclo
    return False


def toca_condicional(precio: float, centro: float, oz_cond_pct: float) -> bool:
    p_oz = beru_cazador.precio_desde_pct(centro, oz_cond_pct)
    if oz_cond_pct < 0:
        return precio <= p_oz + 1e-9
    return precio >= p_oz - 1e-9


def toca_trailing(precio: float, centro: float, trailing_pct: float) -> bool:
    """Fill de la única trailing (negociación de esa orilla cerrada)."""
    return toca_condicional(precio, centro, trailing_pct)


def toca_red_negociador(precio: float, centro: float, red_pct: float) -> bool:
    """Sin Red de acordeón: red_pct==0 → nunca. Compat legado."""
    if red_pct == 0.0:
        return False
    p_red = beru_cazador.precio_desde_pct(centro, red_pct)
    if red_pct < 0:
        return precio >= p_red - 1e-9
    return precio <= p_red + 1e-9


def toca_oz_negociador(precio: float, centro: float, oz_pct: float) -> bool:
    return toca_trailing(precio, centro, oz_pct)


def distancia_hoz_a_red(ancla_pct: float, red_pct: float) -> float:
    return abs(ancla_pct - red_pct)


# --- Legado API (smokes / reciclaje viejo) ---

def adan_armado_pct() -> float:
    return float(getattr(config, "BERU_ADAN_ARMADO_PCT", 0.005))


def trigger_salida_precio(precio_entrada: float, direccion: str) -> float:
    ab = abismo_salida_pct()
    if direccion == "LONG":
        return precio_entrada * (1.0 - ab)
    return precio_entrada * (1.0 + ab)


def trigger_recompra_precio(precio_venta: float, direccion: str) -> float:
    ab = abismo_salida_pct()
    if direccion == "LONG":
        return precio_venta * (1.0 + ab)
    return precio_venta * (1.0 - ab)


def distancia_pct_a_trigger(precio: float, trigger: float) -> float:
    if trigger <= 0:
        return 999.0
    return abs(precio - trigger) / trigger


def precio_cerca_de_trigger(precio: float, trigger: float, umbral: float | None = None) -> bool:
    u = adan_armado_pct() if umbral is None else float(umbral)
    return distancia_pct_a_trigger(precio, trigger) <= u + 1e-12


def toca_trigger_precio(precio: float, trigger: float, direccion: str, modo: str = "SALIDA") -> bool:
    if modo == "RECOMPRA":
        if direccion == "LONG":
            return precio >= trigger - 1e-9
        return precio <= trigger + 1e-9
    if direccion == "LONG":
        return precio <= trigger + 1e-9
    return precio >= trigger - 1e-9


def cerca_condicional(
    precio: float,
    centro: float,
    oz_cond_pct: float,
    umbral: float | None = None,
) -> bool:
    p_oz = beru_cazador.precio_desde_pct(centro, oz_cond_pct)
    return precio_cerca_de_trigger(precio, p_oz, umbral)


def bracket_desde_trigger_precio(
    trigger: float,
    centro: float,
    direccion: str,
    paso_oz: float,
) -> tuple[float, float, float, float]:
    if centro <= 0:
        centro = trigger
    oz_pct = beru_cazador.pct_desde_precio(centro, trigger)
    oz_n, red_n = activar_trailing_unica(oz_pct, paso_oz)
    oz_p, red_p = sincronizar_grid(centro, oz_n, red_n if red_n != 0 else oz_n)
    return oz_n, red_n, oz_p, red_p


def gatillo_caza_pct(vacio_adan: float, direccion_caza: str) -> float:
    g = beru_cazador.gatillo_pct(vacio_adan)
    return g if direccion_caza == "SHORT" else -g


def cruzo_gatillo_caza(precio: float, centro: float, vacio: float, direccion_caza: str) -> bool:
    touch = beru_cazador.pct_desde_precio(centro, precio)
    if direccion_caza == "SHORT":
        return touch > 0 and beru_cazador.distancia_gatillo_cumplida(touch, vacio)
    return touch < 0 and beru_cazador.distancia_gatillo_cumplida(touch, vacio)
