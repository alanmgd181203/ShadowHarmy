"""Beru Negociador — abismo -2%, vacío Adán 0.5%, reciclaje sin engorde."""
from __future__ import annotations

from core import beru_cazador
from core import beru_tier
import core.config as config

FaseNeg = str  # ESPERANDO_CONDICIONAL | ARMADO_ADAN | ACORDEON | RECICLANDO


def abismo_salida_pct() -> float:
    """Distancia fija de salida tras caza (−2% doctrina Monarca)."""
    return float(getattr(config, "BERU_ABISMO_SALIDA_PCT", 0.02))


def adan_armado_pct() -> float:
    """Vacío Adán: armar bracket en memoria cuando el precio está a ≤0.5% del trigger."""
    return float(getattr(config, "BERU_ADAN_ARMADO_PCT", 0.005))


def abismo_pct(vacio_adan: float | None = None) -> float:
    """Preferir abismo de salida fijo 2%; vacio_adan queda como fallback legacy."""
    fijo = abismo_salida_pct()
    if fijo > 0:
        return fijo
    return float(vacio_adan or getattr(config, "BERU_VACIO_NORMAL", 0.016))


def lado_desde_ancla(ancla_pct: float) -> int:
    if ancla_pct > 0:
        return -1
    if ancla_pct < 0:
        return 1
    return -1


def oz_condicional_pct(ancla_pct: float, vacio: float | None = None) -> float:
    """Trigger de salida: ancla − 2% (hacia el 0 / retroceso)."""
    abismo = abismo_pct(vacio)
    if ancla_pct > 0:
        return ancla_pct - abismo
    if ancla_pct < 0:
        return ancla_pct + abismo
    return -abismo


def trigger_salida_precio(precio_entrada: float, direccion: str) -> float:
    """Precio absoluto de salida: −2% respecto a entrada (LONG baja; SHORT sube para cubrir)."""
    ab = abismo_salida_pct()
    if direccion == "LONG":
        return precio_entrada * (1.0 - ab)
    return precio_entrada * (1.0 + ab)


def trigger_recompra_precio(precio_venta: float, direccion: str) -> float:
    """Tras soltar: recompra +2% arriba del precio de venta (mismo volumen)."""
    ab = abismo_salida_pct()
    if direccion == "LONG":
        return precio_venta * (1.0 + ab)
    return precio_venta * (1.0 - ab)


def distancia_pct_a_trigger(precio: float, trigger: float) -> float:
    if trigger <= 0:
        return 999.0
    return abs(precio - trigger) / trigger


def precio_cerca_de_trigger(precio: float, trigger: float, umbral: float | None = None) -> bool:
    """Vacío Adán: True si el precio está a ≤ umbral del trigger (default 0.5%)."""
    u = adan_armado_pct() if umbral is None else float(umbral)
    return distancia_pct_a_trigger(precio, trigger) <= u + 1e-12


def toca_trigger_precio(precio: float, trigger: float, direccion: str, modo: str = "SALIDA") -> bool:
    """modo SALIDA: LONG vende si precio≤trigger; SHORT cubre si precio≥trigger.
    modo RECOMPRA: inverso."""
    if modo == "RECOMPRA":
        if direccion == "LONG":
            return precio >= trigger - 1e-9
        return precio <= trigger + 1e-9
    if direccion == "LONG":
        return precio <= trigger + 1e-9
    return precio >= trigger - 1e-9


def pasos_negociador(tier_id: str | None) -> tuple[float, float]:
    t = beru_tier.tier_por_id(tier_id)
    return t.pasos("NEGOCIADOR")


def sincronizar_grid(centro: float, oz_pct: float, red_pct: float) -> tuple[float, float]:
    return beru_cazador.sincronizar_precios_grid(centro, oz_pct, red_pct)


def activar_primera_vez(
    oz_cond_pct: float,
    paso_oz: float,
) -> tuple[float, float]:
    """Primera activación: oz y red avanzan paso_oz; red queda más cerca del 0."""
    if oz_cond_pct < 0:
        oz_n = oz_cond_pct - paso_oz
        red_n = oz_cond_pct + paso_oz
    else:
        oz_n = oz_cond_pct + paso_oz
        red_n = oz_cond_pct - paso_oz
    return oz_n, red_n


def bracket_desde_trigger_precio(
    trigger: float,
    centro: float,
    direccion: str,
    paso_oz: float,
) -> tuple[float, float, float, float]:
    """Devuelve (oz_pct, red_pct, oz_precio, red_precio) alrededor del trigger."""
    if centro <= 0:
        centro = trigger
    oz_pct = beru_cazador.pct_desde_precio(centro, trigger)
    oz_n, red_n = activar_primera_vez(oz_pct, paso_oz)
    oz_p, red_p = sincronizar_grid(centro, oz_n, red_n)
    return oz_n, red_n, oz_p, red_p


def avanzar_toque_oz(
    oz_pct: float,
    red_pct: float,
    paso_oz: float,
    paso_red: float,
) -> tuple[float, float]:
    if oz_pct < 0:
        return oz_pct - paso_oz, red_pct - paso_red
    return oz_pct + paso_oz, red_pct + paso_red


def resorte_sexto_toque(oz_pct: float, paso_oz: float) -> tuple[float, float]:
    if oz_pct < 0:
        condicional = oz_pct - paso_oz
        oz_n = condicional - paso_oz
        red_n = condicional + paso_oz
    else:
        condicional = oz_pct + paso_oz
        oz_n = condicional + paso_oz
        red_n = condicional - paso_oz
    return oz_n, red_n


def toques_hasta_resorte() -> int:
    return 5


def es_sexto_toque(toques_ciclo: int) -> bool:
    return toques_ciclo >= toques_hasta_resorte()


def toca_condicional(precio: float, centro: float, oz_cond_pct: float) -> bool:
    p_oz = beru_cazador.precio_desde_pct(centro, oz_cond_pct)
    if oz_cond_pct < 0:
        return precio <= p_oz + 1e-9
    return precio >= p_oz - 1e-9


def cerca_condicional(
    precio: float,
    centro: float,
    oz_cond_pct: float,
    umbral: float | None = None,
) -> bool:
    p_oz = beru_cazador.precio_desde_pct(centro, oz_cond_pct)
    return precio_cerca_de_trigger(precio, p_oz, umbral)


def toca_red_negociador(precio: float, centro: float, red_pct: float) -> bool:
    p_red = beru_cazador.precio_desde_pct(centro, red_pct)
    if red_pct < 0:
        return precio >= p_red - 1e-9
    return precio <= p_red + 1e-9


def gatillo_caza_pct(vacio_adan: float, direccion_caza: str) -> float:
    g = beru_cazador.gatillo_pct(vacio_adan)
    return g if direccion_caza == "SHORT" else -g


def toca_oz_negociador(precio: float, centro: float, oz_pct: float) -> bool:
    p_oz = beru_cazador.precio_desde_pct(centro, oz_pct)
    if oz_pct < 0:
        return precio <= p_oz + 1e-9
    return precio >= p_oz - 1e-9


def cruzo_gatillo_caza(precio: float, centro: float, vacio: float, direccion_caza: str) -> bool:
    touch = beru_cazador.pct_desde_precio(centro, precio)
    if direccion_caza == "SHORT":
        return touch > 0 and beru_cazador.distancia_gatillo_cumplida(touch, vacio)
    return touch < 0 and beru_cazador.distancia_gatillo_cumplida(touch, vacio)
