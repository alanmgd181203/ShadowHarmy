#!/usr/bin/env python3
"""Smoke estático del ritual de ojos (sin API / sin red)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCRIPT = ROOT / "scripts" / "arise_ojos_tusk.py"


def main() -> int:
    assert SCRIPT.is_file(), f"falta {SCRIPT}"
    src = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for req in ("ritual_ojos", "main", "_cronica_tesoreria", "_publicar_estado"):
        assert req in names, f"falta {req}"
    assert ".vigilar_manto_operativo()" not in src, "ojos no debe arrancar Igris manto"
    assert ".vigilancia_oportunidades()" not in src, "ojos no debe arrancar Greed"
    assert "KaiserVocero" in src and "TankCluster" in src and "TuskBoveda" in src
    import core.config as config
    assert hasattr(config, "ARISE_OJOS_TUSK")
    assert hasattr(config, "TUSK_TESORERIA_ACTIVA")
    print("PASS arise_ojos_tusk smoke (estático)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
