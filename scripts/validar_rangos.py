#!/usr/bin/env python3
"""Prueba de ácido — capital por fricción directa (sin ×8 sobre X)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc


ACTIVOS = ["ETH", "SOL", "LTC", "BTC"]


def main() -> int:
    print("=" * 64)
    print("  LEY DE FRICCIÓN — Hitos directos (sin 2X/4X/8X)")
    print("  Soldado 0.8% → Capitán 0.4% → General 0.2% → Mariscal 0.1%")
    print("=" * 64)

    cola = bc.cola_activos_con_a_base(ACTIVOS)
    for fila in cola:
        a = fila["activo"]
        x = fila["X"]
        margen = fila["margen_volumen_base_usd"]
        reserva_pct = (1.0 - margen / x) * 100 if x else 0
        cf = fila.get("costos_friccion") or {}
        print(f"\n[{a}]  G_min=${fila['G_min']:.2f}  lev_avg={fila['lev_promedio']}")
        print(f"  margen volumen base (95%): ${margen:.4f}")
        print(f"  Costo Base X (ceil Soldado): ${x}  · reserva ~{reserva_pct:.2f}%")
        print(f"  Topes fricción: Cap {cf.get('CAPITAN')} · Gen {cf.get('GENERAL')} · Mar {cf.get('MARISCAL')}")
        print(f"  A_base: ${fila['A_base']}")
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

    # Invariantes: NO 8X; BTC/ETH aislados Mariscal=105 con config default lev 100
    r_btc = bc.rangos_activo("BTC", 0)
    assert r_btc["MARISCAL"] == 105, r_btc["MARISCAL"]
    assert r_btc["MARISCAL"] != 8 * r_btc["X"]
    assert all(
        (1.0 - f["margen_volumen_base_usd"] / f["X"]) >= 0.05 - 1e-9 for f in cola
    ), "reserva < 5%"
    tel0 = bc.telemetria_progresion(0)
    assert "Inanición" in tel0["rango_ejercito"]
    print("\n[OK] invariantes: Mariscal=fricción 0.1% · ≠8X · reserva≥5% · $0=Inanición")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
