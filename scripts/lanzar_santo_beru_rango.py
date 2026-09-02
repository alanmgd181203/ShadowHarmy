#!/usr/bin/env python3
"""Lanza UN Santo Beru rango en proceso propio (ojos o manos)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_despertar_mil_btc as dm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--activo", required=True)
    ap.add_argument("--fase", default="ojos", choices=["ojos", "manos"])
    ap.add_argument("--manos-go", action="store_true")
    ap.add_argument("--segundos", type=float, default=0.0)
    args = ap.parse_args()
    row = dm.lanzar_santo_proceso(
        args.activo,
        fase=args.fase,
        manos_go=bool(args.manos_go),
        segundos=float(args.segundos or 0),
    )
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
