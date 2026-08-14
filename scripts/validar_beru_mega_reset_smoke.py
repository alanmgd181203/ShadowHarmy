"""Smoke — Mega purga: NO mueve 0 Igris · sangre abs pct_purga+0.9%."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_mega_reset
from core import beru_cazador
from generales.capitanes import CapitanCazador


def test_debe_purgar_solo_mega():
    mega = BeruShip(
        uid="M1", centro_local=1000, centro_manto=1000, masa=100, masa_congelada=100,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        ciclo_infinito=True, es_super_beru=True, neg_oz_pct=-0.008,
        adn_capitan=CapitanCazador,
    )
    normal = BeruShip(
        uid="N1", centro_local=1000, centro_manto=1000, masa=35, masa_congelada=35,
        direccion="SHORT", estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
        ciclo_infinito=True, es_super_beru=False, neg_oz_pct=-0.008,
        adn_capitan=CapitanCazador,
    )
    assert beru_mega_reset.debe_purgar_mega(mega)
    assert not beru_mega_reset.debe_purgar_mega(normal)


def test_semilla_conserva_0_igris():
    centro_igris = 100.0
    s = beru_mega_reset.crear_semilla_post_purga(
        centro_igris,
        pct_purga=0.30,
        direccion="SHORT",
        tier_id="PROTO1",
        adn_capitan=CapitanCazador,
        generacion=3,
        uid="BERU_MEGA0_TEST",
    )
    assert s.masa == 0.0
    assert s.centro_manto == centro_igris  # NO 130
    assert s.centro_local == centro_igris
    assert abs(s.piso_sangre_pct - 0.309) < 1e-9  # +30.9%
    assert s.estado == "ACECHANDO"
    assert s.modo_combate == "CAZA"


def test_sangre_abs_desde_purga():
    assert abs(beru_mega_reset.sangre_abs_desde_purga(0.30) - 0.309) < 1e-9
    assert abs(beru_mega_reset.sangre_abs_desde_purga(-0.30) + 0.309) < 1e-9


def test_niveles_post_mega_no_rebases():
    oz, red = beru_cazador.niveles_desde_toque(0.309)
    assert abs(oz - 0.308) < 1e-9
    assert abs(red - 0.309) < 1e-9


def main() -> int:
    test_debe_purgar_solo_mega()
    test_semilla_conserva_0_igris()
    test_sangre_abs_desde_purga()
    test_niveles_post_mega_no_rebases()
    print("validar_beru_mega_reset_smoke: OK (purga · 0 Igris intacto)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
