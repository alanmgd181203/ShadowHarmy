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

# Claves de frente que Beru rango PUEDE usar como ojo
_CLAVES_LINEAL = ("USDT_LINEAL",)


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
    if bool(getattr(config, "TESTNET", False)):
        return "https://api-testnet.bybit.com"
    return "https://api.bybit.com"


def claves_lineal(activo: str) -> tuple[str, ...]:
    u = str(activo or "").strip().upper()
    if not u:
        return ()
    return tuple(f"{u}{suf}" for suf in _CLAVES_LINEAL)


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


def last_lineal_desde_precios(precios: dict | None, activo: str) -> float:
    """Solo last lineal USDT. 0 si no hay — no inventar con spot/inverso."""
    if not precios:
        return 0.0
    for clave in claves_lineal(activo):
        try:
            px = float(precios.get(clave) or 0)
        except (TypeError, ValueError):
            px = 0.0
        if px > 0:
            return px
    return 0.0


def last_lineal_desde_tank(tank, activo: str) -> float:
    """Lee last lineal del líder Tank; 0 si ciego (sin fallback spot)."""
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
            return last_lineal_desde_precios(precios, act)
        if hasattr(lider, "precios_con_reflejo"):
            precios = lider.precios_con_reflejo() or {}
        else:
            precios = getattr(lider, "precios", None) or {}
        return last_lineal_desde_precios(precios, act)
    except Exception:
        return 0.0


def _latido_vacio(last: float = 0.0) -> dict[str, Any]:
    px = float(last or 0)
    return {"last": px, "high": px, "low": px, "prints": []}


def latido_lineal_desde_tank(tank, activo: str) -> dict[str, Any]:
    """Last + extremos + tratos del latido lineal. Limpia el tramo."""
    last = last_lineal_desde_tank(tank, activo)
    act = str(activo or "").strip().upper()
    if not act or tank is None:
        return _latido_vacio(last)
    merged = _latido_vacio(last)
    consumir = getattr(tank, "consumir_latido_lineal", None)
    if not callable(consumir):
        return merged
    for clave in claves_lineal(act):
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


def _get_json_publico(url: str, timeout: float = 8.0) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": "ShadowHarmy/beru-rango-ojos"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw or "{}")
    return data if isinstance(data, dict) else {}


def _tickers_lineal_publicos() -> dict[str, float]:
    """lastPrice lineal público — no usa la boca de combate."""
    url = f"{_host_publico()}/v5/market/tickers?category=linear"
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


def _ticker_lineal_publico(symbol: str) -> float:
    u = str(symbol or "").strip().upper()
    if not u:
        return 0.0
    url = f"{_host_publico()}/v5/market/tickers?category=linear&symbol={u}"
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


def inyectar_precios_rest(
    bridge,
    tank,
    activos: list[str],
    *,
    latencia_ms: float = 80.0,
) -> dict[str, float]:
    """Pide tickers lineal lastPrice públicos y los escribe en Tank.

    ``bridge`` queda por firma (rituales); la sesión de combate no se usa.
    """
    _ = bridge
    out: dict[str, float] = {}
    if tank is None:
        return out
    nodos = list(getattr(tank, "nodos", None) or [])
    if not nodos:
        return out

    mapa = _tickers_lineal_publicos()
    for act in activos:
        u = str(act or "").strip().upper()
        if not u:
            continue
        sym = f"{u}USDT"
        px = float(mapa.get(sym) or 0)
        if px <= 0:
            px = _ticker_lineal_publico(sym)
        if px <= 0:
            continue
        frente = f"{u}USDT_LINEAL"
        out[u] = px
        for n in nodos:
            try:
                n.inyectar_verdad_real(frente, px, float(latencia_ms))
                # NO inyectar spot como respaldo (Beru rango ciego a spot)
                if str(getattr(n, "estado_foco", "") or "") in ("CONGELADO", "ROJO", ""):
                    n.estado_foco = "AMARILLO"
            except Exception:
                pass
        # Muleta también deja rastro en el vaso (sin marcar río WS vivo).
        if hasattr(tank, "registrar_print_lineal"):
            try:
                tank.registrar_print_lineal(frente, px, fuente_ws=False)
            except Exception:
                pass
    return out


def resumen_inyeccion(precios: dict[str, float]) -> dict[str, Any]:
    return {
        "ts": time.time(),
        "n": len(precios),
        "precios": dict(precios),
        "fuente": "rest_last_lineal",
    }
