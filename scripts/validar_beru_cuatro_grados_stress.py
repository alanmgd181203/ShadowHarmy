#!/usr/bin/env python3
"""Stress frío: cuatro grados mueven Hoz condicional y acumulan toda la masa."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_altar_cazador as altar
from core.models import BeruShip
from generales.capitanes import CapitanNormal


PASO = {
    "SOLDADO": 0.625,
    "CAPITAN": 1.25,
    "GENERAL": 2.50,
    "MARISCAL": 5.00,
}
CASOS = (
    ("BERUBBY", "SOLDADO"),
    ("PROTO2", "CAPITAN"),
    ("PROTO1", "GENERAL"),
    ("PLENO", "MARISCAL"),
)


def _barco(tier: str, grado: str, signo: int, vuelta: int) -> BeruShip:
    lado = "SUBE" if signo > 0 else "BAJA"
    return BeruShip(
        uid=f"BERU_STRESS_{grado}_{lado}_{vuelta}",
        centro_local=1000.0,
        centro_manto=1000.0,
        ancla_tramo=1000.0,
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        adn_capitan=CapitanNormal,
        tier_id=tier,
        modo_combate="CAZA",
    )


def _correr(tier: str, grado: str, signo: int, vuelta: int) -> int:
    b = _barco(tier, grado, signo, vuelta)
    llamado = 1000.0 + signo * 11.0
    altar.pulsar_cazador_sim(b, 1000.0, activo="ETH")
    armado = altar.pulsar_cazador_sim(b, llamado, activo="ETH")
    assert [e.tipo for e in armado.eventos] == ["ARMAR_CONDICIONAL"]
    assert b.arma_cazador == "CONDICIONAL"

    por_peldano = PASO[grado]
    esperado = 10.0 * por_peldano
    assert abs(b.masa - esperado) < 1e-8

    movimientos = 1 + (vuelta % 20)
    for _ in range(movimientos):
        red_tocada = float(b.red_adan)
        movida = altar.pulsar_cazador_sim(b, red_tocada, activo="ETH")
        assert [e.tipo for e in movida.eventos] == ["MOVER_CONDICIONAL"]
        esperado += por_peldano
        assert abs(b.masa - esperado) < 1e-8
        assert abs(movida.eventos[0].masa - esperado) < 1e-8
        assert movida.eventos[0].arma == "CONDICIONAL"

    hoz = float(b.oz_adan)
    cosecha = altar.pulsar_cazador_sim(b, hoz, activo="ETH")
    assert [e.tipo for e in cosecha.eventos] == ["COSECHA_CONDICIONAL"]
    assert abs(cosecha.eventos[0].masa - esperado) < 1e-8
    assert b.estado == "COSECHADO"
    assert b.masa == 0.0
    assert b.funeral_red_confirmado
    assert not any("TRAILING" in e.tipo for e in armado.eventos + movida.eventos + cosecha.eventos)

    assert cosecha.relevo is not None
    assert cosecha.relevo.oreja_sangre_activa
    assert cosecha.relevo.oreja_red_activa
    return movimientos


def main() -> int:
    recorridos = 0
    movimientos = 0
    with patch(
        "core.beru_cazador.engorde_paso_usd",
        side_effect=lambda _activo, grado: PASO[str(grado).upper()],
    ):
        for tier, grado in CASOS:
            for signo in (+1, -1):
                for vuelta in range(50):
                    movimientos += _correr(tier, grado, signo, vuelta)
                    recorridos += 1

    assert recorridos == 400
    assert movimientos == 3800
    print(
        "OK validar_beru_cuatro_grados_stress "
        "(400 recorridos · 3800 Hoces movidas · masa acumulada exacta · ±)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
