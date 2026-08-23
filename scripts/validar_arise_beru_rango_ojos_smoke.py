#!/usr/bin/env python3
"""Smoke frío — ritual ojos Beru rango flota 19 / manos OFF."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    path = ROOT / "scripts" / "arise_beru_rango_ojos.py"
    src = path.read_text(encoding="utf-8")
    assert "SANTOS_RANGO_19" in src
    assert "BERU_RANGO_MANOS" in src
    assert "BRIDGE_WS_SOLO_LINEAR" in src
    assert "bridge=None" in src
    assert "rango_ojos_informe.json" in src

    # Contar 19
    ns = src.split("SANTOS_RANGO_19: tuple[str, ...] = (")[1].split(")")[0]
    n = sum(1 for part in ns.replace("\n", " ").split('"') if part.isalpha() and part.isupper() and len(part) <= 5)
    # Más fiable: import ejecutando solo la constante via exec parcial
    import importlib.util
    import os
    os.environ["BERU_RANGO_MANOS"] = "false"
    # No cargar el módulo completo (setea env y corre side effects al import config).
    # Parse lista a mano:
    import re
    block = re.search(r"SANTOS_RANGO_19: tuple\[str, \.\.\.\] = \((.*?)\)", src, re.S)
    assert block
    santos = re.findall(r'"([A-Z0-9]+)"', block.group(1))
    assert len(santos) == 19, f"esperaba 19, hay {len(santos)}: {santos}"
    assert "APT" not in santos and "BCH" not in santos and "ETC" not in santos
    assert "HYPE" in santos and "ETH" in santos
    print("OK validar_arise_beru_rango_ojos_smoke · 19 Santos · manos OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
