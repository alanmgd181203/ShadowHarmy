"""Beru cazador puro — Hoz/Red y relevo desde la última Red tocada.

Primera caza:
  Vacío de Adán ±1.1% desde el 0 local de wake (precio al nacer).
  El metro es el 0 del manto: puntos de ese metro, sin composición.
  Hoz un peldaño detrás (±1.0%). Los cuatro grados oyen el mismo silbato;
  solo cambia el dólar por peldaño.

Tras cada cosecha confirmada (los cuatro grados, Mariscal incluido):
  el 0 del manto NO cambia. El padre muere. El hijo oye DOS orejas:
  sangre 1.1 al otro lado de la última Hoz cobrada, y Red en la tendencia
  (0.9/0.5/0.3; Mariscal un peldaño 0.1). Dual Vacío solo al nacer. Si la Red
  despierta al nuevo Beru, la sangre vieja se apaga.

La masa de cada tramo es distancia hasta Hoz × engorde por peldaño. Si al
nacer el precio ya pasó el silbato, la primera Hoz nace un peldaño detrás
de ahora y la masa cuenta esos peldaños desde el 0 de esa Oz. Si el precio
continúa, Red/Hoz avanzan 0.1% y añaden otro peldaño. Al tocar Hoz se
transmuta todo el tramo y su cuenta local vuelve a cero.

No existe oficio negociador, masa congelada, ping-pong, residual, fusión ni Mega.
"""
from __future__ import annotations

from typing import Any

from core import beru_cazador
import core.config as config


def cosechas_hechas(beru: Any) -> int:
    return max(0, int(getattr(beru, "cosechas_continuas", 0) or 0))


def es_primer_tramo(beru: Any) -> bool:
    return cosechas_hechas(beru) == 0


def paso_pct() -> float:
    return float(beru_cazador.paso_pct())


def vacio_adan_pct(beru: Any | None = None) -> float:
    adn = getattr(beru, "adn_capitan", None) if beru is not None else None
    valor = float(getattr(adn, "vacio_adan", 0) or 0)
    if valor > 0:
        return valor
    return float(getattr(config, "BERU_VACIO_NORMAL", 0.011) or 0.011)


def distancia_llamado_pct(beru: Any) -> float:
    """Distancia del llamado de sangre desde el 0 local.

    Semilla y sangre post-Hoz: Vacío ±1.1 %. Si ganó la oreja de Red,
    el silbato pasa a 0.9/0.5/0.3 del relevo.
    """
    silbato = float(getattr(beru, "llamado_tramo_pct", 0) or 0)
    if silbato > 0:
        return silbato
    return float(beru_cazador.llamado_sangre_pct())


def distancia_hoz_pct(beru: Any) -> float:
    silbato = float(getattr(beru, "llamado_tramo_pct", 0) or 0)
    if silbato > 0:
        return max(paso_pct(), silbato - paso_pct())
    return float(beru_cazador.hoz_productiva_pct())


def beneficio_desde_manto_pct(beru: Any, precio_fill: float) -> float:
    """% capturado vs el 0 del manto. SHORT vende arriba; LONG compra abajo."""
    centro = float(getattr(beru, "centro_manto", 0) or 0)
    fill = float(precio_fill or 0)
    if centro <= 0 or fill <= 0:
        return 0.0
    pct = (fill - centro) / centro
    if str(getattr(beru, "direccion", "") or "").upper() == "LONG":
        return -pct
    return pct


def beneficio_ida_vuelta_pct(direccion: str, entrada: float, salida: float) -> float:
    """Ida y vuelta con signo. Una pérdida no se disfraza de botín."""
    e = float(entrada or 0)
    s = float(salida or 0)
    if e <= 0 or s <= 0:
        return 0.0
    if str(direccion or "").upper() == "SHORT":
        return (e - s) / e
    return (s - e) / e


def beneficio_cosecha_pct(beru: Any, precio_fill: float) -> float:
    """Si hubo dos fills, PnL firmado. Si la Hoz es el único fill, % vs manto."""
    entrada = float(getattr(beru, "precio_entrada_real", 0) or 0)
    fill = float(precio_fill or 0)
    if entrada > 0 and fill > 0 and abs(fill - entrada) / entrada > 1e-12:
        return beneficio_ida_vuelta_pct(
            str(getattr(beru, "direccion", "") or ""),
            entrada,
            fill,
        )
    return beneficio_desde_manto_pct(beru, fill)


def precio_ultima_hoz(beru: Any) -> float:
    """Altar vivo (Hoz plantada); si ya no está, la última Hoz tocada."""
    for attr in ("oz_adan", "ultima_hoz_tocada_precio"):
        v = float(getattr(beru, attr, 0) or 0)
        if v > 0:
            return v
    return 0.0


def beneficio_desde_hoz_pct(beru: Any, precio_fill: float) -> float:
    """% de la transmutación vs la última Hoz. Fill en el altar ≈ 0."""
    hoz = precio_ultima_hoz(beru)
    fill = float(precio_fill or 0)
    if hoz <= 0 or fill <= 0:
        return 0.0
    return beneficio_ida_vuelta_pct(
        str(getattr(beru, "direccion", "") or ""),
        hoz,
        fill,
    )


def lecturas_cosecha(beru: Any, precio_fill: float) -> dict[str, float]:
    """Dos reglas, no una: metro (manto) y caza (última Hoz)."""
    fill = float(precio_fill or 0)
    return {
        "metro": float(beneficio_desde_manto_pct(beru, fill) or 0),
        "hoz": float(beneficio_desde_hoz_pct(beru, fill) or 0),
        "precio_hoz": float(precio_ultima_hoz(beru) or 0),
        "precio_manto": float(getattr(beru, "centro_manto", 0) or 0),
        "precio_fill": fill,
    }


def _sello_botin(pct: float) -> str:
    return "Botín" if float(pct or 0) >= 0 else "Merma"


def texto_lecturas_cosecha(lec: dict[str, float]) -> str:
    """Una línea: metro …% · Hoz …%."""
    m = float(lec.get("metro") or 0)
    h = float(lec.get("hoz") or 0)
    return (
        f"metro {_sello_botin(m)} {m * 100:.2f}% · "
        f"Hoz {_sello_botin(h)} {h * 100:.2f}%"
    )


def extra_bitacora_cosecha(lec: dict[str, float]) -> dict[str, float | None]:
    """Campos de bitácora/crónica. beneficio_pct = metro (compat)."""
    m = float(lec.get("metro") or 0)
    h = float(lec.get("hoz") or 0)
    hoz_px = float(lec.get("precio_hoz") or 0)
    manto_px = float(lec.get("precio_manto") or 0)
    return {
        "beneficio_pct": round(m * 100.0, 4),
        "beneficio_metro_pct": round(m * 100.0, 4),
        "beneficio_hoz_pct": round(h * 100.0, 4),
        "precio_hoz": round(hoz_px, 10) if hoz_px > 0 else None,
        "precio_manto": round(manto_px, 10) if manto_px > 0 else None,
    }


def ancla_tramo(beru: Any) -> float:
    """0 local: wake en la semilla; última Red tocada en el relevo.

    Nunca el manto: ese es solo el metro de los puntos porcentuales.
    """
    ancla = float(getattr(beru, "ancla_tramo", 0) or 0)
    if ancla > 0:
        return ancla
    local = float(getattr(beru, "centro_local", 0) or 0)
    if local > 0:
        return local
    return float(getattr(beru, "centro_manto", 0) or 0)


def escala_manto(beru: Any) -> float:
    """Metro absoluto Igris. Si falta, se usa el 0 local (no inventar)."""
    escala = float(getattr(beru, "centro_manto", 0) or 0)
    if escala > 0:
        return escala
    return ancla_tramo(beru)


def pct_desde_ancla(beru: Any, precio: float) -> float:
    """Puntos del manto desde el 0 local. Semilla y relevo usan la misma regla."""
    ancla = ancla_tramo(beru)
    escala = escala_manto(beru)
    px = float(precio or 0)
    if ancla <= 0 or escala <= 0:
        return 0.0
    return (px - ancla) / escala


def precio_desde_ancla(beru: Any, pct: float) -> float:
    ancla = ancla_tramo(beru)
    escala = escala_manto(beru)
    if ancla <= 0 or escala <= 0:
        return 0.0
    return ancla + escala * float(pct)


def toca_llamado(beru: Any, precio: float) -> bool:
    """Vacío de Adán. Semilla: ±1,1. Tras la primera Hoz: solo el lado contrario."""
    umbral = distancia_llamado_pct(beru)
    px = float(precio or 0)
    if umbral <= 0 or px <= 0:
        return False
    if sangre_dual(beru):
        pct = pct_desde_ancla(beru, px)
        if abs(pct) < umbral - 1e-9:
            beru.sangre_vista_dentro = True
            return False
        if not bool(getattr(beru, "sangre_vista_dentro", False)):
            return False
        return abs(pct) >= umbral - 1e-9
    oz = ancla_sangre_contraria(beru)
    escala = escala_manto(beru)
    signo = signo_sangre_contraria(beru)
    if oz <= 0 or escala <= 0 or signo == 0:
        return False
    pct = (px - oz) / escala
    if signo < 0:
        if pct > -umbral + 1e-9:
            if pct >= -1e-9:
                beru.sangre_vista_dentro = True
            return False
        if not bool(getattr(beru, "sangre_vista_dentro", False)):
            return False
        return pct <= -umbral + 1e-9
    if pct < umbral - 1e-9:
        if pct <= 1e-9:
            beru.sangre_vista_dentro = True
        return False
    if not bool(getattr(beru, "sangre_vista_dentro", False)):
        return False
    return pct >= umbral - 1e-9


def sangre_dual(beru: Any) -> bool:
    """Dos Vacío solo al nacer: aún no hay Hoz, no sabemos arriba o abajo."""
    if bool(getattr(beru, "es_relevo_cazador", False)):
        return False
    if str(getattr(beru, "estado", "") or "").upper() == "CAZANDO":
        return False
    if float(getattr(beru, "oz_adan", 0) or 0) > 0:
        return False
    if float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0) > 0:
        return False
    return True


def signo_sangre_contraria(beru: Any) -> int:
    """Tras SHORT la sangre es abajo (−). Tras LONG, arriba (+)."""
    d = str(getattr(beru, "direccion", "") or "").upper()
    if d == "SHORT":
        return -1
    if d == "LONG":
        return 1
    return 0


def ancla_sangre_contraria(beru: Any) -> float:
    """Sangre desde la última Oz cobrada, nunca desde la Hoz que persigue ahora."""
    hoz = float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0)
    if hoz > 0:
        return hoz
    return ancla_tramo(beru)


def precio_sangre_contraria(beru: Any) -> float:
    oz = ancla_sangre_contraria(beru)
    escala = escala_manto(beru)
    off = vacio_adan_pct(beru)
    signo = signo_sangre_contraria(beru)
    if oz <= 0 or escala <= 0 or off <= 0 or signo == 0:
        return 0.0
    return oz + signo * escala * off


def apagar_llamado_sangre(beru: Any) -> bool:
    """Apaga la sangre pendiente. No deja un oído viejo vivo."""
    viva = bool(getattr(beru, "oreja_sangre_activa", False))
    beru.oreja_sangre_activa = False
    return viva


def apagar_orejas_acecho(beru: Any) -> None:
    apagar_llamado_sangre(beru)
    beru.oreja_red_activa = False


def offset_oreja_red(beru: Any, grado: str = "") -> float:
    """0,9 / 0,5 / 0,3 del relevo. Si el barco ya lo trae escrito, manda eso."""
    off = float(getattr(beru, "llamado_red_pct", 0) or 0)
    if off > 0:
        return off
    g = str(grado or "").upper()
    if not g:
        from core.beru_capital import grado_desde_tier

        tid = str(getattr(beru, "tier_id", "") or "")
        g = grado_desde_tier(tid) if tid else "SOLDADO"
    return float(beru_cazador.relevo_llamado_pct(g))


def precio_oreja_red(beru: Any, grado: str = "") -> float:
    """Precio de la Red de relevo (oído, no carta). 0 si esa oreja no está viva."""
    if not bool(getattr(beru, "oreja_red_activa", False)):
        return 0.0
    ancla = float(getattr(beru, "ultima_red_tocada_precio", 0) or 0)
    escala = escala_manto(beru)
    off = offset_oreja_red(beru, grado)
    if ancla <= 0 or escala <= 0 or off <= 0:
        return 0.0
    direccion = str(getattr(beru, "direccion", "") or "").upper()
    if direccion == "LONG":
        return ancla - escala * off
    return ancla + escala * off


def precio_hoz_si_oreja_red(beru: Any, grado: str = "") -> float:
    """Dónde nacería la Hoz si el relevo toca ahora. Un peldaño detrás de esa Red."""
    ancla = float(getattr(beru, "ultima_red_tocada_precio", 0) or 0)
    escala = escala_manto(beru)
    off = offset_oreja_red(beru, grado)
    if ancla <= 0 or escala <= 0 or off <= 0:
        return 0.0
    hoz_off = max(paso_pct(), off - paso_pct())
    direccion = str(getattr(beru, "direccion", "") or "").upper()
    if direccion == "LONG":
        return ancla - escala * hoz_off
    return ancla + escala * hoz_off


def masa_prometida_silbato_usd(
    beru: Any,
    activo: str,
    grado: str,
    *,
    oreja: str = "SANGRE",
) -> float:
    """Masa doctrinal del tramo si ese silbato despierta ahora (antes del lote)."""
    por = float(beru_cazador.engorde_paso_usd(activo, grado))
    if str(oreja or "").upper() == "RED":
        off = offset_oreja_red(beru, grado)
        dist = max(paso_pct(), off - paso_pct())
    else:
        dist = distancia_hoz_pct(beru)
    return max(0.0, por * (dist / max(paso_pct(), 1e-12)))


def toca_oreja_red(beru: Any, precio: float) -> bool:
    """Red de continuación 0.9/0.5/0.3 desde la última Red tocada."""
    if not bool(getattr(beru, "oreja_red_activa", False)):
        return False
    ancla = float(getattr(beru, "ultima_red_tocada_precio", 0) or 0)
    escala = escala_manto(beru)
    off = offset_oreja_red(beru)
    px = float(precio or 0)
    if ancla <= 0 or escala <= 0 or off <= 0 or px <= 0:
        return False
    pct = (px - ancla) / escala
    direccion = str(getattr(beru, "direccion", "") or "").upper()
    if direccion == "LONG":
        return pct <= -off + 1e-9
    return pct >= off - 1e-9


def _px_nuevo(seq: list[float], px: float) -> bool:
    if px <= 0:
        return False
    return all(abs(px - q) > 1e-12 for q in seq)


def secuencia_latido_spot(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> list[float]:
    """Mismo río para acecho y caza: tratos en orden; si no, last + alto + bajo."""
    _ = beru
    lat = latido or {}
    prints = [float(p) for p in (lat.get("prints") or []) if float(p or 0) > 0]
    if prints:
        return prints
    last = float(lat.get("last") or precio or 0)
    out: list[float] = []
    for px in (last, float(lat.get("high") or 0), float(lat.get("low") or 0)):
        if _px_nuevo(out, px):
            out.append(px)
    return out


def toca_red_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    """La Red viva se tocó en este latido (trato o extremo), no solo el last ahora."""
    from core import beru_cazador

    red = float(getattr(beru, "red_adan", 0) or 0)
    direccion = str(getattr(beru, "direccion", "") or "")
    for px in secuencia_latido_spot(beru, precio, latido):
        if beru_cazador.toca_red(px, direccion, red):
            return True
    return False


def toca_oz_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    """La mecha rozó la Hoz. En vivo no cosecha: solo pide fill a casa."""
    from core import beru_cazador

    oz = float(getattr(beru, "oz_adan", 0) or 0)
    direccion = str(getattr(beru, "direccion", "") or "")
    for px in secuencia_latido_spot(beru, precio, latido):
        if beru_cazador.toca_oz(px, direccion, oz):
            return True
    return False


def last_bajo_hoz_venta(beru: Any, precio: float) -> bool:
    """Caza SHORT: el last ya está bajo la Hoz. Pose sana = Hoz abajo, Red arriba."""
    if str(getattr(beru, "direccion", "") or "").upper() != "SHORT":
        return False
    oz = float(getattr(beru, "oz_adan", 0) or 0)
    px = float(precio or 0)
    return oz > 0 and px > 0 and px < oz - 1e-9


def extremo_latido_caza(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> float:
    """Punta del latido hacia la Red: SHORT oye el alto; LONG el bajo."""
    seq = secuencia_latido_spot(beru, precio, latido)
    if not seq:
        return float(precio or 0)
    direccion = str(getattr(beru, "direccion", "") or "").upper()
    if direccion == "LONG":
        return min(seq)
    return max(seq)


def n_peldaños_red(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
    *,
    tope: int = 20,
) -> int:
    """Cuántos pisos de Red ya pisó este latido (regilla del metro, sin mutar)."""
    from core import beru_cazador

    px = extremo_latido_caza(beru, precio, latido)
    if px <= 0:
        return 0
    direccion = str(getattr(beru, "direccion", "") or "")
    oz_pct = float(getattr(beru, "oz_pct", 0) or 0)
    red_pct = float(getattr(beru, "red_pct", 0) or 0)
    n = 0
    tope_n = max(1, int(tope or 20))
    while n < tope_n:
        red_px = precio_desde_ancla(beru, red_pct)
        if not beru_cazador.toca_red(px, direccion, red_px):
            break
        n += 1
        oz_pct, red_pct = beru_cazador.mover_niveles_cazador(
            direccion, oz_pct, red_pct,
        )
    return n


def saltar_pisos_red(beru: Any, n: int, masa_extra: float) -> None:
    """Corre n peldaños de la regilla y suma la masa de golpe."""
    pasos = max(0, int(n or 0))
    extra = max(0.0, float(masa_extra or 0))
    if pasos <= 0:
        return
    from core.beru_altar_cazador import registrar_red_tocada

    for _ in range(pasos):
        registrar_red_tocada(beru)
        avanzar_frontera(beru, 0.0)
    if extra > 0:
        beru.masa = float(getattr(beru, "masa", 0) or 0) + extra
        beru.masa_tramo_usd = beru.masa


def decidir_oreja_acecho(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> str:
    """Qué oído gana este latido: RED (mata sangre), SANGRE, o nada.

    Mismo río que la caza: tratos en orden; si no, last + alto + bajo.
    El primer toque gana.
    """
    seq = secuencia_latido_spot(beru, precio, latido)
    if not seq:
        px = float(precio or 0)
        seq = [px] if px > 0 else []
    for px in seq:
        oreja = _decidir_oreja_un_precio(beru, px)
        if oreja:
            if latido is not None:
                latido["toque"] = px
            return oreja
    return ""


def _decidir_oreja_un_precio(beru: Any, precio: float) -> str:
    """Un solo last: RED gana a sangre. La vista-dentro se acumula en el barco."""
    if toca_oreja_red(beru, precio):
        apagar_llamado_sangre(beru)
        beru.oreja_red_activa = False
        red_px = float(getattr(beru, "ultima_red_tocada_precio", 0) or 0)
        beru.ancla_tramo = red_px
        beru.centro_local = red_px
        beru.llamado_tramo_pct = float(getattr(beru, "llamado_red_pct", 0) or 0)
        beru.sangre_vista_dentro = True
        return "RED"
    sangre_viva = bool(getattr(beru, "oreja_sangre_activa", False))
    es_semilla = not bool(getattr(beru, "es_relevo_cazador", False))
    if sangre_viva or es_semilla:
        if toca_llamado(beru, precio):
            apagar_orejas_acecho(beru)
            return "SANGRE"
    return ""


def boveda_ahogada(tusk: Any = None) -> bool:
    """Tusk sin aire: disponible ≤ 0 o estado ahogada. No usa masa_autorizada sola."""
    if tusk is None:
        return False
    tes = getattr(tusk, "tesoreria", None) or {}
    if not isinstance(tes, dict):
        tes = {}
    if str(tes.get("estado") or "").lower() == "ahogada":
        return True
    try:
        disp = tes.get("disponible_usd")
        if disp is not None and float(disp) <= 0:
            return True
    except (TypeError, ValueError):
        pass
    return False


def masa_tramo_inicial_usd(
    beru: Any,
    activo: str,
    grado: str,
    *,
    ahogada: bool = False,
) -> float:
    """Masa escrita por el manto hasta la Hoz de este tramo.

    Si la bóveda está ahogada: un peldaño (carta chica en la Oz), no
    peldaños × grado. El precio de la Hoz sigue un peldaño detrás de ahora.
    """
    por_peldano = beru_cazador.engorde_paso_usd(activo, grado)
    if ahogada:
        return max(0.0, float(por_peldano))
    hoz_pct = abs(float(getattr(beru, "oz_pct", 0) or 0))
    distancia = hoz_pct if hoz_pct > 0 else distancia_hoz_pct(beru)
    peldaños = distancia / max(paso_pct(), 1e-12)
    return max(0.0, float(por_peldano) * float(peldaños))


def niveles_desde_llamado(
    beru: Any,
    signo: int,
    *,
    touch_pct: float | None = None,
) -> tuple[float, float]:
    """Hoz un peldaño detrás del silbato. Si ya pasó, Hoz un peldaño detrás de ahora."""
    s = 1 if signo >= 0 else -1
    paso = paso_pct()
    hoz_primera = distancia_hoz_pct(beru)
    red_primera = distancia_llamado_pct(beru) + paso
    if touch_pct is None:
        return s * hoz_primera, s * red_primera
    dist = abs(float(touch_pct))
    silbato = distancia_llamado_pct(beru)
    if dist <= silbato + 1e-9:
        return s * hoz_primera, s * red_primera
    n_ahora = max(0, int(dist / max(paso, 1e-12) + 1e-9))
    n_hoz_min = max(1, int(hoz_primera / max(paso, 1e-12) + 1e-9))
    n_hoz = max(n_hoz_min, n_ahora - 1)
    hoz_abs = n_hoz * paso
    return s * hoz_abs, s * (hoz_abs + paso)


def armar_tramo(
    beru: Any,
    precio: float,
    *,
    activo: str,
    grado: str,
    oreja: str = "SANGRE",
    tusk: Any = None,
) -> float:
    """Arma Hoz/Red. El llamado de sangre no ejecuta fill; solo la Hoz."""
    ancla = ancla_tramo(beru)
    px = float(precio or 0)
    if ancla <= 0 or px <= 0:
        return 0.0
    touch = pct_desde_ancla(beru, px)
    signo = 1 if touch >= 0 else -1
    if str(oreja or "").upper() == "RED":
        off = float(getattr(beru, "llamado_red_pct", 0) or 0)
        if off <= 0:
            from core.beru_capital import grado_desde_tier

            tid = str(getattr(beru, "tier_id", "") or "")
            g = grado or grado_desde_tier(tid) if tid else grado
            off = float(beru_cazador.relevo_llamado_pct(g))
            beru.llamado_red_pct = off
        beru.llamado_tramo_pct = off
        signo = -1 if str(getattr(beru, "direccion", "") or "").upper() == "LONG" else 1
    oz_pct, red_pct = niveles_desde_llamado(
        beru, signo, touch_pct=touch,
    )
    beru.ancla_tramo = ancla
    beru.centro_local = ancla
    beru.direccion = "SHORT" if signo > 0 else "LONG"
    beru.oz_pct = oz_pct
    beru.red_pct = red_pct
    beru.oz_adan = precio_desde_ancla(beru, oz_pct)
    beru.red_adan = precio_desde_ancla(beru, red_pct)
    # La Red plantada queda un paso más afuera. La frontera que desplegó
    # esta Hoz es la inmediatamente anterior (la llamada en el primer tramo).
    beru.ultima_red_tocada_pct = beru_cazador.ultima_red_tocada_pct(
        red_pct, beru.direccion,
    )
    beru.ultima_red_tocada_precio = precio_desde_ancla(
        beru, beru.ultima_red_tocada_pct,
    )
    beru.funeral_red_confirmado = False
    beru.modo_combate = "CAZA"
    beru.estado = "CAZANDO"
    beru.masa = masa_tramo_inicial_usd(
        beru, activo, grado, ahogada=boveda_ahogada(tusk),
    )
    beru.masa_tramo_usd = beru.masa
    return float(beru.masa)


def avanzar_frontera(beru: Any, masa_extra: float) -> None:
    beru.masa = float(getattr(beru, "masa", 0) or 0) + max(0.0, float(masa_extra or 0))
    beru.masa_tramo_usd = beru.masa
    beru.oz_pct, beru.red_pct = beru_cazador.mover_niveles_cazador(
        beru.direccion,
        float(getattr(beru, "oz_pct", 0) or 0),
        float(getattr(beru, "red_pct", 0) or 0),
    )
    ancla = ancla_tramo(beru)
    beru.oz_adan = precio_desde_ancla(beru, beru.oz_pct)
    beru.red_adan = precio_desde_ancla(beru, beru.red_pct)


def plantar_orejas_post_hoz(
    beru: Any,
    precio_hoz: float,
    *,
    activo: str,
    grado: str,
) -> Any:
    """Tras cosecha: una sangre, la contraria a la Hoz cobrada; Red en tendencia.

    Ninguna oreja es condicional. Solo la Hoz lo es, cuando el silbato detona.
    """
    fill = float(precio_hoz or 0)
    if fill <= 0:
        return None

    escala = escala_manto(beru)
    if escala <= 0:
        return None

    hoz_pct = float(getattr(beru, "ultima_hoz_tocada_pct", 0) or 0)
    if hoz_pct == 0:
        ancla_prev = float(getattr(beru, "ancla_tramo", 0) or 0)
        if ancla_prev > 0 and escala > 0:
            hoz_pct = (fill - ancla_prev) / escala
    red_pct = float(getattr(beru, "ultima_red_tocada_pct", 0) or 0)
    red_px = float(getattr(beru, "ultima_red_tocada_precio", 0) or 0)
    if red_px <= 0 and red_pct != 0:
        ancla = float(getattr(beru, "ancla_tramo", 0) or 0)
        if ancla > 0:
            red_px = ancla + escala * red_pct

    sangre_off = float(beru_cazador.llamado_sangre_pct())
    red_off = float(beru_cazador.relevo_llamado_pct(grado))

    from core.models import BeruShip

    gen = int(getattr(beru, "generacion", 1) or 1) + 1
    cola = str(getattr(beru, "uid", "") or "")[-12:].replace(":", "_")
    uid = f"BERU_SEM_{str(activo or 'ETH').upper()}_R{gen}_{cola}"
    hijo = BeruShip(
        uid=uid,
        centro_local=fill,
        centro_manto=float(getattr(beru, "centro_manto", 0) or 0),
        ancla_tramo=fill,
        masa=0.0,
        direccion=str(getattr(beru, "direccion", "LONG") or "LONG"),
        estado="ACECHANDO",
        generacion=int(getattr(beru, "generacion", 1) or 1) + 1,
        adn_capitan=getattr(beru, "adn_capitan", None),
        tier_id=str(getattr(beru, "tier_id", "") or ""),
        modo_combate="CAZA",
        arma_cazador="",
        ultima_hoz_tocada_pct=hoz_pct,
        ultima_hoz_tocada_precio=fill,
        ultima_red_tocada_pct=red_pct,
        ultima_red_tocada_precio=red_px,
        oreja_sangre_activa=True,
        oreja_red_activa=red_px > 0,
        llamado_red_pct=red_off,
        es_relevo_cazador=True,
        padre_cazador_uid=str(getattr(beru, "uid", "") or ""),
        frente_asignado=str(getattr(beru, "frente_asignado", "INDEFINIDO") or "INDEFINIDO"),
        ciclo_infinito=False,
        neg_post_cazador=False,
        masa_congelada=0.0,
        sangre_vista_dentro=True,
        ts_wake=float(getattr(beru, "ts_wake", 0) or 0),
    )
    _ = sangre_off  # sangre siempre Vacío 1.1 vía distancia_llamado_pct default
    beru.relevo_cazador_uid = uid
    return hijo


def activo_de_barco(beru: Any) -> str:
    frente = str(getattr(beru, "frente_asignado", "") or "").upper()
    if frente and frente not in {"INDEFINIDO", ""}:
        return (
            frente.replace("USDT_SPOT", "")
            .replace("_SPOT", "")
            .replace("USDT", "")
            .strip("_")
        )
    uid = str(getattr(beru, "uid", "") or "")
    parts = uid.split("_")
    if len(parts) >= 3:
        return str(parts[2] or "").upper()
    return ""


def carta_hoz_viva(beru: Any) -> bool:
    """Hay Stop de Hoz en casa (Untriggered). Enlace muerto no cuenta."""
    link = str(getattr(beru, "altar_link_id", "") or "")
    if not link:
        return False
    st = str(getattr(beru, "altar_order_status", "") or "")
    if st in {"Cancelled", "Rejected", "Deactivated", "Filled"}:
        return False
    if st in {"Untriggered", "Created", "New", "Pending", "Live"}:
        return True
    return False


def lado_fill_a_direccion(side: str) -> str:
    """Sell cobrado = Oz SHORT. Buy cobrado = Oz LONG."""
    s = str(side or "").strip().upper()
    if s in {"SELL", "SHORT"}:
        return "SHORT"
    return "LONG"


def _apagar_carta_casa(beru: Any) -> None:
    """La Hoz de foto no se replanta. Carta muerta, masa del tramo a cero."""
    beru.estado = "ACECHANDO"
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.oz_pct = 0.0
    beru.red_pct = 0.0
    beru.oz_adan = 0.0
    beru.red_adan = 0.0
    beru.llamado_tramo_pct = 0.0
    beru.arma_cazador = ""
    beru.hoz_modo = ""
    beru.masa_carta_usd = 0.0
    beru.masa_rafaga_usd = 0.0
    beru.rafaga_en_curso = False
    beru.altar_order_id = ""
    beru.altar_link_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    beru.altar_cancel_confirmado = False
    beru.altar_rependiente = False
    beru.altar_lote_bloqueado = False


def alinear_acecho_con_oz_fill(
    beru: Any,
    *,
    precio: float,
    side: str,
    grado: str = "",
) -> bool:
    """Mano de la casa (fill spot cobrado) = última Oz. No es botín ni dual Vacío.

    Misma geometría que el funeral: sangre 1,1 al otro lado y Red de relevo.
    El barco sigue vivo (no COSECHADO, no hijo nuevo) para no duplicar la flota.
    No suma cosechas: no es botín del General.
    """
    fill = float(precio or 0)
    if fill <= 0:
        return False
    direccion = lado_fill_a_direccion(side)
    escala = escala_manto(beru)
    ancla_prev = float(getattr(beru, "ancla_tramo", 0) or 0)
    if escala > 0 and ancla_prev > 0:
        hoz_pct = (fill - ancla_prev) / escala
    elif escala > 0:
        manto = float(getattr(beru, "centro_manto", 0) or 0)
        hoz_pct = (fill - manto) / escala if manto > 0 else 0.0
    else:
        hoz_pct = 0.0

    # Vida nueva: la Red del saco muerto no manda. Relevo desde esta Oz.
    red_px = fill
    red_pct = hoz_pct

    g = str(grado or "").upper()
    if not g:
        from core.beru_altar_cazador import grado_de_barco

        g = str(grado_de_barco(beru) or "").upper()

    _apagar_carta_casa(beru)
    beru.direccion = direccion
    beru.ancla_tramo = fill
    beru.centro_local = fill
    beru.ultima_hoz_tocada_precio = fill
    beru.ultima_hoz_tocada_pct = hoz_pct
    beru.ultima_red_tocada_precio = red_px
    beru.ultima_red_tocada_pct = red_pct
    beru.modo_combate = "CAZA"
    beru.sangre_vista_dentro = True
    red_off = float(beru_cazador.relevo_llamado_pct(g))
    beru.es_relevo_cazador = True
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = red_px > 0
    beru.llamado_red_pct = red_off
    if not str(getattr(beru, "padre_cazador_uid", "") or ""):
        beru.padre_cazador_uid = str(getattr(beru, "uid", "") or "")
    return True


def desarmar_caza_huerfana(beru: Any) -> None:
    """Caza en foto, Hoz de casa ya no está: acecha; no replanta el saco viejo."""
    hoz = float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0)
    relevo = bool(getattr(beru, "es_relevo_cazador", False))
    _apagar_carta_casa(beru)
    if hoz > 0 or relevo:
        beru.es_relevo_cazador = True if hoz > 0 or relevo else False
        restaurar_acecho_tras_fallo_armado(beru)
        return
    beru.sangre_vista_dentro = False
    beru.oreja_sangre_activa = False
    beru.oreja_red_activa = False


def preparar_legion_tras_manos_casa(
    legion: list[Any],
    fills: dict[str, dict] | None = None,
) -> dict[str, str]:
    """Al recargar: fill de casa en acecho dual; caza con carta viva se conserva.

    Caza en memoria sin Stop: no se pisa con Oz vieja; el pulso planta esa Hoz.
    """
    fills = fills or {}
    informe: dict[str, str] = {}
    for beru in legion or []:
        act = activo_de_barco(beru)
        raw = fills.get(act) or fills.get(str(act).upper()) or {}
        px = float(raw.get("precio") or 0)
        ts = float(raw.get("ts") or 0)
        piso = float(raw.get("piso_ts") or 0)
        cazando = str(getattr(beru, "estado", "") or "").upper() == "CAZANDO"
        oz_mem = float(getattr(beru, "oz_adan", 0) or 0)
        if cazando and carta_hoz_viva(beru):
            informe[act or str(getattr(beru, "uid", ""))] = "caza_viva"
            continue
        if cazando and oz_mem > 0:
            informe[act or str(getattr(beru, "uid", ""))] = "caza_sin_carta"
            continue
        if px > 0 and (piso <= 0 or ts > piso) and not cazando:
            ok = alinear_acecho_con_oz_fill(
                beru,
                precio=px,
                side=str(raw.get("side") or ""),
                grado=str(raw.get("grado") or ""),
            )
            informe[act or str(getattr(beru, "uid", ""))] = (
                "oz_casa" if ok else "fill_invalido"
            )
            continue
        if cazando:
            desarmar_caza_huerfana(beru)
            informe[act or str(getattr(beru, "uid", ""))] = "caza_huerfana"
        else:
            informe[act or str(getattr(beru, "uid", ""))] = "intacta"
    for hijo in adoptar_cosechados_sin_hijo(legion):
        legion.append(hijo)
        act = activo_de_barco(hijo)
        informe[act or str(getattr(hijo, "uid", ""))] = "hijo_cosecha"
    return informe


def adoptar_cosechados_sin_hijo(legion: list[Any]) -> list[Any]:
    """Cosecha sin hijo (Mariscal viejo u orejas muertas): nace el relevo desde esa Oz."""
    vivos = {str(getattr(b, "uid", "") or "") for b in (legion or [])}
    padres = {
        str(getattr(b, "padre_cazador_uid", "") or "")
        for b in (legion or [])
        if str(getattr(b, "padre_cazador_uid", "") or "")
    }
    from core.beru_altar_cazador import grado_de_barco

    nuevos: list[Any] = []
    for beru in list(legion or []):
        if str(getattr(beru, "estado", "") or "").upper() != "COSECHADO":
            continue
        rid = str(getattr(beru, "relevo_cazador_uid", "") or "")
        if rid and rid in vivos:
            continue
        uid = str(getattr(beru, "uid", "") or "")
        if uid and uid in padres:
            continue
        fill = float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0)
        if fill <= 0:
            continue
        act = activo_de_barco(beru)
        grado = str(grado_de_barco(beru) or "")
        hijo = plantar_orejas_post_hoz(beru, fill, activo=act, grado=grado)
        if hijo is None:
            continue
        beru.relevo_creado = True
        nuevos.append(hijo)
        vivos.add(str(getattr(hijo, "uid", "") or ""))
        if uid:
            padres.add(uid)
    return nuevos


def resucitar_santos_cosechados_sin_barco(
    legion: list[Any],
    activos: list[str],
    *,
    tusk: Any = None,
) -> list[Any]:
    """Santo que cobró y ya no tiene Beru: hijo desde esa Oz, no dual Vacío."""
    from core import beru_asset_detail as bad
    from core import beru_cazador
    from core import beru_wake
    from core.beru_altar_cazador import grado_de_barco
    from core.models import BeruShip
    from generales.capitanes import CapitanNormal

    ya: set[str] = set()
    for b in legion or []:
        a = str(activo_de_barco(b) or "").upper()
        if a:
            ya.add(a)
    corte = beru_wake.leer_wake_ritual()
    nuevos: list[Any] = []
    for raw in activos or []:
        act = str(raw or "").upper()
        if not act or act in ya:
            continue
        if tusk is not None and not beru_wake.manto_bellion_usable(tusk, act):
            continue
        row = bad.ultima_cosecha_esta_vida(act, corte)
        if not row:
            continue
        fill = float(row.get("precio") or 0)
        if fill <= 0:
            continue
        manto = float(row.get("precio_manto") or 0)
        if tusk is not None:
            vivo = float(
                beru_cazador.centro_manto_desde_tusk(
                    tusk, act, fallback_global=False,
                ) or 0
            )
            if vivo > 0:
                manto = vivo
        if manto <= 0:
            continue
        direccion = str(row.get("direccion") or "SHORT").upper()
        if direccion not in ("LONG", "SHORT"):
            direccion = "SHORT"
        uid_p = str(row.get("uid") or f"BERU_SEM_{act}_COSECHA")
        tier = str(beru_wake.tier_siembra_activo(act, tusk=tusk) or "PLENO")
        padre = BeruShip(
            uid=uid_p,
            centro_local=fill,
            centro_manto=manto,
            ancla_tramo=fill,
            masa=0.0,
            direccion=direccion,
            estado="COSECHADO",
            adn_capitan=CapitanNormal,
            tier_id=tier,
            modo_combate="CAZA",
            ultima_hoz_tocada_precio=fill,
            ultima_red_tocada_precio=fill,
            frente_asignado=f"{act}USDT_SPOT",
        )
        grado = str(grado_de_barco(padre) or "MARISCAL")
        hijo = plantar_orejas_post_hoz(padre, fill, activo=act, grado=grado)
        if hijo is None:
            continue
        nuevos.append(hijo)
        ya.add(act)
    return nuevos


def restaurar_acecho_tras_fallo_armado(beru: Any) -> None:
    """Si reserva/plan falló: vuelve a acechar. Semilla conserva el 0 de wake."""
    if not bool(getattr(beru, "es_relevo_cazador", False)):
        beru.estado = "ACECHANDO"
        beru.masa = 0.0
        beru.masa_tramo_usd = 0.0
        beru.oz_pct = 0.0
        beru.red_pct = 0.0
        beru.oz_adan = 0.0
        beru.red_adan = 0.0
        beru.llamado_tramo_pct = 0.0
        beru.arma_cazador = ""
        beru.sangre_vista_dentro = True
        return
    hoz = float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0)
    red = float(getattr(beru, "ultima_red_tocada_precio", 0) or 0)
    if hoz > 0:
        beru.ancla_tramo = hoz
        beru.centro_local = hoz
    beru.oreja_sangre_activa = hoz > 0
    beru.oreja_red_activa = red > 0
    beru.sangre_vista_dentro = True
    beru.estado = "ACECHANDO"
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.oz_pct = 0.0
    beru.red_pct = 0.0
    beru.oz_adan = 0.0
    beru.red_adan = 0.0
    beru.llamado_tramo_pct = 0.0
    beru.arma_cazador = ""


def reiniciar_tras_cosecha(beru: Any, precio_fill: float) -> None:
    """FÓSIL bloqueado: no reiniciar al mismo Beru desde el fill/Vacío."""
    _ = beru, precio_fill
    raise RuntimeError(
        "FOSIL_BLOQUEADO: tras Hoz debe nacer relevo desde última Red tocada"
    )


def aplicar_cero_manto(beru: Any, nuevo_cero: float) -> bool:
    """Actualiza el metro Igris. Nunca mueve el 0 local de wake ni un tramo armado."""
    nuevo = float(nuevo_cero or 0)
    if nuevo <= 0:
        return False
    viejo = float(getattr(beru, "centro_manto", 0) or 0)
    if viejo > 0 and abs(nuevo - viejo) / viejo < 1e-6:
        return False
    beru.centro_manto = nuevo
    return True
