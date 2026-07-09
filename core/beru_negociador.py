"""Beru Negociador — post-cazador: abismo 1.6%, oz condicional, acordeón 5+resorte."""
from __future__ import annotations

from core import beru_cazador
from core import beru_tier

FaseNeg = str  # ESPERANDO_CONDICIONAL | ACORDEON


def abismo_pct(vacio_adan: float) -> float:
    """Distancia oz condicional desde ancla de cosecha (= vacío Normal 1.6%)."""
    return float(vacio_adan)


def lado_desde_ancla(ancla_pct: float) -> int:
    """+1 = ancla arriba del manto (cazador SHORT); −1 = ancla abajo (cazador LONG)."""
    if ancla_pct > 0:
        return -1
    if ancla_pct < 0:
        return 1
    return -1


def oz_condicional_pct(ancla_pct: float, vacio: float) -> float:
    """Oz condicional al otro lado del manto: ±abismo desde ancla de cosecha."""
    abismo = abismo_pct(vacio)
    if ancla_pct > 0:
        return ancla_pct - abismo
    if ancla_pct < 0:
        return ancla_pct + abismo
    return -abismo


def pasos_negociador(tier_id: str | None) -> tuple[float, float]:
    t = beru_tier.tier_por_id(tier_id)
    return t.pasos("NEGOCIADOR")


def sincronizar_grid(centro: float, oz_pct: float, red_pct: float) -> tuple[float, float]:
    return beru_cazador.sincronizar_precios_grid(centro, oz_pct, red_pct)


def activar_primera_vez(
    oz_cond_pct: float,
    paso_oz: float,
) -> tuple[float, float]:
    """Primera activación: oz y red avanzan paso_oz; red queda más cerca del 0 (orden inverso)."""
    if oz_cond_pct < 0:
        oz_n = oz_cond_pct - paso_oz
        red_n = oz_cond_pct + paso_oz
    else:
        oz_n = oz_cond_pct + paso_oz
        red_n = oz_cond_pct - paso_oz
    return oz_n, red_n


def avanzar_toque_oz(
    oz_pct: float,
    red_pct: float,
    paso_oz: float,
    paso_red: float,
) -> tuple[float, float]:
    """Toques 2–5: oz paso_oz, red paso_red en la misma dirección (sin engorde)."""
    if oz_pct < 0:
        return oz_pct - paso_oz, red_pct - paso_red
    return oz_pct + paso_oz, red_pct + paso_red


def resorte_sexto_toque(oz_pct: float, paso_oz: float) -> tuple[float, float]:
    """6.º toque: oz +paso extra; red salta a 0.1% bajo la oz condicional del disparo."""
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


def toca_red_negociador(precio: float, centro: float, red_pct: float) -> bool:
    """Toque de red negociador (subida desde abajo) = oz en modo caza."""
    p_red = beru_cazador.precio_desde_pct(centro, red_pct)
    if red_pct < 0:
        return precio >= p_red - 1e-9
    return precio <= p_red + 1e-9


def gatillo_caza_pct(vacio_adan: float, direccion_caza: str) -> float:
    """Nivel ±vacío/2 para armar grid cazador fantasma tras cruzar abismo."""
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
