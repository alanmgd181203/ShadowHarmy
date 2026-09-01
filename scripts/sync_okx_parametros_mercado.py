#!/usr/bin/env python3
"""Sync instrumentos OKX SWAP USDT → data/okx_parametros_mercado.json (sin manos)."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_mar  # noqa: E402
from core import okx_rest  # noqa: E402

OUT = ROOT / "data" / "okx_parametros_mercado.json"


def _f(x, default=0.0) -> float:
  try:
    v = float(x)
  except (TypeError, ValueError):
    return default
  return v if v > 0 else default


def main() -> int:
  rows = okx_rest.instruments_swap()
  activos: dict = {}
  for row in rows:
    if not isinstance(row, dict):
      continue
    inst = str(row.get("instId") or "")
    if not inst.endswith("-USDT-SWAP"):
      continue
    if str(row.get("state") or "").lower() not in ("live", "trading", ""):
      continue
    act = beru_mar.inst_id_a_activo(inst)
    ct = _f(row.get("ctVal"), 1.0)
    min_sz = _f(row.get("minSz"), 1.0)
    lot = _f(row.get("lotSz"), min_sz)
    tick = _f(row.get("tickSz"), 0.01)
    lev = _f(row.get("lever"), 75.0)
    # Estimado mínimo USD con last si existe (sync sin ticker: ct*min_sz placeholder 1)
    min_usd = min_sz * ct
    activos[act] = {
      "instId": inst,
      "minSz": min_sz,
      "lotSz": lot,
      "ctVal": ct,
      "tickSz": tick,
      "maxLever": lev,
      "min_usd_est": round(min_usd, 4),
      "min_usd_como": "minSz_x_ctVal_sin_precio",
    }

  # Enriquecer min_usd con tickers públicos
  try:
    for t in okx_rest.tickers_swap_usdt():
      inst = str(t.get("instId") or "")
      act = beru_mar.inst_id_a_activo(inst)
      if act not in activos:
        continue
      px = _f(t.get("last"), 0)
      if px <= 0:
        continue
      p = activos[act]
      min_usd = p["minSz"] * p["ctVal"] * px
      p["min_usd_est"] = round(min_usd, 4)
      p["min_usd_como"] = "minSz_x_ctVal_x_last"
      p["precio_ref"] = px
  except Exception as exc:
    print(f"[sync_okx] tickers opcional falló: {exc}", flush=True)

  payload = {
    "meta": {
      "ts_utc": datetime.now(timezone.utc).isoformat(),
      "fuente": "okx_public_instruments",
      "mar": "okx",
      "n_activos": len(activos),
      "nota": "Beru rango mono-pierna SWAP USDT. Sin inverso / sin pentiverso.",
    },
    "activos": activos,
  }
  OUT.parent.mkdir(parents=True, exist_ok=True)
  OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
  print(f"[sync_okx] {len(activos)} SWAP USDT -> {OUT}", flush=True)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
