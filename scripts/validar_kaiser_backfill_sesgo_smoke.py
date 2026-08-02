#!/usr/bin/env python3
"""Smoke — backfill sesgo vs índice (sin red: helpers + lista bases)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import kaiser_backfill as bf  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    bases = bf.bases_backfill_necesarias()
    _assert("LTC" in bases or "BTC" in bases, bases)
    _assert("MNT" in bases, f"MNT debe ir por bóveda: {bases}")
    _assert(len(bases) <= 12, bases)

    idx = {"1000": 100.0, "2000": 100.0}
    price_rows = [
        ["1000", "0", "0", "0", "100.1"],
        ["2000", "0", "0", "0", "99.9"],
    ]
    rows = bf._rows_precio_vs_index(
        base="LTC", edge="spot_vs_index", price_rows=price_rows, idx_by_ts=idx,
    )
    _assert(len(rows) == 2, rows)
    _assert(rows[0]["signed_pct"] > 0, rows[0])
    _assert(rows[1]["signed_pct"] < 0, rows[1])
    _assert(rows[0]["source"] == "backfill", rows[0])

    print("PASS kaiser_backfill sesgo helpers (sin red)")
    print("  bases:", ",".join(bases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
