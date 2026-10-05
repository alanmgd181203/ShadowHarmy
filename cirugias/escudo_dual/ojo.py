"""El ojo de los dos metales. No planta capa.

El permiso es el tramo reciente, de quince minutos.
La relación de aquí es solo esa misma ventana: no es la lenta.
Si no hay datos, calla. No inventa un uno.
"""
from __future__ import annotations

import json
import time
import urllib.request

from cirugias.escudo_dual.permiso import conceder, mirar
from cirugias.escudo_dual.relaciones import las_dos

REY = "BTC-USD-SWAP"
REINA = "ETH-USD-SWAP"
MAREA = (
    "SOL-USDT-SWAP",
    "XRP-USDT-SWAP",
    "DOGE-USDT-SWAP",
    "LINK-USDT-SWAP",
    "AVAX-USDT-SWAP",
    "ADA-USDT-SWAP",
    "NEAR-USDT-SWAP",
    "LTC-USDT-SWAP",
)
_CACHE: dict = {"ts": 0.0, "dato": None}
_ULTIMOS: dict[str, float] = {}


def ver() -> dict:
    """Quién acompañó. No manda orden."""
    ahora = time.time()
    if _CACHE["dato"] is not None and ahora - float(_CACHE["ts"]) < 60:
        return dict(_CACHE["dato"])
    rey = _cierres(REY)
    reina = _cierres(REINA)
    marea = _marea()
    visto_rey = mirar(marea, rey)
    visto_reina = mirar(marea, reina)
    dato = {
        "permiso_rey": conceder(visto_rey),
        "permiso_reina": conceder(visto_reina),
        "relaciones": las_dos(marea, rey, reina),
        "marcas": len(marea),
        "nivel": marea[-1] if marea else None,
        "ultimos": dict(_ULTIMOS),
    }
    _CACHE["ts"] = ahora
    _CACHE["dato"] = dato
    return dict(dato)


def frase(dato: dict) -> str:
    """Una línea. No elige capa si la relación es la corta."""
    rey = _palabra(dato.get("permiso_rey"))
    reina = _palabra(dato.get("permiso_reina"))
    return f"rey {rey} · reina {reina} · sin capa"


def _palabra(permiso: bool | None) -> str:
    if permiso is True:
        return "acompaña"
    if permiso is False:
        return "no acompaña"
    return "calla"


def _marea() -> list[float]:
    series = []
    _ULTIMOS.clear()
    for inst in MAREA:
        cierres = _cierres(inst)
        if len(cierres) < 2:
            continue
        series.append(cierres)
        _ULTIMOS[inst.split("-")[0]] = cierres[-1]
    if len(series) < 3:
        return []
    n = min(len(c) for c in series)
    series = [c[-n:] for c in series]
    indice = [100.0]
    for i in range(1, n):
        saltos = []
        for serie in series:
            antes = serie[i - 1]
            ahora = serie[i]
            if antes > 0 and ahora > 0:
                saltos.append((ahora / antes) - 1.0)
        if not saltos:
            indice.append(indice[-1])
        else:
            indice.append(indice[-1] * (1.0 + sum(saltos) / len(saltos)))
    return indice


def _cierres(inst: str) -> list[float]:
    url = (
        "https://www.okx.com/api/v5/market/candles"
        f"?instId={inst}&bar=1m&limit=16"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ShadowHarmy-ojo"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    filas = list(data.get("data") or [])
    filas.reverse()
    out = []
    for fila in filas:
        try:
            px = float(fila[4])
        except (TypeError, ValueError, IndexError):
            continue
        if px > 0:
            out.append(px)
    return out
