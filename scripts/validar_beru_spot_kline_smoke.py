#!/usr/bin/env python3
"""Smoke velas spot Beru — mapeo + parse + escala de TODOS los Santos."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.beru_spot_kline import (  # noqa: E402
    escala_spot,
    parse_list,
    precision_desde_precio,
    precision_desde_tick,
    simbolo_spot,
)


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_mapeo() -> None:
    _assert(simbolo_spot("ETH") == "ETHUSDT", "ETH")
    _assert(simbolo_spot("ethusdt_spot") == "ETHUSDT", "frente spot")
    _assert(simbolo_spot("HYPE") == "HYPEUSDT", "HYPE casa")
    _assert(simbolo_spot("HYPE") != "HYPERUSDT", "HYPE no es HYPER")
    _assert(simbolo_spot("MNT") == "MNTUSDT", "MNT")
    rows = parse_list([
        ["1700000002000", "2", "3", "1", "2.5", "10", "10"],
        ["1700000000000", "1", "2", "0.5", "1.5", "10", "10"],
    ])
    _assert(len(rows) == 2, "n rows")
    _assert(rows[0]["time"] == 1700000000, "orden tiempo")
    _assert(rows[0]["close"] == 1.5, "close")
    _assert(rows[1]["time"] > rows[0]["time"], "sort")
    _assert(parse_list([["x"]]) == [], "basura")
    print("  A) mapeo + parse OK")


def test_ticks() -> None:
    _assert(precision_desde_tick("0.00001")[1] == 5, "DOGE tick")
    _assert(precision_desde_tick("0.0001")[1] == 4, "ADA tick")
    _assert(precision_desde_tick("0.01")[1] == 2, "ETH tick")
    _assert(precision_desde_tick("0.1")[1] == 1, "BTC tick")
    _assert(precision_desde_precio(0.07)[1] >= 5, "fallback DOGE")
    _assert(precision_desde_precio(67000)[1] <= 2, "fallback BTC")
    print("  B) ticks OK")


def test_flota_22() -> None:
    path = Path(ROOT) / "data" / "bybit_minimos_orden.json"
    bd = json.loads(path.read_text(encoding="utf-8"))
    activos = bd.get("activos") or {}
    _assert(len(activos) >= 17, f"santos {len(activos)}")
    baratos = []
    for nombre, row in sorted(activos.items()):
        spot = (row or {}).get("spot_usdt") or {}
        tick = spot.get("tickSize")
        ref = float(spot.get("precio_ref") or 0)
        esc = escala_spot(nombre, ref)
        prec = int(esc["precision"])
        _assert(prec >= 1, f"{nombre} sin decimales")
        if ref and ref < 1:
            _assert(prec >= 4, f"{nombre} barato prec={prec} tick={tick} ref={ref}")
            baratos.append(nombre)
        if nombre == "DOGE":
            _assert(prec >= 5, f"DOGE prec={prec}")
        if nombre in ("BTC", "ETH") and tick:
            _assert(prec <= 3, f"{nombre} prec={prec}")
    _assert("DOGE" in baratos, "DOGE en baratos")
    print(f"  C) flota {len(activos)} Santos OK · baratos={len(baratos)}")


def main() -> None:
    print("Smoke velas spot Beru")
    test_mapeo()
    test_ticks()
    test_flota_22()
    print("PASS 3/3")


if __name__ == "__main__":
    main()
