"""Smoke — fusión colisión oz + Mega Beru (promedio manto)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_fusion
from core import beru_cazador
from generales.capitanes import CapitanCazador


def _barco(
    uid: str,
    ancla: float,
    *,
    estado: str = "ESPERANDO_CONDICIONAL",
    masa: float = 35.0,
    neg_oz: float = 0.0,
    neg_red: float = 0.0,
) -> BeruShip:
    return BeruShip(
        uid=uid,
        centro_local=1000.0,
        masa=masa,
        masa_congelada=masa,
        direccion="SHORT",
        estado=estado,
        modo_combate="NEGOCIADOR" if estado == "NEGOCIANDO" else "NEGOCIADOR",
        ciclo_infinito=True,
        ancla_cosecha_pct=ancla,
        neg_oz_pct=neg_oz,
        neg_red_pct=neg_red,
        adn_capitan=CapitanCazador,
    )


def test_mega_beru_promedio():
    anclas = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10]
    barcos = [_barco(f"B{i}", a) for i, a in enumerate(anclas)]
    grupos = beru_fusion.grupos_mega_beru(barcos)
    assert len(grupos) == 1
    lider, victimas, prom = grupos[0]
    assert abs(prom - 0.05) < 1e-9
    assert len(victimas) == 2
    beru_fusion.aplicar_mega_beru(lider, victimas, prom, 0.016)
    assert lider.masa_congelada == 35.0 * 3
    assert lider.estado == "ESPERANDO_CONDICIONAL"
    assert lider.es_super_beru


def test_fusion_colision_misma_hoz():
    centro = 1000.0
    oz_p = beru_cazador.precio_desde_pct(centro, -0.01)
    b1 = _barco(
        "N1", 0.01, estado="NEGOCIANDO", masa=35.0,
        neg_oz=-0.01, neg_red=-0.008,
    )
    b2 = _barco(
        "N2", 0.012, estado="NEGOCIANDO", masa=40.0,
        neg_oz=-0.009, neg_red=-0.007,
    )
    b1.oz_adan = oz_p
    b2.oz_adan = oz_p
    grupos = beru_fusion.grupos_colision_oz([b1, b2])
    assert len(grupos) == 1
    lider, victimas = beru_fusion.fusionar_colision_oz(grupos[0])
    assert lider.masa_congelada == 75.0
    assert len(victimas) == 1


def test_sin_colision_no_fusiona():
    b1 = _barco("N1", 0.01, estado="NEGOCIANDO", neg_oz=-0.01, neg_red=-0.008)
    b2 = _barco("N2", 0.012, estado="NEGOCIANDO", neg_oz=-0.009, neg_red=-0.007)
    b1.oz_adan = 990.0
    b2.oz_adan = 991.5
    assert beru_fusion.grupos_colision_oz([b1, b2]) == []


def test_caza_fantasma_colision():
    centro = 1000.0
    oz_p = beru_cazador.precio_desde_pct(centro, 0.007)
    b1 = BeruShip(
        uid="C1", centro_local=centro, masa=35, masa_congelada=35, direccion="SHORT",
        estado="NEGOCIANDO", modo_combate="CAZA", ciclo_infinito=True,
        oz_pct=0.007, red_pct=0.009, oz_adan=oz_p, adn_capitan=CapitanCazador,
    )
    b2 = BeruShip(
        uid="C2", centro_local=centro, masa=35, masa_congelada=35, direccion="SHORT",
        estado="NEGOCIANDO", modo_combate="CAZA", ciclo_infinito=True,
        oz_pct=0.007, red_pct=0.009, oz_adan=oz_p, adn_capitan=CapitanCazador,
    )
    grupos = beru_fusion.grupos_colision_oz([b1, b2])
    assert len(grupos) == 1
    lider, victimas = beru_fusion.fusionar_colision_oz(grupos[0])
    assert lider.masa_congelada == 70.0


def main() -> int:
    test_mega_beru_promedio()
    test_fusion_colision_misma_hoz()
    test_sin_colision_no_fusiona()
    test_caza_fantasma_colision()
    print("validar_beru_fusion_smoke: OK (4 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
