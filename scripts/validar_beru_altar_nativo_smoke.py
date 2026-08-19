#!/usr/bin/env python3
"""Smoke frío — Hoz condicional nativa para los cuatro grados."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_ley
from core.beru_altar_nativo import (
    armar_condicional,
    cancelar_confirmado,
    consultar_fill,
    link_id_determinista,
    mover_condicional,
    plan_condicional_spot,
    replantar_sin_esperar_sello,
)
from core.bridge import BybitBridge, OrdenResultado
from core.models import BeruShip


class BridgeFalso:
    def __init__(self) -> None:
        self.ordenes: dict[str, dict] = {}
        self.creadas = 0
        self.canceladas = 0
        self.enmendadas = 0

    async def get_order_status(self, symbol, *, link_id, category, order_filter=None):
        assert order_filter == "StopOrder"
        orden = self.ordenes.get(link_id)
        if orden is None:
            return OrdenResultado(
                False, link_id=link_id, mensaje="orden_no_encontrada",
                datos={"not_found": True},
            )
        return OrdenResultado(
            True,
            order_id=orden["orderId"],
            link_id=link_id,
            mensaje=orden["orderStatus"],
            datos=dict(orden),
        )

    async def place_order(self, symbol, side, qty, **kwargs):
        link_id = kwargs["link_id"]
        self.creadas += 1
        orden = {
            "orderId": f"O-{self.creadas}",
            "orderLinkId": link_id,
            "orderStatus": "Untriggered",
            "symbol": symbol,
            "side": side,
            "qty": qty,
        }
        self.ordenes[link_id] = orden
        return OrdenResultado(
            True, order_id=orden["orderId"], link_id=link_id, datos=orden,
        )

    async def cancel_order(self, symbol, *, link_id, category, order_filter=None):
        assert order_filter == "StopOrder"
        self.canceladas += 1
        self.ordenes[link_id]["orderStatus"] = "Cancelled"
        return OrdenResultado(True, link_id=link_id)

    async def amend_order(
        self, symbol, order_id=None, link_id=None,
        new_qty=None, new_price=None, new_trigger_price=None, category="linear",
    ):
        orden = self.ordenes.get(link_id)
        if orden is None:
            return OrdenResultado(False, mensaje="amend_no_encontrada")
        self.enmendadas += 1
        if new_qty is not None:
            orden["qty"] = new_qty
        if new_trigger_price is not None:
            orden["triggerPrice"] = float(new_trigger_price)
        return OrdenResultado(
            True, order_id=orden["orderId"], link_id=link_id, datos=orden,
        )


class BridgeIncierto(BridgeFalso):
    async def get_order_status(self, symbol, *, link_id, category, order_filter=None):
        assert order_filter == "StopOrder"
        return OrdenResultado(
            False, link_id=link_id, mensaje="timeout",
            datos={"not_found": False},
        )


class SessionFalsa:
    def __init__(self) -> None:
        self.params = None

    def place_order(self, **params):
        self.params = dict(params)
        return {
            "retCode": 0,
            "retMsg": "OK",
            "result": {"orderId": "OID-NATIVO"},
        }


class BellionFalso:
    async def anotar(self, *_args, **_kwargs):
        return None


def _beru(direccion: str = "LONG", tier_id: str = "PROTO1") -> BeruShip:
    return BeruShip(
        uid=f"BERU_ETH_{direccion}_{tier_id}",
        centro_local=100.0,
        masa=5.0,
        direccion=direccion,
        estado="CAZANDO",
        oz_adan=99.8 if direccion == "LONG" else 100.2,
        tier_id=tier_id,
        modo_combate="CAZA",
    )


async def _probar() -> None:
    puente = object.__new__(BybitBridge)
    puente.session = SessionFalsa()
    puente.bel = BellionFalso()
    enviada = await puente.place_order(
        "ETHUSDT", "Buy", 0.05,
        category="spot",
        is_leverage=1,
        link_id="BERU-PRUEBA",
        trigger_price=99.8,
        trigger_direction=1,
        trigger_by="LastPrice",
        order_filter="StopOrder",
    )
    assert enviada.exito
    assert puente.session.params["triggerPrice"] == "99.8"
    assert "triggerDirection" not in puente.session.params
    assert "triggerBy" not in puente.session.params
    assert puente.session.params["orderFilter"] == "StopOrder"

    linear = await puente.place_order(
        "ETHUSDT", "Buy", 0.01,
        category="linear",
        link_id="BERU-LIN",
        trigger_price=100.0,
        trigger_direction=0,
    )
    assert not linear.exito

    long = _beru("LONG")
    sello0 = link_id_determinista(long)
    assert sello0 == link_id_determinista(long)
    assert len(sello0) <= 36

    plan = plan_condicional_spot(
        long, activo="ETH", masa_usd=5.0, trigger_price=99.8,
    )
    assert plan.side == "Buy"
    assert plan.qty > 0
    assert plan.market_unit == "baseCoin"
    assert plan.is_leverage == (1 if beru_ley.spot_margen_activo() else 0)
    assert plan.trigger_direction == 1

    short = _beru("SHORT")
    plan_short = plan_condicional_spot(
        short, activo="ETH", masa_usd=5.0, trigger_price=100.2,
    )
    assert plan_short.side == "Sell"
    assert plan_short.qty > 0
    assert plan_short.trigger_direction == 2

    bridge = BridgeFalso()
    creada = await armar_condicional(bridge, long, plan)
    assert creada.exito and bridge.creadas == 1
    # Recovery/reintento con el mismo sello consulta primero: cero duplicado.
    recuperada = await armar_condicional(bridge, long, plan)
    assert recuperada.exito and bridge.creadas == 1

    movida, motivo = await mover_condicional(
        bridge, long, activo="ETH", masa_usd=7.0, trigger_price=99.9,
    )
    assert motivo == "enmendada"
    assert movida is not None and movida.exito
    assert bridge.enmendadas == 1 and bridge.canceladas == 0 and bridge.creadas == 1
    assert long.altar_revision == 0
    assert long.altar_link_id == sello0
    assert long.altar_trigger_price == 99.9

    # Mariscal usa exactamente la misma carta: Beru mueve Hoz y masa acumulada.
    mariscal = _beru("SHORT", "PLENO")
    plan_mariscal = plan_condicional_spot(
        mariscal, activo="ETH", masa_usd=40.0, trigger_price=100.8,
    )
    assert plan_mariscal.side == "Sell"
    creada_mariscal = await armar_condicional(bridge, mariscal, plan_mariscal)
    assert creada_mariscal.exito and bridge.creadas == 2
    movida_mariscal, motivo = await mover_condicional(
        bridge,
        mariscal,
        activo="ETH",
        masa_usd=55.0,
        trigger_price=101.1,
    )
    assert motivo == "enmendada"
    assert movida_mariscal is not None and movida_mariscal.exito
    assert bridge.enmendadas == 2 and bridge.canceladas == 0 and bridge.creadas == 2
    assert mariscal.altar_revision == 0
    assert mariscal.altar_trigger_price == 101.1

    class BridgeAmendMuerto(BridgeFalso):
        async def amend_order(self, *a, **k):
            return OrdenResultado(False, mensaje="amend_rechazado")

    plan_b = BridgeAmendMuerto()
    b2 = _beru("LONG")
    plan2 = plan_condicional_spot(b2, activo="ETH", masa_usd=5.0, trigger_price=99.8)
    await armar_condicional(plan_b, b2, plan2)
    sello_b = b2.altar_link_id
    mov_b, mot_b = await mover_condicional(
        plan_b, b2, activo="ETH", masa_usd=7.0, trigger_price=99.9,
    )
    assert mot_b == "replantada"
    assert plan_b.canceladas == 1 and plan_b.creadas == 2
    assert b2.altar_revision == 0
    assert b2.altar_link_id == sello_b

    incierto = BridgeIncierto()
    bloqueada = await armar_condicional(incierto, _beru(), plan)
    assert not bloqueada.exito and incierto.creadas == 0

    # Fill confirmado: el General cosecha sin Market.
    bridge.ordenes[long.altar_link_id]["orderStatus"] = "Filled"
    bridge.ordenes[long.altar_link_id]["avgPrice"] = 99.9
    bridge.ordenes[long.altar_link_id]["cumExecQty"] = 0.05
    fill = await consultar_fill(bridge, long, activo="ETH")
    assert fill is not None
    assert fill["avgPrice"] == 99.9
    assert fill["cumExecQty"] == 0.05

    muerta = _beru("LONG")
    puente_m = BridgeFalso()
    plan_m = plan_condicional_spot(muerta, activo="ETH", masa_usd=5.0, trigger_price=99.8)
    await armar_condicional(puente_m, muerta, plan_m)
    puente_m.ordenes[plan_m.link_id]["orderStatus"] = "Deactivated"
    muerta.altar_order_status = "Deactivated"
    sello_m = plan_m.link_id
    otra = await armar_condicional(puente_m, muerta, plan_m)
    assert otra.exito and puente_m.creadas == 2
    assert muerta.altar_order_status == "Untriggered"
    assert muerta.altar_link_id == sello_m
    assert muerta.altar_revision == 0

    class BridgeDuplicado(BridgeFalso):
        async def place_order(self, symbol, side, qty, **kwargs):
            link_id = kwargs["link_id"]
            if self.creadas == 0:
                self.creadas += 1
                return OrdenResultado(
                    False, link_id=link_id,
                    mensaje="Duplicate clientOrderId. (ErrCode: 170141)",
                    datos={"retCode": 170141},
                )
            return await BridgeFalso.place_order(self, symbol, side, qty, **kwargs)

    dup = BridgeDuplicado()
    bdup = _beru("LONG")
    plan_d = plan_condicional_spot(bdup, activo="ETH", masa_usd=5.0, trigger_price=99.8)
    sello_d = plan_d.link_id
    creada_d = await armar_condicional(dup, bdup, plan_d)
    assert creada_d.exito and dup.creadas == 2
    assert bdup.altar_link_id != sello_d

    huérfana = _beru("LONG")
    huérfana.altar_link_id = "BERU-HOZ-0-desaparecida"
    ok_nf, mot_nf = await cancelar_confirmado(bridge, huérfana, symbol="ETHUSDT")
    assert ok_nf and mot_nf == "no_existia"

    class Bridge170213(BridgeFalso):
        async def get_order_status(self, symbol, *, link_id, category, order_filter=None):
            return OrdenResultado(
                False, link_id=link_id,
                mensaje="Order does not exist. (ErrCode: 170213)",
                datos={"retCode": 170213},
            )

        async def cancel_order(self, *a, **k):
            raise AssertionError("170213 no debe martillar cancel")

    ok_213, mot_213 = await cancelar_confirmado(
        Bridge170213(), huérfana, symbol="ETHUSDT",
    )
    assert ok_213 and mot_213 == "no_existia"

    class BridgeCancel170213(BridgeFalso):
        async def cancel_order(self, symbol, *, link_id, category, order_filter=None):
            self.canceladas += 1
            self.ordenes.pop(link_id, None)
            return OrdenResultado(
                False, link_id=link_id,
                mensaje="Order does not exist. (ErrCode: 170213)",
                datos={"retCode": 170213},
            )

    plan_r = BridgeCancel170213()
    br = _beru("LONG")
    plan_rr = plan_condicional_spot(br, activo="ETH", masa_usd=5.0, trigger_price=99.8)
    await armar_condicional(plan_r, br, plan_rr)
    sello_r = br.altar_link_id
    rev_r = int(br.altar_revision or 0)
    creada_r, mot_r = await replantar_sin_esperar_sello(
        plan_r, br, activo="ETH", masa_usd=5.0, trigger_price=99.7,
    )
    assert mot_r == "replantada" and creada_r.exito
    assert br.altar_link_id == sello_r
    assert int(br.altar_revision or 0) == rev_r


def main() -> int:
    asyncio.run(_probar())
    print("OK altar nativo Beru · cuatro grados · Mariscal mueve Hoz · fill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
