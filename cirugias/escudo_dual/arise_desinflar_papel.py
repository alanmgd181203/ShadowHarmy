"""Papel de las otras recetas del desinflador. No planta.

La receta viva sigue siendo la del manto. Aquí se apuntan las demás,
las dos casas, para ver más adelante cuál pierde menos.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from cirugias.escudo_dual.desinflar import paso, precio, total_del_mercado
from core import beru_rango_paths

DIR = RAIZ / "data" / "beru" / "escudo"
DIARIO = DIR / "extasis_papel.jsonl"
CRIPTO = DIR / "desinflar_papel_cripto.csv"
BOLSA = DIR / "desinflar_papel_bolsa.csv"
INFORME = DIR / "desinflar_papel.json"
INDICADOR = 1.6
GRANO = 10.0
TASA = 0.0005
UMBRALES = (0.01, 0.02, 0.05, 0.10)
PISOS = (0.50, 0.30, 0.10, 0.0)
FORMAS = ("lenta", "media", "rapida")
MIRADAS = {
    "bolsa": (),
    "total": ("total",),
    "rey": ("rey",),
    "reina": ("reina",),
    "total_rey": ("total", "rey"),
    "total_reina": ("total", "reina"),
    "rey_reina": ("rey", "reina"),
    "tres": ("total", "rey", "reina"),
}
VIVA = {"adelgazo": 0.10, "piso": 0.0, "forma": "lenta", "mirada": "total_reina"}


def _grano(dolares: float) -> float:
    pasos = int(abs(dolares) / GRANO + 1e-9)
    metal = pasos * GRANO
    return -metal if dolares < 0 else float(metal)


def _velas(inst: str, desde_s: int, hasta_s: int) -> list[tuple[int, float]]:
    closes: dict[int, float] = {}
    cursor = hasta_s * 1000 + 60_000
    desde_ms = desde_s * 1000
    for _ in range(24):
        url = (
            "https://www.okx.com/api/v5/market/history-candles"
            f"?instId={inst}&bar=1m&after={cursor}&limit=300"
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
            if desde_ms - 120_000 <= ts <= hasta_s * 1000 + 120_000:
                closes[ts // 1000] = float(vela[4])
        if oldest is None or oldest <= desde_ms or oldest >= cursor:
            break
        cursor = oldest
        time.sleep(0.12)
    return sorted(closes.items())


def _totales(desde_s: int, hasta_s: int) -> list[tuple[int, float]]:
    url = (
        "https://api.coinmarketcap.com/data-api/v3/global-metrics/quotes/historical"
        f"?convert=USD&format=chart&interval=1h&timeStart={desde_s - 7200}&timeEnd={hasta_s + 3600}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        dato = json.loads(resp.read().decode("utf-8"))
    out = []
    for punto in (dato.get("data") or {}).get("quotes") or []:
        momento = int(
            datetime.fromisoformat(str(punto.get("timestamp")).replace("Z", "+00:00")).timestamp()
        )
        total = float(((punto.get("quote") or [{}])[0]).get("totalMarketCap") or 0)
        if total > 0:
            out.append((momento, total))
    return sorted(out)


def _en(serie: list[tuple[int, float]], momento: int, holgura: int) -> float:
    lo, hi, elegido = 0, len(serie) - 1, -1
    while serie and lo <= hi:
        mid = (lo + hi) // 2
        if serie[mid][0] <= momento:
            elegido = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if elegido < 0 or momento - serie[elegido][0] > holgura:
        return 0.0
    return serie[elegido][1]


def _sembrar_cripto() -> None:
    if CRIPTO.exists() and CRIPTO.stat().st_size > 40:
        return
    filas = []
    ultimo = -1
    if not DIARIO.exists():
        return
    for linea in DIARIO.read_text(encoding="utf-8", errors="replace").splitlines():
        if not linea.strip():
            continue
        try:
            fila = json.loads(linea)
        except json.JSONDecodeError:
            continue
        ts = int(float(fila.get("ts") or 0))
        minuto = ts // 60
        if ts <= 0 or minuto == ultimo:
            continue
        ultimo = minuto
        filas.append((ts, float(fila.get("cruzado") or 0)))
    if len(filas) < 5:
        return
    eth = _velas("ETH-USD-SWAP", filas[0][0], filas[-1][0])
    btc = _velas("BTC-USD-SWAP", filas[0][0], filas[-1][0])
    total = _totales(filas[0][0], filas[-1][0])
    DIR.mkdir(parents=True, exist_ok=True)
    with CRIPTO.open("w", encoding="utf-8") as fh:
        fh.write("ts,cruzado,reina,rey,total\n")
        for ts, cruzado in filas:
            fh.write(
                f"{ts},{cruzado:.1f},{_en(eth, ts, 180):.4f},"
                f"{_en(btc, ts, 180):.2f},{_en(total, ts, 5400):.0f}\n"
            )
    print(f"[PAPEL] semilla cripto {len(filas)}", flush=True)


def _ultimo_ts(path: Path) -> int:
    if not path.exists():
        return 0
    ultima = ""
    with path.open(encoding="utf-8", errors="replace") as fh:
        for linea in fh:
            if linea.strip() and not linea.startswith("ts,"):
                ultima = linea
    if not ultima:
        return 0
    try:
        return int(ultima.split(",")[0])
    except ValueError:
        return 0


def _cruzado_diario() -> tuple[int, float] | None:
    if not DIARIO.exists():
        return None
    ultima = ""
    with DIARIO.open(encoding="utf-8", errors="replace") as fh:
        for linea in fh:
            if linea.strip():
                ultima = linea
    if not ultima:
        return None
    try:
        fila = json.loads(ultima)
    except json.JSONDecodeError:
        return None
    ts = int(float(fila.get("ts") or 0))
    if ts <= 0:
        return None
    return ts, float(fila.get("cruzado") or 0)


def _cruzado_bolsa() -> float | None:
    path = beru_rango_paths.RANGO_DIR / "balanza_bolsa.json"
    try:
        dato = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    return float(dato.get("short_usd") or 0) - float(dato.get("long_usd") or 0)


def _anotar(path: Path, ts: int, cruzado: float, reina: float, rey: float, total: float) -> None:
    DIR.mkdir(parents=True, exist_ok=True)
    nuevo = not path.exists()
    with path.open("a", encoding="utf-8") as fh:
        if nuevo:
            fh.write("ts,cruzado,reina,rey,total\n")
        fh.write(f"{ts},{cruzado:.1f},{reina:.4f},{rey:.2f},{total:.0f}\n")


def _leer(path: Path) -> list[tuple[int, float, float, float, float]]:
    if not path.exists():
        return []
    out = []
    for linea in path.read_text(encoding="utf-8").splitlines()[1:]:
        if not linea.strip():
            continue
        trozos = linea.split(",")
        if len(trozos) < 5:
            continue
        out.append(tuple(float(x) for x in trozos[:5]))  # type: ignore[misc]
    return [(int(a), b, c, d, e) for a, b, c, d, e in out]


def _neto(filas: list[tuple], metal: list[float], inverso: bool) -> float:
    pnl = fee = 0.0
    previo_px = None
    anterior = None
    ultimo = 0.0
    for (ts, _c, reina, _rey, _total), puesto in zip(filas, metal):
        px = float(reina)
        if px <= 0:
            continue
        ultimo = px
        if previo_px:
            if inverso:
                pnl += puesto * (1.0 / previo_px - 1.0 / px)
            else:
                pnl += puesto * (px - previo_px) / previo_px
        if anterior is not None and puesto != anterior and px > 0:
            delta = abs(puesto - anterior)
            fee += (TASA * delta / px) if inverso else (TASA * delta)
        anterior = puesto
        previo_px = px
    if inverso:
        return (pnl - fee) * ultimo
    return pnl - fee


def _metales(filas, receta: dict | None) -> tuple[list[float], dict]:
    estado: dict = {}
    out = []
    for _ts, cruzado, reina, rey, total in filas:
        if receta is None:
            frac = 1.0
        else:
            estado, frac = paso(
                estado,
                cruzado,
                total,
                reina,
                rey=rey,
                adelgazo=receta["adelgazo"],
                piso=receta["piso"],
                forma=receta["forma"],
                miradas=MIRADAS[receta["mirada"]],
            )
        out.append(_grano(cruzado * INDICADOR * frac))
    return out, estado


def _recetas() -> list[dict]:
    out = []
    for adelgazo in UMBRALES:
        for piso in PISOS:
            for forma in FORMAS:
                for mirada in MIRADAS:
                    out.append(
                        {
                            "adelgazo": adelgazo,
                            "piso": piso,
                            "forma": forma,
                            "mirada": mirada,
                        }
                    )
    return out


def _corte(piso: float) -> int:
    return int(round((1.0 - piso) * 100))


def _ranking(filas, inverso: bool) -> dict:
    if len(filas) < 30:
        return {"n": len(filas), "siempre": None, "top": [], "viva": None}
    metal_base, _ = _metales(filas, None)
    base = _neto(filas, metal_base, inverso)
    hechos = []
    viva = None
    for receta in _recetas():
        metal, estado = _metales(filas, receta)
        neto = _neto(filas, metal, inverso)
        fila = {
            "adelgaza": int(receta["adelgazo"] * 100),
            "corta": _corte(receta["piso"]),
            "forma": receta["forma"],
            "mirada": receta["mirada"],
            "neto": round(neto, 1),
            "vs": round(neto - base, 1),
            "engordes": int(estado.get("engordes") or 0),
            "desengordes": int(estado.get("desengordes") or 0),
            "es_la_viva": receta["adelgazo"] == VIVA["adelgazo"]
            and receta["piso"] == VIVA["piso"]
            and receta["forma"] == VIVA["forma"]
            and receta["mirada"] == VIVA["mirada"],
        }
        hechos.append(fila)
        if fila["es_la_viva"]:
            viva = fila
    hechos.sort(key=lambda h: h["neto"], reverse=True)
    return {
        "n": len(filas),
        "siempre": round(base, 1),
        "viva": viva,
        "top": hechos[:8],
    }


def _publicar() -> None:
    cripto = _leer(CRIPTO)
    bolsa = _leer(BOLSA)
    informe = {
        "papel": True,
        "no_planta": True,
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "receta_viva": "adelgaza 10, apaga todo, despacio, total y reina",
        "cripto": _ranking(cripto, True),
        "bolsa": _ranking(bolsa, False),
    }
    INFORME.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    viva = (informe["cripto"].get("viva") or {})
    mejor = (informe["cripto"].get("top") or [{}])[0]
    print(
        f"[PAPEL] cripto n={informe['cripto']['n']} "
        f"viva {viva.get('neto')} engordes {viva.get('engordes')} "
        f"desengordes {viva.get('desengordes')} mejor {mejor.get('adelgaza')}/"
        f"{mejor.get('corta')} {mejor.get('forma')} {mejor.get('mirada')} "
        f"{mejor.get('neto')} · bolsa n={informe['bolsa']['n']}",
        flush=True,
    )


def main() -> None:
    print("[PAPEL] otras recetas del desinflador. no planta.", flush=True)
    _sembrar_cripto()
    ultima_cuenta = 0.0
    while True:
        ahora = int(time.time())
        total = total_del_mercado()
        rey = precio("BTC-USD-SWAP")
        casa = _cruzado_diario()
        if casa and ahora // 60 != _ultimo_ts(CRIPTO) // 60:
            _anotar(CRIPTO, casa[0], casa[1], precio("ETH-USD-SWAP"), rey, total)
        bolsa = _cruzado_bolsa()
        if bolsa is not None and ahora // 60 != _ultimo_ts(BOLSA) // 60:
            _anotar(BOLSA, ahora, bolsa, precio("US100-USDT-SWAP"), rey, total)
        if time.time() - ultima_cuenta >= 600:
            try:
                _publicar()
            except Exception as exc:
                print(f"[PAPEL] {exc}", flush=True)
            ultima_cuenta = time.time()
        time.sleep(60)


if __name__ == "__main__":
    main()
