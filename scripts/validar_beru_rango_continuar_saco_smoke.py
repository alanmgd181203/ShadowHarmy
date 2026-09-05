#!/usr/bin/env python3
"""Smoke — CONTINUAR_CAZA restaura saco del sello (no lo deja en 0)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango as br
from core.models import BeruShip


def main() -> int:
    print("=== validar_beru_rango_continuar_saco_smoke ===")
    b = BeruShip(uid="T", centro_local=1.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 1.0, activo="ETH")
    assert float(b.saco_long_usd or 0) == 0.0
    br.restaurar_caza_trailing(
        b,
        cero=1.0,
        direccion="SHORT",
        oz=1.002,
        trail_extremo=1.004,
        masa=0.45,
        saco_long=37.0,
        saco_short=35.1,
        ultima_hoz_direccion="LONG",
        oz_despliegue=1.001,
        cosechas=31,
    )
    assert abs(float(b.saco_long_usd) - 37.0) < 1e-9, b.saco_long_usd
    assert abs(float(b.saco_short_usd) - 35.1) < 1e-9, b.saco_short_usd
    assert b.estado == "CAZANDO"
    assert str(b.direccion).upper() == "SHORT"
    assert str(b.ultima_hoz_direccion).upper() == "LONG"
    print("  CONTINUAR_CAZA restaura saco OK")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
