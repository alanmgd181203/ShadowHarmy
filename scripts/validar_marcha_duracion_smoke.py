#!/usr/bin/env python3
"""Smoke marcha_duracion — calibración personalizada."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import marcha_duracion as md


def main() -> int:
    print("[SMOKE] marcha_duracion")
    # Sin muestras: ops puede ser None; calibrar_lote aún persiste
    try:
        md.calibrar_lote({"ETH": 14.0}, 0, 100.0)
        raise AssertionError("dias=0 debe fallar")
    except ValueError:
        pass

    out = md.calibrar_lote({"ETH": 14.0, "SOL": 18.0}, 2.0, 500.0, forzar=True)
    assert out.get("duracion_dias") == 2.0
    assert "ETH" in (out.get("por_base") or {})
    ua = md.umbral_activo("ETH", reajustar=False)
    assert ua["modo"] == "personalizado"
    assert "umbral_pct" in ua
    # reuso <1h
    out2 = md.calibrar_lote({"ETH": 14.0, "SOL": 18.0}, 2.0, 500.0, forzar=False)
    assert out2.get("calibrado_ts") == out.get("calibrado_ts")
    u2 = md.reajustar_umbral("ETH", progreso_frac=0.2, tiempo_frac=0.5, umbral_actual=0.1)
    assert u2 < 0.1  # atrasado → baja
    print("[OK] marcha_duracion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
