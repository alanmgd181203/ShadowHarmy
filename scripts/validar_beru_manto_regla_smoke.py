"""Espejo de la regla del manto (Pergamino velas): grado = nocional L+S vs 2×G_min/fricción."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc

FRICCION = {"SOLDADO": 0.008, "CAPITAN": 0.004, "GENERAL": 0.002, "MARISCAL": 0.001}
GRADOS = ("SOLDADO", "CAPITAN", "GENERAL", "MARISCAL")


def grado_que_aguanta(usd_total: float, g_min: float) -> str:
    have = float(usd_total or 0)
    g = float(g_min or 0)
    if have <= 0 or g <= 0:
        return "00"
    out = "00"
    for cand in GRADOS:
        need = (2.0 * g) / FRICCION[cand]
        if have + 1e-9 >= need * 0.995:
            out = cand
        else:
            break
    return out


def main() -> int:
    g = float(bc.g_min_usd("ETH"))
    assert g > 0
    for grado in GRADOS:
        need = float(bc.notional_manto_ls_grado("ETH", grado))
        espejo = (2.0 * g) / FRICCION[grado]
        assert abs(need - espejo) < 1e-6, (grado, need, espejo)
        assert grado_que_aguanta(need, g) == grado
        assert grado_que_aguanta(need * 0.99, g) != grado

    assert grado_que_aguanta(0, g) == "00"
    print("OK validar_beru_manto_regla_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
