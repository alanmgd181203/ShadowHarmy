#!/usr/bin/env python3
"""CLI velas Beru para el Pergamino — delega a core.beru_spot_kline.

El panel (Vite) pide: python scripts/beru_spot_kline.py --symbol X --category linear
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.beru_spot_kline import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
