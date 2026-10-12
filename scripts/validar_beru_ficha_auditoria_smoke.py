#!/usr/bin/env python3
"""Smoke — ficha de auditoría Beru (lectura; no planta)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango_ficha as ficha
from core import beru_rango_paths as paths


def main() -> None:
    act = "_FICHA_SMOKE"
    d = paths.dir_santo(act)
    ev = paths.manos_piedra_eventos(act)
    ahora = time.time()
    rows = [
        {
            "ts": ahora - 120,
            "evento": "ARMAR_RED",
            "detalle": {"dir": "SHORT", "masa": 0.4, "escalon": 1},
        },
        {
            "ts": ahora - 60,
            "evento": "OZ_COSECHA",
            "detalle": {
                "dir": "SHORT",
                "fill": 100.1,
                "oz": 100.0,
                "oz_despliegue": 100.0,
                "masa_hecha": 3.2,
                "red": 100.8,
            },
        },
    ]
    ev.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    snap = {
        "vivo": {
            "estado": "ACECHANDO",
            "origen_tramo": "RED",
            "direccion": "",
            "escalones_red": 2,
            "cosechas": 3,
            "engorde_cero_oz": 100.0,
            "engorde_memoria_peldaños": 10,
            "engorde_peldaño_offset": 10,
            "engorde_campana_dir": "SHORT",
            "masa": 0.0,
            "red": 100.8,
            "oz": 0.0,
            "cero": 99.0,
            "sangre_lado": "ABAJO",
        },
        "geometria": {
            "red_activacion_long_pct": 0.007,
            "red_activacion_short_pct": 0.008,
        },
    }
    out = ficha.armar_ficha(act, last=101.0, snapshot=snap, perfil="piedra")
    assert out["activo"] == act
    assert out["campana"]["redes_consecutivas"] == 2
    assert out["ultima_orden_ejecutada"]["evento"] == "OZ_COSECHA"
    assert out["desde_ultima_orden"]["pct"] is not None
    assert out["desde_ultima_orden"]["pct"] > 0
    path = ficha.escribir_ficha(act, last=101.0, snapshot=snap, perfil="piedra")
    assert path.is_file()
    leida = ficha.leer_ficha(act)
    assert leida.get("activo") == act
    # limpia
    for p in (ev, path, paths.manos_piedra_informe(act)):
        try:
            p.unlink()
        except OSError:
            pass
    try:
        d.rmdir()
    except OSError:
        pass
    print("OK ficha auditoria smoke")


if __name__ == "__main__":
    main()
