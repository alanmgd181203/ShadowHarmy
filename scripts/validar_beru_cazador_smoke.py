"""Smoke — doctrina Beru Cazador: trailing 0.1%, resolución dinámica, frontera."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_cazador
from core import beru_tier
from core import beru_residual
from core import beru_fusion
from generales.capitanes import CapitanCazador


def test_gatillo_desde_manto():
    vacio = 0.016
    assert beru_cazador.gatillo_pct(vacio) == 0.008
    assert beru_cazador.distancia_gatillo_cumplida(0.008, vacio)
    assert not beru_cazador.distancia_gatillo_cumplida(0.007, vacio)


def test_niveles_primer_toque_trailing_fijo():
    oz, red = beru_cazador.niveles_desde_toque(0.008, paso_oz=0.001, paso_red_clon=0.001)
    assert abs(oz - 0.007) < 1e-9
    assert abs(red - 0.009) < 1e-9


def test_resolucion_dinamica_tier():
    """Mariscal 0.1% clon · Soldado 0.8% clon — trailing oz siempre 0.1%."""
    t_m = beru_tier.tier_por_id("PLENO")
    t_s = beru_tier.tier_por_id("BERUBBY")
    oz_m, red_m = beru_cazador.niveles_desde_toque(
        0.008, paso_oz=t_m.paso_oz_caza, paso_red_clon=t_m.distancia_clon_pct,
    )
    oz_s, red_s = beru_cazador.niveles_desde_toque(
        0.008, paso_oz=t_s.paso_oz_caza, paso_red_clon=t_s.distancia_clon_pct,
    )
    assert abs(oz_m - oz_s) < 1e-9
    assert abs(red_m - 0.009) < 1e-9
    assert abs(red_s - 0.016) < 1e-9


def test_acordeon_red_mueve_ambos():
    oz, red = beru_cazador.mover_niveles_cazador("SHORT", 0.007, 0.009)
    assert abs(oz - 0.008) < 1e-9
    assert abs(red - 0.010) < 1e-9


def test_red_residual_registro():
    b = BeruShip(
        uid="T1", centro_local=1000, centro_manto=1000, masa=35,
        direccion="SHORT", red_adan=1009.0, oz_adan=1007.0, capa=1,
        adn_capitan=CapitanCazador, tier_id="PLENO",
    )
    rr = beru_residual.registrar_desde_barco(b, b.red_adan)
    assert rr is not None
    assert rr.precio == 1009.0
    assert beru_residual.toca_residual(1009.0, rr)
    assert not beru_residual.toca_residual(1008.0, rr)


def test_frontera_solo_red_extrema():
    b1 = BeruShip(
        uid="F1", centro_local=1000, centro_manto=1000, masa=5,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA",
        red_adan=1010.0, oz_adan=1007.0, adn_capitan=CapitanCazador,
    )
    b2 = BeruShip(
        uid="F2", centro_local=1000, centro_manto=1000, masa=5,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA",
        red_adan=1012.0, oz_adan=1008.0, adn_capitan=CapitanCazador,
    )
    legion = [b1, b2]
    assert beru_cazador.es_frontera_red(b2, legion, lambda b: "CAZA")
    assert not beru_cazador.es_frontera_red(b1, legion, lambda b: "CAZA")


def test_fusion_colision_oz():
    centro = 1000.0
    oz_p = beru_cazador.precio_desde_pct(centro, 0.007)
    b1 = BeruShip(
        uid="C1", centro_local=centro, centro_manto=centro, masa=35, masa_congelada=35,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA", ciclo_infinito=True,
        oz_pct=0.007, red_pct=0.009, oz_adan=oz_p, red_adan=1009.0,
        adn_capitan=CapitanCazador,
    )
    b2 = BeruShip(
        uid="C2", centro_local=centro, centro_manto=centro, masa=40, masa_congelada=40,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA", ciclo_infinito=True,
        oz_pct=0.007, red_pct=0.010, oz_adan=oz_p, red_adan=1010.0,
        adn_capitan=CapitanCazador,
    )
    assert beru_fusion.oz_colisionan(b1.oz_adan, b2.oz_adan)
    grupos = beru_fusion.grupos_colision_oz([b1, b2])
    assert len(grupos) == 1
    lider, victimas = beru_fusion.fusionar_colision_oz(grupos[0])
    assert lider.masa_congelada == 75.0
    assert len(victimas) == 1


def test_sin_colision_oz_no_fusiona():
    b1 = BeruShip(
        uid="X1", centro_local=1000, centro_manto=1000, masa=35, masa_congelada=35,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA", ciclo_infinito=True,
        oz_pct=0.007, red_pct=0.009, oz_adan=1007.0, red_adan=1009.0,
        adn_capitan=CapitanCazador,
    )
    b2 = BeruShip(
        uid="X2", centro_local=1000, centro_manto=1000, masa=35, masa_congelada=35,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA", ciclo_infinito=True,
        oz_pct=0.008, red_pct=0.010, oz_adan=1008.0, red_adan=1010.0,
        adn_capitan=CapitanCazador,
    )
    assert not beru_fusion.oz_colisionan(b1.oz_adan, b2.oz_adan)
    assert beru_fusion.grupos_colision_oz([b1, b2]) == []


def main() -> int:
    test_gatillo_desde_manto()
    test_niveles_primer_toque_trailing_fijo()
    test_resolucion_dinamica_tier()
    test_acordeon_red_mueve_ambos()
    test_red_residual_registro()
    test_frontera_solo_red_extrema()
    test_fusion_colision_oz()
    test_sin_colision_oz_no_fusiona()
    print("validar_beru_cazador_smoke: OK (8 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
