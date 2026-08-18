"""Beru Cazador — doctrina sellada Monarca 2026-08-17 · Vacío 1.1 desde wake.

Primer silbato = Vacío de Adán ±1.1% desde el 0 local de wake (precio al nacer).
El metro es el 0 del manto Igris: 1.1 puntos de ese metro, sin composición.
Hoz un peldaño detrás (±1.0%). El llamado solo detona — cero fill.
Mientras caza: Red de 0.1 en 0.1; Hoz engorda lo del grado por peldaño
solo si el Santo tiene manto Igris vivo.
Relevo: desde la ÚLTIMA Red TOCADA (+0.9 / +0.5 / +0.3), no desde la plantada.
Mariscal mueve la misma Hoz condicional; engorda G_min por cada peldaño.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import core.config as config
from core import beru_tier

if TYPE_CHECKING:
    from generales.tusk import TuskBoveda

# Vacío 1.1% → Hoz 1.0%; llamado = Hoz + 0.1%
HOZ_PRODUCTIVA_PCT = 0.010
LLAMADO_SANGRE_OFFSET = 0.001  # llamado = hoz + 0.1%


def paso_pct() -> float:
    return beru_tier.PASO_HOZ_CAZA


def llamado_sangre_pct() -> float:
    """Primer silbato: Vacío de Adán ±1.1% desde el 0 de wake, escala del manto."""
    return float(getattr(config, "BERU_LLAMADO_SANGRE_PCT", HOZ_PRODUCTIVA_PCT + LLAMADO_SANGRE_OFFSET))


def hoz_productiva_pct() -> float:
    """Primera Hoz: ±1.0% — un peldaño detrás del Vacío."""
    return float(getattr(config, "BERU_HOZ_PRODUCTIVA_PCT", HOZ_PRODUCTIVA_PCT))


def gatillo_pct(vacio_adan: float | None = None) -> float:
    """Gatillo de la semilla = Vacío ±1.1. El ADN del capitán no sustituye esto."""
    _ = vacio_adan
    return llamado_sangre_pct()


def mordida_usd(asset: str | None = None) -> float:
    """Mordida = G_min del Santo. Override fijo si BERU_CAZADOR_MORDIDA_USD > 0."""
    override = float(getattr(config, "BERU_CAZADOR_MORDIDA_USD", 0.0) or 0.0)
    if override > 0:
        return override
    from core.beru_capital import g_min_usd

    activo = (asset or str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH"))).upper()
    return float(g_min_usd(activo))


def engorde_paso_usd(asset: str | None = None, grado: str | None = None) -> float:
    """Cuánto engorda la Hoz por cada 0.1% de frontera (fricción del grado).

    Soldado ~G_min/8 · Capitán /4 · General /2 · Mariscal = G_min.
    """
    from core.beru_capital import friccion_grado_pct, g_min_usd, grado_desde_tier

    activo = (asset or str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH"))).upper()
    g = g_min_usd(activo)
    if grado:
        fr = friccion_grado_pct(str(grado).upper())
    else:
        tid = str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1")).upper()
        fr = friccion_grado_pct(grado_desde_tier(tid))
    paso = paso_pct()
    if fr <= 0:
        return float(g)
    return float(g) * (paso / fr)


def grado_de_barco(beru) -> str:
    from core.beru_capital import grado_desde_tier

    tid = str(getattr(beru, "tier_id", None) or getattr(config, "BERU_TIER_DEFAULT", "PROTO1")).upper()
    return grado_desde_tier(tid)


def relevo_llamado_pct(grado_o_tier: str) -> float:
    """Silbato del siguiente cazador desde la última Red TOCADA."""
    g = str(grado_o_tier or "SOLDADO").upper()
    # Si llega tier id, mapear
    from core.beru_capital import grado_desde_tier

    if g in ("PLENO", "PROTO1", "PROTO2", "BERUBBY"):
        g = grado_desde_tier(g)
    tabla = {
        "SOLDADO": 0.009,
        "CAPITAN": 0.005,
        "GENERAL": 0.003,
        "MARISCAL": 0.001,
    }
    return float(tabla.get(g, 0.009))


def capa1_masa_usd(masa_autorizada: float, asset: str | None = None, grado: str | None = None) -> float:
    """Masa inicial al detonar: peldaños desde 0 hasta Hoz 1.0% × engorde del grado.

    Soldado ≈ 1.25×G_min · Mariscal ≈ 10×G_min ($50 si G_min=$5). Oxígeno Tusk acota.
    """
    fijo = float(getattr(config, "BERU_CAZA_CAPA1_USD", 0.0))
    cap = float(getattr(config, "BERU_CAZA_CAPA1_MAX_USD", 0.0))
    if fijo > 0:
        masa = fijo
    else:
        peldaños = hoz_productiva_pct() / max(paso_pct(), 1e-12)
        masa = engorde_paso_usd(asset, grado) * peldaños
    auth = float(masa_autorizada or 0.0)
    if auth > 0:
        masa = min(masa, auth)
    if cap > 0:
        masa = min(masa, cap)
    return max(0.0, float(masa))


def frente_es_santo(frente: str, activo: str) -> bool:
    """HYPE ≠ HYPER. El Santo es prefijo de la clave (HYPEUSDT… / HYPEUSD_…)."""
    fu = str(frente or "").upper()
    act = str(activo or "").upper()
    if not fu or not act:
        return False
    return (
        fu.startswith(f"{act}USDT")
        or fu.startswith(f"{act}USDC")
        or fu.startswith(f"{act}USDE")
        or fu.startswith(f"{act}USD1")
        or fu.startswith(f"{act}USD_")
    )


def centro_manto_desde_tusk(
    tusk: TuskBoveda,
    activo: str | None = None,
    *,
    fallback_global: bool = True,
) -> float:
    """0 de Beru = promedio de entrada L+S del manto (Igris/Tusk).

    Si hay activo, prioriza pesos de ese Santo; si no, promedio de todos los medios.
    No usa spot/last como 0 (eso son ojos, no el metro).
    """
    precios: list[float] = []
    act = str(activo or "").upper()
    pesos = tusk.pesos or {}
    for frente, p in pesos.items():
        if act and not frente_es_santo(frente, act):
            continue
        pm_l = float(p.get("precio_medio_long") or 0)
        pm_s = float(p.get("precio_medio_short") or 0)
        if pm_l > 0:
            precios.append(pm_l)
        if pm_s > 0:
            precios.append(pm_s)
    if not precios and act and fallback_global:
        # Sin filtro si el activo no matcheó claves
        for p in pesos.values():
            pm_l = float(p.get("precio_medio_long") or 0)
            pm_s = float(p.get("precio_medio_short") or 0)
            if pm_l > 0:
                precios.append(pm_l)
            if pm_s > 0:
                precios.append(pm_s)
    if precios:
        return sum(precios) / len(precios)
    return 0.0


def manto_vivo(tusk, activo: str) -> bool:
    """Ese Santo tiene metro L+S de Igris. Sin manto no se arma ni se engorda."""
    act = str(activo or "").upper()
    if not act or tusk is None:
        return False
    centro = float(centro_manto_desde_tusk(tusk, act, fallback_global=False) or 0)
    if centro <= 0:
        return False
    pesos = getattr(tusk, "pesos", None) or {}
    masa = 0.0
    for frente, p in pesos.items():
        if not frente_es_santo(frente, act):
            continue
        masa += float((p or {}).get("long") or 0) + float((p or {}).get("short") or 0)
    return masa > 1e-12


def aplicar_nuevo_cero(beru, nuevo_centro: float, *, umbral_rel: float = 1e-6) -> bool:
    """Si el 0 del manto se movió (Igris engordó), refresca centro y re-sincroniza precios absolutos.

    Los % (oz_pct, red_pct, neg_*) se conservan — solo cambian oz_adan/red_adan.
    """
    nuevo = float(nuevo_centro or 0)
    if nuevo <= 0:
        return False
    viejo = float(getattr(beru, "centro_manto", 0) or 0)
    if viejo > 0 and abs(nuevo - viejo) / viejo < umbral_rel:
        return False
    beru.centro_manto = nuevo
    # El 0 local de acecho es el wake; no se pisa con el manto.
    if float(getattr(beru, "centro_local", 0) or 0) <= 0:
        ancla = float(getattr(beru, "ancla_tramo", 0) or 0)
        beru.centro_local = ancla if ancla > 0 else nuevo
    # Reproyectar cartas desde %
    oz_p = float(getattr(beru, "oz_pct", 0) or 0)
    red_p = float(getattr(beru, "red_pct", 0) or 0)
    if oz_p != 0.0 or red_p != 0.0:
        beru.oz_adan, beru.red_adan = sincronizar_precios_grid(nuevo, oz_p, red_p)
    neg_oz = float(getattr(beru, "neg_oz_pct", 0) or 0)
    if neg_oz != 0.0 and str(getattr(beru, "modo_combate", "")).upper() == "NEGOCIADOR":
        # Trailing única: oz_adan = precio del gatillo
        beru.oz_adan = precio_desde_pct(nuevo, neg_oz)
        beru.red_adan = 0.0
    return True


def pct_desde_precio(centro: float, precio: float) -> float:
    if centro <= 0:
        return 0.0
    return (precio - centro) / centro


def precio_desde_pct(centro: float, pct: float) -> float:
    return centro * (1.0 + pct)


def niveles_desde_llamado_sangre(signo: int) -> tuple[float, float]:
    """Al detonar Vacío: Hoz ±1.0; Red un peldaño más afuera (±1.2)."""
    s = 1 if signo >= 0 else -1
    oz = s * hoz_productiva_pct()
    red = s * (llamado_sangre_pct() + paso_pct())
    return oz, red


def niveles_desde_sangre_abs(sangre_pct: float) -> tuple[float, float]:
    """Sangre absoluta sobre 0 Igris (ej. +30.9%) → Hoz un peldaño detrás, Red en sangre."""
    signo = 1 if sangre_pct >= 0 else -1
    if sangre_pct == 0:
        return niveles_desde_llamado_sangre(1)
    oz = sangre_pct - signo * LLAMADO_SANGRE_OFFSET
    red = sangre_pct
    return oz, red


def niveles_desde_toque(
    touch_pct: float,
    paso_oz: float | None = None,
    paso_red_clon: float | None = None,
) -> tuple[float, float]:
    """Si |touch|≈1.1 → primera caza; si mayor (fósil post-Mega) → sangre absoluta."""
    _ = paso_oz, paso_red_clon
    if abs(touch_pct) <= llamado_sangre_pct() + 1e-9:
        signo = 1 if touch_pct >= 0 else -1
        return niveles_desde_llamado_sangre(signo)
    return niveles_desde_sangre_abs(touch_pct)


def ultima_red_tocada_pct(red_plantada_pct: float, direccion: str) -> float:
    """Si la Red plantada está en X, la última tocada fue X − 0.1% (hacia el 0)."""
    p = paso_pct()
    if direccion == "SHORT" or red_plantada_pct > 0:
        return red_plantada_pct - p
    return red_plantada_pct + p


def llamado_relevo_pct(red_plantada_pct: float, direccion: str, grado_o_tier: str) -> float:
    """Nuevo llamado = última Red tocada + offset de grado."""
    tocada = ultima_red_tocada_pct(red_plantada_pct, direccion)
    off = relevo_llamado_pct(grado_o_tier)
    if direccion == "SHORT" or red_plantada_pct > 0:
        return tocada + off
    return tocada - off


def mover_niveles_cazador(
    direccion: str, oz_pct: float, red_pct: float, paso: float | None = None,
) -> tuple[float, float]:
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


def distancia_gatillo_cumplida(pct: float, vacio_adan: float | None = None) -> bool:
    return abs(pct) >= gatillo_pct(vacio_adan) - 1e-9


def toca_llamado_sangre(pct: float) -> bool:
    return abs(pct) >= llamado_sangre_pct() - 1e-9


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
