#!/usr/bin/env python3
"""Smoke — Red no reengorda si pierna del mismo lado ya está gorda."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango as br
from core.models import BeruShip
import core.config as config


def main() -> int:
    print("=== validar_beru_rango_red_pierna_smoke ===")
    os.environ["BERU_RANGO_PERFIL"] = "piedra"
    config.aplicar_perfil_beru_rango("piedra")
    os.environ["BERU_RANGO_RED_TOPE_PIERNA_USD"] = "100"

    b = BeruShip(uid="T_RED", centro_local=1.0, masa=0.0, direccion="", estado="ACECHANDO")
    b.cero_wake = 1.0
    b.ultima_hoz_direccion = "LONG"
    b.red_adan = 0.99
    b.saco_long_usd = 120.0
    b.saco_short_usd = 10.0
    assert br.red_bloqueada_por_pierna(b) is True
    assert br.armar_tramo_desde_red(b, precio=0.99) == 0.0
    print("  saco long 120 >= 100 -> Red bloqueada OK")

    b2 = BeruShip(uid="T_RED2", centro_local=1.0, masa=0.0, direccion="", estado="ACECHANDO")
    b2.cero_wake = 1.0
    b2.ultima_hoz_direccion = "LONG"
    b2.red_adan = 0.99
    b2.saco_long_usd = 20.0
    b2.saco_short_usd = 10.0
    assert br.red_bloqueada_por_pierna(b2) is False
    # Con pierna casa gorda sí bloquea
    assert br.red_bloqueada_por_pierna(b2, pierna_casa_usd=150.0) is True
    print("  pierna_casa 150 bloquea aunque saco chico OK")

    # Sangre no usa este candado (solo Red)
    b3 = BeruShip(uid="T_SG", centro_local=1.0, masa=0.0, direccion="", estado="ACECHANDO")
    b3.cero_wake = 1.0
    b3.ultima_hoz_direccion = "LONG"
    b3.sangre_lado = "ARRIBA"
    b3.sangre_adan = 1.012
    b3.oreja_sangre_activa = True
    b3.es_relevo_cazador = True
    b3.saco_long_usd = 200.0
    masa = br.armar_tramo_desde_sangre(b3, precio=1.012)
    assert masa > 0, masa
    assert str(b3.direccion).upper() == "SHORT"
    print("  sangre contraria sigue armando OK")

    os.environ["BERU_RANGO_RED_TOPE_PIERNA_USD"] = "0"
    assert br.red_bloqueada_por_pierna(b) is False
    print("  tope=0 desactiva candado OK")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
