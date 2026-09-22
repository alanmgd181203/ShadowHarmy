#!/usr/bin/env python3
"""Terminal viva — balanza L/S desde casa OKX (sin BTC). Solo oído."""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango_balanza as balanza


def main() -> int:
    intervalo = 60.0
    if len(sys.argv) > 1:
        try:
            intervalo = max(5.0, float(sys.argv[1]))
        except ValueError:
            intervalo = 60.0
    print("Balanza de la legion — casa OKX (sin BTC). Ctrl+C para cerrar.", flush=True)
    print(f"Actualiza cada {int(intervalo)}s.\n", flush=True)
    prev_s = None
    while True:
        try:
            snap = balanza.sellar_balanza()
            hora = datetime.now().strftime("%H:%M:%S")
            frase = snap.get("frase") or "?"
            net = snap.get("net_long_usd")
            n = snap.get("n_santos_con_pos")
            fuente = snap.get("fuente") or "?"
            s = float(snap.get("short_usd") or 0)
            delta = ""
            if prev_s is not None:
                d = s - prev_s
                if abs(d) >= 1.0:
                    delta = f"  |  dS {d:+.0f}"
            prev_s = s
            print(
                f"[{hora}] {frase}  |  net L-S ${net}  |  con pos {n}  |  {fuente}{delta}",
                flush=True,
            )
        except Exception as exc:
            hora = datetime.now().strftime("%H:%M:%S")
            print(f"[{hora}] error balanza: {exc}", flush=True)
        time.sleep(intervalo)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nBalanza cerrada.", flush=True)
        raise SystemExit(0)
