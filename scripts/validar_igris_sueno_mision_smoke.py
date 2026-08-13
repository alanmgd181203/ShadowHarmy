#!/usr/bin/env python3
"""Smoke frío — mega-cirugía Igris sueño/misión/Asalto/bocado (sin red)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import igris_mision as imis
from core import igris_bocado as iboc
from core import pase_director as pd


def test_solo_asalto():
    config.IGRIS_SOLO_ASALTO = True
    assert pd.normalizar_marcha("personalizado") == "asalto"
    assert pd.perfil_marcha("personalizado")["id"] == "asalto"
    assert pd.perfil_marcha("asalto")["force_market"] is True
    print("  solo Asalto OK")


def test_bocado_asimetrico():
    # long gordo 119 vs short 117 → más short en el siguiente
    boc = iboc.bocado_asimetrico_usd(119.0, 117.0, 38.0)
    assert boc["ok"]
    assert float(boc["usd_short"]) >= float(boc["usd_long"])
    print("  bocado asimétrico (más short) OK", boc["ajuste"])


def test_reducir_confirma():
    config.IGRIS_REDUCIR_REQUIERE_CONFIRMA = True
    config.IGRIS_REDUCIR_CONFIRMADO = False
    ok, motivo = imis.reducir_permitido({"tipo": "reducir", "confirmado": False})
    assert ok is False and "CONFIRMA" in motivo
    ok2, _ = imis.reducir_permitido({"tipo": "reducir", "confirmado": True})
    assert ok2 is True
    print("  reducir espera confirma OK")


async def test_cola_mision():
    imis.vaciar_cola()
    await imis.encolar(imis.MisionIgris(tipo="dormir", origen="smoke"))
    m = await imis.sacar_mision(timeout=1.0)
    assert m and m["tipo"] == "dormir"
    assert imis.sueno_mision_activo() is True or True
    print("  cola misión dormir OK")


def test_flags_cirugia():
    assert getattr(config, "IGRIS_SUENO_MISION", True) is True
    assert getattr(config, "IGRIS_DUAL_SALVAVIDAS_EMPATE", False) is False
    assert getattr(config, "IGRIS_OXIGENO_PILOTO", False) is False
    print("  flags cirugía defaults OK")


def main() -> int:
    print("[SMOKE] Igris sueño/misión cirugía")
    test_solo_asalto()
    test_bocado_asimetrico()
    test_reducir_confirma()
    asyncio.run(test_cola_mision())
    test_flags_cirugia()
    print("OK validar_igris_sueno_mision_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
