#!/usr/bin/env python3
"""Smoke Greed↔Igris — ley marcial VIP, toques manto."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import greed_mision as mision
from core import greed_sizing as sizing
from core import manto_touch as mt


class _TuskStub:
    toques_greed_manto = {}


def test_ley_marcial_solo_vip():
    planes = [
        {"oid": "a", "es_vip": False, "notional_usd": 10},
        {"oid": "b", "es_vip": True, "notional_usd": 5},
    ]
    out = mision.filtrar_planes_ley_marcial(planes, 96.0)
    assert len(out) == 1 and out[0]["oid"] == "b"
    pausa, _ = mision.vetos_globales(tank_semaforo="VERDE", margen_ocupado_pct=96, equity=100)
    assert not pausa
    print("  ley marcial VIP OK")


def test_manto_touch():
    t = _TuskStub()
    mt.registrar_toque_greed(t, ["LTCUSDT_LINEAL", "LTCUSDC_LINEAL"], motivo="TEST")
    assert mt.rebalanceo_en_pausa_por_greed(t)
    snap = mt.snapshot_toques(t)
    assert len(snap["activos"]) >= 1
    print("  manto touch OK")


def test_score_manto_ideal():
    assert sizing.score_manto(88) == 0.85
    assert sizing.score_manto(91) == 1.0
    assert sizing.score_manto(96) == 0.0
    print("  score_manto OK")


def main():
    test_ley_marcial_solo_vip()
    test_manto_touch()
    test_score_manto_ideal()
    print("OK greed manto smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
