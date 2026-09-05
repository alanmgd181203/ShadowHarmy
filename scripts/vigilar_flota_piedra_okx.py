#!/usr/bin/env python3
"""Vigilante flota piedra OKX — mantiene 115/115 manos tras corte luz/red.

Revisa cada N segundos:
  - dedupe (1 manos por Santo)
  - relanza faltantes con --continuar + apalanc max
  - sella informe en data/beru/rango/vigilante_flota_informe.json

Uso:
  python scripts/vigilar_flota_piedra_okx.py --intervalo 300
  python scripts/vigilar_flota_piedra_okx.py --una-vez
  python scripts/vigilar_flota_piedra_okx.py --una-vez --dry-run

Windows (loop en background):
  .\\scripts\\vigilar_flota_piedra_okx_win.ps1
"""
from __future__ import annotations

import argparse
import signal
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

from core import beru_flota_vigilante as vf


def _imprimir(informe: dict) -> None:
    print(
        f"[FLOTA] {informe.get('manos_vivas')}/{informe.get('flota_esperada')} "
        f"({informe.get('pct_cobertura')}%) · "
        f"faltan={len(informe.get('faltan') or [])} · "
        f"dupes={informe.get('duplicados_purgados')} · "
        f"net={'OK' if informe.get('internet_ok') else 'NO'} · "
        f"relanzados={len(informe.get('relanzados_este_tick') or [])}",
        flush=True,
    )
    faltan = list(informe.get("faltan") or [])
    if faltan:
        muestra = faltan[:12]
        extra = f" ... +{len(faltan) - len(muestra)}" if len(faltan) > len(muestra) else ""
        print(f"  faltan: {', '.join(muestra)}{extra}", flush=True)
    for row in informe.get("relanzados_este_tick") or []:
        if row.get("error"):
            print(f"  RELANZAR_FAIL {row.get('activo')}: {row.get('error')}", flush=True)
        elif not row.get("dry_run"):
            print(
                f"  RELANZADO {row.get('activo')} pid={row.get('pid')}",
                flush=True,
            )


def main() -> int:
    ap = argparse.ArgumentParser(description="Vigilante flota piedra OKX")
    ap.add_argument("--intervalo", type=float, default=300.0, help="Segundos entre ticks")
    ap.add_argument("--escalon", type=float, default=30.0, help="Segundos entre relanzamientos")
    ap.add_argument(
        "--max-relanzar",
        type=int,
        default=15,
        help="Max Santos a relanzar por tick (evita tormenta OKX)",
    )
    ap.add_argument("--una-vez", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not vf.adquirir_lock():
        print("[FLOTA] Otro vigilante ya corre — salgo", flush=True)
        return 0

    stop = False

    def _sig(*_a):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _sig)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _sig)

    print("=" * 56)
    print("  VIGILANTE FLOTA — piedra OKX manos")
    print(f"  Esperados: {len(vf.flota_esperada())} · intervalo {args.intervalo}s")
    print(f"  Informe: {vf.INFORME_PATH}")
    print("=" * 56)

    try:
        while not stop:
            try:
                informe = vf.tick_flota(
                    dry_run=bool(args.dry_run),
                    escalon_s=float(args.escalon),
                    max_relanzar_por_tick=int(args.max_relanzar),
                )
                _imprimir(informe)
            except Exception as exc:
                print(f"[FLOTA] tick error: {exc}", flush=True)
            if args.una_vez:
                break
            try:
                time.sleep(max(30.0, float(args.intervalo)))
            except KeyboardInterrupt:
                break
    finally:
        vf.liberar_lock()

    print("[FLOTA] Vigilante sellado.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
