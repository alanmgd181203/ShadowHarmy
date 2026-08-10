"""Densidad máxima del manto — forzar apalancamiento al techo del catálogo.

Doctrina: Igris despliega siempre a la densidad máxima por contrato (inverso + lineal).
Si Bybit rechaza el techo (posición abierta, risk limit, etc.), aviso claro y
se intenta el mayor escalón inferior aceptable.
"""
from __future__ import annotations

import re
import time
from typing import Any

import core.config as config
from core import beru_capital as bc
from core import mercado
from core import igris_manto as im


def force_max_on() -> bool:
    return bool(getattr(config, "IGRIS_FORCE_MAX_LEVERAGE", True))


def cooldown_s() -> float:
    return float(getattr(config, "IGRIS_LEVERAGE_FORCE_COOLDOWN_S", 300) or 300)


def _activos_lote_default() -> list[str]:
    """Santos del pase + exclusivos + bóveda — universo del manto vivo."""
    out: list[str] = []
    seen: set[str] = set()

    def _add(a: str) -> None:
        u = str(a or "").upper()
        if not u or u in seen:
            return
        seen.add(u)
        out.append(u)

    try:
        from core import pase_director as pd

        for p in pd.PASE_PASOS:
            _add(str(p.get("activo") or ""))
            if len(out) >= 40:
                break
    except Exception:
        pass
    for a in getattr(config, "IGRIS_ACTIVOS_EXCLUSIVOS", None) or []:
        _add(a)
    for a in getattr(config, "IGRIS_BOVEDA_BASES", None) or []:
        _add(a)
    for a in getattr(config, "ACTIVOS_PENTIVERSO", None) or []:
        _add(a)
    # Lote típico Asalto si pase vacío
    if not out:
        for a in (
            "ETH", "HYPE", "XRP", "MNT", "LTC", "SOL", "LINK",
            "ADA", "BCH", "AVAX", "FIL", "OP",
        ):
            _add(a)
    return out


def _escalones_prueba(lev_pedido: float) -> list[int]:
    """Pedido primero; luego escalones inferiores típicos Bybit."""
    pedido = max(1, int(round(float(lev_pedido or 1))))
    candidatos = [pedido]
    for x in (100, 75, 50, 25, 20, 15, 12, 10, 8, 5, 3, 2, 1):
        if x < pedido and x not in candidatos:
            candidatos.append(x)
    # Descenso fino cerca del pedido
    for step in (5, 2, 1):
        v = pedido - step
        while v > 1:
            if v not in candidatos:
                candidatos.append(v)
            v -= step
            if len(candidatos) > 40:
                break
        if len(candidatos) > 40:
            break
    # únicos preservando orden
    seen: set[int] = set()
    out: list[int] = []
    for c in candidatos:
        if c in seen or c < 1:
            continue
        seen.add(c)
        out.append(c)
    return out


def _parse_hint_max(msg: str) -> int | None:
    """Intenta leer un techo numérico del rechazo Bybit."""
    t = str(msg or "")
    patterns = (
        r"(?:max(?:imum)?\s*leverage|leverage\s*max(?:imum)?)\s*(?:is|=|:)?\s*(\d+)",
        r"(?:cannot exceed|not exceed|upto|up to)\s*(\d+)",
        r"(\d+)\s*x\s*(?:max|maximum)",
        r"max(?:imum)?[^\d]{0,24}(\d+)\s*x?",
    )
    for pat in patterns:
        m = re.search(pat, t, flags=re.I)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    return None


async def forzar_max_en_symbol(
    bridge,
    bel,
    *,
    symbol: str,
    category: str,
    lev_pedido: float,
    activo: str = "",
) -> dict[str, Any]:
    """Intenta techo de catálogo; si falla, baja escalones y avisa."""
    pedido = max(1, int(round(float(lev_pedido or 1))))
    cat = str(category or "linear").lower()
    sym = str(symbol or "")
    if not bridge or not sym:
        return {
            "ok": False,
            "symbol": sym,
            "category": cat,
            "pedido": pedido,
            "aplicado": None,
            "motivo": "sin_bridge_o_symbol",
        }

    aplicado: int | None = None
    ultimo_msg = ""
    for lev in _escalones_prueba(pedido):
        res = await bridge.set_leverage(sym, lev, category=cat)
        ultimo_msg = str(getattr(res, "mensaje", "") or "")
        if getattr(res, "exito", False):
            aplicado = lev
            break
        hint = _parse_hint_max(ultimo_msg)
        if hint and hint < lev and hint >= 1:
            # Priorizar hint en siguiente vuelta insertándolo
            # (el loop ya probará hint si está en escalones; forzar inmediato)
            res2 = await bridge.set_leverage(sym, hint, category=cat)
            ultimo_msg = str(getattr(res2, "mensaje", "") or ultimo_msg)
            if getattr(res2, "exito", False):
                aplicado = hint
                break

    out: dict[str, Any] = {
        "ok": aplicado is not None,
        "activo": str(activo or "").upper(),
        "symbol": sym,
        "category": cat,
        "pedido": pedido,
        "aplicado": aplicado,
        "motivo": "OK" if aplicado is not None else (ultimo_msg or "rechazado"),
    }

    if bel is None:
        return out

    act_txt = f"{activo} · " if activo else ""
    if aplicado is None:
        await bel.anotar(
            "IGRIS", "LEVERAGE_MAX_AVISO",
            f"{act_txt}{sym} ({cat}): pedido {pedido}x · Bybit NO dejó · {ultimo_msg}",
        )
    elif aplicado < pedido:
        await bel.anotar(
            "IGRIS", "LEVERAGE_MAX_AVISO",
            f"{act_txt}{sym} ({cat}): pedido {pedido}x · aplicado {aplicado}x "
            f"(máximo que Bybit aceptó ahora)",
        )
    else:
        await bel.anotar(
            "IGRIS", "LEVERAGE_MAX_OK",
            f"{act_txt}{sym} ({cat}): {aplicado}x (techo catálogo)",
        )
    return out


async def forzar_max_leverage_activo(
    bridge,
    bel,
    activo: str,
    *,
    forzar: bool | None = None,
) -> dict[str, Any]:
    """Fija densidad máxima en L inverso + S lineal del Santo."""
    if forzar is None:
        forzar = force_max_on()
    act = str(activo or "").upper()
    if not forzar or not act:
        return {"ok": True, "activo": act, "omitido": True, "piernas": []}

    try:
        fl, fs = im.frentes_bootstrap(act)
    except Exception as e:
        return {"ok": False, "activo": act, "motivo": f"frentes:{e}", "piernas": []}

    piernas: list[dict[str, Any]] = []
    for frente, lado in ((fl, "inverse"), (fs, "linear")):
        if not frente:
            continue
        sym = mercado.frente_a_symbol(frente)
        cat = mercado.frente_a_category(frente)
        if cat == "spot":
            continue
        lev = bc.apalancamiento_ejecucion(frente, cat)
        piernas.append(
            await forzar_max_en_symbol(
                bridge, bel,
                symbol=sym, category=cat, lev_pedido=lev, activo=act,
            )
        )

    ok_all = all(p.get("ok") for p in piernas) if piernas else False
    return {
        "ok": ok_all,
        "activo": act,
        "piernas": piernas,
        "avisos": [p for p in piernas if not p.get("ok") or (p.get("aplicado") or 0) < (p.get("pedido") or 0)],
    }


async def forzar_max_leverage_lote(
    bridge,
    bel,
    activos: list[str] | None = None,
    *,
    forzar: bool | None = None,
) -> dict[str, Any]:
    """Pasa el lote (o lista) a densidad máxima. No aborta el manto si uno falla."""
    if forzar is None:
        forzar = force_max_on()
    if not forzar:
        return {"ok": True, "omitido": True, "activos": [], "n_ok": 0, "n_aviso": 0}

    lista = [str(a).upper() for a in (activos or _activos_lote_default()) if a]
    resultados: list[dict[str, Any]] = []
    for act in lista:
        resultados.append(await forzar_max_leverage_activo(bridge, bel, act, forzar=True))
        # Respiro API Bybit
        await _sleep_brief()

    n_ok = sum(1 for r in resultados if r.get("ok"))
    n_aviso = sum(1 for r in resultados if r.get("avisos"))
    if bel is not None:
        await bel.anotar(
            "IGRIS", "LEVERAGE_MAX_LOTE",
            f"Densidad máxima · Santos={len(lista)} · ok={n_ok} · con_aviso={n_aviso}",
        )
    return {
        "ok": n_ok == len(lista),
        "activos": lista,
        "resultados": resultados,
        "n_ok": n_ok,
        "n_aviso": n_aviso,
    }


async def _sleep_brief() -> None:
    import asyncio

    await asyncio.sleep(float(getattr(config, "IGRIS_LEVERAGE_FORCE_GAP_S", 0.15) or 0.15))


class LeverageForceGate:
    """Evita spamear set_leverage en cada dual (cooldown por Santo)."""

    def __init__(self) -> None:
        self._until: dict[str, float] = {}

    def due(self, activo: str, *, ahora: float | None = None) -> bool:
        act = str(activo or "").upper()
        if not act:
            return False
        now = float(ahora if ahora is not None else time.time())
        return now >= float(self._until.get(act, 0.0))

    def mark(self, activo: str, *, ahora: float | None = None) -> None:
        act = str(activo or "").upper()
        if not act:
            return
        now = float(ahora if ahora is not None else time.time())
        self._until[act] = now + cooldown_s()
