#!/usr/bin/env python3
"""Smoke estático 4.0.2 arise_igris_sim (sin API / sin red)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCRIPT = ROOT / "scripts" / "arise_igris_sim.py"


def main() -> int:
    assert SCRIPT.is_file(), f"falta {SCRIPT}"
    src = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for req in ("ritual_igris_sim", "main", "_snapshot_cierre", "_apagado"):
        assert req in names, f"falta {req}"
    assert "vigilar_manto_operativo" in src, "debe despertar Igris"
    assert "MODO_SIMULACION" in src and "true" in src.lower()
    assert "GreedFrancotirador" not in src, "no despertar Greed"
    assert "Beru" not in src or "hibern" in src.lower()
    assert "vigilancia_oportunidades" not in src
    assert "KaiserVocero" in src and "TankCluster" in src and "TuskBoveda" in src
    import core.config as config
    assert hasattr(config, "ARISE_IGRIS_SIM")
    print("PASS arise_igris_sim smoke (estático)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
