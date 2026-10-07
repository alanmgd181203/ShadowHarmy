"""Manos del manto de la bolsa. Rey e reina lineales, en dólares.

El contrato de la bolsa no vale su cara: vale el precio.
Cero contra cero no manda orden. Si el lado voltea, este latido solo sienta en cero.
"""
from __future__ import annotations

import uuid

from cirugias.escudo_dual.bolsa import REINA, REY


def contratos(delta_usd: float, precio: float, ct: float, lot: float, minimo: float) -> float:
    """Cuántos contratos cubren esos dólares, en pasos del lote. Cero si no alcanza uno."""
    px = float(precio or 0)
    cara = float(ct or 0)
    paso_ct = float(lot or 0)
    piso = float(minimo or 0)
    if px <= 0 or cara <= 0 or paso_ct <= 0 or piso <= 0:
        return 0.0
    paso_usd = paso_ct * cara * px
    if paso_usd <= 0:
        return 0.0
    n = int(abs(float(delta_usd or 0)) / paso_usd + 1e-9)
    qty = n * paso_ct
    if qty + 1e-12 < piso:
        return 0.0
    return float(qty)


def dolares(pos: float, ct: float, precio: float) -> float:
    """Dólares firmados de una pierna lineal."""
    return float(pos or 0) * float(ct or 0) * float(precio or 0)


def sentado(inst: str) -> float | None:
    """Dólares firmados del metal. None si el ojo no ve."""
    from core import okx_rest

    if not okx_rest.credenciales_ok():
        return None
    filtros = _filtros(okx_rest, inst)
    if filtros is None:
        return None
    vivo, _px = _vivo(okx_rest, inst, filtros)
    return vivo


def ajustar(meta_signed_usd: float, inst: str) -> dict:
    """Acerca ese metal a la meta. No cruza de lado en el mismo latido."""
    from core import okx_rest

    if not okx_rest.credenciales_ok():
        return {"aplicado": False, "frase": "sin llaves"}
    filtros = _filtros(okx_rest, inst)
    if filtros is None:
        return {"aplicado": False, "frase": "sin talla"}
    vivo, px = _vivo(okx_rest, inst, filtros)
    if vivo is None or px is None or px <= 0:
        return {"aplicado": False, "frase": "ojo ciego, no planta"}
    meta = float(meta_signed_usd or 0)
    paso = filtros["lot"] * filtros["ct"] * px
    if vivo * meta < 0 and abs(vivo) > paso * 0.5:
        meta = 0.0
    if abs(meta - vivo) + 1e-9 < max(paso * 0.5, 1.0):
        return {"aplicado": False, "frase": "ya en la capa", "vivo": vivo}
    boc = meta - vivo
    qty = contratos(boc, px, filtros["ct"], filtros["lot"], filtros["min"])
    if qty <= 0:
        return {"aplicado": False, "frase": "no alcanza un contrato", "vivo": vivo}
    reduce = (vivo > 0 and boc < 0) or (vivo < 0 and boc > 0)
    if reduce and abs(meta) > abs(vivo) + 1e-9:
        reduce = False
    nombre = "reina" if inst == REINA else "rey"
    cuerpo = {
        "instId": inst,
        "tdMode": "cross",
        "side": "buy" if boc > 0 else "sell",
        "ordType": "market",
        "sz": f"{qty:.8f}".rstrip("0").rstrip("."),
        "clOrdId": (("BOL" + uuid.uuid4().hex)[:32]),
    }
    if reduce:
        cuerpo["reduceOnly"] = True
    if _en_piernas(okx_rest):
        if vivo > 0:
            cuerpo["posSide"] = "long"
        elif vivo < 0:
            cuerpo["posSide"] = "short"
        elif boc > 0:
            cuerpo["posSide"] = "long"
        else:
            cuerpo["posSide"] = "short"
    else:
        cuerpo["posSide"] = "net"
    data = okx_rest.post_private("/api/v5/trade/order", cuerpo)
    fila = (list(data or [{}]) or [{}])[0]
    if str((fila or {}).get("sCode") or "0") not in ("0", ""):
        return {"aplicado": False, "frase": "la casa rechazó", "vivo": vivo}
    return {"aplicado": True, "frase": f"{nombre} {cuerpo['side']} {cuerpo['sz']}", "vivo": vivo}


def _filtros(okx, inst: str) -> dict | None:
    pub = okx.get_public(
        "/api/v5/public/instruments",
        params={"instType": "SWAP", "instId": inst},
    ) or []
    if not pub or not isinstance(pub[0], dict):
        return None
    fila = pub[0]
    try:
        ct = float(fila.get("ctVal") or 0)
        lot = float(fila.get("lotSz") or 0)
        minimo = float(fila.get("minSz") or lot)
    except (TypeError, ValueError):
        return None
    if ct <= 0 or lot <= 0 or minimo <= 0:
        return None
    return {"ct": ct, "lot": lot, "min": minimo}


def _precio(okx, inst: str, fila: dict | None) -> float:
    if isinstance(fila, dict):
        for clave in ("markPx", "last", "avgPx"):
            try:
                px = float(fila.get(clave) or 0)
            except (TypeError, ValueError):
                px = 0.0
            if px > 0:
                return px
    try:
        tik = okx.get_public(
            "/api/v5/market/ticker",
            params={"instId": inst},
        ) or []
        if tik and isinstance(tik[0], dict):
            return float(tik[0].get("last") or 0)
    except Exception:
        return 0.0
    return 0.0


def _vivo(okx, inst: str, filtros: dict) -> tuple[float | None, float | None]:
    try:
        filas = okx.get_private(
            "/api/v5/account/positions",
            params={"instType": "SWAP", "instId": inst},
        ) or []
    except Exception:
        return None, None
    fila = None
    for candidata in filas:
        if isinstance(candidata, dict) and str(candidata.get("instId")) == inst:
            fila = candidata
            break
    px = _precio(okx, inst, fila)
    if px <= 0:
        return None, None
    # En piernas puede haber long y short a la vez: sumar firmados.
    total = 0.0
    vio = False
    for candidata in filas:
        if not isinstance(candidata, dict) or str(candidata.get("instId")) != inst:
            continue
        vio = True
        try:
            q = float(candidata.get("pos") or 0)
        except (TypeError, ValueError):
            return None, None
        lado_f = str(candidata.get("posSide") or "net").strip().lower()
        if lado_f == "short":
            total += -abs(q)
        elif lado_f == "long":
            total += abs(q)
        else:
            total += q
    if not vio:
        return 0.0, px
    return dolares(total, filtros["ct"], px), px


def _en_piernas(okx) -> bool:
    try:
        filas = okx.get_private("/api/v5/account/config") or []
        modo = str((list(filas) or [{}])[0].get("posMode") or "")
    except Exception:
        return False
    return modo == "long_short_mode"
