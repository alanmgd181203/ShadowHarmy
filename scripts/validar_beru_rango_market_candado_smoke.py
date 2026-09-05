#!/usr/bin/env python3
"""Smoke — candado Market + saco = masa real de casa."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango as br
from core import beru_rango_altar as altar
from core.bridge import OrdenResultado
from core.models import BeruShip
from generales.beru_rango import BeruRango


class Bel:
    async def anotar(self, *_a, **_k):
        return None


class Tusk:
    pesos = {}


def _beru_cazando() -> BeruShip:
    b = BeruShip(
        uid="T_MKT",
        centro_local=100.0,
        masa=1.0,
        direccion="LONG",
        estado="CAZANDO",
        oz_adan=100.2,
    )
    b.cero_wake = 100.0
    b.trail_extremo = 100.0
    b.tramo_precio_activacion = 100.0
    b.caza_trail_iniciado = True
    b.pierna_snap_usd = 0.0
    b.pierna_snap_lado = "LONG"
    return b


async def _test_market_no_repite() -> None:
    beru = _beru_cazando()
    bridge = MagicMock()
    bridge.place_order = AsyncMock(
        return_value=OrdenResultado(True, order_id="1", link_id="BRGMKT-1", datos={"avgPrice": "100.2"}),
    )
    with patch.object(altar, "plan_trailing_entrada") as plan_m:
        plan = MagicMock()
        plan.symbol = "ETHUSDT"
        plan.side = "Buy"
        plan.qty = 0.01
        plan.link_id = "BRGMKT-1"
        plan.category = "linear"
        plan.position_idx = 1
        plan.masa_usd = 1.23
        plan_m.return_value = plan
        r1 = await altar.disparar_entrada_market(bridge, beru, activo="ETH", masa_usd=1.0)
        assert r1.exito, r1
        assert beru.altar_entrada_disparada is True
        assert float(beru.altar_masa_colocada_usd) == 1.23
        r2 = await altar.disparar_entrada_market(bridge, beru, activo="ETH", masa_usd=1.0)
        assert not r2.exito
        assert "entrada_ya_disparada" in str(r2.mensaje)
        assert bridge.place_order.await_count == 1
    print("  market: segundo disparo bloqueado OK")


def _test_cosecha_masa_real() -> None:
    b = BeruShip(uid="T_SACO", centro_local=100.0, masa=5.0, direccion="LONG", estado="CAZANDO")
    b.cero_wake = 100.0
    b.oz_adan = 100.2
    br.cosechar_oz_y_mover_cero(b, 100.2, oz_despliegue=100.2, masa_usd=1.37)
    assert abs(float(b.saco_long_usd) - 1.37) < 1e-9, b.saco_long_usd
    assert abs(float(b.ultima_masa_cosechada) - 1.37) < 1e-9
    print("  cosecha: saco usa masa_usd real OK")


async def _test_pulso_saco_delta() -> None:
    os.environ["BERU_RANGO_MANOS"] = "1"
    import core.config as config

    config.BERU_RANGO_MANOS = True
    g = BeruRango(Tusk(), Bel(), MagicMock(), bridge=MagicMock())
    g._activo = "ETH"
    beru = _beru_cazando()
    beru.masa = 5.0  # doctrinal miente
    beru.altar_link_id = "BRGTEST"
    beru.pierna_snap_usd = 10.0
    g.vivo = beru
    g._consultar_fill = AsyncMock(return_value=None)  # type: ignore[method-assign]
    g._reconciliar_casa = AsyncMock()  # type: ignore[method-assign]
    g._delta_pierna_tramo = MagicMock(  # type: ignore[method-assign]
        return_value={"avgPrice": 100.18, "masa_usd": 1.41, "orderStatus": "Filled"},
    )
    g._precio_lineal = MagicMock(return_value=100.25)  # type: ignore[method-assign]

    with patch(
        "generales.beru_rango.beru_rango_altar.seguir_trailing",
        new_callable=AsyncMock,
    ), patch(
        "generales.beru_rango.beru_rango_altar.cancelar_pendiente",
        new_callable=AsyncMock,
    ):
        out = await g.pulso(precio=100.25, latido={"last": 100.25, "high": 100.25, "low": 100.0})
    assert out.get("evento") == "OZ_COSECHA", out
    assert abs(float(out.get("masa_hecha") or 0) - 1.41) < 1e-9, out
    assert abs(float(beru.saco_long_usd) - 1.41) < 1e-9, beru.saco_long_usd
    print("  pulso manos: saco=delta casa OK")


async def _test_reparar_no_market_si_sellado() -> None:
    os.environ["BERU_RANGO_MANOS"] = "1"
    import core.config as config

    config.BERU_RANGO_MANOS = True
    g = BeruRango(Tusk(), Bel(), MagicMock(), bridge=MagicMock())
    g._activo = "ETH"
    beru = _beru_cazando()
    # LONG: Oz detrás del extremo; last lejos para no tocar Oz este latido.
    beru.trail_extremo = 99.0
    beru.oz_adan = 99.0 * 1.002
    beru.altar_entrada_disparada = True
    beru.altar_link_id = "BRGMKT-x"
    beru.altar_order_status = "MarketSent"
    g.vivo = beru
    g._precio_lineal = MagicMock(return_value=98.5)  # type: ignore[method-assign]
    g._intentar_sello_entrada = AsyncMock(return_value=True)  # type: ignore[method-assign]
    g.bridge.get_order_status = AsyncMock(return_value=None)

    with patch(
        "generales.beru_rango.beru_rango_altar.seguir_trailing",
        new_callable=AsyncMock,
    ) as seg:
        out = await g.pulso(precio=98.5, latido={"last": 98.5, "high": 98.5, "low": 98.0})
    assert out.get("evento") == "CAZA", out
    g._intentar_sello_entrada.assert_not_awaited()
    seg.assert_awaited()
    print("  REPARAR: no intenta sello si Market ya sellado OK")


async def main() -> int:
    print("=== validar_beru_rango_market_candado_smoke ===")
    await _test_market_no_repite()
    _test_cosecha_masa_real()
    await _test_pulso_saco_delta()
    await _test_reparar_no_market_si_sellado()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
