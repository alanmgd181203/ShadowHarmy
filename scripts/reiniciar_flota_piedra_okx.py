#!/usr/bin/env python3
"""Reinicia flota piedra OKX para cargar pergamino nuevo (candado Market / Red).

  python scripts/reiniciar_flota_piedra_okx.py
  python scripts/reiniciar_flota_piedra_okx.py --escalon 1.5
  python scripts/reiniciar_flota_piedra_okx.py --dry-run
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

from core import beru_flota_vigilante as vf


def main() -> int:
    ap = argparse.ArgumentParser(description="Reinicio total flota piedra OKX")
    ap.add_argument("--escalon", type=float, default=1.0, help="Segundos entre relanzos")
    ap.add_argument("--lote", type=int, default=25, help="Pausa extra cada N Santos")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Reinicio ordenado: tomar el lock a la fuerza (el vigilante loop cede).
    try:
        vf.LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        vf.LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as exc:
        print(f"[FLOTA] No pude sellar lock: {exc}", flush=True)
        return 1

    print("=" * 56, flush=True)
    print("  REINICIO FLOTA — piedra OKX (codigo nuevo)", flush=True)
    print(f"  Esperados: {len(vf.flota_esperada())} · escalon {args.escalon}s", flush=True)
    print("=" * 56, flush=True)
    try:
        informe = vf.reiniciar_flota(
            dry_run=bool(args.dry_run),
            escalon_s=float(args.escalon),
            max_por_lote=int(args.lote),
            pausa_entre_lotes_s=2.0,
        )
        print(
            f"[FLOTA] muertos={informe.get('muertos')} · "
            f"vivos={informe.get('manos_vivas')}/{informe.get('flota_esperada')} "
            f"({informe.get('pct_cobertura')}%) · "
            f"faltan={len(informe.get('faltan') or [])}",
            flush=True,
        )
        faltan = list(informe.get("faltan") or [])
        if faltan:
            print(f"  faltan: {', '.join(faltan[:20])}", flush=True)
            if not args.dry_run and faltan:
                print("[FLOTA] Segundo pase (solo faltantes)…", flush=True)
                for i, act in enumerate(faltan):
                    try:
                        vf.lanzar_manos_piedra(act, continuar=True)
                        print(f"  RELANZADO {act}", flush=True)
                    except Exception as exc:
                        print(f"  FAIL {act}: {exc}", flush=True)
                    if i < len(faltan) - 1:
                        time.sleep(float(args.escalon))
                reg = vf._leer_pids_registro()
                vivos = sum(1 for a in vf.flota_esperada() if a in reg and vf._pid_vivo(reg[a]))
                print(f"[FLOTA] tras pase2 ~{vivos}/{len(vf.flota_esperada())}", flush=True)
    finally:
        vf.liberar_lock()
    print("[FLOTA] Reinicio sellado.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
