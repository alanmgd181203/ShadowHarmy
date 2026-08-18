#!/usr/bin/env python3
"""Flota mixta — Mariscales HYPE/LINK/AVAX con Hoz real; el resto fantasma.

Ojos reales · ambas campanas · margen spot ON · sin techo de ensayo.
Si el manto no sostiene PLENO en los tres, la siembra aborta.

  python scripts/arise_beru_flota_mixta.py
  python scripts/arise_beru_flota_mixta.py --segundos 14400
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

FLOTA = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "LTC", "AAVE", "HYPE",
    "MNT", "APT", "AVAX", "BCH", "ETC", "LINK", "NEAR", "OP", "SUI", "UNI",
    "XLM", "FIL",
]
MARISCALES = ["HYPE", "LINK", "AVAX"]

# Antes de cargar el ritual fantasma (él respeta MIXTA y no fuerza sim).
os.environ["ARISE_BERU_FLOTA_MIXTA"] = "true"
os.environ["MODO_SIMULACION"] = "false"
os.environ["BERU_MANOS"] = "true"
os.environ["BERU_MANOS_FANTASMA"] = "true"
os.environ["BERU_MANOS_ACTIVOS"] = ",".join(MARISCALES)
os.environ["BERU_MANOS_EXIGIR_TIER"] = "PLENO"
os.environ["BERU_ENSAYO_NIVEL3"] = "false"
os.environ["BERU_ENSAYO_SOLO_LONG"] = "false"
os.environ["BERU_SPOT_MARGEN_ENABLED"] = "true"
os.environ.setdefault("ARISE_BERU_FANTASMA_S", "14400")
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
        description="Beru mixto — Mariscales HYPE/LINK/AVAX vivos, resto fantasma",
    )
    ap.add_argument(
        "--segundos",
        type=float,
        default=float(os.getenv("ARISE_BERU_FANTASMA_S", "14400") or 14400),
        help="Duración (default 4 h). 0 = hasta Ctrl+C.",
    )
    args = ap.parse_args()
    seg = float(args.segundos or 0)
    print(
        f"\n[FLOTA MIXTA] Mariscales {', '.join(MARISCALES)} · Hoz real · "
        f"resto sombra · {seg:.0f}s\n",
        flush=True,
    )
    ritual = _cargar_ritual_fantasma()
    asyncio.run(ritual(segundos=seg, activos=list(FLOTA)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
