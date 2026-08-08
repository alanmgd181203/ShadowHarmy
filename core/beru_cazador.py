"""Beru Cazador — doctrina capas: 0 manto, ±vacio/2 gatillo, trailing 0.1%, G_min/escalón."""
from __future__ import annotations

from typing import TYPE_CHECKING

import core.config as config
from core import beru_tier

if TYPE_CHECKING:
    from generales.tusk import TuskBoveda


def paso_pct() -> float:
    return beru_tier.PASO_TRAILING_CAZA


def mordida_usd(asset: str | None = None) -> float:
    """Mordida = G_min del Santo. Override fijo si BERU_CAZADOR_MORDIDA_USD > 0."""
    override = float(getattr(config, "BERU_CAZADOR_MORDIDA_USD", 0.0) or 0.0)
    if override > 0:
        return override
    from core.beru_capital import g_min_usd

    activo = (asset or str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH"))).upper()
    return float(g_min_usd(activo))


def gatillo_pct(vacio_adan: float) -> float:
    """Normal 1.6% → gatillo ±0.8% desde centro manto."""
    fraccion = float(getattr(config, "BERU_CAZADOR_GATILLO_FRACCION", 0.5))
    return float(vacio_adan) * fraccion


def capa1_masa_usd(masa_autorizada: float, asset: str | None = None) -> float:
    """Masa inicial al gatillar capa 1.

    Default: mordida = G_min del Santo. Engorde frontera (+G_min / 0.1%) sin techo
    artificial — solo el oxígeno que Tusk reserve (doctrina Monarca 2026-07-18).

    BERU_CAZA_CAPA1_USD > 0 → fuerza masa inicial fija.
    BERU_CAZA_CAPA1_MAX_USD > 0 → techo legacy opcional (0 = sin techo).
    """
    fijo = float(getattr(config, "BERU_CAZA_CAPA1_USD", 0.0))
    cap = float(getattr(config, "BERU_CAZA_CAPA1_MAX_USD", 0.0))
    masa = fijo if fijo > 0 else mordida_usd(asset)
    auth = float(masa_autorizada or 0.0)
    if auth > 0:
        masa = min(masa, auth)
    if cap > 0:
        masa = min(masa, cap)
    return max(0.0, float(masa))


def centro_manto_desde_tusk(tusk: TuskBoveda) -> float:
    precios: list[float] = []
    for p in (tusk.pesos or {}).values():
        pm_l = float(p.get("precio_medio_long") or 0)
        pm_s = float(p.get("precio_medio_short") or 0)
        if pm_l > 0:
            precios.append(pm_l)
        if pm_s > 0:
            precios.append(pm_s)
    if precios:
        return sum(precios) / len(precios)
    if tusk.precio_spot > 0:
        return float(tusk.precio_spot)
    return float(tusk.ultimo_precio or 0)


def pct_desde_precio(centro: float, precio: float) -> float:
    if centro <= 0:
        return 0.0
    return (precio - centro) / centro


def precio_desde_pct(centro: float, pct: float) -> float:
    return centro * (1.0 + pct)


def niveles_desde_toque(
    touch_pct: float,
    paso_oz: float | None = None,
    paso_red_clon: float | None = None,
) -> tuple[float, float]:
    """Al gatillar: oz 0.1% hacia el 0; red a distancia de clonación del tier."""
    p_oz = paso_oz if paso_oz is not None else paso_pct()
    p_red = paso_red_clon if paso_red_clon is not None else p_oz
    if touch_pct >= 0:
        return touch_pct - p_oz, touch_pct + p_red
    return touch_pct + p_oz, touch_pct - p_red


def mover_niveles_cazador(direccion: str, oz_pct: float, red_pct: float, paso: float | None = None) -> tuple[float, float]:
    """Cada toque de red (frontera): oz y red avanzan 0.1% juntas."""
    p = paso if paso is not None else paso_pct()
    if direccion == "SHORT":
        return oz_pct + p, red_pct + p
    return oz_pct - p, red_pct - p


def sincronizar_precios_grid(centro: float, oz_pct: float, red_pct: float) -> tuple[float, float]:
    return precio_desde_pct(centro, oz_pct), precio_desde_pct(centro, red_pct)


def toca_red(precio: float, direccion: str, red_precio: float) -> bool:
    if red_precio <= 0:
        return False
    eps = 1e-9
    if direccion == "SHORT":
        return precio >= red_precio - eps
    return precio <= red_precio + eps


def toca_oz(precio: float, direccion: str, oz_precio: float) -> bool:
    if oz_precio <= 0:
        return False
    eps = 1e-9
    if direccion == "SHORT":
        return precio <= oz_precio + eps
    return precio >= oz_precio - eps


def distancia_gatillo_cumplida(pct: float, vacio_adan: float) -> bool:
    return abs(pct) >= gatillo_pct(vacio_adan) - 1e-9


def es_frontera_red(beru, legion: list, modo_caza_fn) -> bool:
    """Solo el Beru con la red más extrema puede engordar."""
    activos = [
        b for b in legion
        if b is not beru
        and b.estado == "NEGOCIANDO"
        and modo_caza_fn(b) == "CAZA"
        and not getattr(b, "ciclo_infinito", False)
        and b.direccion == beru.direccion
        and float(getattr(b, "red_adan", 0) or 0) > 0
    ]
    if beru.red_adan <= 0:
        return False
    todos = activos + [beru]
    if beru.direccion == "SHORT":
        max_red = max(float(b.red_adan) for b in todos)
        return float(beru.red_adan) >= max_red - 1e-9
    min_red = min(float(b.red_adan) for b in todos)
    return float(beru.red_adan) <= min_red + 1e-9
