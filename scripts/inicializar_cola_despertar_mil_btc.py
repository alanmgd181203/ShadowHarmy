#!/usr/bin/env python3
"""Inicializa cola despertar mil BTC desde piedra_asignacion.json.

Uso:
  python scripts/inicializar_cola_despertar_mil_btc.py
  python scripts/inicializar_cola_despertar_mil_btc.py --fase manos --modo-cruce por_direccion
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_despertar_mil_btc as dm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paso", type=int, default=1000, help="Paso en USD (default 1000)")
    ap.add_argument(
        "--modo-cruce",
        default="cada_zona",
        choices=["cada_zona", "por_direccion", "unico"],
        help="cada_zona = cada cambio de banda; por_direccion = una vez arriba/abajo por mil",
    )
    ap.add_argument("--fase", default="ojos", choices=["ojos", "manos"])
    ap.add_argument("--precio-btc", type=float, default=0.0, help="Ancla precio inicial")
    args = ap.parse_args()

    px = float(args.precio_btc or 0)
    if px <= 0:
        try:
            px = dm.precio_btc_publico()
        except Exception:
            px = 0.0

    st = dm.inicializar_estado(
        paso_usd=int(args.paso),
        modo_cruce=str(args.modo_cruce),
        fase=str(args.fase),
        precio_btc=px if px > 0 else None,
    )
    path = dm.guardar_estado(st)
    cola = st.get("cola") or {}
    print(f"Cola inicializada: {path}")
    print(
        f"  rojos={len(cola.get('rojos') or [])} "
        f"amarillos={len(cola.get('amarillos') or [])} "
        f"paso=${args.paso} modo={args.modo_cruce} fase={args.fase}"
    )
    if px > 0:
        print(f"  ancla BTC={px:.2f} zona_mil={dm.zona_mil(px)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
