"""Perfiles multietiqueta Kaiser — corto (3d), mediano (1m), largo (1a)."""
from __future__ import annotations

import statistics
import time
from typing import Any

import core.config as config
from core.kaiser_samples import load_samples

PLAZOS = {
    "corto": 3 * 86400,
    "mediano": 30 * 86400,
    "largo": 365 * 86400,
}


def _umbral_evento() -> float:
    return getattr(config, "KAISER_EVENT_UMBRAL_PCT", 0.5)


def _ventana_reversion_s() -> float:
    return getattr(config, "KAISER_REVERSION_WINDOW_S", 900)


def _reversion_rates(samples: list[dict], umbral: float) -> dict[str, Any]:
    """Tras cruzar umbral, ¿vuelve a la mitad del umbral en ventana temporal?"""
    if len(samples) < 10:
        return {"long_revert_rate": None, "short_revert_rate": None, "long_events": 0, "short_events": 0}

    rev_win = _ventana_reversion_s()
    long_ok, long_n = 0, 0
    short_ok, short_n = 0, 0
    i = 0
    while i < len(samples):
        s = float(samples[i].get("signed_pct", 0))
        ts0 = float(samples[i].get("ts", 0))
        if s <= -umbral:
            long_n += 1
            if _revirtio(samples, i, ts0, rev_win, umbral):
                long_ok += 1
        elif s >= umbral:
            short_n += 1
            if _revirtio(samples, i, ts0, rev_win, umbral):
                short_ok += 1
        i += 1

    def rate(ok, n):
        return round(ok / n, 4) if n > 0 else None

    return {
        "long_revert_rate": rate(long_ok, long_n),
        "short_revert_rate": rate(short_ok, short_n),
        "long_events": long_n,
        "short_events": short_n,
    }


def _revirtio(samples: list[dict], idx: int, ts0: float, rev_win: float, umbral: float) -> bool:
    meta = umbral * 0.5
    for j in range(idx + 1, len(samples)):
        tsj = float(samples[j].get("ts", 0))
        if tsj - ts0 > rev_win:
            break
        if abs(float(samples[j].get("signed_pct", 0))) <= meta:
            return True
    return False


def _etiquetas(metricas: dict) -> list[str]:
    tags: list[str] = []
    n = metricas.get("n_muestras", 0)
    min_n = getattr(config, "KAISER_PERFIL_MIN_MUESTRAS", 20)
    if n < min_n:
        tags.append("DATOS_INSUFICIENTES")
        return tags

    umbral = _umbral_evento()
    pct_above = metricas.get("pct_tiempo_sobre_umbral", 0)
    if pct_above > 0.35:
        tags.append("RUIDOSO")
    elif pct_above < 0.05:
        tags.append("EVENTOS_RAROS")

    lr = metricas.get("long_revert_rate")
    sr = metricas.get("short_revert_rate")
    le = metricas.get("long_events", 0)
    se = metricas.get("short_events", 0)

    if lr is not None and le >= 3 and lr >= 0.55:
        tags.append("LONG_FRIENDLY")
    if sr is not None and se >= 3 and sr < 0.45:
        tags.append("SHORT_HUMO")
    if sr is not None and se >= 3 and sr >= 0.55:
        tags.append("SHORT_FRIENDLY")
    if lr is not None and le >= 3 and lr < 0.45:
        tags.append("LONG_HUMO")

    mean_abs = metricas.get("mean_abs_pct", 0)
    if mean_abs >= umbral * 1.5 and pct_above > 0.2:
        tags.append("DESVIO_PERSISTENTE")
    elif lr is not None and sr is not None and (lr + sr) / 2 >= 0.5:
        tags.append("REVIERTE_RAPIDO")

    ms = metricas.get("mean_signed_pct", 0)
    if ms <= -umbral * 0.3:
        tags.append("TENDENCIA_BARATO")
    elif ms >= umbral * 0.3:
        tags.append("TENDENCIA_CARO")

    if not tags:
        tags.append("NEUTRO")
    return tags


def calcular_metricas(samples: list[dict]) -> dict[str, Any]:
    if not samples:
        return {"n_muestras": 0}

    umbral = _umbral_evento()
    abs_vals = [float(s.get("abs_pct", 0)) for s in samples]
    signed_vals = [float(s.get("signed_pct", 0)) for s in samples]
    above = sum(1 for a in abs_vals if a >= umbral)

    rev = _reversion_rates(samples, umbral)
    p90 = statistics.quantiles(abs_vals, n=10)[8] if len(abs_vals) >= 10 else max(abs_vals)

    return {
        "n_muestras": len(samples),
        "pct_tiempo_sobre_umbral": round(above / len(samples), 4),
        "mean_abs_pct": round(statistics.mean(abs_vals), 4),
        "p90_abs_pct": round(p90, 4),
        "mean_signed_pct": round(statistics.mean(signed_vals), 4),
        **rev,
    }


def perfil_par(base: str, edge: str = "perp_vs_index") -> dict[str, Any]:
    """Multietiqueta corto / mediano / largo vs precio global (índice)."""
    ahora = time.time()
    plazos_out: dict[str, Any] = {}
    for nombre, segundos in PLAZOS.items():
        since = ahora - segundos
        samples = load_samples(base, edge, since_ts=since)
        metricas = calcular_metricas(samples)
        plazos_out[nombre] = {
            "ventana_dias": round(segundos / 86400, 1),
            "metricas": metricas,
            "etiquetas": _etiquetas(metricas),
        }
    return {
        "base": base.upper(),
        "edge": edge,
        "par": f"{base.upper()}USDT perp vs ref global (index)",
        "plazos": plazos_out,
        "etiquetas_resumen": _fusionar_etiquetas(plazos_out),
    }


def _fusionar_etiquetas(plazos: dict) -> list[str]:
    """Etiquetas que se repiten en 2+ plazos o críticas en largo."""
    counts: dict[str, int] = {}
    for p in plazos.values():
        for t in p.get("etiquetas", []):
            if t == "DATOS_INSUFICIENTES":
                continue
            counts[t] = counts.get(t, 0) + 1
    largo = plazos.get("largo", {}).get("etiquetas", [])
    out = [t for t, c in counts.items() if c >= 2]
    for t in largo:
        if t in ("LONG_FRIENDLY", "SHORT_HUMO", "DESVIO_PERSISTENTE") and t not in out:
            out.append(t)
    return out or ["SIN_CONSENSO"]


def perfil_arista(base: str, edge: str) -> dict[str, Any]:
    return perfil_par(base, edge)


def perfiles_para_bases(bases: list[str], edges: list[str] | None = None) -> dict[str, dict]:
    edges = edges or ["perp_vs_index"]
    out: dict[str, dict] = {}
    for base in bases:
        out[base.upper()] = {}
        for edge in edges:
            out[base.upper()][edge] = perfil_par(base, edge)
    return out
