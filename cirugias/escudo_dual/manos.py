"""Manos del escudo de dos metales. Rey e reina, cada uno su inverso.

No abre si no hay capa que sentar. Si la casa no responde, no inventa un cero.
Si el lado voltea, este latido solo sienta en cero.
"""
from __future__ import annotations

import uuid

REINA = "ETH-USD-SWAP"
REY = "BTC-USD-SWAP"
INST = REINA


def sentado(inst: str) -> float | None:
    """Dólares firmados del metal. None si el ojo no ve."""
    from core import okx_rest

    filtros = _filtros(okx_rest, inst)
    if filtros is None:
        return None
    return _vivo(okx_rest, inst, filtros["ct"])


def ajustar(meta_signed_usd: float, inst: str = INST) -> dict:
    """Acerca ese metal a la meta. Cero contra cero no manda orden."""
    from core import okx_rest

    if not okx_rest.credenciales_ok():
        return {"aplicado": False, "frase": "sin llaves"}
    filtros = _filtros(okx_rest, inst)
    if filtros is None:
        return {"aplicado": False, "frase": "sin talla"}
    vivo = _vivo(okx_rest, inst, filtros["ct"])
    if vivo is None:
        return {"aplicado": False, "frase": "ojo ciego, no planta"}
    meta = float(meta_signed_usd or 0)
    paso = filtros["ct"] * filtros["lot"]
    if vivo * meta < 0 and abs(vivo) > paso * 0.5:
        meta = 0.0
    if abs(meta - vivo) + 1e-9 < max(paso * 0.5, 1.0):
        return {"aplicado": False, "frase": "ya en la capa", "vivo": vivo}
    boc = meta - vivo
    pasos = int(abs(boc) / paso + 1e-9)
    qty = pasos * filtros["lot"]
    if qty + 1e-12 < filtros["min"]:
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
        "clOrdId": ((nombre[:3].upper() + uuid.uuid4().hex)[:32]),
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
    data = okx_rest.post_private("/api/v5/trade/order", cuerpo)
    fila = (list(data or [{}]) or [{}])[0]
    if str((fila or {}).get("sCode") or "0") not in ("0", ""):
        return {"aplicado": False, "frase": "la casa rechazó", "vivo": vivo}
    return {"aplicado": True, "frase": f"{nombre} {cuerpo['side']} {cuerpo['sz']}", "vivo": vivo}


def _filtros(okx, inst: str = INST) -> dict | None:
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


def _vivo(okx, inst: str, ct: float) -> float | None:
    try:
        filas = okx.get_private(
            "/api/v5/account/positions",
            params={"instType": "SWAP", "instId": inst},
        ) or []
    except Exception:
        return None
    for fila in filas:
        if isinstance(fila, dict) and str(fila.get("instId")) == inst:
            try:
                return float(fila.get("pos") or 0) * ct
            except (TypeError, ValueError):
                return None
    return 0.0


def _en_piernas(okx) -> bool:
    try:
        filas = okx.get_private("/api/v5/account/config") or []
        modo = str((list(filas) or [{}])[0].get("posMode") or "")
    except Exception:
        return False
    return modo == "long_short_mode"
