"""Grafo metaverso — aristas precargadas y ranking de rutas de arbitraje."""
from __future__ import annotations

from typing import Any

import core.config as config

# Aristas estándar por activo (precargadas)
ARISTAS_TIPO = (
    "perp_vs_index",
    "spot_vs_perp",
    "lineal_vs_inverse",
    "usdt_vs_usdc",
    "spot_vs_index",
    "basis_fut_vs_perp",
)

RUTAS_PLANTILLA = (
    {
        "id": "stable_plus_perp",
        "nombre": "USDT↔USDC + spot↔perp",
        "aristas": ("usdt_vs_usdc", "spot_vs_perp"),
    },
    {
        "id": "lineal_inverse",
        "nombre": "Lineal↔inverse",
        "aristas": ("lineal_vs_inverse",),
    },
    {
        "id": "perp_index_directo",
        "nombre": "Perp vs índice",
        "aristas": ("perp_vs_index",),
    },
)

# Plantillas multicruce (filas tipo multicruce_Np en matriz)
RUTAS_MULTICRUCE_PLANTILLA = (
    {"id": "via_usdc", "nombre": "Base USDT ↔ USDC puente", "tipo_prefix": "multicruce_3p", "via": "USDC"},
    {"id": "via_mnt", "nombre": "Base USDT ↔ MNT puente", "tipo_prefix": "multicruce_3p", "via": "MNT"},
    {"id": "via_eur", "nombre": "Base USDT ↔ EUR puente", "tipo_prefix": "multicruce_4p", "via": "EUR"},
)


def frentes_metaverso(base: str) -> list[str]:
    b = base.upper()
    return [
        f"{b}USDT_LINEAL",
        f"{b}USDC_LINEAL",
        f"{b}USD_INVERSE",
        f"{b}USDT_SPOT",
        f"{b}USDC_SPOT",
    ]


def aristas_precargadas(base: str) -> list[dict]:
    b = base.upper()
    return [
        {"id": f"{b}:{t}", "base": b, "tipo": t, "edge": t}
        for t in ARISTAS_TIPO
    ]


def _slippage_estimado(base: str, tipo: str) -> float:
    b = base.upper()
    defaults = {
        "perp_vs_index": getattr(config, "KAISER_SLIPPAGE_PERP_PCT", 0.04),
        "spot_vs_perp": getattr(config, "KAISER_SLIPPAGE_SPOT_PERP_PCT", 0.08),
        "lineal_vs_inverse": getattr(config, "KAISER_SLIPPAGE_PERP_PCT", 0.04),
        "usdt_vs_usdc": getattr(config, "KAISER_SLIPPAGE_STABLE_PCT", 0.03),
        "spot_vs_index": getattr(config, "KAISER_SLIPPAGE_SPOT_PCT", 0.05),
        "basis_fut_vs_perp": getattr(config, "KAISER_SLIPPAGE_PERP_PCT", 0.04),
    }
    base_slip = defaults.get(tipo, 0.05)
    if b in config.ACTIVOS_PENTIVERSO:
        return base_slip * 0.85
    return base_slip


def _score_etiquetas(perfil_arista: dict | None) -> float:
    if not perfil_arista:
        return 0.5
    tags = perfil_arista.get("etiquetas_resumen") or []
    if "DATOS_INSUFICIENTES" in tags or "SIN_CONSENSO" in tags:
        return 0.4
    score = 1.0
    if "LONG_FRIENDLY" in tags or "REVIERTE_RAPIDO" in tags:
        score += 0.25
    if "SHORT_HUMO" in tags or "LONG_HUMO" in tags:
        score -= 0.15
    if "DESVIO_PERSISTENTE" in tags:
        score -= 0.2
    if "RUIDOSO" in tags:
        score -= 0.1
    return max(0.1, min(1.5, score))


def _fila_matriz_por_tipo(matriz: list[dict], base: str, tipo: str) -> dict | None:
    b = base.upper()
    for row in matriz:
        if row.get("base", "").upper() == b and row.get("tipo") == tipo:
            return row
    return None


def rankear_aristas_vivas(
    base: str,
    matriz_filas: list[dict],
    perfiles: dict | None = None,
    libros: dict | None = None,
) -> list[dict]:
    """Ranking de aristas del metaverso con regalo neto (Ancla si hay libro)."""
    from core import ancla

    b = base.upper()
    perfiles = perfiles or {}
    libros = libros or {}
    perf_base = perfiles.get(b) or {}
    ranking: list[dict] = []

    for tipo in ARISTAS_TIPO:
        row = _fila_matriz_por_tipo(matriz_filas, b, tipo)
        if not row:
            continue
        bruto = float(row.get("spread_pct") or row.get("desvio_signed_pct") or 0)
        if bruto <= 0:
            bruto = float(row.get("spread_pct") or 0)
        bruto = abs(bruto)

        neto = None
        slip = None
        max_usd = None
        seg_usd = None
        if libros:
            ev = ancla.evaluar_fila_matriz(row, libros)
            if ev:
                neto = float(ev.get("regalo_neto_pct_est") or (bruto - float(ev.get("slippage_pct") or 0)))
                slip = float(ev.get("slippage_pct") or 0)
                max_usd = ev.get("entrada_maxima_usd")
                seg_usd = ev.get("entrada_segura_usd")
                bruto = float(ev.get("spread_bruto_pct") or bruto)

        if neto is None:
            slip = _slippage_estimado(b, tipo)
            neto = round(bruto - slip, 4)
        perf = perf_base.get(tipo) or perf_base.get("perp_vs_index")
        calidad = _score_etiquetas(perf)
        ranking.append({
            "arista_id": f"{b}:{tipo}",
            "tipo": tipo,
            "regalo_bruto_pct": round(bruto, 4),
            "slippage_est_pct": round(slip, 4),
            "regalo_neto_pct": round(neto, 4),
            "entrada_maxima_usd": max_usd,
            "entrada_segura_usd": seg_usd,
            "fuente_slippage": "ANCLA" if libros and max_usd else "CONSTANTE",
            "score_calidad": round(calidad, 3),
            "score_total": round(neto * calidad, 4),
            "etiquetas_arista": (perf or {}).get("etiquetas_resumen", []),
            "datos_vivos": row,
        })

    ranking.sort(key=lambda x: x["score_total"], reverse=True)
    return ranking


def rankear_rutas_plantilla(
    base: str,
    matriz_filas: list[dict],
    perfiles: dict | None = None,
    libros: dict | None = None,
) -> list[dict]:
    """Rutas multi-arista precargadas (triangulación simple)."""
    aristas_rank = {
        a["tipo"]: a for a in rankear_aristas_vivas(base, matriz_filas, perfiles, libros)
    }
    rutas: list[dict] = []

    for plantilla in RUTAS_PLANTILLA:
        legs = []
        bruto = 0.0
        slip = 0.0
        ok = True
        tags_union: list[str] = []
        for tipo in plantilla["aristas"]:
            leg = aristas_rank.get(tipo)
            if not leg:
                ok = False
                break
            legs.append(leg)
            bruto += leg["regalo_bruto_pct"]
            slip += leg["slippage_est_pct"]
            tags_union.extend(leg.get("etiquetas_arista") or [])
        if not ok or not legs:
            continue
        neto = round(bruto - slip, 4)
        calidad = sum(l["score_calidad"] for l in legs) / len(legs)
        rutas.append({
            "ruta_id": f"{base.upper()}:{plantilla['id']}",
            "nombre": plantilla["nombre"],
            "base": base.upper(),
            "aristas": [l["arista_id"] for l in legs],
            "regalo_bruto_pct": round(bruto, 4),
            "slippage_est_pct": round(slip, 4),
            "regalo_neto_pct": neto,
            "score_calidad": round(calidad, 3),
            "score_total": round(neto * calidad, 4),
            "etiquetas_ruta": list(dict.fromkeys(tags_union)),
        })

    rutas.sort(key=lambda x: x["score_total"], reverse=True)
    return rutas


def rankear_multicruces(
    matriz_filas: list[dict],
    base: str,
) -> list[dict]:
    """Rutas multicruce spot desde filas matriz (Greed)."""
    b = base.upper()
    out: list[dict] = []
    for row in matriz_filas:
        if str(row.get("base", "")).upper() != b:
            continue
        tipo = str(row.get("tipo", ""))
        if not tipo.startswith("multicruce_"):
            continue
        sp = float(row.get("spread_pct") or 0)
        via = str(row.get("via_quote") or "?")
        n = int(row.get("n_piernas") or len(row.get("piernas") or []))
        slip = getattr(config, "KAISER_SLIPPAGE_SPOT_PCT", 0.05) * n
        neto = round(sp - slip, 4)
        out.append({
            "ruta_id": row.get("ruta_id") or f"{b}:via_{via}",
            "nombre": f"Multicruce {b} vía {via} ({n}p)",
            "base": b,
            "via_quote": via,
            "n_piernas": n,
            "regalo_bruto_pct": round(sp, 4),
            "slippage_est_pct": round(slip, 4),
            "regalo_neto_pct": neto,
            "score_calidad": 0.85 if via in ("USDC", "MNT") else 0.75,
            "score_total": round(neto * (0.85 if via in ("USDC", "MNT") else 0.75), 4),
            "piernas": row.get("piernas"),
            "tipo_spread": tipo,
        })
    out.sort(key=lambda x: x["score_total"], reverse=True)
    return out


def rankear_basis(
    matriz_filas: list[dict],
    base: str,
    perfiles: dict | None = None,
    libros: dict | None = None,
) -> list[dict]:
    """Candidatos basis hold (spot↔perp, lineal↔inverse) desde matriz."""
    from core import greed_basis as basis_mod

    b = base.upper()
    perfiles = perfiles or {}
    libros = libros or {}
    perf_base = perfiles.get(b) or {}
    out: list[dict] = []

    for tipo in basis_mod.TIPOS_BASIS:
        row = _fila_matriz_por_tipo(matriz_filas, b, tipo)
        if not row:
            continue
        bruto = abs(float(row.get("spread_pct") or 0))
        neto = None
        slip = None
        frentes = None
        if libros:
            from core import ancla
            ev = ancla.evaluar_fila_matriz(row, libros)
            if ev:
                bruto = float(ev.get("spread_bruto_pct") or bruto)
                neto = float(ev.get("regalo_neto_pct_est") or 0)
                slip = float(ev.get("slippage_pct") or 0)
                frentes = ev.get("frentes")
        if neto is None:
            slip = _slippage_estimado(b, tipo)
            neto = round(bruto - slip, 4)
        op = {
            "base": b,
            "tipo_spread": tipo,
            "spread_bruto_pct": bruto,
            "regalo_neto_pct_est": neto,
            "fees_total_pct": float(getattr(config, "GREED_BASIS_SALIDA_NETO_MIN_PCT", 0.08)) * 0.5,
            "frentes": frentes,
        }
        ok, mot = basis_mod.debe_entrar_basis(op)
        perf = perf_base.get(tipo) or {}
        calidad = _score_etiquetas(perf)
        out.append({
            "ruta_id": f"{b}:basis_{tipo}",
            "nombre": f"Basis hold {tipo}",
            "base": b,
            "tipo_spread": tipo,
            "modo": "BASIS_HOLD",
            "regalo_bruto_pct": round(bruto, 4),
            "slippage_est_pct": round(slip or 0, 4),
            "regalo_neto_pct": round(neto, 4),
            "score_calidad": round(calidad, 3),
            "score_total": round(neto * calidad, 4) if ok else 0,
            "entrar_ok": ok,
            "motivo_entrada": mot,
            "etiquetas_ruta": (perf or {}).get("etiquetas_resumen", []),
            "datos_vivos": row,
        })
    out.sort(key=lambda x: (x.get("entrar_ok", False), x["score_total"]), reverse=True)
    return out


def oportunidades_metaverso(
    matriz_filas: list[dict],
    bases: list[str],
    perfiles: dict | None = None,
    libros: dict | None = None,
    *,
    top_n: int | None = None,
) -> dict[str, Any]:
    """Por base con señal en matriz: aristas + rutas precargadas rankeadas."""
    top_n = top_n or getattr(config, "KAISER_RUTAS_TOP_N", 5)
    umbral = getattr(config, "KAISER_MATRIZ_UMBRAL_PCT", 0.25)
    out: dict[str, Any] = {}

    bases_con_senal: set[str] = set()
    for row in matriz_filas:
        if float(row.get("spread_pct") or 0) >= umbral * 0.5:
            bases_con_senal.add(str(row.get("base", "")).upper())

    for base in bases:
        bu = base.upper()
        if bu not in bases_con_senal and bu not in config.ACTIVOS_PENTIVERSO:
            continue
        rutas = rankear_rutas_plantilla(bu, matriz_filas, perfiles, libros)
        mc = rankear_multicruces(matriz_filas, bu)
        bh = rankear_basis(matriz_filas, bu, perfiles, libros)
        rutas = sorted(rutas + mc + bh, key=lambda x: x["score_total"], reverse=True)
        aristas = rankear_aristas_vivas(bu, matriz_filas, perfiles, libros)
        if not rutas and not aristas:
            continue
        out[bu] = {
            "aristas_top": aristas[:top_n],
            "rutas_top": rutas[:top_n],
            "ruta_idonea": rutas[0] if rutas else (None if not aristas else {"arista_directa": aristas[0]}),
        }
    return out
