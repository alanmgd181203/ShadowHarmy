"""Ojos Beru rango — last lineal USDT (donde vive el oficio).

Espejo del Beru spot fósil: ciego a spot, inverso, índice y orderbook como cerebro.
En ritual de rango, Tank y el puente se estrechan a lineal USDT del Santo.
Pregón vivo: tratos públicos lineal (mecha). El ticker es muleta. REST: pozo
si cae el WS. Sin inventar precio con spot.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

import core.config as config
from core import beru_mar

# Claves de frente que Beru rango PUEDE usar como ojo
_CLAVES_LINEAL = ("USDT_LINEAL",)
_CLAVES_INVERSE = ("USD_INVERSE",)


def mercado_norm(mercado: str | None = None) -> str:
    m = str(
        mercado or getattr(config, "BERU_RANGO_MERCADO", "linear") or "linear"
    ).strip().lower()
    return m if m in ("linear", "inverse") else "linear"


def perfil_norm(perfil: str | None = None) -> str:
    """Geometría Beru rango: normal (default) · feria (orejas x2)."""
    p = str(
        perfil or getattr(config, "BERU_RANGO_PERFIL", "normal") or "normal"
    ).strip().lower()
    return p if p in ("normal", "feria") else "normal"


def _claves(mercado: str | None = None) -> tuple[str, ...]:
    return _CLAVES_INVERSE if mercado_norm(mercado) == "inverse" else _CLAVES_LINEAL


def _symbol_rest(activo: str, mercado: str | None = None) -> str:
    u = str(activo or "").strip().upper()
    return f"{u}USD" if mercado_norm(mercado) == "inverse" else f"{u}USDT"


def _category_rest(mercado: str | None = None) -> str:
    return "inverse" if mercado_norm(mercado) == "inverse" else "linear"


def rest_fallback_activo() -> bool:
    return bool(getattr(config, "BERU_RANGO_OJOS_REST_FALLBACK", True))


def rest_intervalo_s() -> float:
    return float(getattr(config, "BERU_RANGO_OJOS_REST_S", 10.0) or 10.0)


def ws_max_age_s() -> float:
    return float(getattr(config, "BERU_RANGO_OJOS_WS_MAX_AGE_S", 5.0) or 5.0)


def rio_ws_vivo(tank) -> bool:
    """True si el río WS de last lineal late. La muleta REST no cuenta."""
    if tank is None:
        return False
    ts = float(getattr(tank, "ts_rio_lineal_ws", 0) or 0)
    if ts <= 0:
        return False
    return (time.time() - ts) <= ws_max_age_s()


def muleta_rest_necesaria(tank) -> bool:
    if not rest_fallback_activo():
        return False
    return not rio_ws_vivo(tank)


def _host_publico() -> str:
    if beru_mar.es_okx():
        return "https://www.okx.com"
    if bool(getattr(config, "TESTNET", False)):
        return "https://api-testnet.bybit.com"
    return "https://api.bybit.com"


def claves_lineal(activo: str) -> tuple[str, ...]:
    u = str(activo or "").strip().upper()
    if not u:
        return ()
    return tuple(f"{u}{suf}" for suf in _CLAVES_LINEAL)


def claves_inverse(activo: str) -> tuple[str, ...]:
    u = str(activo or "").strip().upper()
    if not u:
        return ()
    return tuple(f"{u}{suf}" for suf in _CLAVES_INVERSE)


def claves_ojo(activo: str, mercado: str | None = None) -> tuple[str, ...]:
    u = str(activo or "").strip().upper()
    if not u:
        return ()
    return tuple(f"{u}{suf}" for suf in _claves(mercado))


def frentes_lineal_tank(bases: list[str] | None) -> list[str]:
    """Solo last lineal USDT de esos Santos. Ciego a spot/inverso/futuros."""
    acts = [str(a or "").strip().upper() for a in (bases or []) if str(a or "").strip()]
    if not acts:
        act = str(getattr(config, "BERU_RANGO_ACTIVO", "ETH") or "ETH").upper()
        if act:
            acts = [act]
    out: list[str] = []
    seen: set[str] = set()
    for act in acts:
        for clave in claves_lineal(act):
            if clave not in seen:
                seen.add(clave)
                out.append(clave)
    for f in list(getattr(config, "FRENTES_TANK", None) or []):
        fu = str(f or "").upper()
        if not fu.endswith("USDT_LINEAL"):
            continue
        if acts and not any(fu.startswith(f"{a}USDT") for a in acts):
            continue
        if fu not in seen:
            seen.add(fu)
            out.append(fu)
    return out


def frentes_inverse_tank(bases: list[str] | None) -> list[str]:
    """Solo last inverso USD de esos Santos. Ciego a spot/lineal."""
    acts = [str(a or "").strip().upper() for a in (bases or []) if str(a or "").strip()]
    if not acts:
        act = str(getattr(config, "BERU_RANGO_ACTIVO", "ETH") or "ETH").upper()
        if act:
            acts = [act]
    out: list[str] = []
    seen: set[str] = set()
    for act in acts:
        for clave in claves_inverse(act):
            if clave not in seen:
                seen.add(clave)
                out.append(clave)
    for f in list(getattr(config, "FRENTES_TANK", None) or []):
        fu = str(f or "").upper()
        if not fu.endswith("USD_INVERSE"):
            continue
        if acts and not any(fu.startswith(f"{a}USD") for a in acts):
            continue
        if fu not in seen:
            seen.add(fu)
            out.append(fu)
    return out


def frentes_ojo_tank(bases: list[str] | None, mercado: str | None = None) -> list[str]:
    if mercado_norm(mercado) == "inverse":
        return frentes_inverse_tank(bases)
    return frentes_lineal_tank(bases)


def last_desde_precios(
    precios: dict | None, activo: str, mercado: str | None = None,
) -> float:
    """Solo last del mercado pedido. 0 si no hay — no inventar con otro rail."""
    if not precios:
        return 0.0
    for clave in claves_ojo(activo, mercado):
        try:
            px = float(precios.get(clave) or 0)
        except (TypeError, ValueError):
            px = 0.0
        if px > 0:
            return px
    return 0.0


def last_lineal_desde_precios(precios: dict | None, activo: str) -> float:
    return last_desde_precios(precios, activo, mercado="linear")


def last_inverse_desde_precios(precios: dict | None, activo: str) -> float:
    return last_desde_precios(precios, activo, mercado="inverse")


def last_desde_tank(tank, activo: str, mercado: str | None = None) -> float:
    """Lee last del líder Tank para el mercado pedido."""
    act = str(activo or "").strip().upper()
    if not act or tank is None:
        return 0.0
    try:
        lider = None
        if hasattr(tank, "_obtener_lider_verde"):
            lider = tank._obtener_lider_verde()
        if not lider:
            nodos = list(getattr(tank, "nodos", None) or [])
            if nodos:
                lider = max(
                    nodos,
                    key=lambda n: float(getattr(n, "ultima_actualizacion", 0) or 0),
                )
        if not lider:
            precios = getattr(tank, "precios", None) or {}
            return last_desde_precios(precios, act, mercado)
        if hasattr(lider, "precios_con_reflejo"):
            precios = lider.precios_con_reflejo() or {}
        else:
            precios = getattr(lider, "precios", None) or {}
        return last_desde_precios(precios, act, mercado)
    except Exception:
        return 0.0


def last_lineal_desde_tank(tank, activo: str) -> float:
    """Lee last lineal del líder Tank; 0 si ciego (sin fallback spot)."""
    return last_desde_tank(tank, activo, mercado="linear")


def last_inverse_desde_tank(tank, activo: str) -> float:
    return last_desde_tank(tank, activo, mercado="inverse")


def _latido_vacio(last: float = 0.0) -> dict[str, Any]:
    px = float(last or 0)
    return {"last": px, "high": px, "low": px, "prints": []}


def latido_desde_tank(tank, activo: str, mercado: str | None = None) -> dict[str, Any]:
    """Last + extremos + tratos del latido del mercado pedido."""
    last = last_desde_tank(tank, activo, mercado)
    act = str(activo or "").strip().upper()
    if not act or tank is None:
        return _latido_vacio(last)
    merged = _latido_vacio(last)
    consumir = getattr(tank, "consumir_latido_lineal", None)
    if not callable(consumir):
        return merged
    for clave in claves_ojo(act, mercado):
        try:
            lat = consumir(clave) or {}
        except Exception:
            continue
        px = float(lat.get("last") or 0)
        hi = float(lat.get("high") or 0)
        lo = float(lat.get("low") or 0)
        prints = [float(p) for p in (lat.get("prints") or []) if float(p or 0) > 0]
        if px > 0:
            merged["last"] = px
        if hi > 0:
            merged["high"] = max(float(merged.get("high") or 0), hi)
        if lo > 0:
            prev = float(merged.get("low") or 0)
            merged["low"] = lo if prev <= 0 else min(prev, lo)
        if prints:
            merged["prints"] = list(merged.get("prints") or []) + prints
            # Cap suave
            if len(merged["prints"]) > 500:
                merged["prints"] = merged["prints"][-500:]
        if px > 0 or prints:
            break
    # Refuerzo: el last vivo del tanque también cuenta en la mecha.
    if last > 0:
        merged["last"] = last
        hi = float(merged.get("high") or 0)
        lo = float(merged.get("low") or 0)
        merged["high"] = last if hi <= 0 else max(hi, last)
        merged["low"] = last if lo <= 0 else min(lo, last)
    if float(merged.get("last") or 0) <= 0 and last > 0:
        merged = _latido_vacio(last)
    elif float(merged.get("last") or 0) > 0:
        last = float(merged["last"])
        if float(merged.get("high") or 0) <= 0:
            merged["high"] = last
        if float(merged.get("low") or 0) <= 0:
            merged["low"] = last
    return merged


def latido_lineal_desde_tank(tank, activo: str) -> dict[str, Any]:
    return latido_desde_tank(tank, activo, mercado="linear")


def latido_inverse_desde_tank(tank, activo: str) -> dict[str, Any]:
    return latido_desde_tank(tank, activo, mercado="inverse")


def _get_json_publico(url: str, timeout: float = 8.0) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": "ShadowHarmy/beru-rango-ojos"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw or "{}")
    return data if isinstance(data, dict) else {}


def _tickers_publicos(mercado: str | None = None) -> dict[str, float]:
    """lastPrice público — no usa la boca de combate."""
    if beru_mar.es_okx():
        url = f"{_host_publico()}/api/v5/market/tickers?instType=SWAP"
        try:
            payload = _get_json_publico(url)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return {}
        out: dict[str, float] = {}
        for row in (payload.get("data") or []):
            if not isinstance(row, dict):
                continue
            inst = str(row.get("instId") or "")
            if not inst.endswith("-USDT-SWAP"):
                continue
            act = beru_mar.inst_id_a_activo(inst)
            sym = f"{act}USDT"
            try:
                px = float(row.get("last") or 0)
            except (TypeError, ValueError):
                continue
            if sym and px > 0:
                out[sym] = px
        return out
    cat = _category_rest(mercado)
    url = f"{_host_publico()}/v5/market/tickers?category={cat}"
    try:
        payload = _get_json_publico(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return {}
    out: dict[str, float] = {}
    for row in ((payload.get("result") or {}).get("list") or []):
        if not isinstance(row, dict):
            continue
        sym = str(row.get("symbol") or "").upper()
        try:
            px = float(row.get("lastPrice") or 0)
        except (TypeError, ValueError):
            continue
        if sym and px > 0:
            out[sym] = px
    return out


def _tickers_lineal_publicos() -> dict[str, float]:
    return _tickers_publicos(mercado="linear")


def _ticker_publico(symbol: str, mercado: str | None = None) -> float:
    u = str(symbol or "").strip().upper()
    if not u:
        return 0.0
    if beru_mar.es_okx():
        act = u[:-4] if u.endswith("USDT") else u
        inst = beru_mar.activo_a_inst_id(act)
        url = f"{_host_publico()}/api/v5/market/ticker?instId={inst}"
        try:
            payload = _get_json_publico(url)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return 0.0
        lst = list(payload.get("data") or [])
        if not lst or not isinstance(lst[0], dict):
            return 0.0
        try:
            px = float(lst[0].get("last") or 0)
        except (TypeError, ValueError):
            return 0.0
        return px if px > 0 else 0.0
    cat = _category_rest(mercado)
    url = f"{_host_publico()}/v5/market/tickers?category={cat}&symbol={u}"
    try:
        payload = _get_json_publico(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return 0.0
    lst = ((payload.get("result") or {}).get("list") or [])
    if not lst or not isinstance(lst[0], dict):
        return 0.0
    try:
        px = float(lst[0].get("lastPrice") or 0)
    except (TypeError, ValueError):
        return 0.0
    return px if px > 0 else 0.0


def _ticker_lineal_publico(symbol: str) -> float:
    return _ticker_publico(symbol, mercado="linear")


def inyectar_precios_rest(
    bridge,
    tank,
    activos: list[str],
    *,
    latencia_ms: float = 80.0,
    mercado: str | None = None,
) -> dict[str, float]:
    """Pide tickers lastPrice públicos y los escribe en Tank.

    ``bridge`` queda por firma (rituales); la sesión de combate no se usa.
    """
    _ = bridge
    m = mercado_norm(mercado)
    out: dict[str, float] = {}
    if tank is None:
        return out
    nodos = list(getattr(tank, "nodos", None) or [])
    if not nodos:
        return out

    mapa = _tickers_publicos(m)
    for act in activos:
        u = str(act or "").strip().upper()
        if not u:
            continue
        sym = _symbol_rest(u, m)
        px = float(mapa.get(sym) or 0)
        if px <= 0:
            px = _ticker_publico(sym, m)
        if px <= 0:
            continue
        frente = f"{u}{_claves(m)[0]}"
        out[u] = px
        for n in nodos:
            try:
                n.inyectar_verdad_real(frente, px, float(latencia_ms))
                if str(getattr(n, "estado_foco", "") or "") in ("CONGELADO", "ROJO", ""):
                    n.estado_foco = "AMARILLO"
            except Exception:
                pass
        if hasattr(tank, "registrar_print_lineal"):
            try:
                tank.registrar_print_lineal(frente, px, fuente_ws=False)
            except Exception:
                pass
    return out


def resumen_inyeccion(
    precios: dict[str, float], mercado: str | None = None,
) -> dict[str, Any]:
    m = mercado_norm(mercado)
    return {
        "ts": time.time(),
        "n": len(precios),
        "precios": dict(precios),
        "fuente": f"rest_last_{m}",
        "mercado": m,
    }
