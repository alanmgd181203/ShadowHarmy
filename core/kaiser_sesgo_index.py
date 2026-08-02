"""Kaiser — sesgo estructural vs índice Bybit (checkpoint 3.8.P4/P5).

Convención: signed_pct = (precio − index) / index × 100
  positivo = instrumento caro vs índice
  negativo = barato vs índice

El cero estructural = mediana histórica del signed en plazos.
Oportunidad ≠ gap eterno; clima normal = cerca del cero.
"""
from __future__ import annotations

import statistics
import time
from typing import Any

import core.config as config
from core.kaiser_samples import load_samples

# Día + plazos de perfil Kaiser
PLAZOS_SESGO = {
    "dia": 86400,
    "corto": 3 * 86400,
    "mediano": 30 * 86400,
    "largo": 365 * 86400,
}

# Mar → edge de muestras (nombre digest amigable)
MARES_EDGE = {
    "lineal": "perp_vs_index",
    "spot": "spot_vs_index",
    "inverso": "inverse_vs_index",
}

MAR_LABEL = {
    "lineal": "perp/lineal USDT",
    "spot": "spot USDT",
    "inverso": "inverse USD",
}


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _min_muestras() -> int:
    return int(getattr(config, "KAISER_SESGO_MIN_MUESTRAS", 15) or 15)


def _epsilon_clima_pct() -> float:
    """¿Qué tan cerca del cero cuenta como clima normal? (puntos % absolutos)."""
    return float(getattr(config, "KAISER_SESGO_CLIMA_EPS_PCT", 0.05) or 0.05)


def metricas_sesgo(samples: list[dict]) -> dict[str, Any]:
    if not samples:
        return {"n": 0, "mediana_pct": None, "media_pct": None}
    vals = [_f(s.get("signed_pct")) for s in samples]
    if len(vals) == 1:
        med = vals[0]
    else:
        med = statistics.median(vals)
    return {
        "n": len(vals),
        "mediana_pct": round(med, 6),
        "media_pct": round(statistics.mean(vals), 6),
        "p10_pct": round(statistics.quantiles(vals, n=10)[0], 6) if len(vals) >= 10 else None,
        "p90_pct": round(statistics.quantiles(vals, n=10)[8], 6) if len(vals) >= 10 else None,
    }


def etiquetas_sesgo(cero_pct: float | None, n: int) -> list[str]:
    tags: list[str] = []
    if n < _min_muestras() or cero_pct is None:
        tags.append("DATOS_INSUFICIENTES")
        return tags
    eps = 0.02  # casi pegado al índice
    if cero_pct >= eps:
        tags.append("SUELE_CARO_VS_INDEX")
    elif cero_pct <= -eps:
        tags.append("SUELE_BARATO_VS_INDEX")
    else:
        tags.append("SUELE_PEGADO_INDEX")
    if abs(cero_pct) >= 0.15:
        tags.append("SESGO_FUERTE")
    else:
        tags.append("SESGO_LEVE")
    tags.append("CERO_ESTRUCTURAL")
    return tags


def perfil_sesgo_edge(base: str, edge: str) -> dict[str, Any]:
    """Histórico multiplazo para una arista vs índice."""
    ahora = time.time()
    plazos: dict[str, Any] = {}
    for nombre, seg in PLAZOS_SESGO.items():
        samples = load_samples(base, edge, since_ts=ahora - seg)
        m = metricas_sesgo(samples)
        plazos[nombre] = {
            "ventana_dias": round(seg / 86400, 2),
            **m,
            "etiquetas": etiquetas_sesgo(m.get("mediana_pct"), int(m.get("n") or 0)),
        }

    # Cero preferido: mediano si hay datos; si no corto; si no dia
    cero = None
    fuente_cero = None
    for pref in ("mediano", "corto", "dia", "largo"):
        m = plazos.get(pref) or {}
        if m.get("mediana_pct") is not None and int(m.get("n") or 0) >= _min_muestras():
            cero = float(m["mediana_pct"])
            fuente_cero = pref
            break
    if cero is None:
        for pref in ("mediano", "corto", "dia", "largo"):
            m = plazos.get(pref) or {}
            if m.get("mediana_pct") is not None and int(m.get("n") or 0) >= 3:
                cero = float(m["mediana_pct"])
                fuente_cero = pref
                break

    return {
        "base": base.upper(),
        "edge": edge,
        "cero_estructural_pct": round(cero, 6) if cero is not None else None,
        "fuente_cero": fuente_cero,
        "etiquetas": etiquetas_sesgo(cero, int((plazos.get(fuente_cero) or {}).get("n") or 0)),
        "plazos": plazos,
    }


def _lider_para_sesgo(tank):
    """Mismo criterio que Tank.vision_especulativa: verde/amarillo, si no el nodo más fresco.

    El digest de sesgo es lectura (sin disparos). Si el semáforo está ROJO por latencia
    pero aún hay precios/index en memoria, el clima vivo debe seguir publicándose.
    """
    if not tank:
        return None
    lider = tank._obtener_lider_verde()
    if lider:
        return lider
    nodos = getattr(tank, "nodos", None) or []
    if not nodos:
        return None
    return max(nodos, key=lambda n: getattr(n, "ultima_actualizacion", 0.0) or 0.0)


def _precio_e_index(tank, base: str, mar: str) -> tuple[float | None, float | None]:
    lider = _lider_para_sesgo(tank)
    if not lider:
        return None, None
    px = lider.precios_con_reflejo() if hasattr(lider, "precios_con_reflejo") else (lider.precios or {})
    idx_map = lider.index_prices or {}
    bu = base.upper()
    idx = _f(idx_map.get(f"{bu}USDT_LINEAL"))
    if idx <= 0:
        # a veces el index llegó en otro frente
        for k, v in idx_map.items():
            if k.startswith(bu) and _f(v) > 0:
                idx = _f(v)
                break
    if mar == "lineal":
        p = _f(px.get(f"{bu}USDT_LINEAL"))
    elif mar == "spot":
        p = _f(px.get(f"{bu}USDT_SPOT"))
    elif mar == "inverso":
        p = _f(px.get(f"{bu}USD_INVERSE"))
    else:
        p = 0.0
    if p <= 0 or idx <= 0:
        return (p if p > 0 else None), (idx if idx > 0 else None)
    return p, idx


def vivo_vs_index(tank, base: str, mar: str) -> dict[str, Any]:
    p, idx = _precio_e_index(tank, base, mar)
    if p is None or idx is None:
        return {"ok": False, "signed_pct": None, "precio": p, "index": idx}
    signed = (p - idx) / idx * 100.0
    return {
        "ok": True,
        "signed_pct": round(signed, 6),
        "precio": round(p, 8),
        "index": round(idx, 8),
    }


def clima_vs_cero(vivo_pct: float | None, cero_pct: float | None) -> dict[str, Any]:
    if vivo_pct is None or cero_pct is None:
        return {"estado": "desconocido", "delta_vs_cero_pct": None}
    delta = vivo_pct - cero_pct
    eps = _epsilon_clima_pct()
    if abs(delta) <= eps:
        estado = "normal"
    elif abs(delta) <= eps * 3:
        estado = "tenso"
    else:
        estado = "anomalia"
    return {
        "estado": estado,
        "delta_vs_cero_pct": round(delta, 6),
        "epsilon_pct": eps,
    }


def snapshot_sesgo_estructural(tank, bases: list[str] | None = None) -> dict[str, Any]:
    """Bloque para digest Kaiser — sin disparos."""
    if bases is None:
        bases = list(getattr(config, "ACTIVOS_PENTIVERSO", []) or [])[:12]
        for b in getattr(config, "ACTIVOS_TRINIDAD", []) or []:
            if b not in bases:
                bases.append(b)
    bases = [str(b).upper() for b in bases if b]

    por_base: dict[str, Any] = {}
    for base in bases:
        mares: dict[str, Any] = {}
        for mar, edge in MARES_EDGE.items():
            hist = perfil_sesgo_edge(base, edge)
            vivo = vivo_vs_index(tank, base, mar)
            clima = clima_vs_cero(vivo.get("signed_pct"), hist.get("cero_estructural_pct"))
            mares[mar] = {
                "label": MAR_LABEL[mar],
                "edge": edge,
                "cero_estructural_pct": hist.get("cero_estructural_pct"),
                "fuente_cero": hist.get("fuente_cero"),
                "etiquetas": hist.get("etiquetas"),
                "plazos": hist.get("plazos"),
                "vivo": vivo,
                "clima": clima,
            }
        por_base[base] = {
            "mares": mares,
            "nota": (
                "Cero = mediana histórica (precio−index)/index×100. "
                "Clima normal = vivo cerca del cero (no del 0 absoluto)."
            ),
        }

    return {
        "doctrina": "CHECKPOINT_KAISER_INDICE_SESGO",
        "ts": time.time(),
        "convencion": "signed_pct=(precio-index)/index*100; + = caro vs índice",
        "ancla_absoluta": "indexPrice Bybit",
        "bases": por_base,
        "n_bases": len(por_base),
    }
