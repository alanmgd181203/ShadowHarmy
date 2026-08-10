#!/usr/bin/env python3
"""Smoke — ojos frescos Igris (libro_stale + invalidar + divergencia)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import igris_despliegue as ides
from core import igris_ojos as ojos


class _Nodo:
    def __init__(self):
        self.libros = {}
        self.muros = {}
        self.precios = {}
        self.estado_foco = "VERDE"
        self.latencia_ms = 50.0
        self.ultima_actualizacion = time.time()
        self.node_id = 1

    def asegurar_frente(self, f):
        self.muros.setdefault(f, {"bid": 0.0, "ask": 0.0})
        self.precios.setdefault(f, 0.0)

    def asegurar_libro(self, f):
        self.asegurar_frente(f)
        self.libros.setdefault(f, {"bids": [], "asks": [], "ts": 0.0})

    def inyectar_muro(self, f, bid, ask):
        self.asegurar_frente(f)
        self.muros[f] = {"bid": bid, "ask": ask}

    def inyectar_libro_snapshot(self, f, bids, asks):
        self.asegurar_libro(f)
        self.libros[f] = {"bids": list(bids), "asks": list(asks), "ts": time.time()}
        self.inyectar_muro(f, 1.0, 1.0)

    def aplicar_delta_libro(self, f, bid_u, ask_u):
        self.asegurar_libro(f)
        if float(self.libros[f].get("ts") or 0) <= 0:
            return
        # noop merge for smoke
        self.libros[f]["ts"] = time.time()


class _Tank:
    def __init__(self):
        self.nodos = [_Nodo()]
        self.libros = {}

    def _obtener_lider_verde(self):
        return self.nodos[0]

    def invalidar_libros(self, bases=None):
        return ojos.invalidar_libros_tank(self, bases)


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


def test_stale_gate():
    config.IGRIS_TICKER_PUERTA_SI_SIN_LIBRO = "false"
    config.IGRIS_LIBRO_STALE_S = 5.0
    config.IGRIS_LIBRO_DIVERGENCIA_PCT = 50.0  # no molestar en este test
    tank = _Tank()
    fl, fs = "ETHUSD_INVERSE", "ETHUSDT_LINEAL"
    # Libro fresco
    tank.nodos[0].inyectar_libro_snapshot(
        fl, [["1910", "1"]], [["1911", "1"]],
    )
    tank.nodos[0].inyectar_libro_snapshot(
        fs, [["1909", "1"]], [["1910", "1"]],
    )
    tank.nodos[0].precios[fl] = 1910.5
    tank.nodos[0].precios[fs] = 1909.5
    p = ides.evaluar_puerta_se(
        tank, fl, fs, t0_paciencia=time.time(), restante_usd=20, activo="ETH",
    )
    # Puede fallar por spread/umbral — pero NO por stale
    _assert(p.get("motivo") != "libro_stale", f"no stale fresco: {p}")

    # Envejecer
    tank.nodos[0].libros[fl]["ts"] = time.time() - 60
    tank.nodos[0].libros[fs]["ts"] = time.time() - 60
    p2 = ides.evaluar_puerta_se(
        tank, fl, fs, t0_paciencia=time.time(), restante_usd=20, activo="ETH",
    )
    _assert(p2.get("ok") is False, "stale debe bloquear")
    _assert(p2.get("motivo") == "libro_stale", f"motivo={p2.get('motivo')}")
    print("  stale gate OK")


def test_invalidar_bloquea_delta():
    tank = _Tank()
    tank.nodos[0].inyectar_libro_snapshot("ETHUSDT_LINEAL", [["1900", "1"]], [["1901", "1"]])
    n_cleared = tank.invalidar_libros(["ETH"])
    _assert(n_cleared >= 1, "invalidó")
    _assert(float(tank.nodos[0].libros["ETHUSDT_LINEAL"]["ts"]) == 0, "ts=0")
    tank.nodos[0].aplicar_delta_libro("ETHUSDT_LINEAL", [["1899", "2"]], [])
    _assert(tank.nodos[0].libros["ETHUSDT_LINEAL"]["bids"] == [], "delta ignorado sin snapshot")
    print("  invalidar + delta bloqueado OK")


def test_divergencia():
    config.IGRIS_TICKER_PUERTA_SI_SIN_LIBRO = "false"
    config.IGRIS_LIBRO_STALE_S = 60.0
    config.IGRIS_LIBRO_DIVERGENCIA_PCT = 0.3
    config.IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT = 0.3  # prueba dura
    tank = _Tank()
    fl, fs = "ETHUSD_INVERSE", "ETHUSDT_LINEAL"
    tank.nodos[0].inyectar_libro_snapshot(fl, [["1900", "1"]], [["1901", "1"]])
    tank.nodos[0].inyectar_libro_snapshot(fs, [["1899", "1"]], [["1900", "1"]])
    # Ticker muy lejos del libro
    tank.nodos[0].precios[fl] = 1920.0
    tank.nodos[0].precios[fs] = 1920.0

    def _px(t, frente):
        return float(t.nodos[0].precios.get(frente) or 0)

    # monkeypatch precio_ticker
    orig = ides.precio_ticker_frente
    ides.precio_ticker_frente = lambda tank, frente: _px(tank, frente)  # type: ignore
    try:
        p = ides.evaluar_puerta_se(
            tank, fl, fs, t0_paciencia=time.time(), restante_usd=20, activo="ETH",
        )
        _assert(p.get("motivo") == "libro_divergente_ticker", f"got {p.get('motivo')}")
    finally:
        ides.precio_ticker_frente = orig
    print("  divergencia ticker OK")


def test_asalto_holgado_ruido_05():
    """Ruido ~0.5% (el que castraba el lote live) pasa bajo Asalto 2.5%."""
    from core import pase_director as pd

    config.IGRIS_TICKER_PUERTA_SI_SIN_LIBRO = "false"
    config.IGRIS_LIBRO_STALE_S = 60.0
    config.IGRIS_LIBRO_DIVERGENCIA_PCT = 0.35
    config.IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT = 2.5
    orig_m = pd.cargar_marcha
    pd.cargar_marcha = lambda: "asalto"  # type: ignore[assignment]
    try:
        lim = ojos.divergencia_max_pct(marcha_asalto=True)
        _assert(lim >= 2.0, f"asalto lim={lim}")
        mid, ticker = 8.32, 8.275
        div = abs(mid - ticker) / ticker * 100.0
        _assert(div < lim, f"div={div} lim={lim}")
        _assert(div > 0.35, "simula el ruido que antes bloqueaba")
    finally:
        pd.cargar_marcha = orig_m  # type: ignore[assignment]
    print("  asalto ojos holgado OK")


def main() -> int:
    print("validar_igris_ojos_smoke:")
    test_stale_gate()
    test_invalidar_bloquea_delta()
    test_divergencia()
    test_asalto_holgado_ruido_05()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
