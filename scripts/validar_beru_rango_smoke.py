#!/usr/bin/env python3
"""Smoke frio — Beru rango (Vacío arma trailing Oz 0.2 · Red ladder $5)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango as br
from core import beru_rango_altar as altar
from core.models import BeruShip
from generales.beru_rango import BeruRango


class Bel:
    def __init__(self) -> None:
        self.tags: list[str] = []

    async def anotar(self, _g, tag, _msg):
        self.tags.append(str(tag))


class Tank:
    precios = {"ETHUSDT_LINEAL": 100.0}


class Tusk:
    pass


def _assert_geometria() -> None:
    g = br.resumen_geometria()
    assert abs(g["vacio_pct"] - 0.012) < 1e-12
    assert abs(g["trailing_pct"] - 0.002) < 1e-12
    assert g["oz_modo"] == "trailing"
    assert abs(g["sangre_pct"] - 0.012) < 1e-12
    assert abs(g["masa_usd"] - 10.0) < 1e-9
    assert abs(g["masa_red_usd"] - 5.0) < 1e-9
    print("  geometria Vacio 1.2 / trailing Oz 0.2 / Red->$5 OK")


def _assert_trailing_short() -> None:
    b = BeruShip(uid="R1", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    assert br.toca_vacio(b, 101.2) == "ARRIBA"
    masa = br.armar_tramo_desde_vacio(b, "ARRIBA", precio=101.2)
    assert abs(masa - 10.0) < 1e-9
    assert b.direccion == "SHORT"
    assert abs(b.trail_extremo - 101.2) < 1e-9
    assert abs(b.oz_adan - 101.2 * 0.998) < 1e-9
    # Sube: el rastro persigue
    assert not br.toca_oz(b, 101.5)
    br.actualizar_trailing_oz(b, 102.0)
    assert abs(b.trail_extremo - 102.0) < 1e-9
    assert abs(b.oz_adan - 102.0 * 0.998) < 1e-9
    # Retrocede a la Oz -> SHORT
    assert not br.toca_oz(b, 102.0 * 0.998 + 0.01)
    assert br.toca_oz(b, 102.0 * 0.998)
    br.cosechar_oz_y_mover_cero(b, b.oz_adan)
    assert b.sangre_lado == "ABAJO"
    assert b.oreja_red_activa is True
    print("  trailing SHORT persigue extremo y detona al bajar OK")


def _assert_ladder_y_sangre() -> None:
    b = BeruShip(uid="R2", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b, 101.2)
    br.cosechar_oz_y_mover_cero(b, b.oz_adan)
    assert br.toca_red_continuacion(b, b.red_adan)
    br.armar_tramo_desde_red(b, precio=b.red_adan)
    assert abs(b.masa - 5.0) < 1e-9
    assert b.direccion == "SHORT"
    # LONG por Vacío abajo
    b2 = BeruShip(uid="R3", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b2, 100.0, activo="ETH")
    br.toca_vacio(b2, 100.0)
    br.armar_tramo_desde_vacio(b2, "ABAJO", precio=98.8)
    br.actualizar_trailing_oz(b2, 98.0)
    assert br.toca_oz(b2, b2.oz_adan)
    br.cosechar_oz_y_mover_cero(b2, b2.oz_adan)
    assert b2.sangre_lado == "ARRIBA"
    print("  ladder Red $5 + LONG trailing OK")


async def _assert_general() -> None:
    g = BeruRango(Tusk(), Bel(), Tank(), bridge=None)
    await g.despertar(100.0, activo="ETH")
    await g.pulso(100.0)
    r2 = await g.pulso(101.2)
    assert r2.get("evento") == "ARMAR_ARRIBA"
    # Aun en el extremo: no detona
    r3 = await g.pulso(101.2)
    assert r3.get("evento") == "CAZA"
    # Sube y luego baja a Oz
    await g.pulso(102.0)
    oz = g.vivo.oz_adan
    r4 = await g.pulso(oz)
    assert r4.get("evento") == "OZ_COSECHA"
    r5 = await g.pulso(g.vivo.red_adan)
    assert r5.get("evento") == "ARMAR_RED"
    assert abs(r5.get("masa") - 5.0) < 1e-9
    print("  General trailing + Red->$5 OK")


def _assert_plan() -> None:
    b = BeruShip(
        uid="R3", centro_local=100.0, masa=10.0, direccion="SHORT",
        estado="CAZANDO", oz_adan=101.0, modo_combate="RANGO",
    )
    plan = altar.plan_trailing_entrada(b, activo="ETH", masa_usd=10.0)
    assert plan.category == "linear"
    assert plan.side == "Sell"
    assert plan.trigger_direction == 2  # baja a la Oz
    print("  plan trailing SHORT Sell dir=2 OK", plan.qty)


def main() -> int:
    print("[SMOKE] beru rango trailing Oz")
    _assert_geometria()
    _assert_trailing_short()
    _assert_ladder_y_sangre()
    _assert_plan()
    asyncio.run(_assert_general())
    print("OK validar_beru_rango_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
