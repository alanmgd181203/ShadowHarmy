"""Beru rango (lineal) — molino de laterales, Oz = trailing 0,2 %.

Geometría sellada 2026-08-20:
  · Vacío de Adán ±1,2 % desde el 0 → ARMA el trailing (no es la Oz fija)
  · Oz = trailing stop 0,2 % detrás del extremo:
      – subiendo → SHORT al retroceder 0,2
      – bajando → LONG al rebotar 0,2
  · Red mapa / continuación 0,7 % (ladder $5 post-Oz)
  · Tras fill Oz: 0 = fill; sangre 1,2 contraria ($10) o Red 0,7 mismo sentido ($5)
  · Ladder Red→$5 repetible ambos lados · un vivo · ojos/manos lineal
  · Bybit: el cerebro lleva el rastro; manos detonán Market / Stop que se enmienda
"""
from __future__ import annotations

from typing import Any

import core.config as config


def vacio_adan_pct() -> float:
    return float(getattr(config, "BERU_RANGO_VACIO_PCT", 0.012) or 0.012)


def oz_gap_pct() -> float:
    """Callback del trailing (= Oz). Default 0,2 %."""
    return float(getattr(config, "BERU_RANGO_OZ_GAP_PCT", 0.002) or 0.002)


def red_desde_oz_pct() -> float:
    return float(getattr(config, "BERU_RANGO_RED_DESDE_OZ_PCT", 0.007) or 0.007)


def sangre_contraria_pct() -> float:
    return float(getattr(config, "BERU_RANGO_SANGRE_PCT", 0.012) or 0.012)


def masa_tramo_usd() -> float:
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_USD", 10.0) or 10.0))


def masa_red_usd() -> float:
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_RED_USD", 5.0) or 5.0))


def trailing_dist_pct() -> float:
    """Alias del callback Oz (Bybit distance)."""
    return float(getattr(config, "BERU_RANGO_TRAILING_PCT", 0) or 0) or oz_gap_pct()


def manos_activas() -> bool:
    return bool(getattr(config, "BERU_RANGO_MANOS", False))


def hilo_activo() -> bool:
    return bool(getattr(config, "BERU_RANGO_HILO", False))


def cero_local(beru: Any) -> float:
    return float(getattr(beru, "centro_local", 0) or 0)


def pct_desde_cero(beru: Any, precio: float) -> float:
    c = cero_local(beru)
    px = float(precio or 0)
    if c <= 0 or px <= 0:
        return 0.0
    return (px - c) / c


def precio_desde_cero(beru: Any, pct: float) -> float:
    c = cero_local(beru)
    if c <= 0:
        return 0.0
    return c * (1.0 + float(pct))


def despertar(beru: Any, precio: float, *, activo: str = "") -> None:
    px = float(precio or 0)
    if px <= 0:
        raise ValueError("beru_rango: precio de wake inválido")
    beru.centro_local = px
    beru.ancla_tramo = px
    beru.centro_manto = 0.0
    beru.modo_combate = "RANGO"
    beru.estado = "ACECHANDO"
    beru.direccion = ""
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.oz_pct = 0.0
    beru.red_pct = 0.0
    beru.oz_adan = 0.0
    beru.red_adan = 0.0
    beru.trail_extremo = 0.0
    beru.llamado_tramo_pct = vacio_adan_pct()
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = False
    beru.sangre_vista_dentro = False
    beru.es_relevo_cazador = False
    beru.engorde_bloqueado = True
    beru.sangre_lado = ""
    beru.rango_escalones_red = 0
    beru.origen_tramo = ""
    if activo:
        beru.frente_asignado = f"{str(activo).upper()}USDT_LINEAL"


def marcar_visto_dentro(beru: Any, precio: float) -> None:
    if bool(getattr(beru, "sangre_vista_dentro", False)):
        return
    vac = vacio_adan_pct()
    if abs(pct_desde_cero(beru, precio)) <= vac + 1e-12:
        beru.sangre_vista_dentro = True


def toca_vacio(beru: Any, precio: float) -> str:
    if str(getattr(beru, "estado", "") or "") != "ACECHANDO":
        return ""
    if bool(getattr(beru, "es_relevo_cazador", False)):
        return ""
    if not bool(getattr(beru, "oreja_sangre_activa", False)):
        return ""
    marcar_visto_dentro(beru, precio)
    if not bool(getattr(beru, "sangre_vista_dentro", False)):
        return ""
    vac = vacio_adan_pct()
    pct = pct_desde_cero(beru, precio)
    if pct >= vac - 1e-12:
        return "ARRIBA"
    if pct <= -vac + 1e-12:
        return "ABAJO"
    return ""


def _oz_desde_extremo(extremo: float, *, short: bool) -> float:
    gap = trailing_dist_pct()
    ex = float(extremo or 0)
    if ex <= 0:
        return 0.0
    if short:
        return ex * (1.0 - gap)
    return ex * (1.0 + gap)


def _plantar_trailing(
    beru: Any,
    *,
    short: bool,
    masa: float,
    precio_armado: float,
) -> float:
    """Vacío/sangre/Red sonó: arma trailing Oz 0,2 detrás del extremo."""
    px = float(precio_armado or 0)
    if px <= 0:
        return 0.0
    gap = trailing_dist_pct()
    red_off = red_desde_oz_pct()
    beru.direccion = "SHORT" if short else "LONG"
    beru.trail_extremo = px
    beru.oz_adan = _oz_desde_extremo(px, short=short)
    if short:
        beru.red_adan = px * (1.0 + red_off)
    else:
        beru.red_adan = px * (1.0 - red_off)
    beru.oz_pct = pct_desde_cero(beru, beru.oz_adan)
    beru.red_pct = pct_desde_cero(beru, beru.red_adan)
    beru.llamado_tramo_pct = gap
    beru.masa = float(masa)
    beru.masa_tramo_usd = float(masa)
    beru.estado = "CAZANDO"
    beru.oreja_sangre_activa = False
    beru.oreja_red_activa = False
    beru.engorde_bloqueado = True
    return float(masa)


def armar_tramo_desde_vacio(
    beru: Any, lado: str, precio: float | None = None,
) -> float:
    """Vacío ±1,2 arma trailing SHORT/LONG masa $10."""
    lado_u = str(lado or "").upper()
    vac = vacio_adan_pct()
    if lado_u == "ARRIBA":
        px = float(precio or 0) or precio_desde_cero(beru, vac)
        beru.origen_tramo = "VACIO"
        return _plantar_trailing(beru, short=True, masa=masa_tramo_usd(), precio_armado=px)
    if lado_u == "ABAJO":
        px = float(precio or 0) or precio_desde_cero(beru, -vac)
        beru.origen_tramo = "VACIO"
        return _plantar_trailing(beru, short=False, masa=masa_tramo_usd(), precio_armado=px)
    return 0.0


def actualizar_trailing_oz(beru: Any, precio: float) -> bool:
    """Persigue el extremo; Oz = extremo ± 0,2 %. True si la Oz se movió."""
    if str(getattr(beru, "estado", "") or "") != "CAZANDO":
        return False
    px = float(precio or 0)
    if px <= 0:
        return False
    d = str(getattr(beru, "direccion", "") or "").upper()
    gap = trailing_dist_pct()
    red_off = red_desde_oz_pct()
    extremo = float(getattr(beru, "trail_extremo", 0) or 0) or px
    oz_antes = float(getattr(beru, "oz_adan", 0) or 0)
    moved = False
    if d == "SHORT":
        if px > extremo + 1e-15:
            extremo = px
            moved = True
        beru.trail_extremo = extremo
        beru.oz_adan = extremo * (1.0 - gap)
        beru.red_adan = extremo * (1.0 + red_off)
    elif d == "LONG":
        if px < extremo - 1e-15 or extremo <= 0:
            extremo = px
            moved = True
        beru.trail_extremo = extremo
        beru.oz_adan = extremo * (1.0 + gap)
        beru.red_adan = extremo * (1.0 - red_off)
    else:
        return False
    beru.oz_pct = pct_desde_cero(beru, beru.oz_adan)
    beru.red_pct = pct_desde_cero(beru, beru.red_adan)
    if abs(float(beru.oz_adan) - oz_antes) > 1e-12:
        moved = True
    return moved


def toca_oz(beru: Any, precio: float) -> bool:
    """Fill del trailing: SHORT al bajar a la Oz; LONG al subir a la Oz."""
    if str(getattr(beru, "estado", "") or "") != "CAZANDO":
        return False
    oz = float(getattr(beru, "oz_adan", 0) or 0)
    px = float(precio or 0)
    if oz <= 0 or px <= 0:
        return False
    d = str(getattr(beru, "direccion", "") or "").upper()
    if d == "SHORT":
        return px <= oz + 1e-12
    if d == "LONG":
        return px >= oz - 1e-12
    return False


def toca_sangre(beru: Any, precio: float) -> bool:
    if not bool(getattr(beru, "oreja_sangre_activa", False)):
        return False
    if str(getattr(beru, "estado", "") or "") != "ACECHANDO":
        return False
    if not (
        bool(getattr(beru, "es_relevo_cazador", False))
        or float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0) > 0
    ):
        return False
    sil = float(getattr(beru, "llamado_tramo_pct", 0) or sangre_contraria_pct())
    pct = pct_desde_cero(beru, precio)
    lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    if lado == "ABAJO":
        return pct <= -sil + 1e-12
    if lado == "ARRIBA":
        return pct >= sil - 1e-12
    oz_dir = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if oz_dir == "SHORT":
        return pct <= -sil + 1e-12
    if oz_dir == "LONG":
        return pct >= sil - 1e-12
    return False


def toca_red_continuacion(beru: Any, precio: float) -> bool:
    if not bool(getattr(beru, "oreja_red_activa", False)):
        return False
    if str(getattr(beru, "estado", "") or "") != "ACECHANDO":
        return False
    if not bool(getattr(beru, "es_relevo_cazador", False)):
        return False
    red = float(getattr(beru, "red_adan", 0) or 0)
    px = float(precio or 0)
    if red <= 0 or px <= 0:
        return False
    d = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if d == "SHORT":
        return px >= red - 1e-12
    if d == "LONG":
        return px <= red + 1e-12
    return False


def _plantar_orejas_post_oz(beru: Any, fill: float, direccion: str) -> None:
    sil = sangre_contraria_pct()
    red_off = red_desde_oz_pct()
    beru.llamado_tramo_pct = sil
    d = str(direccion or "").upper()
    if d == "SHORT":
        beru.sangre_lado = "ABAJO"
        beru.red_adan = fill * (1.0 + red_off)
        beru.red_pct = red_off
    else:
        beru.sangre_lado = "ARRIBA"
        beru.red_adan = fill * (1.0 - red_off)
        beru.red_pct = -red_off
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = True


def cosechar_oz_y_mover_cero(beru: Any, precio_fill: float) -> float:
    """Trailing detonó: 0 = fill; sangre 1,2 + Red 0,7."""
    fill = float(precio_fill or 0) or float(getattr(beru, "oz_adan", 0) or 0)
    if fill <= 0:
        return 0.0
    d = str(getattr(beru, "direccion", "") or "").upper()
    masa_hecha = float(getattr(beru, "masa", 0) or 0) or masa_tramo_usd()
    beru.ultima_hoz_tocada_precio = fill
    beru.ultima_hoz_tocada_pct = float(getattr(beru, "oz_pct", 0) or 0)
    beru.ultima_hoz_direccion = d
    beru.ultima_masa_cosechada = masa_hecha
    beru.precio_entrada_real = fill
    beru.centro_local = fill
    beru.ancla_tramo = fill
    beru.estado = "ACECHANDO"
    beru.sangre_vista_dentro = True
    beru.es_relevo_cazador = True
    beru.oz_adan = 0.0
    beru.oz_pct = 0.0
    beru.trail_extremo = 0.0
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.direccion = ""
    _plantar_orejas_post_oz(beru, fill, d)
    beru.cosechas_continuas = int(getattr(beru, "cosechas_continuas", 0) or 0) + 1
    return masa_tramo_usd()


def armar_tramo_desde_sangre(beru: Any, precio: float | None = None) -> float:
    lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    if lado == "ABAJO":
        return armar_tramo_desde_vacio(beru, "ABAJO", precio=precio)
    if lado == "ARRIBA":
        return armar_tramo_desde_vacio(beru, "ARRIBA", precio=precio)
    oz_dir = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if oz_dir == "SHORT":
        return armar_tramo_desde_vacio(beru, "ABAJO", precio=precio)
    if oz_dir == "LONG":
        return armar_tramo_desde_vacio(beru, "ARRIBA", precio=precio)
    return 0.0


def armar_tramo_desde_red(beru: Any, precio: float | None = None) -> float:
    """Red → Beru $5 con trailing Oz 0,2 detrás del extremo (parte en la Red)."""
    red = float(getattr(beru, "red_adan", 0) or 0)
    px = float(precio or 0) or red
    if px <= 0:
        return 0.0
    d = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    masa = masa_red_usd()
    if d == "SHORT":
        beru.origen_tramo = "RED"
        out = _plantar_trailing(beru, short=True, masa=masa, precio_armado=px)
    elif d == "LONG":
        beru.origen_tramo = "RED"
        out = _plantar_trailing(beru, short=False, masa=masa, precio_armado=px)
    else:
        return 0.0
    beru.rango_escalones_red = int(getattr(beru, "rango_escalones_red", 0) or 0) + 1
    return out


def resumen_geometria() -> dict[str, float | str]:
    vac = vacio_adan_pct()
    gap = trailing_dist_pct()
    return {
        "oficio": "RANGO",
        "mercado": "linear",
        "vacio_pct": vac,
        "oz_gap_pct": gap,
        "oz_modo": "trailing",
        "red_desde_oz_pct": red_desde_oz_pct(),
        "sangre_pct": sangre_contraria_pct(),
        "masa_usd": masa_tramo_usd(),
        "masa_red_usd": masa_red_usd(),
        "trailing_pct": gap,
        "engorde": 0.0,
        "ladder_red": "si",
    }
