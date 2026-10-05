"""El desinflador. No cambia la banda. Solo achica el metal que ella ya vistió.

Si la bolsa adelgaza un diez por ciento desde su máximo, el metal se
apaga. Vuelve despacio, al cuadrado, cuando el total del mercado y la
reina de ese manto suben otra vez, y del todo al tocar el máximo.

Ya cortado: si engorda otra vez un diez desde el valle (o desde la
última alza), se cuenta engorde y se rehace la mirada. Si desde esa
cresta vuelve a adelgazar un diez, se cuenta otro desengorde.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = RAIZ / "data" / "beru" / "escudo"
ADELGAZO = 0.10
_CACHE_TOTAL = {"ts": 0.0, "valor": 0.0}


def _vacio() -> dict:
    return {
        "pico": 0.0,
        "valle": 0.0,
        "cortado": False,
        "lado": 0,
        "bajo_total": 0.0,
        "bajo_reina": 0.0,
        "bajo_rey": 0.0,
        "cresta": 0.0,
        "alza": 0.0,
        "engordes": 0,
        "desengordes": 0,
    }


def _ruta(nombre: str) -> Path:
    return DIR / f"desinflar_{nombre}.json"


def _leer(nombre: str) -> dict:
    try:
        dato = json.loads(_ruta(nombre).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return _vacio()
    base = _vacio()
    if isinstance(dato, dict):
        base.update({k: dato.get(k, base[k]) for k in base})
    base["cortado"] = bool(base["cortado"])
    base["lado"] = int(base["lado"] or 0)
    return base


def _guardar(nombre: str, estado: dict) -> None:
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        _ruta(nombre).write_text(json.dumps(estado), encoding="utf-8")
    except OSError:
        pass


def _forma(trecho: float, cual: str) -> float:
    t = 0.0 if trecho < 0 else 1.0 if trecho > 1 else trecho
    if cual == "rapida":
        return t ** 0.5
    if cual == "media":
        return t
    return t * t


def paso(
    estado: dict,
    cruzado: float,
    total: float,
    reina: float,
    *,
    rey: float = 0.0,
    adelgazo: float = ADELGAZO,
    piso: float = 0.0,
    forma: str = "lenta",
    miradas: tuple[str, ...] = ("total", "reina"),
) -> tuple[dict, float]:
    """La fracción del metal de la banda. 1 es el vestido entero.

    Lo vivo usa el diez por ciento, el apagado total y la vuelta
    despacio con el total y la reina. El papel puede pedir otra receta.
    """
    masa = abs(float(cruzado or 0))
    signo = 1 if cruzado > 0 else -1 if cruzado < 0 else 0
    lado = int(estado.get("lado") or 0)
    pico = float(estado.get("pico") or 0)
    valle = float(estado.get("valle") or 0)
    cortado = bool(estado.get("cortado"))
    bajo_t = float(estado.get("bajo_total") or 0)
    bajo_r = float(estado.get("bajo_reina") or 0)
    bajo_k = float(estado.get("bajo_rey") or 0)
    cresta = float(estado.get("cresta") or 0)
    alza = float(estado.get("alza") or 0)
    engordes = int(estado.get("engordes") or 0)
    desengordes = int(estado.get("desengordes") or 0)
    queda = max(0.0, min(1.0, float(piso)))
    umbral = max(1e-9, float(adelgazo))

    def _bajos() -> tuple[float, float, float]:
        return float(total or 0), float(reina or 0), float(rey or 0)

    if signo == 0 or (lado and signo != lado):
        cortado = False
        pico = valle = masa
        bajo_t, bajo_r, bajo_k = _bajos()
        lado = signo
        cresta = alza = 0.0
        engordes = desengordes = 0
        frac = 1.0
    elif not cortado:
        lado = signo
        if masa >= pico:
            pico = masa
        if pico > 0 and masa <= pico * (1.0 - umbral):
            cortado = True
            valle = masa
            bajo_t, bajo_r, bajo_k = _bajos()
            cresta = alza = 0.0
            desengordes += 1
            frac = queda
        else:
            frac = 1.0
    elif masa >= pico:
        cortado = False
        pico = valle = masa
        bajo_t, bajo_r, bajo_k = _bajos()
        cresta = alza = 0.0
        frac = 1.0
    else:
        # Primero la cresta: un -umbral cuenta desengorde aunque baje del valle viejo.
        if cresta > 0 and masa <= cresta * (1.0 - umbral):
            desengordes += 1
            valle = masa
            cresta = alza = 0.0
            bajo_t, bajo_r, bajo_k = _bajos()
        elif masa < valle:
            valle = masa
            bajo_t, bajo_r, bajo_k = _bajos()
            cresta = alza = 0.0
        else:
            base_alza = alza if alza > 0 else valle
            if base_alza > 0 and masa >= base_alza * (1.0 + umbral):
                engordes += 1
                alza = masa
                cresta = masa
                bajo_t, bajo_r, bajo_k = _bajos()
            elif cresta > 0:
                cresta = max(cresta, masa)
        trecho = 0.0 if pico <= valle else (masa - valle) / (pico - valle)
        sube = {
            "total": float(total or 0) > bajo_t > 0,
            "reina": float(reina or 0) > bajo_r > 0,
            "rey": float(rey or 0) > bajo_k > 0,
        }
        ok = all(sube[nombre] for nombre in miradas)
        if not miradas:
            ok = trecho > 0
        frac = queda if not ok else queda + (1.0 - queda) * _forma(trecho, forma)
    nuevo = {
        "pico": pico,
        "valle": valle,
        "cortado": cortado,
        "lado": lado,
        "bajo_total": bajo_t,
        "bajo_reina": bajo_r,
        "bajo_rey": bajo_k,
        "cresta": cresta,
        "alza": alza,
        "engordes": engordes,
        "desengordes": desengordes,
    }
    return nuevo, float(frac)


def total_del_mercado() -> float:
    """El total del mercado, en dólares. Si no se ve, el último que se vio."""
    ahora = time.time()
    if _CACHE_TOTAL["valor"] > 0 and ahora - _CACHE_TOTAL["ts"] < 600:
        return float(_CACHE_TOTAL["valor"])
    try:
        desde = int(ahora) - 6 * 3600
        url = (
            "https://api.coinmarketcap.com/data-api/v3/global-metrics/quotes/historical"
            f"?convert=USD&format=chart&interval=1h&timeStart={desde}&timeEnd={int(ahora) + 60}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            dato = json.loads(resp.read().decode("utf-8"))
        puntos = []
        for punto in (dato.get("data") or {}).get("quotes") or []:
            momento = int(
                datetime.fromisoformat(
                    str(punto.get("timestamp")).replace("Z", "+00:00")
                ).timestamp()
            )
            total = float(((punto.get("quote") or [{}])[0]).get("totalMarketCap") or 0)
            if total > 0:
                puntos.append((momento, total))
        if puntos:
            _CACHE_TOTAL["valor"] = float(puntos[-1][1])
            _CACHE_TOTAL["ts"] = ahora
    except Exception:
        pass
    return float(_CACHE_TOTAL["valor"] or 0)


def precio(inst: str) -> float:
    inst_id = str(inst or "")
    if not inst_id:
        return 0.0
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "ShadowHarmy-ojo"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            dato = json.loads(resp.read().decode("utf-8"))
        fila = (dato.get("data") or [{}])[0]
        return float(fila.get("last") or fila.get("markPx") or 0)
    except Exception:
        return 0.0


def fraccion(nombre: str, cruzado: float, reina_inst: str) -> tuple[float, str]:
    """Fracción viva y una frase corta para el latido."""
    estado = _leer(nombre)
    nuevo, frac = paso(
        estado,
        float(cruzado or 0),
        total_del_mercado(),
        precio(reina_inst),
    )
    _guardar(nombre, nuevo)
    if not nuevo["cortado"]:
        frase = "desinfla · lleno"
    elif frac <= 0:
        frase = "desinfla · apagado"
    else:
        frase = f"desinfla · viste {frac:.2f}"
    return frac, frase
