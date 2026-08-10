#!/usr/bin/env python3
"""Smoke: Igris no poda por Ley Marcial (IGRIS_PODA_AUTO=false)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import igris_estado as ie
from core import manto_jurisdiccion as mj
from generales.igris import IgrisEscudo


def test_flag_y_heuristica() -> None:
    assert config.IGRIS_PODA_AUTO is False
    assert mj.sobre_muro(96.0) is True
    r = ie.resumen_manto(
        margen_ocupado_pct=96,
        peso_long=60,
        peso_short=40,
        banda_min=0.48,
        banda_max=0.52,
    )
    assert r["accion_heuristica"] == "VIGILAR_OXIGENO"
    print("  flag + heurística OK")


async def test_maniobra_poda_bloqueada() -> None:
    bel = MagicMock()
    bel.anotar = AsyncMock()
    tusk = MagicMock()
    tusk.pesos = {
        "SOLUSD_INVERSE": {"long": 100.0, "short": 0.0},
        "SOLUSDT_LINEAL": {"long": 0.0, "short": 50.0},
    }
    tusk.solicitar_reserva = AsyncMock(return_value=True)
    tusk.liberar_reserva = AsyncMock()
    tank = MagicMock()
    tank.vision_especulativa = AsyncMock(return_value=({}, "VERDE"))
    ig = IgrisEscudo(tusk, tank, bel, bridge=None)
    await ig._ejecutar_maniobra("PODAR_MANTO", "LONG", 15.0)
    motivos = [c.args[1] for c in bel.anotar.await_args_list]
    assert "PODA_DESARMADA" in motivos
    assert not any(m == "PODA" for m in motivos)
    print("  PODAR_MANTO bloqueada OK")


def main() -> int:
    test_flag_y_heuristica()
    asyncio.run(test_maniobra_poda_bloqueada())
    print("OK igris sin poda smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
