#!/usr/bin/env python3
"""CLI — fija marcha de despliegue vía pase_director.guardar_marcha (calibra custom)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import pase_director as pd  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Guardar marcha de despliegue")
    ap.add_argument(
        "--id", "-i", required=True,
        help="asalto|personalizado (legado tactico|marcha_forzada → asalto)",
    )
    ap.add_argument("--dias", "-d", type=float, default=None, help="Obligatorio si personalizado")
    ap.add_argument("--equity", "-e", type=float, default=None)
    ap.add_argument("--json-out", action="store_true")
    args = ap.parse_args()
    try:
        payload = pd.guardar_marcha(
            args.id,
            duracion_dias=args.dias,
            equity_usd=args.equity,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if args.json_out:
        print(json.dumps(payload, indent=2))
    else:
        print(f"OK marcha={payload.get('marcha_id')} fill={payload.get('fill_ratio')} reserva={payload.get('reserva_pasos')}")
        if payload.get("duracion_dias"):
            print(f"  duracion_dias={payload['duracion_dias']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
