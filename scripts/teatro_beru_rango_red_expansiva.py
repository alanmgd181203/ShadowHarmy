#!/usr/bin/env python3
"""Teatro corto — Red expansiva: OFF vs ON en ciclo Oz→Red (piedra, sin manos)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_rango as br
from core.models import BeruShip


def _ciclo(flag_on: bool) -> list[float]:
    """Devuelve |red_pct| tras cada plantado post-Oz (el % doctrinal real)."""
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA", None)
    if flag_on:
        os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    prev = getattr(config, "BERU_RANGO_PERFIL", "normal")
    config.BERU_RANGO_PERFIL = "piedra"
    try:
        b = BeruShip(
            uid="T_TEATRO_RED",
            centro_local=100.0,
            masa=0.0,
            direccion="",
            estado="ACECHANDO",
        )
        br.despertar(b, 100.0, activo="ETH")
        pcts: list[float] = []
        b.direccion = "SHORT"
        b.masa = 5.0
        br.cosechar_oz_y_mover_cero(b, 100.2, oz_despliegue=100.0, masa_usd=5.0)
        pcts.append(abs(float(b.red_pct or 0)))
        for _ in range(5):
            red = float(b.red_adan)
            assert red > 0
            out = br.armar_tramo_desde_red(b, precio=red)
            assert out > 0
            oz = float(b.oz_adan)
            fill = max(oz, red * 1.001)
            br.cosechar_oz_y_mover_cero(
                b, fill, oz_despliegue=oz, masa_usd=float(b.masa or 5)
            )
            pcts.append(abs(float(b.red_pct or 0)))
        return pcts
    finally:
        config.BERU_RANGO_PERFIL = prev
        os.environ.pop("BERU_RANGO_RED_EXPANSIVA", None)


def main() -> int:
    print("=== teatro Red expansiva OFF vs ON ===")
    off = _ciclo(False)
    on = _ciclo(True)
    base = br.red_activacion_pct("SHORT")
    print("red_pct OFF %:", [round(p * 100, 3) for p in off])
    print("red_pct ON  %:", [round(p * 100, 3) for p in on])
    print("base SHORT %:", round(base * 100, 3))

    # OFF: siempre base (expansiva dormida)
    assert all(abs(p - base) < 1e-9 for p in off), off
    # ON: primer plantado sin escalones = base; luego +0.1% por Red tocada
    assert abs(on[0] - base) < 1e-9, on[0]
    for i in range(1, len(on)):
        want = base + 0.001 * i
        assert abs(on[i] - want) < 1e-9, (i, on[i], want)
    assert on[-1] > off[-1] + 0.004
    print("OK teatro: OFF clavado · ON se aleja +0.1% por escalon")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
