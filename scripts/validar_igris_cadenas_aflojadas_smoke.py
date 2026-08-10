#!/usr/bin/env python3
"""Smoke: cadenas Asalto aflojadas (ventana no bloquea, ojos, auth)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from generales.igris import IgrisEscudo


def test_flags() -> None:
    assert config.IGRIS_VENTANA_NO_BLOQUEA_ENGORDE is True
    assert config.IGRIS_ASALTO_SIN_TANK_ROJO is True
    assert config.IGRIS_ASALTO_PUERTA_SIN_OJOS is True
    assert config.IGRIS_RESERVA_AJUSTAR_A_AUTH is True
    assert config.IGRIS_PODA_AUTO is False
    print("  flags OK")


def test_prioridad_sin_espejo() -> None:
    bel = MagicMock()
    tusk = MagicMock()
    tusk.pesos = {
        "AVAXUSD_INVERSE": {"long": 1000.0, "short": 0.0},
        "AVAXUSDT_LINEAL": {"long": 0.0, "short": 100.0},
        "SOLUSD_INVERSE": {"long": 0.0, "short": 0.0},
        "SOLUSDT_LINEAL": {"long": 0.0, "short": 0.0},
    }
    tusk.masa_bruta_real = 1500.0
    tusk.masa_bruta = 1500.0
    ig = IgrisEscudo(tusk, MagicMock(), bel, bridge=None)
    assert ig._espejo_dual_completo("AVAX") is True
    assert ig._espejo_dual_completo("SOL") is False
    print("  prioridad sin espejo OK")


def main() -> int:
    test_flags()
    test_prioridad_sin_espejo()
    print("OK igris cadenas aflojadas smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
