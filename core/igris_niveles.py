"""Escalera permanente de Igris — el freno sobrevive reinicios.

Ley:
- Archivo ausente/corrupto ⇒ nivel 0 (solo ojos).
- Variables/env/``--nivel`` solo pueden bajar el techo, nunca subir.
- Ascenso explícito: ``ascender()`` (+1) o ``fijar_nivel()`` con ``forzar=True``.
- Duales confirmados se acumulan en el libro mainnet; reiniciar no borra el cupo.
- Manos paralelas: varios ``duales_pendientes`` (uno por Santo). ``bloqueado``
  solo tras incertidumbre (abort); no castra otras manos en vuelo.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

NIVELES: dict[int, dict[str, Any]] = {
    0: {
        "nombre": "OJOS",
        "solo_ojos": True,
        "max_duales": 0,
        "desc": "Reconciliar, calcular pase y publicar qué haría; sin órdenes.",
    },
    1: {
        "nombre": "UN_DUAL",
        "solo_ojos": False,
        "max_duales": 1,
        "desc": "Un bocado L+S confirmado acumulado.",
    },
    2: {
        "nombre": "TRES_DUALES",
        "solo_ojos": False,
        "max_duales": 3,
        "desc": "Hasta tres bocados L+S confirmados acumulados.",
    },
    3: {
        "nombre": "DIEZ_DUALES",
        "solo_ojos": False,
        "max_duales": 10,
        "desc": "Guardia prolongada con freno a diez duales.",
    },
    4: {
        "nombre": "AUTONOMO",
        "solo_ojos": False,
        "max_duales": 0,
        "desc": "Sin tope numérico; el pase y el oxígeno mandan.",
    },
}

_ROOT = Path(__file__).resolve().parents[1]
_RUTA_DEFAULT = _ROOT / "data" / "igris_nivel_mainnet.json"
_LIBRO_LOCK = threading.RLock()


def ruta_libro(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    raw = os.getenv("IGRIS_NIVEL_LIBRO", "").strip()
    return Path(raw) if raw else _RUTA_DEFAULT


def normalizar_nivel(value: Any) -> int:
    try:
        nivel = int(float(value))
    except (TypeError, ValueError):
        nivel = 0
    return min(max(nivel, min(NIVELES)), max(NIVELES))


def perfil(value: Any) -> dict[str, Any]:
    nivel = normalizar_nivel(value)
    return {"nivel": nivel, **NIVELES[nivel]}


def _estado_seguro() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "red": "mainnet",
        "modo": "ESCALONADO",
        "nivel": 0,
        "duales_confirmados": 0,
        "dual_pendiente": None,
        "duales_pendientes": {},
        "bloqueado": False,
        "revision": 0,
        "ultimo_recibo": {},
        "actualizado_ts": 0.0,
    }


def _pendientes_de(libro: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Mapa activo→pendiente; migra el legado ``dual_pendiente`` único."""
    out: dict[str, dict[str, Any]] = {}
    raw = libro.get("duales_pendientes")
    if isinstance(raw, dict):
        for k, v in raw.items():
            act = str(k or "").upper()
            if act and isinstance(v, dict):
                out[act] = dict(v)
                out[act]["activo"] = act
    legacy = libro.get("dual_pendiente")
    if isinstance(legacy, dict):
        act = str(legacy.get("activo") or "").upper()
        if act and act not in out:
            out[act] = dict(legacy)
            out[act]["activo"] = act
    return out


def _sync_pendientes(libro: dict[str, Any], pendientes: dict[str, dict[str, Any]]) -> None:
    libro["duales_pendientes"] = dict(pendientes)
    libro["dual_pendiente"] = next(iter(pendientes.values()), None)


def _escribir_atomico(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    if path.exists():
        path.unlink()
    os.rename(tmp, path)


def cargar(path: str | Path | None = None) -> dict[str, Any]:
    with _LIBRO_LOCK:
        libro = ruta_libro(path)
        if not libro.exists():
            return _estado_seguro()
        try:
            raw = json.loads(libro.read_text(encoding="utf-8"))
        except Exception:
            return _estado_seguro()
        if not isinstance(raw, dict) or str(raw.get("red") or "") != "mainnet":
            return _estado_seguro()
        out = _estado_seguro()
        out.update(raw)
        out["nivel"] = normalizar_nivel(out.get("nivel"))
        try:
            out["duales_confirmados"] = max(0, int(float(out.get("duales_confirmados") or 0)))
        except (TypeError, ValueError):
            out["duales_confirmados"] = 0
        out["bloqueado"] = bool(out.get("bloqueado"))
        _sync_pendientes(out, _pendientes_de(out))
        return out


def guardar(estado: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    with _LIBRO_LOCK:
        out = _estado_seguro()
        out.update(dict(estado or {}))
        out["nivel"] = normalizar_nivel(out.get("nivel"))
        out["duales_confirmados"] = max(0, int(float(out.get("duales_confirmados") or 0)))
        out["bloqueado"] = bool(out.get("bloqueado"))
        out["red"] = "mainnet"
        _sync_pendientes(out, _pendientes_de(out))
        out["actualizado_ts"] = time.time()
        out["revision"] = int(float(out.get("revision") or 0)) + 1
        _escribir_atomico(ruta_libro(path), out)
        return out


def nivel_efectivo(pedido: Any = None, path: str | Path | None = None) -> dict[str, Any]:
    """Techo efectivo = min(libro, pedido). Pedido None ⇒ solo libro."""
    libro = cargar(path)
    nivel_libro = normalizar_nivel(libro.get("nivel"))
    if pedido is None:
        nivel = nivel_libro
    else:
        nivel = min(nivel_libro, normalizar_nivel(pedido))
    p = perfil(nivel)
    pendientes = _pendientes_de(libro)
    return {
        **p,
        "nivel_libro": nivel_libro,
        "duales_confirmados": int(libro.get("duales_confirmados") or 0),
        "bloqueado": bool(libro.get("bloqueado")),
        "dual_pendiente": libro.get("dual_pendiente"),
        "duales_pendientes": pendientes,
        "libro": libro,
    }


def aplicar(config: Any, value: Any = None, *, path: str | Path | None = None) -> dict[str, Any]:
    """Sincroniza config con el techo efectivo (nunca asciende el libro)."""
    p = nivel_efectivo(value, path=path)
    config.IGRIS_DESPLIEGUE_NIVEL = int(p["nivel"])
    config.IGRIS_MAX_DUALES_SESION = int(p["max_duales"])
    return p


def puede_disparar(
    path: str | Path | None = None,
    *,
    pedido: Any = None,
    activo: str | None = None,
) -> dict[str, Any]:
    p = nivel_efectivo(pedido, path=path)
    if p["bloqueado"]:
        return {**p, "ok": False, "motivo": "bloqueado"}
    if p["solo_ojos"]:
        return {**p, "ok": False, "motivo": "nivel_ojos"}
    pendientes = dict(p.get("duales_pendientes") or {})
    act = str(activo or "").upper()
    if act and act in pendientes:
        return {**p, "ok": False, "motivo": "pendiente_mismo_santo"}
    tope = int(p["max_duales"] or 0)
    usados = int(p["duales_confirmados"] or 0)
    en_vuelo = len(pendientes)
    if tope > 0 and (usados + en_vuelo) >= tope:
        return {**p, "ok": False, "motivo": "tope_duales"}
    return {**p, "ok": True, "motivo": "autorizado"}


def reservar_dual(
    activo: str,
    *,
    path: str | Path | None = None,
    dual_id: str | None = None,
) -> dict[str, Any]:
    with _LIBRO_LOCK:
        act = str(activo or "").upper()
        gate = puede_disparar(path, activo=act)
        if not gate.get("ok"):
            return {**gate, "reservado": False}
        libro = dict(gate["libro"])
        pendientes = _pendientes_de(libro)
        pending = {
            "dual_id": dual_id or f"dual-{int(time.time() * 1000)}-{act or 'X'}",
            "activo": act,
            "ts": time.time(),
        }
        pendientes[act] = pending
        _sync_pendientes(libro, pendientes)
        guardado = guardar(libro, path=path)
        return {**gate, "ok": True, "reservado": True, "pendiente": pending, "libro": guardado}


def confirmar_dual(
    recibo: dict[str, Any] | None = None,
    *,
    path: str | Path | None = None,
    activo: str | None = None,
) -> dict[str, Any]:
    with _LIBRO_LOCK:
        libro = cargar(path)
        recibo = dict(recibo or {})
        act = str(activo or recibo.get("activo") or "").upper()
        pendientes = _pendientes_de(libro)
        if act and act in pendientes:
            pendientes.pop(act, None)
        elif pendientes and not act:
            first = next(iter(pendientes))
            pendientes.pop(first, None)
            act = first
        _sync_pendientes(libro, pendientes)
        libro["duales_confirmados"] = int(libro.get("duales_confirmados") or 0) + 1
        libro["bloqueado"] = False
        libro["ultimo_recibo"] = recibo
        libro["ultimo_recibo"]["activo"] = act or recibo.get("activo")
        libro["ultimo_recibo"]["ts"] = time.time()
        return guardar(libro, path=path)


def abortar_pendiente(
    *,
    path: str | Path | None = None,
    consumir_cupo: bool = True,
    motivo: str = "abortado",
    activo: str | None = None,
    congelar_ejercito: bool | None = None,
) -> dict[str, Any]:
    """Tras orden incierta: conserva cupo (conservador) y deja rastro.

    En nivel autónomo (sin tope numérico) o con manos paralelas, un dual
    incompleto NO debe congelar a todos los Santos: solo limpia ese pendiente.
    En niveles 1–3 sí puede pedir revisión humana (``bloqueado``).
    """
    with _LIBRO_LOCK:
        libro = cargar(path)
        pendientes = _pendientes_de(libro)
        act = str(activo or "").upper()
        if act and act in pendientes:
            pend = pendientes.pop(act)
        elif pendientes:
            act = next(iter(pendientes))
            pend = pendientes.pop(act)
        else:
            pend = libro.get("dual_pendiente")
        if consumir_cupo and pend:
            libro["duales_confirmados"] = int(libro.get("duales_confirmados") or 0) + 1
        libro["ultimo_recibo"] = {
            "ok": False,
            "motivo": motivo,
            "pendiente": pend,
            "ts": time.time(),
        }
        _sync_pendientes(libro, pendientes)
        nivel = normalizar_nivel(libro.get("nivel"))
        tope = int(NIVELES[nivel].get("max_duales") or 0)
        if congelar_ejercito is None:
            # Autónomo (tope 0) = no castrar el lote por una mano fallida.
            congelar_ejercito = tope > 0 and consumir_cupo
        libro["bloqueado"] = bool(congelar_ejercito)
        return guardar(libro, path=path)


def liberar_bloqueo(path: str | Path | None = None) -> dict[str, Any]:
    with _LIBRO_LOCK:
        libro = cargar(path)
        libro["bloqueado"] = False
        _sync_pendientes(libro, {})
        return guardar(libro, path=path)


def ascender(path: str | Path | None = None) -> dict[str, Any]:
    with _LIBRO_LOCK:
        libro = cargar(path)
        actual = normalizar_nivel(libro.get("nivel"))
        if actual >= max(NIVELES):
            return {**perfil(actual), "libro": libro, "ascendido": False, "motivo": "ya_maximo"}
        libro["nivel"] = actual + 1
        libro["bloqueado"] = False
        _sync_pendientes(libro, {})
        guardado = guardar(libro, path=path)
        return {**perfil(guardado["nivel"]), "libro": guardado, "ascendido": True}


def fijar_nivel(nivel: Any, path: str | Path | None = None, *, forzar: bool = False) -> dict[str, Any]:
    with _LIBRO_LOCK:
        libro = cargar(path)
        destino = normalizar_nivel(nivel)
        actual = normalizar_nivel(libro.get("nivel"))
        if destino > actual and not forzar:
            return {
                **perfil(actual),
                "libro": libro,
                "cambiado": False,
                "motivo": "ascenso_requiere_forzar_o_ascender",
            }
        libro["nivel"] = destino
        libro["bloqueado"] = False
        _sync_pendientes(libro, {})
        guardado = guardar(libro, path=path)
        return {**perfil(destino), "libro": guardado, "cambiado": True}
