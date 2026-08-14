"""Smoke — negociador ping-pong: oro 1.6 · trailing única · sin acordeón."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import beru_negociador


def test_abismo_1_6():
    assert abs(beru_negociador.abismo_salida_pct() - 0.016) < 1e-9
    assert abs(beru_negociador.oz_condicional_pct(0.008) + 0.008) < 1e-9


def test_trailing_unica_sin_acordeon():
    oz, red = beru_negociador.activar_trailing_unica(-0.008)
    assert abs(oz + 0.008) < 1e-9
    assert red == 0.0
    p_oz, p_red = beru_negociador.pasos_negociador("BERUBBY")
    assert abs(p_oz - p_red) < 1e-12
    assert beru_negociador.es_sexto_toque(5) is False
    assert beru_negociador.toques_hasta_resorte() == 0


def test_ping_pong_orilla():
    # Fill en +0.8% → oro en -0.8%
    oro = beru_negociador.oro_orilla_opuesta(0.008)
    assert abs(oro + 0.008) < 1e-9
    # Fill en -0.8% → oro en +0.8%
    oro2 = beru_negociador.oro_orilla_opuesta(-0.008)
    assert abs(oro2 - 0.008) < 1e-9


def test_ping_pong_ciclo():
    fill = 0.008
    oro = beru_negociador.oro_orilla_opuesta(fill)
    trail, red = beru_negociador.activar_trailing_unica(oro)
    assert red == 0.0
    fill2 = trail
    oro2 = beru_negociador.oro_orilla_opuesta(fill2)
    assert abs(oro2 - 0.008) < 1e-9


def main() -> int:
    test_abismo_1_6()
    test_trailing_unica_sin_acordeon()
    test_ping_pong_orilla()
    test_ping_pong_ciclo()
    print("validar_beru_negociador_smoke: OK (ping-pong · sin acordeón)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
