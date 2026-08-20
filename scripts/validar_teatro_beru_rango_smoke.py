#!/usr/bin/env python3
"""Smoke frio — teatro Beru rango (velas sinteticas, trailing Oz)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.teatro_beru_rango import expandir_ohlc, simular_rango, escribir_html, escribir_cronica_md


def _velas_laterales() -> list[tuple[int, float, float, float, float]]:
    """Vacío arriba -> trailing persigue -> pullback Oz -> sangre/Red."""
    base = 1_700_000_000
    return [
        (base + 0, 100.0, 100.2, 99.9, 100.1),
        (base + 60, 100.1, 101.5, 101.0, 101.2),  # Vacío + pullback a Oz
        (base + 120, 101.2, 101.9, 101.1, 101.8),  # posible Red
        (base + 180, 101.8, 101.95, 101.5, 101.6),
        (base + 240, 101.6, 101.7, 99.5, 99.6),  # sangre abajo
    ]


def main() -> int:
    candles = _velas_laterales()
    assert len(expandir_ohlc(candles)) == 20
    sim = asyncio.run(simular_rango(candles, activo="HYPE"))
    assert sim["n_eventos"] >= 2
    assert any(e["tipo"].startswith("ARMAR") for e in sim["eventos"])
    arm = next(e for e in sim["eventos"] if e["tipo"].startswith("ARMAR"))
    assert arm["niveles"].get("fase") == "caza"
    assert arm["niveles"].get("oz")
    tipos = [e["tipo"] for e in sim["eventos"]]
    assert "OZ_COSECHA" in tipos
    oz_ev = next(e for e in sim["eventos"] if e["tipo"] == "OZ_COSECHA")
    assert oz_ev["niveles"].get("fase") == "bifurca"
    assert oz_ev["niveles"].get("sangre") and oz_ev["niveles"].get("red")
    out = ROOT / "data" / "coliseo" / "rango_teatro"
    out.mkdir(parents=True, exist_ok=True)
    html = out / "_smoke_teatro_rango.html"
    md = out / "_smoke_cronica_rango.md"
    escribir_html(sim, html)
    escribir_cronica_md(sim, md)
    text = html.read_text(encoding="utf-8")
    assert "Play" in text and "trailing" in text.lower() or "Oz" in text
    print("OK validar_teatro_beru_rango_smoke · eventos", sim["n_eventos"], "cosechas", sim["cosechas"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
