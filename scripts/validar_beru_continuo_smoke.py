#!/usr/bin/env python3
"""Smoke frío — núcleo Beru cazador continuo (Vacío 1.1 · Hoz 1.0 · 0 de wake)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_continuo as bc
from generales.capitanes import CapitanNormal


def _beru(local: float = 100.0, manto: float = 100.0) -> BeruShip:
    return BeruShip(
        uid="BERU_SEM_TEST_1",
        centro_local=local,
        centro_manto=manto,
        ancla_tramo=local,
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        adn_capitan=CapitanNormal,
        modo_combate="CAZA",
        sangre_vista_dentro=False,
    )


def main() -> int:
    b = _beru()
    assert bc.es_primer_tramo(b)
    assert abs(bc.distancia_llamado_pct(b) - 0.011) < 1e-9
    assert abs(bc.distancia_hoz_pct(b) - 0.010) < 1e-9
    assert abs(bc.vacio_adan_pct(b) - 0.011) < 1e-9
    # Nació ya fuera: no detona hasta volver a entrar.
    assert not bc.toca_llamado(b, 101.3)
    assert not bc.toca_llamado(_beru(), 100.8)
    assert bc.toca_llamado(b, 100.0) is False  # marca visto_dentro
    assert not bc.toca_llamado(b, 100.9)
    assert not bc.toca_llamado(b, 101.0)
    assert bc.toca_llamado(b, 101.1)

    with patch("core.beru_cazador.engorde_paso_usd", return_value=5.0):
        assert abs(bc.armar_tramo(b, 101.1, activo="TEST", grado="MARISCAL") - 50.0) < 1e-9
        assert b.estado == "CAZANDO"
        assert b.direccion == "SHORT"
        assert round(b.oz_adan, 6) == 101.0
        assert round(b.red_adan, 6) == 101.2
        bc.avanzar_frontera(b, 5.0)
        assert b.masa == 55.0
        assert round(b.oz_adan, 6) == 101.1
        assert round(b.red_adan, 6) == 101.3

        try:
            bc.reiniciar_tras_cosecha(b, 101.1)
            raise AssertionError("debía bloquear reinicio fósil")
        except RuntimeError as exc:
            assert "FOSIL_BLOQUEADO" in str(exc)

        # Nacer lejos no persigue el precio: Hoz/Red siguen siendo las del Vacío.
        tarde = _beru()
        masa = bc.armar_tramo(tarde, 103.35, activo="TEST", grado="MARISCAL")
        assert tarde.centro_manto == 100.0
        assert tarde.ancla_tramo == 100.0
        assert round(tarde.oz_adan, 6) == 101.0
        assert round(tarde.red_adan, 6) == 101.2
        assert round(masa, 6) == 50.0

        # Tumor: el 0 de wake no es el manto. Metro 100, nace en 130.
        lejos = _beru(local=130.0, manto=100.0)
        assert abs(bc.pct_desde_ancla(lejos, 130.0)) < 1e-12
        assert not bc.toca_llamado(lejos, 130.0)
        assert not bc.toca_llamado(lejos, 130.9)
        assert bc.toca_llamado(lejos, 131.1)
        masa_lejos = bc.armar_tramo(lejos, 131.1, activo="TEST", grado="MARISCAL")
        assert lejos.direccion == "SHORT"
        assert round(lejos.oz_adan, 6) == 131.0
        assert round(lejos.red_adan, 6) == 131.2
        assert round(masa_lejos, 6) == 50.0
        # Igris mueve el metro: el 0 local de acecho no se pisa.
        acecho = _beru(local=130.0, manto=100.0)
        assert bc.aplicar_cero_manto(acecho, 110.0) is True
        assert acecho.centro_manto == 110.0
        assert acecho.ancla_tramo == 130.0
        assert acecho.centro_local == 130.0
        abajo = _beru(local=130.0, manto=100.0)
        assert bc.toca_llamado(abajo, 130.0) is False
        assert bc.toca_llamado(abajo, 128.9)
        bc.armar_tramo(abajo, 128.9, activo="TEST", grado="MARISCAL")
        assert abajo.direccion == "LONG"
        assert round(abajo.oz_adan, 6) == 129.0
        assert round(abajo.red_adan, 6) == 128.8

    b.direccion = "SHORT"
    b.centro_manto = 57.5
    b.precio_entrada_real = 59.281
    merma = bc.beneficio_cosecha_pct(b, 59.579)
    assert merma < 0
    assert abs(merma) > 0.004
    b.precio_entrada_real = 0.0
    b.oz_adan = 58.19
    assert abs(bc.beneficio_desde_manto_pct(b, 58.19) - (58.19 - 57.5) / 57.5) < 1e-9

    print("OK validar_beru_continuo_smoke (Vacío 1.1 · Hoz 1.0 · 0 de wake · metro manto)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
