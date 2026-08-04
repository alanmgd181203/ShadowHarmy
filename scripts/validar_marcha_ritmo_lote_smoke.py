#!/usr/bin/env python3
"""Smoke marcha_ritmo_lote — reloj del lote táctico/forzada."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import marcha_ritmo_lote as mrl
from core import pase_director as pd


def main() -> int:
    print("[SMOKE] marcha_ritmo_lote")
    assert mrl.aplica_marcha("tactico")
    assert mrl.aplica_marcha("marcha_forzada")
    assert not mrl.aplica_marcha("asalto")
    assert not mrl.aplica_marcha("personalizado")

    clock = mrl.estimar_reloj_lote({"ETH": 14.0}, "tactico")
    assert "reloj_eta_h" in clock
    # sin muestras: ok puede ser False; umbral_ritmo aún devuelve piso
    u = mrl.umbral_ritmo_par("ETH", "tactico", meta_usd=14.0, reloj_eta_h=48.0)
    assert u["modo_paciencia"].startswith("ritmo_lote_")
    assert u["umbral_pct"] >= 0
    assert u["force_market"] is False

    um = pd.umbral_por_marcha(0.10, marcha_id="asalto", base="ETH")
    assert um["umbral_pct"] == 0.0 and um["force_market"] is True
    up = pd.umbral_por_marcha(0.10, marcha_id="personalizado", base="ETH")
    assert up["modo_paciencia"] == "marcha_personalizado"
    print("[OK] marcha_ritmo_lote")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
