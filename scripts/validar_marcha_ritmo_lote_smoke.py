#!/usr/bin/env python3
"""Smoke marcha_ritmo_lote — módulo legado inactivo (2 marchas: asalto/personalizado)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import marcha_ritmo_lote as mrl
from core import pase_director as pd


def main() -> int:
    print("[SMOKE] marcha_ritmo_lote (legado dormido)")
    # Sello 2 marchas: nada usa ritmo; legado → asalto
    assert pd.normalizar_marcha("tactico") == "asalto"
    assert pd.normalizar_marcha("marcha_forzada") == "asalto"
    assert not mrl.aplica_marcha("tactico")
    assert not mrl.aplica_marcha("marcha_forzada")
    assert not mrl.aplica_marcha("asalto")
    assert not mrl.aplica_marcha("personalizado")
    assert mrl.MARCHAS_RITMO == frozenset()

    clock = mrl.estimar_reloj_lote({"ETH": 14.0}, "asalto")
    assert clock.get("ok") is False
    assert clock.get("motivo") == "marcha_sin_ritmo"

    um = pd.umbral_por_marcha(0.10, marcha_id="asalto", base="ETH")
    assert um["umbral_pct"] == 0.0 and um["force_market"] is True
    up = pd.umbral_por_marcha(0.10, marcha_id="personalizado", base="ETH")
    assert up["modo_paciencia"] == "marcha_personalizado"
    print("[OK] marcha_ritmo_lote")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
