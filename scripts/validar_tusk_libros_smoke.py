#!/usr/bin/env python3
"""Smoke tusk_libros — tres libros + reglas."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import tusk_libros as tl


def main() -> int:
    print("[SMOKE] tusk_libros")

    class FakeTusk:
        masa_bruta_real = 1500.0
        masa_bruta = 1500.0

    snap = tl.snapshot_libros(FakeTusk())
    assert snap["boveda"]["mtm_no_es_riqueza_beru"] is True
    assert snap["testigo"]["no_es_veredicto_riqueza"] is True
    assert abs(snap["testigo"]["equity_uta_usd"] - 1500.0) < 1e-6
    assert snap["guerra"]["reportes_vivos"] is False
    assert snap["reglas"]["no_mezclar_contabilidades"] is True
    print("[OK] tusk_libros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
