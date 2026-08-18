"""Smoke — doctrina Beru Cazador: Vacío 1.1 → Hoz 1.0 · relevo 0.9/0.5/0.3."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import beru_cazador
from core import beru_tier
import core.config as config


def test_llamado_sangre_y_hoz():
    assert abs(beru_cazador.llamado_sangre_pct() - 0.011) < 1e-9
    assert abs(beru_cazador.hoz_productiva_pct() - 0.010) < 1e-9
    assert abs(config.BERU_VACIO_NORMAL - 0.011) < 1e-9
    assert beru_cazador.toca_llamado_sangre(0.011)
    assert not beru_cazador.toca_llamado_sangre(0.010)
    assert not beru_cazador.toca_llamado_sangre(0.009)


def test_niveles_sangre():
    oz, red = beru_cazador.niveles_desde_toque(0.011)
    assert abs(oz - 0.010) < 1e-9
    assert abs(red - 0.012) < 1e-9
    oz_n, red_n = beru_cazador.niveles_desde_toque(-0.011)
    assert abs(oz_n + 0.010) < 1e-9
    assert abs(red_n + 0.012) < 1e-9


def test_engorde_paso_grados():
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
    assert abs(beru_cazador.llamado_relevo_pct(0.012, "SHORT", "CAPITAN") - 0.016) < 1e-9
    assert abs(beru_cazador.llamado_relevo_pct(0.012, "SHORT", "GENERAL") - 0.014) < 1e-9


def test_acordeon_red_mueve_ambos():
    oz, red = beru_cazador.mover_niveles_cazador("SHORT", 0.010, 0.012)
    assert abs(oz - 0.011) < 1e-9
    assert abs(red - 0.013) < 1e-9


def test_tier_relevo_no_caza_clon():
    t_s = beru_tier.tier_por_id("BERUBBY")
    assert abs(t_s.distancia_clon_pct - 0.009) < 1e-9


def test_masa_inicial_peldaños():
    # Mariscal: 10 peldaños × engorde; Soldado: 10 × ~1/8 = 1.25×G_min
    m_m = beru_cazador.capa1_masa_usd(0, "ETH", "MARISCAL")
    m_s = beru_cazador.capa1_masa_usd(0, "ETH", "SOLDADO")
    assert m_m > m_s * 7.5
    paso = beru_cazador.engorde_paso_usd("ETH", "MARISCAL")
    assert abs(m_m - paso * 10) < 0.05


def test_manto_vivo_exige_ls():
    class _Tusk:
        pesos = {}

    assert beru_cazador.manto_vivo(None, "ETH") is False
    t = _Tusk()
    assert beru_cazador.manto_vivo(t, "ETH") is False
    t.pesos = {
        "ETHUSDT_LINEAL": {
            "long": 100.0,
            "short": 100.0,
            "precio_medio_long": 2000.0,
            "precio_medio_short": 2000.0,
        }
    }
    assert beru_cazador.manto_vivo(t, "ETH") is True
    assert beru_cazador.manto_vivo(t, "APT") is False
    # HYPE no bebe HYPER
    t.pesos["HYPERUSDT_LINEAL"] = {
        "long": 0.0,
        "short": 50.0,
        "precio_medio_long": 0.0,
        "precio_medio_short": 0.12,
    }
    t.pesos["HYPEUSD_INVERSE"] = {
        "long": 10.0,
        "short": 0.0,
        "precio_medio_long": 57.5,
        "precio_medio_short": 0.0,
    }
    assert beru_cazador.frente_es_santo("HYPEUSDT_LINEAL", "HYPE") is True
    assert beru_cazador.frente_es_santo("HYPERUSDT_LINEAL", "HYPE") is False
    c = beru_cazador.centro_manto_desde_tusk(t, "HYPE", fallback_global=False)
    assert abs(c - 57.5) < 1e-9
    assert beru_cazador.manto_vivo(t, "HYPER") is True
    assert beru_cazador.manto_vivo(t, "HYPE") is True


def test_manos_mixtas_solo_lista():
    from core import beru_wake
    import core.config as config

    prev_m = bool(config.BERU_MANOS)
    prev_f = bool(config.BERU_MANOS_FANTASMA)
    prev_a = str(getattr(config, "BERU_MANOS_ACTIVOS", "") or "")
    prev_t = str(getattr(config, "BERU_MANOS_EXIGIR_TIER", "PLENO") or "PLENO")
    try:
        config.BERU_MANOS = True
        config.BERU_MANOS_FANTASMA = True
        config.BERU_MANOS_ACTIVOS = "HYPE,LINK,AVAX"
        config.BERU_MANOS_EXIGIR_TIER = "PLENO"
        assert beru_wake.activos_manos_reales() == ["HYPE", "LINK", "AVAX"]
        assert beru_wake.manos_reales_de_activo("HYPE") is True
        assert beru_wake.manos_reales_de_activo("ADA") is False
        assert beru_wake.tier_manos_exigido("HYPE") == "PLENO"
        assert beru_wake.tier_manos_exigido("ADA") is None
        config.BERU_MANOS_EXIGIR_TIER = "AUTO"
        assert beru_wake.tier_manos_exigido("HYPE") is None
    finally:
        config.BERU_MANOS = prev_m
        config.BERU_MANOS_FANTASMA = prev_f
        config.BERU_MANOS_ACTIVOS = prev_a
        config.BERU_MANOS_EXIGIR_TIER = prev_t


def main() -> int:
    test_llamado_sangre_y_hoz()
    test_niveles_sangre()
    test_engorde_paso_grados()
    test_relevo_desde_ultima_tocada()
    test_acordeon_red_mueve_ambos()
    test_tier_relevo_no_caza_clon()
    test_masa_inicial_peldaños()
    test_manto_vivo_exige_ls()
    test_manos_mixtas_solo_lista()
    print("validar_beru_cazador_smoke: OK (Vacío 1.1 · Hoz 1.0 · relevo 0.9/0.5/0.3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
