"""Reloj de la puerta. Cada tres días el propio ejército cuenta y mueve.

La sala cambia solo si la misma sentencia sale dos veces seguidas.
Si la ventana casi no tocó, no vota y no mueve a nadie.
La masa no se toca. La caza ya abierta no se reescribe.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cirugias.sala_por_color.contar_cuota import COLORES, santos, una_ventana

DIR = ROOT / "data" / "beru" / "sala_cuota"
PUERTA = DIR / "puerta.json"
RELOJ = DIR / "reloj.json"
DIARIO = DIR / "diario.jsonl"
CANDADO = DIR / "reloj.lock"
TRES_DIAS = 3 * 86400
REINTENTO = 6 * 3600
MINIMO_VOTOS = 150


def _leer(path: Path, vacio: dict) -> dict:
    if not path.exists():
        return dict(vacio)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(vacio)
    return data if isinstance(data, dict) else dict(vacio)


def _guardar(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def decidir(
    ultima: dict[str, str],
    nueva: dict[str, str],
    amarillo: set[str],
    rojo: set[str],
) -> tuple[dict[str, str], set[str], set[str], list[str]]:
    """Dos sentencias iguales mueven la puerta. Una ventana muda no cuenta."""
    cambios: list[str] = []
    for santo, sala in nueva.items():
        if sala not in COLORES:
            continue
        previa = ultima.get(santo)
        ultima[santo] = sala
        if previa != sala:
            continue
        antes = "rojo" if santo in rojo else "amarillo" if santo in amarillo else "verde"
        if sala == antes:
            continue
        rojo.discard(santo)
        amarillo.discard(santo)
        if sala == "rojo":
            rojo.add(santo)
        elif sala == "amarillo":
            amarillo.add(santo)
        cambios.append(f"{santo} {antes}->{sala}")
    return ultima, amarillo, rojo, cambios


async def medir() -> list[dict]:
    hechos: list[dict] = []
    nombres = santos()
    for i, nombre in enumerate(nombres, start=1):
        try:
            hechos.append(await una_ventana(nombre))
        except Exception as exc:
            hechos.append({"santo": nombre, "sala": "sin_precio", "error": str(exc)[:120]})
        if i % 20 == 0 or i == len(nombres):
            print(f"mirados {i}/{len(nombres)}", flush=True)
    return hechos


def pasar(hechos: list[dict]) -> str:
    votos = [h for h in hechos if str(h.get("sala")) in COLORES]
    if len(votos) < MINIMO_VOTOS:
        estado = _leer(RELOJ, {})
        estado["proximo"] = time.time() + REINTENTO
        estado["nota"] = "la ventana no alcanzó a votar; no se mueve a nadie"
        _guardar(RELOJ, estado)
        return f"calla votos={len(votos)}"

    estado = _leer(RELOJ, {})
    ultima = {
        str(k).upper(): str(v)
        for k, v in (estado.get("ultima") or {}).items()
        if str(v) in COLORES
    }
    nueva = {str(h["santo"]).upper(): str(h["sala"]) for h in votos}
    puerta = _leer(PUERTA, {"amarillo": [], "rojo": []})
    amarillo = {str(s).upper() for s in (puerta.get("amarillo") or [])}
    rojo = {str(s).upper() for s in (puerta.get("rojo") or [])}
    ultima, amarillo, rojo, cambios = decidir(ultima, nueva, amarillo, rojo)
    puerta["amarillo"] = sorted(amarillo)
    puerta["rojo"] = sorted(rojo)
    puerta["nota"] = (
        "El reloj mueve la puerta si la misma sala sale dos veces. "
        "Quien no está en la lista se queda en la de hoy. La masa no se toca."
    )
    puerta["contado"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _guardar(PUERTA, puerta)
    estado["ultima"] = ultima
    estado["proximo"] = time.time() + TRES_DIAS
    estado["cuando"] = puerta["contado"]
    estado["nota"] = "siguiente cuenta en tres días"
    _guardar(RELOJ, estado)
    linea = {
        "cuando": puerta["contado"],
        "votos": len(votos),
        "cambios": cambios,
    }
    with DIARIO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    return f"listo cambios={len(cambios)} " + ", ".join(cambios[:12])


def main() -> None:
    """Una mirada. Si aún no cumplió tres días, se va. La casa lo llama cada día."""
    DIR.mkdir(parents=True, exist_ok=True)
    if CANDADO.exists() and time.time() - CANDADO.stat().st_mtime < 4 * 3600:
        print("ya cuenta", flush=True)
        return
    estado = _leer(RELOJ, {})
    proximo = float(estado.get("proximo") or 0)
    if proximo <= 0:
        estado["proximo"] = time.time() + TRES_DIAS
        estado["nota"] = "primera espera de tres días"
        _guardar(RELOJ, estado)
        print("primera espera", flush=True)
        return
    if time.time() + 30 < proximo:
        print(
            "todavia no, hasta "
            + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(proximo)),
            flush=True,
        )
        return
    CANDADO.write_text(str(time.time()), encoding="utf-8")
    try:
        print("cuenta", flush=True)
        print(pasar(asyncio.run(medir())), flush=True)
    finally:
        CANDADO.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
