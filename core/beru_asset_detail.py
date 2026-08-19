"""Beru — Sub-Santuario por activo (flota + ficha + red engorde).

Espejo doctrinal de `igris_asset_detail`: lista por moneda → detalle de legión.
Solo lectura. PnL estimado vs centro 0 (doctrina provisional).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import core.config as config
from core import beru_altar_cazador
from core import beru_capital as bc
from core import beru_cazador
from core import beru_continuo
from core import beru_ley
from core import beru_rail
from core import beru_wake
from core import g_min as gm
from core import lote_bybit

ROOT = Path(__file__).resolve().parents[1]
CRONICA_DIR = ROOT / "data" / "beru" / "cronicas"


def _modo_caza(b: Any) -> str:
    est = str(getattr(b, "estado", "") or "")
    if est == "FOSIL_BLOQUEADO":
        return est
    if est in ("ACECHANDO",):
        return "ACECHANDO"
    if est in ("CAZANDO", "ESPERANDO_MATERIALIZACION", "ESPERANDO_SUELTA"):
        return "CAZA"
    if est == "FUSIONADO":
        return "FUSIONADO"
    return est or "OTRO"


def _activo_de_uid(uid: str, fallback: str = "") -> str:
    u = str(uid or "")
    # BERU_SEM_ETH_… · BERU_CAPA2_SOL_…
    parts = u.split("_")
    for i, p in enumerate(parts):
        if p in ("SEM", "CAPA1", "CAPA2", "CAPA3", "CAPA4", "CAPA5") and i + 1 < len(parts):
            cand = parts[i + 1]
            if cand.isalpha() and len(cand) <= 12:
                return cand.upper()
        if p.startswith("CAPA") and i + 1 < len(parts):
            cand = parts[i + 1]
            if cand.isalpha() and len(cand) <= 12:
                return cand.upper()
    # frente_asignado ETHUSDT_SPOT
    return (fallback or "").upper()


def activo_de_legionario(b: Any, semilla: str = "") -> str:
    """Activo (ETH, BTC…) de un barco Beru — público para crónica / panel."""
    return _activo_barco(b, semilla)


def _activo_barco(b: Any, semilla: str = "") -> str:
    frente = str(getattr(b, "frente_asignado", "") or "")
    if frente and frente != "INDEFINIDO":
        for q in ("USDT", "USDC", "USDE", "USD1"):
            if frente.upper().endswith(f"{q}_SPOT"):
                return frente.upper().replace(f"{q}_SPOT", "")
            if f"{q}_SPOT" in frente.upper():
                base = frente.upper().split(f"{q}_SPOT")[0]
                if base:
                    return base
    uid_act = _activo_de_uid(getattr(b, "uid", ""), semilla)
    if uid_act:
        return uid_act
    return (semilla or beru_rail.activo_semilla()).upper()


def _quote_de_frente(frente: str) -> str | None:
    f = (frente or "").upper()
    for q in ("USDT", "USDC", "USDE", "USD1"):
        if f.endswith(f"{q}_SPOT") or f"{q}_SPOT" in f:
            return q
    return None


def _pct_desde_centro(centro: float, precio: float) -> float | None:
    if centro <= 0 or precio <= 0:
        return None
    return round((precio - centro) / centro * 100.0, 4)


def _campanas_vacio(b: Any) -> tuple[float, float, float]:
    """Vacío de sangre. Semilla: ±1,1 del wake. Luego: 1,1 del otro lado de la Hoz.

    Nunca 1,1 % del propio wake como metro. Devuelve (arriba, abajo, umbral_pct).
    """
    off = float(beru_continuo.vacio_adan_pct(b) or 0)
    ancla = beru_continuo.ancla_tramo(b)
    if off <= 0 or ancla <= 0:
        return 0.0, 0.0, 0.0
    umbral = off * 100.0
    if beru_continuo.sangre_dual(b):
        up = float(beru_continuo.precio_desde_ancla(b, off) or 0)
        dn = float(beru_continuo.precio_desde_ancla(b, -off) or 0)
        return up, dn, umbral
    px = float(beru_continuo.precio_sangre_contraria(b) or 0)
    if px <= 0:
        return 0.0, 0.0, umbral
    if beru_continuo.signo_sangre_contraria(b) > 0:
        return px, 0.0, umbral
    return 0.0, px, umbral


def _pct_metro(b: Any, precio: float) -> float | None:
    """% en puntos del manto desde el 0 local — misma regla que el cazador."""
    px = float(precio or 0)
    if px <= 0 or beru_continuo.ancla_tramo(b) <= 0:
        return None
    return round(float(beru_continuo.pct_desde_ancla(b, px) or 0) * 100.0, 4)


def _es_caza_activa(b: Any) -> bool:
    return _modo_caza(b) == "CAZA"


def _frente_spot(b: Any, activo: str) -> str:
    frente = str(getattr(b, "frente_asignado", "") or "")
    if frente and frente != "INDEFINIDO":
        return frente
    act = str(activo or "").upper()
    return f"{act}USDT_SPOT" if act else ""


def _masa_lote_carta(
    b: Any,
    activo: str,
    masa_usd: float,
    trigger_px: float,
    direccion: str,
) -> float:
    """USD que Bybit aceptaría en la Hoz, tras qtyStep y mínimo de la casa."""
    usd = float(masa_usd or 0)
    px = float(trigger_px or 0)
    if usd <= 0 or px <= 0:
        return 0.0
    frente = _frente_spot(b, activo)
    if not frente:
        return round(usd, 6)
    modo: lote_bybit.ModoRedondeo = (
        "ceil" if str(direccion or "").upper() == "LONG" else "floor"
    )
    try:
        px_q = lote_bybit.cuantizar_precio(px, frente, mode=modo)
        conv = lote_bybit.cuantizar_presupuesto_usd(
            usd, float(px_q or px), frente, mode=modo,
        )
    except (TypeError, ValueError, KeyError):
        return round(usd, 6)
    if conv.get("ok") and float(conv.get("usd") or 0) > 0:
        return round(float(conv["usd"]), 6)
    return round(usd, 6)


def _masas_prometidas_barco(b: Any, activo: str, grado: str) -> dict[str, float]:
    """Masa a la izquierda de Vacío / Red: lo que despertaría si esa raya toca."""
    out = {
        "masa_vacio_arriba_usd": 0.0,
        "masa_vacio_abajo_usd": 0.0,
        "masa_red_usd": 0.0,
        "red_relevo_precio": 0.0,
    }
    modo = _modo_caza(b)
    act = str(activo or "").upper()
    g = str(grado or "")
    if modo == "ACECHANDO":
        relevo = _es_relevo_barco(b)
        if relevo:
            teo = float(bc.g_min_usd(act) or gm.g_min_usd(act) or 0)
        else:
            teo = beru_continuo.masa_prometida_silbato_usd(b, act, g, oreja="SANGRE")
        hoz_off = float(beru_continuo.distancia_hoz_pct(b) or 0)
        hoz_up = float(beru_continuo.precio_desde_ancla(b, hoz_off) or 0)
        hoz_dn = float(beru_continuo.precio_desde_ancla(b, -hoz_off) or 0)
        out["masa_vacio_arriba_usd"] = _masa_lote_carta(b, act, teo, hoz_up, "SHORT")
        out["masa_vacio_abajo_usd"] = _masa_lote_carta(b, act, teo, hoz_dn, "LONG")
        if not beru_continuo.sangre_dual(b):
            if beru_continuo.signo_sangre_contraria(b) > 0:
                out["masa_vacio_abajo_usd"] = 0.0
            elif beru_continuo.signo_sangre_contraria(b) < 0:
                out["masa_vacio_arriba_usd"] = 0.0
        red_px = float(beru_continuo.precio_oreja_red(b, g) or 0)
        out["red_relevo_precio"] = round(red_px, 8) if red_px > 0 else 0.0
        if red_px > 0:
            teo_red = teo if relevo else beru_continuo.masa_prometida_silbato_usd(
                b, act, g, oreja="RED",
            )
            hoz_red = float(beru_continuo.precio_hoz_si_oreja_red(b, g) or 0)
            direccion = str(getattr(b, "direccion", "LONG") or "LONG")
            out["masa_red_usd"] = _masa_lote_carta(
                b, act, teo_red, hoz_red, direccion,
            )
        return out

    if modo != "CAZA":
        return out
    direccion = str(getattr(b, "direccion", "LONG") or "LONG")
    oz_px = float(getattr(b, "oz_adan", 0) or 0)
    teo = beru_continuo.masa_prometida_silbato_usd(b, act, g, oreja="SANGRE")
    masa_now = float(getattr(b, "masa", 0) or 0)
    hoz_off = float(beru_continuo.distancia_hoz_pct(b) or 0)
    hoz_up = float(beru_continuo.precio_desde_ancla(b, hoz_off) or 0)
    hoz_dn = float(beru_continuo.precio_desde_ancla(b, -hoz_off) or 0)
    sangre_px = float(beru_continuo.precio_sangre_contraria(b) or 0)
    if str(direccion).upper() == "SHORT":
        out["masa_vacio_arriba_usd"] = 0.0
        out["masa_vacio_abajo_usd"] = _masa_lote_carta(
            b, act, teo, sangre_px or hoz_dn, "LONG",
        )
    else:
        out["masa_vacio_abajo_usd"] = 0.0
        out["masa_vacio_arriba_usd"] = _masa_lote_carta(
            b, act, teo, sangre_px or hoz_up, "SHORT",
        )
    red_px = float(getattr(b, "red_adan", 0) or 0)
    if red_px <= 0:
        return out
    extra = 0.0
    if beru_ley.engorde_permitido() and float(getattr(b, "centro_manto", 0) or 0) > 0:
        extra = float(beru_cazador.engorde_paso_usd(act, g) or 0)
    masa_next = masa_now + extra
    oz_pct = float(getattr(b, "oz_pct", 0) or 0)
    red_pct = float(getattr(b, "red_pct", 0) or 0)
    if abs(oz_pct) < 1e-12 and oz_px > 0:
        oz_pct = float(beru_continuo.pct_desde_ancla(b, oz_px) or 0)
    if abs(red_pct) < 1e-12 and red_px > 0:
        red_pct = float(beru_continuo.pct_desde_ancla(b, red_px) or 0)
    new_oz_pct, _ = beru_cazador.mover_niveles_cazador(direccion, oz_pct, red_pct)
    new_oz = float(beru_continuo.precio_desde_ancla(b, new_oz_pct) or 0)
    if new_oz <= 0:
        new_oz = red_px
    out["masa_red_usd"] = _masa_lote_carta(b, act, masa_next, new_oz, direccion)
    return out


def _es_negociando(b: Any) -> bool:
    _ = b
    return False


def red_engorde_de_legion(legion: list[Any], activo: str) -> dict[str, Any] | None:
    """Red que permite engordar (frontera) para el activo."""
    ships = [b for b in legion if _activo_barco(b) == activo.upper()]
    if not ships:
        return None

    candidatos = [
        b for b in ships
        if str(getattr(b, "estado", "")) == "CAZANDO"
        and _es_caza_activa(b)
        and float(getattr(b, "red_adan", 0) or 0) > 0
    ]
    if not candidatos:
        # Fallback: cualquier caza con red
        candidatos = [
            b for b in ships
            if _es_caza_activa(b) and float(getattr(b, "red_adan", 0) or 0) > 0
        ]
    frontera = candidatos[0] if candidatos else None
    if frontera is None and candidatos:
        # LONG: red más baja; SHORT: más alta
        longs = [b for b in candidatos if getattr(b, "direccion", "LONG") == "LONG"]
        shorts = [b for b in candidatos if getattr(b, "direccion", "") == "SHORT"]
        if longs:
            frontera = min(longs, key=lambda x: float(x.red_adan))
        elif shorts:
            frontera = max(shorts, key=lambda x: float(x.red_adan))

    if frontera is None:
        return None
    centro = float(getattr(frontera, "centro_manto", 0) or getattr(frontera, "centro_local", 0) or 0)
    red_p = float(getattr(frontera, "red_adan", 0) or 0)
    red_pct = float(getattr(frontera, "red_pct", 0) or 0)
    return {
        "uid": getattr(frontera, "uid", ""),
        "precio": red_p,
        "pct_vs_centro": _pct_desde_centro(centro, red_p) if red_p > 0 else (
            round(red_pct * 100.0, 4) if red_pct else None
        ),
        "direccion": getattr(frontera, "direccion", "LONG"),
        "centro_0": centro,
        "nota": "Red del mismo cazador: cada 0.1% añade un peldaño al tramo.",
    }


def _barco_fila(b: Any, activo: str, precio_mark: float = 0.0) -> dict[str, Any]:
    manto = float(getattr(b, "centro_manto", 0) or 0)
    wake = float(getattr(b, "centro_wake", 0) or getattr(b, "centro_local", 0) or 0)
    ancla = float(getattr(b, "ancla_tramo", 0) or 0)
    # 0 local = wake de la semilla o ancla de esta vida. El manto no se mezcla.
    cero_local = ancla or wake
    oz = float(getattr(b, "oz_adan", 0) or 0)
    red = float(getattr(b, "red_adan", 0) or 0)
    masa = float(getattr(b, "masa", 0) or getattr(b, "masa_congelada", 0) or 0)
    entrada = float(getattr(b, "precio_entrada_real", 0) or 0)
    mark = precio_mark or entrada or cero_local
    pnl = None
    if entrada > 0 and mark > 0 and masa > 0:
        dir_ = str(getattr(b, "direccion", "LONG") or "LONG").upper()
        ret = (mark - entrada) / entrada
        if dir_ == "SHORT":
            ret = -ret
        pnl = round(ret * masa, 4)

    frente = str(getattr(b, "frente_asignado", "") or "")
    link = str(getattr(b, "altar_link_id", "") or "")
    vacio_up, vacio_dn, vacio_pct = _campanas_vacio(b)
    grado = ""
    try:
        grado = beru_altar_cazador.grado_de_barco(b)
    except Exception:
        grado = str(getattr(b, "tier_id", "") or "")
    masas = _masas_prometidas_barco(b, activo, grado)
    return {
        "uid": getattr(b, "uid", ""),
        "estado": getattr(b, "estado", ""),
        "modo": _modo_caza(b),
        "direccion": getattr(b, "direccion", "LONG"),
        "grado": grado,
        "masa": round(masa, 6),
        "centro_0": cero_local,
        "centro_manto": manto,
        "centro_wake": cero_local,
        "centro_local": cero_local,
        "ancla_tramo": ancla,
        "vacio_pct": round(vacio_pct, 4) if vacio_pct else 1.1,
        "vacio_arriba": round(vacio_up, 8) if vacio_up else None,
        "vacio_abajo": round(vacio_dn, 8) if vacio_dn else None,
        "spot_last": mark or None,
        "cosechas_continuas": int(getattr(b, "cosechas_continuas", 0) or 0),
        "masa_tramo_usd": round(float(getattr(b, "masa_tramo_usd", masa) or 0), 6),
        "llamado_tramo_pct": round(float(getattr(b, "llamado_tramo_pct", 0) or 0) * 100.0, 4),
        "llamado_red_pct": float(getattr(b, "llamado_red_pct", 0) or 0),
        "oz_precio": oz,
        "oz_pct": round(float(getattr(b, "oz_pct", 0) or 0) * 100.0, 4),
        "red_precio": red,
        "red_pct": round(float(getattr(b, "red_pct", 0) or 0) * 100.0, 4),
        "oz_vs_centro_pct": _pct_metro(b, oz),
        "red_vs_centro_pct": _pct_metro(b, red),
        "ultima_hoz_precio": float(getattr(b, "ultima_hoz_tocada_precio", 0) or 0) or None,
        "ultima_hoz_pct": round(float(getattr(b, "ultima_hoz_tocada_pct", 0) or 0) * 100.0, 4),
        "ultima_red_precio": float(getattr(b, "ultima_red_tocada_precio", 0) or 0) or None,
        "ultima_red_pct": round(float(getattr(b, "ultima_red_tocada_pct", 0) or 0) * 100.0, 4),
        "oreja_vacio": bool(getattr(b, "oreja_sangre_activa", False)),
        "oreja_red": bool(getattr(b, "oreja_red_activa", False)),
        "es_relevo": _es_relevo_barco(b),
        "ts_wake": float(getattr(b, "ts_wake", 0) or 0) or beru_wake.ts_wake_de_uid(
            str(getattr(b, "uid", "") or "")
        ),
        "masa_vacio_arriba_usd": masas["masa_vacio_arriba_usd"],
        "masa_vacio_abajo_usd": masas["masa_vacio_abajo_usd"],
        "masa_red_usd": masas["masa_red_usd"],
        "red_relevo_precio": masas["red_relevo_precio"] or None,
        "carta_colgada": bool(link),
        "altar_link_id": link or None,
        "altar_status": str(getattr(b, "altar_order_status", "") or "") or None,
        "hoz_modo": str(getattr(b, "hoz_modo", "") or "") or "GORDA",
        "masa_carta_usd": round(float(getattr(b, "masa_carta_usd", 0) or 0), 6),
        "masa_rafaga_usd": round(float(getattr(b, "masa_rafaga_usd", 0) or 0), 6),
        "tier_id": getattr(b, "tier_id", "") or "",
        "modo_combate": getattr(b, "modo_combate", "") or "",
        "capa": int(getattr(b, "capa", 1) or 1),
        "generacion": int(getattr(b, "generacion", 1) or 1),
        "es_super": bool(getattr(b, "es_super_beru", False)),
        "ciclo_infinito": bool(getattr(b, "ciclo_infinito", False)),
        "neg_toques_ciclo": int(getattr(b, "neg_toques_ciclo", 0) or 0),
        "ancla_cosecha_pct": round(float(getattr(b, "ancla_cosecha_pct", 0) or 0) * 100.0, 4),
        "frente": frente if frente != "INDEFINIDO" else None,
        "rail_quote": _quote_de_frente(frente),
        "precio_entrada": entrada or None,
        "precio_salida": float(getattr(b, "precio_salida_real", 0) or 0) or None,
        "max_favor_pct": round(float(getattr(b, "max_favor", 0) or 0) * 100.0, 4),
        "pnl_est_usd": pnl,
        "fees_paid_usd": None,
    }


def _barco_vivo(barcos: list[dict]) -> dict:
    """El cazador que todavía oye: acecho o caza. El padre cosechado no pinta."""
    for b in barcos:
        modo = str(b.get("modo") or "")
        est = str(b.get("estado") or "")
        if modo in ("ACECHANDO", "CAZA") or est in ("ACECHANDO", "CAZANDO"):
            return b
    return barcos[0] if barcos else {}


def _barco_semilla_fila(barcos: list[dict]) -> dict:
    for b in barcos:
        if not b.get("es_relevo"):
            return b
    return barcos[0] if barcos else {}


_RELEVO_OFF = {
    "SOLDADO": 0.009,
    "CAPITAN": 0.005,
    "GENERAL": 0.003,
    "MARISCAL": 0.0,
}
_UID_HIJO = re.compile(r"_R\d+(_|$)")


def _uid_es_hijo(uid: str) -> bool:
    """BERU_SEM_{SANTO}_R2_… — toda la flota, no un Santo suelto."""
    return bool(_UID_HIJO.search(str(uid or "")))


def _es_relevo_barco(b: Any) -> bool:
    if bool(getattr(b, "es_relevo_cazador", False) or (isinstance(b, dict) and b.get("es_relevo"))):
        return True
    gen = int(getattr(b, "generacion", None) or (b.get("generacion") if isinstance(b, dict) else 1) or 1)
    if gen > 1:
        return True
    uid = str(getattr(b, "uid", "") or (b.get("uid") if isinstance(b, dict) else "") or "")
    return _uid_es_hijo(uid)


def _es_relevo_fila(b: dict[str, Any]) -> bool:
    return _es_relevo_barco(b)


def _cazando_fila(b: dict[str, Any]) -> bool:
    return str(b.get("modo") or "") == "CAZA" or str(b.get("estado") or "") == "CAZANDO"


def _id_vacio_caza(vivo: dict[str, Any]) -> str:
    """Lado de la caza: SHORT sube (vacio_up) · LONG baja (vacio_dn)."""
    return "vacio_up" if str(vivo.get("direccion") or "").upper() == "SHORT" else "vacio_dn"


def _precio_red_grafica(vivo: dict[str, Any]) -> float:
    """Red de caza (carta) o Red de relevo (oído). Sirve a toda la flota."""
    for k in ("red_precio", "red_relevo_precio"):
        p = float(vivo.get(k) or 0)
        if p > 0:
            return p
    grado = str(vivo.get("grado") or "").upper()
    if grado == "MARISCAL":
        return 0.0
    if not (vivo.get("oreja_red") or _es_relevo_fila(vivo)):
        return 0.0
    ancla = float(vivo.get("ultima_red_precio") or 0)
    escala = float(vivo.get("centro_manto") or 0)
    off = float(vivo.get("llamado_red_pct") or 0)
    if off > 1:
        off = off / 100.0
    if off <= 0:
        off = float(_RELEVO_OFF.get(grado) or 0)
    if ancla <= 0 or escala <= 0 or off <= 0:
        return 0.0
    if str(vivo.get("direccion") or "").upper() == "LONG":
        return ancla - escala * off
    return ancla + escala * off


def _reparar_grafica(
    grafica: dict[str, Any],
    vivo: dict[str, Any],
    cronica: list[dict[str, Any]] | None = None,
    ts_corte: float = 0.0,
) -> dict[str, Any]:
    """No quita rayas: 0 local, dos sangres, manto, Red. Solo Hoz sin carta y × viejas."""
    g = dict(grafica or {})
    niveles = []
    for n in list(g.get("niveles") or []):
        if str(n.get("rol") or "") == "oz" and not vivo.get("carta_colgada"):
            continue
        niveles.append(n)
    cero = float(
        vivo.get("ancla_tramo")
        or vivo.get("centro_local")
        or vivo.get("centro_wake")
        or 0
    )
    if cero > 0:
        hay_wake = False
        for n in niveles:
            if str(n.get("rol") or "") == "wake":
                n["precio"] = cero
                n["id"] = n.get("id") or "wake"
                hay_wake = True
        if not hay_wake:
            niveles.append({
                "id": "wake", "precio": cero, "pct": 0.0, "rol": "wake",
            })
    vacio_pct = float(vivo.get("vacio_pct") or 1.1)
    if vivo.get("vacio_arriba"):
        hay_up = False
        for n in niveles:
            if str(n.get("id") or "") == "vacio_up":
                n["precio"] = vivo["vacio_arriba"]
                n["pct"] = vacio_pct
                hay_up = True
        if not hay_up:
            niveles.append({
                "id": "vacio_up", "precio": vivo["vacio_arriba"],
                "pct": vacio_pct, "rol": "vacio",
                "masa_usd": vivo.get("masa_vacio_arriba_usd") or None,
            })
    if vivo.get("vacio_abajo"):
        hay_dn = False
        for n in niveles:
            if str(n.get("id") or "") == "vacio_dn":
                n["precio"] = vivo["vacio_abajo"]
                n["pct"] = -vacio_pct
                hay_dn = True
        if not hay_dn:
            niveles.append({
                "id": "vacio_dn", "precio": vivo["vacio_abajo"],
                "pct": -vacio_pct, "rol": "vacio",
                "masa_usd": vivo.get("masa_vacio_abajo_usd") or None,
            })
    manto = float(vivo.get("centro_manto") or 0)
    if manto > 0:
        hay_manto = False
        for n in niveles:
            if str(n.get("rol") or "") == "manto":
                n["precio"] = manto
                hay_manto = True
        if not hay_manto:
            niveles.append({"id": "manto", "precio": manto, "pct": 0.0, "rol": "manto"})
    dual = not (
        bool(vivo.get("es_relevo") or vivo.get("es_relevo_cazador"))
        or str(vivo.get("estado") or "").upper() == "CAZANDO"
        or str(vivo.get("modo") or "").upper() == "CAZANDO"
        or float(vivo.get("oz_precio") or vivo.get("oz_adan") or 0) > 0
        or float(vivo.get("ultima_hoz_tocada_precio") or 0) > 0
    )
    if not vivo.get("vacio_arriba") or (not dual and str(vivo.get("direccion") or "").upper() == "SHORT"):
        niveles = [n for n in niveles if str(n.get("id") or "") != "vacio_up"]
    if not vivo.get("vacio_abajo") or (not dual and str(vivo.get("direccion") or "").upper() == "LONG"):
        niveles = [n for n in niveles if str(n.get("id") or "") != "vacio_dn"]
    red_oido = _precio_red_grafica(vivo)
    if red_oido > 0 and not any(n.get("rol") in ("red", "red_engorde") for n in niveles):
        niveles.append({
            "id": "red_relevo",
            "precio": round(red_oido, 8),
            "pct": None,
            "rol": "red",
            "uid": vivo.get("uid"),
            "masa_usd": vivo.get("masa_red_usd") or None,
        })
    cazas = _cazas_de_cronica(cronica or g.get("cazas") or [], ts_corte=ts_corte)
    if not cazas:
        cazas = _cazas_de_cronica(g.get("cazas") or [], ts_corte=ts_corte)
    g["niveles"] = niveles
    g["cazas"] = cazas
    if cero > 0:
        g["centro_0"] = cero
        g["centro_wake"] = cero
    if manto > 0:
        g["centro_manto"] = manto
    return g


def _niveles_grafica(barcos: list[dict], red_engorde: dict | None, centro: float) -> dict[str, Any]:
    """Semilla: 0 local + dos Vacío. Tras la primera Hoz: una sangre contraria. Caza: Hoz+Red. Manto = metro."""
    niveles = []
    primer = barcos[0] if barcos else {}
    vivo = _barco_vivo(barcos)
    manto = float(vivo.get("centro_manto") or primer.get("centro_manto") or 0)
    cero_local = float(
        vivo.get("ancla_tramo")
        or vivo.get("centro_local")
        or vivo.get("centro_wake")
        or centro
        or 0
    )
    vacio_pct = float(vivo.get("vacio_pct") or 1.1)
    if manto > 0:
        niveles.append({"id": "manto", "precio": manto, "pct": 0.0, "rol": "manto"})
    if cero_local > 0:
        niveles.append({"id": "wake", "precio": cero_local, "pct": 0.0, "rol": "wake"})
    elif centro > 0 and not manto:
        niveles.append({"id": "centro_0", "precio": centro, "pct": 0.0, "rol": "centro"})
    if vivo.get("vacio_arriba"):
        niveles.append({
            "id": "vacio_up", "precio": vivo["vacio_arriba"],
            "pct": vacio_pct, "rol": "vacio",
            "masa_usd": vivo.get("masa_vacio_arriba_usd") or None,
        })
    if vivo.get("vacio_abajo"):
        niveles.append({
            "id": "vacio_dn", "precio": vivo["vacio_abajo"],
            "pct": -vacio_pct, "rol": "vacio",
            "masa_usd": vivo.get("masa_vacio_abajo_usd") or None,
        })
    spot = float(vivo.get("spot_last") or primer.get("spot_last") or 0)
    if spot > 0:
        niveles.append({"id": "spot", "precio": spot, "pct": None, "rol": "spot"})
    for b in barcos:
        if not (_cazando_fila(b) or b.get("carta_colgada")):
            continue
        if b.get("oz_precio") and b.get("carta_colgada"):
            niveles.append({
                "id": f"oz_{str(b.get('uid') or '')[:12]}",
                "precio": b["oz_precio"],
                "pct": b.get("oz_vs_centro_pct"),
                "rol": "oz",
                "uid": b["uid"],
                "carta_colgada": True,
                "masa_usd": float(b.get("masa") or 0) or None,
            })
        red_px = float(b.get("red_precio") or 0)
        if red_px > 0:
            niveles.append({
                "id": f"red_{str(b.get('uid') or '')[:12]}",
                "precio": red_px,
                "pct": b.get("red_vs_centro_pct"),
                "rol": "red",
                "uid": b["uid"],
                "masa_usd": b.get("masa_red_usd") or None,
            })
    red_oido = _precio_red_grafica(vivo)
    if red_oido > 0 and not any(n.get("rol") in ("red", "red_engorde") for n in niveles):
        niveles.append({
            "id": "red_relevo",
            "precio": round(red_oido, 8),
            "pct": None,
            "rol": "red",
            "uid": vivo.get("uid"),
            "masa_usd": vivo.get("masa_red_usd") or None,
        })
    if red_engorde and red_engorde.get("precio"):
        ya = any(
            abs(float(n.get("precio") or 0) - float(red_engorde["precio"])) < 1e-9
            for n in niveles if n.get("rol") in ("red", "red_engorde")
        )
        if not ya:
            masa_eng = None
            uid_e = red_engorde.get("uid")
            for b in barcos:
                if b.get("uid") == uid_e:
                    masa_eng = b.get("masa_red_usd") or None
                    break
            if masa_eng is None:
                masa_eng = vivo.get("masa_red_usd") or None
            niveles.append({
                "id": "red_engorde",
                "precio": red_engorde["precio"],
                "pct": red_engorde.get("pct_vs_centro"),
                "rol": "red_engorde",
                "uid": red_engorde.get("uid"),
                "masa_usd": masa_eng,
            })
    return {
        "centro_0": cero_local or centro,
        "centro_manto": manto,
        "centro_wake": cero_local,
        "spot_last": spot or None,
        "niveles": niveles,
        "cazas": [],
    }


def _cargar_cronica(activo: str, limit: int = 40) -> list[dict[str, Any]]:
    path = CRONICA_DIR / f"{activo.upper()}.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            rows.append(json.loads(ln))
    except (OSError, json.JSONDecodeError):
        return []
    return rows[-limit:]


def _es_fill_cosecha(row: dict[str, Any]) -> bool:
    tipo = str(row.get("tipo") or "").upper()
    if tipo == "COSECHA":
        return True
    return tipo.startswith("COSECHA") and "TRAMO" not in tipo


def _fmt_sello_pct(pct: float | None) -> str | None:
    if pct is None:
        return None
    x = float(pct)
    sello = "Botín" if x >= 0 else "Merma"
    return f"{sello} {x:.2f}%"


def _lecturas_evento(row: dict[str, Any]) -> dict[str, Any]:
    metro = row.get("beneficio_metro_pct")
    hoz = row.get("beneficio_hoz_pct")
    if metro is None and row.get("beneficio_pct") is not None:
        metro = row.get("beneficio_pct")
    out: dict[str, Any] = {
        "beneficio_metro_pct": float(metro) if metro is not None else None,
        "beneficio_hoz_pct": float(hoz) if hoz is not None else None,
        "precio_hoz": float(row.get("precio_hoz") or 0) or None,
    }
    mtxt = _fmt_sello_pct(out["beneficio_metro_pct"])
    htxt = _fmt_sello_pct(out["beneficio_hoz_pct"])
    if mtxt and htxt:
        out["detalle_lecturas"] = f"metro {mtxt} · Hoz {htxt}"
    elif mtxt:
        out["detalle_lecturas"] = f"metro {mtxt}"
    else:
        out["detalle_lecturas"] = None
    return out


def _ultima_cosecha_lecturas(cronica: list[dict[str, Any]]) -> dict[str, Any]:
    for r in reversed(cronica or []):
        if not _es_fill_cosecha(r):
            continue
        lec = _lecturas_evento(r)
        lec["ts"] = r.get("ts")
        return lec
    return {
        "beneficio_metro_pct": None,
        "beneficio_hoz_pct": None,
        "precio_hoz": None,
        "detalle_lecturas": None,
        "ts": None,
    }


def _cronica_desde(rows: list[dict[str, Any]], ts_corte: float) -> list[dict[str, Any]]:
    if ts_corte <= 0:
        return list(rows or [])
    out = []
    for r in rows or []:
        ts = float(r.get("ts") or 0)
        if ts + 1e-6 >= ts_corte:
            out.append(r)
    return out


def _lado_caza(row: dict[str, Any]) -> str:
    d = str(row.get("direccion") or "").upper()
    if d == "LONG":
        return "Buy"
    if d == "SHORT":
        return "Sell"
    lado = str(row.get("lado") or "")
    if lado in ("Buy", "Sell"):
        return lado
    return ""


def _cazas_de_cronica(
    rows: list[dict[str, Any]],
    ts_corte: float = 0.0,
) -> list[dict[str, Any]]:
    """Fills de Hoz de ESTA vida (desde el wake/arise)."""
    out: list[dict[str, Any]] = []
    for r in rows or []:
        if r.get("tipo") and not _es_fill_cosecha(r):
            continue
        px = float(r.get("precio") or 0)
        ts = float(r.get("ts") or 0)
        if px <= 0 or ts <= 0:
            continue
        if ts_corte > 0 and ts + 1e-6 < ts_corte:
            continue
        lado = _lado_caza(r)
        out.append({
            "ts": int(ts),
            "precio": round(px, 8),
            "lado": lado or None,
        })
    return out[-40:]


def _oficio_vivo(snap: dict[str, Any]) -> str:
    """cazando = Vacío o Red ya sonó y hay Hoz; acechando = espera o post-cosecha."""
    vivo = _barco_vivo(snap.get("barcos") or [])
    modo = str(vivo.get("modo") or "")
    est = str(vivo.get("estado") or "")
    if modo == "CAZA" or est == "CAZANDO":
        return "cazando"
    return "acechando"


def _n_cazas_cronica(cronica: list[dict[str, Any]]) -> int:
    n = 0
    for r in cronica or []:
        if _es_fill_cosecha(r):
            n += 1
    return n


def _saco_desde_vacio(snap: dict[str, Any]) -> float:
    """Masa prometida del Vacío vivo — un número, no la suma de campanas."""
    best = 0.0
    for n in (snap.get("grafica") or {}).get("niveles") or []:
        if str(n.get("rol") or "") != "vacio":
            continue
        best = max(best, float(n.get("masa_usd") or 0))
    if best > 0:
        return round(best, 6)
    vivo = _barco_vivo(snap.get("barcos") or [])
    for k in ("masa_vacio_arriba_usd", "masa_vacio_abajo_usd"):
        best = max(best, float(vivo.get(k) or 0))
    return round(best, 6)


def _saco_tarjeta(oficio: str, snap: dict[str, Any]) -> float:
    """Cazando: Hoz viva. Acechando: misma masa que el Vacío de ahora."""
    if oficio == "cazando":
        vivo = _barco_vivo(snap.get("barcos") or [])
        return round(float(vivo.get("masa") or 0), 6)
    return _saco_desde_vacio(snap)


def _dist_silbato(snap: dict[str, Any], oficio: str) -> float:
    """Puntos de manto al oído más cercano. Más chico = más caliente."""
    spot = float(snap.get("spot_last") or 0)
    escala = float(snap.get("centro_manto") or 0)
    if spot <= 0 or escala <= 0:
        return 1e9
    if oficio == "cazando":
        roles = ("oz", "red", "red_engorde", "vacio")
    else:
        roles = ("vacio", "red", "red_engorde")
    best: float | None = None
    for n in (snap.get("grafica") or {}).get("niveles") or []:
        if n.get("rol") not in roles:
            continue
        px = float(n.get("precio") or 0)
        if px <= 0:
            continue
        d = abs(spot - px) / escala
        if best is None or d < best:
            best = d
    return float(best) if best is not None else 1e9


def _calor_banda(oficio: str, snap: dict[str, Any], dist: float) -> int:
    """0 caza · 1 hijo acecha · 2 semilla cerca del silbato · 3 sordo · 4 cerrado."""
    if oficio == "cazando":
        return 0
    if oficio == "cerrado":
        return 4
    vivo = _barco_vivo(snap.get("barcos") or [])
    if _es_relevo_fila(vivo):
        return 1
    if dist < 1e8:
        return 2
    return 3


_ARMAS_GRADO = frozenset({"SOLDADO", "CAPITAN", "GENERAL", "MARISCAL"})


def _grado_tarjeta(snap: dict[str, Any], vivo: dict[str, Any]) -> str:
    """Rango del cazador vivo. Nunca 00: si el barco no trae grado, se busca en la ficha."""
    g = str(vivo.get("grado") or "").upper()
    if g in _ARMAS_GRADO:
        return g
    for b in snap.get("barcos") or []:
        g2 = str(b.get("grado") or "").upper()
        if g2 in _ARMAS_GRADO:
            return g2
    return ""


def _santo_con_beru_y_manto(row: dict[str, Any]) -> bool:
    if str(row.get("oficio") or "").lower() == "cerrado":
        return bool(str(row.get("activo") or "").strip())
    if int(row.get("n_barcos") or 0) <= 0:
        return False
    return float(row.get("centro_manto") or 0) > 0


def _tarjeta_flota(act: str, snap: dict[str, Any]) -> dict[str, Any]:
    oficio = _oficio_vivo(snap)
    vivo = _barco_vivo(snap.get("barcos") or [])
    grado = _grado_tarjeta(snap, vivo)
    dist = _dist_silbato(snap, oficio)
    try:
        paso = float(beru_cazador.engorde_paso_usd(act, grado or None))
    except Exception:
        paso = 0.0
    ultima = _ultima_cosecha_lecturas(snap.get("cronica") or [])
    return {
        "oficio": oficio,
        "grado": grado,
        "engorde_paso_usd": round(paso, 6),
        "n_cazas": _n_cazas_cronica(snap.get("cronica") or []),
        "saco_usd": _saco_tarjeta(oficio, snap),
        "dist_silbato": round(dist, 6) if dist < 1e8 else None,
        "calor_banda": _calor_banda(oficio, snap, dist),
        "ultima_metro_pct": ultima["beneficio_metro_pct"],
        "ultima_hoz_pct": ultima["beneficio_hoz_pct"],
        "ultima_lecturas": ultima["detalle_lecturas"],
    }


def _hay_cosecha_esta_vida(cronica: list[dict[str, Any]]) -> bool:
    return any(_es_fill_cosecha(r) for r in cronica or [])


def _activos_cerrados_mariscal(vivos: set[str], corte: float) -> list[str]:
    """Mariscal que cobró y no dejó hijo: hay crónica de esta vida, no hay Beru vivo."""
    out: list[str] = []
    if not CRONICA_DIR.is_dir():
        return out
    for path in sorted(CRONICA_DIR.glob("*.jsonl")):
        act = str(path.stem or "").upper()
        if not act or act in vivos:
            continue
        rows = _cronica_desde(_cargar_cronica(act), corte)
        if _hay_cosecha_esta_vida(rows):
            out.append(act)
    return out


def _fila_cerrado(act: str, snap: dict[str, Any]) -> dict[str, Any]:
    ultima = _ultima_cosecha_lecturas(snap.get("cronica") or [])
    return {
        "activo": act,
        "n_barcos": 0,
        "n_caza": 0,
        "n_negociando": 0,
        "n_acechando": 0,
        "n_mega": 0,
        "G_min": snap.get("G_min"),
        "G_min_fuente": snap.get("G_min_fuente"),
        "G_min_hay_dato": snap.get("G_min_hay_dato"),
        "mordida_usd": snap.get("mordida_usd"),
        "masa_total_usd": 0.0,
        "pnl_est_usd": snap.get("pnl_est_usd") or 0,
        "centro_0": snap.get("centro_0") or 0,
        "centro_manto": snap.get("centro_manto") or 0,
        "centro_wake": snap.get("centro_wake") or 0,
        "composicion": snap.get("composicion") or {},
        "red_engorde_pct": None,
        "red_engorde_precio": None,
        "rails_vivos": snap.get("rails_vivos") or [],
        "es_semilla": False,
        "oficio": "cerrado",
        "grado": "MARISCAL",
        "engorde_paso_usd": 0.0,
        "n_cazas": _n_cazas_cronica(snap.get("cronica") or []),
        "saco_usd": 0.0,
        "dist_silbato": None,
        "calor_banda": 4,
        "ultima_metro_pct": ultima["beneficio_metro_pct"],
        "ultima_hoz_pct": ultima["beneficio_hoz_pct"],
        "ultima_lecturas": ultima["detalle_lecturas"],
    }


def _clave_orden_flota(row: dict[str, Any]) -> tuple:
    of = str(row.get("oficio") or "").lower()
    dist = float(row.get("dist_silbato") if row.get("dist_silbato") is not None else 1e9)
    nombre = str(row.get("activo") or "")
    if of == "cazando":
        return (0, dist, nombre)
    if of == "cerrado":
        return (2, 0.0, nombre)
    return (1, dist, nombre)


def append_cronica(activo: str, evento: dict[str, Any]) -> None:
    """Append evento de ciclo (caza/cosecha/mega/reset). Llamar desde Beru/Bellion."""
    CRONICA_DIR.mkdir(parents=True, exist_ok=True)
    path = CRONICA_DIR / f"{(activo or 'UNK').upper()}.jsonl"
    row = {"ts": time.time(), "activo": (activo or "").upper(), **evento}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # trim
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 500:
            path.write_text("\n".join(lines[-400:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def snapshot_activo(
    activo: str,
    legion: list[Any],
    *,
    precio_mark: float = 0.0,
    semilla: str | None = None,
) -> dict[str, Any]:
    act = (activo or "").upper()
    ships_raw = [b for b in (legion or []) if _activo_barco(b, semilla or "") == act]
    # Si no hay match por activo, y es la semilla, tomar toda la legión sin tag
    if not ships_raw and act == (semilla or beru_rail.activo_semilla()).upper():
        ships_raw = [
            b for b in (legion or [])
            if _activo_barco(b, semilla or "") in (act, "", (semilla or "").upper())
        ]

    barcos = [_barco_fila(b, act, precio_mark) for b in ships_raw]
    n_caza = sum(1 for x in barcos if x["modo"] == "CAZA")
    n_neg = sum(1 for x in barcos if x["modo"] in ("NEGOCIADOR", "CICLO_INFINITO"))
    n_acech = sum(1 for x in barcos if x["modo"] == "ACECHANDO")
    n_mega = sum(1 for x in barcos if x.get("es_super"))
    masa_total = round(sum(float(x.get("masa") or 0) for x in barcos), 6)
    pnl_sum = sum(float(x["pnl_est_usd"]) for x in barcos if x.get("pnl_est_usd") is not None)

    centros = [float(x["centro_0"]) for x in barcos if x.get("centro_0")]
    centro_0 = centros[0] if centros else 0.0
    manto0 = next((float(x.get("centro_manto") or 0) for x in barcos if x.get("centro_manto")), 0.0)
    wake0 = next((float(x.get("centro_wake") or 0) for x in barcos if x.get("centro_wake")), 0.0)

    red_eng = red_engorde_de_legion(ships_raw, act)
    rails = sorted({x["rail_quote"] for x in barcos if x.get("rail_quote")})
    frentes_casa = beru_rail.frentes_casa_estables(act)

    total = max(len(barcos), 1)
    det_g = gm.detalle_g_min(act)
    g_mostrar = bc.g_min_usd(act)
    cronica_all = _cargar_cronica(act)
    ts_corte = beru_wake.ts_corte_memoria(barcos, cronica_all)
    if ts_corte <= 0:
        ts_corte = beru_wake.ts_corte_memoria(ships_raw, cronica_all)
    cronica = _cronica_desde(cronica_all, ts_corte)
    for r in cronica:
        lec = _lecturas_evento(r)
        if lec.get("detalle_lecturas") and not str(r.get("detalle") or "").startswith("metro "):
            if str(r.get("tipo") or "").upper().startswith("COSECHA"):
                r["detalle_lecturas"] = lec["detalle_lecturas"]
                r["beneficio_metro_pct"] = lec["beneficio_metro_pct"]
                r["beneficio_hoz_pct"] = lec["beneficio_hoz_pct"]
    grafica = _niveles_grafica(barcos, red_eng, centro_0)
    grafica = _reparar_grafica(grafica, _barco_vivo(barcos), cronica, ts_corte=ts_corte)
    return {
        "symbol": act,
        "fuente": "legion" if barcos else "cero",
        "n_barcos": len(barcos),
        "n_caza": n_caza,
        "n_negociando": n_neg,
        "n_acechando": n_acech,
        "n_mega": n_mega,
        "G_min": round(float(g_mostrar), 4),
        "G_min_fuente": det_g.get("fuente_pierna") or det_g.get("archivo"),
        "G_min_hay_dato": bool(det_g.get("hay_dato_archivo")),
        "mordida_usd": round(float(beru_cazador.mordida_usd(act)), 4),
        "masa_total_usd": masa_total,
        "pnl_est_usd": round(pnl_sum, 4) if barcos else 0.0,
        "fees_paid_usd": None,
        "centro_0": centro_0,
        "centro_manto": manto0,
        "centro_wake": wake0,
        "spot_last": precio_mark or None,
        "composicion": {
            "caza": n_caza,
            "negociando": n_neg,
            "acechando": n_acech,
            "otros": max(0, len(barcos) - n_caza - n_neg - n_acech),
            "pct_caza": round(n_caza / total * 100.0, 1),
            "pct_negociando": round(n_neg / total * 100.0, 1),
        },
        "red_engorde": red_eng,
        "rails_vivos": rails,
        "rails_disponibles": [
            {"frente": f, "quote": _quote_de_frente(f)} for f in frentes_casa
        ],
        "barcos": barcos,
        "grafica": grafica,
        "cronica": cronica,
        "ts_wake": ts_corte or None,
        "nota_pnl": (
            "PnL estimado = retorno vs precio_entrada × masa. "
            "Fees ledger aún no cableado (hueco preparado)."
        ),
    }


def snapshot_cero(activo: str) -> dict[str, Any]:
    act = (activo or "ETH").upper()
    det_g = gm.detalle_g_min(act)
    return {
        "symbol": act,
        "fuente": "cero",
        "n_barcos": 0,
        "n_caza": 0,
        "n_negociando": 0,
        "n_acechando": 0,
        "n_mega": 0,
        "G_min": round(float(bc.g_min_usd(act)), 4),
        "G_min_fuente": det_g.get("fuente_pierna") or det_g.get("archivo"),
        "G_min_hay_dato": bool(det_g.get("hay_dato_archivo")),
        "mordida_usd": round(float(beru_cazador.mordida_usd(act)), 4),
        "masa_total_usd": 0.0,
        "pnl_est_usd": 0.0,
        "fees_paid_usd": None,
        "centro_0": 0.0,
        "centro_manto": 0.0,
        "centro_wake": 0.0,
        "spot_last": None,
        "composicion": {
            "caza": 0, "negociando": 0, "acechando": 0, "otros": 0,
            "pct_caza": 0.0, "pct_negociando": 0.0,
        },
        "red_engorde": None,
        "rails_vivos": [],
        "rails_disponibles": [
            {"frente": f, "quote": _quote_de_frente(f)}
            for f in beru_rail.frentes_casa_estables(act)
        ],
        "barcos": [],
        "grafica": {
            "centro_0": 0.0,
            "centro_manto": 0.0,
            "centro_wake": 0.0,
            "spot_last": None,
            "niveles": [],
            "cazas": [],
        },
        "cronica": [],
        "ts_wake": None,
        "nota_pnl": "Sin barcos — legión en reposo.",
    }


def flota_resumen(
    legion: list[Any],
    *,
    semilla: str | None = None,
    precios: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Lista por activo para panel / Pergamino. Orden: calor de combate, no A→Z."""
    sem = (semilla or beru_rail.activo_semilla()).upper()
    precios = precios or {}
    by_act: dict[str, list] = {}
    for b in legion or []:
        act = _activo_barco(b, sem) or sem
        by_act.setdefault(act, []).append(b)

    activos = []
    for act in by_act.keys():
        mark = float(precios.get(act) or precios.get(f"{act}USDT_SPOT") or 0)
        snap = snapshot_activo(act, by_act[act], precio_mark=mark, semilla=sem)
        tar = _tarjeta_flota(act, snap)
        activos.append({
            "activo": act,
            "n_barcos": snap["n_barcos"],
            "n_caza": snap["n_caza"],
            "n_negociando": snap["n_negociando"],
            "n_acechando": snap["n_acechando"],
            "n_mega": snap["n_mega"],
            "G_min": snap.get("G_min"),
            "G_min_fuente": snap.get("G_min_fuente"),
            "G_min_hay_dato": snap.get("G_min_hay_dato"),
            "mordida_usd": snap.get("mordida_usd"),
            "masa_total_usd": snap["masa_total_usd"],
            "pnl_est_usd": snap["pnl_est_usd"],
            "centro_0": snap["centro_0"],
            "centro_manto": snap.get("centro_manto"),
            "centro_wake": snap.get("centro_wake"),
            "composicion": snap["composicion"],
            "red_engorde_pct": (snap.get("red_engorde") or {}).get("pct_vs_centro"),
            "red_engorde_precio": (snap.get("red_engorde") or {}).get("precio"),
            "rails_vivos": snap["rails_vivos"],
            "es_semilla": act == sem,
            **tar,
        })

    activos = [a for a in activos if _santo_con_beru_y_manto(a)]
    vivos = {str(a.get("activo") or "").upper() for a in activos}
    corte = beru_wake.leer_wake_ritual()
    if corte <= 0:
        corte = 0.0
    if corte > 0:
        for act in _activos_cerrados_mariscal(vivos, corte):
            mark = float(precios.get(act) or precios.get(f"{act}USDT_SPOT") or 0)
            snap_c = snapshot_activo(act, [], precio_mark=mark, semilla=sem)
            activos.append(_fila_cerrado(act, snap_c))

    activos.sort(key=_clave_orden_flota)

    return {
        "ts": time.time(),
        "semilla": sem,
        "n_activos": len(activos),
        "n_barcos_total": sum(a["n_barcos"] for a in activos),
        "activos": activos,
    }


def mapa_asset_details(
    legion: list[Any],
    *,
    precios: dict[str, float] | None = None,
    semilla: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Mapa activo → ficha completa (para estado_vivo.beru_asset_details)."""
    sem = (semilla or beru_rail.activo_semilla()).upper()
    flota = flota_resumen(legion, semilla=sem, precios=precios)
    out: dict[str, dict[str, Any]] = {}
    precios = precios or {}
    by_act: dict[str, list] = {}
    for b in legion or []:
        act = _activo_barco(b, sem) or sem
        by_act.setdefault(act, []).append(b)
    for row in flota["activos"]:
        act = row["activo"]
        mark = float(precios.get(act) or precios.get(f"{act}USDT_SPOT") or 0)
        out[act] = snapshot_activo(act, by_act.get(act) or [], precio_mark=mark, semilla=sem)
    return out


def enriquecer_legion_resumen(legion: list[Any], semilla: str | None = None) -> list[dict[str, Any]]:
    """Filas ricas para estado_vivo.legion (compat + campos nuevos)."""
    sem = semilla or beru_rail.activo_semilla()
    out = []
    for b in legion or []:
        act = _activo_barco(b, sem)
        fila = _barco_fila(b, act)
        fila["activo"] = act
        fila["centro"] = fila["centro_0"] or fila["centro_local"]  # compat panel viejo
        fila["es_super"] = fila["es_super"]
        out.append(fila)
    return out
