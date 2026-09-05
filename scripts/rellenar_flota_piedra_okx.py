#!/usr/bin/env python3
"""Rellena Santos faltantes con --continuar (sin matar vivos)."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_flota_vigilante as vf


def main() -> int:
    esp = vf.flota_esperada()
    reg = vf._leer_pids_registro()
    vivos = {a for a in esp if a in reg and vf._pid_vivo(int(reg[a]))}
    faltan = [a for a in esp if a not in vivos]
    print(f"vivos={len(vivos)} faltan={len(faltan)}", flush=True)
    vf.LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    vf.LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    try:
        n = len(faltan)
        for i, act in enumerate(faltan):
            try:
                row = vf.lanzar_manos_piedra(act, continuar=True)
                if (i + 1) % 15 == 0 or (i + 1) == n:
                    print(
                        f"lanzados {i + 1}/{n} last={act} pid={row.get('pid')}",
                        flush=True,
                    )
            except Exception as exc:
                print(f"FAIL {act}: {exc}", flush=True)
            time.sleep(0.4)
        reg = vf._leer_pids_registro()
        vivos_l = [a for a in esp if a in reg and vf._pid_vivo(int(reg[a]))]
        faltan2 = [a for a in esp if a not in vivos_l]
        print(
            f"cobertura {len(vivos_l)}/{len(esp)} faltan={len(faltan2)}",
            flush=True,
        )
        inf = {
            "ts_utc": vf._ahora_utc(),
            "modo": "cirugia_relleno",
            "flota_esperada": len(esp),
            "manos_vivas": len(vivos_l),
            "faltan": faltan2,
            "pct_cobertura": round(100.0 * len(vivos_l) / max(1, len(esp)), 1),
        }
        vf.INFORME_PATH.write_text(
            json.dumps(inf, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    finally:
        vf.liberar_lock()
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
