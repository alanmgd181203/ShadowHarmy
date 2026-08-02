#!/usr/bin/env python3
"""Smoke — sesgo estructural Kaiser vs índice (sin API)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import kaiser_sesgo_index as ksi  # noqa: E402
from core import spreads as sp  # noqa: E402
from core.kaiser_samples import append_sample  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


class _Nodo:
    def __init__(self):
        self.precios = {
            "LTCUSDT_LINEAL": 100.0,
            "LTCUSDT_SPOT": 100.1,
            "LTCUSD_INVERSE": 99.9,
        }
        self.index_prices = {"LTCUSDT_LINEAL": 100.0}
        self.estado_foco = "VERDE"

    def precios_con_reflejo(self):
        return dict(self.precios)


class _Tank:
    def _obtener_lider_verde(self):
        return _Nodo()


def main() -> int:
    filas = sp.calcular_matriz_spreads(
        {
            "LTCUSDT_LINEAL": 100.0,
            "LTCUSDT_SPOT": 100.1,
            "LTCUSD_INVERSE": 99.9,
        },
        index_prices={"LTCUSDT_LINEAL": 100.0},
        bases_trinidad=["LTC"],
        top_n=20,
    )
    tipos = {r["tipo"] for r in filas if r.get("base") == "LTC"}
    _assert("spot_vs_index" in tipos, tipos)
    _assert("perp_vs_index" in tipos, tipos)
    _assert("inverse_vs_index" in tipos, tipos)
    spot_row = next(r for r in filas if r["tipo"] == "spot_vs_index" and r["base"] == "LTC")
    inv_row = next(r for r in filas if r["tipo"] == "inverse_vs_index" and r["base"] == "LTC")
    _assert(float(spot_row["desvio_signed_pct"]) > 0, "spot caro → signed +")
    _assert(float(inv_row["desvio_signed_pct"]) < 0, "inverso barato → signed -")

    base = "LTC"
    ahora = time.time()
    for i in range(20):
        ts = ahora - i * 3600
        append_sample(base, "perp_vs_index", signed_pct=0.01, ts=ts)
        append_sample(base, "spot_vs_index", signed_pct=0.10, ts=ts)
        append_sample(base, "inverse_vs_index", signed_pct=-0.10, ts=ts)

    hist_spot = ksi.perfil_sesgo_edge(base, "spot_vs_index")
    _assert(hist_spot.get("cero_estructural_pct") is not None, hist_spot)
    _assert(abs(float(hist_spot["cero_estructural_pct"]) - 0.10) < 0.02, hist_spot)

    tank = _Tank()
    vivo = ksi.vivo_vs_index(tank, "LTC", "spot")
    _assert(vivo["ok"] and vivo["signed_pct"] > 0, vivo)
    vivo_i = ksi.vivo_vs_index(tank, "LTC", "inverso")
    _assert(vivo_i["ok"] and vivo_i["signed_pct"] < 0, vivo_i)

    _assert(ksi.clima_vs_cero(0.10, 0.10)["estado"] == "normal", "clima normal")
    _assert(ksi.clima_vs_cero(0.50, 0.10)["estado"] == "anomalia", "clima anomalia")

    snap = ksi.snapshot_sesgo_estructural(tank, bases=["LTC"])
    _assert("LTC" in snap["bases"], snap)
    _assert(snap["bases"]["LTC"]["mares"]["spot"]["vivo"]["ok"], snap)
    _assert(snap["bases"]["LTC"]["mares"]["spot"]["cero_estructural_pct"] is not None, snap)

    print("PASS kaiser_sesgo_index smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
