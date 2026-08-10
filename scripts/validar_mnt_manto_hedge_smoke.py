#!/usr/bin/env python3
"""Smoke: bóveda MNT ≠ manto; hedge obligatorio; anti-duplicar contable."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import igris_proteccion as iprot
from core import mnt_manto_hedge as mmh
from core import pase_director as pd


def main() -> None:
    assert "MNT" in mmh.bases_boveda()
    # Con bóveda en lote: MNT es Santo operable
    import core.config as config

    config.IGRIS_BOVEDA_EN_LOTE = True
    config.IGRIS_EXCLUIR_BASES = []
    config.IGRIS_ACTIVOS_EXCLUSIVOS = []
    out = iprot.filtrar_activos_trabajo(["ETH", "HYPE", "MNT", "XRP"])
    assert out == ["ETH", "HYPE", "MNT", "XRP"], out
    # Pausa Monarca: MNT fuera del canal
    config.IGRIS_BOVEDA_EN_LOTE = False
    out2 = iprot.filtrar_activos_trabajo(["ETH", "HYPE", "MNT", "XRP"])
    assert out2 == ["ETH", "HYPE", "XRP"], out2
    assert "MNT" in iprot.bases_excluidas_lote()
    config.IGRIS_BOVEDA_EN_LOTE = True

    # Contable: short inverso no suma al have del pase
    class T:
        pesos = {
            "MNTUSD_INVERSE": {
                "long": 0.0,
                "short": 5000.0,
                "precio_medio_long": 0.0,
                "precio_medio_short": 0.4,
            },
            "MNTUSDT_LINEAL": {
                "long": 0.0,
                "short": 0.0,
                "precio_medio_short": 0.0,
            },
        }

    have_solo_boveda = pd.notional_manto_usd(T(), "MNT")
    assert have_solo_boveda < 1.0, f"bóveda no debe inflar manto: {have_solo_boveda}"

    T.pesos["MNTUSD_INVERSE"]["long"] = 100.0
    T.pesos["MNTUSD_INVERSE"]["precio_medio_long"] = 0.4
    T.pesos["MNTUSDT_LINEAL"]["short"] = 250.0  # qty base @0.4 → 100 USD
    T.pesos["MNTUSDT_LINEAL"]["precio_medio_short"] = 0.4
    have_manto = pd.notional_manto_usd(T(), "MNT")
    # inverse long 100 USD + lineal 100 USD ≈ 200; short bóveda 5000 ignorado
    assert 150.0 < have_manto < 250.0, have_manto

    # Netting prohibido sin hedge
    assert mmh.amenaza_netting_boveda("MNTUSD_INVERSE", "LONG", modo_hedge=False)
    assert not mmh.amenaza_netting_boveda("MNTUSD_INVERSE", "LONG", modo_hedge=True)
    assert mmh.amenaza_netting_boveda("MNTUSD_INVERSE", "SHORT", modo_hedge=True)
    assert mmh.position_idx_para("LONG", hedge=True) == 1
    assert mmh.position_idx_para("SHORT", hedge=True) == 2
    assert ("MNTUSD", "inverse") in mmh.pares_hedge_boveda()
    assert ("MNTUSDT", "linear") in mmh.pares_hedge_boveda()

    # Ventana: strip short bóveda
    limpio = mmh.pesos_sin_boveda_short(T.pesos)
    assert float(limpio["MNTUSD_INVERSE"].get("short") or 0) == 0.0
    assert float(limpio["MNTUSD_INVERSE"].get("long") or 0) == 100.0

    # ETH have no se confunde con MNT
    class Te:
        pesos = {
            "ETHUSD_INVERSE": {"long": 634.0, "precio_medio_long": 1914.0, "short": 0.0},
            "ETHUSDT_LINEAL": {"short": 0.33, "precio_medio_short": 1916.0, "long": 0.0},
            "MNTUSD_INVERSE": {"short": 5000.0, "precio_medio_short": 0.4, "long": 0.0},
        }

    he = pd.notional_manto_usd(Te(), "ETH")
    assert 1200 < he < 1400, he

    print("OK validar_mnt_manto_hedge_smoke")


if __name__ == "__main__":
    main()
