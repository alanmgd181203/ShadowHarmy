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


def cero_estructural_manto(base: str) -> dict[str, Any]:
    """Cero del spread lineal↔inverso para frecuencia/ETA/puerta Igris.

    Preferencia: cero_lineal − cero_inverso (ambos vs índice).
    Fallback: mediana histórica de muestras `lineal_vs_inverse`.
    """
    bu = (base or "").upper()
    out: dict[str, Any] = {
        "base": bu,
        "cero_pct": None,
        "fuente": None,
        "cero_lineal_pct": None,
        "cero_inverso_pct": None,
        "ok": False,
    }
    if not bu:
        return out

    pl = perfil_sesgo_edge(bu, MARES_EDGE["lineal"])
    pi = perfil_sesgo_edge(bu, MARES_EDGE["inverso"])
    cl = pl.get("cero_estructural_pct")
    ci = pi.get("cero_estructural_pct")
    out["cero_lineal_pct"] = cl
    out["cero_inverso_pct"] = ci
    if cl is not None and ci is not None:
        out["cero_pct"] = round(float(cl) - float(ci), 6)
        out["fuente"] = "index_lineal_menos_inverso"
        out["ok"] = True
        return out

    # Fallback: historia directa del edge de manto
    ahora = time.time()
    samples = load_samples(bu, "lineal_vs_inverse", since_ts=ahora - PLAZOS_SESGO["mediano"])
    if len(samples) < _min_muestras():
        samples = load_samples(bu, "lineal_vs_inverse", since_ts=ahora - PLAZOS_SESGO["corto"])
    m = metricas_sesgo(samples)
    if m.get("mediana_pct") is not None and int(m.get("n") or 0) >= 3:
        out["cero_pct"] = float(m["mediana_pct"])
        out["fuente"] = "mediana_lineal_vs_inverse"
        out["ok"] = True
        out["n"] = m.get("n")
    return out


def usar_cero_en_manto() -> bool:
    return bool(getattr(config, "MANTO_CERO_ESTRUCTURAL", True))


def umbral_manto_con_cero(umbral_fees_pct: float, cero_pct: float | None) -> float:
    """Umbral efectivo: fees (o marcha) + cero estructural.

    Si el gap eterno es +0.08% y fees 0.11%, hace falta ~0.19% de spread vivo.
    """
    u = max(0.0, float(umbral_fees_pct or 0.0))
    if not usar_cero_en_manto() or cero_pct is None:
        return u
    return round(u + float(cero_pct), 6)


def exceso_vs_cero(signed_or_spread_pct: float, cero_pct: float | None) -> float:
    """Cuánto se aleja el spread vivo del clima normal (puede ser negativo)."""
    if cero_pct is None or not usar_cero_en_manto():
        return float(signed_or_spread_pct)
    return float(signed_or_spread_pct) - float(cero_pct)


def _serie_gap_lineal_inverso(base: str, *, ventana_s: float) -> list[dict[str, Any]]:
    """Serie gap ≈ signed_lineal − signed_inverso alineada por timestamp (~1h).

    Prefiere muestras `lineal_vs_inverse` si hay suficientes; si no, empareja vs índice.
    """
    bu = (base or "").upper()
    ahora = time.time()
    since = ahora - ventana_s
    direct = load_samples(bu, "lineal_vs_inverse", since_ts=since)
    if len(direct) >= _min_muestras():
        out = []
        for s in sorted(direct, key=lambda r: _f(r.get("ts"))):
            out.append({
                "ts": _f(s.get("ts")),
                "gap_pct": _f(s.get("signed_pct")),
                "fuente": "lineal_vs_inverse",
            })
        return out

    lin = load_samples(bu, MARES_EDGE["lineal"], since_ts=since)
    inv = load_samples(bu, MARES_EDGE["inverso"], since_ts=since)
    if not lin or not inv:
        return []
    inv_sorted = sorted(inv, key=lambda r: _f(r.get("ts")))
    out = []
    j = 0
    tol = 3600.0  # 1h
    for s in sorted(lin, key=lambda r: _f(r.get("ts"))):
        ts = _f(s.get("ts"))
        while j + 1 < len(inv_sorted) and abs(_f(inv_sorted[j + 1].get("ts")) - ts) <= abs(
            _f(inv_sorted[j].get("ts")) - ts
        ):
            j += 1
        ts_i = _f(inv_sorted[j].get("ts"))
        if abs(ts_i - ts) > tol:
            continue
        gap = _f(s.get("signed_pct")) - _f(inv_sorted[j].get("signed_pct"))
        out.append({"ts": ts, "gap_pct": gap, "fuente": "lineal_menos_inverso_index"})
    return out


def analisis_residencia_y_volteos(
    base: str,
    *,
    ventana: str = "mediano",
) -> dict[str, Any]:
    """% del tiempo en el desfase estructural + episodios cuando se voltea.

    - residencia: cerca del cero (clima normal) y mismo lado del sesgo.
    - volteo: el gap cruza al lado opuesto del cero más allá de epsilon
      (momentos raros — candidatos a planear / aprovechar).
    """
    bu = (base or "").upper()
    segs = float(PLAZOS_SESGO.get(ventana) or PLAZOS_SESGO["mediano"])
    eps = _epsilon_clima_pct()
    cero_info = cero_estructural_manto(bu)
    cero = cero_info.get("cero_pct") if cero_info.get("ok") else None
    serie = _serie_gap_lineal_inverso(bu, ventana_s=segs)

    vacio: dict[str, Any] = {
        "base": bu,
        "ok": False,
        "ventana": ventana,
        "ventana_dias": round(segs / 86400, 1),
        "n": 0,
        "cero_gap_pct": cero,
        "epsilon_pct": eps,
        "motivo": "sin_serie" if not serie else "sin_cero",
    }
    if not serie or cero is None:
        return vacio

    gaps = [float(p["gap_pct"]) for p in serie]
    n = len(gaps)
    med_serie = statistics.median(gaps) if n > 1 else gaps[0]

    # Estados por muestra respecto al cero estructural
    estados: list[str] = []
    for g in gaps:
        d = g - float(cero)
        if abs(d) <= eps:
            estados.append("normal")
        elif (float(cero) >= 0 and d < -eps) or (float(cero) < 0 and d > eps):
            # hacia / a través del lado opuesto del sesgo
            estados.append("tenso_contra" if abs(d) <= eps * 3 else "volteo")
        else:
            estados.append("tenso_favor" if abs(d) <= eps * 3 else "anomalia_favor")

    n_normal = sum(1 for e in estados if e == "normal")
    n_volteo = sum(1 for e in estados if e == "volteo")
    n_contra = sum(1 for e in estados if e in ("volteo", "tenso_contra"))
    n_favor = sum(1 for e in estados if e in ("tenso_favor", "anomalia_favor"))
    pct_normal = n_normal / n
    pct_volteo = n_volteo / n
    pct_contra = n_contra / n
    pct_favor = n_favor / n
    # Vive en el desfase ≈ clima normal + mismo lado a favor
    pct_en_desfase = (n_normal + n_favor) / n

    # Episodios de volteo (rachas)
    episodios: list[dict[str, Any]] = []
    i = 0
    while i < len(serie):
        if estados[i] != "volteo":
            i += 1
            continue
        j = i
        while j < len(serie) and estados[j] == "volteo":
            j += 1
        chunk = serie[i:j]
        gaps_e = [float(p["gap_pct"]) for p in chunk]
        dur_h = max(0.0, (_f(chunk[-1]["ts"]) - _f(chunk[0]["ts"])) / 3600.0)
        if len(chunk) == 1:
            dur_h = max(dur_h, 1.0)
        excesos = [abs(g - float(cero)) for g in gaps_e]
        episodios.append({
            "ts_inicio": _f(chunk[0]["ts"]),
            "ts_fin": _f(chunk[-1]["ts"]),
            "n_muestras": len(chunk),
            "duracion_h": round(dur_h, 2),
            "gap_medio_pct": round(statistics.mean(gaps_e), 6),
            "exceso_medio_pct": round(statistics.mean(excesos), 6),
            "exceso_max_pct": round(max(excesos), 6),
        })
        i = j

    dur_media = (
        round(statistics.mean([e["duracion_h"] for e in episodios]), 2)
        if episodios else None
    )
    exceso_medio_vol = (
        round(statistics.mean([e["exceso_medio_pct"] for e in episodios]), 6)
        if episodios else None
    )

    if pct_en_desfase >= 0.85:
        veredicto = "abrumador"
    elif pct_en_desfase >= 0.65:
        veredicto = "dominante"
    elif pct_en_desfase >= 0.45:
        veredicto = "mitad_mitad"
    else:
        veredicto = "inestable"

    return {
        "base": bu,
        "ok": True,
        "ventana": ventana,
        "ventana_dias": round(segs / 86400, 1),
        "n": n,
        "fuente_serie": serie[0].get("fuente") if serie else None,
        "cero_gap_pct": round(float(cero), 6),
        "cero_info": cero_info,
        "mediana_serie_pct": round(float(med_serie), 6),
        "epsilon_pct": eps,
        "pct_tiempo_clima_normal": round(pct_normal, 4),
        "pct_tiempo_en_desfase": round(pct_en_desfase, 4),
        "pct_tiempo_volteado": round(pct_volteo, 4),
        "pct_tiempo_contra_sesgo": round(pct_contra, 4),
        "pct_tiempo_favor_extra": round(pct_favor, 4),
        "veredicto_residencia": veredicto,
        "volteos": {
            "n_episodios": len(episodios),
            "duracion_media_h": dur_media,
            "exceso_medio_pct": exceso_medio_vol,
            "episodios_muestra": episodios[:12],
            "nota": (
                "Volteo = gap al lado opuesto del cero estructural (mas alla de epsilon). "
                "Candidatos a planear/aprovechar; no son el gap eterno."
            ),
        },
        "lectura": (
            f"Vive ~{pct_en_desfase*100:.0f}% del tiempo en el desfase estructural "
            f"({veredicto}). Volteos: {len(episodios)} episodios "
            f"(~{pct_volteo*100:.1f}% del tiempo)."
        ),
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
