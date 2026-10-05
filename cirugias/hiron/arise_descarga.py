# -*- coding: utf-8 -*-
"""Descarga viva. Solo normal y difícil.

La limpia no habla. Si el precio ya pasó el final, suelta lo que queda
una vez. Si todavía hay camino, este latido no cobra el tramo callado:
la próxima décima se reparte sobre lo que falta.
"""
from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cirugias.hiron.descarga import Descarga

RAIZ = Path(__file__).resolve().parents[2]
LIBRO = RAIZ / "data" / "beru" / "papel" / "iron_memoria.json"
ESTADO = RAIZ / "data" / "beru" / "papel" / "descarga_estado.json"
PAUSA = 20


def _f(valor, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _ultimo() -> dict:
    try:
        data = json.loads(LIBRO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    ultimo = {}
    if not isinstance(data, dict):
        return ultimo
    for clave, fila in data.items():
        if not isinstance(fila, dict):
            continue
        nombre, _, ts = str(clave).partition(":")
        try:
            cuando = int(ts or 0)
        except ValueError:
            cuando = 0
        prev = ultimo.get(nombre)
        if prev is None or cuando >= prev[0]:
            ultimo[nombre] = (cuando, fila)
    return ultimo


def _estado() -> dict:
    try:
        data = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _guardar(dato: dict) -> None:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    temporal = ESTADO.with_suffix(".tmp")
    temporal.write_text(json.dumps(dato, ensure_ascii=True), encoding="ascii")
    temporal.replace(ESTADO)


def _paso(lado: str, marca: float, fin: float) -> bool:
    if lado == "LONG":
        return marca >= fin - 1e-12
    return marca <= fin + 1e-12


def _cerrar(okx, inst: str, lado: str, contratos: float) -> str:
    sz = f"{contratos:.8f}".rstrip("0").rstrip(".")
    cuerpo = {
        "instId": inst,
        "tdMode": "cross",
        "side": "buy" if lado == "SHORT" else "sell",
        "ordType": "market",
        "sz": sz,
        "reduceOnly": True,
        "clOrdId": ("DES" + uuid.uuid4().hex[:16])[:32],
    }
    data = okx.post_private("/api/v5/trade/order", cuerpo)
    fila = (list(data or [{}]) or [{}])[0]
    if str((fila or {}).get("sCode") or "0") not in ("0", ""):
        return ""
    return str((fila or {}).get("ordId") or "ok")


def _mirar_ahora(activo: str, lado: str, suelo: float) -> str | None:
    """La clase del camino ya visto. No sella y no manda orden."""
    from cirugias.hiron.arise_papel import _color, _mechas
    from cirugias.hiron.subida import Subida

    ruta = RAIZ / "data" / "beru" / "rango" / activo / "manos_piedra_eventos.jsonl"
    if suelo <= 0 or not ruta.is_file():
        return None
    ancla = None
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        if "OZ_COSECHA" not in linea:
            continue
        try:
            row = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if row.get("evento") != "OZ_COSECHA":
            continue
        det = row.get("detalle") or {}
        if str(det.get("dir") or "").upper() != lado:
            continue
        px = _f(det.get("fill"))
        ts = _f(row.get("ts"))
        if px <= 0 or ts <= 0:
            continue
        if lado == "SHORT" and px <= suelo:
            continue
        if lado == "LONG" and px >= suelo:
            continue
        if ancla is None or ts >= ancla[0]:
            ancla = (ts, px)
    if ancla is None:
        return None
    try:
        camino = _mechas(f"{activo}-USDT-SWAP", int(ancla[0] * 1000), int(time.time() * 1000))
    except Exception:
        return None
    subida = Subida(_color(activo), lado)
    subida.anclar_oz(ancla[1])
    subida.anclar_meta(suelo)
    for paso in camino:
        subida.ver(paso)
    return subida.ahora()


def _anotar_sin_clase(okx, estado: dict, candidatas: list[dict]) -> None:
    """Una bolsa por latido. Si todavía camina, no cobra el tramo callado."""
    if not candidatas:
        return
    turno = int(_f(estado.get("_turno")))
    estado["_turno"] = turno + 1
    fila = candidatas[turno % len(candidatas)]
    clave = fila["clave"]
    ya = estado.get(clave) if isinstance(estado.get(clave), dict) else {}
    if time.time() - _f(ya.get("mirada")) < 900:
        _guardar(estado)
        return
    clase = _mirar_ahora(fila["nombre"], fila["lado"], fila["suelo"])
    nota = {"mirada": time.time(), "precio": _f(ya.get("precio")), "vacia": False}
    if clase not in ("normal", "dificil"):
        estado[clave] = nota
        _guardar(estado)
        print(f"{fila['nombre']} sigue limpia o calla", flush=True)
        return
    d = Descarga(fila["lado"], clase, fila["promedio"], fila["suelo"])
    if not d.habla or d.fin() is None or _paso(fila["lado"], fila["marca"], float(d.fin())):
        estado[clave] = nota
        _guardar(estado)
        print(f"{fila['nombre']} todavia no, sin vaciar", flush=True)
        return
    if _f(nota.get("precio")) <= 0:
        nota["precio"] = fila["marca"]
        estado[clave] = nota
        _guardar(estado)
        print(f"{fila['nombre']} {clase}, en camino, no cobra el tramo callado", flush=True)
        return
    masa = fila["usd"]
    sol = d.soltar(_f(nota["precio"]), fila["marca"], masa)
    nota["precio"] = fila["marca"]
    estado[clave] = nota
    _guardar(estado)
    if not sol or sol <= 1.0:
        return
    ct = fila["ct"]
    lot = fila["lot"]
    if ct <= 0 or lot <= 0:
        pub = okx.get_public(
            "/api/v5/public/instruments",
            params={"instType": "SWAP", "instId": fila["inst"]},
        ) or []
        ins = pub[0] if pub else {}
        ct = _f(ins.get("ctVal"))
        lot = _f(ins.get("lotSz"))
    pos = fila["pos"]
    if ct <= 0 or lot <= 0 or fila["marca"] <= 0:
        return
    monedas = min(abs(pos) * ct, sol / fila["marca"])
    pasos = int((monedas / ct) / lot + 1e-9)
    contratos = pasos * lot
    if contratos <= 0 or contratos > abs(pos) + 1e-9:
        return
    orden = _cerrar(okx, fila["inst"], fila["lado"], contratos)
    if orden:
        print(f"{fila['nombre']} suelta {sol:.0f}", flush=True)


def latido() -> None:
    from core import okx_rest

    cfg = okx_rest.get_private("/api/v5/account/config") or []
    if str((list(cfg) or [{}])[0].get("posMode") or "") != "net_mode":
        print("sin neto", flush=True)
        return
    estado = _estado()
    ultimo = _ultimo()
    filas = okx_rest.get_private("/api/v5/account/positions", params={"instType": "SWAP"}) or []
    candidatas: list[dict] = []
    for fila in filas:
        if not isinstance(fila, dict):
            continue
        inst = str(fila.get("instId") or "")
        if not inst.endswith("-USDT-SWAP"):
            continue
        nombre = inst.split("-")[0]
        previo = ultimo.get(nombre)
        if previo is None:
            continue
        nace_libro, nota = previo
        clase = str(nota.get("clase") or "")
        if clase not in ("normal", "dificil"):
            suelo = _f(nota.get("suelo"))
            try:
                nace = int(float(fila.get("cTime") or 0))
            except (TypeError, ValueError):
                continue
            pos = _f(fila.get("pos"))
            if suelo > 0 and nace == nace_libro and pos != 0 and str(fila.get("mgnMode") or "") == "cross":
                candidatas.append({
                    "nombre": nombre,
                    "lado": "SHORT" if pos < 0 else "LONG",
                    "suelo": suelo,
                    "marca": _f(fila.get("markPx")),
                    "promedio": _f(fila.get("avgPx")),
                    "usd": abs(_f(fila.get("notionalUsd"))),
                    "pos": pos,
                    "inst": inst,
                    "ct": 0.0,
                    "lot": 0.0,
                    "clave": f"{nombre}:{nace}",
                })
            continue
        try:
            nace = int(float(fila.get("cTime") or 0))
        except (TypeError, ValueError):
            continue
        if nace != nace_libro:
            continue
        pos = _f(fila.get("pos"))
        if pos == 0 or str(fila.get("mgnMode") or "") != "cross":
            continue
        lado = "SHORT" if pos < 0 else "LONG"
        marca = _f(fila.get("markPx"))
        promedio = _f(fila.get("avgPx"))
        suelo = _f(nota.get("suelo"))
        d = Descarga(lado, clase, promedio, suelo)
        if not d.habla or d.fin() is None or marca <= 0:
            continue
        clave = f"{nombre}:{nace}"
        ya = estado.get(clave) if isinstance(estado.get(clave), dict) else {}
        if ya.get("vacia"):
            continue
        pub = okx_rest.get_public(
            "/api/v5/public/instruments",
            params={"instType": "SWAP", "instId": inst},
        ) or []
        ins = pub[0] if pub else {}
        ct = _f(ins.get("ctVal"))
        lot = _f(ins.get("lotSz"))
        if ct <= 0 or lot <= 0:
            continue
        if _paso(lado, marca, float(d.fin())):
            pasos = int((abs(pos) / lot) + 1e-9)
            contratos = pasos * lot
            if contratos <= 0 or contratos > abs(pos) + 1e-9:
                continue
            orden = _cerrar(okx_rest, inst, lado, contratos)
            if not orden:
                print(f"{nombre} no salio", flush=True)
                continue
            estado[clave] = {"vacia": True, "orden": orden}
            _guardar(estado)
            print(f"{nombre} suelta lo que quedaba", flush=True)
            continue
        visto = _f(ya.get("precio"))
        if visto <= 0:
            estado[clave] = {"vacia": False, "precio": marca}
            _guardar(estado)
            print(f"{nombre} en camino, no cobra el tramo callado", flush=True)
            continue
        masa = abs(_f(fila.get("notionalUsd")))
        sol = d.soltar(visto, marca, masa)
        estado[clave] = {"vacia": False, "precio": marca}
        _guardar(estado)
        if not sol or sol <= 1.0:
            continue
        monedas = min(abs(pos) * ct, sol / marca) if marca > 0 else 0.0
        pasos = int((monedas / ct) / lot + 1e-9)
        contratos = pasos * lot
        if contratos <= 0 or contratos > abs(pos) + 1e-9:
            continue
        orden = _cerrar(okx_rest, inst, lado, contratos)
        if orden:
            print(f"{nombre} suelta {sol:.0f}", flush=True)
    _anotar_sin_clase(okx_rest, estado, candidatas)


def main() -> None:
    while True:
        try:
            latido()
        except Exception as exc:
            print(f"latido {exc}", flush=True)
        time.sleep(PAUSA)


if __name__ == "__main__":
    main()
