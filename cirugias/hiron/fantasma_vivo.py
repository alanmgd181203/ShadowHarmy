"""El fantasma que el hacha deja, y que el cazador consulta.

El cazador no abre mientras este libro tenga su nombre.
Cuando nace el cero, el campamento lo usa como wake y borra la hoja.
"""
from __future__ import annotations

import json
from pathlib import Path

from cirugias.hiron.fantasma import Fantasma

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "data" / "beru" / "papel" / "fantasma.json"


def _leer() -> dict:
    if not RUTA.exists():
        return {}
    try:
        data = json.loads(RUTA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _guardar(data: dict) -> None:
    RUTA.parent.mkdir(parents=True, exist_ok=True)
    temporal = RUTA.with_suffix(".tmp")
    temporal.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporal.replace(RUTA)


def sellar_corte(santo: str, corte: float) -> None:
    """El hacha vació la bolsa. Empieza el fantasma en el precio del corte."""
    nombre = str(santo or "").strip().upper()
    px = float(corte or 0)
    if not nombre or px <= 0:
        return
    doc = _leer()
    viejo = doc.get(nombre)
    if isinstance(viejo, dict) and float(viejo.get("cero") or 0) <= 0 and float(viejo.get("corte") or 0) > 0:
        return
    doc[nombre] = {
        "corte": px,
        "puerta": 0.0,
        "punta_alta": px,
        "punta_baja": px,
        "mando": "",
        "cero": 0.0,
        "lado": "",
        "callado": False,
        "anunciado": False,
    }
    _guardar(doc)


def paso(santo: str, precio: float, puerta: float) -> dict:
    """libre, sigue, o nacio. Nacio trae el nuevo cero."""
    nombre = str(santo or "").strip().upper()
    doc = _leer()
    row = doc.get(nombre)
    if not isinstance(row, dict):
        return {"estado": "libre"}
    if float(row.get("cero") or 0) > 0 and str(row.get("lado") or "") in ("LONG", "SHORT"):
        return {
            "estado": "nacio",
            "cero": float(row["cero"]),
            "lado": str(row["lado"]),
            "callado": True,
            "anunciado": True,
        }
    corte = float(row.get("corte") or 0)
    if corte <= 0:
        return {"estado": "libre"}
    pta = float(row.get("puerta") or 0)
    if pta <= 0 and float(puerta or 0) > 0:
        pta = float(puerta)
    fant = Fantasma(corte, pta if pta > 0 else 0.0)
    fant.punta_alta = float(row.get("punta_alta") or corte)
    fant.punta_baja = float(row.get("punta_baja") or corte)
    fant.mando = str(row.get("mando") or "")
    fant.ver(float(precio or 0))
    row["puerta"] = fant.puerta if fant.puerta > 0 else pta
    row["punta_alta"] = fant.punta_alta
    row["punta_baja"] = fant.punta_baja
    row["mando"] = fant.mando
    if fant.despierto():
        row["cero"] = fant.cero
        row["lado"] = fant.lado
        doc[nombre] = row
        _guardar(doc)
        return {
            "estado": "nacio",
            "cero": fant.cero,
            "lado": fant.lado,
            "callado": bool(row.get("callado")),
            "anunciado": bool(row.get("anunciado")),
        }
    doc[nombre] = row
    _guardar(doc)
    return {
        "estado": "sigue",
        "callado": bool(row.get("callado")),
        "anunciado": bool(row.get("anunciado")),
    }


def marcar(santo: str, *, callado: bool = False, anunciado: bool = False) -> None:
    nombre = str(santo or "").strip().upper()
    doc = _leer()
    row = doc.get(nombre)
    if not isinstance(row, dict):
        return
    if callado:
        row["callado"] = True
    if anunciado:
        row["anunciado"] = True
    doc[nombre] = row
    _guardar(doc)


def olvidar(santo: str) -> None:
    """El cero ya es el wake. La hoja no vuelve a congelarlo."""
    nombre = str(santo or "").strip().upper()
    doc = _leer()
    if nombre not in doc:
        return
    doc.pop(nombre, None)
    _guardar(doc)
