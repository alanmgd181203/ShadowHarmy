#!/usr/bin/env python3
"""Smoke: Asalto acepta peaje (spread negativo); banda dual se mide en USD del Santo."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PASE_PROGRESO_FORCE_WRITE", "1")

from core import igris_despliegue as ides
from core import igris_ojos as ojos
from core import manto_ventana as mv
from core import pase_director as pd


def main() -> None:
    urg = pd.umbral_por_marcha(0.12, marcha_id="asalto", base="HYPE")
    assert urg["umbral_pct"] == 0.0 and urg["force_market"] is True
    assert urg["modo_paciencia"] == "marcha_asalto"

    ask_l, bid_s = 54.782, 54.698
    spread = ides.spread_ejecutable_pct(ask_l, bid_s)
    assert spread < 0, spread

    # Sin Tank real: muleta de libro + ojos frescos
    orig_libro = ides.libro_tank
    orig_marcha = pd.cargar_marcha
    orig_meta = ojos.meta_libro
    orig_div = ojos.divergencia_libro_vs_ticker

    def _libro(_tank, frente: str):
        if "INVERSE" in frente.upper():
            return ([[ask_l * 0.999, 200.0]], [[ask_l, 200.0]])
        return ([[bid_s, 200.0]], [[bid_s * 1.001, 200.0]])

    ides.libro_tank = _libro  # type: ignore[assignment]
    pd.cargar_marcha = lambda: "asalto"  # type: ignore[assignment]
    ojos.meta_libro = lambda *a, **k: {  # type: ignore[assignment]
        "stale": False, "edad_s": 0.1, "stale_lim_s": 30.0, "ok": True,
    }
    ojos.divergencia_libro_vs_ticker = lambda *a, **k: {"ok": True}  # type: ignore[assignment]
    try:
        puerta = ides.evaluar_puerta_se(
            object(),
            "HYPEUSD_INVERSE",
            "HYPEUSDT_LINEAL",
            t0_paciencia=0.0,
            restante_usd=625.0,
            activo="HYPE",
            tank_semaforo="VERDE",
        )
    finally:
        ides.libro_tank = orig_libro  # type: ignore[assignment]
        pd.cargar_marcha = orig_marcha  # type: ignore[assignment]
        ojos.meta_libro = orig_meta  # type: ignore[assignment]
        ojos.divergencia_libro_vs_ticker = orig_div  # type: ignore[assignment]

    assert puerta.get("motivo") != "spread_bajo_umbral", puerta
    assert float(puerta.get("spread_pct") or 0) < 0, puerta

    # Personalizado (umbral > 0 vía mock) seguiría rechazando peaje — no tocamos disco.
    # Banda USD del Santo (camino lote completo).
    assert mv.verificar_post_maniobra(100.0, 100.0, operativo=True)
    assert not mv.verificar_post_maniobra(634.0, 0.33, operativo=True)
    assert mv.verificar_post_maniobra(25.0, 25.0, operativo=True)

    print("OK asalto_peaje_banda_smoke")


if __name__ == "__main__":
    main()
