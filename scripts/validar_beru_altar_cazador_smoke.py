#!/usr/bin/env python3
"""Smoke simulación — cuatro grados con Hoz CONDICIONAL, sin tumores."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_altar_cazador as altar
from generales.capitanes import CapitanNormal


def _barco(uid: str, tier_id: str) -> BeruShip:
    return BeruShip(
        uid=uid,
        centro_local=100.0,
        centro_manto=100.0,
        ancla_tramo=100.0,
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        adn_capitan=CapitanNormal,
        modo_combate="CAZA",
        tier_id=tier_id,
    )


def _camino_subida() -> list[float]:
    # Vacío 1.1 → Red 1.2 → 1.3 → 1.4 → vuelve a Hoz (cosecha)
    return [
        100.0,
        100.85,  # aún no
        101.10,  # arma
        101.20,  # toca Red → mover + masa
        101.30,  # mover
        101.40,  # mover
        101.35,  # entre Hoz y Red (Hoz ya avanzó)
        101.10,  # toca Hoz → cosecha (Hoz quedó en 1.3 tras 3 movidas)
    ]


def main() -> int:
    assert altar.arma_de_grado("SOLDADO") == "CONDICIONAL"
    assert altar.arma_de_grado("CAPITAN") == "CONDICIONAL"
    assert altar.arma_de_grado("GENERAL") == "CONDICIONAL"
    assert altar.arma_de_grado("MARISCAL") == "CONDICIONAL"

    # engorde fijo: Soldado $0.625/peldaño · Mariscal $5/peldaño (como G_min=$5)
    with patch("core.beru_cazador.engorde_paso_usd", side_effect=lambda a, g: {
        "SOLDADO": 0.625,
        "CAPITAN": 1.25,
        "GENERAL": 2.5,
        "MARISCAL": 5.0,
    }.get(str(g).upper(), 5.0)):
        soldado = _barco("BERU_SOLD", "BERUBBY")
        ev_s = altar.simular_camino(soldado, _camino_subida(), activo="ETH")
        tipos_s = [e.tipo for e in ev_s]
        assert "ARMAR_CONDICIONAL" in tipos_s, tipos_s
        assert "MOVER_CONDICIONAL" in tipos_s, tipos_s
        assert "COSECHA_CONDICIONAL" in tipos_s, tipos_s
        assert all(e.arma == "CONDICIONAL" for e in ev_s)
        assert "ARMAR_TRAILING" not in tipos_s
        assert [round(e.masa, 3) for e in ev_s if e.tipo == "MOVER_CONDICIONAL"] == [
            6.875, 7.5, 8.125,
        ]
        assert soldado.estado == "COSECHADO"
        assert soldado.relevo_creado
        assert soldado.funeral_red_confirmado
        assert soldado.modo_combate == "CAZA"
        assert not soldado.ciclo_infinito
        assert float(soldado.masa_congelada or 0) == 0.0

        mariscal = _barco("BERU_MAR", "PLENO")
        ev_m = altar.simular_camino(mariscal, _camino_subida(), activo="ETH")
        tipos_m = [e.tipo for e in ev_m]
        assert "ARMAR_CONDICIONAL" in tipos_m, tipos_m
        assert "MOVER_CONDICIONAL" in tipos_m, tipos_m
        assert "COSECHA_CONDICIONAL" in tipos_m, tipos_m
        assert all(e.arma == "CONDICIONAL" for e in ev_m)
        assert not any("TRAILING" in tipo for tipo in tipos_m)
        assert mariscal.estado == "COSECHADO"
        assert mariscal.relevo_creado
        assert mariscal.funeral_red_confirmado

        # Masa: primera Hoz 10 peldaños × engorde; +3 toques Red
        # Mariscal: 50 + 3*5 = 65 al último mover; tras cosecha 0
        assert [e.masa for e in ev_m if e.tipo == "MOVER_CONDICIONAL"] == [
            55.0, 60.0, 65.0,
        ]
        assert [e.masa for e in ev_m if e.tipo == "COSECHA_CONDICIONAL"] == [65.0]
        assert mariscal.masa == 0.0
        # Mariscal no cae a Vacío/plan A: su recorrido termina con la caza.
        assert mariscal.relevo_cazador_uid == ""

        # Capitán también CONDICIONAL
        cap = _barco("BERU_CAP", "PROTO2")
        ev_c = altar.simular_camino(cap, [100.0, 101.1, 101.2], activo="ETH")
        assert ev_c[0].tipo == "ARMAR_CONDICIONAL"
        assert ev_c[1].tipo == "MOVER_CONDICIONAL"
        assert abs(cap.masa - (1.25 * 10 + 1.25)) < 1e-6  # 10 peldaños + 1

        # Tumor: modo negociador debe fallar el candado
        malo = _barco("BERU_MAL", "BERUBBY")
        malo.modo_combate = "NEGOCIADOR"
        try:
            altar.pulsar_cazador_sim(malo, 101.3)
            raise AssertionError("debió rechazar tumor NEGOCIADOR")
        except AssertionError as e:
            assert "tumor" in str(e)

    # Fósiles del General no deben revivir negociador
    import asyncio
    from generales.beru import BeruCazador

    class _Bel:
        def __init__(self):
            self.eventos = []

        async def anotar(self, *a, **k):
            self.eventos.append((a, k))
            return None

    class _Tank:
        capitan_activo = CapitanNormal

    class _Tusk:
        # Engorde exige manto vivo de ese Santo.
        pesos = {
            "ETHUSDT_LINEAL": {
                "long": 1000.0,
                "short": 1000.0,
                "precio_medio_long": 100.0,
                "precio_medio_short": 100.0,
            }
        }
        masa_autorizada = 0.0

        async def solicitar_reserva(self, *a, **k):
            return True

    bel = _Bel()
    g = BeruCazador(_Tusk(), bel, _Tank())
    assert asyncio.run(g._pulsar_negociador_post_cazador(100.0)) is None
    assert asyncio.run(g._pulsar_clonacion_residual(100.0)) is None
    assert asyncio.run(g._crear_negociador_post_cazador(
        soldado, 100.0, 0.01, 100.0,
    )) is None
    assert asyncio.run(g.evaluar_colisiones_y_fusion()) is None

    # Cable real del General: Mariscal toca Red, replanta condicional y engorda.
    mar_general = _barco("BERU_MAR_GENERAL", "PLENO")
    with patch("core.beru_cazador.engorde_paso_usd", return_value=5.0):
        altar.pulsar_cazador_sim(mar_general, 100.0, activo="ETH")
        altar.pulsar_cazador_sim(mar_general, 101.1, activo="ETH")
        assert mar_general.masa == 50.0
        g.legion = [mar_general]
        g._precio_de_barco = lambda _b: float(mar_general.red_adan)
        asyncio.run(g._acordeon_cazador_capas(0.0))
    assert mar_general.masa == 55.0
    assert mar_general.arma_cazador == "CONDICIONAL"
    assert any(
        args[1] == "MOVER_CONDICIONAL"
        for args, _kwargs in bel.eventos
        if len(args) >= 2
    )
    assert not any(
        "TRAILING" in str(args)
        for args, _kwargs in bel.eventos
    )

    print("OK validar_beru_altar_cazador_smoke")
    print("soldado:", altar.resumen_bitacora(ev_s))
    print("mariscal:", altar.resumen_bitacora(ev_m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
