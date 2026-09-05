#!/usr/bin/env python3
"""Smoke — candado fill: manos exige plata; ojos sigue en mapa."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from generales.beru_rango import BeruRango
from core import beru_rango as br


class Bel:
    async def anotar(self, *_a, **_k):
        return None


class Tusk:
    pesos = {}


def _beru_cazando() -> BeruShip:
    b = BeruShip(
        uid="T_FILL",
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
    return b


async def _test_oz_sin_fill_manos() -> None:
    os.environ["BERU_RANGO_MANOS"] = "1"
    import core.config as config

    config.BERU_RANGO_MANOS = True
    tusk = Tusk()
    g = BeruRango(tusk, Bel(), MagicMock(), bridge=MagicMock())
    g._activo = "ETH"
    beru = _beru_cazando()
    g.vivo = beru
    g._consultar_fill = AsyncMock(return_value=None)  # type: ignore[method-assign]
    g._reconciliar_casa = AsyncMock()  # type: ignore[method-assign]
    g._posicion_tramo_casa = MagicMock(return_value=None)  # type: ignore[method-assign]
    g._precio_lineal = MagicMock(return_value=100.25)  # type: ignore[method-assign]

  # Market falla → no cosecha
    from core.bridge import OrdenResultado

    with patch(
        "generales.beru_rango.beru_rango_altar.cancelar_pendiente",
        new_callable=AsyncMock,
    ), patch(
        "generales.beru_rango.beru_rango_altar.disparar_entrada_market",
        new_callable=AsyncMock,
        return_value=OrdenResultado(False, mensaje="rechazada"),
    ), patch(
        "generales.beru_rango.beru_rango_altar.seguir_trailing",
        new_callable=AsyncMock,
    ):
        out = await g.pulso(precio=100.25, latido={"last": 100.25, "high": 100.25, "low": 100.0})
    assert out.get("evento") == "CAZA", out
    assert out.get("nota") == "oz_sin_fill_casa", out
    assert beru.estado == "CAZANDO", beru.estado
    print("  manos: Oz sin fill no cosecha OK")


async def _test_oz_con_posicion_casa() -> None:
    os.environ["BERU_RANGO_MANOS"] = "1"
    import core.config as config

    config.BERU_RANGO_MANOS = True
    tusk = Tusk()
    g = BeruRango(tusk, Bel(), MagicMock(), bridge=MagicMock())
    g._activo = "ETH"
    beru = _beru_cazando()
    beru.altar_link_id = "BRGTEST"
    beru.pierna_snap_usd = 0.0
    beru.pierna_snap_lado = "LONG"
    g.vivo = beru
    g._consultar_fill = AsyncMock(return_value=None)  # type: ignore[method-assign]
    g._reconciliar_casa = AsyncMock()  # type: ignore[method-assign]
    g._delta_pierna_tramo = MagicMock(  # type: ignore[method-assign]
        return_value={"avgPrice": 100.18, "masa_usd": 1.0, "orderStatus": "Filled"},
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
    assert beru.estado == "ACECHANDO", beru.estado
    assert abs(float(out.get("masa_hecha") or 0) - 1.0) < 1e-9, out
    print("  manos: Oz con delta casa cosecha OK")


async def _test_consultar_fill_sin_avg() -> None:
    """_consultar_fill no acepta Filled sin avgPrice (OKX algo)."""
    g = BeruRango(Tusk(), Bel(), MagicMock(), bridge=MagicMock())
    g._activo = "ETH"
    beru = _beru_cazando()
    beru.altar_link_id = "BRGTEST"

    async def _estado(*_a, **_k):
        from core.bridge import OrdenResultado

        return OrdenResultado(
            True,
            mensaje="Filled",
            datos={"orderStatus": "Filled", "avgPrice": "0"},
        )

    g.bridge.get_order_status = AsyncMock(side_effect=_estado)
    out = await g._consultar_fill(beru)
    assert out is None
    print("  consultar_fill sin avg -> None OK")


def _test_ojos_cosecha_mapa() -> None:
    os.environ.pop("BERU_RANGO_MANOS", None)
    import core.config as config

    config.BERU_RANGO_MANOS = False
    b = BeruShip(uid="T_OJOS", centro_local=100.0, masa=5.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ABAJO", precio=98.8)
    br.actualizar_trailing_oz(b, 98.8)
    oz = float(b.oz_adan)
    br.cosechar_oz_y_mover_cero(b, oz, oz_despliegue=oz)
    assert b.estado == "ACECHANDO"
    assert float(b.saco_long_usd or 0) > 0
    print("  ojos/teatro: cosecha mapa sin manos OK")


async def main() -> int:
    print("=== validar_beru_rango_fill_guard_smoke ===")
    await _test_consultar_fill_sin_avg()
    _test_ojos_cosecha_mapa()
    await _test_oz_sin_fill_manos()
    await _test_oz_con_posicion_casa()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
