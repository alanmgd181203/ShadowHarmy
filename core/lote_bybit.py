"""Lotes Bybit — minOrderQty + qtyStep desde BD Jess (sin API en la forja).

Fuente: data/bybit_parametros_mercado.json (ritual México).
Cuantiza cantidades a múltiplos válidos del exchange.
"""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from typing import Any, Literal

import core.config as config
from core import ancla
from core import mercado

ModoRedondeo = Literal["floor", "ceil"]


def _ruta_bd() -> str:
    override = getattr(config, "BYBIT_PARAMETROS_PATH", None)
    if override:
        return str(override)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "bybit_parametros_mercado.json")


@lru_cache(maxsize=1)
def _cargar_bd() -> dict[str, Any]:
    ruta = _ruta_bd()
    if not os.path.exists(ruta):
        return {"activos": {}, "meta": {}}
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"activos": {}, "meta": {}}


def invalidar_cache_bd() -> None:
    _cargar_bd.cache_clear()


def base_desde_frente(frente: str) -> str:
    """ETHUSDT_LINEAL → ETH · BTCUSD_INVERSE → BTC."""
    f = (frente or "").upper()
    if "_" in f:
        sym = f.rsplit("_", 1)[0]
    else:
        sym = f
    for suf in ("USDT", "USDC", "USD"):
        if sym.endswith(suf) and len(sym) > len(suf):
            return sym[: -len(suf)]
    return sym


def clave_mercado_desde_frente(frente: str) -> str:
    """linear | inverse | spot_usdt | spot_usdc."""
    f = (frente or "").upper()
    cat = mercado.frente_a_category(f)
    if cat == "inverse" or f.endswith("_INVERSE"):
        return "inverse"
    if f.endswith("_SPOT"):
        if "USDC" in f:
            return "spot_usdc"
        return "spot_usdt"
    if "USDC" in f and cat == "linear":
        return "linear"  # USDC linear vive bajo linear en BD si existe
    return "linear"


def filtros_lote(frente: str) -> dict[str, Any]:
    """
    Filtros de lote para un frente.
    Fallback: min USD Ancla + step desconocido (1.0 o sin step).
    """
    bd = _cargar_bd()
    base = base_desde_frente(frente)
    clave = clave_mercado_desde_frente(frente)
    activo = (bd.get("activos") or {}).get(base) or {}
    row = activo.get(clave) if isinstance(activo.get(clave), dict) else None

    min_usd_ancla = ancla.min_order_usd_frente(frente)
    if not row:
        return {
            "base": base,
            "clave": clave,
            "frente": frente,
            "minOrderQty": 0.0,
            "qtyStep": 0.0,
            "minNotionalValue": min_usd_ancla,
            "min_usd_est": min_usd_ancla,
            "unidad_min_qty": "base_coin" if clave != "inverse" else "usd_contrato",
            "tickSize": None,
            "precio_ref": None,
            "fuente": "fallback_ancla",
            "ok": False,
        }

    min_qty = float(row.get("minOrderQty") or 0)
    step = float(row.get("qtyStep") or 0)
    min_not = float(row.get("minNotionalValue") or 0)
    min_usd = float(row.get("min_usd_est") or min_not or min_usd_ancla or 0)
    return {
        "base": base,
        "clave": clave,
        "frente": (frente or "").upper(),
        "symbol": row.get("symbol"),
        "minOrderQty": min_qty,
        "qtyStep": step,
        "minNotionalValue": min_not,
        "min_usd_est": max(min_usd, min_usd_ancla) if min_usd_ancla else min_usd,
        "unidad_min_qty": row.get("unidad_min_qty") or (
            "usd_contrato" if clave == "inverse" else "base_coin"
        ),
        "tickSize": row.get("tickSize"),
        "precio_ref": row.get("precio_ref"),
        "fuente": "bybit_parametros_mercado",
        "ok": True,
    }


def cuantizar_qty(
    qty: float,
    *,
    min_qty: float,
    qty_step: float,
    mode: ModoRedondeo = "floor",
) -> float:
    """Redondea a múltiplo de qtyStep, ≥ minOrderQty. 0 si no alcanza el mínimo."""
    q = float(qty)
    if q <= 0:
        return 0.0
    step = float(qty_step or 0)
    minimo = float(min_qty or 0)
    if step <= 0:
        if minimo > 0 and q + 1e-15 < minimo:
            return 0.0
        return q
    if mode == "ceil":
        n = math.ceil(q / step - 1e-12)
    else:
        n = math.floor(q / step + 1e-12)
    out = n * step
    if minimo > 0 and out + 1e-15 < minimo:
        if q + 1e-12 >= minimo:
            n_min = math.ceil(minimo / step - 1e-12)
            out = n_min * step
        else:
            return 0.0
    # Evitar polvo float (0.001 * 3 = 0.0030000000004)
    dec = max(0, min(10, -int(math.floor(math.log10(step))) if step < 1 else 0))
    return round(out, dec + 2)


def usd_a_qty(usd: float, precio: float, filtros: dict[str, Any]) -> float:
    """Convierte presupuesto USD → qty de exchange según unidad del contrato."""
    u = float(usd)
    px = float(precio)
    if u <= 0:
        return 0.0
    unidad = str(filtros.get("unidad_min_qty") or "base_coin")
    if unidad == "usd_contrato" or filtros.get("clave") == "inverse":
        return u  # inverse: qty ≈ USD contrato
    if px <= 0:
        return 0.0
    return u / px


def qty_a_usd(qty: float, precio: float, filtros: dict[str, Any]) -> float:
    q = float(qty)
    px = float(precio)
    if q <= 0:
        return 0.0
    unidad = str(filtros.get("unidad_min_qty") or "base_coin")
    if unidad == "usd_contrato" or filtros.get("clave") == "inverse":
        return q
    return q * max(px, 0.0)


def cuantizar_presupuesto_usd(
    usd: float,
    precio: float,
    frente: str,
    *,
    mode: ModoRedondeo = "floor",
) -> dict[str, Any]:
    """USD deseado → qty válida + USD efectivo tras qtyStep."""
    filt = filtros_lote(frente)
    qty_raw = usd_a_qty(usd, precio, filt)
    qty = cuantizar_qty(
        qty_raw,
        min_qty=float(filt.get("minOrderQty") or 0),
        qty_step=float(filt.get("qtyStep") or 0),
        mode=mode,
    )
    usd_eff = qty_a_usd(qty, precio, filt)
    # Bybit linear suele exigir ~5 USDT aunque la BD no traiga minNotionalValue
    min_not = max(
        float(filt.get("minNotionalValue") or 0),
        float(filt.get("min_usd_est") or 0),
        float(getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0) or 5.0),
    )
    if min_not > 0 and usd_eff + 1e-9 < min_not and qty > 0:
        # Subir un step hasta cubrir notional si el presupuesto original alcanzaba
        step = float(filt.get("qtyStep") or 0)
        min_q = float(filt.get("minOrderQty") or 0)
        if step > 0 and float(usd) + 1e-9 >= min_not:
            while usd_eff + 1e-9 < min_not:
                qty = cuantizar_qty(qty + step, min_qty=min_q, qty_step=step, mode="floor")
                usd_eff = qty_a_usd(qty, precio, filt)
                if qty <= 0:
                    break
        if usd_eff + 1e-9 < min_not:
            qty, usd_eff = 0.0, 0.0
    return {
        "ok": qty > 0,
        "qty": qty,
        "usd": round(usd_eff, 6),
        "filtros": filt,
    }


def paso_minimo_usd(frente: str, precio: float) -> float:
    """USD de un escalón mínimo válido (1× minOrderQty cuantizado)."""
    filt = filtros_lote(frente)
    min_q = float(filt.get("minOrderQty") or 0)
    step = float(filt.get("qtyStep") or 0)
    floor_usd = float(
        filt.get("min_usd_est")
        or ancla.min_order_usd_frente(frente)
        or getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0)
        or 5.0
    )
    q = cuantizar_qty(min_q if min_q > 0 else step, min_qty=min_q, qty_step=step, mode="ceil")
    if q <= 0:
        return floor_usd
    return max(
        qty_a_usd(q, precio, filt),
        float(filt.get("minNotionalValue") or 0),
        floor_usd,
    )


def asegurar_qty_min_notional(
    qty: float,
    precio: float,
    frente: str,
    *,
    mode: ModoRedondeo = "ceil",
) -> dict[str, Any]:
    """
    Qty deseada → qty válida que cumple minOrderQty/qtyStep y minNotional (~5 USDT).
    Si no se puede formar un escalón válido: ok=False, qty=0.
    """
    filt = filtros_lote(frente)
    px = float(precio or 0)
    if px <= 0:
        return {"ok": False, "qty": 0.0, "usd": 0.0, "filtros": filt, "motivo": "sin_precio"}
    min_u = paso_minimo_usd(frente, px)
    usd_want = qty_a_usd(float(qty), px, filt)
    usd_use = max(usd_want, min_u)
    conv = cuantizar_presupuesto_usd(usd_use, px, frente, mode=mode)
    if not conv.get("ok"):
        # Segundo intento: pedir exactamente el mínimo Bybit/Ancla
        conv = cuantizar_presupuesto_usd(min_u, px, frente, mode="ceil")
    if not conv.get("ok"):
        return {
            "ok": False,
            "qty": 0.0,
            "usd": 0.0,
            "filtros": filt,
            "motivo": "bajo_min_notional",
            "min_usd": min_u,
        }
    return {
        "ok": True,
        "qty": float(conv["qty"]),
        "usd": float(conv["usd"]),
        "filtros": filt,
        "min_usd": min_u,
        "motivo": "OK",
    }


def _frente_lineal_del_par(frente_a: str, frente_b: str) -> str | None:
    """El Lineal dicta la Masa Absoluta; si ambos o ninguno son linear → None."""
    a_lin = clave_mercado_desde_frente(frente_a) == "linear"
    b_lin = clave_mercado_desde_frente(frente_b) == "linear"
    if a_lin and not b_lin:
        return (frente_a or "").upper()
    if b_lin and not a_lin:
        return (frente_b or "").upper()
    return None


def _elegir_espejo_inv_long_primero(
    candidatos: list[dict[str, Any]],
    usd_espejo: float,
) -> dict[str, Any]:
    """
    Elige ceil/floor del Inverso al espejar el USD del Lineal.

    Claramente más cercano → ese. Ante duda (equidistantes o |Δcercanía|
    ≤ max(1e-6 USD, medio step entre candidatos)) → más USD (long / Inverso).
    """
    if len(candidatos) == 1:
        return candidatos[0]

    usds = [float(c["usd"]) for c in candidatos]
    step_usd = max(usds) - min(usds)
    eps = max(1e-6, 0.5 * step_usd)

    def _dist(c: dict[str, Any]) -> float:
        return abs(float(c["usd"]) - usd_espejo)

    por_cercania = sorted(candidatos, key=_dist)
    mejor = por_cercania[0]
    # Candidatos en zona de duda respecto al más cercano
    en_duda = [c for c in candidatos if abs(_dist(c) - _dist(mejor)) <= eps + 1e-15]
    if len(en_duda) > 1:
        return max(en_duda, key=lambda c: float(c["usd"]))
    return mejor


def asim_masa_lim_activo(*, marcha_asalto: bool | None = None) -> float:
    """
    Techo |USD_L−USD_S|/ref.
    Asalto: holgado (peaje de espejo). Personalizado / default: 5%.
    """
    if marcha_asalto is None:
        try:
            from core import pase_director as pd

            pm = pd.perfil_marcha()
            marcha_asalto = bool(pm.get("force_market")) or str(pm.get("id")) == "asalto"
        except Exception:
            marcha_asalto = False
    if marcha_asalto:
        return float(getattr(config, "IGRIS_MASA_ASIMETRIA_ASALTO_PCT", 0.12) or 0.12)
    return float(getattr(config, "IGRIS_MASA_ASIMETRIA_MAX_PCT", 0.05) or 0.05)


def ley_de_la_masa_dual(
    frente_a: str,
    frente_b: str,
    precio_a: float,
    precio_b: float,
    usd_deseado: float,
    *,
    asim_max_pct: float | None = None,
) -> dict[str, Any]:
    """
    Ley de la Masa (Monarca): el Inverso no pelea su mínimo aislado.

    1) Alfa = mínimo real del Lineal (max fracción-en-USD, piso ~$5).
    2) Masa Absoluta = max(usd_deseado, Alfa) → cuantiza el Lineal (ceil).
    3) Inverso espeja el USD efectivo del Lineal: candidatos ceil/floor;
       el más cercano al espejo gana; ante duda (equidistantes / cercanía
       despreciable) → más USD en el Inverso (long). Lineal manda siempre.
    4) Candado: si |USD_a − USD_b| / ref > asim_max → disparo prohibido.
    """
    fa = (frente_a or "").upper()
    fb = (frente_b or "").upper()
    px_a = float(precio_a or 0)
    px_b = float(precio_b or 0)
    usd_want = max(0.0, float(usd_deseado or 0))
    lim = float(
        asim_max_pct
        if asim_max_pct is not None
        else asim_masa_lim_activo()
    )
    lim = max(0.0, lim)

    if px_a <= 0 or px_b <= 0:
        return {
            "ok": False,
            "motivo": "sin_precio_ley_masa",
            "usd_deseado": usd_want,
        }

    frente_lin = _frente_lineal_del_par(fa, fb)
    if not frente_lin:
        return {
            "ok": False,
            "motivo": "sin_frente_lineal",
            "frente_a": fa,
            "frente_b": fb,
            "usd_deseado": usd_want,
        }

    frente_inv = fb if frente_lin == fa else fa
    px_lin = px_a if frente_lin == fa else px_b
    px_inv = px_b if frente_lin == fa else px_a

    alfa = float(paso_minimo_usd(frente_lin, px_lin))
    piso = float(getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0) or 5.0)
    masa_absoluta = max(usd_want, alfa, piso)

    conv_lin = cuantizar_presupuesto_usd(masa_absoluta, px_lin, frente_lin, mode="ceil")
    if not conv_lin.get("ok"):
        return {
            "ok": False,
            "motivo": "no_cuantiza_lineal",
            "frente_lineal": frente_lin,
            "alfa_usd": round(alfa, 6),
            "masa_absoluta_usd": round(masa_absoluta, 6),
            "conv_lin": conv_lin,
        }

    usd_espejo = float(conv_lin["usd"])
    conv_ceil = cuantizar_presupuesto_usd(usd_espejo, px_inv, frente_inv, mode="ceil")
    conv_floor = cuantizar_presupuesto_usd(usd_espejo, px_inv, frente_inv, mode="floor")

    candidatos = []
    for c in (conv_ceil, conv_floor):
        if c.get("ok") and float(c.get("qty") or 0) > 0:
            candidatos.append(c)
    if not candidatos:
        return {
            "ok": False,
            "motivo": "no_cuantiza_inverso",
            "frente_lineal": frente_lin,
            "alfa_usd": round(alfa, 6),
            "masa_absoluta_usd": round(masa_absoluta, 6),
            "usd_espejo": round(usd_espejo, 6),
            "conv_inv_ceil": conv_ceil,
            "conv_inv_floor": conv_floor,
        }

    # Espejo: más cercano al USD del Lineal; ante duda → más USD inverso (long)
    conv_inv = _elegir_espejo_inv_long_primero(candidatos, usd_espejo)

    usd_lin = float(conv_lin["usd"])
    usd_inv = float(conv_inv["usd"])
    ref = max((usd_lin + usd_inv) / 2.0, usd_espejo, 1e-9)
    asim = abs(usd_lin - usd_inv) / ref

    if frente_lin == fa:
        qty_a, qty_b = float(conv_lin["qty"]), float(conv_inv["qty"])
        usd_a, usd_b = usd_lin, usd_inv
        filt_a, filt_b = conv_lin.get("filtros"), conv_inv.get("filtros")
    else:
        qty_a, qty_b = float(conv_inv["qty"]), float(conv_lin["qty"])
        usd_a, usd_b = usd_inv, usd_lin
        filt_a, filt_b = conv_inv.get("filtros"), conv_lin.get("filtros")

    return {
        "ok": asim <= lim + 1e-12,
        "motivo": "OK" if asim <= lim + 1e-12 else "asimetr_masa_usd",
        "frente_lineal": frente_lin,
        "frente_inverso": frente_inv,
        "alfa_usd": round(alfa, 6),
        "masa_absoluta_usd": round(masa_absoluta, 6),
        "usd_espejo": round(usd_espejo, 6),
        "usd_deseado": round(usd_want, 6),
        "qty_a": qty_a,
        "qty_b": qty_b,
        "usd_a": round(usd_a, 6),
        "usd_b": round(usd_b, 6),
        "asim_pct": round(asim * 100.0, 4),
        "asim_max_pct": round(lim * 100.0, 4),
        "filtros_a": filt_a,
        "filtros_b": filt_b,
    }


def qty_espejo_usd(
    usd: float,
    precio: float,
    frente: str,
    *,
    mode: ModoRedondeo = "ceil",
) -> dict[str, Any]:
    """Convierte un USD espejo a qty nativa válida del frente (sin re-elevar a otro Alfa)."""
    return cuantizar_presupuesto_usd(float(usd), float(precio), frente, mode=mode)
