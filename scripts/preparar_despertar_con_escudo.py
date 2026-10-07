#!/usr/bin/env python3
"""Preparar despertar limpio: ejército desde 0 + Igris Escudo listo (papel).

NO despierta Santos ni abre manos. Solo:
  1. Borra memoria del escudo (libro papel → 0).
  2. Deja knobs listos (ACTIVO, sim, R dinámico).
  3. Imprime el mandato de wake para el Monarca.

Doctrina: Beru nace sin memoria (--desde-cero). Igris espera con el manto
apagado hasta que la balanza cruce el primer umbral (~400 USD neto), y
entonces va desplegando cobertura BTC en papel (peldaños de 200).

Uso::

  python scripts/preparar_despertar_con_escudo.py
  python scripts/preparar_despertar_con_escudo.py --santos DOT,FIL,OP
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Knobs de convivencia limpia (no live)
os.environ["IGRIS_ESCUDO_BTC_ACTIVO"] = "1"
os.environ.setdefault("IGRIS_ESCUDO_BTC_MODO", "sim")
os.environ.setdefault("IGRIS_ESCUDO_BTC_R", "dinamico")
os.environ.setdefault("IGRIS_ESCUDO_BTC_FRENTE", "inverso")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Preparar despertar desde 0 + Escudo BTC listo (sin wake)"
    )
    ap.add_argument(
        "--santos",
        default="",
        help="Lista opcional para el ejemplo de campamento (comma)",
    )
    args = ap.parse_args()

    from core import igris_escudo_btc as escudo
    from core import beru_rango_paths as paths

    libro = escudo.resetear_libro_escudo(motivo="preparar_despertar_limpio")
    r = escudo.escudo_relacion()
    act = escudo.escudo_activar_usd()
    pel = escudo.escudo_peldaño_usd()
    path = paths.escudo_btc_sim()
    hora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    santos = [a.strip().upper() for a in str(args.santos or "").split(",") if a.strip()]
    ejemplo_santos = ",".join(santos) if santos else "SANTO1,SANTO2,SANTO3"

    print("", flush=True)
    print("═" * 56, flush=True)
    print("  DESPERTAR LIMPIO + ESCUDO LISTO (papel)", flush=True)
    print(f"  {hora}", flush=True)
    print("═" * 56, flush=True)
    print("", flush=True)
    print("Hecho ahora (sin tocar Beru ni casa):", flush=True)
    print(f"  · Memoria escudo borrada → {path.name}", flush=True)
    print(f"  · Libro: ancla=None · papel=0 · peldaño_armado=False", flush=True)
    print(f"  · R={r:.2f} (dinámico) · modo=sim · live cerrado", flush=True)
    print(
        f"  · Primer despliegue cuando |neto Beru| ≥ ${act:.0f} "
        f"(peldaños de ${pel:.0f})",
        flush=True,
    )
    print("", flush=True)
    print("Ley del manto desde 0:", flush=True)
    print("  Beru caza y engorda → balanza sube → Igris arma peldaños.", flush=True)
    print("  Oz / diluye → balanza baja → Igris achica el papel.", flush=True)
    print("  Volteo de lado → desarma y vuelve a esperar el umbral.", flush=True)
    print("", flush=True)
    print("Cuando el Monarca diga GO (campamento):", flush=True)
    print(
        f"  python scripts/arise_beru_rango_campamento.py "
        f"--santos {ejemplo_santos} --manos-go --desde-cero --con-escudo",
        flush=True,
    )
    print("", flush=True)
    print("Oído aparte (opcional):", flush=True)
    print("  python scripts/vigilar_escudo_btc_convivencia.py 60", flush=True)
    print("", flush=True)
    print(
        "Candado: BTC real sigue cerrado hasta LIVE_OK + orden explícita.",
        flush=True,
    )
    print("═" * 56, flush=True)
    _ = libro  # silencio linter
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
