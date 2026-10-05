"""Una nota viva del neto y de los dos escudos.

La nota se reescribe. Un mensaje suelto solo cuando un escudo
se coloca o se retira. No despierta cazadores y no mueve metal.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from core import config  # noqa: E402
from core import okx_rest  # noqa: E402

BOLSA = {
    "AAPL", "CBRS", "SOXL", "ALAB", "SOXS", "COIN", "SPCX", "AVGO", "CRDO", "QCOM",
    "QNT", "IBM", "CRWV", "RAM", "INTW", "UNITREE", "AMZN", "MRNA", "USAR", "GOOGL",
    "MSTR", "APP", "MUU", "UVXY", "ARM", "EWY", "RKLB", "IREN", "BE", "MINIMAX",
    "NFLX", "SAMSUNG", "TSLA", "BMNR", "MRVL", "AAOI", "NOK", "TSM", "NBIS",
    "ANTHROPIC", "GLW", "SKDD", "MSFT", "COHR", "NVDA", "SKHY", "MSTU", "ASTS",
    "OPENAI", "SKHYNIX", "MVLL", "WDC", "AXTI", "ORCL", "SNDK", "SKUU", "PLTR",
    "SNXX",
}
ESCUDO_CRIPTO = {"BTC-USD-SWAP", "ETH-USD-SWAP"}
ESCUDO_BOLSA = {"US100-USDT-SWAP", "US500-USDT-SWAP"}
MEMORIA = RAIZ / "data" / "beru" / "escudo" / "neto_telegram.json"
PAUSA_S = 60.0
POLVO = 500.0


def vestir(neto: float) -> str:
    """El neto en miles. Positivo es más corto."""
    if abs(neto) < POLVO:
        return "neto, parejo"
    millar = int(abs(neto) / 1000.0 + 0.5)
    if millar < 1:
        return "neto, parejo"
    bando = "short" if neto > 0 else "long"
    return f"neto, {millar}k en {bando}"


def vestir_escudo(tam: float, casa: str) -> str:
    nombre = "escudo trade fi" if casa == "bolsa" else "escudo"
    if tam < POLVO:
        return f"{nombre}, apagado"
    millar = int(tam / 1000.0 + 0.5)
    if millar < 1:
        return f"{nombre}, apagado"
    return f"{nombre}, {millar}k puesto"


def _lado_corto(row: dict, pos: float) -> bool:
    side = str(row.get("posSide") or "net").lower()
    return side == "short" or pos < 0


def _tam(row: dict) -> float:
    return abs(float(row.get("notionalUsd") or 0))


def medir() -> dict[str, float]:
    rows = okx_rest.get_private("/api/v5/account/positions", params={"instType": "SWAP"})
    foto = {"cripto": 0.0, "bolsa": 0.0, "escudo": 0.0, "escudo_bolsa": 0.0}
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        inst = str(row.get("instId") or "")
        try:
            pos = float(row.get("pos") or 0)
            tam = _tam(row)
        except (TypeError, ValueError):
            continue
        if abs(pos) < 1e-12 or tam <= 0:
            continue
        if inst in ESCUDO_CRIPTO:
            foto["escudo"] += tam
            continue
        if inst in ESCUDO_BOLSA:
            foto["escudo_bolsa"] += tam
            continue
        if not inst.endswith("-USDT-SWAP"):
            continue
        activo = inst.split("-")[0].upper()
        cubo = "bolsa" if activo in BOLSA else "cripto"
        if _lado_corto(row, pos):
            foto[cubo] += tam
        else:
            foto[cubo] -= tam
    return foto


def tablero(foto: dict[str, float]) -> str:
    return "\n".join(
        (
            f"cripto, {vestir(foto['cripto'])}",
            f"trade fi, {vestir(foto['bolsa'])}",
            vestir_escudo(foto["escudo"], "cripto"),
            vestir_escudo(foto["escudo_bolsa"], "bolsa"),
        )
    )


def _avisos(foto: dict[str, float], memoria: dict) -> list[str]:
    avisos: list[str] = []
    pares = (
        ("escudo", foto["escudo"], "el escudo"),
        ("escudo_bolsa", foto["escudo_bolsa"], "el escudo de trade fi"),
    )
    for clave, tam, nombre in pares:
        if clave not in memoria:
            continue
        antes = bool(memoria.get(clave))
        ahora = tam >= POLVO
        if (not antes) and ahora:
            millar = int(tam / 1000.0 + 0.5)
            avisos.append(f"{nombre} se colocó, {millar}k")
        elif antes and (not ahora):
            avisos.append(f"{nombre} se retiró")
    return avisos


def _cargar() -> dict:
    try:
        dato = json.loads(MEMORIA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}
    return dato if isinstance(dato, dict) else {}


def _guardar(dato: dict) -> None:
    MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    MEMORIA.write_text(json.dumps(dato, ensure_ascii=True), encoding="utf-8")


def _post(metodo: str, cuerpo: dict) -> dict | None:
    token = str(getattr(config, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    chat = str(getattr(config, "TELEGRAM_CHAT_ID", "") or "").strip()
    if not token or not chat:
        print("sin mensajero", flush=True)
        return None
    cuerpo = {"chat_id": chat, "disable_web_page_preview": True, **cuerpo}
    url = f"https://api.telegram.org/bot{token}/{metodo}"
    req = urllib.request.Request(
        url,
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            dato = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        crudo = exc.read().decode("utf-8", errors="replace")
        try:
            desc = str(json.loads(crudo).get("description") or "")
        except json.JSONDecodeError:
            desc = ""
        if "message is not modified" in desc:
            return {"ok": True, "igual": True}
        print(f"no llego {exc.code} {desc}".encode("ascii", "replace").decode("ascii"), flush=True)
        return None
    except Exception as exc:
        print(f"no llego {type(exc).__name__}", flush=True)
        return None
    if not dato.get("ok"):
        return None
    return dato


def decir(texto: str) -> int | None:
    dato = _post("sendMessage", {"text": texto})
    if not dato or dato.get("igual"):
        return None
    try:
        return int((dato.get("result") or {}).get("message_id"))
    except (TypeError, ValueError):
        return None


def reescribir(message_id: int, texto: str) -> bool:
    dato = _post("editMessageText", {"message_id": message_id, "text": texto})
    return dato is not None


def main() -> None:
    memoria = _cargar()
    while True:
        try:
            foto = medir()
        except Exception as exc:
            aviso = str(exc).encode("ascii", "replace").decode("ascii")[:80]
            print(f"casa ciega {aviso}", flush=True)
            time.sleep(180.0)
            continue
        texto = tablero(foto)
        for aviso in _avisos(foto, memoria):
            if decir(aviso):
                print(aviso.encode("ascii", "replace").decode("ascii"), flush=True)
        if texto != memoria.get("tablero"):
            nuevo = decir(texto)
            if nuevo:
                memoria["message_id"] = nuevo
                memoria["tablero"] = texto
                print("aviso", flush=True)
        memoria["escudo"] = foto["escudo"] >= POLVO
        memoria["escudo_bolsa"] = foto["escudo_bolsa"] >= POLVO
        memoria["ts"] = int(time.time())
        _guardar(memoria)
        time.sleep(PAUSA_S)


if __name__ == "__main__":
    main()
