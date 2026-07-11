#!/usr/bin/env python3
"""Prueba de ácido — Ley de Fricción + cola A_base (fórmula manda sobre docs históricos)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc


ACTIVOS = ["ETH", "SOL", "LTC", "BTC"]


def main() -> int:
    print("=" * 64)
    print("  LEY DE FRICCIÓN — Hitos del Motor (ceil X, reserva ≥5%)")
    print("  Soldado 0.8% → Capitán 0.4% → General 0.2% → Mariscal 0.1%")
    print("  Graduación Mariscal = A_base + 8X")
    print("=" * 64)

    cola = bc.cola_activos_con_a_base(ACTIVOS)
    for fila in cola:
        a = fila["activo"]
        x = fila["X"]
        margen = fila["margen_volumen_base_usd"]
        capital_x = x
        reserva_pct = (1.0 - margen / capital_x) * 100 if capital_x else 0
        print(f"\n[{a}]  G_min=${fila['G_min']:.2f}  lev_avg={fila['lev_promedio']}")
        print(f"  margen volumen base (95%): ${margen:.4f}")
        print(f"  Costo Base X (ceil): ${x}  · reserva efectiva ~{reserva_pct:.2f}%")
        print(f"  A_base: ${fila['A_base']}")
        print(f"  Fricción: Soldado {fila['friccion']['SOLDADO']}% · "
              f"Capitán {fila['friccion']['CAPITAN']}% · "
              f"General {fila['friccion']['GENERAL']}% · "
              f"Mariscal {fila['friccion']['MARISCAL']}%")
        lo_s, hi_s = fila["SOLDADO"]
        lo_c, hi_c = fila["CAPITAN"]
        lo_g, hi_g = fila["GENERAL"]
        print(f"  Soldado  [{lo_s} … {hi_s}]")
        print(f"  Capitán  [{lo_c} … {hi_c}]")
        print(f"  General  [{lo_g} … {hi_g}]")
        print(f"  Mariscal = {fila['MARISCAL']}  → A_base siguiente")

    print("\n" + "-" * 64)
    print("TABLA DE HITOS (graduación acumulativa)")
    print("-" * 64)
    print(f"{'Activo':<8} {'X':>6} {'A_base':>8} {'Mariscal':>10} {'Inanición':>14}")
    for fila in cola:
        piso = fila["SOLDADO"][0]
        print(
            f"{fila['activo']:<8} ${fila['X']:>5} ${fila['A_base']:>7} "
            f"${fila['MARISCAL']:>9}  $0–${piso - 1}"
        )

    print("\n" + "-" * 64)
    print("TELEMETRÍA PANEL (ejemplos)")
    for eq in (0, 10, 20, 50, 120, 300):
        t = bc.telemetria_progresion(eq)
        print(
            f"  equity=${eq:<6} → {t['rango_ejercito']:<28} "
            f"grado={t['grado_beru']:<10} X={t['costo_base_X']}"
        )

    # Invariantes
    assert all(f["MARISCAL"] == f["A_base"] + 8 * f["X"] for f in cola)
    assert all(
        (1.0 - f["margen_volumen_base_usd"] / f["X"]) >= 0.05 - 1e-9 for f in cola
    ), "reserva < 5%"
    tel0 = bc.telemetria_progresion(0)
    assert "Inanición" in tel0["rango_ejercito"]
    print("\n[OK] invariantes: Mariscal=A_base+8X · reserva≥5% · $0=Inanición")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
