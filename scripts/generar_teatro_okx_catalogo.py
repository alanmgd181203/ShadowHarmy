#!/usr/bin/env python3
"""Volcado OKX USDT-SWAP → teatro_okx_catalogo.json (lista teatro sin juicio)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "data" / "okx_parametros_mercado.json"
OUT = ROOT / "data" / "coliseo" / "rango_juicio" / "teatro_okx_catalogo.json"

TRADEFI_HINTS = frozenset(
    {
        "AAPL", "TSLA", "NVDA", "AMZN", "META", "GOOG", "MSFT", "COIN", "MSTR",
        "SPX", "NDX", "HYUNDAI", "XAU", "XAG", "GOLD", "SILVER", "OIL", "BRENT",
        "WTI", "TRUMP",
    }
)


def _es_tradefi(act: str, row: dict) -> bool:
    clase = str(row.get("clase") or "").lower()
    if clase == "perp_tradefi":
        return True
    a = str(act or "").upper()
    return a in TRADEFI_HINTS


def main() -> int:
    if not SRC.exists():
        print(f"Falta {SRC} — corre sync_okx_catalogo_completo.py", file=sys.stderr)
        return 1
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    activos_map = raw.get("activos") or {}
    rows = []
    for act, row in activos_map.items():
        if not isinstance(row, dict):
            continue
        base = str(act or "").upper()
        if not base:
            continue
        tradefi = _es_tradefi(base, row)
        rows.append(
            {
                "activo": base,
                "tradefi": tradefi,
                "tipo": "tradefi" if tradefi else "perp",
                "instId": str(row.get("instId") or f"{base}-USDT-SWAP"),
                "symbol": str(row.get("symbol") or f"{base}USDT"),
                "frente": str(row.get("frente") or f"{base}USDT_LINEAL"),
                "precio_ref": float(row.get("precio_ref") or 0) or None,
                "min_usd": float(row.get("G_min") or row.get("min_usd_est") or 0) or None,
                "max_leverage": float(row.get("maxLever") or 0) or None,
                "lotSz": row.get("lotSz"),
                "minSz": row.get("minSz"),
            }
        )
    rows.sort(key=lambda r: str(r.get("activo") or ""))
    n_tf = sum(1 for r in rows if r.get("tradefi"))
    payload = {
        "meta": {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "mar": "okx",
            "fuente": str(SRC.relative_to(ROOT)).replace("\\", "/"),
            "n_total": len(rows),
            "n_perp": len(rows) - n_tf,
            "n_tradefi": n_tf,
            "nota": "Catálogo crudo USDT-SWAP — sin juicio ni semáforo aún.",
        },
        "activos": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK teatro_okx_catalogo - {len(rows)} pares ({n_tf} tradefi) -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
