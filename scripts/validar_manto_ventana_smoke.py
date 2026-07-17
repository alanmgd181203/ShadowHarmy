#!/usr/bin/env python3
"""Smoke ventana 48–52 / long-primero — core/manto_ventana.py"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import manto_ventana as mv  # noqa: E402


def main() -> int:
    assert mv.ventana_activa()
    assert mv.dentro_ventana(0.50)
    assert mv.dentro_ventana(0.52)
    assert mv.dentro_ventana(0.49)
    assert not mv.dentro_ventana(0.53)
    assert not mv.dentro_ventana(0.48)  # operativo: piso 49%
    assert mv.dentro_ventana(0.48, operativo=False)  # hard permite 48
    assert not mv.dentro_ventana(0.47, operativo=False)

    assert mv.clasificar_ratio(0.53) == "LONG_EXCEDIDO"
    assert mv.clasificar_ratio(0.485) == "SHORT_EXCEDIDO"
    assert mv.clasificar_ratio(0.47) == "FUERA_HARD"
    assert mv.clasificar_ratio(0.51) == "OK"

    assert mv.direccion_engorde_preferida(0, 0) == "LONG"
    assert mv.direccion_engorde_preferida(48, 52) == "LONG"  # short gordo
    assert mv.direccion_correccion(0.53) == "SHORT"

    # Acoplar long para no pasar 52 con short=48 → max long = 52/48 * 48 = 52
    capped = mv.acoplar_pierna_usd(60, 48, propuesta_es_long=True)
    assert capped <= 52.01

    r = mv.resumen_barco(52, 48)
    assert r["ok"] and r["ley"] == "ventana_48_52_long_primero"
    print("OK manto_ventana (ventana 48-52 / long-primero)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
