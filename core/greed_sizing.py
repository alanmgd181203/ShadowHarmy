"""
Greed — tamaño de mordida desde indicadores Kaiser + techo Ancla/margen.
Doctrina: calor modula %; máx 1% equity en margen por misión; huérfana sin perfil ≤30%.
"""
from __future__ import annotations

from typing import Any

import core.config as config


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def es_huerfana(base: str) -> bool:
    b = base.upper()
    huerf = [str(x).upper() for x in (getattr(config, "ACTIVOS_HUERFANOS", []) or [])]
    return b in huerf and b not in getattr(config, "ACTIVOS_PENTIVERSO", ())


def apalancamiento_frente(frente: str) -> float:
    mp = getattr(config, "GREED_LEVERAGE_BY_FRENTE", {}) or {}
    default = float(getattr(config, "GREED_LEVERAGE_DEFAULT", 10.0))
    spot_default = float(getattr(config, "GREED_LEVERAGE_SPOT", 1.0))
    f = str(frente)
    if f in mp:
        return float(mp[f])
    if "_SPOT" in f:
        return spot_default
    return default


def apalancamiento_ruta(frentes: list[str]) -> float:
    if not frentes:
        return float(getattr(config, "GREED_LEVERAGE_DEFAULT", 10.0))
    return min(apalancamiento_frente(f) for f in frentes)


def margen_libre_usd(equity: float, margen_ocupado_pct: float) -> float:
    libre = max(0.0, 100.0 - float(margen_ocupado_pct)) / 100.0
    return equity * libre


def cap_notional_riesgo(
    equity: float,
    leverage: float,
    riesgo_pct: float | None = None,
) -> float:
    """Máx notional: riesgo_pct equity como margen × apalancamiento."""
    pct = riesgo_pct if riesgo_pct is not None else float(
        getattr(config, "GREED_RIESGO_MAX_PCT_CUENTA", 0.01),
    )
    return equity * pct * max(leverage, 1.0)


def cap_notional_1pct_riesgo(equity: float, leverage: float) -> float:
    """Máx notional: 1% equity como margen × apalancamiento."""
    return cap_notional_riesgo(equity, leverage)


def techo_real_usd(
    op: dict,
    *,
    equity: float,
    margen_ocupado_pct: float,
    frentes: list[str] | None = None,
) -> dict[str, Any]:
    """min(Ancla, margen libre × lev, cap 1% cuenta × lev)."""
    max_ancla = float(op.get("entrada_maxima_usd") or 0)
    frentes = frentes or []
    for leg in op.get("piernas") or []:
        f = leg.get("frente")
        if f:
            frentes.append(str(f))
    todos = (op.get("frentes") or {}).get("todos") or []
    for f in todos:
        frentes.append(str(f))
    fc = (op.get("frentes") or {}).get("compra")
    fv = (op.get("frentes") or {}).get("venta")
    if fc:
        frentes = list(dict.fromkeys([*frentes, str(fc)]))
    if fv and fv != fc:
        frentes.append(str(fv))
    frentes = list(dict.fromkeys(frentes))
    lev = apalancamiento_ruta(frentes)
    cap_margen = margen_libre_usd(equity, margen_ocupado_pct) * lev
    cap_1pct = cap_notional_1pct_riesgo(equity, lev)
    techo = min(max_ancla, cap_margen, cap_1pct) if max_ancla > 0 else 0.0
    return {
        "techo_real_usd": round(max(0.0, techo), 2),
        "max_ancla_usd": round(max_ancla, 2),
        "cap_margen_usd": round(cap_margen, 2),
        "cap_1pct_usd": round(cap_1pct, 2),
        "apalancamiento": lev,
        "equity_usd": round(equity, 2),
    }


def _tags_score(tags: list[str], favorable_long: bool) -> float:
    if not tags:
        return 0.5
    if "DATOS_INSUFICIENTES" in tags:
        return 0.0
    if "SIN_CONSENSO" in tags:
        return 0.4
    score = 0.55
    if favorable_long:
        if "LONG_FRIENDLY" in tags or "TENDENCIA_BARATO" in tags:
            score += 0.2
        if "SHORT_HUMO" in tags:
            score += 0.1
        if "LONG_HUMO" in tags or "TENDENCIA_CARO" in tags:
            score -= 0.15
    else:
        if "SHORT_FRIENDLY" in tags or "TENDENCIA_CARO" in tags:
            score += 0.2
        if "LONG_HUMO" in tags:
            score += 0.1
        if "SHORT_HUMO" in tags or "TENDENCIA_BARATO" in tags:
            score -= 0.15
    if "REVIERTE_RAPIDO" in tags:
        score += 0.1
    if "DESVIO_PERSISTENTE" in tags:
        score -= 0.15
    if "RUIDOSO" in tags:
        score -= 0.1
    if "EVENTOS_RAROS" in tags:
        score -= 0.05
    return _clamp(score, 0.05, 0.95)


def _calor_plazo(plazo: dict, favorable_long: bool) -> float | None:
    tags = plazo.get("etiquetas") or []
    if "DATOS_INSUFICIENTES" in tags:
        return None
    m = plazo.get("metricas") or {}
    ms = float(m.get("mean_signed_pct") or 0)
    score = 0.5
    umbral = float(getattr(config, "KAISER_EVENT_UMBRAL_PCT", 0.5)) * 0.3
    if favorable_long:
        if ms <= -umbral:
            score = 0.65 + min(0.3, abs(ms) / 2.0)
        elif ms >= umbral:
            score = 0.35 - min(0.2, ms / 3.0)
    else:
        if ms >= umbral:
            score = 0.65 + min(0.3, ms / 2.0)
        elif ms <= -umbral:
            score = 0.35 - min(0.2, abs(ms) / 3.0)
    score = _tags_score(tags, favorable_long) * 0.4 + score * 0.6
    return _clamp(score, 0.0, 1.0)


def calor_direccional(perfil_edge: dict | None, favorable_long: bool) -> float:
    """0..1 — mediano manda; corto/largo acompañan."""
    if not perfil_edge:
        return 0.5
    plazos = perfil_edge.get("plazos") or {}
    pesos = {"mediano": 0.50, "corto": 0.30, "largo": 0.20}
    total_w = 0.0
    acc = 0.0
    for nombre, w in pesos.items():
        c = _calor_plazo(plazos.get(nombre) or {}, favorable_long)
        if c is None:
            continue
        acc += c * w
        total_w += w
    if total_w <= 0:
        return 0.5
    return _clamp(acc / total_w, 0.0, 1.0)


def consenso_plazos(perfil_edge: dict | None) -> float:
    if not perfil_edge:
        return 0.5
    plazos = perfil_edge.get("plazos") or {}
    med = (plazos.get("mediano") or {}).get("etiquetas") or []
    cor = (plazos.get("corto") or {}).get("etiquetas") or []
    if "DATOS_INSUFICIENTES" in med:
        return 0.0
    med_set = {t for t in med if t not in ("NEUTRO", "DATOS_INSUFICIENTES")}
    cor_set = {t for t in cor if t not in ("NEUTRO", "DATOS_INSUFICIENTES")}
    if not med_set:
        return 0.45
    overlap = len(med_set & cor_set)
    if overlap >= 2 or (overlap >= 1 and len(med_set) <= 2):
        return 0.8
    if cor_set and not (med_set & cor_set):
        return 0.35
    return 0.6


def score_calidad_ruta(
    op: dict,
    ruta_idonea: dict | None,
) -> float:
    neto_op = float(op.get("regalo_neto_pct_est") or 0)
    if not ruta_idonea:
        return 0.7 if neto_op > 0 else 0.3
    if ruta_idonea.get("arista_directa"):
        return 0.75
    neto_r = float(ruta_idonea.get("regalo_neto_pct") or neto_op)
    if neto_r >= neto_op * 1.05:
        return 0.9
    if neto_r >= neto_op * 0.85:
        return 0.7
    if neto_r > 0:
        return 0.45
    return 0.2


def score_clima(
    *,
    tank_semaforo: str,
    pipeline_ms: float | None,
) -> float:
    if tank_semaforo == "ROJO":
        return 0.0
    score = 1.0
    if tank_semaforo == "AMARILLO":
        score *= 0.65
    pmax = float(getattr(config, "PIPELINE_MAX_MS", 500))
    if pipeline_ms is not None and pipeline_ms > pmax * 0.7:
        score *= 0.75
    return _clamp(score, 0.0, 1.0)


def score_manto(margen_ocupado_pct: float) -> float:
    """Calor Greed vs margen — alineado 21 §A (piso 85, ideal 90)."""
    m = float(margen_ocupado_pct)
    ley = float(getattr(config, "MURO_LEY_MARCIAL", 95.0))
    piso = float(getattr(config, "RANGO_PISO_IDEAL", 85.0))
    objetivo = float(getattr(config, "RANGO_OBJETIVO_MARGEN", 90.0))
    if m >= ley:
        return 0.0
    if m >= objetivo:
        return 1.0
    if m >= piso:
        return 0.85
    if m >= float(getattr(config, "RANGO_EXPANSION_MIN", 80.0)):
        return 0.7
    return 1.0


def favorable_long_desde_op(op: dict) -> bool:
    """True si compramos el frente 'compra' (lado barato del spread)."""
    return True


def perfil_edge_para_op(perfiles: dict | None, base: str, tipo_spread: str) -> dict | None:
    if not perfiles:
        return None
    if str(tipo_spread).startswith("multicruce_"):
        tipo_spread = "usdt_vs_usdc"
    edges = perfiles.get(base.upper()) or {}
    return edges.get(tipo_spread) or edges.get("perp_vs_index")


def veto_perfil_mediano(perfil_edge: dict | None, base: str) -> tuple[bool, str]:
    if es_huerfana(base):
        return False, "HUERFANA_CAP"
    if not perfil_edge:
        return True, "SIN_PERFIL"
    med = ((perfil_edge.get("plazos") or {}).get("mediano") or {}).get("etiquetas") or []
    if "DATOS_INSUFICIENTES" in med:
        return True, "DATOS_INSUFICIENTES"
    return False, "OK"


def veto_humo_tres_plazos(perfil_edge: dict | None, favorable_long: bool) -> tuple[bool, str]:
    if not perfil_edge:
        return False, "OK"
    plazos = perfil_edge.get("plazos") or {}
    humo_tag = "LONG_HUMO" if favorable_long else "SHORT_HUMO"
    n = 0
    for p in plazos.values():
        if humo_tag in (p.get("etiquetas") or []):
            n += 1
    if n >= 3:
        return True, f"VETO_{humo_tag}_3PLAZOS"
    return False, "OK"


def calcular_confianza(
    op: dict,
    *,
    perfiles: dict | None = None,
    ruta_idonea: dict | None = None,
    tank_semaforo: str = "VERDE",
    pipeline_ms: float | None = None,
    margen_ocupado_pct: float = 0.0,
) -> dict[str, Any]:
    base = str(op.get("base", "")).upper()
    tipo = str(op.get("tipo_spread", ""))
    perfil = perfil_edge_para_op(perfiles, base, tipo)
    fav_long = favorable_long_desde_op(op)

    calor = calor_direccional(perfil, fav_long)
    tags = _tags_score((perfil or {}).get("etiquetas_resumen") or [], fav_long)
    plazos = consenso_plazos(perfil)
    ruta = score_calidad_ruta(op, ruta_idonea)
    clima = score_clima(tank_semaforo=tank_semaforo, pipeline_ms=pipeline_ms)
    manto = score_manto(margen_ocupado_pct)

    w = getattr(config, "GREED_PESOS_INDICADORES", None) or {
        "calor": 0.25, "tags": 0.25, "plazos": 0.20,
        "ruta": 0.15, "clima": 0.10, "manto": 0.05,
    }
    confianza = (
        w.get("calor", 0.25) * calor
        + w.get("tags", 0.25) * tags
        + w.get("plazos", 0.20) * plazos
        + w.get("ruta", 0.15) * ruta
        + w.get("clima", 0.10) * clima
        + w.get("manto", 0.05) * manto
    )
    # Calor modula el % final (doctrina Monarca)
    mod = float(getattr(config, "GREED_CALOR_MODULO", 0.5))
    fraccion = confianza * (mod + (1.0 - mod) * calor)
    f_min = float(getattr(config, "GREED_FRACCION_MIN", 0.05))
    f_max = float(getattr(config, "GREED_FRACCION_MAX", 0.85))
    fraccion = _clamp(fraccion, f_min, f_max)

    sin_perfil = not perfil or "DATOS_INSUFICIENTES" in (
        (perfil.get("etiquetas_resumen") or [])
    )
    if es_huerfana(base) and sin_perfil:
        cap_h = float(getattr(config, "GREED_HUERFANA_SIN_PERFIL_FRACCION_MAX", 0.30))
        fraccion = min(fraccion, cap_h)

    return {
        "confianza": round(confianza, 4),
        "fraccion": round(fraccion, 4),
        "calor": round(calor, 4),
        "scores": {
            "tags": round(tags, 4),
            "plazos": round(plazos, 4),
            "ruta": round(ruta, 4),
            "clima": round(clima, 4),
            "manto": round(manto, 4),
        },
        "perfil_edge": tipo,
        "sin_perfil": sin_perfil,
        "huerfana": es_huerfana(base),
    }


def calcular_mordida(
    op: dict,
    *,
    equity: float,
    margen_ocupado_pct: float,
    perfiles: dict | None = None,
    ruta_idonea: dict | None = None,
    tank_semaforo: str = "VERDE",
    pipeline_ms: float | None = None,
    masa_autorizada: float | None = None,
) -> dict[str, Any]:
    """Mordida USD notional para una oportunidad Kaiser."""
    from core import ancla

    techo_info = techo_real_usd(
        op, equity=equity, margen_ocupado_pct=margen_ocupado_pct,
    )
    techo = float(techo_info["techo_real_usd"])
    conf = calcular_confianza(
        op,
        perfiles=perfiles,
        ruta_idonea=ruta_idonea,
        tank_semaforo=tank_semaforo,
        pipeline_ms=pipeline_ms,
        margen_ocupado_pct=margen_ocupado_pct,
    )
    fraccion = float(conf["fraccion"])
    mordida = techo * fraccion
    min_ord = float(op.get("min_order_usd_cruce") or ancla.min_order_usd_frente(
        (op.get("frentes") or {}).get("compra", ""),
    ))
    if masa_autorizada is not None:
        mordida = min(mordida, float(masa_autorizada))
    mordida = round(max(0.0, mordida), 2)
    ok = mordida >= min_ord and techo >= min_ord
    lev = float(techo_info["apalancamiento"])
    margen_riesgo = mordida / lev if lev > 0 else mordida
    cap_margen = equity * float(getattr(config, "GREED_RIESGO_MAX_PCT_CUENTA", 0.01))
    return {
        "ok": ok,
        "mordida_usd": mordida,
        "techo_real_usd": techo,
        "min_order_usd": min_ord,
        "margen_riesgo_est_usd": round(margen_riesgo, 4),
        "cap_margen_riesgo_usd": round(cap_margen, 4),
        **conf,
        **techo_info,
        "motivo": None if ok else (
            "BAJO_MIN_ORDEN" if techo < min_ord else "MORDIDA_CERO"
        ),
    }
