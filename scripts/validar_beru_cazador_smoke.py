"""Smoke — doctrina Beru Cazador 2026-08-13: sangre 0.9 → Hoz 0.8 · engorde por grado · relevo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import beru_cazador
from core import beru_tier


def test_llamado_sangre_y_hoz():
    assert abs(beru_cazador.llamado_sangre_pct() - 0.009) < 1e-9
    assert abs(beru_cazador.hoz_productiva_pct() - 0.008) < 1e-9
    assert beru_cazador.toca_llamado_sangre(0.009)
    assert not beru_cazador.toca_llamado_sangre(0.008)


def test_niveles_sangre():
    oz, red = beru_cazador.niveles_desde_toque(0.009)
    assert abs(oz - 0.008) < 1e-9
    assert abs(red - 0.009) < 1e-9
    oz_n, red_n = beru_cazador.niveles_desde_toque(-0.009)
    assert abs(oz_n + 0.008) < 1e-9
    assert abs(red_n + 0.009) < 1e-9


def test_engorde_paso_grados():
    # Con G_min mock implícito: ratios 1:2:4:8
    s = beru_cazador.engorde_paso_usd("ETH", "SOLDADO")
    c = beru_cazador.engorde_paso_usd("ETH", "CAPITAN")
    g = beru_cazador.engorde_paso_usd("ETH", "GENERAL")
    m = beru_cazador.engorde_paso_usd("ETH", "MARISCAL")
    assert abs(m / s - 8.0) < 0.05 or abs(m - 8 * s) < 0.1
    assert abs(m / c - 4.0) < 0.05 or abs(m - 4 * c) < 0.1
    assert abs(m / g - 2.0) < 0.05 or abs(m - 2 * g) < 0.1


def test_relevo_desde_ultima_tocada():
    # Red plantada 1.2% → tocada 1.1% → Soldado +0.9 → llamado 2.0%
    llamado = beru_cazador.llamado_relevo_pct(0.012, "SHORT", "SOLDADO")
    assert abs(llamado - 0.020) < 1e-9
    # Capitán +0.5 → 1.6%
    assert abs(beru_cazador.llamado_relevo_pct(0.012, "SHORT", "CAPITAN") - 0.016) < 1e-9
    # General +0.3 → 1.4%
    assert abs(beru_cazador.llamado_relevo_pct(0.012, "SHORT", "GENERAL") - 0.014) < 1e-9


def test_acordeon_red_mueve_ambos():
    oz, red = beru_cazador.mover_niveles_cazador("SHORT", 0.008, 0.009)
    assert abs(oz - 0.009) < 1e-9
    assert abs(red - 0.010) < 1e-9


def test_tier_relevo_no_caza_clon():
    t_s = beru_tier.tier_por_id("BERUBBY")
    assert abs(t_s.distancia_clon_pct - 0.009) < 1e-9


def test_masa_inicial_peldaños():
    # Mariscal: 8 × G_min; Soldado: ≈ G_min
    m_m = beru_cazador.capa1_masa_usd(0, "ETH", "MARISCAL")
    m_s = beru_cazador.capa1_masa_usd(0, "ETH", "SOLDADO")
    assert m_m > m_s * 7.5  # ~8×
    paso = beru_cazador.engorde_paso_usd("ETH", "MARISCAL")
    assert abs(m_m - paso * 8) < 0.05


def main() -> int:
    test_llamado_sangre_y_hoz()
    test_niveles_sangre()
    test_engorde_paso_grados()
    test_relevo_desde_ultima_tocada()
    test_acordeon_red_mueve_ambos()
    test_tier_relevo_no_caza_clon()
    test_masa_inicial_peldaños()
    print("validar_beru_cazador_smoke: OK (sangre 0.9 · Hoz 0.8 · masa $40 Mariscal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
