"""Altar lineal Beru rango — Oz = trailing de entrada 0,2 %.

Manos OFF por defecto. En Bybit:
  · Al armar: StopOrder en la Oz actual (SHORT: detona al bajar; LONG: al subir)
  · Mientras CAZA: enmienda el trigger si el rastro sube/baja el extremo
  · Al detonar: Market si hace falta; el cerebro ya marcó el fill
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from core import beru_rango
from core import lote_bybit


TERMINALES = frozenset({
    "Filled", "Cancelled", "Rejected", "Deactivated",
    "PartiallyFilledCanceled",
})


@dataclass(frozen=True)
class PlanLinealRango:
    symbol: str
    category: str
    side: str
    qty: float
    trigger_price: float
    trigger_direction: int
    link_id: str
    position_idx: int
    frente: str
    masa_usd: float
    trailing_dist: float


def link_id_rango(beru: Any, *, proposito: str = "TRAIL") -> str:
    rev = int(getattr(beru, "altar_revision", 0) or 0)
    semilla = f"RANGO|{getattr(beru, 'uid', '')}|{rev}|{proposito.upper()}"
    digest = hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:14]
    return f"BRG-{proposito.upper()[:3]}-{rev}-{digest}"[:36]


def plan_trailing_entrada(
    beru: Any,
    *,
    activo: str,
    masa_usd: float | None = None,
    trigger_price: float | None = None,
) -> PlanLinealRango:
    """Oz trailing: SHORT Sell cuando el precio baja a la Oz; LONG Buy al subir."""
    act = str(activo or "").upper()
    if not act:
        raise ValueError("beru_rango_altar: activo vacío")
    symbol = f"{act}USDT"
    frente = f"{act}USDT_LINEAL"
    d = str(getattr(beru, "direccion", "") or "").upper()
    if d not in ("LONG", "SHORT"):
        raise ValueError("beru_rango_altar: dirección inválida")
    oz = float(trigger_price if trigger_price is not None else getattr(beru, "oz_adan", 0) or 0)
    if oz <= 0:
        raise ValueError("beru_rango_altar: Oz trailing sin precio")
    masa = float(masa_usd if masa_usd is not None else beru_rango.masa_tramo_usd())
    if masa <= 0:
        raise ValueError("beru_rango_altar: masa ≤ 0")
    qty_bruta = masa / oz
    pack = lote_bybit.asegurar_qty_min_notional(
        qty_bruta, oz, frente, mode="ceil",
    )
    if not pack.get("ok"):
        raise ValueError(str(pack.get("motivo") or "lote_lineal_invalido"))
    qty = float(pack.get("qty") or 0)
    if qty <= 0:
        raise ValueError("beru_rango_altar: qty ≤ 0")
    dist = round(oz * beru_rango.trailing_dist_pct(), 8)
    if d == "SHORT":
        side = "Sell"
        trigger_direction = 2  # precio baja → toca Oz del rastro
        position_idx = 2
    else:
        side = "Buy"
        trigger_direction = 1  # precio sube → toca Oz del rastro
        position_idx = 1
    return PlanLinealRango(
        symbol=symbol,
        category="linear",
        side=side,
        qty=qty,
        trigger_price=oz,
        trigger_direction=trigger_direction,
        link_id=link_id_rango(beru),
        position_idx=position_idx,
        frente=frente,
        masa_usd=round(qty * oz, 6),
        trailing_dist=dist,
    )


# Compat smokes / imports viejos
def plan_condicional_lineal(*a, **k) -> PlanLinealRango:
    return plan_trailing_entrada(*a, **k)


async def armar_condicional(bridge: Any, beru: Any, plan: PlanLinealRango):
    """Coloca Stop en la Oz del trailing (se enmendará al moverse el extremo)."""
    previa = await bridge.get_order_status(
        plan.symbol, link_id=plan.link_id, category=plan.category,
        order_filter="StopOrder",
    )
    if getattr(previa, "exito", False):
        status = str(
            (previa.datos or {}).get("orderStatus") or previa.mensaje or ""
        )
        if status == "Filled":
            beru.altar_order_id = str(getattr(previa, "order_id", "") or "")
            beru.altar_link_id = plan.link_id
            beru.altar_order_status = "Filled"
            beru.altar_trigger_price = float(plan.trigger_price)
            return previa
        if status not in TERMINALES:
            beru.altar_order_id = str(getattr(previa, "order_id", "") or "")
            beru.altar_link_id = plan.link_id
            beru.altar_order_status = status
            beru.altar_trigger_price = float(plan.trigger_price)
            return previa
    elif not bool((getattr(previa, "datos", None) or {}).get("not_found")):
        return previa

    creada = await bridge.place_order(
        plan.symbol,
        plan.side,
        plan.qty,
        order_type="Market",
        link_id=plan.link_id,
        category=plan.category,
        trigger_price=plan.trigger_price,
        trigger_direction=plan.trigger_direction,
        trigger_by="LastPrice",
        order_filter="StopOrder",
        position_idx=plan.position_idx,
        reduce_only=False,
    )
    if getattr(creada, "exito", False):
        beru.altar_order_id = str(getattr(creada, "order_id", "") or "")
        beru.altar_link_id = plan.link_id
        beru.altar_order_status = "Untriggered"
        beru.altar_trigger_price = float(plan.trigger_price)
        beru.altar_cancel_confirmado = False
        beru.altar_trailing_dist = float(plan.trailing_dist)
    return creada


async def seguir_trailing(bridge: Any, beru: Any, *, activo: str) -> Any:
    """Enmienda el trigger a la Oz viva del rastro."""
    oz = float(getattr(beru, "oz_adan", 0) or 0)
    link = str(getattr(beru, "altar_link_id", "") or "")
    if oz <= 0 or not link or bridge is None:
        return None
    prev = float(getattr(beru, "altar_trigger_price", 0) or 0)
    if prev > 0 and abs(oz - prev) / prev < 1e-6:
        return None
    act = str(activo or "").upper()
    symbol = f"{act}USDT"
    amend = await bridge.amend_order(
        symbol,
        link_id=link,
        category="linear",
        new_trigger_price=oz,
    )
    if getattr(amend, "exito", False):
        beru.altar_trigger_price = oz
    return amend


async def disparar_entrada_market(
    bridge: Any, beru: Any, *, activo: str, masa_usd: float | None = None,
) -> Any:
    """Si el cerebro detona y la casa no llenó el Stop: Market de entrada."""
    plan = plan_trailing_entrada(beru, activo=activo, masa_usd=masa_usd)
    return await bridge.place_order(
        plan.symbol,
        plan.side,
        plan.qty,
        order_type="Market",
        link_id=link_id_rango(beru, proposito="MKT"),
        category=plan.category,
        position_idx=plan.position_idx,
        reduce_only=False,
    )


async def armar_trailing(
    bridge: Any,
    beru: Any,
    *,
    activo: str,
    active_price: float | None = None,
):
    """LEGADO: trailing de posición post-fill. El oficio rango ya no lo usa al cosechar;
    la Oz de entrada es el rastro del cerebro + Stop enmendado."""
    _ = active_price
    plan = plan_trailing_entrada(beru, activo=activo)
    return await armar_condicional(bridge, beru, plan)
