"""Igris §E — piernas manto, promedio de entrada, bootstrap inverse L + lineal S."""
from __future__ import annotations

from typing import Any

import core.config as config


def frentes_bootstrap(base: str | None = None) -> tuple[str, str]:
    """(frente_long_inverse, frente_short_lineal) — doctrina 21 §E."""
    b = (base or config.TICKER_BASE).upper()
    return f"{b}USD_INVERSE", f"{b}USDT_LINEAL"


def asegurar_peso(pesos: dict, frente: str) -> dict:
    if frente not in pesos:
        pesos[frente] = {
            "long": 0.0,
            "short": 0.0,
            "precio_medio_long": 0.0,
            "precio_medio_short": 0.0,
            "baseline_long": 0.0,
            "baseline_short": 0.0,
            "fees_paid_long": 0.0,
            "fees_paid_short": 0.0,
        }
    else:
        pesos[frente].setdefault("precio_medio_long", 0.0)
        pesos[frente].setdefault("precio_medio_short", 0.0)
        pesos[frente].setdefault("baseline_long", 0.0)
        pesos[frente].setdefault("baseline_short", 0.0)
        pesos[frente].setdefault("fees_paid_long", 0.0)
        pesos[frente].setdefault("fees_paid_short", 0.0)
    return pesos[frente]


def actualizar_promedio(
    pesos: dict,
    frente: str,
    direccion: str,
    masa: float,
    precio: float,
    fee_usd: float = 0.0,
) -> None:
    """Promedio ponderado de entrada por pierna (§E contabilidad).

    En la primera apertura de la pierna fija `baseline_*` (precio original
    para auditoría de mejora Igris). Acumula fees del fill si vienen del Bridge.
    """
    if masa <= 0 or precio <= 0:
        return
    pf = asegurar_peso(pesos, frente)
    key_masa = "long" if direccion == "LONG" else "short"
    key_px = "precio_medio_long" if direccion == "LONG" else "precio_medio_short"
    key_base = "baseline_long" if direccion == "LONG" else "baseline_short"
    key_fee = "fees_paid_long" if direccion == "LONG" else "fees_paid_short"
    prev_m = float(pf[key_masa])
    prev_px = float(pf[key_px])
    if prev_m <= 0 or prev_px <= 0:
        pf[key_px] = precio
    else:
        pf[key_px] = (prev_m * prev_px + masa * precio) / (prev_m + masa)
    # Baseline = primera sangre de la pierna; no se reescribe al optimizar
    if float(pf.get(key_base) or 0) <= 0:
        pf[key_base] = precio
    if fee_usd and fee_usd > 0:
        pf[key_fee] = float(pf.get(key_fee) or 0) + float(fee_usd)


def baselines_activo(pesos: dict, symbol: str) -> dict[str, float]:
    """Baseline L/S agregados para un activo (primer fill por pierna)."""
    s = str(symbol or "").upper()
    bl = bs = 0.0
    for frente, p in (pesos or {}).items():
        if not str(frente).upper().startswith(s):
            continue
        if float(p.get("long") or 0) > 0:
            v = float(p.get("baseline_long") or 0)
            if v > 0:
                bl = v
        if float(p.get("short") or 0) > 0:
            v = float(p.get("baseline_short") or 0)
            if v > 0:
                bs = v
    return {"long": bl, "short": bs}


def fees_activo(pesos: dict, symbol: str) -> dict[str, float]:
    """Fees acumulados L/S para un activo."""
    s = str(symbol or "").upper()
    fl = fs = 0.0
    for frente, p in (pesos or {}).items():
        if not str(frente).upper().startswith(s):
            continue
        fl += float(p.get("fees_paid_long") or 0)
        fs += float(p.get("fees_paid_short") or 0)
    return {"long": fl, "short": fs}


def resumen_promedios(pesos: dict) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for frente, p in (pesos or {}).items():
        pl = float(p.get("long") or 0)
        ps = float(p.get("short") or 0)
        if pl <= 0 and ps <= 0:
            continue
        row: dict[str, Any] = {"frente": frente}
        if pl > 0:
            row["long"] = round(pl, 6)
            row["precio_medio_long"] = round(float(p.get("precio_medio_long") or 0), 4)
        if ps > 0:
            row["short"] = round(ps, 6)
            row["precio_medio_short"] = round(float(p.get("precio_medio_short") or 0), 4)
        out.append(row)
    return out


def precio_ctx(ctx_map: dict | None, frente: str) -> float:
    if not ctx_map:
        return 0.0
    ctx = ctx_map.get(frente)
    if ctx is None:
        return 0.0
    if isinstance(ctx, dict):
        return float(ctx.get("precio") or ctx.get("last") or 0)
    return float(getattr(ctx, "precio", 0) or getattr(ctx, "last", 0) or 0)


def bootstrap_viable(ctx_map: dict | None, base: str | None = None) -> tuple[bool, str]:
    fl, fs = frentes_bootstrap(base)
    pl = precio_ctx(ctx_map, fl)
    ps = precio_ctx(ctx_map, fs)
    if pl <= 0:
        return False, f"SIN_PRECIO_{fl}"
    if ps <= 0:
        return False, f"SIN_PRECIO_{fs}"
    return True, "OK"
