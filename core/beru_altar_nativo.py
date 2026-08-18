"""Manos nativas del altar Beru, dormidas hasta integrarlas al pulso live.

Camino feliz: Hoz condicional. Cero Market de entrada.
La ráfaga Market (bocados mínimos, uno tras otro) vive en ``beru_rafaga``
y solo dispara si Bybit escupe la carta gorda — o la mínima — por ahogo.
- Los cuatro grados usan condicional spot sellada por ``orderLinkId``.
- Mariscal emula su trailing: Beru cancela y replanta la Hoz como los demás.
- Mover una Hoz exige cancelación confirmada antes de plantar la siguiente.
"""
from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Any

from core import beru_ley
from core import lote_bybit


TERMINALES = frozenset({
    "Filled", "Cancelled", "Rejected", "Deactivated",
    "PartiallyFilledCanceled",
})


@dataclass(frozen=True)
class PlanOrdenNativa:
    symbol: str
    category: str
    side: str
    qty: float
    market_unit: str | None
    is_leverage: int
    trigger_price: float
    trigger_direction: int
    link_id: str
    frente: str


def link_id_determinista(beru: Any, *, proposito: str = "HOZ") -> str:
    """Mismo Beru+revisión+propósito produce el mismo sello de reintento."""
    rev = int(getattr(beru, "altar_revision", 0) or 0)
    semilla = f"{getattr(beru, 'uid', '')}|{rev}|{proposito.upper()}"
    digest = hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:16]
    return f"BERU-{proposito.upper()[:4]}-{rev}-{digest}"[:36]


def plan_condicional_spot(
    beru: Any,
    *,
    activo: str,
    masa_usd: float,
    trigger_price: float,
) -> PlanOrdenNativa:
    act = str(activo or "").upper()
    direccion = str(getattr(beru, "direccion", "") or "").upper()
    px = float(trigger_price or 0)
    usd = float(masa_usd or 0)
    if not act or direccion not in ("LONG", "SHORT") or px <= 0 or usd <= 0:
        raise ValueError("plan condicional incompleto")

    frente = f"{act}USDT_SPOT"
    side = "Buy" if direccion == "LONG" else "Sell"
    # Dirección local para validar la Hoz. Spot no la envía a Bybit.
    trigger_direction = 1 if direccion == "LONG" else 2
    # Condicional spot: qty siempre en moneda base (no quoteCoin).
    modo = "ceil" if side == "Buy" else "floor"
    px = lote_bybit.cuantizar_precio(px, frente, mode=modo)
    if px <= 0:
        raise ValueError("gatillo no cuantizable al tick del frente")
    conv = lote_bybit.cuantizar_presupuesto_usd(
        usd, px, frente, mode=modo,
    )
    if not conv.get("ok"):
        raise ValueError(
            f"masa spot no cuantizable: {conv.get('motivo') or 'desconocido'}"
        )
    qty = float(conv["qty"])

    return PlanOrdenNativa(
        symbol=f"{act}USDT",
        category="spot",
        side=side,
        qty=qty,
        market_unit="baseCoin",
        is_leverage=1 if beru_ley.spot_margen_activo() else 0,
        trigger_price=px,
        trigger_direction=trigger_direction,
        link_id=link_id_determinista(beru),
        frente=frente,
    )


def _guardar_orden(beru: Any, plan: PlanOrdenNativa, resultado: Any) -> None:
    beru.altar_order_id = str(getattr(resultado, "order_id", "") or "")
    beru.altar_link_id = plan.link_id
    beru.altar_order_status = "Untriggered"
    beru.altar_trigger_price = float(plan.trigger_price)
    beru.altar_cancel_confirmado = False


async def armar_condicional(bridge: Any, beru: Any, plan: PlanOrdenNativa):
    """Query-before-create: un timeout nunca duplica la carta."""
    previa = await bridge.get_order_status(
        plan.symbol, link_id=plan.link_id, category=plan.category,
        order_filter="StopOrder",
    )
    if previa.exito:
        _guardar_orden(beru, plan, previa)
        beru.altar_order_status = str(
            (previa.datos or {}).get("orderStatus") or previa.mensaje or "Untriggered"
        )
        return previa
    if not bool((previa.datos or {}).get("not_found")):
        # Consulta incierta: no crear. El siguiente pulso consultará otra vez.
        return previa

    # Spot: no pasar triggerDirection/triggerBy (Bybit los rechaza).
    creada = await bridge.place_order(
        plan.symbol,
        plan.side,
        plan.qty,
        order_type="Market",
        link_id=plan.link_id,
        category=plan.category,
        market_unit=plan.market_unit,
        is_leverage=plan.is_leverage,
        trigger_price=plan.trigger_price,
        order_filter="StopOrder",
    )
    if creada.exito:
        _guardar_orden(beru, plan, creada)
    return creada


async def cancelar_confirmado(
    bridge: Any,
    beru: Any,
    *,
    symbol: str,
    category: str = "spot",
    intentos: int = 4,
):
    """Cancela y confirma. Filled no se trata como cancelado."""
    link_id = str(getattr(beru, "altar_link_id", "") or "")
    if not link_id:
        return False, "sin_carta"

    estado = await bridge.get_order_status(
        symbol, link_id=link_id, category=category,
        order_filter="StopOrder",
    )
    status = str((estado.datos or {}).get("orderStatus") or estado.mensaje or "")
    if estado.exito and status == "Filled":
        beru.altar_order_status = status
        return False, "fill_confirmado"
    if estado.exito and status in ("Cancelled", "Rejected", "Deactivated"):
        beru.altar_order_status = status
        beru.altar_cancel_confirmado = True
        return True, status
    if not estado.exito and not bool((estado.datos or {}).get("not_found")):
        return False, "consulta_incierta"

    cancelada = await bridge.cancel_order(
        symbol, link_id=link_id, category=category,
        order_filter="StopOrder",
    )
    if not cancelada.exito:
        return False, str(cancelada.mensaje or "cancel_rechazada")

    for _ in range(max(1, int(intentos))):
        await asyncio.sleep(0.3)
        estado = await bridge.get_order_status(
            symbol, link_id=link_id, category=category,
            order_filter="StopOrder",
        )
        status = str((estado.datos or {}).get("orderStatus") or estado.mensaje or "")
        if estado.exito and status == "Filled":
            beru.altar_order_status = status
            return False, "fill_confirmado"
        if estado.exito and status in ("Cancelled", "Rejected", "Deactivated"):
            beru.altar_order_status = status
            beru.altar_cancel_confirmado = True
            return True, status
    return False, "cancel_sin_confirmar"


async def mover_condicional(
    bridge: Any,
    beru: Any,
    *,
    activo: str,
    masa_usd: float,
    trigger_price: float,
):
    """Quita la carta vieja y solo entonces planta la nueva revisión."""
    symbol = f"{str(activo or '').upper()}USDT"
    ok, motivo = await cancelar_confirmado(
        bridge, beru, symbol=symbol, category="spot",
    )
    if not ok:
        return None, motivo
    beru.altar_revision = int(getattr(beru, "altar_revision", 0) or 0) + 1
    plan = plan_condicional_spot(
        beru,
        activo=activo,
        masa_usd=masa_usd,
        trigger_price=trigger_price,
    )
    return await armar_condicional(bridge, beru, plan), "replantada"


async def consultar_fill(
    bridge: Any,
    beru: Any,
    *,
    activo: str,
    category: str = "spot",
) -> dict[str, Any] | None:
    """Si la Hoz ya filló en exchange, devuelve avgPrice / cumExecQty."""
    link_id = str(getattr(beru, "altar_link_id", "") or "")
    if not link_id:
        return None
    symbol = f"{str(activo or '').upper()}USDT"
    estado = await bridge.get_order_status(
        symbol, link_id=link_id, category=category,
        order_filter="StopOrder",
    )
    datos = dict(estado.datos or {})
    status = str(datos.get("orderStatus") or estado.mensaje or "")
    if estado.exito:
        beru.altar_order_status = status
    cum_qty = float(datos.get("cumExecQty") or 0)
    avg = float(datos.get("avgPrice") or 0)
    if estado.exito and status == "Filled":
        return {
            "avgPrice": avg,
            "cumExecQty": cum_qty,
            "orderStatus": status,
            "order_id": str(getattr(estado, "order_id", "") or datos.get("orderId") or ""),
        }
    if estado.exito and cum_qty > 0 and status in (
        "Filled", "PartiallyFilledCanceled",
    ):
        return {
            "avgPrice": avg,
            "cumExecQty": cum_qty,
            "orderStatus": status,
            "order_id": str(getattr(estado, "order_id", "") or datos.get("orderId") or ""),
        }
    return None
