"""Sombra del manto. No planta y no escribe el sello.

Recorre la masa que el papel ya anotó. Cada hora se viste con la ley
que estaba viva entonces. El precio, el peaje y el funding salen aparte,
para cotejarlos con la boleta de la reina.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("BERU_MAR", "okx")
os.environ.setdefault("IGRIS_ESCUDO_BTC_POLVO_USD", "250")
os.environ.setdefault("IGRIS_ESCUDO_BTC_ACTIVAR_USD", "500")
os.environ.setdefault("IGRIS_ESCUDO_BTC_PELDANO_USD", "250")

from core.igris_escudo_btc import neto_peldaño_atrasado
from cirugias.escudo_dual.comparar_histerico import _cuenta, _grano, _muestras, _tasa
from cirugias.escudo_dual.elegir import _parte_baja

TZ = timezone(timedelta(hours=-6))
# Reinicios reales del escudo. Cada uno olvida el asiento en memoria.
CIRUGIA = datetime(2026, 9, 29, 15, 6, tzinfo=TZ)
PUERTA = datetime(2026, 10, 1, 13, 13, tzinfo=TZ)
TAJO = datetime(2026, 10, 1, 13, 22, tzinfo=TZ)
INDICADOR = 1.6


def _ley(ts: float) -> str:
    if ts < CIRUGIA.timestamp():
        return "llena"
    if ts < PUERTA.timestamp():
        return "banda"
    if ts < TAJO.timestamp():
        return "puerta"
    return "tajo"


def _asiento(neto: float, estado: dict, abre: float, cierra: float) -> float:
    """La banda de esa hora. No toca el sello vivo."""
    n = float(neto or 0)
    if not estado["armado"]:
        if abs(n) < abre:
            estado["lado"] = ""
            estado["valor"] = 0.0
            return 0.0
        asiento, sigo, lado = neto_peldaño_atrasado(
            n, armado=False, lado_armado="", asentado=None,
        )
    else:
        asiento, sigo, lado = neto_peldaño_atrasado(
            n,
            armado=True,
            lado_armado=estado["lado"],
            asentado=estado["valor"],
        )
        if (not sigo) or abs(n) <= cierra:
            asiento, sigo, lado = 0.0, False, ""
    estado["armado"] = bool(sigo)
    estado["lado"] = lado if sigo else ""
    estado["valor"] = float(asiento) if sigo else 0.0
    return float(asiento)


def _parte_vieja(asiento: float, calma: float, alerta: float) -> float:
    a = abs(float(asiento or 0))
    if a <= 0:
        return 0.5
    if a <= calma:
        return 0.5
    if a <= alerta:
        return 0.75
    return 1.0


def camino_ley(muestras: list[dict]) -> list[tuple[float, float]]:
    """Metal de la reina según la ley de cada hora. Un evento por cambio."""
    estado = {"armado": False, "lado": "", "valor": 0.0}
    parte = None
    ley_previa = ""
    ultimo = None
    out: list[tuple[float, float]] = []
    for fila in muestras:
        ts = float(fila["ts"])
        ley = _ley(ts)
        if ley != ley_previa:
            estado = {"armado": False, "lado": "", "valor": 0.0}
            parte = None
            ley_previa = ley
        n = float(fila["cruzado"])
        if ley == "llena":
            asiento, sigo, lado = neto_peldaño_atrasado(
                n,
                armado=estado["armado"],
                lado_armado=estado["lado"],
                asentado=estado["valor"] if estado["armado"] else None,
            )
            estado["armado"] = bool(sigo)
            estado["lado"] = lado if sigo else ""
            estado["valor"] = float(asiento) if sigo else 0.0
            metal = _grano(float(asiento) * INDICADOR)
        else:
            if ley == "banda":
                asiento = _asiento(n, estado, 2500.0, 1000.0)
                parte = _parte_vieja(asiento, 6000.0, 12000.0)
            elif ley == "puerta":
                asiento = _asiento(n, estado, 5000.0, 1000.0)
                parte = _parte_vieja(asiento, 8000.0, 12000.0)
            else:
                asiento = _asiento(n, estado, 5000.0, 2500.0)
                parte = _parte_baja(asiento, parte)
            metal = 0.0 if asiento == 0 else _grano(float(asiento) * parte * INDICADOR)
        if ultimo is None or metal != ultimo[1]:
            out.append((ts, metal))
            ultimo = (ts, metal)
    return out


def camino_vivida(muestras: list[dict]) -> list[tuple[float, float]]:
    """Lo que la reina tenía puesto, anotado en el papel."""
    ultimo = None
    out: list[tuple[float, float]] = []
    for fila in muestras:
        if fila["reina"] is None:
            continue
        metal = _grano(float(fila["reina"]))
        ts = float(fila["ts"])
        if ultimo is None or metal != ultimo:
            out.append((ts, metal))
            ultimo = metal
    return out


def _velas(desde_ms: int, hasta_ms: int) -> dict[int, float]:
    closes: dict[int, float] = {}
    cursor = hasta_ms + 60_000
    for _ in range(40):
        url = (
            "https://www.okx.com/api/v5/market/history-candles?instId=ETH-USD-SWAP"
            f"&bar=1m&after={cursor}&limit=300"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ShadowHarmy-ojo"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                dato = json.loads(resp.read().decode("utf-8"))
        except Exception:
            break
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
        time.sleep(0.12)
    return closes


def _boleta(desde_ms: int) -> dict:
    from core import okx_rest

    def f(valor) -> float:
        try:
            return float(valor or 0)
        except (TypeError, ValueError):
            return 0.0

    filas: list[dict] = []
    after = ""
    for _ in range(30):
        params: dict = {"ccy": "ETH", "limit": "100"}
        if after:
            params["after"] = after
        batch = list(okx_rest.get_private("/api/v5/account/bills", params=params) or [])
        if not batch:
            break
        filas.extend(batch)
        after = str(batch[-1].get("billId") or "")
        oldest = min(int(b.get("ts") or 0) for b in batch)
        if oldest < desde_ms or len(batch) < 100 or not after:
            break
    precio = 0.0
    peaje = 0.0
    funding = 0.0
    interes = 0.0
    n = 0
    for b in filas:
        if int(b.get("ts") or 0) < desde_ms:
            continue
        if str(b.get("instId") or "") != "ETH-USD-SWAP":
            continue
        n += 1
        tipo = str(b.get("type") or "")
        if tipo == "2":
            precio += f(b.get("pnl"))
            peaje += f(b.get("fee"))
        elif tipo == "8":
            funding += f(b.get("balChg"))
        elif tipo == "7":
            interes += f(b.get("balChg"))
    aire = 0.0
    for p in list(okx_rest.get_private(
        "/api/v5/account/positions", params={"instId": "ETH-USD-SWAP"},
    ) or []):
        if abs(f(p.get("pos"))) < 1e-12:
            continue
        aire += f(p.get("upl"))
    return {
        "n": n,
        "precio_eth": precio,
        "peaje_eth": peaje,
        "funding_eth": funding,
        "interes_eth": interes,
        "aire_eth": aire,
    }


def _linea(nombre: str, hecho: dict, px: float) -> None:
    print(
        f"{nombre} precio {hecho['pnl_usd']:.1f} peaje {hecho['fee_usd']:.1f} "
        f"neto {hecho['neto_usd']:.1f} veces {round(hecho['veces'])} "
        f"final {round(hecho['final'])} eth_precio {hecho['pnl_eth']:.6f}",
        flush=True,
    )
    del px


def main() -> None:
    muestras = _muestras()
    if len(muestras) < 5:
        print("sin camino", flush=True)
        return
    desde = int(muestras[0]["ts"] * 1000)
    hasta = int(muestras[-1]["ts"] * 1000)
    print(
        "CAMINO",
        datetime.fromtimestamp(muestras[0]["ts"], TZ).strftime("%m-%d %H:%M"),
        "->",
        datetime.fromtimestamp(muestras[-1]["ts"], TZ).strftime("%m-%d %H:%M"),
        "n",
        len(muestras),
        flush=True,
    )
    ley = camino_ley(muestras)
    viva = camino_vivida(muestras)
    closes = _velas(desde, hasta)
    velas = sorted(closes.items())
    print("VELAS", len(velas), flush=True)
    if len(velas) < 10:
        print("sin velas", flush=True)
        return
    tasa = _tasa()
    px = velas[-1][1]
    corta = velas[0][0] / 1000.0
    print("VELA_DESDE", datetime.fromtimestamp(corta, TZ).strftime("%m-%d %H:%M"), "TASA", tasa, flush=True)
    ley_c = [(t, m) for t, m in ley if t >= corta - 60]
    viva_c = [(t, m) for t, m in viva if t >= corta - 60]
    _linea("LEY", _cuenta(ley_c, velas, tasa), px)
    _linea("VIVA", _cuenta(viva_c, velas, tasa), px)
    boleta = _boleta(int(corta * 1000))
    print(
        "BOLETA filas {n} precio_eth {precio_eth:.6f} peaje_eth {peaje_eth:.6f} "
        "funding_eth {funding_eth:.6f} interes_eth {interes_eth:.6f} aire_eth {aire_eth:.6f}".format(**boleta),
        flush=True,
    )
    print(
        "BOLETA_USD precio {0:.1f} peaje {1:.1f} funding {2:.1f} aire {3:.1f} "
        "precio_mas_aire {4:.1f}".format(
            boleta["precio_eth"] * px,
            boleta["peaje_eth"] * px,
            boleta["funding_eth"] * px,
            boleta["aire_eth"] * px,
            (boleta["precio_eth"] + boleta["aire_eth"]) * px,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
