"""Ojos Beru — solo last price spot (cirugía precisión 2026-08-13).

Beru es ciego a lineal, inverso, índice y orderbook como cerebro.
Tank puede seguir pidiendo eso para Igris/Kaiser; Beru solo lee …USDT_SPOT.
Muleta REST: ticker spot lastPrice cuando cae el WS.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config

# Claves de frente que Beru PUEDE usar como ojo
_CLAVES_SPOT = ("USDT_SPOT", "USDC_SPOT")


def rest_fallback_activo() -> bool:
    return bool(getattr(config, "BERU_OJOS_REST_FALLBACK", True))


def rest_intervalo_s() -> float:
    return float(getattr(config, "BERU_OJOS_REST_S", 10.0) or 10.0)


def claves_spot(activo: str) -> tuple[str, ...]:
    u = str(activo or "").strip().upper()
    if not u:
        return ()
    return tuple(f"{u}{suf}" for suf in _CLAVES_SPOT)


def last_spot_desde_precios(precios: dict | None, activo: str) -> float:
    """Solo last spot. 0 si no hay — no inventar con lineal/inverso."""
    if not precios:
        return 0.0
    for clave in claves_spot(activo):
        px = float(precios.get(clave) or 0)
        if px > 0:
            return px
    return 0.0


def last_spot_desde_tank(tank, activo: str) -> float:
    """Lee last spot del líder Tank; 0 si ciego (sin fallback perp)."""
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
                lider = max(nodos, key=lambda n: float(getattr(n, "ultima_actualizacion", 0) or 0))
        if not lider:
            return 0.0
        if hasattr(lider, "precios_con_reflejo"):
            precios = lider.precios_con_reflejo() or {}
        else:
            precios = getattr(lider, "precios", None) or {}
        return last_spot_desde_precios(precios, act)
    except Exception:
        return 0.0


def _ticker_spot_rest(session, symbol: str) -> float:
    """lastPrice spot vía REST; 0 si falla. No bid/ask como verdad primaria."""
    if not symbol:
        return 0.0
    sess = session
    if sess is None:
        try:
            from pybit.unified_trading import HTTP
            sess = HTTP(testnet=False)
        except Exception:
            return 0.0
    try:
        r = sess.get_tickers(category="spot", symbol=symbol)
        lst = ((r or {}).get("result") or {}).get("list") or []
        if not lst:
            return 0.0
        row = lst[0] if isinstance(lst[0], dict) else {}
        # Solo lastPrice — ojo sellado Monarca
        px = float(row.get("lastPrice") or 0)
        return px if px > 0 else 0.0
    except Exception:
        return 0.0


def inyectar_precios_rest(
    bridge,
    tank,
    activos: list[str],
    *,
    latencia_ms: float = 80.0,
) -> dict[str, float]:
    """Pide tickers spot lastPrice y los escribe en Tank — solo frentes SPOT."""
    sess = getattr(bridge, "session", None)
    out: dict[str, float] = {}
    if tank is None:
        return out
    nodos = list(getattr(tank, "nodos", None) or [])
    if not nodos:
        return out

    for act in activos:
        u = str(act or "").strip().upper()
        if not u:
            continue
        sym = f"{u}USDT"
        px = _ticker_spot_rest(sess, sym)
        if px <= 0:
            continue
        frente = f"{u}USDT_SPOT"
        out[u] = px
        for n in nodos:
            try:
                n.inyectar_verdad_real(frente, px, float(latencia_ms))
                # Cirugía: NO inyectar lineal como respaldo (Beru ciego a perp)
                if str(getattr(n, "estado_foco", "") or "") in ("CONGELADO", "ROJO", ""):
                    n.estado_foco = "AMARILLO"
            except Exception:
                pass
    return out


def resumen_inyeccion(precios: dict[str, float]) -> dict[str, Any]:
    return {
        "ts": time.time(),
        "n": len(precios),
        "precios": dict(precios),
        "fuente": "rest_last_spot",
    }
