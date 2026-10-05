"""Cuota de sala en papel.

Tres puertas sobre el mismo precio. Dos ventanas de tres días.
La sala más lejos se sostiene si todavía toca al menos dos tercios
de la puerta de hoy. Si la puerta de hoy casi no tocó, esa ventana calla.
Nadie cambia de color. No despierta campamentos.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import sys
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["BERU_RANGO_SALA_POR_COLOR"] = "1"
os.environ["BERU_RANGO_PERFIL"] = "normal"
os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
os.environ["BERU_RANGO_RED_EXPANSIVA_MAX_ESCALONES"] = "15"
os.environ["BERU_RANGO_BITACORA"] = "0"

from core import config  # noqa: E402
from generales.beru_rango import BeruRango  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAMPOS = ROOT / "data" / "beru" / "rango" / "vigilante_flota" / "campamentos.json"
SALIDA = ROOT / "data" / "beru" / "sala_cuota" / "primera_ventana.json"

DIAS = 3
BAR = "5m"
PASO_MS = 5 * 60 * 1000
PISO = 3  # menos de un toque al día: la ventana no vota
DOS_TERCIOS = 2.0 / 3.0
COLORES = ("verde", "amarillo", "rojo")


class _Mudo:
    async def anotar(self, *_a, **_k):
        return None


class _Tanque:
    def __init__(self) -> None:
        self.precios: dict[str, float] = {}


def santos() -> list[str]:
    doc = json.loads(CAMPOS.read_text(encoding="utf-8"))
    out: list[str] = []
    vistos: set[str] = set()
    for camp in doc.get("campamentos") or []:
        for s in camp.get("santos") or []:
            n = str(s or "").strip().upper()
            if n and n not in vistos:
                vistos.add(n)
                out.append(n)
    return out


def _pedir(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "sala-cuota"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _guardar(sueltas: dict, rows: list, desde_ms: int) -> int | None:
    menor = None
    for row in rows:
        ts = int(row[0])
        menor = ts if menor is None else min(menor, ts)
        if ts < desde_ms:
            continue
        sueltas[ts] = (float(row[1]), float(row[2]), float(row[3]), float(row[4]))
    return menor


def velas(activo: str, desde_ms: int) -> list[tuple[int, float, float, float, float]]:
    """Velas viejas → nuevas. Vacío si el santo no tiene puerta en la casa."""
    inst = f"{activo}-USDT-SWAP"
    sueltas: dict[int, tuple[float, float, float, float]] = {}
    after = ""
    for camino in ("candles", "history-candles"):
        tope = 8 if camino == "candles" else 24
        limite = 300 if camino == "candles" else 100
        for _ in range(tope):
            if sueltas and min(sueltas) <= desde_ms:
                break
            url = (
                f"https://www.okx.com/api/v5/market/{camino}"
                f"?instId={inst}&bar={BAR}&limit={limite}"
            )
            if after:
                url += f"&after={after}"
            try:
                doc = _pedir(url)
            except Exception:
                return []
            if str(doc.get("code")) != "0":
                return [] if not sueltas else [(ts, *sueltas[ts]) for ts in sorted(sueltas)]
            rows = doc.get("data") or []
            if not rows:
                break
            menor = _guardar(sueltas, rows, desde_ms)
            if menor is None or menor <= desde_ms:
                break
            after = str(menor)
            time.sleep(0.03)
        if sueltas and min(sueltas) <= desde_ms:
            break
    return [(ts, *sueltas[ts]) for ts in sorted(sueltas)]


def _pasos(o: float, h: float, l: float, c: float) -> list[float]:
    crudo = [o, l, h, c] if c >= o else [o, h, l, c]
    out: list[float] = []
    for px in crudo:
        if px > 0 and (not out or abs(out[-1] - px) > 1e-12):
            out.append(px)
    return out


async def toques(activo: str, color: str, filas: list[tuple]) -> int:
    config.BERU_RANGO_BITACORA = False
    g = BeruRango(object(), _Mudo(), _Tanque(), bridge=None)
    await g.despertar(float(filas[0][1]), activo=activo)
    if g.vivo is not None:
        g.vivo.puerta_ensayo = color
    n = 0
    for vela in filas:
        for px in _pasos(vela[1], vela[2], vela[3], vela[4]):
            if g.vivo is not None:
                g.vivo.puerta_ensayo = color
            r = await g.pulso(px)
            ev = str((r or {}).get("evento") or "")
            if ev.startswith("ARMAR_"):
                n += 1
    return n


def sentencia(conteo: dict[str, int]) -> str:
    hoy = int(conteo.get("verde") or 0)
    if hoy < PISO:
        return "calla"
    if int(conteo.get("rojo") or 0) + 1e-9 >= hoy * DOS_TERCIOS:
        return "rojo"
    if int(conteo.get("amarillo") or 0) + 1e-9 >= hoy * DOS_TERCIOS:
        return "amarillo"
    return "verde"


def partir(filas: list[tuple], ahora_ms: int) -> tuple[list, list]:
    corte = ahora_ms - DIAS * 86400 * 1000
    previa = [v for v in filas if v[0] < corte]
    reciente = [v for v in filas if v[0] >= corte]
    return previa, reciente


async def uno(activo: str, desde_ms: int, ahora_ms: int) -> dict:
    filas = await asyncio.to_thread(velas, activo, desde_ms)
    previa, reciente = partir(filas, ahora_ms)
    ventanas = {}
    for nombre, trozo in (("previa", previa), ("reciente", reciente)):
        if len(trozo) < 10:
            ventanas[nombre] = {"verde": 0, "amarillo": 0, "rojo": 0, "sala": "sin_precio"}
            continue
        conteo = {}
        for color in COLORES:
            conteo[color] = await toques(activo, color, trozo)
        conteo["sala"] = sentencia(conteo)
        ventanas[nombre] = conteo
    a = ventanas["previa"]["sala"]
    b = ventanas["reciente"]["sala"]
    if a == b and a in COLORES:
        firma = a
    else:
        firma = "espera"
    return {"santo": activo, "ventanas": ventanas, "firma": firma, "velas": len(filas)}


async def una_ventana(activo: str) -> dict:
    """Solo los tres días que acaban de pasar. La puerta del medio la decide el reloj."""
    ahora_ms = int(time.time() * 1000)
    desde_ms = ahora_ms - DIAS * 86400 * 1000 - PASO_MS
    filas = await asyncio.to_thread(velas, activo, desde_ms)
    corte = ahora_ms - DIAS * 86400 * 1000
    trozo = [v for v in filas if v[0] >= corte]
    if len(trozo) < 10:
        return {"santo": activo, "verde": 0, "amarillo": 0, "rojo": 0, "sala": "sin_precio"}
    conteo = {}
    for color in COLORES:
        conteo[color] = await toques(activo, color, trozo)
    conteo["sala"] = sentencia(conteo)
    conteo["santo"] = activo
    return conteo


async def main() -> None:
    nombres = santos()
    ahora_ms = int(time.time() * 1000)
    desde_ms = ahora_ms - (DIAS * 2) * 86400 * 1000 - PASO_MS
    hechos: list[dict] = []
    for i, nombre in enumerate(nombres, start=1):
        try:
            hechos.append(await uno(nombre, desde_ms, ahora_ms))
        except Exception as exc:
            hechos.append(
                {
                    "santo": nombre,
                    "ventanas": {},
                    "firma": "sin_precio",
                    "vela_error": str(exc)[:120],
                }
            )
        if i % 10 == 0 or i == len(nombres):
            print(f"mirados {i}/{len(nombres)}", flush=True)
    firmas: dict[str, int] = {}
    for row in hechos:
        k = str(row.get("firma") or "espera")
        firmas[k] = firmas.get(k, 0) + 1
    doc = {
        "cuando": time.strftime("%Y-%m-%d %H:%M:%S"),
        "nota": (
            "Papel. Dos ventanas de tres días. "
            "Firma solo si la misma sala sale dos veces. "
            "Nadie fue movido de color."
        ),
        "piso_toques": PISO,
        "mantiene_si": "dos tercios de la puerta de hoy",
        "firmas": firmas,
        "santos": hechos,
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FIRMAS", json.dumps(firmas, ensure_ascii=False), flush=True)
    print("SALIDA", SALIDA, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
