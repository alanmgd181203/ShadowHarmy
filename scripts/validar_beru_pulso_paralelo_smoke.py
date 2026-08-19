#!/usr/bin/env python3
"""Smoke frío — pulso de Beru: Santos en paralelo, cupo y cooldown propio."""
from __future__ import annotations

import asyncio
import inspect
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core.models import BeruShip
from generales.beru import BeruCazador
from generales.capitanes import CapitanNormal


class Bel:
    async def anotar(self, *_a, **_k):
        return None


class Tank:
    capitan_activo = CapitanNormal
    precios = {}


class Tusk:
    pesos = {}
    tesoreria = {"estado": "ok", "disponible_usd": 50.0}


def _barco(uid: str) -> BeruShip:
    return BeruShip(
        uid=uid,
        centro_local=100.0,
        masa=5.0,
        direccion="LONG",
        estado="CAZANDO",
        oz_adan=100.0,
        frente_asignado="ETHUSDT_SPOT",
        tier_id="PROTO1",
        modo_combate="CAZA",
    )


def _general() -> BeruCazador:
    g = BeruCazador(Tusk(), Bel(), Tank(), bridge=object())
    g._llamado_ahogado = lambda *a, **k: None  # type: ignore[method-assign]
    return g


async def _probar() -> None:
    g = _general()
    naves = [_barco(f"SEM_{i}") for i in range(3)]
    prev = int(getattr(config, "BERU_MANOS_PARALELAS", 8) or 8)
    try:
        config.BERU_MANOS_PARALELAS = 8
        t0 = time.perf_counter()
        await g._mapear_santos(naves, lambda _b: asyncio.sleep(0.12))
        paralelo = time.perf_counter() - t0
        assert paralelo < 0.28, paralelo

        config.BERU_MANOS_PARALELAS = 1
        t1 = time.perf_counter()
        await g._mapear_santos(naves, lambda _b: asyncio.sleep(0.12))
        fila = time.perf_counter() - t1
        assert fila >= 0.30, fila
    finally:
        config.BERU_MANOS_PARALELAS = prev

    visto: list[str] = []
    frio = _barco("FRIO")
    frio.api_bloqueo_hasta = time.time() + 30
    vivo = _barco("VIVO")

    async def _marca(beru: BeruShip) -> None:
        visto.append(beru.uid)

    await g._mapear_santos([frio, vivo], _marca)
    assert visto == ["VIVO"], visto

    src = inspect.getsource(BeruCazador._mapear_santos)
    assert "asyncio.gather" in src
    assert "en_cooldown_api" in src
    src_acecho = inspect.getsource(BeruCazador.auditar_gatillos_adan)
    src_caza = inspect.getsource(BeruCazador._acordeon_cazador_capas)
    assert "_mapear_santos" in src_acecho
    assert "_mapear_santos" in src_caza


def main() -> int:
    asyncio.run(_probar())
    print("OK pulso paralelo Beru · cupo · cooldown por Santo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
