#!/usr/bin/env python3
"""Despertar TODOS los rojos piedra OKX con manos live + apalanc maximo.

Sella el reloj BTC (cola roja completa).

Uso:
  python scripts/despertar_rojos_piedra_okx.py
  python scripts/despertar_rojos_piedra_okx.py --escalon 25 --dry-run
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


def _rojos_lista(st: dict) -> list[str]:
    cola = st.get("cola") or {}
    return [str(a).upper() for a in (cola.get("rojos") or []) if str(a).strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--escalon", type=float, default=25.0, help="Segundos entre lanzamientos")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--desde", type=int, default=0, help="Indice rojo para reanudar")
    ap.add_argument(
        "--lista-file",
        default="",
        help="Archivo con un Santo por linea (reintento)",
    )
    args = ap.parse_args()

    path = dm.ruta_estado()
    if not path.is_file():
        print(f"FALLO: falta {path} — inicializar cola primero", flush=True)
        return 1

    st = dm.cargar_estado(path)
    rojos = _rojos_lista(st)
    if not rojos:
        print("FALLO: cola rojos vacia", flush=True)
        return 1

    if not args.dry_run and not dm.rojos_manos_total(st):
        dm.marcar_rojos_manos_total(st)
        dm.guardar_estado(st, path)
        print("Sello temprano: reloj BTC sin mas despertares", flush=True)

    inicio = max(0, int(args.desde))
    lista_path = str(getattr(args, "lista_file", "") or "").strip()
    if lista_path:
        pedidos = [
            ln.strip().upper()
            for ln in Path(lista_path).read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        lote = [a for a in pedidos if a in rojos]
    else:
        lote = rojos[inicio:]
    print("=" * 56)
    print("  DESPERTAR ROJOS — piedra OKX manos GO")
    print(f"  Cola: {len(rojos)} · este lote: {len(lote)} · escalon {args.escalon}s")
    print("  Apalanc: IGRIS_FORCE_MAX_LEVERAGE=true")
    print("=" * 56)

    lanzados: list[dict] = []
    for i, act in enumerate(lote):
        if args.dry_run:
            print(f"  [DRY] manos {act}", flush=True)
            lanzados.append({"activo": act, "dry_run": True})
        else:
            row = dm.lanzar_santo_proceso(act, fase="manos", manos_go=True)
            print(f"  [{i + 1}/{len(lote)}] MANOS {act} pid={row.get('pid')}", flush=True)
            lanzados.append(row)
        if i < len(lote) - 1 and args.escalon > 0 and not args.dry_run:
            time.sleep(float(args.escalon))

    if not args.dry_run:
        st = dm.cargar_estado(path)
        hist = st.setdefault("historial", [])
        hist.append({
            "evento": "ROJOS_MANOS_TOTAL",
            "ts_utc": dm._ahora_utc(),
            "n": len(rojos),
            "procesos": lanzados,
        })
        dm.guardar_estado(st, path)
        print(f"\nHistorial: {len(lanzados)} rojos manos registrados", flush=True)

    print(f"Listo: {len(lanzados)} rojos {'(dry)' if args.dry_run else 'despertados'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
