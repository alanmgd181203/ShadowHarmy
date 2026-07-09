"""Greed VIP / Mega VIP — micro-órdenes, sondas, escalado por neto metaverso."""
from __future__ import annotations

from typing import Any

import core.config as config
from core import greed_sizing as sizing


def neto_efectivo_ruta(op: dict, ruta: dict | None) -> float:
    """Neto % post ruta idónea metaverso (o Ancla en la op)."""
    if ruta:
        if ruta.get("arista_directa"):
            ad = ruta["arista_directa"]
            return float(
                ad.get("regalo_neto_pct")
                or ad.get("regalo_neto_pct_est")
                or 0
            )
        nr = float(ruta.get("regalo_neto_pct") or 0)
        if nr > 0:
            return nr
    return float(op.get("regalo_neto_pct_est") or 0)


def clasificar_modo_vip(neto_pct: float, *, equity: float | None = None) -> str | None:
    mega = float(getattr(config, "GREED_MEGA_VIP_NETO_MIN_PCT", 1.0))
    vip = float(getattr(config, "GREED_VIP_NETO_MIN_PCT", 0.5))
    eq_min = float(getattr(config, "MONARCA_MEGA_VIP_EQUITY_MIN", 100.0))
    if neto_pct >= mega:
        if equity is not None and equity < eq_min:
            return "VIP" if neto_pct >= vip else None
        return "MEGA_VIP"
    if neto_pct >= vip:
        return "VIP"
    return None


def riesgo_pct_para_modo(modo: str, mega_desbloqueado: bool) -> float:
    if modo == "MEGA_VIP" and mega_desbloqueado:
        return float(getattr(config, "GREED_MEGA_VIP_RIESGO_MAX_PCT", 0.05))
    return float(getattr(config, "GREED_RIESGO_MAX_PCT_CUENTA", 0.01))


def techo_modo_usd(
    op: dict,
    *,
    equity: float,
    margen_ocupado_pct: float,
    modo: str,
    mega_desbloqueado: bool = False,
) -> dict[str, Any]:
    riesgo = riesgo_pct_para_modo(modo, mega_desbloqueado)
    max_ancla = float(op.get("entrada_maxima_usd") or 0)
    fc = (op.get("frentes") or {}).get("compra")
    fv = (op.get("frentes") or {}).get("venta")
    frentes = [str(x) for x in (fc, fv) if x]
    lev = sizing.apalancamiento_ruta(frentes)
    cap_margen = sizing.margen_libre_usd(equity, margen_ocupado_pct) * lev
    cap_riesgo = equity * riesgo * max(lev, 1.0)
    techo = min(max_ancla, cap_margen, cap_riesgo) if max_ancla > 0 else 0.0
    return {
        "techo_usd": round(max(0.0, techo), 2),
        "cap_riesgo_usd": round(cap_riesgo, 2),
        "riesgo_pct": riesgo,
        "apalancamiento": lev,
        "mega_desbloqueado": mega_desbloqueado,
    }


def min_order_op(op: dict) -> float:
    from core import ancla
    fc = (op.get("frentes") or {}).get("compra", "")
    return float(
        op.get("min_order_usd_cruce")
        or ancla.min_order_usd_cruce([str(fc), str((op.get("frentes") or {}).get("venta", ""))])
        or ancla.min_order_usd_frente(str(fc))
    )


def neto_continuar_min() -> float:
    return float(getattr(config, "GREED_VIP_NETO_CONTINUAR_PCT", 0.5))


def sondas_requeridas() -> int:
    return int(getattr(config, "GREED_VIP_SONDAS_MIN", 3))


def elegible_vip(neto_pct: float) -> bool:
    return clasificar_modo_vip(neto_pct) is not None


def crear_estado_vip(
    plan: dict,
    *,
    equity: float,
    margen_ocupado_pct: float,
) -> dict[str, Any]:
    op = plan["op"]
    modo = plan["modo_vip"]
    mega = modo == "MEGA_VIP"
    techo_vip = techo_modo_usd(
        op, equity=equity, margen_ocupado_pct=margen_ocupado_pct,
        modo=modo, mega_desbloqueado=False,
    )
    techo_mega = techo_modo_usd(
        op, equity=equity, margen_ocupado_pct=margen_ocupado_pct,
        modo="MEGA_VIP", mega_desbloqueado=True,
    ) if mega else techo_vip
    min_ord = min_order_op(op)
    return {
        "oid": plan["oid"],
        "modo": modo,
        "mega_desbloqueado": False,
        "sondas_ok": 0,
        "micros_total": 0,
        "deployed_usd": 0.0,
        "techo_vip_usd": techo_vip["techo_usd"],
        "techo_mega_usd": techo_mega["techo_usd"],
        "min_order_usd": min_ord,
        "neto_inicial_pct": plan.get("neto_ruta_pct", 0),
        "frente_buy": plan["frente_long"],
        "frente_sell": plan["frente_short"],
        "base": plan["base"],
        "tipo_spread": plan["tipo_spread"],
        "abort": False,
    }


def techo_activo(estado: dict) -> float:
    if estado.get("mega_desbloqueado"):
        return float(estado.get("techo_mega_usd") or 0)
    return float(estado.get("techo_vip_usd") or 0)


def puede_escalar(estado: dict) -> bool:
    min_o = float(estado.get("min_order_usd") or 0)
    return (float(estado.get("deployed_usd") or 0) + min_o) <= techo_activo(estado) + 1e-6


def siguiente_micro_usd(estado: dict) -> float:
    return float(estado.get("min_order_usd") or 0)


def tras_fill_ok(estado: dict, micro_usd: float, neto_actual_pct: float) -> dict[str, Any]:
    """Actualiza estado tras micro exitosa; puede desbloquear Mega VIP."""
    estado = dict(estado)
    estado["sondas_ok"] = int(estado.get("sondas_ok") or 0) + 1
    estado["micros_total"] = int(estado.get("micros_total") or 0) + 1
    estado["deployed_usd"] = round(float(estado.get("deployed_usd") or 0) + micro_usd, 2)
    mega_min = float(getattr(config, "GREED_MEGA_VIP_NETO_MIN_PCT", 1.0))
    if (
        estado.get("modo") == "MEGA_VIP"
        and estado["sondas_ok"] >= sondas_requeridas()
        and neto_actual_pct >= mega_min
    ):
        estado["mega_desbloqueado"] = True
    return estado


def debe_continuar(neto_actual_pct: float) -> bool:
    return neto_actual_pct >= neto_continuar_min()


def evaluar_plan_vip(
    op: dict,
    ruta: dict | None,
    *,
    equity: float,
    margen_ocupado_pct: float,
) -> dict[str, Any] | None:
    """Plan VIP si neto ruta ≥ umbral y techo ≥ min_order."""
    neto = neto_efectivo_ruta(op, ruta)
    modo = clasificar_modo_vip(neto, equity=equity)
    if not modo:
        return None
    techo = techo_modo_usd(
        op, equity=equity, margen_ocupado_pct=margen_ocupado_pct,
        modo=modo, mega_desbloqueado=False,
    )
    min_ord = min_order_op(op)
    if techo["techo_usd"] < min_ord:
        return None
    if ruta and not ruta.get("arista_directa"):
        if float(ruta.get("regalo_neto_pct") or 0) <= 0:
            return None
    fc = (op.get("frentes") or {}).get("compra")
    fv = (op.get("frentes") or {}).get("venta")
    return {
        "modo_vip": modo,
        "neto_ruta_pct": round(neto, 4),
        "techo_vip_usd": techo["techo_usd"],
        "min_order_usd": min_ord,
        "frente_long": str(fc),
        "frente_short": str(fv),
    }
