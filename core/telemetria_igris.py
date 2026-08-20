"""Telemetría de posiciones — stub (Igris de baja). Solo lectura de pesos Tusk."""
from __future__ import annotations

from typing import Any


def telemetria_desde_pesos(pesos: dict, equity: float) -> dict[str, Any]:
    filas = []
    for frente, p in (pesos or {}).items():
        lon = float((p or {}).get("long") or 0)
        sho = float((p or {}).get("short") or 0)
        if lon <= 0 and sho <= 0:
            continue
        filas.append({
            "frente": frente,
            "long": lon,
            "short": sho,
            "precio_medio_long": float((p or {}).get("precio_medio_long") or 0),
            "precio_medio_short": float((p or {}).get("precio_medio_short") or 0),
        })
    return {
        "ok": True,
        "fuente": "pesos",
        "equity": float(equity or 0),
        "filas": filas,
        "n": len(filas),
    }


def telemetria_desde_exchange(posiciones: list, equity: float) -> dict[str, Any]:
    filas = []
    for p in posiciones or []:
        filas.append({
            "symbol": p.get("symbol"),
            "side": p.get("side"),
            "size": p.get("size"),
            "avgPrice": p.get("avgPrice"),
        })
    return {
        "ok": True,
        "fuente": "exchange",
        "equity": float(equity or 0),
        "filas": filas,
        "n": len(filas),
    }
