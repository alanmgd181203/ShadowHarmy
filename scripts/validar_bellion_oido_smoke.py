#!/usr/bin/env python3
"""
Smoke oído Bellion 4.1.2 — core/bellion_oido.py

  A) clasificar critico / ejecucion / salud / ruido
  B) anillo snapshot sin ruido
  C) BellionAuditor.anotar → snapshot_oido

Uso: python scripts/validar_bellion_oido_smoke.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import bellion_oido as bo  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_clasificar() -> None:
    _assert(bo.clasificar("BRIDGE", "ORDEN_ERROR", "x") == "critico", "orden error")
    _assert(bo.clasificar("BRIDGE", "NAV_ERROR_API", "?") == "critico", "nav error")
    _assert(bo.clasificar("BERU", "COSECHA", "botín") == "ejecucion", "cosecha")
    _assert(bo.clasificar("IGRIS", "DISPARO_MANTO", "ok") == "ejecucion", "disparo")
    _assert(bo.clasificar("SYSTEM", "ARRANQUE", "arise") == "salud", "arranque")
    _assert(bo.clasificar("BERU", "PACIENCIA", "bajo") == "ruido", "paciencia")
    _assert(bo.clasificar("IGRIS", "ESCALERA_SKIP", "skip") == "ruido", "escalera")
    _assert(bo.clasificar("TANK", "FOO_BAR", "nada") == "ruido", "desconocido")
    print("  A) clasificar OK")


def test_anillo() -> None:
    ring = bo.OidoRing(max_n=20)
    ring.push(general="BRIDGE", accion="ORDEN_ERROR", detalle="fail")
    ring.push(general="BERU", accion="COSECHA", detalle="ok")
    ring.push(general="BERU", accion="PACIENCIA", detalle="wait")
    ring.push(general="SYS", accion="ARRANQUE", detalle="up")
    snap = ring.snapshot(limit=10, incluir_ruido=False)
    _assert(snap["counts"]["critico"] == 1, "count critico")
    _assert(snap["counts"]["ejecucion"] == 1, "count ejec")
    _assert(snap["counts"]["salud"] == 1, "count salud")
    _assert(snap["counts"]["ruido"] == 1, "count ruido interno")
    niveles = {r["nivel"] for r in snap["recientes"]}
    _assert("ruido" not in niveles, "sin ruido en recientes")
    _assert(len(snap["por_nivel"]["critico"]) == 1, "por_nivel critico")
    print("  B) anillo OK")


async def test_auditor() -> None:
    with tempfile.TemporaryDirectory() as td:
        prev = os.getcwd()
        os.chdir(td)
        try:
            Path("data").mkdir()
            bel = BellionAuditor()
            await bel.anotar("BRIDGE", "FILL_TIMEOUT", "orden x")
            await bel.anotar("BERU", "PACIENCIA", "bajo umbral")
            await bel.anotar("BERU", "COSECHA", "botín 1%")
            snap = bel.snapshot_oido()
            _assert(snap["counts"]["critico"] >= 1, "auditor critico")
            _assert(snap["counts"]["ejecucion"] >= 1, "auditor ejec")
            acts = [r["accion"] for r in snap["recientes"]]
            _assert("PACIENCIA" not in acts, "paciencia filtrada")
            _assert("COSECHA" in acts or any(
                x["accion"] == "COSECHA" for x in snap["por_nivel"]["ejecucion"]
            ), "cosecha visible")
        finally:
            os.chdir(prev)
    print("  C) auditor OK")


def main() -> None:
    print("Smoke oído Bellion 4.1.2")
    test_clasificar()
    test_anillo()
    asyncio.run(test_auditor())
    print("PASS 3/3")


if __name__ == "__main__":
    main()
