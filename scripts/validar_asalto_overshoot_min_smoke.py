#!/usr/bin/env python3
"""Smoke: Asalto mordida = mínimo real Santo; OK pasarse meta (polvo)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import igris_despliegue as ides


def main() -> None:
    config.IGRIS_ASALTO_OVERSHOOT_META = True
    # Libro profundo (inversos: qty≈USD nocional; lineales: qty*px)
    bids_l = [[100.0, 5000.0]]
    asks_l = [[100.1, 5000.0]]
    bids_s = [[100.0, 50.0]]
    asks_s = [[100.1, 50.0]]
    fl, fs = "ETHUSD_INVERSE", "ETHUSDT_LINEAL"
    piso = 19.0  # Alfa típico ETH
    # Sin overshoot: restante 3 < piso → techo falla
    t0 = ides.techo_mision_usd(
        bids_long=bids_l, asks_long=asks_l,
        bids_short=bids_s, asks_short=asks_s,
        frente_long=fl, frente_short=fs,
        restante_mision_usd=3.0,
        permitir_overshoot_min=False,
        piso_mordida_usd=piso,
    )
    assert t0["ok_techo"] is False, t0

    # Con overshoot Asalto: techo = piso, OK
    t1 = ides.techo_mision_usd(
        bids_long=bids_l, asks_long=asks_l,
        bids_short=bids_s, asks_short=asks_s,
        frente_long=fl, frente_short=fs,
        restante_mision_usd=3.0,
        permitir_overshoot_min=True,
        piso_mordida_usd=piso,
    )
    assert t1["ok_techo"] is True, t1
    assert t1["overshoot_meta"] is True
    assert abs(float(t1["techo_usd"]) - piso) < 1e-6, t1
    assert float(t1["piso_mordida_usd"]) >= piso - 1e-6

    # Resto holgado: no overshoot; techo = restante si libro ≥
    t2 = ides.techo_mision_usd(
        bids_long=bids_l, asks_long=asks_l,
        bids_short=bids_s, asks_short=asks_s,
        frente_long=fl, frente_short=fs,
        restante_mision_usd=100.0,
        permitir_overshoot_min=True,
        piso_mordida_usd=piso,
    )
    assert t2["ok_techo"] and not t2["overshoot_meta"], t2
    assert abs(float(t2["techo_usd"]) - 100.0) < 1e-6, t2

    print("OK validar_asalto_overshoot_min_smoke")


if __name__ == "__main__":
    main()
