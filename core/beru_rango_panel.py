"""Foto viva Beru rango → panel (Pergamino).

Escribe data/beru/rango_vivo.json con flota + niveles (0 / sangre / Red / Oz).
Multi-Santo: fusiona por activo (no pisa otros procesos).
Solo ojos de escritura local — sin manos.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from core import beru_rango_paths

ROOT = Path(__file__).resolve().parents[1]
RANGO_VIVO_PATH = beru_rango_paths.RANGO_VIVO_PATH

# Si un Santo no refresca en este tiempo, se retira del panel (proceso muerto).
STALE_S_DEFAULT = 120.0


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def niveles_combate(vivo: dict[str, Any], geom: dict[str, Any]) -> list[dict[str, Any]]:
    """Rayas del combate rango: wake=0, sangre=Vacío act., Red, Oz."""
    cero = _f(vivo.get("cero"))
    if cero <= 0:
        return []
    sp = _f(geom.get("sangre_pct"), 0.012)
    if sp > 1:
        sp /= 100.0
    masa = _f(geom.get("masa_usd"), 5.0)
    masa_red = _f(geom.get("masa_red_usd"), 5.0)
    niveles: list[dict[str, Any]] = [
        {"id": "wake", "precio": cero, "pct": 0.0, "rol": "wake"},
    ]
    lado = str(vivo.get("sangre_lado") or "").upper()
    up = cero * (1.0 + sp)
    dn = cero * (1.0 - sp)
    # Semilla: ambas activaciones. Tras Oz: solo el lado de sangre.
    if not lado:
        niveles.append(
            {
                "id": "sangre_up",
                "precio": up,
                "pct": sp * 100.0,
                "rol": "vacio",
                "label": "Sangre+",
                "masa_usd": masa,
            }
        )
        niveles.append(
            {
                "id": "sangre_dn",
                "precio": dn,
                "pct": -sp * 100.0,
                "rol": "vacio",
                "label": "Sangre−",
                "masa_usd": masa,
            }
        )
    elif lado == "ARRIBA":
        niveles.append(
            {
                "id": "sangre_up",
                "precio": up,
                "pct": sp * 100.0,
                "rol": "vacio",
                "label": "Sangre",
                "masa_usd": masa,
            }
        )
    elif lado == "ABAJO":
        niveles.append(
            {
                "id": "sangre_dn",
                "precio": dn,
                "pct": -sp * 100.0,
                "rol": "vacio",
                "label": "Sangre",
                "masa_usd": masa,
            }
        )

    red = _f(vivo.get("red"))
    if red > 0:
        niveles.append(
            {
                "id": "red",
                "precio": red,
                "pct": None,
                "rol": "red",
                "label": "Red",
                "masa_usd": masa_red,
            }
        )
    oz = _f(vivo.get("oz"))
    if oz > 0:
        niveles.append(
            {
                "id": "oz",
                "precio": oz,
                "pct": None,
                "rol": "oz",
                "label": "Oz",
                "masa_usd": _f(vivo.get("masa")) or masa,
            }
        )
    return niveles


def oficio_ui(estado: str) -> str:
    e = str(estado or "").upper()
    if e in ("CAZANDO", "COSECHA", "TRAILING"):
        return "cazando"
    if e in ("MUERTO", "OFF", "SELLADO"):
        return "cerrado"
    return "acechando"


def cazas_desde_eventos(activo: str, *, max_n: int = 40) -> list[dict[str, Any]]:
    """X del panel: fills Oz (OZ_COSECHA) del Santo en esta vida de eventos."""
    act = str(activo or "").strip().upper()
    if not act:
        return []
    path = beru_rango_paths.manos_eventos(act)
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    for line in lines:
        line = (line or "").strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        ev = str(row.get("evento") or "").upper()
        if ev != "OZ_COSECHA":
            continue
        det = row.get("detalle") if isinstance(row.get("detalle"), dict) else {}
        px = _f(det.get("oz")) or _f(det.get("cero")) or _f(det.get("precio"))
        ts = _f(row.get("ts"))
        if px <= 0 or ts <= 0:
            continue
        dir_u = str(det.get("dir") or det.get("direccion") or "").upper()
        if dir_u not in ("LONG", "SHORT"):
            sangre = str(det.get("sangre") or "").upper()
            # Post-Oz: LONG → sangre ARRIBA; SHORT → sangre ABAJO
            if sangre == "ARRIBA":
                dir_u = "LONG"
            elif sangre == "ABAJO":
                dir_u = "SHORT"
        lado = "Buy" if dir_u == "LONG" else "Sell" if dir_u == "SHORT" else None
        out.append(
            {
                "ts": int(ts),
                "precio": round(px, 8),
                "lado": lado,
                "evento": "OZ_COSECHA",
                "masa_usd": _f(det.get("masa_hecha") or det.get("masa")),
            }
        )
    return out[-max(1, int(max_n or 40)) :]


def cronica_desde_eventos(activo: str, *, max_n: int = 24) -> list[dict[str, Any]]:
    """Crónica corta para el detalle (ARMAR / OZ / RED)."""
    act = str(activo or "").strip().upper()
    path = beru_rango_paths.manos_eventos(act)
    if not act or not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    for line in lines:
        line = (line or "").strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        ev = str(row.get("evento") or "").upper()
        if not ev or ev in ("ACECHO", "CAZA"):
            continue
        det = row.get("detalle") if isinstance(row.get("detalle"), dict) else {}
        px = (
            _f(det.get("oz"))
            or _f(det.get("cero"))
            or _f(det.get("precio"))
            or _f(det.get("red"))
        )
        ts = _f(row.get("ts"))
        if ts <= 0:
            continue
        dir_u = str(det.get("dir") or det.get("direccion") or "").upper()
        tipo = "COSECHA" if ev == "OZ_COSECHA" else ev
        out.append(
            {
                "ts": ts,
                "tipo": tipo,
                "evento": ev,
                "precio": px if px > 0 else None,
                "direccion": dir_u or None,
                "detalle": det,
            }
        )
    return out[-max(1, int(max_n or 24)) :]


def posicion_desde_tusk(tusk: Any, activo: str) -> list[dict[str, Any]]:
    """Posiciones reales del Santo (libros Tusk alineados con Bybit)."""
    act = str(activo or "").strip().upper()
    if not act or tusk is None:
        return []
    pesos = getattr(tusk, "pesos", None) or {}
    frente = f"{act}USDT_LINEAL"
    row = pesos.get(frente)
    if not isinstance(row, dict):
        # fallback: buscar clave que empiece por ACTIVOUSDT
        for k, v in pesos.items():
            if str(k).upper().startswith(f"{act}USDT") and isinstance(v, dict):
                row = v
                break
    if not isinstance(row, dict):
        return []
    out: list[dict[str, Any]] = []
    lng = _f(row.get("long"))
    sh = _f(row.get("short"))
    px_l = _f(row.get("precio_medio_long"))
    px_s = _f(row.get("precio_medio_short"))
    if lng > 1e-12 and px_l > 0:
        out.append(
            {
                "lado": "LONG",
                "qty": lng,
                "precio": px_l,
                "masa_usd": round(lng * px_l, 4),
            }
        )
    if sh > 1e-12 and px_s > 0:
        out.append(
            {
                "lado": "SHORT",
                "qty": sh,
                "precio": px_s,
                "masa_usd": round(sh * px_s, 4),
            }
        )
    return out


def niveles_posicion(posiciones: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Rayas de gráfica: entrada real LONG/SHORT."""
    niv: list[dict[str, Any]] = []
    for p in posiciones or []:
        if not isinstance(p, dict):
            continue
        lado = str(p.get("lado") or "").upper()
        px = _f(p.get("precio"))
        qty = _f(p.get("qty"))
        if lado not in ("LONG", "SHORT") or px <= 0 or qty <= 0:
            continue
        rol = "posicion_long" if lado == "LONG" else "posicion_short"
        niv.append(
            {
                "id": f"pos_{lado.lower()}",
                "precio": px,
                "pct": None,
                "rol": rol,
                "label": lado,
                "lado": lado,
                "qty": qty,
                "masa_usd": _f(p.get("masa_usd")) or round(qty * px, 4),
            }
        )
    return niv


def armar_payload(
    *,
    snapshot: dict[str, Any],
    last: float,
    activo: str | None = None,
    posicion: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Construye flota+details para el panel (solo Santos con vivo)."""
    snap = snapshot or {}
    geom = snap.get("geometria") or {}
    vivo = snap.get("vivo")
    act = str(activo or snap.get("activo") or "").upper()
    if not act or not isinstance(vivo, dict):
        return {
            "ts": time.time(),
            "oficio": "RANGO",
            "mercado": "linear",
            "activos": [],
            "details": {},
            "latido_vivo": False,
        }
    estado = str(vivo.get("estado") or "")
    if not estado or estado.upper() in ("OFF", "MUERTO"):
        return {
            "ts": time.time(),
            "oficio": "RANGO",
            "mercado": "linear",
            "activos": [],
            "details": {},
            "latido_vivo": False,
        }

    cero = _f(vivo.get("cero"))
    last_f = _f(last) or cero
    niveles = niveles_combate(vivo, geom)
    pos_list = list(posicion or [])
    niveles.extend(niveles_posicion(pos_list))
    cazas = cazas_desde_eventos(act)
    cronica = cronica_desde_eventos(act)
    oficio = oficio_ui(estado)
    sp = _f(geom.get("sangre_pct"), 0.012)
    if sp > 1:
        sp /= 100.0
    barco = {
        "uid": vivo.get("uid") or f"RANGO_{act}",
        "activo": act,
        "estado": estado,
        "direccion": vivo.get("direccion") or "",
        "centro_local": cero,
        "ancla_tramo": cero,
        "centro_wake": cero,
        "oz_adan": _f(vivo.get("oz")),
        "oz_precio": _f(vivo.get("oz")),
        "red_precio": _f(vivo.get("red")),
        "red_adan": _f(vivo.get("red")),
        "masa": _f(vivo.get("masa")),
        "sangre_lado": vivo.get("sangre_lado") or "",
        "cosechas_continuas": int(vivo.get("cosechas") or 0),
        "rango_escalones_red": int(vivo.get("escalones_red") or 0),
        "trail_extremo": _f(vivo.get("trail_extremo")),
        "vacio_pct": sp * 100.0,
        "grado": "GENERAL",
        "oficio": "RANGO",
        "carta_colgada": _f(vivo.get("oz")) > 0,
    }
    lado = str(vivo.get("sangre_lado") or "").upper()
    if not lado:
        barco["vacio_arriba"] = cero * (1.0 + sp) if cero > 0 else 0.0
        barco["vacio_abajo"] = cero * (1.0 - sp) if cero > 0 else 0.0
    elif lado == "ARRIBA":
        barco["vacio_arriba"] = cero * (1.0 + sp) if cero > 0 else 0.0
        barco["vacio_abajo"] = 0.0
    else:
        barco["vacio_arriba"] = 0.0
        barco["vacio_abajo"] = cero * (1.0 - sp) if cero > 0 else 0.0

    detail = {
        "symbol": act,
        "oficio": "RANGO",
        "mercado": "linear",
        "spot_last": last_f,
        "last_lineal": last_f,
        "G_min": _f(geom.get("masa_usd"), 5.0),
        "centro_manto": cero,
        "n_barcos": 1,
        "grado": "GENERAL",
        "barcos": [barco],
        "grafica": {
            "mercado": "linear",
            "oficio": "RANGO",
            "centro_0": cero,
            "centro_wake": cero,
            "centro_manto": cero,
            "niveles": niveles,
            "cazas": cazas,
            "posicion": pos_list,
        },
        "vivo_rango": vivo,
        "geometria": geom,
        "manos": bool(snap.get("manos")),
        "posicion": pos_list,
        "cronica": cronica,
        "pid": os.getpid(),
        "ts_santo": time.time(),
    }
    row = {
        "activo": act,
        "grado": "GENERAL",
        "oficio": oficio,
        "n_barcos": 1,
        "centro_manto": cero,
        "estado": estado,
        "last": last_f,
        "cero": cero,
        "oz": _f(vivo.get("oz")),
        "red": _f(vivo.get("red")),
        "sangre_lado": vivo.get("sangre_lado") or "",
        "cosechas": int(vivo.get("cosechas") or 0),
        "escalones_red": int(vivo.get("escalones_red") or 0),
        "n_cazas": len(cazas),
        "manos": bool(snap.get("manos")),
        "mercado": "linear",
        "posicion": pos_list,
        "pid": os.getpid(),
        "ts_santo": time.time(),
    }
    return {
        "ts": time.time(),
        "oficio": "RANGO",
        "mercado": "linear",
        "activos": [row],
        "details": {act: detail},
        "latido_vivo": True,
        "activo_foco": act,
    }


def _leer_vivo(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _purgar_stale(
    base: dict[str, Any],
    *,
    stale_s: float,
    now: float,
) -> dict[str, Any]:
    acts = list(base.get("activos") or [])
    details = dict(base.get("details") or {})
    vivos: list[dict[str, Any]] = []
    for row in acts:
        if not isinstance(row, dict):
            continue
        act = str(row.get("activo") or "").upper()
        if not act:
            continue
        ts = _f(row.get("ts_santo")) or _f(base.get("ts"))
        if ts > 0 and (now - ts) > stale_s:
            details.pop(act, None)
            continue
        vivos.append(row)
    base["activos"] = vivos
    base["details"] = details
    return base


def _fusionar(
    base: dict[str, Any],
    piece: dict[str, Any],
    *,
    stale_s: float,
) -> dict[str, Any]:
    now = time.time()
    base = _purgar_stale(base if base else {}, stale_s=stale_s, now=now)
    if not piece.get("activos") and not piece.get("details"):
        return base

    by_act: dict[str, dict[str, Any]] = {}
    for row in base.get("activos") or []:
        if isinstance(row, dict) and row.get("activo"):
            by_act[str(row["activo"]).upper()] = row
    details = dict(base.get("details") or {})

    for row in piece.get("activos") or []:
        if not isinstance(row, dict):
            continue
        act = str(row.get("activo") or "").upper()
        if not act:
            continue
        by_act[act] = row
    for act, det in (piece.get("details") or {}).items():
        a = str(act).upper()
        if a and isinstance(det, dict):
            details[a] = det

    activos = sorted(by_act.values(), key=lambda r: str(r.get("activo") or ""))
    foco = str(piece.get("activo_foco") or base.get("activo_foco") or "")
    if foco.upper() not in {str(r.get("activo") or "").upper() for r in activos}:
        foco = str(activos[0].get("activo") or "") if activos else ""

    return {
        "ts": now,
        "oficio": "RANGO",
        "mercado": "linear",
        "activos": activos,
        "details": details,
        "latido_vivo": bool(activos),
        "activo_foco": foco.upper() if foco else "",
        "n_santos": len(activos),
        "pids": sorted(
            {
                int(r.get("pid") or 0)
                for r in activos
                if int(r.get("pid") or 0) > 0
            }
        ),
    }


def _con_candado(path: Path, fn, *, intentos: int = 80, sleep_s: float = 0.025):
    """Candado de archivo exclusivo (Windows/POSIX) para no pisar escrituras."""
    lock = path.with_name(path.name + ".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    last_err: Exception | None = None
    for _ in range(max(1, intentos)):
        fd = None
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            try:
                return fn()
            finally:
                try:
                    os.close(fd)
                except Exception:
                    pass
                try:
                    lock.unlink(missing_ok=True)
                except Exception:
                    pass
                fd = None
        except FileExistsError:
            time.sleep(sleep_s)
        except Exception as exc:
            last_err = exc
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
            time.sleep(sleep_s)
    if last_err:
        raise last_err
    return fn()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Escritura atómica; en Windows no se cuelga si el panel tiene el archivo abierto."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    last_err: Exception | None = None
    for _ in range(20):
        try:
            os.replace(str(tmp), str(path))
            return
        except PermissionError as exc:
            last_err = exc
            time.sleep(0.05)
        except OSError as exc:
            last_err = exc
            time.sleep(0.05)
    try:
        path.write_text(data, encoding="utf-8")
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
    if last_err and not path.is_file():
        raise last_err


def publicar(
    *,
    snapshot: dict[str, Any],
    last: float,
    activo: str | None = None,
    path: Path | None = None,
    merge: bool = True,
    stale_s: float = STALE_S_DEFAULT,
    tusk: Any = None,
    posicion: list[dict[str, Any]] | None = None,
) -> Path:
    """Publica un Santo. Por defecto fusiona con la flota ya viva."""
    out = path or RANGO_VIVO_PATH
    act = str(activo or (snapshot or {}).get("activo") or "").upper()
    pos = list(posicion) if posicion is not None else (
        posicion_desde_tusk(tusk, act) if tusk is not None and act else []
    )
    piece = armar_payload(
        snapshot=snapshot, last=last, activo=activo, posicion=pos,
    )

    def _write():
        if not merge:
            payload = piece
        else:
            prev = _leer_vivo(out)
            payload = _fusionar(prev, piece, stale_s=float(stale_s))
        _atomic_write_json(out, payload)
        return out

    return _con_candado(out, _write)


def publicar_flota(
    *,
    piezas: list[dict[str, Any]],
    path: Path | None = None,
    stale_s: float = STALE_S_DEFAULT,
) -> Path:
    """Fusiona varios payloads ya armados (un proceso, varios Santos)."""
    out = path or RANGO_VIVO_PATH

    def _write():
        prev = _leer_vivo(out)
        payload = prev
        for piece in piezas:
            if isinstance(piece, dict):
                payload = _fusionar(payload, piece, stale_s=float(stale_s))
        _atomic_write_json(out, payload)
        return out

    return _con_candado(out, _write)


def retirar_activo(
    activo: str,
    *,
    path: Path | None = None,
) -> Path:
    """Saca un Santo del panel al sellar el proceso."""
    out = path or RANGO_VIVO_PATH
    act = str(activo or "").upper()

    def _write():
        prev = _leer_vivo(out)
        acts = [
            r
            for r in (prev.get("activos") or [])
            if isinstance(r, dict) and str(r.get("activo") or "").upper() != act
        ]
        details = dict(prev.get("details") or {})
        details.pop(act, None)
        payload = {
            "ts": time.time(),
            "oficio": "RANGO",
            "mercado": "linear",
            "activos": acts,
            "details": details,
            "latido_vivo": bool(acts),
            "activo_foco": str(acts[0].get("activo") or "").upper() if acts else "",
            "n_santos": len(acts),
        }
        _atomic_write_json(out, payload)
        return out

    return _con_candado(out, _write)
