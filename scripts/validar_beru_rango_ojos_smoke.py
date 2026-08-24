#!/usr/bin/env python3
"""Smoke — ojos rango: latido/mecha (no solo last)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango as br
from core.models import BeruShip
from generales.tank import TankCluster


class Bel:
    async def anotar(self, *_a, **_k):
        return None


class Tusk:
    async def actualizar_precios(self, *_a, **_k):
        return None


def _assert_mecha_red() -> None:
    b = BeruShip(uid="M1", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b, 101.2)
    br.cosechar_oz_y_mover_cero(b, b.oz_adan)
    red = float(b.red_adan)
    # Last ya volvió debajo; la mecha del latido sí rozó la Red.
    lat = {"last": red - 0.5, "high": red + 0.01, "low": red - 0.8, "prints": []}
    assert not br.toca_red_activacion(b, lat["last"])
    assert br.toca_red_activacion_en_latido(b, lat["last"], lat)
    print("  mecha Red (high toca, last no) OK")


def _assert_misma_vela_sangre_antes_que_red() -> None:
    """Doctrina: misma vela → sangre primero (aunque el high toque Red)."""
    b = BeruShip(uid="M1S", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b, 101.2)
    br.cosechar_oz_y_mover_cero(b, float(b.oz_adan or 0) or 101.0)
    assert str(b.sangre_lado).upper() == "ABAJO"
    assert bool(b.oreja_sangre_activa) and bool(b.oreja_red_activa)
    # Sangre 1,2 % del peldaño Oz — no del wake (wake sigue en 100).
    sangre_px = float(b.sangre_adan or 0)
    oz_dep = float(b.oz_despliegue_px or 0)
    assert sangre_px > 0 and oz_dep > 0
    assert abs(sangre_px - oz_dep * (1.0 - br.sangre_contraria_pct())) < 1e-6
    assert abs(sangre_px - 100.0 * (1.0 - br.sangre_contraria_pct())) > 0.3
    red_px = float(b.red_adan)
    assert red_px > 100.0
    # Vela ancha: high toca Red, low toca sangre, last en medio.
    lat = {
        "last": (sangre_px + red_px) / 2.0,
        "high": red_px + 0.05,
        "low": sangre_px - 0.05,
        "prints": [],
    }
    assert br.toca_sangre_en_latido(b, lat["last"], lat)
    assert br.toca_red_activacion_en_latido(b, lat["last"], lat)
    # Orden doctrinal del for anidado (como en generales.beru_rango.pulso):
    trig = ""
    for sample in br.secuencia_latido(lat["last"], lat):
        if br.toca_sangre(b, sample):
            trig = "SANGRE"
            break
    if not trig:
        for sample in br.secuencia_latido(lat["last"], lat):
            if br.toca_red_activacion(b, sample):
                trig = "RED"
                break
    assert trig == "SANGRE", f"misma vela debe ganar sangre, got {trig}"
    print("  misma vela sangre antes que Red OK")


def _assert_tank_latido() -> None:
    tank = TankCluster(Tusk(), Bel(), ticker_base="ETH")
    tank.expandir_frentes(["ETHUSDT_LINEAL"])
    tank.registrar_print_lineal("ETHUSDT_LINEAL", 100.0, fuente_ws=True)
    tank.registrar_print_lineal("ETHUSDT_LINEAL", 101.5, fuente_ws=True)
    tank.registrar_print_lineal("ETHUSDT_LINEAL", 99.2, fuente_ws=True)
    assert tank.ts_rio_lineal_ws > 0
    lat = tank.consumir_latido_lineal("ETHUSDT_LINEAL")
    assert abs(lat["last"] - 99.2) < 1e-9
    assert abs(lat["high"] - 101.5) < 1e-9
    assert abs(lat["low"] - 99.2) < 1e-9 or abs(lat["low"] - 100.0) < 1e-9
    assert len(lat["prints"]) == 3
    vacio = tank.consumir_latido_lineal("ETHUSDT_LINEAL")
    assert float(vacio.get("last") or 0) == 0.0
    print("  tank vaso latido lineal OK")


def _assert_latido_sugerido() -> None:
    b = BeruShip(uid="M2", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    lento = br.latido_sugerido_s(b, 100.0, lento_s=1.5)
    assert lento >= 1.0
    b.estado = "CAZANDO"
    rap = br.latido_sugerido_s(b, 100.0, lento_s=1.5)
    assert rap <= 0.5
    # Post-Oz: latido rápido junto a sangre_adan, no al wake±1,2 lejano.
    b2 = BeruShip(uid="M2O", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b2, 100.0, activo="ETH")
    br.toca_vacio(b2, 100.0)
    br.armar_tramo_desde_vacio(b2, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b2, 101.2)
    oz = float(b2.oz_adan)
    br.cosechar_oz_y_mover_cero(b2, oz, oz_despliegue=oz)
    sangre_px = float(b2.sangre_adan or 0)
    assert sangre_px > 0
    assert br.latido_sugerido_s(b2, sangre_px * 1.001, lento_s=1.5) <= 0.5
    wake_sangre = 100.0 * (1.0 - br.sangre_contraria_pct())
    if abs(sangre_px - wake_sangre) > 0.2:
        assert br.latido_sugerido_s(b2, wake_sangre, lento_s=1.5) >= 1.0
    print("  latido_sugerido_s OK")


def main() -> int:
    print("=== validar_beru_rango_ojos_smoke ===")
    _assert_mecha_red()
    _assert_misma_vela_sangre_antes_que_red()
    _assert_tank_latido()
    _assert_latido_sugerido()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
