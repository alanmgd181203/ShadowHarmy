"""Compara el manto vivo con uno más histérico. No planta.

Recorre el cruce que el papel ya anotó. El de 250 es la ley de ahora.
El de 100 baja el peldaño y deja el primer asiento en 500 y el polvo en 250,
para no bailar en el borde. La reina de verdad es la tercera cuenta.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("IGRIS_ESCUDO_BTC_POLVO_USD", "250")

from core.igris_escudo_btc import neto_peldaño_atrasado

DIARIO = RAIZ / "data" / "beru" / "escudo" / "extasis_papel.jsonl"
RELACION = 1.6
GRANO = 10.0
ACTIVAR = 500.0


def _f(valor, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _muestras() -> list[dict]:
    filas = []
    ultima = None
    for linea in DIARIO.read_text(encoding="utf-8", errors="replace").splitlines():
        if not linea.strip():
            continue
        try:
            fila = json.loads(linea)
        except json.JSONDecodeError:
            continue
        reina = fila.get("reina_ahora")
        if reina is None:
            reina = ultima
        else:
            ultima = reina
        filas.append(
            {
                "ts": _f(fila.get("ts")),
                "hora": str(fila.get("hora") or ""),
                "cruzado": _f(fila.get("cruzado")),
                "reina": None if reina is None else _f(reina),
            }
        )
    return [f for f in filas if f["ts"] > 0]


def _grano(dolares: float) -> float:
    pasos = int(abs(dolares) / GRANO + 1e-9)
    metal = pasos * GRANO
    if dolares < 0:
        metal = -metal
    return float(metal)


def _camino(muestras: list[dict], peldaño: float) -> list[tuple[float, float]]:
    armado = False
    lado = ""
    asentado = None
    events = []
    for fila in muestras:
        asiento, armado, lado = neto_peldaño_atrasado(
            fila["cruzado"],
            peldaño=peldaño,
            activar=ACTIVAR,
            armado=armado,
            lado_armado=lado,
            asentado=asentado,
        )
        asentado = asiento if armado else None
        events.append((fila["ts"], _grano(asiento * RELACION)))
    return events


def _velas(desde_ms: int, hasta_ms: int) -> dict[int, float]:
    closes = {}
    cursor = hasta_ms + 60_000
    for _ in range(12):
        url = (
            "https://www.okx.com/api/v5/market/candles?instId=ETH-USD-SWAP"
            f"&bar=1m&after={cursor}&limit=300"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ShadowHarmy-ojo"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            dato = json.loads(resp.read().decode("utf-8"))
        filas = list(dato.get("data") or [])
        if not filas:
            break
        oldest = None
        for vela in filas:
            ts = int(vela[0])
            oldest = ts if oldest is None else min(oldest, ts)
            if desde_ms - 60_000 <= ts <= hasta_ms + 60_000:
                closes[ts] = float(vela[4])
        if oldest is None or oldest <= desde_ms or oldest >= cursor:
            break
        cursor = oldest
        time.sleep(0.15)
    return closes


def _tasa() -> float:
    """Tasa tomadora de la casa. Si no se ve, 0,05 %."""
    try:
        from core import okx_rest

        filas = okx_rest.get_private(
            "/api/v5/account/trade-fee",
            params={"instType": "SWAP"},
        )
        for fila in list(filas or []):
            if str(fila.get("instType") or "SWAP") != "SWAP":
                continue
            taker = abs(float(fila.get("taker") or 0))
            if taker > 0:
                return taker
    except Exception:
        pass
    return 0.0005


def _sostener(eventos: list[tuple[float, float]], momento: float) -> float:
    metal = 0.0
    for ts, valor in eventos:
        if ts > momento:
            break
        metal = valor
    return metal


def _precio_en(velas: list[tuple[int, float]], momento_ms: int) -> float:
    if not velas:
        return 0.0
    cercano = min(velas, key=lambda v: abs(v[0] - momento_ms))
    if abs(cercano[0] - momento_ms) > 120_000:
        return 0.0
    return cercano[1]


def _cuenta(eventos: list[tuple[float, float]], velas: list[tuple[int, float]], tasa: float) -> dict:
    pnl = 0.0
    fee = 0.0
    giros = 0.0
    veces = 0
    sosten = 0.0
    minutos = 0
    previo = None
    for ts, px in velas:
        metal = _sostener(eventos, ts / 1000.0)
        if previo is not None and previo > 0 and px > 0:
            # Inverso: el largo gana si el precio sube. El número va en la moneda.
            pnl += metal * (1.0 / previo - 1.0 / px)
            sosten += abs(metal)
            minutos += 1
        previo = px
    anterior = None
    for ts, metal in eventos:
        if anterior is None:
            anterior = metal
            continue
        if metal == anterior:
            continue
        delta = abs(metal - anterior)
        veces += 1
        giros += delta
        px = _precio_en(velas, int(ts * 1000))
        if px > 0:
            fee += tasa * delta / px
        anterior = metal
    peso = sosten / minutos if minutos else 0.0
    ultimo = velas[-1][1] if velas else 0.0
    return {
        "pnl_eth": pnl,
        "pnl_usd": pnl * ultimo,
        "fee_eth": fee,
        "fee_usd": fee * ultimo,
        "neto_usd": (pnl - fee) * ultimo,
        "giros": giros,
        "veces": veces,
        "peso": peso,
        "final": anterior if anterior is not None else 0.0,
    }


def main() -> None:
    muestras = _muestras()
    if len(muestras) < 10:
        print("sin camino")
        return
    desde = int(muestras[0]["ts"] * 1000)
    hasta = int(muestras[-1]["ts"] * 1000)
    closes = _velas(desde, hasta)
    velas = sorted(closes.items())
    tasa = _tasa()
    vivo = [(f["ts"], _grano(f["reina"])) for f in muestras if f["reina"] is not None]
    caminos = {
        "vivo": vivo,
        "p250": _camino(muestras, 250.0),
        "p100": _camino(muestras, 100.0),
    }
    print(
        "VENTANA",
        muestras[0]["hora"],
        "->",
        muestras[-1]["hora"],
        "muestras",
        len(muestras),
        "velas",
        len(velas),
        "tasa",
        tasa,
    )
    print(
        "CRUCE",
        muestras[0]["cruzado"],
        "->",
        muestras[-1]["cruzado"],
        "REINA",
        muestras[0]["reina"],
        "->",
        muestras[-1]["reina"],
    )
    for nombre, eventos in caminos.items():
        hecho = _cuenta(eventos, velas, tasa)
        print(
            nombre,
            "veces", round(hecho["veces"]),
            "giros", round(hecho["giros"]),
            "peso", round(hecho["peso"]),
            "final", round(hecho["final"]),
            "precio", round(hecho["pnl_usd"], 1),
            "comision", round(hecho["fee_usd"], 1),
            "neto", round(hecho["neto_usd"], 1),
        )


if __name__ == "__main__":
    main()
