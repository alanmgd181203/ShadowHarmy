#!/usr/bin/env python3
"""Candado frío — la ruta viva de Beru no alcanza fósiles."""
from __future__ import annotations

import asyncio
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_continuo
from core import beru_tier
from generales.beru import BeruCazador
from generales.capitanes import CapitanNormal


class Bel:
    async def anotar(self, *args, **kwargs):
        return None


class Tank:
    capitan_activo = CapitanNormal


class Tusk:
    pesos = {}
    masa_autorizada = 0.0
    masa_bruta_real = 0.0
    masa_bruta = 0.0

    async def liberar_reserva(self, *args, **kwargs):
        return None


def main() -> int:
    src_mod = inspect.getsource(sys.modules["generales.beru"])
    cabecera = "\n".join(src_mod.splitlines()[:30])
    for import_tumor in (
        "from core import beru_negociador",
        "from core import beru_fusion",
        "from core import beru_mega_reset",
        "from core import beru_residual",
    ):
        assert import_tumor not in cabecera

    src_hilo = inspect.getsource(BeruCazador.hilo_beru_berserker)
    for llamada_tumor in (
        "_pulsar_negociador",
        "_pulsar_clonacion",
        "evaluar_colisiones",
        "_fusion",
        "_purga_mega",
    ):
        assert llamada_tumor not in src_hilo
    # Un fósil no puede congelar a toda la flota.
    assert "if any(b.estado == \"FOSIL_BLOQUEADO\"" not in src_hilo
    assert "FOSIL_BLOQUEADO" not in src_hilo or "_cuarentena_tumores" in src_hilo

    src_caza = inspect.getsource(BeruCazador._acordeon_cazador_capas)
    for nombre_tumor in ("NEGOCIADOR", "residual", "fusion", "Mega"):
        assert nombre_tumor not in src_caza
    assert "_precio_de_barco" in src_caza

    src_cosecha = inspect.getsource(BeruCazador._ejecutar_cosecha)
    assert "base=act" in src_cosecha
    assert "_precio_de_barco(barco)" in src_cosecha

    # Las dos puertas matemáticas que podían reanimar la ruta vieja fallan duro.
    try:
        beru_tier.tier_por_id("PROTO1").pasos("NEGOCIADOR")  # type: ignore[arg-type]
        raise AssertionError("NEGOCIADOR no debe entregar pasos")
    except RuntimeError as exc:
        assert "FOSIL_BLOQUEADO" in str(exc)

    b = BeruShip(
        uid="BERU_SEM_ETH_FOSIL",
        centro_local=100.0,
        centro_manto=100.0,
        masa=35.0,
        direccion="SHORT",
        estado="CAZANDO",
        adn_capitan=CapitanNormal,
        tier_id="PROTO1",
        modo_combate="CAZA",
    )
    try:
        beru_continuo.reiniciar_tras_cosecha(b, 100.0)
        raise AssertionError("Vacío desde fill no debe reiniciar al padre")
    except RuntimeError as exc:
        assert "FOSIL_BLOQUEADO" in str(exc)

    general = BeruCazador(Tusk(), Bel(), Tank())
    general.restaurar_legion([
        {
            "uid": "BERU_NEG_VIEJO",
            "centro_local": 100.0,
            "masa": 35.0,
            "direccion": "SHORT",
            "estado": "NEGOCIANDO",
            "modo_combate": "NEGOCIADOR",
            "ciclo_infinito": True,
            "masa_congelada": 35.0,
        },
        {
            "uid": "BERU_MEGA_VIEJO",
            "centro_local": 100.0,
            "masa": 70.0,
            "direccion": "SHORT",
            "estado": "ACECHANDO",
            "es_super_beru": True,
        },
    ])
    assert len(general.legion) == 2
    assert all(b.estado == "FOSIL_BLOQUEADO" for b in general.legion)

    # Un fósil en cuarentena no debe impedir que un cazador sano oiga su Santo.
    sano = BeruShip(
        uid="BERU_SEM_SOL_SANO",
        centro_local=50.0,
        centro_manto=50.0,
        ancla_tramo=50.0,
        masa=5.0,
        direccion="SHORT",
        estado="CAZANDO",
        oz_adan=50.4,
        red_adan=50.5,
        oz_pct=0.008,
        red_pct=0.009,
        adn_capitan=CapitanNormal,
        tier_id="BERUBBY",
        modo_combate="CAZA",
        frente_asignado="SOLUSDT_SPOT",
    )
    general.legion.append(sano)
    precios = {"ETH": 100.0, "SOL": 50.45}

    def precio_activo(act: str) -> float:
        return float(precios.get(str(act).upper(), 0.0))

    general._precio_de_activo = precio_activo
    general._precio_casa = lambda: 100.0
    # Casa en 100 no debe disparar la Hoz de SOL (50.4). Solo el precio SOL.
    asyncio.run(general._acordeon_cazador_capas(100.0))
    assert sano.estado == "CAZANDO"
    assert sano.oz_adan == 50.4
    # Precio del propio Santo toca la Hoz → intentaría cosechar.
    # Con manos OFF/simulación el camino sigue; aquí solo verificamos que oyó SOL.
    precios["SOL"] = 50.40
    # Sin bridge/manos reales: _ejecutar_cosecha abortará o diferirá, pero
    # el acordeón debe usar 50.40 y no 100.
    seen = {"px": None}

    async def cosecha_spy(beru, px):
        seen["px"] = float(px)

    general._cosecha_capa_cazador = cosecha_spy
    sano.qty_base_ejecutada = 0.1
    asyncio.run(general._acordeon_cazador_capas(100.0))
    assert seen["px"] == 50.40

    n_antes = len(general.legion)
    assert asyncio.run(general._pulsar_negociador_post_cazador(100.0)) is None
    assert asyncio.run(general._pulsar_clonacion_residual(100.0)) is None
    assert asyncio.run(general._crear_negociador_post_cazador(
        b, 100.0, 0.01, 100.0,
    )) is None
    assert asyncio.run(general.evaluar_colisiones_y_fusion()) is None
    assert len(general.legion) == n_antes

    # Aunque alguien encienda BERU_MANOS, el placeholder market no dispara.
    vivo = BeruShip(
        uid="BERU_SEM_ETH_NO_MARKET",
        centro_local=100.0,
        centro_manto=100.0,
        ancla_tramo=100.0,
        masa=5.0,
        direccion="SHORT",
        estado="ESPERANDO_MATERIALIZACION",
        adn_capitan=CapitanNormal,
        tier_id="BERUBBY",
        modo_combate="CAZA",
    )
    general._manos_activas = lambda: True
    general._manos_fantasma = lambda: False
    general._beru_caza_permitida = lambda _act=None: True
    with patch("generales.beru.config.MODO_SIMULACION", False):
        asyncio.run(general._ejecutar_caza(vivo))
    assert vivo.estado == "ALTAR_NATIVO_PENDIENTE"

    print(
        "OK validar_beru_sin_tumores_smoke "
        "(CAZA · fósiles en cuarentena · precio por Santo · market bloqueado)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
