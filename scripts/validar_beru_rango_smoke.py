#!/usr/bin/env python3
"""Smoke doctrinal — Beru rango: nace $5, engorde desde activación, techo meta−ya."""
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
    assert abs(g["masa_sangre_usd"] - 5.0) < 1e-9
    assert g["cero"] == "wake"
    assert g["nacimiento"] == "cinco_usd"
    assert g["engorde"] == "desde_activacion"
    assert g["saco_techo"] == "meta_menos_ya"
    assert abs(br.meta_saco_usd(100.0, 101.2) - 17.0) < 1e-9  # techo 1.2% → 12+$5
    assert abs(br.meta_saco_usd(100.0, 102.0) - 25.0) < 1e-9  # techo 2.0% → 20+$5
    print("  geometria + meta_saco numeros OK")


def _assert_vacio_cinco_y_cupo() -> None:
    """Vacío nace $5 (no $17); engorde desde ancla; Red también $5; cupo anti-stack."""
    b = BeruShip(uid="S1", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    m1 = br.armar_tramo_desde_vacio(b, "ABAJO", precio=98.8)
    assert abs(m1 - 5.0) < 1e-9, f"Vacío debe nacer en 5, got {m1}"
    # Avanza ~0.3% desde ancla → $8 (no meta wake)
    br.actualizar_trailing_oz(b, 98.8 * 0.997)
    assert abs(float(b.masa) - 8.0) < 1e-9, f"engorde Vacío desde ancla → 8, got {b.masa}"
    br.cosechar_oz_y_mover_cero(b, float(b.oz_adan))
    assert abs(br.saco_lado_usd(b, "LONG") - 8.0) < 1e-9
    assert abs(br.cero_wake(b) - 100.0) < 1e-9

    # Red a ~2.2%: cupo = 27 − 8 = 19 → nace $5 (no el cupo entero)
    assert float(b.red_adan) > 0
    b.red_adan = 97.8
    cupo = br.cupo_lado_usd(b, lado="LONG", precio=97.8, origen="RED")
    assert abs(cupo - 19.0) < 1e-9, cupo
    m2 = br.armar_tramo_desde_red(b, precio=97.8)
    assert abs(m2 - 5.0) < 1e-9, f"Red debe nacer en 5, got {m2}"
    # Engorde hasta el techo del cupo (~14 peldaños → $19)
    br.actualizar_trailing_oz(b, 97.8 * (1.0 - 0.014))
    assert abs(float(b.masa) - 19.0) < 1e-9, f"Red engorda hasta cupo 19, got {b.masa}"
    br.cosechar_oz_y_mover_cero(b, float(b.oz_adan))
    assert abs(br.saco_lado_usd(b, "LONG") - 27.0) < 1e-9
    print("  Vacío/Red $5 + engorde + cupo meta-ya OK")


def _assert_sangre_cinco_luego_engorde() -> None:
    """Sangre nace $5; si avanza 0.3% desde activación → $8; no $17 de wake."""
    b = BeruShip(uid="S2", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ABAJO", precio=98.8)
    br.actualizar_trailing_oz(b, 98.8)
    br.cosechar_oz_y_mover_cero(b, float(b.oz_adan))
    assert b.sangre_lado == "ARRIBA"
    sangre_px = 101.2
    m = br.armar_tramo_desde_sangre(b, precio=sangre_px)
    assert abs(m - 5.0) < 1e-9, f"sangre debe nacer en 5, got {m}"
    assert abs(float(b.masa) - 5.0) < 1e-9
    # Avanza ~0.3% desde ancla 101.2 → 101.504
    br.actualizar_trailing_oz(b, 101.2 * 1.003)
    assert abs(float(b.masa) - 8.0) < 1e-9, f"engorde desde ancla → 8, got {b.masa}"
    assert b.oreja_red_activa is False
    print("  sangre $5 nace + engorde desde activacion OK")


def _assert_red_fill_asimetrica() -> None:
    b = BeruShip(uid="RF1", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b, 101.2)
    oz = float(b.oz_adan)
    br.cosechar_oz_y_mover_cero(b, oz * 0.999, oz_despliegue=oz)
    assert abs(b.red_adan - oz * 1.007) < 1e-9

    b2 = BeruShip(uid="RF2", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b2, 100.0, activo="ETH")
    br.toca_vacio(b2, 100.0)
    br.armar_tramo_desde_vacio(b2, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b2, 101.2)
    oz2 = float(b2.oz_adan)
    fill_peor = oz2 * 1.001
    br.cosechar_oz_y_mover_cero(b2, fill_peor, oz_despliegue=oz2)
    assert abs(b2.red_adan - fill_peor * 1.007) < 1e-9
    print("  Red asimétrica SHORT OK")


async def _assert_general() -> None:
    g = BeruRango(Tusk(), Bel(), Tank(), bridge=None)
    await g.despertar(100.0, activo="ETH")
    await g.pulso(100.0)
    r = await g.pulso(101.2)
    assert r.get("evento") == "ARMAR_ARRIBA"
    assert abs(float(r.get("masa") or 0) - 5.0) < 1e-9, r.get("masa")
    await g.pulso(102.0)
    # Desde ancla 101.2 → 102 ≈ 0,79 % → 7 peldaños → $12 (techo meta 25)
    assert abs(float(g.vivo.masa) - 12.0) < 1e-9, g.vivo.masa
    cosecha = await g.pulso(g.vivo.oz_adan)
    assert cosecha.get("evento") == "OZ_COSECHA"
    assert abs(float(cosecha.get("cero") or 0) - 100.0) < 1e-9
    assert abs(float(getattr(g.vivo, "saco_short_usd", 0) or 0) - 12.0) < 1e-9
    r5 = await g.pulso(g.vivo.red_adan)
    assert r5.get("evento") == "ARMAR_RED"
    assert abs(float(r5.get("masa") or 0) - 5.0) < 1e-9, r5.get("masa")
    print("  General nace $5 + engorde + wake OK")


def _assert_plan_y_restaurar() -> None:
    b = BeruShip(
        uid="R3", centro_local=100.0, masa=10.0, direccion="SHORT",
        estado="CAZANDO", oz_adan=101.0, modo_combate="RANGO",
    )
    plan = altar.plan_trailing_entrada(b, activo="ETH", masa_usd=10.0)
    assert plan.trigger_direction == 2
    b2 = BeruShip(uid="R5", centro_local=1.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.restaurar_caza_trailing(
        b2, cero=0.40, direccion="LONG", oz=0.3954, trail_extremo=0.3962,
        masa=10.0, altar_link_id="BRG-TRA-1-abc", altar_order_id="oid1",
        altar_trigger_price=0.3954, altar_revision=3, uid="RANGO_WLD_CAZA",
    )
    assert b2.estado == "CAZANDO"
    assert abs(br.cero_wake(b2) - 0.40) < 1e-9
    print("  plan + restaurar OK")


def main() -> int:
    print("[SMOKE] beru rango doctrina nace $5 / engorde 2026-08-22")
    _assert_geometria()
    _assert_vacio_cinco_y_cupo()
    _assert_sangre_cinco_luego_engorde()
    _assert_red_fill_asimetrica()
    _assert_plan_y_restaurar()
    asyncio.run(_assert_general())
    print("OK validar_beru_rango_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
