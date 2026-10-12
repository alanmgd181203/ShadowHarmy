"""Ficha de auditoría por Santo — para revisar tumores sin abrir el cráneo.

No planta. No cambia masa ni órdenes. Solo lee sello + eventos + Iron y escribe
``data/beru/rango/{ACT}/ficha_auditoria.json``.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from core import beru_rango_paths as paths

# Alertas (auditoría humana / agente)
_PCT_LEJOS_WARN = 0.015  # 1,5 % desde última Oz/fill
_PCT_LEJOS_CRIT = 0.040  # 4 %
_EDAD_ORDEN_WARN_S = 900.0  # 15 min sin fill con campaña viva
_EDAD_SELLO_TIBIO_S = 300.0  # 5 min


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x if x is not None else default)
    except (TypeError, ValueError):
        return float(default)


def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x if x is not None else default)
    except (TypeError, ValueError):
        return int(default)


def _pct(a: float, b: float) -> float | None:
    """|a-b|/b en fracción. None si no hay ancla."""
    if b <= 1e-12 or a <= 1e-12:
        return None
    return abs(a - b) / b


def _leer_eventos(path: Path, *, limit: int = 120) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for ln in lines[-limit:]:
        try:
            row = json.loads(ln)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _det(ev: dict[str, Any]) -> dict[str, Any]:
    d = ev.get("detalle")
    return d if isinstance(d, dict) else {}


def armar_ficha(
    activo: str,
    *,
    last: float | None = None,
    snapshot: dict[str, Any] | None = None,
    informe: dict[str, Any] | None = None,
    mercado: str = "linear",
    perfil: str = "piedra",
) -> dict[str, Any]:
    """Construye la ficha. No escribe disco."""
    act = str(activo or "").strip().upper()
    ahora = time.time()
    vivo: dict[str, Any] = {}
    geo: dict[str, Any] = {}
    if isinstance(snapshot, dict):
        vivo = snapshot.get("vivo") or {}
        geo = snapshot.get("geometria") or {}
    elif isinstance(informe, dict):
        snap = informe.get("snapshot") or {}
        vivo = (snap.get("vivo") or {}) if isinstance(snap, dict) else {}
        geo = (snap.get("geometria") or {}) if isinstance(snap, dict) else {}
        if last is None:
            last = _f(informe.get("last") or informe.get("last_lineal"))

    px = _f(last)
    ev_path = paths.eventos_manos(act, mercado, perfil)
    eventos = _leer_eventos(ev_path)

    # --- última orden ejecutada (fill / Oz cosecha preferida) ---
    ultima: dict[str, Any] | None = None
    fills: list[tuple[float, float, str]] = []  # ts, fill_px, tipo
    spreads_oz: list[float] = []  # |fill-oz|/oz
    caminos: list[float] = []  # % entre fills consecutivos mismo lado
    reds_dir = 0
    oz_dir = 0
    sangre_n = 0
    prev_fill: tuple[float, str] | None = None  # px, dir

    for ev in eventos:
        tipo = str(ev.get("evento") or ev.get("tipo") or "")
        det = _det(ev)
        ts = _f(ev.get("ts"))
        d = str(det.get("dir") or "").upper()
        if tipo == "OZ_COSECHA":
            oz_dir += 1
            fill = _f(det.get("fill") or det.get("oz") or det.get("oz_despliegue"))
            oz = _f(det.get("oz") or det.get("oz_despliegue") or fill)
            if fill > 0:
                fills.append((ts, fill, "OZ_COSECHA"))
                if oz > 0:
                    sp = _pct(fill, oz)
                    if sp is not None:
                        spreads_oz.append(sp)
                if prev_fill and prev_fill[1] == d and prev_fill[0] > 0:
                    cam = _pct(fill, prev_fill[0])
                    if cam is not None:
                        caminos.append(cam)
                prev_fill = (fill, d)
            ultima = {
                "ts": ts,
                "evento": "OZ_COSECHA",
                "dir": d,
                "precio": fill or oz,
                "oz": oz,
                "fill": fill,
                "masa": _f(det.get("masa_hecha") or det.get("masa")),
                "red": _f(det.get("red")),
            }
        elif tipo == "ARMAR_RED":
            reds_dir += 1
            if ultima is None or _f(ultima.get("ts")) <= ts:
                # no pisa Oz como "ejecutada"; solo si no hay Oz reciente después
                pass
            # precio de planta no es fill; se anota aparte
        elif tipo == "ARMAR_SANGRE":
            sangre_n += 1

    # si la última fila del jsonl es ARMAR_* más nueva que Oz, la Oz sigue siendo
    # la última *ejecutada* (fill). Buscar Oz más reciente explícita:
    ultima_oz = None
    for ev in reversed(eventos):
        if str(ev.get("evento") or "") != "OZ_COSECHA":
            continue
        det = _det(ev)
        ts = _f(ev.get("ts"))
        fill = _f(det.get("fill") or det.get("oz") or det.get("oz_despliegue"))
        oz = _f(det.get("oz") or det.get("oz_despliegue") or fill)
        ultima_oz = {
            "ts": ts,
            "evento": "OZ_COSECHA",
            "dir": str(det.get("dir") or "").upper(),
            "precio": fill or oz,
            "oz": oz,
            "fill": fill,
            "masa": _f(det.get("masa_hecha") or det.get("masa")),
            "red": _f(det.get("red")),
            "edad_s": round(ahora - ts, 1) if ts > 0 else None,
        }
        break

    precio_ref = _f((ultima_oz or {}).get("precio"))
    pct_desde_ultima = _pct(px, precio_ref) if px > 0 and precio_ref > 0 else None

    spread_prom = (
        sum(spreads_oz[-12:]) / len(spreads_oz[-12:]) if spreads_oz else None
    )
    camino_prom = sum(caminos[-12:]) / len(caminos[-12:]) if caminos else None

    # Iron
    iron: dict[str, Any] = {}
    try:
        from cirugias.hiron.campo_masa import leer as _leer_iron

        iron = _leer_iron(act) or {}
    except Exception:
        iron = {}

    estado = str(vivo.get("estado") or "")
    origen = str(vivo.get("origen_tramo") or "")
    escalones = _i(vivo.get("escalones_red"))
    mem = _i(vivo.get("engorde_memoria_peldaños"))
    off = _i(vivo.get("engorde_peldaño_offset"))
    eng0 = _f(vivo.get("engorde_cero_oz"))
    masa = _f(vivo.get("masa"))
    red_px = _f(vivo.get("red"))
    oz_viva = _f(vivo.get("oz"))
    sangre_px = _f(vivo.get("sangre") or vivo.get("sangre_adan"))

    # alertas
    alertas: list[str] = []
    if pct_desde_ultima is not None and pct_desde_ultima >= _PCT_LEJOS_CRIT:
        alertas.append("LEJOS_CRIT_ultima_oz")
    elif pct_desde_ultima is not None and pct_desde_ultima >= _PCT_LEJOS_WARN:
        alertas.append("LEJOS_WARN_ultima_oz")
    edad_oz = (ultima_oz or {}).get("edad_s")
    if (
        isinstance(edad_oz, (int, float))
        and edad_oz >= _EDAD_ORDEN_WARN_S
        and estado == "CAZANDO"
    ):
        alertas.append("CAZANDO_SIN_FILL_RECIENTE")
    if estado == "CAZANDO" and masa <= 0:
        alertas.append("CAZANDO_SIN_MASA")
    if mem > 0 and off == 0 and origen == "RED":
        alertas.append("MEMORIA_SIN_OFFSET")
    if eng0 > 0 and mem == 0 and escalones >= 2:
        alertas.append("REDES_SIN_MEMORIA")

    # masa delta aproximada próxima Red (si hay engorde_cero y last/red)
    masa_proxima_red = None
    try:
        from core import beru_rango as br

        if eng0 > 0 and (red_px > 0 or px > 0) and br.engorde_modo_peldaños_sumados():

            class _B:
                pass

            b = _B()
            b.origen_tramo = "RED"
            b.direccion = str(vivo.get("direccion") or vivo.get("ultima_hoz_direccion") or "")
            b.ultima_hoz_direccion = b.direccion
            b.engorde_cero_oz_px = eng0
            b.engorde_peldaño_offset = off
            b.engorde_memoria_peldaños = mem
            ref_px = red_px if red_px > 0 else px
            n = br.peldaños_para_engorde(b, eng0, ref_px)
            base = br._base_masa_origen("RED", b)
            step = br.engorde_paso_usd(b)
            tope = br.engorde_tope_usd(b)
            masa_proxima_red = round(
                br._masa_delta_peldaños(n, off, base, step, tope_por_peldaño=tope),
                4,
            )
    except Exception:
        masa_proxima_red = None

    # últimas 6 acciones compactas
    recientes: list[dict[str, Any]] = []
    for ev in eventos[-8:]:
        tipo = str(ev.get("evento") or "")
        if tipo not in ("OZ_COSECHA", "ARMAR_RED", "ARMAR_SANGRE"):
            continue
        det = _det(ev)
        ts = _f(ev.get("ts"))
        recientes.append(
            {
                "edad_s": round(ahora - ts, 1) if ts > 0 else None,
                "evento": tipo,
                "dir": str(det.get("dir") or ""),
                "masa": _f(det.get("masa_hecha") or det.get("masa")),
                "escalon": det.get("escalon"),
                "fill": _f(det.get("fill")) or None,
                "oz": _f(det.get("oz") or det.get("oz_despliegue")) or None,
            }
        )

    ficha = {
        "oficio": "FICHA_AUDITORIA_BERU",
        "activo": act,
        "ts": ahora,
        "perfil": perfil,
        "mercado": mercado,
        "estado": estado,
        "origen_tramo": origen,
        "direccion": str(vivo.get("direccion") or ""),
        "sangre_lado": str(vivo.get("sangre_lado") or ""),
        "ultima_hoz": str(vivo.get("ultima_hoz_direccion") or ""),
        "campana": {
            "redes_consecutivas": escalones,
            "cosechas_continuas": _i(vivo.get("cosechas")),
            "engorde_cero_oz": eng0,
            "engorde_memoria_peldaños": mem,
            "engorde_peldaño_offset": off,
            "engorde_campana_dir": str(vivo.get("engorde_campana_dir") or ""),
        },
        "mapa": {
            "last": px or None,
            "cero_wake": _f(vivo.get("cero")) or None,
            "oz_viva": oz_viva or None,
            "red": red_px or None,
            "sangre": sangre_px or None,
            "red_long_pct": geo.get("red_activacion_long_pct"),
            "red_short_pct": geo.get("red_activacion_short_pct"),
        },
        "masa": {
            "viva": masa,
            "proxima_red_delta_est": masa_proxima_red,
            "saco_long": _f(vivo.get("saco_long")),
            "saco_short": _f(vivo.get("saco_short")),
        },
        "ultima_orden_ejecutada": ultima_oz,
        "desde_ultima_orden": {
            "pct": None if pct_desde_ultima is None else round(pct_desde_ultima, 6),
            "pct_humano": None
            if pct_desde_ultima is None
            else round(pct_desde_ultima * 100.0, 3),
            "precio_ref": precio_ref or None,
            "last": px or None,
        },
        "calidad_fills": {
            "n_oz_en_ventana": len(spreads_oz),
            "spread_oz_fill_prom_pct": None
            if spread_prom is None
            else round(spread_prom * 100.0, 4),
            "camino_entre_oz_prom_pct": None
            if camino_prom is None
            else round(camino_prom * 100.0, 4),
        },
        "iron": {
            "campo": iron.get("campo"),
            "factor": iron.get("factor"),
            "ganancia_pct": None
            if iron.get("ganancia_frac") is None
            else round(_f(iron.get("ganancia_frac")) * 100.0, 3),
            "posicion_usd": iron.get("posicion_usd"),
        },
        "contadores_ventana": {
            "oz": oz_dir,
            "armar_red": reds_dir,
            "armar_sangre": sangre_n,
        },
        "recientes": recientes[-6:],
        "alertas": alertas,
        "ok_auditoria": len(alertas) == 0,
    }
    return ficha


def escribir_ficha(
    activo: str,
    *,
    last: float | None = None,
    snapshot: dict[str, Any] | None = None,
    informe: dict[str, Any] | None = None,
    mercado: str = "linear",
    perfil: str = "piedra",
) -> Path:
    """Arma y sella la ficha en disco. Nunca lanza al caller de manos."""
    act = str(activo or "").strip().upper()
    path = paths.ficha_auditoria(act)
    try:
        ficha = armar_ficha(
            act,
            last=last,
            snapshot=snapshot,
            informe=informe,
            mercado=mercado,
            perfil=perfil,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        # La ficha no tumba al Santo.
        pass
    return path


def leer_ficha(activo: str) -> dict[str, Any]:
    path = paths.ficha_auditoria(activo)
    if not path.is_file():
        return {}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}
    return d if isinstance(d, dict) else {}
