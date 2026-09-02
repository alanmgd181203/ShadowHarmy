#!/usr/bin/env python3
"""Smoke — reloj BTC mil + cola despertar (sin lanzar procesos)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_despertar_mil_btc as dm


def main() -> int:
    assert dm.zona_mil(78543) == 78000
    assert dm.zona_mil(77999) == 77000
    assert dm.zona_mil(80000) == 80000

    c1 = dm.cruces_zona(77900, 78100)
    assert len(c1) == 1 and c1[0]["zona_mil"] == 78000 and c1[0]["direccion"] == "arriba"

    c2 = dm.cruces_zona(80100, 77800)
    assert len(c2) == 3
    assert [x["zona_mil"] for x in c2] == [79000, 78000, 77000]

    st = dm.inicializar_estado(precio_btc=78050)
    assert len(st["cola"]["rojos"]) >= 1
    assert len(st["cola"]["amarillos"]) >= 1

    st["ultimo_precio_btc"] = 77900
    evs = dm.procesar_tick(st, 78100)
    assert len(evs) == 1
    assert evs[0].get("rojo") and evs[0].get("amarillo")

    print("OK validar_despertar_mil_btc_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
