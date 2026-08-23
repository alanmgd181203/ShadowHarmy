#!/usr/bin/env python3
"""Stress frío: 300 relevos cazadores, dos lados, tres grados."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_altar_cazador as altar
from generales.capitanes import CapitanNormal


PASO = {
    "SOLDADO": 0.625,
    "CAPITAN": 1.25,
    "GENERAL": 2.50,
}
CASOS = (
    ("BERUBBY", "SOLDADO"),
    ("PROTO2", "CAPITAN"),
    ("PROTO1", "GENERAL"),
)


def semilla(tier: str, centro: float, lado: str) -> BeruShip:
    return BeruShip(
        uid=f"BERU_SEM_ETH_STRESS_{tier}_{lado}",
        centro_local=centro,
        centro_manto=centro,
        ancla_tramo=centro,
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        adn_capitan=CapitanNormal,
        tier_id=tier,
        modo_combate="CAZA",
    )


def correr_linea(tier: str, grado: str, signo: int, generaciones: int = 50) -> int:
    centro = 1000.0
    actual = semilla(tier, centro, "UP" if signo > 0 else "DOWN")
    vistos = {actual.uid}
    relevos = 0
    altar.pulsar_cazador_sim(actual, centro, activo="ETH")

    for gen in range(generaciones):
        ancla = float(actual.ancla_tramo)
        if str(actual.estado) == "ACECHANDO":
            if bool(getattr(actual, "oreja_red_activa", False)):
                px_llamado = float(actual.ultima_red_tocada_precio) + signo * centro * float(
                    actual.llamado_red_pct
                )
            else:
                px_llamado = ancla + signo * centro * 0.011
        else:
            px_llamado = ancla + signo * centro * (
                float(actual.llamado_tramo_pct) if float(actual.llamado_tramo_pct or 0) > 0 else 0.011
            )
        r = altar.pulsar_cazador_sim(actual, px_llamado, activo="ETH")
        assert r.eventos and r.eventos[0].tipo == "ARMAR_CONDICIONAL"
        if str(actual.estado) == "ACECHANDO" and bool(getattr(actual, "oreja_red_activa", False)):
            assert not actual.oreja_sangre_activa

        # Entre 1 y 5 Red tocadas: memoria exacta de la última.
        pasos = 1 + (gen % 5)
        ultima = 0.0
        for _ in range(pasos):
            ultima = float(actual.red_adan)
            altar.pulsar_cazador_sim(actual, ultima, activo="ETH")
            assert abs(actual.ultima_red_tocada_precio - ultima) < 1e-7

        hoz = float(actual.oz_adan)
        r = altar.pulsar_cazador_sim(actual, hoz, activo="ETH")
        hijo = r.relevo
        assert hijo is not None
        assert actual.estado == "COSECHADO"
        assert actual.funeral_red_confirmado
        assert actual.red_adan == 0.0
        assert hijo.uid not in vistos
        vistos.add(hijo.uid)
        assert hijo.padre_cazador_uid == actual.uid
        assert abs(hijo.ancla_tramo - hoz) < 1e-7
        assert hijo.oreja_sangre_activa
        assert hijo.modo_combate == "CAZA"
        assert not hijo.ciclo_infinito
        assert not hijo.neg_post_cazador
        assert hijo.masa_congelada == 0.0

        # Aviso duplicado de fill: jamás un segundo hijo.
        assert altar.crear_relevo_desde_hoz(
            actual, hoz, activo="ETH", fill_confirmado=True,
        ) is None
        actual = hijo
        relevos += 1

    return relevos


def main() -> int:
    total = 0
    with patch(
        "core.beru_cazador.engorde_paso_usd",
        side_effect=lambda _a, g: PASO.get(str(g).upper(), 5.0),
    ):
        for tier, grado in CASOS:
            total += correr_linea(tier, grado, +1)
            total += correr_linea(tier, grado, -1)
    assert total == 300
    print(
        "OK validar_beru_relevo_stress "
        "(300 relevos · 900 Red promedio · ± · cero duplicados/tumores)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
