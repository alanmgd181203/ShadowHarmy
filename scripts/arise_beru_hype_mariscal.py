#!/usr/bin/env python3
"""Despertar único — Mariscal HYPE · observación ~2 h.

Ojos reales Bybit · Vacío 1,1 / Hoz 1,0 · manos fantasma (cero place_order).
Solo un Santo. Si el manto no sostiene PLENO, la siembra aborta sola.

  python scripts/arise_beru_hype_mariscal.py
  python scripts/arise_beru_hype_mariscal.py --segundos 3600

Tras veredicto OK del Monarca → despertar el resto de la flota (otro ritual).
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FANTASMA = ROOT / "scripts" / "arise_beru_fantasma.py"

# Candados del ritual HYPE Mariscal (antes de cargar el módulo fantasma)
os.environ["ARISE_BERU_HYPE_MARISCAL"] = "true"
os.environ.setdefault("BERU_FANTASMA_EXIGIR_TIER", "PLENO")
os.environ.setdefault("ARISE_BERU_FANTASMA_S", "7200")  # 2 horas
os.environ.setdefault("BERU_SIEMBRA_FLOTA", "true")


def _cargar_ritual_fantasma():
    spec = importlib.util.spec_from_file_location("arise_beru_fantasma", FANTASMA)
    if spec is None or spec.loader is None:
        raise RuntimeError("no se pudo cargar arise_beru_fantasma")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["arise_beru_fantasma"] = mod
    spec.loader.exec_module(mod)
    return mod.ritual


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Beru Mariscal HYPE — ojos reales, manos fantasma, solo este Santo",
    )
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_BERU_FANTASMA_S", "7200") or 7200),
        help="Duración observación (default 7200 = 2 h). 0 = hasta Ctrl+C.",
    )
    args = ap.parse_args()
    seg = float(args.segundos or 0)
    print(
        f"\n[MARISCAL HYPE] Despertar único · tier exigido PLENO · "
        f"observación {seg:.0f}s · manos reales OFF\n",
        flush=True,
    )
    ritual = _cargar_ritual_fantasma()
    asyncio.run(ritual(segundos=seg, activos=["HYPE"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
