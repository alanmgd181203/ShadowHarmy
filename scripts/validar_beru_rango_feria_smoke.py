#!/usr/bin/env python3
"""Smoke — perfil feria (orejas x2 · engorde +$1/0.2%) sin romper el normal."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_rango as br
from core.models import BeruShip


def main() -> int:
    print("[SMOKE] beru rango perfil feria")
    prev = str(getattr(config, "BERU_RANGO_PERFIL", "normal") or "normal")
    try:
        assert config.aplicar_perfil_beru_rango("feria") == "feria"
        g = br.resumen_geometria()
        assert g["perfil"] == "feria"
        assert abs(float(g["vacio_pct"]) - 0.022) < 1e-12
        assert abs(float(g["sangre_pct"]) - 0.022) < 1e-12
        assert abs(float(g["oz_gap_pct"]) - 0.004) < 1e-12
        assert abs(float(g["red_activacion_pct"]) - 0.012) < 1e-12
        assert abs(float(g["red_activacion_long_pct"]) - 0.012) < 1e-12
        assert abs(float(g["red_activacion_short_pct"]) - 0.012) < 1e-12
        assert abs(float(g["engorde_paso_pct"]) - 0.002) < 1e-12
        assert abs(float(g["masa_usd"]) - 5.0) < 1e-9
        print("  geometria feria OK")

        # Meta a 2.2%: 11 peldaños de 0.2% → $5+$11=$16
        assert abs(br.meta_saco_usd(100.0, 102.2) - 16.0) < 1e-9
        # Engorde 0.4% desde ancla = 2 peldaños → $7
        b = BeruShip(uid="F1", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
        br.despertar(b, 100.0, activo="ETH")
        # Vacío feria a −2.2%
        m = br.armar_tramo_desde_vacio(b, "ABAJO", precio=97.8)
        assert abs(m - 5.0) < 1e-9, m
        br.actualizar_trailing_oz(b, 97.8 * (1.0 - 0.004))
        assert abs(float(b.masa) - 7.0) < 1e-9, f"engorde feria 0.4% → $7, got {b.masa}"
        print("  nace $5 + engorde $1/0.2% OK")
    finally:
        config.aplicar_perfil_beru_rango(prev if prev in ("normal", "feria") else "normal")
        assert str(config.BERU_RANGO_PERFIL) == (prev if prev in ("normal", "feria") else "normal")
        assert abs(br.vacio_adan_pct() - 0.012) < 1e-12 or prev == "feria"
        if prev != "feria":
            assert abs(br.vacio_adan_pct() - 0.012) < 1e-12
            assert abs(br.engorde_paso_pct() - 0.002) < 1e-12
        print("  restaurado perfil", config.BERU_RANGO_PERFIL)

    print("OK validar_beru_rango_feria_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
