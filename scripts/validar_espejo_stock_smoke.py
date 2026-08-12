#!/usr/bin/env python3
"""Smoke: espejo stock pre-engorde — diagnostica lisiado y no engorda hasta curar."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import pase_director as pd
from generales.igris import IgrisEscudo


class _FakeBel:
    def __init__(self):
        self.eventos = []

    async def anotar(self, quien, tipo, msg):
        self.eventos.append((quien, tipo, msg))


def test_usd_piernas_manto():
    tusk = SimpleNamespace(
        pesos={
            "MNTUSD_INVERSE": {
                "long": 179.0,
                "short": 0.0,
                "precio_medio_long": 0.43,
                "precio_medio_short": 0.0,
            },
            "MNTUSDT_LINEAL": {
                "long": 0.0,
                "short": 875.1,
                "precio_medio_long": 0.0,
                "precio_medio_short": 0.434,
            },
        }
    )
    # Vaciar bases bóveda para que short inverso no cuente (ya está en 0)
    config.IGRIS_BOVEDA_BASES = []
    usd_l, usd_s = pd.usd_piernas_manto_activo(tusk, "MNT")
    assert abs(usd_l - 179.0) < 1.0, usd_l
    assert abs(usd_s - 875.1 * 0.434) < 2.0, usd_s
    print("  usd_piernas_manto_activo MNT OK", round(usd_l, 2), round(usd_s, 2))


def test_diagnostico_lisiado():
    config.IGRIS_BOVEDA_BASES = []
    config.IGRIS_MASA_ASIMETRIA_ASALTO_PCT = 0.12
    config.IGRIS_ESPEJO_GAP_MIN_USD = 5.0
    igris = IgrisEscudo(
        SimpleNamespace(
            pesos={
                "ADAUSD_INVERSE": {
                    "long": 100.0,
                    "short": 0.0,
                    "precio_medio_long": 0.2,
                    "precio_medio_short": 0.0,
                },
                "ADAUSDT_LINEAL": {
                    "long": 0.0,
                    "short": 2000.0,
                    "precio_medio_long": 0.0,
                    "precio_medio_short": 0.2,
                },
            },
            masa_bruta=2000,
            masa_bruta_real=2000,
            masa_autorizada=500,
            margen_ocupado=50,
        ),
        SimpleNamespace(),
        _FakeBel(),
    )
    # force asalto lim via env already
    d = igris._diagnostico_espejo_stock("ADA")
    assert d["ok"] is False, d
    assert d["thin"] == "LONG", d
    assert d["gap_usd"] > 50, d
    print("  diagnostico lisiado ADA OK", d)

    igris.tusk.pesos["ADAUSD_INVERSE"]["long"] = 400.0
    igris.tusk.pesos["ADAUSDT_LINEAL"]["short"] = 2000.0  # 400 USD
    d2 = igris._diagnostico_espejo_stock("ADA")
    assert d2["ok"] is True, d2
    print("  diagnostico equilibrado ADA OK", d2)


async def test_asegurar_bloquea_sin_cura():
    config.IGRIS_ESPEJO_STOCK_PRE_ENGORDE = True
    config.IGRIS_DUAL_SALVAVIDAS_MARKET = True
    config.IGRIS_BOVEDA_BASES = []
    bel = _FakeBel()

    async def _fail_salva(*a, **k):
        return {"ok": False, "masa": 0.0, "precio": 0.0}

    igris = IgrisEscudo(
        SimpleNamespace(
            pesos={
                "MNTUSD_INVERSE": {
                    "long": 100.0,
                    "short": 0.0,
                    "precio_medio_long": 0.4,
                    "precio_medio_short": 0.0,
                },
                "MNTUSDT_LINEAL": {
                    "long": 0.0,
                    "short": 1000.0,
                    "precio_medio_long": 0.0,
                    "precio_medio_short": 0.4,
                },
            },
            masa_bruta=2000,
            masa_bruta_real=2000,
            masa_autorizada=500,
            margen_ocupado=50,
        ),
        SimpleNamespace(),
        bel,
    )
    igris._salvavidas_market_pierna = _fail_salva  # type: ignore
    igris._precio_ref_espejo = lambda frente, direccion: 0.4  # type: ignore
    ok = await igris._asegurar_espejo_stock("MNT")
    assert ok is False
    tipos = [t for _, t, _ in bel.eventos]
    assert "ESPEJO_STOCK_CURA" in tipos or "ESPEJO_STOCK_FALLIDO" in tipos
    print("  asegurar bloquea si no cura OK", tipos[-3:])


def main():
    print("validar_espejo_stock_smoke…")
    test_usd_piernas_manto()
    test_diagnostico_lisiado()
    asyncio.run(test_asegurar_bloquea_sin_cura())
    print("OK espejo stock smoke")


if __name__ == "__main__":
    main()
