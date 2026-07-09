"""Greed — evaluar cola Kaiser, ruta idónea, vetos, plan de ejecución.

Nota doctrina (21 §A): Greed no administra el manto (eso es Igris). Un arbitraje puede
cruzar frentes del manto y alterar L/S brevemente; Igris rebalancea/poda por margen.
"""
from __future__ import annotations

from typing import Any

import core.config as config
from core import greed_sizing as sizing
from core import greed_vip as vip
from core import greed_basis as basis


def oid_oportunidad(op: dict) -> str:
    base = op.get("base", "?")
    tipo = op.get("tipo_spread", "?")
    if str(tipo).startswith("multicruce_"):
        via = op.get("via_quote", "?")
        return f"{base}:{tipo}:{via}"
    fc = (op.get("frentes") or {}).get("compra", "")
    return f"{base}:{tipo}:{fc}"


def vetos_globales(
    *,
    tank_semaforo: str,
    margen_ocupado_pct: float,
    equity: float,
) -> tuple[bool, str]:
    """True = pausar radar Greed. Ley marcial: solo filtra planes (§C — VIP permitido)."""
    if getattr(config, "SAFE_MODE", False):
        return True, "SAFE_MODE"
    if tank_semaforo == "ROJO":
        return True, "TANK_ROJO"
    if equity <= 0:
        return True, "SIN_EQUITY"
    return False, "OK"


def filtrar_planes_ley_marcial(
    planes: list[dict],
    margen_ocupado_pct: float,
    *,
    vip_oids_activos: set[str] | None = None,
) -> list[dict]:
    """≥95% margen: solo VIP/Mega VIP y misiones VIP en curso (21 §C)."""
    ley = float(getattr(config, "MURO_LEY_MARCIAL", 95.0))
    if float(margen_ocupado_pct) < ley:
        return planes
    if not getattr(config, "GREED_VIP_PERMITIR_EN_LEY_MARCIAL", True):
        return []
    vip_oids_activos = vip_oids_activos or set()
    return [
        p for p in planes
        if p.get("es_vip") or p.get("oid") in vip_oids_activos
    ]


def ruta_idonea_para_base(kaiser_digest: dict, base: str) -> dict | None:
    mv = (kaiser_digest.get("metaverso") or {}).get(base.upper())
    if not mv:
        return None
    return mv.get("ruta_idonea")


def _plan_base(
    op: dict,
    *,
    oid: str,
    base: str,
    tipo: str,
    frente_long: str,
    frente_short: str,
    ruta: dict | None,
    extra: dict,
) -> dict[str, Any]:
    return {
        "ok": True,
        "oid": oid,
        "base": base,
        "tipo_spread": tipo,
        "frente_long": frente_long,
        "frente_short": frente_short,
        "ruta_idonea": ruta,
        "op": dict(op),
        **extra,
    }


def resolver_plan(
    op: dict,
    kaiser_digest: dict,
    *,
    equity: float,
    margen_ocupado_pct: float,
    masa_autorizada: float,
    tank_semaforo: str,
) -> dict[str, Any]:
    """Plan de misión Greed: VIP (≥0.5% neto ruta) o normal (perfil + mordida)."""
    base = str(op.get("base", "")).upper()
    tipo = str(op.get("tipo_spread", ""))
    perfiles = kaiser_digest.get("perfiles") or {}
    ruta = ruta_idonea_para_base(kaiser_digest, base)
    pipeline_ms = float(
        op.get("pipeline_ms")
        or (kaiser_digest.get("pipeline") or {}).get("total_ms")
        or 0
    )
    oid = oid_oportunidad(op)
    fc = (op.get("frentes") or {}).get("compra")
    fv = (op.get("frentes") or {}).get("venta")
    piernas = op.get("piernas") or []
    if piernas:
        fc = piernas[0].get("frente", fc)
        fv = piernas[-1].get("frente", fv)
    frente_long, frente_short = str(fc), str(fv)

    # --- VIP / Mega VIP: salta perfil, micro-órdenes ---
    if getattr(config, "GREED_VIP_ENABLED", True):
        vip_info = vip.evaluar_plan_vip(
            op, ruta,
            equity=equity,
            margen_ocupado_pct=margen_ocupado_pct,
        )
        if vip_info:
            return _plan_base(
                op,
                oid=oid,
                base=base,
                tipo=tipo,
                frente_long=frente_long,
                frente_short=frente_short,
                ruta=ruta,
                extra={
                    "modo": vip_info["modo_vip"],
                    "modo_vip": vip_info["modo_vip"],
                    "neto_ruta_pct": vip_info["neto_ruta_pct"],
                    "techo_vip_usd": vip_info["techo_vip_usd"],
                    "min_order_usd": vip_info["min_order_usd"],
                    "notional_usd": vip_info["min_order_usd"],
                    "es_vip": True,
                },
            )

    # --- Normal ---
    perfil = sizing.perfil_edge_para_op(perfiles, base, tipo)
    fav_long = sizing.favorable_long_desde_op(op)

    v_humo, mot_humo = sizing.veto_humo_tres_plazos(perfil, fav_long)
    if v_humo:
        return {"ok": False, "motivo": mot_humo, "oid": oid}

    v_perfil, mot_perfil = sizing.veto_perfil_mediano(perfil, base)
    if v_perfil and not sizing.es_huerfana(base):
        return {"ok": False, "motivo": mot_perfil, "oid": oid}

    mordida_info = sizing.calcular_mordida(
        op,
        equity=equity,
        margen_ocupado_pct=margen_ocupado_pct,
        perfiles=perfiles,
        ruta_idonea=ruta,
        tank_semaforo=tank_semaforo,
        pipeline_ms=pipeline_ms,
        masa_autorizada=masa_autorizada,
    )
    if not mordida_info.get("ok"):
        return {
            "ok": False,
            "motivo": mordida_info.get("motivo", "MORDIDA_INVALIDA"),
            "oid": oid,
            "mordida": mordida_info,
        }

    if ruta and not ruta.get("arista_directa"):
        neto_ruta = float(ruta.get("regalo_neto_pct") or 0)
        if neto_ruta <= 0:
            return {"ok": False, "motivo": "RUTA_NETO_NEGATIVO", "oid": oid}

    # --- Basis hold (spot↔perp / lineal↔inverse) — manto temporal ---
    if tipo in basis.TIPOS_BASIS and basis.basis_hold_habilitado():
        ok_b, mot_b = basis.debe_entrar_basis(op)
        if ok_b:
            plan = _plan_base(
                op,
                oid=basis.oid_basis(op),
                base=base,
                tipo=tipo,
                frente_long=frente_long,
                frente_short=frente_short,
                ruta=ruta,
                extra={
                    "modo": "BASIS_HOLD",
                    "es_vip": False,
                    "es_basis": True,
                    "notional_usd": mordida_info["mordida_usd"],
                    "mordida": mordida_info,
                },
            )
            return basis.enriquecer_plan_basis(plan, op)
        if mot_b not in ("BASIS_OFF", "NO_BASIS"):
            return {"ok": False, "motivo": mot_b, "oid": oid}

    return _plan_base(
        op,
        oid=oid,
        base=base,
        tipo=tipo,
        frente_long=frente_long,
        frente_short=frente_short,
        ruta=ruta,
        extra={
            "modo": "NORMAL",
            "es_vip": False,
            "notional_usd": mordida_info["mordida_usd"],
            "mordida": mordida_info,
            "piernas": list(piernas) if piernas else None,
            "n_piernas": len(piernas) if piernas else 2,
            "via_quote": op.get("via_quote"),
        },
    )


def op_viva_por_oid(vivas: list[dict], oid: str) -> dict | None:
    for op in vivas:
        if oid_oportunidad(op) == oid:
            return op
        if basis.oid_basis(op) == oid:
            return op
    return None


def op_basis_por_hold(hold: dict, vivas: list[dict]) -> dict | None:
    oid = hold.get("oid", "")
    base = hold.get("base", "")
    tipo = hold.get("tipo_spread", "")
    for op in vivas:
        if str(op.get("base", "")).upper() == str(base).upper() and op.get("tipo_spread") == tipo:
            return op
    return op_viva_por_oid(vivas, oid)


def planes_desde_kaiser(
    kaiser_digest: dict,
    oportunidades_vivas: list[dict],
    *,
    equity: float,
    margen_ocupado_pct: float,
    masa_autorizada: float,
    tank_semaforo: str,
    abortadas_oids: set[str] | None = None,
    vip_oids_activos: set[str] | None = None,
) -> list[dict]:
    abortadas_oids = abortadas_oids or set()
    vip_oids_activos = vip_oids_activos or set()
    planes: list[dict] = []

    for op in oportunidades_vivas:
        oid = oid_oportunidad(op)
        if oid in abortadas_oids:
            continue
        if str(op.get("estado", "VIVA")) == "ABORTADA":
            continue
        plan = resolver_plan(
            op,
            kaiser_digest,
            equity=equity,
            margen_ocupado_pct=margen_ocupado_pct,
            masa_autorizada=masa_autorizada,
            tank_semaforo=tank_semaforo,
        )
        if plan.get("ok"):
            planes.append(plan)

    # Misiones VIP en curso: prioridad aunque el plan sea re-resuelto
    def sort_key(p: dict) -> tuple:
        vip_pri = 0 if p.get("es_vip") or p["oid"] in vip_oids_activos else 1
        neto = float(p.get("neto_ruta_pct") or 0)
        notional = float(p.get("notional_usd") or 0)
        return (vip_pri, -neto, -notional)

    planes.sort(key=sort_key)
    top = int(getattr(config, "GREED_PLANES_TOP_N", 3))
    return planes[:top]
