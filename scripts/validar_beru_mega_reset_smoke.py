"""Smoke — reset Mega Beru: toque red → nuevo 0 + semilla masa 0."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_mega_reset
from core import beru_negociador
from core import beru_cazador
from generales.capitanes import CapitanCazador


def test_debe_resetear_solo_mega_negociando():
    mega = BeruShip(
        uid="M1", centro_local=1000, centro_manto=1000, masa=100, masa_congelada=100,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        ciclo_infinito=True, es_super_beru=True, neg_red_pct=-0.008,
        adn_capitan=CapitanCazador,
    )
    normal = BeruShip(
        uid="N1", centro_local=1000, centro_manto=1000, masa=35, masa_congelada=35,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        ciclo_infinito=True, es_super_beru=False, neg_red_pct=-0.008,
        adn_capitan=CapitanCazador,
    )
    assert beru_mega_reset.debe_resetear_por_red(mega)
    assert not beru_mega_reset.debe_resetear_por_red(normal)


def test_semilla_reinicio_masa_cero_y_nuevo_0():
    precio = 1012.5
    s = beru_mega_reset.crear_semilla_reinicio(
        precio,
        direccion="SHORT",
        tier_id="PROTO1",
        adn_capitan=CapitanCazador,
        generacion=3,
        uid="BERU_MEGA0_TEST",
    )
    assert s.masa == 0.0
    assert s.masa_congelada == 0.0
    assert s.centro_manto == precio
    assert s.centro_local == precio
    assert s.estado == "ACECHANDO"
    assert s.modo_combate == "CAZA"
    assert not s.ciclo_infinito
    assert not s.es_super_beru
    assert s.generacion == 3


def test_mega_red_toca_dispara_reset_no_flip():
    centro = 1000.0
    red_pct = -0.008
    precio_red = beru_cazador.precio_desde_pct(centro, red_pct)
    assert beru_negociador.toca_red_negociador(precio_red, centro, red_pct)


def test_nuevo_0_engorde_desde_gatillo_local():
    """Tras reset, gatillo ±0.8% se mide desde centro_manto local, no Tusk."""
    nuevo_0 = 1012.0
    vacio = 0.016
    gatillo = beru_cazador.gatillo_pct(vacio)
    touch = beru_cazador.pct_desde_precio(nuevo_0, nuevo_0 * (1 + gatillo))
    assert beru_cazador.distancia_gatillo_cumplida(touch, vacio)


def main() -> int:
    test_debe_resetear_solo_mega_negociando()
    test_semilla_reinicio_masa_cero_y_nuevo_0()
    test_mega_red_toca_dispara_reset_no_flip()
    test_nuevo_0_engorde_desde_gatillo_local()
    print("validar_beru_mega_reset_smoke: OK (4 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
