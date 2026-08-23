"""Velas spot para el Pergamino de Beru.

Ojos públicos de Bybit (sin manos). Casa USDT. HYPE ≠ HYPER.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "beru" / "klines"
TTL_S = 20.0
BYBIT = "https://api.bybit.com/v5/market/kline"
INTERVALOS_OK = frozenset({"1", "3", "5", "15", "30", "60", "120", "240", "D", "W"})


def simbolo_spot(activo: str) -> str:
    """ETH → ETHUSDT. Nunca HYPER cuando el Santo es HYPE."""
    raw = str(activo or "ETH").upper().strip()
    raw = raw.replace("_SPOT", "").replace("_LINEAL", "").replace("_INVERSE", "")
    raw = re.sub(r"[^A-Z0-9]", "", raw)
    if not raw:
        raw = "ETH"
    for q in ("USDT", "USDC", "USDE", "USD1"):
        if raw.endswith(q) and len(raw) > len(q):
            return raw
    return f"{raw}USDT"


def precision_desde_tick(tick: Any) -> tuple[float | None, int | None]:
    """Tick Bybit → (min_move, decimales). 0.00001 → 5."""
    if tick is None or tick == "":
        return None, None
    try:
        t = float(tick)
    except (TypeError, ValueError):
        return None, None
    if not (t > 0):
        return None, None
    try:
        exp = Decimal(str(tick)).as_tuple().exponent
        prec = min(10, max(0, -int(exp)))
    except (ArithmeticError, ValueError):
        s = f"{t:.10f}".rstrip("0")
        prec = len(s.split(".")[1]) if "." in s else 0
    return t, prec


def precision_desde_precio(precio: float) -> tuple[float, int]:
    """Respaldo si no hay tick: más chico el Santo, más decimales."""
    p = abs(float(precio or 0))
    if p >= 1000:
        prec = 2
    elif p >= 100:
        prec = 3
    elif p >= 1:
        prec = 4
    elif p >= 0.1:
        prec = 5
    elif p >= 0.01:
        prec = 6
    elif p >= 0.001:
        prec = 7
    else:
        prec = 8
    move = float(Decimal("1").scaleb(-prec))
    return move, prec


def tick_spot(symbol: str) -> Any:
    """Tick de la casa USDT en la BD de mínimos / parámetros."""
    try:
        from core import lote_bybit as lb
    except Exception:
        return None
    frente = symbol if str(symbol).upper().endswith("_SPOT") else f"{symbol}_SPOT"
    try:
        row = lb.filtros_lote(frente) or {}
    except Exception:
        return None
    return row.get("tickSize")


def escala_spot(symbol: str, precio: float = 0.0) -> dict[str, Any]:
    move, prec = precision_desde_tick(tick_spot(symbol))
    fuente = "tick_bd"
    if prec is None:
        move, prec = precision_desde_precio(precio)
        fuente = "precio"
    return {
        "tick_size": move,
        "min_move": move,
        "precision": prec,
        "escala_fuente": fuente,
    }


def parse_list(raw: list) -> list[dict[str, Any]]:
    """Bybit: [startMs, o, h, l, c, vol, turnover] · más nuevo primero."""
    out: list[dict[str, Any]] = []
    for row in raw or []:
        if not isinstance(row, (list, tuple)) or len(row) < 5:
            continue
        try:
            ts_ms = int(row[0])
            o, h, l, c = (float(row[1]), float(row[2]), float(row[3]), float(row[4]))
        except (TypeError, ValueError):
            continue
        if ts_ms <= 0 or not all(x > 0 for x in (o, h, l, c)):
            continue
        out.append({
            "time": ts_ms // 1000,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
        })
    out.sort(key=lambda x: x["time"])
    return out


def _cache_path(symbol: str, interval: str) -> Path:
    return CACHE_DIR / f"{symbol}_{interval}.json"


def _leer_cache(symbol: str, interval: str, limit: int) -> dict[str, Any] | None:
    path = _cache_path(symbol, interval)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    age = time.time() - float(data.get("ts") or 0)
    if age > TTL_S:
        return None
    velas = data.get("velas") or []
    if len(velas) < min(10, limit):
        return None
    return data


def _guardar_cache(payload: dict[str, Any], *, cache_symbol: str | None = None) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(cache_symbol or payload["symbol"], payload["interval"])
        path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        pass


def pedir_velas(
    activo: str,
    *,
    interval: str = "15",
    limit: int = 200,
    timeout: float = 12.0,
    category: str = "spot",
) -> dict[str, Any]:
    """Foto de velas spot o linear. Cache corta. Sin secretos."""
    iv = str(interval or "15")
    if iv not in INTERVALOS_OK:
        iv = "15"
    lim = max(20, min(int(limit or 200), 500))
    cat = str(category or "spot").strip().lower()
    if cat not in ("spot", "linear"):
        cat = "spot"
    symbol = simbolo_spot(activo)
    cache_key = f"{symbol}_{cat}"
    hit = _leer_cache(cache_key, iv, lim)
    if hit:
        hit["fuente"] = "cache"
        hit["category"] = cat
        hit["velas"] = (hit.get("velas") or [])[-lim:]
        last = (hit["velas"][-1]["close"] if hit.get("velas") else 0)
        hit.update(escala_spot(symbol, last))
        return hit

    url = f"{BYBIT}?category={cat}&symbol={symbol}&interval={iv}&limit={lim}"
    req = urllib.request.Request(url, headers={"User-Agent": "ShadowHarmy-BeruPergamino/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        stale = _cache_path(cache_key, iv)
        if stale.is_file():
            try:
                data = json.loads(stale.read_text(encoding="utf-8"))
                data["fuente"] = "cache_vieja"
                data["category"] = cat
                data["error"] = str(e)[:120]
                last = (data.get("velas") or [{}])[-1].get("close") or 0
                data.update(escala_spot(symbol, last))
                return data
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "symbol": symbol,
            "activo": str(activo or "").upper(),
            "interval": iv,
            "category": cat,
            "velas": [],
            "fuente": "error",
            "error": str(e)[:160],
            "ts": time.time(),
            **escala_spot(symbol, 0.0),
        }

    lista = ((body.get("result") or {}).get("list")) or []
    velas = parse_list(lista)
    last = velas[-1]["close"] if velas else 0.0
    payload = {
        "symbol": symbol,
        "activo": str(activo or "").upper(),
        "interval": iv,
        "category": cat,
        "n": len(velas),
        "velas": velas[-lim:],
        "fuente": f"bybit_{cat}",
        "ts": time.time(),
        "ret_code": body.get("retCode"),
        **escala_spot(symbol, last),
    }
    if velas:
        _guardar_cache(payload, cache_symbol=cache_key)
    return payload


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Velas spot/linear Beru (Pergamino)")
    ap.add_argument("--symbol", "--activo", dest="symbol", default="ETH")
    ap.add_argument("--interval", default="15")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--category", default="spot", help="spot | linear")
    args = ap.parse_args()
    os.chdir(ROOT)
    print(
        json.dumps(
            pedir_velas(
                args.symbol,
                interval=args.interval,
                limit=int(args.limit),
                category=args.category,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
