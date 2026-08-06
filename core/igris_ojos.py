"""Ojos frescos del manto Igris — edad de libro, stale, REST muleta.

Doctrina: libro viejo ≠ mercado vivo. Sin ojos frescos no hay manos.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core import mercado


def stale_s_max() -> float:
    return float(getattr(config, "IGRIS_LIBRO_STALE_S", 12.0) or 12.0)


def rest_cooldown_s() -> float:
    return float(getattr(config, "IGRIS_LIBRO_REST_COOLDOWN_S", 15.0) or 15.0)


def divergencia_max_pct() -> float:
    return float(getattr(config, "IGRIS_LIBRO_DIVERGENCIA_PCT", 0.35) or 0.35)


def rest_fallback_on() -> bool:
    return bool(getattr(config, "IGRIS_LIBRO_REST_FALLBACK", True))


def _libro_dict(tank, frente: str) -> dict[str, Any]:
    libros: dict = {}
    if hasattr(tank, "_obtener_lider_verde"):
        lider = tank._obtener_lider_verde()
        if lider is not None:
            libros = dict(getattr(lider, "libros", {}) or {})
        elif hasattr(tank, "nodos"):
            from core import ancla

            libros = ancla.libros_desde_lider(tank)
    if not libros:
        libros = getattr(tank, "libros", None) or {}
    return dict(libros.get(frente) or {})


def edad_libro_s(tank, frente: str, *, ahora: float | None = None) -> float | None:
    """Segundos desde última inyección WS/REST. None si nunca hubo snapshot."""
    ahora = ahora if ahora is not None else time.time()
    libro = _libro_dict(tank, frente)
    ts = float(libro.get("ts") or 0)
    if ts <= 0:
        return None
    return max(0.0, ahora - ts)


def meta_libro(tank, frente: str, *, ahora: float | None = None) -> dict[str, Any]:
    ahora = ahora if ahora is not None else time.time()
    libro = _libro_dict(tank, frente)
    ts = float(libro.get("ts") or 0)
    edad = (ahora - ts) if ts > 0 else None
    lim = stale_s_max()
    n_b = len(libro.get("bids") or [])
    n_a = len(libro.get("asks") or [])
    stale = ts <= 0 or edad is None or edad > lim or (n_b <= 0 and n_a <= 0)
    return {
        "frente": frente,
        "ts": ts,
        "edad_s": round(edad, 3) if edad is not None else None,
        "stale": stale,
        "stale_lim_s": lim,
        "n_bids": n_b,
        "n_asks": n_a,
    }


def frentes_stale(tank, frentes: list[str], *, ahora: float | None = None) -> list[dict[str, Any]]:
    out = []
    for f in frentes:
        m = meta_libro(tank, f, ahora=ahora)
        if m.get("stale"):
            out.append(m)
    return out


def _best_px(niveles: list, *, lado: str) -> float:
    for row in niveles or []:
        try:
            p, q = float(row[0]), float(row[1])
        except (IndexError, TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            return p
    return 0.0


def divergencia_libro_vs_ticker(tank, frente: str) -> dict[str, Any]:
    """Si libro y ticker divergen demasiado → ojos sospechosos."""
    from core import igris_despliegue as ides

    libro = _libro_dict(tank, frente)
    # Para long inverse usamos ask; short lineal bid — para sanity usamos mid libro
    bid = _best_px(libro.get("bids") or [], lado="bid")
    ask = _best_px(libro.get("asks") or [], lado="ask")
    if bid <= 0 and ask <= 0:
        return {"ok": True, "motivo": "sin_libro", "div_pct": None}
    mid = (bid + ask) / 2.0 if bid > 0 and ask > 0 else max(bid, ask)
    ticker = ides.precio_ticker_frente(tank, frente)
    if ticker <= 0 or mid <= 0:
        return {"ok": True, "motivo": "sin_ticker", "div_pct": None}
    div = abs(mid - ticker) / ticker * 100.0
    lim = divergencia_max_pct()
    return {
        "ok": div <= lim,
        "motivo": "ok" if div <= lim else "divergencia_ticker",
        "div_pct": round(div, 4),
        "lim_pct": lim,
        "mid_libro": mid,
        "ticker": ticker,
    }


def invalidar_libros_tank(tank, bases: list[str] | None = None) -> int:
    """Tirar fotos viejas (post-RECONEXIÓN). Cuenta frentes tocados."""
    bases_u = {str(b).upper() for b in (bases or []) if b}
    n = 0
    nodos = list(getattr(tank, "nodos", None) or [])
    targets = nodos if nodos else [tank]
    for nodo in targets:
        libros = getattr(nodo, "libros", None)
        if not isinstance(libros, dict):
            continue
        for frente in list(libros.keys()):
            if bases_u:
                act = mercado.activo_de_frente(frente)
                if act not in bases_u:
                    continue
            libros[frente] = {"bids": [], "asks": [], "ts": 0.0}
            n += 1
            if hasattr(nodo, "inyectar_muro"):
                try:
                    nodo.inyectar_muro(frente, 0.0, 0.0)
                except Exception:
                    pass
    return n


def _category_symbol(frente: str) -> tuple[str, str]:
    sym = mercado.frente_a_symbol(frente)
    cat = mercado.frente_a_category(frente)
    return cat, sym


def inyectar_libro_en_tank(tank, frente: str, bids: list, asks: list) -> None:
    nodos = list(getattr(tank, "nodos", None) or [])
    if nodos:
        for nodo in nodos:
            if hasattr(nodo, "inyectar_libro_snapshot"):
                nodo.inyectar_libro_snapshot(frente, bids, asks)
    elif hasattr(tank, "inyectar_libro_snapshot"):
        tank.inyectar_libro_snapshot(frente, bids, asks)


def refrescar_libro_rest(bridge, tank, frente: str) -> dict[str, Any]:
    """Muleta HTTP orderbook → snapshot en Tank. No es el camino noble; evita ceguera."""
    if not bridge or not getattr(bridge, "session", None):
        return {"ok": False, "motivo": "sin_sesion"}
    cat, sym = _category_symbol(frente)
    try:
        resp = bridge.session.get_orderbook(category=cat, symbol=sym, limit=50)
    except Exception as e:
        return {"ok": False, "motivo": f"exc:{e}"}
    if resp.get("retCode") != 0:
        return {"ok": False, "motivo": str(resp.get("retMsg") or "ret")}
    data = resp.get("result") or {}
    bids = data.get("b") or []
    asks = data.get("a") or []
    if not bids and not asks:
        return {"ok": False, "motivo": "libro_vacio_rest"}
    inyectar_libro_en_tank(tank, frente, bids, asks)
    return {
        "ok": True,
        "frente": frente,
        "symbol": sym,
        "n_bids": len(bids),
        "n_asks": len(asks),
        "fuente": "rest",
    }


def _cooldown_ok(tank, key: str, *, ahora: float) -> bool:
    store = getattr(tank, "_igris_ojos_rest_ts", None)
    if not isinstance(store, dict):
        store = {}
        setattr(tank, "_igris_ojos_rest_ts", store)
    last = float(store.get(key) or 0)
    if ahora - last < rest_cooldown_s():
        return False
    store[key] = ahora
    return True


async def asegurar_libros_frescos(
    tank,
    bridge,
    frentes: list[str],
    *,
    ahora: float | None = None,
    bases_invalidar: list[str] | None = None,
) -> dict[str, Any]:
    """
    Si algún libro está stale: intenta REST (cooldown).
    Retorna diagnóstico para Bellion / puerta.
    """
    ahora = ahora if ahora is not None else time.time()
    metas = [meta_libro(tank, f, ahora=ahora) for f in frentes]
    stale = [m for m in metas if m.get("stale")]
    divs = []
    for f in frentes:
        d = divergencia_libro_vs_ticker(tank, f)
        if not d.get("ok") and d.get("motivo") == "divergencia_ticker":
            divs.append({"frente": f, **d})

    rest_intentos: list[dict] = []
    if (stale or divs) and rest_fallback_on() and bridge:
        for f in frentes:
            need = any(m["frente"] == f for m in stale) or any(x["frente"] == f for x in divs)
            if not need:
                continue
            if not _cooldown_ok(tank, f, ahora=ahora):
                rest_intentos.append({"frente": f, "ok": False, "motivo": "cooldown"})
                continue
            rest_intentos.append(refrescar_libro_rest(bridge, tank, f))

    metas2 = [meta_libro(tank, f, ahora=time.time()) for f in frentes]
    still = [m for m in metas2 if m.get("stale")]
    # Re-check divergencia post-REST
    divs2 = []
    for f in frentes:
        d = divergencia_libro_vs_ticker(tank, f)
        if not d.get("ok") and d.get("motivo") == "divergencia_ticker":
            divs2.append({"frente": f, **d})

    ok = not still and not divs2
    return {
        "ok": ok,
        "metas": metas2,
        "stale": still,
        "divergencias": divs2,
        "rest": rest_intentos,
        "bases_invalidar": bases_invalidar or [],
    }
