"""Beru rango (lineal) — wake eterno · Red desde Oz · saco meta−ya · sangre $5+.

Doctrina Monarca 2026-08-22 (cirugía saco):
  · 0 absoluto = wake (no se mueve con Oz ni fill)
  · Perfil normal: Vacío/sangre ±1,2 % · Oz 0,2 % · Red 0,7 % · +$1/0,1 %
  · Perfil feria (paralelo): ±2,4 % · Oz 0,4 % · Red 1,4 % · +$1/0,2 %
  · Vacío/Red/Sangre nacen $5; engorde desde activación; techo meta−ya
  · Misma vela: sangre primero · sangre mata Red
  · Un vivo · manos OFF por defecto · lineal · BERU_RANGO_PERFIL
"""
from __future__ import annotations

from typing import Any

import core.config as config


def vacio_adan_pct() -> float:
    """Activación del trailing semilla / sangre (± desde el wake)."""
    return float(getattr(config, "BERU_RANGO_VACIO_PCT", 0.012) or 0.012)


def oz_gap_pct() -> float:
    """Callback del trailing (distancia que persigue)."""
    return float(getattr(config, "BERU_RANGO_OZ_GAP_PCT", 0.002) or 0.002)


def red_activacion_pct() -> float:
    """Activación del trailing Red (desde la Oz desplegada)."""
    return float(getattr(config, "BERU_RANGO_RED_DESDE_OZ_PCT", 0.007) or 0.007)


def red_desde_oz_pct() -> float:
    """Alias histórico = activación Red."""
    return red_activacion_pct()


def sangre_contraria_pct() -> float:
    return float(getattr(config, "BERU_RANGO_SANGRE_PCT", 0.012) or 0.012)


def masa_tramo_usd() -> float:
    """Base Vacío / tramo ($5). Piso Bybit se aplica en altar/manos."""
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_USD", 5.0) or 5.0))


def masa_red_usd() -> float:
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_RED_USD", 5.0) or 5.0))


def masa_sangre_usd() -> float:
    """Sangre parcial: $5 del tramo vivo."""
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_SANGRE_USD", 5.0) or 5.0))


def engorde_paso_usd() -> float:
    return max(0.0, float(getattr(config, "BERU_RANGO_ENGORDE_USD", 1.0) or 1.0))


def engorde_paso_pct() -> float:
    return max(1e-9, float(getattr(config, "BERU_RANGO_ENGORDE_PASO_PCT", 0.001) or 0.001))


def piso_masa_usd(masa: float, *, minimo_bybit: float = 0.0) -> float:
    """max(masa doctrinal, mínimo Bybit del Santo)."""
    return max(float(masa or 0), float(minimo_bybit or 0), 0.0)


def peldaños_entre(a: float, b: float) -> int:
    """Cuántos pasos de 0,1 % hay entre dos precios (referencia = a)."""
    a0 = float(a or 0)
    b0 = float(b or 0)
    if a0 <= 0 or b0 <= 0:
        return 0
    return int(abs(b0 - a0) / a0 / engorde_paso_pct() + 1e-12)


def meta_saco_usd(wake: float, precio: float, *, base: float | None = None) -> float:
    """Saco objetivo a esta profundidad: $5 + $1 × peldaños desde wake."""
    b = float(base if base is not None else masa_tramo_usd())
    w = float(wake or 0)
    px = float(precio or 0)
    if w <= 0 or px <= 0:
        return max(0.0, b)
    return max(0.0, b + float(peldaños_entre(w, px)) * engorde_paso_usd())


def saco_lado_usd(beru: Any, lado: str) -> float:
    """Masa ya cosechada en ese lado (ledger de la ola)."""
    d = str(lado or "").upper()
    if d == "LONG":
        return max(0.0, float(getattr(beru, "saco_long_usd", 0) or 0))
    if d == "SHORT":
        return max(0.0, float(getattr(beru, "saco_short_usd", 0) or 0))
    return 0.0


def registrar_saco(beru: Any, lado: str, masa: float) -> None:
    """Suma fill al ledger del lado (no doble-cuenta en el siguiente tramo)."""
    m = max(0.0, float(masa or 0))
    d = str(lado or "").upper()
    if d == "LONG":
        beru.saco_long_usd = saco_lado_usd(beru, "LONG") + m
    elif d == "SHORT":
        beru.saco_short_usd = saco_lado_usd(beru, "SHORT") + m


def cupo_lado_usd(beru: Any, *, lado: str, precio: float, origen: str) -> float:
    """Techo del saco en ese lado: meta(wake,px) − ya cosechado (anti-stack)."""
    d = str(lado or "").upper()
    px = float(precio or 0)
    origen_u = str(origen or "").upper()
    base = masa_red_usd() if origen_u == "RED" else masa_tramo_usd()
    meta = meta_saco_usd(cero_wake(beru), px, base=base)
    ya = saco_lado_usd(beru, d)
    return max(0.0, meta - ya)


def orden_nacimiento_usd(beru: Any, *, lado: str, precio: float, origen: str) -> float:
    """Vacío/Red nacen en $5 (o menos si el cupo meta−saco es menor)."""
    origen_u = str(origen or "").upper()
    base = masa_red_usd() if origen_u == "RED" else masa_tramo_usd()
    cupo = cupo_lado_usd(beru, lado=lado, precio=precio, origen=origen_u)
    if cupo <= 1e-12:
        return 0.0
    return min(base, cupo)


# Alias: cupo restante (smokes / lectura)
orden_vacio_red_usd = cupo_lado_usd


def masa_tramo_viva_usd(beru: Any, precio: float | None = None) -> float:
    """Masa del tramo vivo — misma regla Vacío / Red / Sangre.

    Nace en $5. Engorda $1 por cada 0,1 % solo desde el precio de activación.
    Vacío/Red además no pasan el cupo meta(wake) − saco ya del lado.
    """
    origen = str(getattr(beru, "origen_tramo", "") or "").upper()
    d = str(getattr(beru, "direccion", "") or "").upper()
    px = float(precio or 0) or float(getattr(beru, "trail_extremo", 0) or 0)
    if origen == "SANGRE":
        base = masa_sangre_usd()
    elif origen == "RED":
        base = masa_red_usd()
    else:
        base = masa_tramo_usd()
    ancla = float(getattr(beru, "engorde_ancla_px", 0) or 0) or px
    if ancla <= 0 or px <= 0:
        viva = base
    else:
        viva = base + float(peldaños_entre(ancla, px)) * engorde_paso_usd()
    if origen == "SANGRE" or d not in ("LONG", "SHORT"):
        return max(0.0, viva)
    origen_arm = "RED" if origen == "RED" else "VACIO"
    cupo = cupo_lado_usd(beru, lado=d, precio=px, origen=origen_arm)
    if cupo <= 1e-12:
        return 0.0
    return min(viva, cupo)


def masa_engordada_usd(beru: Any, precio: float | None = None) -> float:
    """Alias doctrinal = masa del tramo vivo."""
    return masa_tramo_viva_usd(beru, precio)


def actualizar_engorde(beru: Any, precio: float) -> bool:
    """Engorda el tramo vivo desde ancla ($5 + peldaños); Vacío/Red respetan cupo."""
    if bool(getattr(beru, "engorde_bloqueado", True)):
        return False
    if str(getattr(beru, "estado", "") or "").upper() != "CAZANDO":
        return False
    nueva = masa_tramo_viva_usd(beru, precio)
    vieja = float(getattr(beru, "masa", 0) or 0)
    if nueva > vieja + 1e-9:
        beru.masa = nueva
        beru.masa_tramo_usd = nueva
        ancla = float(getattr(beru, "engorde_ancla_px", 0) or 0)
        if ancla > 0:
            beru.engorde_peldaños = peldaños_entre(ancla, precio)
        else:
            beru.engorde_peldaños = 0
        return True
    return False


def trailing_dist_pct() -> float:
    return float(getattr(config, "BERU_RANGO_TRAILING_PCT", 0) or 0) or oz_gap_pct()


def manos_activas() -> bool:
    return bool(getattr(config, "BERU_RANGO_MANOS", False))


def hilo_activo() -> bool:
    return bool(getattr(config, "BERU_RANGO_HILO", False))


def cero_wake(beru: Any) -> float:
    """0 absoluto del wake — no se mueve con Oz/fill."""
    w = float(getattr(beru, "cero_wake", 0) or 0)
    if w > 0:
        return w
    return float(getattr(beru, "centro_local", 0) or 0)


def cero_local(beru: Any) -> float:
    """Alias de medición: siempre el wake."""
    return cero_wake(beru)


def pct_desde_cero(beru: Any, precio: float) -> float:
    c = cero_wake(beru)
    px = float(precio or 0)
    if c <= 0 or px <= 0:
        return 0.0
    return (px - c) / c


def precio_desde_cero(beru: Any, pct: float) -> float:
    c = cero_wake(beru)
    if c <= 0:
        return 0.0
    return c * (1.0 + float(pct))


def ancla_mapa_red(oz_despliegue: float, fill: float, direccion: str) -> float:
    """Peldaño manda. Fill peor (hacia Red) sube ancla; fill mejor no comprime."""
    oz = float(oz_despliegue or 0)
    fill_px = float(fill or 0)
    if oz <= 0:
        return fill_px
    if fill_px <= 0:
        return oz
    d = str(direccion or "").upper()
    if d == "SHORT":
        # Red arriba: fill peor = más alto → ancla sube
        return max(oz, fill_px)
    # LONG: Red abajo: fill peor = más bajo → ancla baja
    return min(oz, fill_px)


def red_desde_ancla(ancla: float, direccion: str) -> float:
    red_act = red_activacion_pct()
    a = float(ancla or 0)
    if a <= 0:
        return 0.0
    d = str(direccion or "").upper()
    if d == "SHORT":
        return a * (1.0 + red_act)
    return a * (1.0 - red_act)


def despertar(beru: Any, precio: float, *, activo: str = "") -> None:
    px = float(precio or 0)
    if px <= 0:
        raise ValueError("beru_rango: precio de wake inválido")
    beru.cero_wake = px
    beru.centro_local = px
    beru.ancla_tramo = px
    beru.centro_manto = px  # mismo 0: wake = manto de referencia
    beru.modo_combate = "RANGO"
    beru.estado = "ACECHANDO"
    beru.direccion = ""
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.oz_pct = 0.0
    beru.red_pct = 0.0
    beru.oz_adan = 0.0
    beru.red_adan = 0.0
    beru.oz_despliegue_px = 0.0
    beru.trail_extremo = 0.0
    beru.llamado_tramo_pct = vacio_adan_pct()
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = False
    beru.sangre_vista_dentro = False
    beru.es_relevo_cazador = False
    beru.engorde_bloqueado = True
    beru.engorde_peldaños = 0
    beru.engorde_ancla_px = 0.0
    beru.saco_long_usd = 0.0
    beru.saco_short_usd = 0.0
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
    """Activación ±1,2 del trailing semilla (desde wake)."""
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
    precio_activacion: float,
) -> float:
    """Activación tocada → arma trailing (callback 0,2). Engorde ON en caza."""
    px = float(precio_activacion or 0)
    if px <= 0:
        return 0.0
    masa_f = float(masa or 0)
    if masa_f <= 1e-12:
        return 0.0
    beru.direccion = "SHORT" if short else "LONG"
    beru.trail_extremo = px
    beru.engorde_ancla_px = px
    beru.oz_adan = _oz_desde_extremo(px, short=short)
    beru.oz_pct = pct_desde_cero(beru, beru.oz_adan)
    beru.red_adan = 0.0
    beru.red_pct = 0.0
    beru.llamado_tramo_pct = trailing_dist_pct()
    beru.masa = masa_f
    beru.masa_tramo_usd = masa_f
    beru.estado = "CAZANDO"
    beru.oreja_sangre_activa = False
    beru.oreja_red_activa = False
    beru.engorde_bloqueado = False
    beru.engorde_peldaños = 0
    # Nuevo sello de altar en cada caza — no reutilizar link de un fill viejo.
    beru.altar_revision = int(getattr(beru, "altar_revision", 0) or 0) + 1
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    # Recalcula: engorde desde ancla; Vacío/Red pueden crecer hasta el cupo.
    actualizar_engorde(beru, px)
    return float(getattr(beru, "masa", 0) or masa_f)


def armar_tramo_desde_vacio(
    beru: Any, lado: str, precio: float | None = None,
) -> float:
    """Vacío ±1,2 → trailing nace en $5; engorde solo si Oz sigue desde activación."""
    lado_u = str(lado or "").upper()
    vac = vacio_adan_pct()
    if lado_u == "ARRIBA":
        px = float(precio or 0) or precio_desde_cero(beru, vac)
        beru.origen_tramo = "VACIO"
        orden = orden_nacimiento_usd(beru, lado="SHORT", precio=px, origen="VACIO")
        if orden <= 1e-12:
            return 0.0
        return _plantar_trailing(beru, short=True, masa=orden, precio_activacion=px)
    if lado_u == "ABAJO":
        px = float(precio or 0) or precio_desde_cero(beru, -vac)
        beru.origen_tramo = "VACIO"
        orden = orden_nacimiento_usd(beru, lado="LONG", precio=px, origen="VACIO")
        if orden <= 1e-12:
            return 0.0
        return _plantar_trailing(beru, short=False, masa=orden, precio_activacion=px)
    return 0.0


def actualizar_trailing_oz(beru: Any, precio: float) -> bool:
    """Persigue el extremo; Oz callback; engorde doctrinal del tramo vivo."""
    if str(getattr(beru, "estado", "") or "") != "CAZANDO":
        return False
    px = float(precio or 0)
    if px <= 0:
        return False
    d = str(getattr(beru, "direccion", "") or "").upper()
    gap = trailing_dist_pct()
    extremo = float(getattr(beru, "trail_extremo", 0) or 0) or px
    oz_antes = float(getattr(beru, "oz_adan", 0) or 0)
    moved = False
    if d == "SHORT":
        if px > extremo + 1e-15:
            extremo = px
            moved = True
        beru.trail_extremo = extremo
        beru.oz_adan = extremo * (1.0 - gap)
    elif d == "LONG":
        if px < extremo - 1e-15 or extremo <= 0:
            extremo = px
            moved = True
        beru.trail_extremo = extremo
        beru.oz_adan = extremo * (1.0 + gap)
    else:
        return False
    beru.oz_pct = pct_desde_cero(beru, beru.oz_adan)
    if abs(float(beru.oz_adan) - oz_antes) > 1e-12:
        moved = True
    if actualizar_engorde(beru, extremo):
        moved = True
    return moved


def toca_oz(beru: Any, precio: float) -> bool:
    """Callback del trailing: SHORT baja a Oz; LONG sube a Oz."""
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
    """Activación 1,2 contraria desde wake (trailing opuesto $5)."""
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


def toca_red_activacion(beru: Any, precio: float) -> bool:
    """Activación del trailing Red (0,7 desde la Oz desplegada)."""
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


def toca_red_continuacion(beru: Any, precio: float) -> bool:
    return toca_red_activacion(beru, precio)


def secuencia_latido(
    precio: float,
    latido: dict[str, Any] | None = None,
) -> list[float]:
    """Tratos en orden; si no hay, last + alto + bajo del vaso."""
    lat = latido or {}
    prints = [float(p) for p in (lat.get("prints") or []) if float(p or 0) > 0]
    if prints:
        return prints
    last = float(lat.get("last") or precio or 0)
    out: list[float] = []
    for px in (last, float(lat.get("high") or 0), float(lat.get("low") or 0)):
        if px > 0 and (not out or abs(out[-1] - px) > 1e-12):
            if px not in out:
                out.append(px)
    return out


def toca_red_activacion_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    for px in secuencia_latido(precio, latido):
        if toca_red_activacion(beru, px):
            return True
    return False


def toca_sangre_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    for px in secuencia_latido(precio, latido):
        if toca_sangre(beru, px):
            return True
    return False


def toca_vacio_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> str:
    for px in secuencia_latido(precio, latido):
        lado = toca_vacio(beru, px)
        if lado:
            return lado
    return ""


def toca_oz_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    for px in secuencia_latido(precio, latido):
        if toca_oz(beru, px):
            return True
    return False


def extremo_latido_trailing(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> float:
    """Punta del latido hacia la caza: SHORT oye el alto; LONG el bajo."""
    seq = secuencia_latido(precio, latido)
    if not seq:
        return float(precio or 0)
    d = str(getattr(beru, "direccion", "") or "").upper()
    if d == "LONG":
        return min(seq)
    if d == "SHORT":
        return max(seq)
    return float(seq[-1])


def latido_rapido_s() -> float:
    return float(getattr(config, "BERU_RANGO_LATIDO_RAPIDO_S", 0.1) or 0.1)


def latido_cerca_pct() -> float:
    return float(getattr(config, "BERU_RANGO_LATIDO_CERCA_PCT", 0.002) or 0.002)


def latido_sugerido_s(
    beru: Any,
    precio: float | None = None,
    *,
    lento_s: float | None = None,
) -> float:
    """Cerca de orejas / cazando → latido rápido; lejos → lento."""
    lento = float(
        lento_s
        if lento_s is not None
        else getattr(config, "BERU_RANGO_LATIDO_LENTO_S", 1.5) or 1.5
    )
    rapido = latido_rapido_s()
    if beru is None:
        return max(0.05, lento)
    estado = str(getattr(beru, "estado", "") or "").upper()
    if estado == "CAZANDO":
        return max(0.05, rapido)
    px = float(precio or 0)
    if px <= 0:
        return max(0.05, lento)
    umbral = latido_cerca_pct()
    candidatos: list[float] = []
    red = float(getattr(beru, "red_adan", 0) or 0)
    if red > 0 and bool(getattr(beru, "oreja_red_activa", False)):
        candidatos.append(red)
    cero = cero_wake(beru)
    vac = vacio_adan_pct()
    if cero > 0 and not bool(getattr(beru, "es_relevo_cazador", False)):
        candidatos.extend([cero * (1.0 + vac), cero * (1.0 - vac)])
    lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    sil = sangre_contraria_pct()
    if cero > 0 and bool(getattr(beru, "oreja_sangre_activa", False)):
        if lado == "ABAJO":
            candidatos.append(cero * (1.0 - sil))
        elif lado == "ARRIBA":
            candidatos.append(cero * (1.0 + sil))
    for nivel in candidatos:
        if nivel <= 0:
            continue
        if abs(px - nivel) / nivel <= umbral + 1e-12:
            return max(0.05, rapido)
    return max(0.05, lento)


def _cancelar_red(beru: Any) -> None:
    """Sangre ganó: elimina el trailing Red que esperaba."""
    beru.oreja_red_activa = False
    beru.red_adan = 0.0
    beru.red_pct = 0.0


def _plantar_orejas_post_oz(beru: Any, ancla_red: float, direccion: str) -> None:
    """Tras Oz: sangre 1,2 desde wake + Red 0,7 desde ancla (peldaño/fill peor)."""
    sil = sangre_contraria_pct()
    red_act = red_activacion_pct()
    beru.llamado_tramo_pct = sil
    d = str(direccion or "").upper()
    ancla = float(ancla_red or 0)
    if d == "SHORT":
        beru.sangre_lado = "ABAJO"
        beru.red_adan = ancla * (1.0 + red_act) if ancla > 0 else 0.0
        beru.red_pct = red_act
    else:
        beru.sangre_lado = "ARRIBA"
        beru.red_adan = ancla * (1.0 - red_act) if ancla > 0 else 0.0
        beru.red_pct = -red_act
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = True


def restaurar_acecho_post_oz(
    beru: Any,
    *,
    cero: float,
    red: float,
    sangre_lado: str,
    ultima_hoz_direccion: str = "",
    escalones_red: int = 0,
    cosechas: int = 0,
    oz_despliegue: float = 0.0,
) -> None:
    """Reengancha acecho tras sello: wake / Red / sangre (sin nuevo wake)."""
    wake = float(cero or 0)
    if wake <= 0 or beru is None:
        return
    lado = str(sangre_lado or "").upper()
    hoz = str(ultima_hoz_direccion or "").upper()
    if not hoz:
        hoz = "LONG" if lado == "ARRIBA" else "SHORT" if lado == "ABAJO" else "LONG"
    red_px = float(red or 0)
    red_act = red_activacion_pct()
    oz_dep = float(oz_despliegue or 0)
    if red_px <= 0:
        ancla = oz_dep if oz_dep > 0 else wake
        red_px = red_desde_ancla(ancla, hoz)
    beru.cero_wake = wake
    beru.centro_local = wake
    beru.ancla_tramo = wake
    beru.centro_manto = wake
    beru.estado = "ACECHANDO"
    beru.direccion = ""
    beru.oz_adan = 0.0
    beru.oz_pct = 0.0
    beru.oz_despliegue_px = oz_dep
    beru.trail_extremo = 0.0
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.sangre_vista_dentro = True
    beru.es_relevo_cazador = True
    beru.engorde_bloqueado = True
    beru.ultima_hoz_direccion = hoz
    beru.sangre_lado = lado or ("ABAJO" if hoz == "SHORT" else "ARRIBA")
    beru.llamado_tramo_pct = sangre_contraria_pct()
    beru.red_adan = red_px
    beru.red_pct = red_act if beru.sangre_lado == "ABAJO" else -red_act
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = True
    beru.rango_escalones_red = int(escalones_red or 0)
    beru.cosechas_continuas = int(cosechas or 0)
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    beru.altar_cancel_confirmado = False


def restaurar_caza_trailing(
    beru: Any,
    *,
    cero: float,
    direccion: str,
    oz: float,
    trail_extremo: float,
    masa: float,
    altar_link_id: str = "",
    altar_order_id: str = "",
    altar_trigger_price: float = 0.0,
    altar_revision: int = 0,
    sangre_lado: str = "",
    escalones_red: int = 0,
    cosechas: int = 0,
    uid: str = "",
) -> None:
    """Reengancha CAZANDO mid-hunt: Oz + extremo + sello del altar (Stop vivo)."""
    if beru is None:
        return
    d = str(direccion or "").upper()
    if d not in ("LONG", "SHORT"):
        return
    c0 = float(cero or 0)
    oz_px = float(oz or 0)
    ext = float(trail_extremo or 0) or oz_px
    if c0 <= 0 or oz_px <= 0:
        return
    if uid:
        beru.uid = str(uid)
    beru.cero_wake = c0
    beru.centro_local = c0
    beru.ancla_tramo = c0
    beru.centro_manto = c0
    beru.estado = "CAZANDO"
    beru.direccion = d
    beru.trail_extremo = ext
    beru.oz_adan = oz_px
    beru.oz_pct = pct_desde_cero(beru, oz_px)
    beru.llamado_tramo_pct = trailing_dist_pct()
    beru.masa = float(masa or 0) or masa_tramo_usd()
    beru.masa_tramo_usd = float(beru.masa)
    beru.red_adan = 0.0
    beru.red_pct = 0.0
    beru.oreja_sangre_activa = False
    beru.oreja_red_activa = False
    beru.sangre_vista_dentro = True
    beru.es_relevo_cazador = True
    beru.engorde_bloqueado = False
    beru.sangre_lado = str(sangre_lado or "")
    beru.rango_escalones_red = int(escalones_red or 0)
    beru.cosechas_continuas = int(cosechas or 0)
    beru.altar_revision = int(altar_revision or 0)
    beru.altar_link_id = str(altar_link_id or "")
    beru.altar_order_id = str(altar_order_id or "")
    beru.altar_order_status = "Untriggered" if beru.altar_link_id else ""
    beru.altar_trigger_price = float(altar_trigger_price or oz_px)
    beru.altar_cancel_confirmado = False


def cosechar_oz_y_mover_cero(
    beru: Any,
    precio_fill: float,
    *,
    oz_despliegue: float | None = None,
) -> float:
    """Trailing detonó: wake intacto; fill → Tusk; Red desde peldaño Oz."""
    oz_dep = float(
        oz_despliegue
        if oz_despliegue is not None
        else getattr(beru, "oz_adan", 0) or 0
    )
    fill = float(precio_fill or 0) or oz_dep
    if fill <= 0 and oz_dep <= 0:
        return 0.0
    if oz_dep <= 0:
        oz_dep = fill
    d = str(getattr(beru, "direccion", "") or "").upper()
    masa_hecha = float(getattr(beru, "masa", 0) or 0) or masa_tramo_usd()
    wake = cero_wake(beru)
    beru.ultima_hoz_tocada_precio = fill
    beru.ultima_hoz_tocada_pct = pct_desde_cero(beru, fill) if wake > 0 else 0.0
    beru.ultima_hoz_direccion = d
    beru.ultima_masa_cosechada = masa_hecha
    beru.precio_entrada_real = fill
    beru.oz_despliegue_px = oz_dep
    if d in ("LONG", "SHORT"):
        registrar_saco(beru, d, masa_hecha)
    # Wake eterno — no pisar centro_local / cero_wake
    if wake > 0:
        beru.cero_wake = wake
        beru.centro_local = wake
        beru.ancla_tramo = wake
        beru.centro_manto = wake
    beru.estado = "ACECHANDO"
    beru.sangre_vista_dentro = True
    beru.es_relevo_cazador = True
    beru.engorde_bloqueado = True
    beru.engorde_ancla_px = 0.0
    beru.oz_adan = 0.0
    beru.oz_pct = 0.0
    beru.trail_extremo = 0.0
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.direccion = ""
    ancla = ancla_mapa_red(oz_dep, fill, d)
    _plantar_orejas_post_oz(beru, ancla, d)
    beru.cosechas_continuas = int(getattr(beru, "cosechas_continuas", 0) or 0) + 1
    # Acecho: sin Stop heredado de la caza (cancel en manos vía cancelar_pendiente).
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    beru.altar_cancel_confirmado = False
    return masa_sangre_usd()


def armar_tramo_desde_sangre(beru: Any, precio: float | None = None) -> float:
    """Sangre → trailing $5 al nacer; engorde luego solo desde activación; mata Red."""
    _cancelar_red(beru)
    lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    masa = masa_sangre_usd()
    vac = vacio_adan_pct()

    def _arm(short: bool, px: float) -> float:
        beru.origen_tramo = "SANGRE"
        return _plantar_trailing(beru, short=short, masa=masa, precio_activacion=px)

    if lado == "ABAJO":
        px = float(precio or 0) or precio_desde_cero(beru, -vac)
        return _arm(False, px)
    if lado == "ARRIBA":
        px = float(precio or 0) or precio_desde_cero(beru, vac)
        return _arm(True, px)
    oz_dir = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if oz_dir == "SHORT":
        px = float(precio or 0) or precio_desde_cero(beru, -vac)
        return _arm(False, px)
    if oz_dir == "LONG":
        px = float(precio or 0) or precio_desde_cero(beru, vac)
        return _arm(True, px)
    return 0.0


def armar_tramo_desde_red(beru: Any, precio: float | None = None) -> float:
    """Red → nace en $5; engorde desde activación; cupo = meta − saco (anti-stack)."""
    red = float(getattr(beru, "red_adan", 0) or 0)
    px = float(precio or 0) or red
    if px <= 0:
        return 0.0
    d = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if d not in ("LONG", "SHORT"):
        return 0.0
    beru.origen_tramo = "RED"
    orden = orden_nacimiento_usd(beru, lado=d, precio=px, origen="RED")
    if orden <= 1e-12:
        return 0.0
    if d == "SHORT":
        out = _plantar_trailing(beru, short=True, masa=orden, precio_activacion=px)
    else:
        out = _plantar_trailing(beru, short=False, masa=orden, precio_activacion=px)
    if out > 0:
        beru.rango_escalones_red = int(getattr(beru, "rango_escalones_red", 0) or 0) + 1
    return out


def resumen_geometria() -> dict[str, float | str]:
    perfil = str(getattr(config, "BERU_RANGO_PERFIL", "normal") or "normal")
    return {
        "oficio": "RANGO",
        "perfil": perfil,
        "mercado": "linear",
        "vacio_pct": vacio_adan_pct(),
        "vacio_rol": "activacion_trailing",
        "oz_gap_pct": trailing_dist_pct(),
        "oz_modo": "trailing_callback",
        "red_activacion_pct": red_activacion_pct(),
        "red_desde_oz_pct": red_activacion_pct(),
        "red_modo": "trailing",
        "red_callback_pct": trailing_dist_pct(),
        "sangre_pct": sangre_contraria_pct(),
        "sangre_rol": "activacion_trailing",
        "masa_usd": masa_tramo_usd(),
        "masa_red_usd": masa_red_usd(),
        "masa_sangre_usd": masa_sangre_usd(),
        "trailing_pct": trailing_dist_pct(),
        "engorde_usd": engorde_paso_usd(),
        "engorde_paso_pct": engorde_paso_pct(),
        "cero": "wake",
        "nacimiento": "cinco_usd",
        "engorde": "desde_activacion",
        "saco_techo": "meta_menos_ya",
        "ladder_red": "si",
    }
