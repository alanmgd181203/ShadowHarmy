#!/usr/bin/env python3
"""Smoke frío — checkpoint / continuar inteligente Beru rango."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango_checkpoint as cp
from core.models import BeruShip
from core import beru_rango as br


def _sello(vivo: dict, *, ts: float, activo: str = "WLD") -> dict:
    return {
        "ts": ts,
        "activo": activo,
        "snapshot": {"vivo": vivo},
        "contadores": {"eventos": 1, "por_evento": {"OZ_COSECHA": 1}},
    }


def main() -> int:
    print("[SMOKE] beru_rango_checkpoint")
    ahora = time.time()

    # Semilla: nada (sello={} evita leer disco real)
    p = cp.decidir_arranque(activo="WLD", last=0.4, posiciones=[], sello={}, ahora=ahora)
    assert p.modo == "SEMILLA", p
    print("  sin sello/pos → SEMILLA OK")

    # Fresco acecho con Red
    s = _sello(
        {
            "estado": "ACECHANDO",
            "cero": 0.39,
            "red": 0.387,
            "sangre_lado": "ARRIBA",
            "cosechas": 1,
            "escalones_red": 0,
            "ultima_hoz_direccion": "LONG",
        },
        ts=ahora - 60,
    )
    p = cp.decidir_arranque(activo="WLD", last=0.41, posiciones=[], sello=s, ahora=ahora)
    assert p.modo == "CONTINUAR_ACECHO", p
    assert abs(p.cero - 0.39) < 1e-9
    print("  sello fresco → CONTINUAR_ACECHO OK")

    # Fresco caza
    s2 = _sello(
        {
            "estado": "CAZANDO",
            "direccion": "LONG",
            "cero": 0.39,
            "oz": 0.395,
            "trail_extremo": 0.396,
            "masa": 10,
            "altar_link_id": "BRG-X",
            "sangre_lado": "ABAJO",
        },
        ts=ahora - 30,
    )
    p = cp.decidir_arranque(activo="WLD", last=0.4, posiciones=[], sello=s2, ahora=ahora)
    assert p.modo == "CONTINUAR_CAZA", p
    print("  sello fresco caza → CONTINUAR_CAZA OK")

    # Viejo pero vivo → conserva wake del sello (no last)
    s3 = _sello(
        {
            "estado": "ACECHANDO",
            "cero": 0.39,
            "red": 0.387,
            "sangre_lado": "ARRIBA",
            "cosechas": 2,
            "escalones_red": 1,
            "ultima_hoz_direccion": "LONG",
            "oz_despliegue": 0.391,
        },
        ts=ahora - 3600,
    )
    p = cp.decidir_arranque(activo="WLD", last=0.42, posiciones=[], sello=s3, ahora=ahora)
    assert p.modo == "ACECHO_AJUSTE", p
    assert abs(p.cero - 0.39) < 1e-9  # wake eterno del sello
    assert p.sangre_lado == "ARRIBA"
    assert abs(p.red - 0.387) < 1e-9  # Red del sello si existe
    print("  sello 1h → ACECHO_AJUSTE wake sello OK")

    # Sello >6h sin posición: wake/Red del sello (no last).
    s_viejo = _sello(
        {
            "estado": "ACECHANDO",
            "cero": 0.39,
            "red": 0.387,
            "sangre_lado": "ARRIBA",
            "cosechas": 2,
            "oz_despliegue": 0.391,
        },
        ts=ahora - 25000,
    )
    p = cp.decidir_arranque(
        activo="WLD", last=0.50, posiciones=[], sello=s_viejo, ahora=ahora,
    )
    assert p.modo == "ACECHO_AJUSTE", p
    assert abs(p.cero - 0.39) < 1e-9
    assert abs(p.red - 0.387) < 1e-9
    print("  sello 7h sin pos → wake sello OK")

    # Sin sello útil + LONG → sembrar
    p = cp.decidir_arranque(
        activo="WLD",
        last=0.4,
        posiciones=[{"lado": "LONG", "qty": 25, "precio": 0.39, "masa_usd": 9.75}],
        sello={},
        ahora=ahora,
    )
    assert p.modo == "SEMBRAR_POS", p
    assert p.sangre_lado == "ABAJO"
    assert p.hoz_dir == "LONG"
    assert abs(p.cero - 0.4) < 1e-9
    assert p.red > 0.4
    print("  posición LONG → SEMBRAR_POS sangre ABAJO OK")

    # SHORT
    p = cp.decidir_arranque(
        activo="UNI",
        last=4.0,
        posiciones=[{"lado": "SHORT", "qty": 6.5, "precio": 3.98, "masa_usd": 25.0}],
        sello={},
        ahora=ahora,
    )
    assert p.modo == "SEMBRAR_POS", p
    assert p.sangre_lado == "ARRIBA"
    assert p.red < 4.0
    print("  posición SHORT → SEMBRAR_POS sangre ARRIBA OK")

    # aplicar_plan
    b = BeruShip(uid="t", centro_local=1.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 0.4, activo="WLD")
    cp.aplicar_plan(b, p)
    assert b.estado == "ACECHANDO"
    assert float(b.red_adan or 0) > 0
    assert str(b.sangre_lado) == "ARRIBA"
    print("  aplicar_plan OK")

    # --desde-cero gana
    p = cp.decidir_arranque(
        activo="WLD",
        last=0.4,
        posiciones=[{"lado": "LONG", "qty": 1, "precio": 0.4, "masa_usd": 0.4}],
        sello=s,
        forzar_semilla=True,
        ahora=ahora,
    )
    assert p.modo == "SEMILLA", p
    print("  forzar_semilla OK")

    print("OK validar_beru_rango_checkpoint_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
