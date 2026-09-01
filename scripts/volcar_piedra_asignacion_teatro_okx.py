#!/usr/bin/env python3
"""Volca flota teatro OKX → piedra_asignacion.json (semáforo por rango anual).

Solo entran Santos de flota elegible (rango verde/amarillo/rojo ≤600%).
Morado y nevera quedan fuera — el altar no los despierta sin orden del Monarca.

Mapeo doctrinal (22b):
  rango verde    → semáforo verde
  rango amarillo → semáforo amarillo
  rango rojo     → semáforo rojo

Uso:
  python scripts/volcar_piedra_asignacion_teatro_okx.py
  python scripts/volcar_piedra_asignacion_teatro_okx.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RANGO = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_rango_okx_teatro.json"
LIQ = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_liquidez_okx.json"
OUT = ROOT / "data" / "beru" / "rango" / "piedra_asignacion.json"

BANDAS_FLOTA = frozenset({"verde", "amarillo", "rojo"})
BANDA_A_SEMAFORO = {"verde": "verde", "amarillo": "amarillo", "rojo": "rojo"}


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        print(f"Falta {path}", file=sys.stderr)
        raise SystemExit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _flota_desde_rango(rango_data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for base, row in sorted((rango_data.get("activos") or {}).items()):
        if not isinstance(row, dict):
            continue
        banda = str(row.get("rango_banda") or "").strip().lower()
        if banda not in BANDAS_FLOTA:
            continue
        if row.get("rango_fuera"):
            continue
        sem = BANDA_A_SEMAFORO.get(banda)
        if not sem:
            continue
        out.append(
            {
                "activo": str(base).upper(),
                "semaforo": sem,
                "rango_banda": banda,
                "rango_anual_pct": row.get("rango_anual_pct"),
                "fuente_rango": row.get("fuente"),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="solo imprime resumen, no escribe JSON")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    rango_data = _load(RANGO)
    liq_data = _load(LIQ) if LIQ.is_file() else {"activos": {}, "meta": {}}
    liq_map = liq_data.get("activos") or {}

    flota = _flota_desde_rango(rango_data)
    if not flota:
        print("Flota vacía — revisa filtros_rango_okx_teatro.json", file=sys.stderr)
        return 1

    activos: dict[str, dict[str, Any]] = {}
    conteo = {"verde": 0, "amarillo": 0, "rojo": 0}
    for row in flota:
        base = row["activo"]
        sem = row["semaforo"]
        conteo[sem] = conteo.get(sem, 0) + 1
        liq = liq_map.get(base) or {}
        activos[base] = {
            "semaforo": sem,
            "rango_banda": row["rango_banda"],
            "rango_anual_pct": row.get("rango_anual_pct"),
            "turnover24h_okx": liq.get("turnover24h"),
            "slip_buy_pct": liq.get("slip_buy_pct"),
            "slip_sell_pct": liq.get("slip_sell_pct"),
            "fuente": "teatro_okx_volcado",
        }

    prev_meta: dict[str, Any] = {}
    if args.out.is_file():
        try:
            prev = json.loads(args.out.read_text(encoding="utf-8"))
            prev_meta = prev.get("meta") or {}
        except (OSError, json.JSONDecodeError):
            prev_meta = {}

    payload = {
        "meta": {
            **(prev_meta if isinstance(prev_meta, dict) else {}),
            "descripcion": (
                "Semáforo piedra por Santo — rojo / amarillo / verde. "
                "Volcado desde teatro OKX (flota ≤600% rango anual Bybit bóveda)."
            ),
            "semaforo_default": "amarillo",
            "mar": "okx",
            "perfil": "piedra",
            "fuente_volcado": str(RANGO.relative_to(ROOT)).replace("\\", "/"),
            "ts_volcado_utc": datetime.now(timezone.utc).isoformat(),
            "n_flota": len(activos),
            "conteo_semaforo": conteo,
            "nota": (
                "Sin entrada en activos → BERU_RANGO_SEMAFORO (amarillo). "
                "Morado/reserva no volcado. Rango 1a = Bybit bóveda; liquidez = OKX scan."
            ),
        },
        "activos": activos,
    }

    print(f"Flota volcada: {len(activos)} Santos")
    print(f"  verde={conteo.get('verde', 0)} amarillo={conteo.get('amarillo', 0)} rojo={conteo.get('rojo', 0)}")

    if args.dry_run:
        print("(dry-run — no se escribió archivo)")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Escrito: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
