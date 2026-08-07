"""Escalera de precios — micro-bocados a distintos niveles del libro.

Doctrina Monarca: comer lo que el hueco permite sin una orden masiva.
Peldaños Limit alrededor del Ask/Bid → cancelar no llenos → equilibrar Market.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Literal

import core.config as config
from core import ancla

Side = Literal["Buy", "Sell"]


def escalera_activa(general: str = "IGRIS") -> bool:
    if not bool(getattr(config, "ESCALERA_PRECIOS_ACTIVA", True)):
        return False
    g = (general or "").upper()
    if g == "GREED":
        return bool(getattr(config, "ESCALERA_GREED_ACTIVA", True))
    return bool(getattr(config, "ESCALERA_IGRIS_ACTIVA", True))


def max_peldaños(marcha_id: str | None = None) -> int:
    tope = int(getattr(config, "ESCALERA_MAX_PELDANOS", 10) or 10)
    tope = max(1, min(12, tope))
    mid = (marcha_id or "").lower()
    # Legado tactico/forzada → asalto (sello 2 marchas)
    if mid in ("tactico", "táctico", "marcha_forzada", "forzada"):
        mid = "asalto"
    if mid == "asalto":
        return 1
    # personalizado u otros: peldaños moderados
    return max(2, min(8, tope))


def tick_precio(precio_ref: float, tick_pct: float | None = None) -> float:
    pct = float(
        tick_pct
        if tick_pct is not None
        else getattr(config, "ESCALERA_TICK_PCT", 0.00015) or 0.00015
    )
    ref = max(float(precio_ref), 1e-12)
    return max(ref * pct, ref * 1e-8)


def armar_peldaños(
    tamaño: float,
    precio_ref: float,
    side: Side,
    *,
    n_max: int | None = None,
    min_tamaño: float = 0.0,
    tick_pct: float | None = None,
    marcha_id: str | None = None,
) -> list[dict[str, float]]:
    """
    Parte `tamaño` (USD o qty) en peldaños ≥ min_tamaño alrededor de precio_ref.
    Buy: precios de más alto a más bajo (atraviesa el ask hacia el mid).
    Sell: precios de más bajo a más alto (atraviesa el bid hacia el mid).
    """
    total = float(tamaño)
    if total <= 0 or float(precio_ref) <= 0:
        return []
    n_cap = int(n_max if n_max is not None else max_peldaños(marcha_id))
    minimo = max(float(min_tamaño), 0.0)
    if minimo > 0 and total + 1e-12 < minimo:
        return []
    if minimo > 0:
        n_por_min = max(1, int(total // minimo))
        n = max(1, min(n_cap, n_por_min))
    else:
        n = max(1, n_cap)
    # Asalto / 1 peldaño
    if n <= 1:
        return [{"tamaño": round(total, 8), "precio": round(float(precio_ref), 8), "i": 0}]

    base = total / n
    # Ajuste para no quedar bajo mínimo en el último
    if minimo > 0 and base + 1e-12 < minimo:
        n = max(1, int(total // minimo))
        base = total / n

    tick = tick_precio(precio_ref, tick_pct)
    mitad = (n - 1) / 2.0
    out: list[dict[str, float]] = []
    resto = total
    for i in range(n):
        if i == n - 1:
            t = resto
        else:
            t = base
            resto -= t
        if minimo > 0 and t + 1e-12 < minimo and i < n - 1:
            continue
        offset = (mitad - i) * tick
        if side == "Buy":
            px = float(precio_ref) + offset  # arriba → abajo
        else:
            px = float(precio_ref) - offset  # abajo → arriba
        if t > 0 and px > 0:
            out.append({"tamaño": round(t, 8), "precio": round(px, 8), "i": float(i)})
    return out


def min_usd_frente(frente: str, precio: float | None = None) -> float:
    """Mínimo USD por peldaño: BD Jess (qtyStep×precio) o Ancla."""
    if precio and float(precio) > 0:
        try:
            from core import lote_bybit as lote

            return float(lote.paso_minimo_usd(frente, float(precio)))
        except Exception:
            pass
    return ancla.min_order_usd_frente(frente)


def armar_peldaños_lote(
    tamaño: float,
    precio_ref: float,
    side: Side,
    *,
    frente: str,
    unidad: Literal["qty", "usd"] = "qty",
    n_max: int | None = None,
    tick_pct: float | None = None,
    marcha_id: str | None = None,
) -> list[dict[str, float]]:
    """
    Peldaños ya cuantizados a minOrderQty + qtyStep (BD Jess).
    unidad=qty → tamaño en monedas/contratos (Igris).
    unidad=usd → presupuesto USD → qty (Greed).
    """
    from core import lote_bybit as lote

    filt = lote.filtros_lote(frente)
    min_q = float(filt.get("minOrderQty") or 0)
    step = float(filt.get("qtyStep") or 0)
    px = float(precio_ref)

    if unidad == "usd":
        conv = lote.cuantizar_presupuesto_usd(float(tamaño), px, frente, mode="floor")
        if not conv.get("ok"):
            # Subir al mínimo notional Bybit/Ancla si el presupuesto era polvo
            min_u = lote.paso_minimo_usd(frente, px)
            conv = lote.cuantizar_presupuesto_usd(min_u, px, frente, mode="ceil")
        if not conv.get("ok"):
            return []
        qty_total = float(conv["qty"])
    else:
        aseg = lote.asegurar_qty_min_notional(float(tamaño), px, frente, mode="ceil")
        if not aseg.get("ok"):
            return []
        qty_total = float(aseg["qty"])

    min_rung = lote.cuantizar_qty(
        min_q if min_q > 0 else (step if step > 0 else qty_total),
        min_qty=min_q,
        qty_step=step,
        mode="ceil",
    )
    if min_rung <= 0:
        min_rung = step if step > 0 else 0.0
    # Peldaño también en USD ≥ mínimo exchange (~5 USDT)
    min_usd = lote.paso_minimo_usd(frente, px)
    min_rung_usd_qty = 0.0
    try:
        conv_r = lote.cuantizar_presupuesto_usd(min_usd, px, frente, mode="ceil")
        if conv_r.get("ok"):
            min_rung_usd_qty = float(conv_r["qty"])
    except Exception:
        min_rung_usd_qty = 0.0
    if min_rung_usd_qty > min_rung:
        min_rung = min_rung_usd_qty

    raw = armar_peldaños(
        qty_total,
        px,
        side,
        n_max=n_max,
        min_tamaño=min_rung,
        tick_pct=tick_pct,
        marcha_id=marcha_id,
    )
    if not raw:
        # Una sola mordida al total ya asegurado
        return [{"tamaño": qty_total, "precio": px, "i": 0.0}] if qty_total > 0 else []

    tick_sz = filt.get("tickSize")
    out: list[dict[str, float]] = []
    used = 0.0
    for i, p in enumerate(raw):
        if i == len(raw) - 1:
            rem = qty_total - used
            q = lote.cuantizar_qty(rem, min_qty=min_q, qty_step=step, mode="floor")
        else:
            q = lote.cuantizar_qty(
                float(p["tamaño"]), min_qty=min_q, qty_step=step, mode="floor",
            )
        if q <= 0:
            continue
        # Descartar peldaños bajo min notional (evita 110094)
        if lote.qty_a_usd(q, float(p["precio"]) or px, filt) + 1e-9 < min_usd:
            continue
        used += q
        precio = float(p["precio"])
        if tick_sz:
            try:
                ts = float(tick_sz)
                if ts > 0:
                    precio = round(round(precio / ts) * ts, 10)
            except (TypeError, ValueError):
                pass
        out.append({"tamaño": q, "precio": precio, "i": float(i)})

    # Si quedó polvo usable, súbelo al último peldaño
    polvo = qty_total - used
    if out and step > 0 and polvo + 1e-12 >= step:
        extra = lote.cuantizar_qty(polvo, min_qty=0.0, qty_step=step, mode="floor")
        if extra > 0:
            out[-1]["tamaño"] = lote.cuantizar_qty(
                float(out[-1]["tamaño"]) + extra,
                min_qty=min_q,
                qty_step=step,
                mode="floor",
            )
    # Si todos los peldaños cayeron por min USD → una sola orden del total
    if not out and qty_total > 0:
        return [{"tamaño": qty_total, "precio": px, "i": 0.0}]
    return out


async def ejecutar_escalera(
    bridge,
    *,
    symbol: str,
    side: Side,
    category: str,
    peldaños: list[dict[str, float]],
    bel=None,
    general: str = "IGRIS",
    fill_timeout_s: float | None = None,
) -> dict[str, Any]:
    """
    Coloca Limits en paralelo, espera, cancela no llenos.
    Retorna filled_tamaño (suma qty/usd colocados), avg_price, handles.
    """
    timeout = float(
        fill_timeout_s
        if fill_timeout_s is not None
        else getattr(config, "ESCALERA_FILL_TIMEOUT_S", 12) or 12
    )
    if not peldaños:
        return {
            "ok": False,
            "filled_tamaño": 0.0,
            "avg_price": 0.0,
            "n_filled": 0,
            "n_cancelled": 0,
            "motivo": "sin_peldaños",
        }
    if len(peldaños) == 1 and float(peldaños[0].get("precio") or 0) <= 0:
        # Fallback market single
        res = await bridge.place_order(
            symbol, side, peldaños[0]["tamaño"], category=category, order_type="Market",
        )
        if not res.exito:
            return {"ok": False, "filled_tamaño": 0.0, "avg_price": 0.0, "n_filled": 0, "n_cancelled": 0, "motivo": res.mensaje}
        fill = await bridge.esperar_fill(symbol, order_id=res.order_id, category=category, timeout_s=timeout)
        if not fill.exito:
            return {"ok": False, "filled_tamaño": 0.0, "avg_price": 0.0, "n_filled": 0, "n_cancelled": 0, "motivo": "market_sin_fill"}
        datos = getattr(fill, "datos", None) or {}
        return {
            "ok": True,
            "filled_tamaño": float(peldaños[0]["tamaño"]),
            "avg_price": float(datos.get("avgPrice") or 0),
            "n_filled": 1,
            "n_cancelled": 0,
            "motivo": "OK_MARKET",
        }

    colocadas: list[dict[str, Any]] = []
    for p in peldaños:
        qty = float(p["tamaño"])
        px = float(p["precio"])
        if qty <= 0 or px <= 0:
            continue
        res = await bridge.place_order(
            symbol, side, qty, category=category, order_type="Limit", price=px,
        )
        if res.exito and res.order_id:
            colocadas.append({"order_id": res.order_id, "tamaño": qty, "precio": px})
        elif bel:
            try:
                await bel.anotar(general, "ESCALERA_SKIP", f"{symbol} @{px}: {getattr(res, 'mensaje', '?')}")
            except Exception:
                pass

    if not colocadas:
        return {
            "ok": False,
            "filled_tamaño": 0.0,
            "avg_price": 0.0,
            "n_filled": 0,
            "n_cancelled": 0,
            "motivo": "ningun_peldaño_aceptado",
        }

    async def _wait_one(c: dict) -> dict:
        fill = await bridge.esperar_fill(
            symbol, order_id=c["order_id"], category=category, timeout_s=timeout,
        )
        if fill.exito:
            datos = getattr(fill, "datos", None) or {}
            return {
                "filled": True,
                "tamaño": float(datos.get("cumExecQty") or c["tamaño"]),
                "precio": float(datos.get("avgPrice") or c["precio"]),
                "order_id": c["order_id"],
            }
        try:
            await bridge.cancel_order(symbol, order_id=c["order_id"], category=category)
        except Exception:
            pass
        return {"filled": False, "tamaño": 0.0, "precio": 0.0, "order_id": c["order_id"]}

    resultados = await asyncio.gather(*[_wait_one(c) for c in colocadas])
    filled_sz = 0.0
    notional = 0.0
    n_ok = 0
    n_cancel = 0
    for r in resultados:
        if r.get("filled"):
            sz = float(r["tamaño"])
            px = float(r["precio"])
            filled_sz += sz
            notional += sz * px
            n_ok += 1
        else:
            n_cancel += 1

    avg = (notional / filled_sz) if filled_sz > 0 else 0.0
    return {
        "ok": filled_sz > 0,
        "filled_tamaño": round(filled_sz, 8),
        "avg_price": round(avg, 8),
        "n_filled": n_ok,
        "n_cancelled": n_cancel,
        "motivo": "OK_ESCALERA" if filled_sz > 0 else "nada_lleno",
        "ts": time.time(),
    }


def n_y_marcha_para_general() -> tuple[int, str | None]:
    try:
        from core import pase_director as pd
        if pd.director_activo():
            mid = pd.cargar_marcha()
            return max_peldaños(mid), mid
    except Exception:
        pass
    return max_peldaños(None), None
