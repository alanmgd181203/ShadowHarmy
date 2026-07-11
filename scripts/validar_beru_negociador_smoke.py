"""Smoke — Beru Negociador post-cazador (abismo, condicional, 5 toques + resorte)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import beru_negociador


def test_abismo_desde_cosecha_cazador():
    """Salida fija −2% desde ancla (doctrina Monarca)."""
    ancla = 0.079
    cond = beru_negociador.oz_condicional_pct(ancla)
    assert abs(cond - 0.059) < 1e-9
    assert abs(beru_negociador.abismo_salida_pct() - 0.02) < 1e-9


def test_adan_cerca_trigger():
    assert beru_negociador.precio_cerca_de_trigger(100.0, 100.4, 0.005)
    assert not beru_negociador.precio_cerca_de_trigger(100.0, 101.0, 0.005)


def test_primera_activacion_orden_inverso():
    paso = 0.001
    oz, red = beru_negociador.activar_primera_vez(-0.009, paso)
    assert abs(oz + 0.010) < 1e-9
    assert abs(red + 0.008) < 1e-9
    assert red > oz


def test_cinco_toques_sin_engorde():
    paso_oz, paso_red = 0.001, 0.0005
    oz, red = -0.010, -0.008
    esperados = [
        (-0.011, -0.0085),
        (-0.012, -0.0090),
        (-0.013, -0.0095),
        (-0.014, -0.0100),
        (-0.015, -0.0105),
    ]
    for i, (e_oz, e_red) in enumerate(esperados, start=1):
        oz, red = beru_negociador.avanzar_toque_oz(oz, red, paso_oz, paso_red)
        assert abs(oz - e_oz) < 1e-9, f"toque {i} oz"
        assert abs(red - e_red) < 1e-9, f"toque {i} red"


def test_resorte_sexto_toque():
    paso = 0.001
    oz, red = beru_negociador.resorte_sexto_toque(-0.015, paso)
    assert abs(oz + 0.017) < 1e-9
    assert abs(red + 0.015) < 1e-9


def test_escenario_monarca_completo():
    """Cosecha +0.7% → cond −1.3% (−2%) → activar → 5 toques → resorte."""
    ancla = 0.007
    paso_oz, paso_red = 0.001, 0.0005
    cond = beru_negociador.oz_condicional_pct(ancla)
    assert abs(cond + 0.013) < 1e-9
    oz, red = beru_negociador.activar_primera_vez(cond, paso_oz)
    toques = 0
    for _ in range(5):
        oz, red = beru_negociador.avanzar_toque_oz(oz, red, paso_oz, paso_red)
        toques += 1
    assert toques == 5
    assert beru_negociador.es_sexto_toque(toques)
    oz, red = beru_negociador.resorte_sexto_toque(oz, paso_oz)
    assert abs(oz + 0.021) < 1e-9
    assert abs(red + 0.019) < 1e-9


def test_red_negociador_equivale_oz_caza():
    centro = 1000.0
    _, red = beru_negociador.activar_primera_vez(-0.009, 0.001)
    assert abs(red + 0.008) < 1e-9
    assert beru_negociador.toca_red_negociador(1008.0, centro, red)


def test_ciclo_infinito_flips():
    ancla = 0.007
    cond = beru_negociador.oz_condicional_pct(ancla)
    assert abs(cond + 0.013) < 1e-9
    centro = 1000.0
    vacio = 0.016
    assert beru_negociador.cruzo_gatillo_caza(1008.0, centro, vacio, "SHORT")


def main() -> int:
    test_abismo_desde_cosecha_cazador()
    test_adan_cerca_trigger()
    test_primera_activacion_orden_inverso()
    test_cinco_toques_sin_engorde()
    test_resorte_sexto_toque()
    test_escenario_monarca_completo()
    test_red_negociador_equivale_oz_caza()
    test_ciclo_infinito_flips()
    print("validar_beru_negociador_smoke: OK (8 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
