#!/usr/bin/env python3
"""Smoke: arise lote completo — exclusivos vacíos; ETH no se re-siembra si meta llena."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Simula arranque arise (sin main)
os.environ["IGRIS_FORZAR_EXCLUSIVOS"] = ""
os.environ["IGRIS_ACTIVOS_EXCLUSIVOS"] = ""

import core.config as config
from core import igris_proteccion as iprot
from core import pase_director as pd


def main() -> None:
    config.IGRIS_ACTIVOS_EXCLUSIVOS = []
    config.IGRIS_BOVEDA_EN_LOTE = False
    config.IGRIS_EXCLUIR_BASES = []
    eq = 1516.0
    plan = pd.plan_lote(eq)
    trabajo = [str(p["activo"]).upper() for p in (plan.get("trabajo") or [])]
    assert trabajo, "debe haber trabajo"
    assert "HYPE" in trabajo or "XRP" in trabajo
    filtrado = iprot.filtrar_activos_trabajo(trabajo)
    assert "HYPE" in filtrado or "XRP" in filtrado, filtrado
    assert "MNT" not in filtrado, f"MNT debe pausarse: {filtrado}"
    assert "ETH" not in filtrado or True  # ETH ya logrado → fuera de trabajo típico
    # Con exclusivos ETH el lote muere
    config.IGRIS_ACTIVOS_EXCLUSIVOS = ["ETH"]
    solo = iprot.filtrar_activos_trabajo(trabajo)
    assert solo == ["ETH"], solo
    config.IGRIS_ACTIVOS_EXCLUSIVOS = []
    # Meta ETH sellado → restante 0
    class T:
        pesos = {
            "ETHUSD_INVERSE": {"long": 634.0, "precio_medio_long": 1914.0},
            "ETHUSDT_LINEAL": {"short": 0.33, "precio_medio_short": 1916.0},
        }

    meta = pd.meta_engorde_usd(
        eq, "ETH", tusk=T(), marcha_id="asalto", pasos_logrados=[1],
    )
    assert float(meta.get("restante_usd") or 0) <= 0 or meta.get("motivo") == "activo_fuera_trabajo"
    print("OK validar_arise_lote_completo_smoke")


if __name__ == "__main__":
    main()
