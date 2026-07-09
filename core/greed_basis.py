"""Greed — manto temporal / basis (spot↔perp, lineal↔inverse) con hold y salida."""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core import ancla


TIPOS_BASIS = frozenset({"spot_vs_perp", "lineal_vs_inverse"})


def basis_hold_habilitado() -> bool:
    return getattr(config, "GREED_BASIS_HOLD_ENABLED", True)


def oid_basis(op: dict) -> str:
    base = op.get("base", "?")
    tipo = op.get("tipo_spread", "?")
    fc = (op.get("frentes") or {}).get("compra", "")
    return f"BASIS:{base}:{tipo}:{fc}"


def piernas_desde_op(op: dict) -> tuple[list[dict], list[dict]] | None:
    """Piernas entrada/salida desde oportunidad Ancla."""
    fc = (op.get("frentes") or {}).get("compra")
    fv = (op.get("frentes") or {}).get("venta")
    if not fc or not fv:
        row = op
        if op.get("tipo_spread") or op.get("tipo"):
            return piernas_desde_fila(row)
        return None
    entrada = [
        {"frente": str(fc), "side": "Buy", "rol": "basis_compra"},
        {"frente": str(fv), "side": "Sell", "rol": "basis_venta"},
    ]
    salida = [
        {"frente": str(fc), "side": "Sell", "rol": "basis_cierra_compra"},
        {"frente": str(fv), "side": "Buy", "rol": "basis_cierra_venta"},
    ]
    return entrada, salida


def piernas_desde_fila(row: dict) -> tuple[list[dict], list[dict]] | None:
    """(entrada, salida) — salida invierte lados."""
    base = str(row.get("base", "")).upper()
    tipo = str(row.get("tipo") or row.get("tipo_spread") or "")
    par = ancla.frentes_desde_fila_matriz(base, tipo, row)
    if not par:
        return None
    fc, fv = par
    entrada = [
        {"frente": fc, "side": "Buy", "rol": "basis_compra"},
        {"frente": fv, "side": "Sell", "rol": "basis_venta"},
    ]
    salida = [
        {"frente": fc, "side": "Sell", "rol": "basis_cierra_compra"},
        {"frente": fv, "side": "Buy", "rol": "basis_cierra_venta"},
    ]
    return entrada, salida


def spread_actual_desde_op(op: dict) -> float:
    return float(op.get("spread_bruto_pct") or op.get("spread_pct") or 0)


def neto_actual_desde_op(op: dict) -> float:
    return float(op.get("regalo_neto_pct_est") or 0)


def debe_entrar_basis(op: dict) -> tuple[bool, str]:
    if not basis_hold_habilitado():
        return False, "BASIS_OFF"
    tipo = str(op.get("tipo_spread", ""))
    if tipo not in TIPOS_BASIS:
        return False, "NO_BASIS"
    spread = spread_actual_desde_op(op)
    min_sp = float(getattr(config, "GREED_BASIS_ENTRADA_SPREAD_MIN_PCT", 0.20))
    if spread < min_sp:
        return False, "SPREAD_BAJO"
    neto = neto_actual_desde_op(op)
    fees = float(op.get("fees_total_pct") or 0)
    if neto <= fees:
        return False, "NETO_BAJO_FEES"
    return True, "OK"


def debe_salir_basis(hold: dict, op: dict | None) -> tuple[bool, str]:
    if not op:
        return True, "OP_DESAPARECIDA"
    max_s = float(getattr(config, "GREED_BASIS_HOLD_MAX_S", 3600))
    edad = time.time() - float(hold.get("ts_entrada") or 0)
    if edad > max_s:
        return True, "TIMEOUT"
    spread = spread_actual_desde_op(op)
    exit_sp = float(getattr(config, "GREED_BASIS_SALIDA_SPREAD_MAX_PCT", 0.05))
    if spread <= exit_sp:
        return True, "SPREAD_CERRADO"
    spread_ent = float(hold.get("spread_entrada_pct") or 0)
    neto_capturado = spread_ent - spread
    min_neto = float(getattr(config, "GREED_BASIS_SALIDA_NETO_MIN_PCT", 0.08))
    if neto_capturado >= min_neto:
        return True, "OBJETIVO_NETO"
    neto = neto_actual_desde_op(op)
    if neto < float(getattr(config, "GREED_BASIS_ABORT_NETO_PCT", 0.02)):
        return True, "SPREAD_EXPANDIO"
    return False, "HOLD"


def crear_hold(plan: dict, op: dict) -> dict[str, Any]:
    piernas = plan.get("piernas_entrada") or plan.get("piernas") or []
    par = piernas_desde_op(op)
    salida = par[1] if par else (plan.get("piernas_salida") or [])
    frentes = list(dict.fromkeys(p["frente"] for p in piernas))
    return {
        "oid": plan["oid"],
        "base": plan["base"],
        "tipo_spread": plan["tipo_spread"],
        "modo": "BASIS_HOLD",
        "notional_usd": float(plan.get("notional_usd") or 0),
        "spread_entrada_pct": spread_actual_desde_op(op),
        "neto_entrada_pct": neto_actual_desde_op(op),
        "piernas_entrada": list(piernas),
        "piernas_salida": list(salida),
        "frentes": frentes,
        "ts_entrada": time.time(),
        "deployed_usd": float(plan.get("notional_usd") or 0),
    }


def enriquecer_plan_basis(plan: dict, op: dict) -> dict[str, Any]:
    par = piernas_desde_op(op)
    if not par:
        return {**plan, "ok": False, "motivo": "SIN_PIERNAS_BASIS"}
    entrada, salida = par
    plan = dict(plan)
    plan["modo"] = "BASIS_HOLD"
    plan["piernas_entrada"] = entrada
    plan["piernas_salida"] = salida
    plan["piernas"] = entrada
    plan["oid"] = oid_basis(op)
    plan["frente_long"] = entrada[0]["frente"]
    plan["frente_short"] = entrada[1]["frente"]
    frentes_t = (op.get("frentes") or {}).get("todos")
    if frentes_t:
        op = dict(op)
        op["frentes"] = {**op.get("frentes", {}), "todos": frentes_t}
    plan["op"] = op
    return plan


def max_holds_abiertos() -> int:
    return int(getattr(config, "GREED_BASIS_MAX_ABIERTOS", 3))


def resumen_holds(holds: dict[str, dict]) -> list[dict]:
    out: list[dict] = []
    for h in holds.values():
        out.append({
            "oid": h.get("oid"),
            "base": h.get("base"),
            "tipo": h.get("tipo_spread"),
            "notional_usd": h.get("notional_usd"),
            "spread_entrada_pct": h.get("spread_entrada_pct"),
            "edad_s": round(time.time() - float(h.get("ts_entrada") or 0), 1),
        })
    return out
