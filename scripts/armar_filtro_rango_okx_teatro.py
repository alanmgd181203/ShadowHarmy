#!/usr/bin/env python3
"""Rango anual (bóveda Bybit reutilizada) → filtro teatro OKX piedra.

Fuente: filtros_absolutos.json (rango_anual_pct = (max−min)/last × 100, ~365d).
Bandas teatro:
  · verde    ≤ 100%
  · amarillo ≤ 300%
  · rojo     ≤ 600%  (flota elegible)
  · morado   600–1000%  (reserva — visible, sin tocar)
  · fuera    > 1000%  (nevera)

Salida: data/coliseo/rango_juicio/filtros_rango_okx_teatro.json

Uso:
  python scripts/armar_filtro_rango_okx_teatro.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIQ = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_liquidez_okx.json"
ABS = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_absolutos.json"
OUT = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_rango_okx_teatro.json"

VERDE_MAX = 100.0
AMARILLO_MAX = 300.0
FLOTA_MAX = 600.0
MORADO_MAX = 1000.0


def _f(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v >= 0 else None


def _banda(pct: float | None, *, fuera: bool) -> str | None:
    if pct is None:
        return None
    if fuera:
        return "fuera"
    if pct <= VERDE_MAX:
        return "verde"
    if pct <= AMARILLO_MAX:
        return "amarillo"
    if pct <= FLOTA_MAX:
        return "rojo"
    if pct <= MORADO_MAX:
        return "morado"
    return "fuera"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuera-max", type=float, default=MORADO_MAX, help="nevera si rango supera esto")
    args = ap.parse_args()
    fuera_max = float(args.fuera_max)

    if not LIQ.exists():
        print(f"Falta {LIQ} — corre armar_filtro_liquidez_okx_teatro.py", file=sys.stderr)
        return 1
    if not ABS.exists():
        print(f"Falta {ABS} — corre armar_rango_anual_fusion.py", file=sys.stderr)
        return 1

    liq = json.loads(LIQ.read_text(encoding="utf-8"))
    abs_map = json.loads(ABS.read_text(encoding="utf-8")).get("activos") or {}

    bases = [
        a
        for a, row in (liq.get("activos") or {}).items()
        if not (row or {}).get("liquidez_fuera")
    ]
    bases.sort()

    activos: dict[str, Any] = {}
    n_fuera = n_morado = n_flota = n_sin = 0
    for base in bases:
        fx = abs_map.get(base) or {}
        pct = _f(fx.get("rango_anual_pct"))
        fuera = pct is not None and pct > fuera_max + 1e-9
        banda = _banda(pct, fuera=fuera)
        if pct is None:
            n_sin += 1
        elif fuera:
            n_fuera += 1
        elif banda == "morado":
            n_morado += 1
        elif banda in ("verde", "amarillo", "rojo"):
            n_flota += 1
        activos[base] = {
            "activo": base,
            "rango_anual_pct": pct,
            "rango_fuera": fuera,
            "rango_reserva": banda == "morado",
            "rango_banda": banda,
            "fuente": "filtros_absolutos_boveda_bybit",
        }

    payload = {
        "meta": {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "flota_max_pct": FLOTA_MAX,
            "morado_max_pct": MORADO_MAX,
            "fuera_max_pct": fuera_max,
            "verde_max_pct": VERDE_MAX,
            "amarillo_max_pct": AMARILLO_MAX,
            "fuente_rango": str(ABS.relative_to(ROOT)).replace("\\", "/"),
            "n_escaneados": len(bases),
            "n_flota": n_flota,
            "n_morado": n_morado,
            "n_fuera_rango": n_fuera,
            "n_sin_dato": n_sin,
            "n_elegibles_post_rango": n_flota,
            "nota": (
                "Rango 1a Bybit. Flota verde/amarillo/rojo <=600%. "
                "Morado 600-1000% reserva. Nevera >1000%."
            ),
        },
        "activos": activos,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK rango OKX · flota={n_flota} morado={n_morado} fuera>{fuera_max}%={n_fuera} -> {OUT}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
