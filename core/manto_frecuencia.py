"""Frecuencia de oportunidades del manto — 4 umbrales × 3 plazos (anual ~10%).

Contadores en paralelo (misma historia `lineal_vs_inverse`):
  - fees        → exceso vs cero ≥ break-even completo (Táctico)
  - medio_fees  → exceso vs cero ≥ ½ fees (Marcha Forzada)
  - tablas      → exceso vs cero ≥ epsilon (~0 edge; Asalto / salir tablas)
  - morado      → exceso vs cero ≥ max(fees_be, umbral OPORTUNIDAD_MANTO)

Cero estructural (MANTO_CERO_ESTRUCTURAL): no cuenta el gap eterno lineal↔inverso;
oportunidad = alejarse del clima normal (cero_lineal − cero_inverso vs índice).

Pesos de fusión (Monarca 2026-07-24): corto 50% · mediano 40% · anual 10%.
Alta frecuencia → más paciencia (tau grande). Baja → empujar (Asalto / tablas).
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core import igris_despliegue as ides
from core import igris_manto as im
from core import kaiser_sesgo_index as ksi
from core.kaiser_samples import load_samples

EDGE_MANTO = "lineal_vs_inverse"

PLAZOS_S: dict[str, float] = {
    "corto": 3 * 86400,
    "mediano": 30 * 86400,
    "largo": 365 * 86400,
}

PESOS_PLAZOS: dict[str, float] = {
    "corto": 0.50,
    "mediano": 0.40,
    "largo": 0.10,
}

UMBRAL_KEYS = ("fees", "medio_fees", "tablas", "morado")


def _pesos() -> dict[str, float]:
    return {
        "corto": float(getattr(config, "MANTO_FREQ_PESO_CORTO", PESOS_PLAZOS["corto"])),
        "mediano": float(getattr(config, "MANTO_FREQ_PESO_MEDIANO", PESOS_PLAZOS["mediano"])),
        "largo": float(getattr(config, "MANTO_FREQ_PESO_LARGO", PESOS_PLAZOS["largo"])),
    }


def _tablas_eps_pct() -> float:
    return float(getattr(config, "MANTO_FREQ_TABLAS_EPS_PCT", 0.01) or 0.01)


def fees_be_activo(base: str) -> float:
    fl, fs = im.frentes_bootstrap(base)
    if not fl or not fs:
        return float(getattr(config, "ANCLA_FEE_INVERSE_TAKER_PCT", 0.055) or 0.055) * 2
    return float(ides.fees_break_even_pct(fl, fs))


def umbrales_pct(base: str, fees_be: float | None = None) -> dict[str, float]:
    fees = float(fees_be if fees_be is not None else fees_be_activo(base))
    piso_morado = float(getattr(config, "KAISER_OPORTUNIDAD_MANTO_UMBRAL_PCT", 0.0) or 0.0)
    return {
        "fees": fees,
        "medio_fees": fees * 0.5,
        "tablas": _tablas_eps_pct(),
        "morado": max(fees, piso_morado),
    }


def _pct_sobre(
    samples: list[dict],
    umbral: float,
    *,
    cero_pct: float | None = None,
) -> dict[str, Any]:
    """% de muestras cuya *exceso vs cero* (o abs_pct legado) supera el umbral de marcha."""
    n = len(samples)
    if n <= 0:
        return {"n": 0, "n_sobre": 0, "pct": None, "cero_pct": cero_pct}
    above = 0
    for s in samples:
        if ksi.usar_cero_en_manto() and cero_pct is not None:
            signed = float(s.get("signed_pct") if s.get("signed_pct") is not None else s.get("abs_pct") or 0)
            exceso = abs(ksi.exceso_vs_cero(signed, cero_pct))
        else:
            exceso = float(s.get("abs_pct") or 0)
        if exceso + 1e-15 >= umbral:
            above += 1
    return {
        "n": n,
        "n_sobre": above,
        "pct": round(above / n, 4),
        "cero_pct": cero_pct,
    }


def _blend(plazos_pct: dict[str, float | None]) -> float | None:
    pesos = _pesos()
    num = 0.0
    den = 0.0
    for nombre, w in pesos.items():
        p = plazos_pct.get(nombre)
        if p is None:
            continue
        num += float(p) * w
        den += w
    if den <= 0:
        return None
    # Renormalizar si falta algún plazo (cuenta nueva / datos cortos)
    return round(num / den, 4)


def frecuencia_activo(base: str, *, ahora: float | None = None) -> dict[str, Any]:
    """Perfil de frecuencia manto para un activo (ranking / flota)."""
    bu = (base or "").upper()
    ahora = ahora if ahora is not None else time.time()
    fees = fees_be_activo(bu)
    umbs = umbrales_pct(bu, fees)
    min_n = int(getattr(config, "MANTO_FREQ_MIN_MUESTRAS", 20) or 20)
    cero_info = ksi.cero_estructural_manto(bu)
    cero = cero_info.get("cero_pct") if cero_info.get("ok") else None

    por_umbral: dict[str, Any] = {}
    for uk in UMBRAL_KEYS:
        plazos_out: dict[str, Any] = {}
        plazos_pct: dict[str, float | None] = {}
        for pn, segs in PLAZOS_S.items():
            samples = load_samples(bu, EDGE_MANTO, since_ts=ahora - segs)
            met = _pct_sobre(samples, umbs[uk], cero_pct=cero)
            ok = int(met["n"]) >= min_n
            plazos_out[pn] = {
                "ventana_dias": round(segs / 86400, 1),
                **met,
                "ok": ok,
            }
            plazos_pct[pn] = float(met["pct"]) if ok and met["pct"] is not None else None
        blended = _blend(plazos_pct)
        por_umbral[uk] = {
            "umbral_pct": round(umbs[uk], 6),
            "plazos": plazos_out,
            "pct_blend": blended,
        }

    # Score de paciencia: fees (exigente) con fallback a medio_fees
    score = por_umbral["fees"].get("pct_blend")
    if score is None:
        score = por_umbral["medio_fees"].get("pct_blend")
    if score is None:
        score = por_umbral["tablas"].get("pct_blend")

    modo = sugerir_modo(score, por_umbral)
    return {
        "base": bu,
        "edge": EDGE_MANTO,
        "fees_be_pct": round(fees, 6),
        "umbrales": umbs,
        "cero_estructural": cero_info,
        "pesos_plazos": _pesos(),
        "contadores": por_umbral,
        "score_paciencia": score,
        "modo_sugerido": modo,
        "ok": score is not None,
        "nota": (
            "Oportunidad = |spread − cero estructural| ≥ umbral marcha. "
            "Sin cero → legado abs_pct."
        ),
    }


def sugerir_modo(score: float | None, contadores: dict[str, Any]) -> str:
    """
    Alta freq fees → tactico (paciencia).
    Media → marcha_forzada.
    Solo tablas / casi nada → asalto.
    """
    if score is None:
        return "sin_datos"
    hi = float(getattr(config, "MANTO_FREQ_SCORE_TACTICO", 0.25) or 0.25)
    mid = float(getattr(config, "MANTO_FREQ_SCORE_FORZADA", 0.08) or 0.08)
    if score >= hi:
        return "tactico"
    if score >= mid:
        return "marcha_forzada"
    tablas_b = (contadores.get("tablas") or {}).get("pct_blend")
    if tablas_b is not None and float(tablas_b) < 0.02:
        return "asalto"
    return "asalto"


def tau_desde_score(score: float | None) -> dict[str, Any]:
    """Mismo reloj invertido: alta freq → tau grande."""
    tau_base = float(getattr(config, "IGRIS_URGENCIA_TAU_HORAS", 8.0) or 8.0)
    tau_min = float(getattr(config, "IGRIS_URGENCIA_TAU_MIN_HORAS", 1.0) or 1.0)
    tau_max = float(getattr(config, "IGRIS_URGENCIA_TAU_MAX_HORAS", 24.0) or 24.0)
    if tau_max < tau_min:
        tau_max = tau_min
    if score is None:
        return {
            "tau_h": tau_base,
            "pct_frecuencia": None,
            "modo": "fallback_estatico",
            "fuente": "manto_frecuencia",
        }
    pct = max(0.0, min(1.0, float(score)))
    tau = tau_min + (tau_max - tau_min) * pct
    return {
        "tau_h": round(tau, 4),
        "pct_frecuencia": round(pct, 4),
        "modo": "manto_frecuencia_4umbrales",
        "fuente": "manto_frecuencia",
    }


def oportunidades_por_hora(base: str, umbral_key: str = "medio_fees", *, ahora: float | None = None) -> float | None:
    """Tasa horaria estimada (plazo corto) de cruces sobre umbral (vs cero estructural)."""
    bu = (base or "").upper()
    ahora = ahora if ahora is not None else time.time()
    umbs = umbrales_pct(bu)
    uk = umbral_key if umbral_key in umbs else "medio_fees"
    segs = PLAZOS_S["corto"]
    samples = load_samples(bu, EDGE_MANTO, since_ts=ahora - segs)
    if len(samples) < int(getattr(config, "MANTO_FREQ_MIN_MUESTRAS", 20) or 20):
        return None
    cero_info = ksi.cero_estructural_manto(bu)
    cero = cero_info.get("cero_pct") if cero_info.get("ok") else None
    met = _pct_sobre(samples, umbs[uk], cero_pct=cero)
    horas = segs / 3600.0
    if horas <= 0:
        return None
    return round(float(met["n_sobre"]) / horas, 4)


def eta_despliegue_horas(
    base: str,
    meta_usd: float,
    *,
    marcha_id: str = "marcha_forzada",
    mordida_usd: float | None = None,
    ahora: float | None = None,
    umbral_pct_override: float | None = None,
) -> dict[str, Any]:
    """
    ETA aproximado: meta / (mordida × oportunidades/h del umbral de la marcha).
    Oportunidades cuentan exceso vs cero estructural (no gap eterno).
    personalizado: usa umbral custom (marcha_duracion) o override.
    """
    from core.pase_director import MARCHAS, normalizar_marcha
    from core import marcha_duracion as mdur

    mid = normalizar_marcha(marcha_id)
    perfil = MARCHAS[mid]
    mult = float(perfil.get("umbral_fees_mult", 0.5))

    umbral_custom = None
    if umbral_pct_override is not None:
        umbral_custom = float(umbral_pct_override)
        uk = "custom"
    elif mid == "personalizado":
        ua = mdur.umbral_activo(base, reajustar=False)
        umbral_custom = float(ua.get("umbral_pct") or 0.0)
        uk = "custom"
    elif mid == "asalto" or mult <= 0:
        uk = "tablas"
    elif mult < 0.99:
        uk = "medio_fees"
    else:
        uk = "fees"

    if umbral_custom is not None:
        rate = mdur.ops_por_hora_umbral(base, umbral_custom, ahora=ahora)
    else:
        rate = oportunidades_por_hora(base, uk, ahora=ahora)
    if mordida_usd is None:
        mordida_usd = float(getattr(config, "MANTO_FREQ_MORDIDA_USD", 5.0) or 5.0)
    mordida = max(float(mordida_usd), 1.0)
    meta = max(float(meta_usd), 0.0)
    bocados = meta / mordida if meta > 0 else 0.0
    cero_info = ksi.cero_estructural_manto(base)

    out: dict[str, Any] = {
        "base": (base or "").upper(),
        "marcha_id": mid,
        "umbral_key": uk,
        "umbral_pct": umbral_custom,
        "meta_usd": round(meta, 4),
        "mordida_usd": round(mordida, 4),
        "bocados_est": round(bocados, 2),
        "ops_por_hora": rate,
        "cero_estructural": cero_info,
        "eta_h": None,
        "eta_h_opt": None,
        "eta_h_pes": None,
        "ok": False,
        "motivo": "ok",
    }
    if rate is None or rate <= 0:
        out["motivo"] = "sin_tasa" if rate is None else "tasa_cero"
        return out
    if bocados <= 0:
        out["motivo"] = "meta_cero"
        out["ok"] = True
        out["eta_h"] = 0.0
        out["eta_h_opt"] = 0.0
        out["eta_h_pes"] = 0.0
        return out

    eta = bocados / rate
    out["eta_h"] = round(eta, 2)
    out["eta_h_opt"] = round(bocados / (rate * 1.5), 2)
    out["eta_h_pes"] = round(bocados / max(rate * 0.5, 1e-9), 2)
    out["ok"] = True
    return out


def ranking_frecuencia(
    bases: list[str],
    *,
    ahora: float | None = None,
) -> list[dict[str, Any]]:
    """Ordena activos por score_paciencia (más oportunidades primero)."""
    rows = [frecuencia_activo(b, ahora=ahora) for b in bases]
    rows.sort(
        key=lambda r: (
            0 if r.get("ok") else 1,
            -(float(r["score_paciencia"]) if r.get("score_paciencia") is not None else -1.0),
            str(r.get("base") or ""),
        )
    )
    return rows


def snapshot_ranking(
    bases: list[str] | None = None,
    *,
    equity_usd: float = 0.0,
    ahora: float | None = None,
) -> dict[str, Any]:
    """Bloque para estado_vivo / panel: flota o Santos + ETA por marcha del foco."""
    if bases is None:
        bases = _bases_ranking()
    ranking = ranking_frecuencia(bases, ahora=ahora)
    etas: dict[str, Any] = {}
    eta_lote: dict[str, Any] = {}
    try:
        from core import pase_director as pd
        from core import marcha_duracion as mdur

        marchas = ["tactico", "marcha_forzada", "asalto"]
        store = mdur.cargar_umbrales()
        if store.get("duracion_dias") or store.get("por_base"):
            marchas.append("personalizado")
        payload = pd.cargar_marcha_payload() or {}
        if payload.get("marcha_id") == "personalizado" and "personalizado" not in marchas:
            marchas.append("personalizado")

        for mid in marchas:
            etas_m: dict[str, Any] = {}
            max_eta = None
            ok_lote = False
            for row in ranking[:8]:
                b = row["base"]
                meta = 0.0
                if equity_usd > 0:
                    me = pd.meta_engorde_usd(equity_usd, b, marcha_id=mid)
                    meta = float(me.get("need_fill_usd") or me.get("need_usd") or 0)
                if meta <= 0:
                    meta = float(getattr(config, "MANTO_FREQ_META_DEFAULT_USD", 100.0) or 100.0)
                et = eta_despliegue_horas(b, meta, marcha_id=mid, ahora=ahora)
                etas_m[b] = et
                if et.get("ok") and et.get("eta_h") is not None:
                    ok_lote = True
                    eh = float(et["eta_h"])
                    max_eta = eh if max_eta is None else max(max_eta, eh)
            etas[mid] = etas_m
            eta_lote[mid] = {
                "eta_h": round(max_eta, 2) if max_eta is not None else None,
                "ok": ok_lote and max_eta is not None,
                "n_pares": len(etas_m),
            }
    except Exception as e:
        etas = {"error": str(e)}
        eta_lote = {"error": str(e)}

    return {
        "ts": ahora if ahora is not None else time.time(),
        "n_activos": len(ranking),
        "pesos_plazos": _pesos(),
        "ranking": [
            {
                "base": r["base"],
                "score_paciencia": r.get("score_paciencia"),
                "modo_sugerido": r.get("modo_sugerido"),
                "fees_be_pct": r.get("fees_be_pct"),
                "pct_fees": (r.get("contadores") or {}).get("fees", {}).get("pct_blend"),
                "pct_medio": (r.get("contadores") or {}).get("medio_fees", {}).get("pct_blend"),
                "pct_tablas": (r.get("contadores") or {}).get("tablas", {}).get("pct_blend"),
                "pct_morado": (r.get("contadores") or {}).get("morado", {}).get("pct_blend"),
                "ok": r.get("ok"),
            }
            for r in ranking
        ],
        "eta_por_marcha": etas,
        "eta_lote_por_marcha": eta_lote,
    }


def _bases_ranking() -> list[str]:
    """Santos del grial ∩ flota manto; fallback flota completa."""
    from pathlib import Path
    import json

    santos: list[str] = []
    try:
        from core import plan_crecimiento as pc

        santos = [str(x).upper() for x in (pc.SANTOS_GRIAL or ())]
    except Exception:
        santos = []

    flota: list[str] = []
    path = Path(__file__).resolve().parents[1] / "config" / "diccionario_beru_flota_manto.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        flota = [str(x).upper() for x in ((data.get("meta") or {}).get("activos") or [])]
    except (OSError, json.JSONDecodeError, TypeError):
        flota = list(getattr(config, "ACTIVOS_PENTIVERSO", []) or [])

    if santos and flota:
        sset = set(flota)
        inter = [b for b in santos if b in sset]
        return inter or flota
    return santos or flota or list(getattr(config, "ACTIVOS_PENTIVERSO", []) or [])
