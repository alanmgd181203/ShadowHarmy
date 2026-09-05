"""Altar lineal Beru rango — Oz = trailing de entrada 0,2 %.

Manos OFF por defecto. Mar por defecto OKX (``BERU_MAR``):
  · Al armar: orden trigger en la Oz (SHORT: detona al bajar; LONG: al subir)
  · Mientras CAZA: enmienda el trigger si el rastro sube/baja el extremo
  · Al detonar: Market si hace falta; cosecha solo con fill/posición en casa
"""
from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Any

from core import beru_mar
from core import beru_rango
from core import lote_beru
from core import lote_okx
from core.bridge import OrdenResultado


TERMINALES = frozenset({
    "Filled", "Cancelled", "Rejected", "Deactivated",
    "PartiallyFilledCanceled",
})


def limpiar_sello_altar(beru: Any) -> None:
    """Borra metadatos del Stop/Market en el vivo (acecho sin sello colgado)."""
    if beru is None:
        return
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    beru.altar_cancel_confirmado = False
    beru.altar_entrada_disparada = False
    beru.altar_market_ts = 0.0


def sello_entrada_activo(beru: Any) -> bool:
    """True si ya hay Stop colgado o Market de este tramo (no repetir entrada)."""
    if beru is None:
        return False
    if bool(getattr(beru, "altar_entrada_disparada", False)):
        return True
    if str(getattr(beru, "altar_link_id", "") or "").strip():
        return True
    return False


def sellar_entrada_market(beru: Any, resultado: Any, *, plan: Any = None) -> None:
    """Tras un Market de entrada: sella el tramo para que REPARAR no dispare otro."""
    if beru is None:
        return
    link = str(getattr(resultado, "link_id", "") or "")
    if not link and plan is not None:
        link = str(getattr(plan, "link_id", "") or "")
    if not link:
        rev = int(getattr(beru, "altar_revision", 0) or 0)
        link = f"BRGMKT-{rev}"
    beru.altar_link_id = link
    beru.altar_order_id = str(getattr(resultado, "order_id", "") or "")
    beru.altar_order_status = "MarketSent"
    beru.altar_entrada_disparada = True
    import time as _time

    beru.altar_market_ts = float(_time.time())
    if plan is not None:
        beru.altar_qty = float(getattr(plan, "qty", 0) or 0)
        beru.altar_masa_colocada_usd = float(getattr(plan, "masa_usd", 0) or 0)
        beru.altar_trigger_price = 0.0


def stop_trigger_valido(beru: Any, precio: float) -> bool:
    """False si el last ya pasó la Oz → Bybit rechaza el Stop (110092)."""
    d = str(getattr(beru, "direccion", "") or "").upper()
    oz = float(getattr(beru, "oz_adan", 0) or 0)
    px = float(precio or 0)
    if oz <= 0 or px <= 0 or d not in ("LONG", "SHORT"):
        return True
    eps = max(oz * 1e-6, 1e-9)
    if d == "LONG":
        return px < oz - eps
    return px > oz + eps


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


def _cuantizar_masa_plan(
    beru: Any,
    masa_doctrinal: float,
    oz: float,
    frente: str,
    *,
    ticket_min_si_cero: bool = False,
) -> dict[str, Any]:
    """Doctrina → qty: una Oz = floor(suma absoluta del cerebro).

    ``masa_doctrinal`` ya es el total ($2,45). No se suma ``masa_pendiente``
    otra vez (tumor: doble conteo doctrina+deuda). La deuda tras el piso es
    solo cola en cabeza = doctrina − notional colocado.
    """
    doctrina = max(0.0, float(masa_doctrinal or 0))
    usar_floor = beru_rango.redondeo_floor_manos()
    objetivo = doctrina
    if not usar_floor:
        minimo = 0.0
        if beru_mar.es_okx():
            act = beru_rango.activo_desde_beru(beru) or frente.replace("USDT_LINEAL", "")
            minimo = float((lote_okx.pierna_activo(act)).get("min_usd_est") or 0)
        objetivo = beru_rango.piso_masa_usd(objetivo, minimo_bybit=minimo)
    pack = lote_beru.masa_a_qty_con_deuda(
        objetivo,
        oz,
        frente,
        pendiente=0.0,
        usar_floor=usar_floor,
        ticket_min_si_cero=ticket_min_si_cero,
    )
    if beru is not None and usar_floor:
        beru_rango.registrar_masa_doctrinal(beru, doctrina)
        if pack.get("ok"):
            beru.masa_pendiente_usd = max(0.0, float(pack.get("deuda_usd") or 0))
            beru.altar_masa_colocada_usd = float(pack.get("notional_usd") or 0)
        else:
            # Espera piso: toda la suma queda en cabeza; no hay sello en el mar.
            beru.masa_pendiente_usd = max(
                0.0, float(pack.get("deuda_usd") or doctrina),
            )
            beru.altar_masa_colocada_usd = 0.0
    return pack


def plan_trailing_entrada(
    beru: Any,
    *,
    activo: str,
    masa_usd: float | None = None,
    trigger_price: float | None = None,
    ticket_min_si_cero: bool = False,
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
    try:
        oz = float(lote_beru.cuantizar_precio(oz, frente) or oz)
    except Exception:
        pass
    masa = float(masa_usd if masa_usd is not None else getattr(beru, "masa", 0) or beru_rango.masa_tramo_usd())
    pack = _cuantizar_masa_plan(
        beru, masa, oz, frente, ticket_min_si_cero=ticket_min_si_cero,
    )
    if not pack.get("ok"):
        motivo = str(pack.get("motivo") or "lote_lineal_invalido")
        deuda = float(pack.get("deuda_usd") or 0)
        if beru is not None and beru_rango.redondeo_floor_manos():
            beru.masa_pendiente_usd = max(0.0, deuda, float(masa or 0))
            beru.altar_masa_colocada_usd = 0.0
        raise ValueError(f"beru_rango_altar: {motivo} (doctrina={masa:.4f} deuda={deuda:.4f})")
    qty = float(pack.get("qty") or 0)
    if qty <= 0:
        raise ValueError("beru_rango_altar: qty ≤ 0")
    notional = float(pack.get("notional_usd") or (qty * oz))
    if beru is not None:
        beru.altar_qty = qty
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
        masa_usd=round(notional, 6),
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
        # Fill/terminal de un sello VIEJO no sirve: hay que nacer otro link.
        if status in TERMINALES or status == "Filled":
            beru.altar_revision = int(getattr(beru, "altar_revision", 0) or 0) + 1
            sym = str(plan.symbol or "")
            act = sym[:-4] if sym.upper().endswith("USDT") else sym
            plan = plan_trailing_entrada(
                beru,
                activo=act,
                masa_usd=float(plan.masa_usd or 0) or None,
                trigger_price=float(plan.trigger_price or 0) or None,
            )
        elif status not in TERMINALES:
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
        beru.altar_link_id = str(getattr(creada, "link_id", "") or plan.link_id)
        beru.altar_order_status = "Untriggered"
        beru.altar_trigger_price = float(plan.trigger_price)
        beru.altar_cancel_confirmado = False
        beru.altar_trailing_dist = float(plan.trailing_dist)
        beru.altar_qty = float(plan.qty)
        beru.altar_masa_colocada_usd = float(plan.masa_usd)
    return creada


async def seguir_trailing(bridge: Any, beru: Any, *, activo: str) -> Any:
    """Enmienda trigger Oz y qty al total doctrinal floored (no parches +0.01)."""
    if str(getattr(beru, "altar_order_status", "") or "") == "MarketSent":
        return None  # entrada ya fue Market; no enmendar Stop fantasma
    oz = float(getattr(beru, "oz_adan", 0) or 0)
    link = str(getattr(beru, "altar_link_id", "") or "")
    if oz <= 0 or not link or bridge is None:
        return None
    act = str(activo or "").upper()
    frente = f"{act}USDT_LINEAL"
    try:
        oz = float(lote_beru.cuantizar_precio(oz, frente) or oz)
        beru.oz_adan = oz
    except Exception:
        pass
    prev_trig = float(getattr(beru, "altar_trigger_price", 0) or 0)
    masa_doc = float(getattr(beru, "masa", 0) or 0)
    new_qty: float | None = None
    lot_step = 0.0
    tick_step = 0.0
    if beru_mar.es_okx():
        fl = lote_okx.filtros_lote(frente)
        lot_step = float(fl.get("lotSz") or 0.01)
        tick_step = float(fl.get("tickSz") or 0.01)
    if beru_rango.redondeo_floor_manos() and masa_doc > 0:
        pack = _cuantizar_masa_plan(beru, masa_doc, oz, frente)
        if pack.get("ok"):
            cand = float(pack.get("qty") or 0)
            if beru_mar.es_okx():
                cand = lote_okx.cuantizar_qty(cand, frente, modo="floor")
            prev_qty = float(getattr(beru, "altar_qty", 0) or 0)
            if beru_mar.es_okx():
                prev_qty = lote_okx.cuantizar_qty(prev_qty, frente, modo="floor")
            umbral_qty = lot_step * 0.5 if lot_step > 0 else 1e-12
            # Total floored absoluto: subir O bajar si el piso cambió (no solo engorde).
            if abs(cand - prev_qty) > umbral_qty and cand > 0:
                new_qty = cand
    umbral_trig = tick_step * 0.5 if tick_step > 0 else 1e-12
    trig_changed = prev_trig <= 0 or abs(oz - prev_trig) >= umbral_trig
    if not trig_changed and new_qty is None:
        return None
    symbol = f"{act}USDT"
    amend = await bridge.amend_order(
        symbol,
        link_id=link,
        category="linear",
        new_trigger_price=oz if trig_changed else None,
        new_qty=new_qty,
    )
    if getattr(amend, "exito", False):
        if trig_changed:
            beru.altar_trigger_price = oz
        if new_qty is not None:
            beru.altar_qty = new_qty
            pack = _cuantizar_masa_plan(beru, masa_doc, oz, frente)
            if pack.get("ok"):
                beru.altar_masa_colocada_usd = float(pack.get("notional_usd") or 0)
    else:
        # Fallo: anotar en segundo plano — no bloquear el siguiente latido de Oz.
        msg = str(getattr(amend, "mensaje", "") or "amend_fallido")
        bel = getattr(bridge, "bel", None)
        if bel is not None:
            detalle = f"{act} link={link} oz={oz} prev={prev_trig} qty={new_qty} · {msg}"
            print(f"[RANGO] ALTAR_AMEND_FALLIDO {detalle}", flush=True)
            try:
                asyncio.create_task(
                    bel.anotar("BERU_RANGO", "ALTAR_AMEND_FALLIDO", detalle)
                )
            except Exception:
                pass
    return amend


async def cancelar_pendiente(
    bridge: Any,
    beru: Any,
    *,
    activo: str,
    motivo: str = "LIMPIEZA",
) -> Any:
    """Cancela el Stop del altar si sigue vivo (salida limpia / wake fresco)."""
    link = str(getattr(beru, "altar_link_id", "") or "")
    oid = str(getattr(beru, "altar_order_id", "") or "")
    if bridge is None or (not link and not oid):
        return None
    act = str(activo or "").upper()
    symbol = f"{act}USDT"
    res = await bridge.cancel_order(
        symbol,
        order_id=oid or None,
        link_id=link or None,
        category="linear",
        order_filter="StopOrder",
    )
    bel = getattr(bridge, "bel", None)
    ok = bool(getattr(res, "exito", False))
    msg = str(getattr(res, "mensaje", "") or "")
    fantasma = (
        "110001" in msg
        or "not exist" in msg.lower()
        or "too late to cancel" in msg.lower()
    )
    if fantasma:
        ok = True
    if bel is not None:
        try:
            await bel.anotar(
                "BERU_RANGO",
                "ALTAR_CANCEL" if ok else "ALTAR_CANCEL_FALLIDO",
                f"{act} {motivo} link={link or oid} · "
                f"{msg or ('ok' if ok else 'fail')}",
            )
        except Exception:
            pass
    if ok:
        beru.altar_order_status = "Cancelled" if not fantasma else "Gone"
        beru.altar_cancel_confirmado = True
        limpiar_sello_altar(beru)
    return res


async def reenganchar_o_rearmar(
    bridge: Any,
    beru: Any,
    *,
    activo: str,
) -> Any:
    """Tras CONTINUAR en CAZANDO: si el Stop sigue, reusa; si no, arma de nuevo."""
    link = str(getattr(beru, "altar_link_id", "") or "")
    act = str(activo or "").upper()
    if bridge is None or not act:
        return None
    if link:
        estado = await bridge.get_order_status(
            f"{act}USDT",
            link_id=link,
            category="linear",
            order_filter="StopOrder",
        )
        if getattr(estado, "exito", False):
            st = str((estado.datos or {}).get("orderStatus") or estado.mensaje or "")
            if st and st not in TERMINALES and st != "Filled":
                beru.altar_order_status = st
                trig = float(
                    (estado.datos or {}).get("triggerPrice")
                    or getattr(beru, "altar_trigger_price", 0)
                    or 0
                )
                if trig > 0:
                    beru.altar_trigger_price = trig
                return estado
        beru.altar_revision = int(getattr(beru, "altar_revision", 0) or 0) + 1
        beru.altar_link_id = ""
        beru.altar_order_id = ""
    try:
        plan = plan_trailing_entrada(
            beru,
            activo=act,
            masa_usd=float(getattr(beru, "masa", 0) or 0) or None,
        )
    except ValueError as exc:
        return OrdenResultado(False, mensaje=str(exc))
    return await armar_condicional(bridge, beru, plan)


def _market_cooldown_s() -> float:
    import os

    try:
        return max(0.0, float(os.environ.get("BERU_RANGO_MARKET_COOLDOWN_S", "3") or 3))
    except (TypeError, ValueError):
        return 3.0


async def disparar_entrada_market(
    bridge: Any, beru: Any, *, activo: str, masa_usd: float | None = None,
) -> Any:
    """Si el cerebro detona y la casa no llenó el Stop: Market de entrada.

    Usa ticket_min si el floor doctrinal aún no cubre 1 contrato (Oz ya tocó).
    Candado: un Market por tramo (``altar_entrada_disparada``) + cooldown corto.
    """
    if bool(getattr(beru, "altar_entrada_disparada", False)):
        return OrdenResultado(False, mensaje="entrada_ya_disparada")
    import time as _time

    last = float(getattr(beru, "altar_market_ts", 0) or 0)
    cool = _market_cooldown_s()
    now = _time.time()
    if cool > 0 and last > 0 and (now - last) < cool:
        return OrdenResultado(False, mensaje="market_cooldown")
    beru.altar_revision = int(getattr(beru, "altar_revision", 0) or 0) + 1
    try:
        plan = plan_trailing_entrada(
            beru, activo=activo, masa_usd=masa_usd, ticket_min_si_cero=True,
        )
    except ValueError as exc:
        return OrdenResultado(False, mensaje=str(exc))
    res = await bridge.place_order(
        plan.symbol,
        plan.side,
        plan.qty,
        order_type="Market",
        link_id=link_id_rango(beru, proposito="MKT"),
        category=plan.category,
        position_idx=plan.position_idx,
        reduce_only=False,
    )
    if getattr(res, "exito", False):
        sellar_entrada_market(beru, res, plan=plan)
    return res


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
