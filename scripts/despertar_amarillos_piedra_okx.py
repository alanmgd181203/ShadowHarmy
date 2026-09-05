#!/usr/bin/env python3
"""Despertar TODOS los amarillos piedra OKX con manos live + apalanc maximo.

El reloj BTC mil queda sellado solo-rojos (ojos paulatinos).

Uso:
  python scripts/despertar_amarillos_piedra_okx.py
  python scripts/despertar_amarillos_piedra_okx.py --escalon 25 --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

os.environ.setdefault("BERU_MAR", "okx")
os.environ.setdefault("BERU_RANGO_PERFIL", "piedra")
os.environ["IGRIS_FORCE_MAX_LEVERAGE"] = "true"

from core import beru_despertar_mil_btc as dm


def _amarillos_lista(st: dict) -> list[str]:
    cola = st.get("cola") or {}
    return [str(a).upper() for a in (cola.get("amarillos") or []) if str(a).strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--escalon", type=float, default=25.0, help="Segundos entre lanzamientos")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--desde", type=int, default=0, help="Indice amarillo para reanudar")
    args = ap.parse_args()

    path = dm.ruta_estado()
    if not path.is_file():
        print(f"FALLO: falta {path} — inicializar cola primero", flush=True)
        return 1

    st = dm.cargar_estado(path)
    amarillos = _amarillos_lista(st)
    if not amarillos:
        print("FALLO: cola amarillos vacia", flush=True)
        return 1

    if not args.dry_run and not dm.amarillos_manos_total(st):
        dm.marcar_amarillos_manos_total(st)
        dm.guardar_estado(st, path)
        print("Sello temprano: reloj BTC solo-rojos desde ahora", flush=True)

    inicio = max(0, int(args.desde))
    lote = amarillos[inicio:]
    print("=" * 56)
    print("  DESPERTAR AMARILLOS — piedra OKX manos GO")
    print(f"  Total: {len(amarillos)} · desde idx {inicio} · escalon {args.escalon}s")
    print("  Apalanc: IGRIS_FORCE_MAX_LEVERAGE=true")
    print("  Reloj BTC: sellara solo-rojos al terminar")
    print("=" * 56)

    lanzados: list[dict] = []
    for i, act in enumerate(lote):
        if args.dry_run:
            print(f"  [DRY] manos {act}", flush=True)
            lanzados.append({"activo": act, "dry_run": True})
        else:
            row = dm.lanzar_santo_proceso(act, fase="manos", manos_go=True)
            print(f"  [{inicio + i + 1}/{len(amarillos)}] MANOS {act} pid={row.get('pid')}", flush=True)
            lanzados.append(row)
        if i < len(lote) - 1 and args.escalon > 0 and not args.dry_run:
            time.sleep(float(args.escalon))

    if not args.dry_run:
        hist = st.setdefault("historial", [])
        hist.append({
            "evento": "AMARILLOS_MANOS_TOTAL",
            "ts_utc": dm._ahora_utc(),
            "n": len(amarillos),
            "procesos": lanzados,
        })
        dm.guardar_estado(st, path)
        print(f"\nHistorial: {len(lanzados)} amarillos manos registrados", flush=True)

    print(f"Listo: {len(lanzados)} amarillos {'(dry)' if args.dry_run else 'despertados'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
