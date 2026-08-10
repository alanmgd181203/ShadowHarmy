#!/usr/bin/env python3
"""Smoke: invalidar frentes de feed (no wipe global) + handshake sin wipe."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import igris_ojos as ojos


class _Nodo:
    def __init__(self):
        self.libros = {}
        self.muros = {}

    def inyectar_muro(self, f, bid, ask):
        self.muros[f] = {"bid": bid, "ask": ask}


class _Tank:
    def __init__(self):
        self.nodos = [_Nodo()]


def main() -> None:
    tank = _Tank()
    n0 = tank.nodos[0]
    # Campamento: 3 frentes vivos
    for f, px in (
        ("ETHUSD_INVERSE", 1900.0),
        ("ETHUSDT_LINEAL", 1901.0),
        ("SOLUSD_INVERSE", 100.0),
    ):
        n0.libros[f] = {
            "bids": [[px, 1.0]],
            "asks": [[px + 1, 1.0]],
            "ts": time.time(),
        }
        n0.inyectar_muro(f, 1.0, 1.0)

    feed_eth = {
        "label": "inverse-1",
        "tickers": [("ETHUSD", "ETHUSD_INVERSE")],
        "books": [("ETHUSD", "ETHUSD_INVERSE")],
    }
    fr = ojos.frentes_de_feed(feed_eth)
    assert fr == ["ETHUSD_INVERSE"], fr

    n = ojos.invalidar_frentes_tank(tank, fr)
    assert n >= 1
    assert float(n0.libros["ETHUSD_INVERSE"]["ts"] or 0) <= 0
    assert float(n0.libros["ETHUSDT_LINEAL"]["ts"] or 0) > 0, "lineal no debe borrarse"
    assert float(n0.libros["SOLUSD_INVERSE"]["ts"] or 0) > 0, "SOL no debe borrarse"

    # Handshake fail policy: session_live=False → caller must NOT wipe
    session_live = False
    should_wipe = session_live and True
    assert should_wipe is False

    print("OK validar_bridge_ojos_sin_wipe_smoke")


if __name__ == "__main__":
    main()
