#!/usr/bin/env python3
"""Estado de la mega campaña Coliseo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CKPT = ROOT / "data" / "coliseo" / "mega" / "checkpoint.json"


def main() -> int:
    if not CKPT.exists():
        print("Sin checkpoint aún.")
        return 1
    c = json.loads(CKPT.read_text(encoding="utf-8"))
    n = len(c.get("jobs_done") or {})
    fails = len(c.get("failures") or {})
    print(f"status={c.get('status')} jobs_done={n} failures={fails}")
    print(f"vacios_dorados={c.get('vacios_dorados')}")
    print(f"outliers={c.get('outliers')}")
    print(f"updated={c.get('updated_utc')}")
    # estimación burda: ~660 jobs totales
    total = 660
    print(f"progreso~{100*n/total:.1f}% ({n}/{total})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
