#!/usr/bin/env python3
"""Smoke frio — Beru rango (activacion + callback; Red tambien trailing)."""
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
    assert g["oz_modo"] == "trailing_callback"
    assert g["red_modo"] == "trailing"
    assert abs(g["red_activacion_pct"] - 0.007) < 1e-12
    assert abs(g["masa_red_usd"] - 5.0) < 1e-9
    print("  geometria act 1.2 / callback 0.2 / Red trailing act 0.7 OK")


def _assert_trailing_short() -> None:
    b = BeruShip(uid="R1", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    assert br.toca_vacio(b, 101.2) == "ARRIBA"
    br.armar_tramo_desde_vacio(b, "ARRIBA", precio=101.2)
    assert abs(b.oz_adan - 101.2 * 0.998) < 1e-9
    assert float(b.red_adan or 0) == 0.0  # Red no durante caza
    br.actualizar_trailing_oz(b, 102.0)
    assert abs(b.oz_adan - 102.0 * 0.998) < 1e-9
    assert br.toca_oz(b, 102.0 * 0.998)
    br.cosechar_oz_y_mover_cero(b, b.oz_adan)
    assert b.oreja_red_activa is True
    assert abs(b.red_adan - b.centro_local * 1.007) < 1e-9
    print("  Vacío act -> callback -> Red act 0.7 plantada OK")


def _assert_red_trailing_y_sangre_cancela() -> None:
    b = BeruShip(uid="R2", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b, 101.2)
    fill = b.oz_adan
    br.cosechar_oz_y_mover_cero(b, fill)
    red_act = b.red_adan
    assert br.toca_red_activacion(b, red_act)
    br.armar_tramo_desde_red(b, precio=red_act)
    assert abs(b.masa - 5.0) < 1e-9
    assert b.oreja_red_activa is False
    br.actualizar_trailing_oz(b, red_act * 1.01)
    assert br.toca_oz(b, b.oz_adan)
    # Sangre cancela Red
    b2 = BeruShip(uid="R3", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b2, 100.0, activo="ETH")
    br.toca_vacio(b2, 100.0)
    br.armar_tramo_desde_vacio(b2, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b2, 101.2)
    br.cosechar_oz_y_mover_cero(b2, b2.oz_adan)
    assert b2.oreja_red_activa
    sangre_px = b2.centro_local * (1 - 0.012)
    assert br.toca_sangre(b2, sangre_px)
    br.armar_tramo_desde_sangre(b2, precio=sangre_px)
    assert b2.direccion == "LONG"
    assert b2.oreja_red_activa is False
    assert float(b2.red_adan or 0) == 0.0
    print("  Red trailing $5 + sangre cancela Red OK")


async def _assert_general() -> None:
    g = BeruRango(Tusk(), Bel(), Tank(), bridge=None)
    await g.despertar(100.0, activo="ETH")
    await g.pulso(100.0)
    assert (await g.pulso(101.2)).get("evento") == "ARMAR_ARRIBA"
    assert (await g.pulso(101.2)).get("evento") == "CAZA"
    await g.pulso(102.0)
    assert (await g.pulso(g.vivo.oz_adan)).get("evento") == "OZ_COSECHA"
    r5 = await g.pulso(g.vivo.red_adan)
    assert r5.get("evento") == "ARMAR_RED"
    assert abs(r5.get("masa") - 5.0) < 1e-9
    print("  General Red trailing OK")


def _assert_plan() -> None:
    b = BeruShip(
        uid="R3", centro_local=100.0, masa=10.0, direccion="SHORT",
        estado="CAZANDO", oz_adan=101.0, modo_combate="RANGO",
    )
    plan = altar.plan_trailing_entrada(b, activo="ETH", masa_usd=10.0)
    assert plan.trigger_direction == 2
    print("  plan trailing SHORT OK", plan.qty)


def main() -> int:
    print("[SMOKE] beru rango activacion+callback")
    _assert_geometria()
    _assert_trailing_short()
    _assert_red_trailing_y_sangre_cancela()
    _assert_plan()
    asyncio.run(_assert_general())
    print("OK validar_beru_rango_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
