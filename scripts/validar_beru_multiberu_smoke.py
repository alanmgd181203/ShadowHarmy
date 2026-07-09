"""Smoke multi-Beru — colisión oz estricta + Mega Beru intacto."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_fusion
from core import beru_negociador
from core import beru_cazador
from generales.capitanes import CapitanCazador

VACIO = 0.016
PASO_OZ = 0.001
CENTRO = 1000.0


def _base(uid: str, **kw) -> BeruShip:
    d = dict(
        uid=uid,
        centro_local=CENTRO,
        centro_manto=CENTRO,
        masa=35.0,
        masa_congelada=35.0,
        direccion="SHORT",
        ciclo_infinito=True,
        adn_capitan=CapitanCazador,
    )
    d.update(kw)
    return BeruShip(**d)


def test_dos_negociadores_colisionan_si_misma_hoz():
    ancla_a, ancla_b = 0.01, 0.012
    cond_a = beru_negociador.oz_condicional_pct(ancla_a, VACIO)
    cond_b = beru_negociador.oz_condicional_pct(ancla_b, VACIO)
    oz_a, red_a = beru_negociador.activar_primera_vez(cond_a, PASO_OZ)
    oz_b, red_b = beru_negociador.activar_primera_vez(cond_b, PASO_OZ)
    oz_p = beru_cazador.precio_desde_pct(CENTRO, oz_a)

    ba = _base(
        "B1", ancla_cosecha_pct=ancla_a, estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        neg_oz_pct=oz_a, neg_red_pct=red_a, oz_adan=oz_p,
    )
    bb = _base(
        "B2", ancla_cosecha_pct=ancla_b, estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        neg_oz_pct=oz_b, neg_red_pct=red_b, oz_adan=oz_p,
    )
    grupos = beru_fusion.grupos_colision_oz([ba, bb])
    assert len(grupos) == 1
    lider, victimas = beru_fusion.fusionar_colision_oz(grupos[0])
    assert lider.masa_congelada == 70.0


def test_dos_negociadores_sin_colision_no_fusionan():
    ancla_a, ancla_b = 0.01, 0.012
    cond_a = beru_negociador.oz_condicional_pct(ancla_a, VACIO)
    cond_b = beru_negociador.oz_condicional_pct(ancla_b, VACIO)
    oz_a, red_a = beru_negociador.activar_primera_vez(cond_a, PASO_OZ)
    oz_b, red_b = beru_negociador.activar_primera_vez(cond_b, PASO_OZ)

    ba = _base(
        "B1", ancla_cosecha_pct=ancla_a, estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        neg_oz_pct=oz_a, neg_red_pct=red_a,
        oz_adan=beru_cazador.precio_desde_pct(CENTRO, oz_a),
    )
    bb = _base(
        "B2", ancla_cosecha_pct=ancla_b, estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        neg_oz_pct=oz_b, neg_red_pct=red_b,
        oz_adan=beru_cazador.precio_desde_pct(CENTRO, oz_b),
    )
    assert beru_fusion.grupos_colision_oz([ba, bb]) == []


def test_dos_caza_fantasma_colisionan():
    oz_p = beru_cazador.precio_desde_pct(CENTRO, 0.007)
    ba = _base(
        "C1", estado="NEGOCIANDO", modo_combate="CAZA",
        oz_pct=0.007, red_pct=0.009, oz_adan=oz_p,
    )
    bb = _base(
        "C2", estado="NEGOCIANDO", modo_combate="CAZA",
        oz_pct=0.008, red_pct=0.010, masa=40.0, masa_congelada=40.0, oz_adan=oz_p,
    )
    grupos = beru_fusion.grupos_colision_oz([ba, bb])
    assert len(grupos) == 1
    lider, _ = beru_fusion.fusionar_colision_oz(grupos[0])
    assert lider.masa_congelada == 75.0


def test_esperando_abismo_no_fusiona():
    ba = _base("A1", estado="ESPERANDO_ABISMO", modo_combate="CAZA")
    bb = _base("A2", estado="ESPERANDO_ABISMO", modo_combate="CAZA")
    assert beru_fusion.grupos_colision_oz([ba, bb]) == []


def test_mega_beru_intacto():
    barcos = [_base(f"M{i}", estado="ESPERANDO_CONDICIONAL", ancla_cosecha_pct=a)
              for i, a in enumerate([0.0, 0.02, 0.04, 0.06, 0.08, 0.10])]
    assert len(beru_fusion.grupos_mega_beru(barcos)) == 1


def main() -> int:
    test_dos_negociadores_colisionan_si_misma_hoz()
    test_dos_negociadores_sin_colision_no_fusionan()
    test_dos_caza_fantasma_colisionan()
    test_esperando_abismo_no_fusiona()
    test_mega_beru_intacto()
    print("validar_beru_multiberu_smoke: OK (5 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
