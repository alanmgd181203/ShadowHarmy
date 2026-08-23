#!/usr/bin/env python3
"""Smoke frío — fill spot de la casa = última Oz, sin botín ni dual Vacío."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_continuo as bc
from generales.capitanes import CapitanNormal


def _cazando() -> BeruShip:
    return BeruShip(
        uid="BERU_SEM_NEAR_R3_TEST",
        centro_local=1.60,
        centro_manto=1.60,
        ancla_tramo=1.60,
        masa=12.5,
        direccion="SHORT",
        estado="CAZANDO",
        oz_adan=1.668,
        red_adan=1.672,
        frente_asignado="NEARUSDT_SPOT",
        tier_id="BERUBBY",
        modo_combate="CAZA",
        altar_link_id="HOZ_VIEJA",
        altar_rependiente=True,
        cosechas_continuas=4,
        ultima_red_tocada_precio=1.672,
        ultima_red_tocada_pct=0.045,
        adn_capitan=CapitanNormal,
    )


def main() -> int:
    b = _cazando()
    assert bc.activo_de_barco(b) == "NEAR"
    ok = bc.alinear_acecho_con_oz_fill(b, precio=1.684, side="Sell", grado="SOLDADO")
    assert ok
    assert b.estado == "ACECHANDO"
    assert b.direccion == "SHORT"
    assert b.masa == 0.0
    assert b.oz_adan == 0.0
    assert b.altar_link_id == ""
    assert b.altar_rependiente is False
    assert b.cosechas_continuas == 4
    assert not bc.sangre_dual(b)
    assert b.es_relevo_cazador is True
    assert abs(b.ultima_hoz_tocada_precio - 1.684) < 1e-9
    assert abs(b.ancla_tramo - 1.684) < 1e-9
    sangre = bc.precio_sangre_contraria(b)
    assert sangre < 1.684
    assert abs(sangre - (1.684 - 1.60 * 0.011)) < 1e-9
    assert bc.precio_oreja_red(b) > 1.684

    buy = _cazando()
    buy.uid = "BERU_SEM_ETH_R1_TEST"
    buy.frente_asignado = "ETHUSDT_SPOT"
    bc.alinear_acecho_con_oz_fill(buy, precio=3200.0, side="Buy", grado="SOLDADO")
    assert buy.direccion == "LONG"
    assert bc.precio_sangre_contraria(buy) > 3200.0
    assert abs(buy.ultima_red_tocada_precio - 3200.0) < 1e-9

    mar = _cazando()
    mar.tier_id = "MARISCAL"
    bc.alinear_acecho_con_oz_fill(mar, precio=1.684, side="Sell", grado="MARISCAL")
    assert mar.es_relevo_cazador is True
    assert mar.oreja_sangre_activa is True
    assert mar.oreja_red_activa is True
    assert bc.precio_sangre_contraria(mar) < 1.684
    assert bc.precio_oreja_red(mar) > 1.684
    assert mar.estado == "ACECHANDO"

    huerfano = _cazando()
    huerfano.oz_adan = 0.0
    huerfano.red_adan = 0.0
    huerfano.altar_link_id = ""
    inf = bc.preparar_legion_tras_manos_casa([huerfano], {})
    assert inf.get("NEAR") == "caza_huerfana"
    assert huerfano.estado == "ACECHANDO"
    assert huerfano.oz_adan == 0.0
    assert huerfano.masa == 0.0

    viva = _cazando()
    viva.altar_order_status = "Untriggered"
    assert bc.carta_hoz_viva(viva) is True
    inf_v = bc.preparar_legion_tras_manos_casa(
        [viva],
        {"NEAR": {"precio": 1.70, "side": "Buy", "ts": 200.0, "piso_ts": 100.0}},
    )
    assert inf_v.get("NEAR") == "caza_viva"
    assert viva.estado == "CAZANDO"
    assert abs(viva.oz_adan - 1.668) < 1e-9

    ghost = _cazando()
    ghost.altar_order_status = "Deactivated"
    assert bc.carta_hoz_viva(ghost) is False
    inf_g = bc.preparar_legion_tras_manos_casa(
        [ghost],
        {"NEAR": {"precio": 1.70, "side": "Buy", "ts": 200.0, "piso_ts": 100.0}},
    )
    assert inf_g.get("NEAR") == "caza_sin_carta"
    assert ghost.estado == "CAZANDO"
    assert abs(ghost.oz_adan - 1.668) < 1e-9

    viejo = _cazando()
    viejo.oz_adan = 0.0
    viejo.altar_link_id = ""
    inf2 = bc.preparar_legion_tras_manos_casa(
        [viejo],
        {"NEAR": {"precio": 1.50, "side": "Sell", "ts": 10.0, "piso_ts": 100.0}},
    )
    assert inf2.get("NEAR") == "caza_huerfana"

    semilla = _cazando()
    semilla.estado = "ACECHANDO"
    semilla.oz_adan = 0.0
    semilla.altar_link_id = ""
    semilla.ultima_hoz_tocada_precio = 0.0
    inf3 = bc.preparar_legion_tras_manos_casa(
        [semilla],
        {"NEAR": {"precio": 1.70, "side": "Buy", "ts": 200.0, "piso_ts": 100.0}},
    )
    assert inf3.get("NEAR") == "oz_casa"
    assert semilla.direccion == "LONG"
    assert not bc.sangre_dual(semilla)
    assert abs(semilla.ultima_hoz_tocada_precio - 1.70) < 1e-9
    print("PASS oz_casa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
