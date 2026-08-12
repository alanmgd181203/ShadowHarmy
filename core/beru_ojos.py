"""Ojos Beru — muleta REST cuando el torrente WS muere.

Doctrina: NAV (bóveda) puede vivir y el WS morir. Beru fantasma / ensayo
necesita precio usable → consulta ticker spot y lo inyecta en Tank.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config


def rest_fallback_activo() -> bool:
    return bool(getattr(config, "BERU_OJOS_REST_FALLBACK", True))


def rest_intervalo_s() -> float:
    return float(getattr(config, "BERU_OJOS_REST_S", 10.0) or 10.0)


def _ticker_spot_rest(session, symbol: str) -> float:
    """lastPrice spot vía REST; 0 si falla."""
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
        for k in ("lastPrice", "bid1Price", "ask1Price"):
            px = float(row.get(k) or 0)
            if px > 0:
                return px
    except Exception:
        return 0.0
    return 0.0


def inyectar_precios_rest(
    bridge,
    tank,
    activos: list[str],
    *,
    latencia_ms: float = 80.0,
) -> dict[str, float]:
    """Pide tickers spot y los escribe en todos los nodos Tank.

    Devuelve mapa activo→precio (>0 solo los que llegaron).
    """
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
                # También lineal como respaldo de lectura Beru
                n.asegurar_frente(f"{u}USDT_LINEAL")
                if float(n.precios.get(f"{u}USDT_LINEAL") or 0) <= 0:
                    n.precios[f"{u}USDT_LINEAL"] = px
                # Evita quedarse etiquetado CONGELADO con update fresco
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
        "fuente": "rest_ticker_spot",
    }
