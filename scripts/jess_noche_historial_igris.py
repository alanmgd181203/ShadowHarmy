#!/usr/bin/env python3
"""Ritual noche — historial/gráficas flota Igris (spots + L/S).

NO es 4.0.3 Asalto (manos). Función del ejército para llenar bóveda de noche.
Ver: migracion/PEGAR_JESS_NOCHE_HISTORIAL_IGRIS.md

Uso:
  python scripts/jess_noche_historial_igris.py --dias 365 --watchdog
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLISEO = ROOT / "scripts" / "jess_boveda_coliseo_noche.py"


def main() -> int:
    argv = list(sys.argv[1:])
    if "--markets" not in argv and "--solo-spot" not in argv:
        argv = ["--markets", "spot,linear,inverse", *argv]
    if "--ritual" not in argv:
        argv = ["--ritual", "historial_igris", *argv]

    spec = importlib.util.spec_from_file_location("jess_boveda_coliseo_noche", COLISEO)
    if spec is None or spec.loader is None:
        print(f"No cargó motor Coliseo: {COLISEO}", file=sys.stderr)
        return 2
    mod = importlib.util.module_from_spec(spec)
    sys.argv = [str(COLISEO), *argv]
    spec.loader.exec_module(mod)
    return int(mod.main())


if __name__ == "__main__":
    raise SystemExit(main())
