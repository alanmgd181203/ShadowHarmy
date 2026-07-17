"""Igris — snapshot de auditoría por activo (Sub-Santuario / AssetDetail).

Solo lectura. Estado cero si no hay piernas. No modifica apalancamiento.
"""
from __future__ import annotations

from typing import Any

from core import beru_capital as bc
from core import igris_manto as im


def _leg_cero(*, frente: str = "", symbol: str | None = None) -> dict[str, Any]:
    return {
        "frente": frente or None,
        "symbol": symbol,
        "size_base": 0.0,
        "size_usd": 0.0,
        "entry_price": 0.0,
        "mark_price": 0.0,
        "margen_usd": 0.0,
        "leverage_actual": None,  # UI: 00 — no inventar
        "leverage_max": 0.0,
        "fees_paid_usd": 0.0,
        "impacto_1pct_usd": 0.0,
        "entry_baseline": 0.0,  # apertura original (optimización Igris)
    }


def snapshot_cero(symbol: str) -> dict[str, Any]:
    """Plantilla reposo — todos en 00 / $0.00."""
    s = str(symbol or "BTC").upper()
    fl, fs = im.frentes_bootstrap(s)
    long_leg = _leg_cero(frente=fl, symbol=None)
    long_leg["leverage_max"] = round(bc.apalancamiento_inverse_max(s), 2)
    short_leg = _leg_cero(frente=fs, symbol=None)
    short_leg["leverage_max"] = round(bc.apalancamiento_linear_max(s), 2)
    return {
        "symbol": s,
        "fuente": "cero",
        "long": long_leg,
        "short": short_leg,
        "global": {
            "entry_avg": 0.0,
            "margen_usd": 0.0,
            "size_usd_long": 0.0,
            "size_usd_short": 0.0,
            "size_usd_total": 0.0,
            "impacto_1pct_usd": 0.0,
            "fees_paid_usd": 0.0,
        },
        "desequilibrio": {
            "puntos": 0.0,
            "pct": 0.0,
            "beneficio": "NEUTRO",
            "mark_long": 0.0,
            "mark_short": 0.0,
        },
        "fase_manto": {
            "estado": "REPOSO",
            "rango_beru": "—",
            "grado_beru": "BLOQUEADO",
            "fase_margen": None,
        },
        "optimizacion_igris": {
            "mejora_pts_long": 0.0,
            "mejora_pct_long": 0.0,
            "mejora_pts_short": 0.0,
            "mejora_pct_short": 0.0,
            "mejora_pts_global": 0.0,
            "mejora_pct_global": 0.0,
        },
    }


def _size_base_from_usd(size_usd: float, price: float) -> float:
    if size_usd <= 0 or price <= 0:
        return 0.0
    return size_usd / price


def _impacto_1pct(size_usd: float) -> float:
    """Sensibilidad ≈ 1% del nocional (misma idea que telemetria_igris)."""
    if size_usd <= 0:
        return 0.0
    return round(size_usd * 0.01, 4)


def _mejora_entrada(baseline: float, actual: float, *, long: bool) -> tuple[float, float]:
    """Mejora en puntos y %. LONG mejor si actual < baseline; SHORT si actual > baseline."""
    if baseline <= 0 or actual <= 0:
        return 0.0, 0.0
    if long:
        pts = baseline - actual
    else:
        pts = actual - baseline
    pct = (pts / baseline) * 100.0
    return round(pts, 6), round(pct, 4)


def _beneficio_desequilibrio(
    mark_long: float,
    mark_short: float,
    entry_long: float,
    entry_short: float,
) -> str:
    """
    Lectura simple: si el short (lineal) cotiza por encima del long (inverse)
    respecto a entradas, el basis puede favorecer o perjudicar.
    Sin marcas → NEUTRO.
    """
    if mark_long <= 0 or mark_short <= 0:
        return "NEUTRO"
    # Spread mark: short - long (mismo activo, unidades de precio)
    spread_mark = mark_short - mark_long
    if abs(spread_mark) < 1e-12:
        return "NEUTRO"
    # Si tenemos entradas, comparar spread actual vs spread de entrada
    if entry_long > 0 and entry_short > 0:
        spread_entry = entry_short - entry_long
        # Para manto L inverse + S lineal: ampliar spread a favor del short caro
        # beneficia el carry relativo si ya estamos posicionados; simplificado:
        delta = spread_mark - spread_entry
        if abs(delta) < 1e-12:
            return "NEUTRO"
        return "FAVOR" if delta > 0 else "CONTRA"
    return "FAVOR" if spread_mark > 0 else "CONTRA"


def _fase_desde_estado(
    *,
    size_l: float,
    size_s: float,
    igris_bloque: dict | None,
    progresion: dict | None,
) -> dict[str, Any]:
    igris_bloque = igris_bloque or {}
    progresion = progresion or {}
    masa = size_l + size_s
    fase_margen = igris_bloque.get("fase_margen")
    grado = progresion.get("grado_beru") or igris_bloque.get("plan_crecimiento", {}).get("grado_beru") or "BLOQUEADO"
    rango = progresion.get("rango_ejercito") or "—"
    accion = str(igris_bloque.get("accion_heuristica") or "")

    if masa <= 0:
        estado = "REPOSO"
    elif accion in ("ENGORDAR_MANTO", "BOOTSTRAP_MANTO") or (
        fase_margen == "EXPANSION" and masa > 0
    ):
        estado = "CRECIMIENTO"
    elif accion in ("PODAR_MANTO", "LIMPIAR_ESPEJOS") or fase_margen == "LEY_MARCIAL":
        estado = "REDUCCION"
    else:
        estado = "CRECIMIENTO" if masa > 0 else "REPOSO"

    return {
        "estado": estado,
        "rango_beru": rango if rango else "—",
        "grado_beru": grado,
        "fase_margen": fase_margen,
    }


def construir_asset_detail(
    symbol: str,
    *,
    pesos: dict | None = None,
    marks: dict[str, float] | None = None,
    igris_bloque: dict | None = None,
    progresion: dict | None = None,
    baselines: dict | None = None,
    fees_paid: dict | None = None,
    leverage_actual: dict | None = None,
    margen_im: dict | None = None,
) -> dict[str, Any]:
    """
    Arma el snapshot del Sub-Santuario para un activo.

    pesos: tusk.pesos (frentes → long/short/precio_medio_*)
    marks: opcional {frente: mark_price}
    baselines: opcional {long: px, short: px} apertura original
    fees_paid: opcional {long: usd, short: usd}
    leverage_actual: opcional {long: x, short: x}
    margen_im: opcional {long: usd, short: usd} position IM
    """
    s = str(symbol or "BTC").upper()
    out = snapshot_cero(s)
    pesos = pesos or {}
    marks = marks or {}
    baselines = baselines or {}
    fees_paid = fees_paid or {}
    leverage_actual = leverage_actual or {}
    margen_im = margen_im or {}

    fl, fs = im.frentes_bootstrap(s)
    # Acumular piernas del activo (todos los frentes que empiecen por SYMBOL)
    size_l = size_s = 0.0
    px_l_num = px_l_den = 0.0
    px_s_num = px_s_den = 0.0
    frente_long = fl
    frente_short = fs

    for frente, p in pesos.items():
        fu = str(frente).upper()
        if not fu.startswith(s):
            continue
        pl = float(p.get("long") or 0)
        ps = float(p.get("short") or 0)
        pml = float(p.get("precio_medio_long") or 0)
        pms = float(p.get("precio_medio_short") or 0)
        if pl > 0:
            size_l += pl
            if pml > 0:
                px_l_num += pl * pml
                px_l_den += pl
            if "INVERSE" in fu or fu.endswith("USD"):
                frente_long = frente
        if ps > 0:
            size_s += ps
            if pms > 0:
                px_s_num += ps * pms
                px_s_den += ps
            if "LINEAL" in fu or "USDT" in fu or "USDC" in fu:
                frente_short = frente

    entry_l = (px_l_num / px_l_den) if px_l_den > 0 else 0.0
    entry_s = (px_s_num / px_s_den) if px_s_den > 0 else 0.0
    mark_l = float(marks.get(frente_long) or marks.get("long") or 0)
    mark_s = float(marks.get(frente_short) or marks.get("short") or 0)

    # Si no hay marcas, usar entradas como proxy neutro (desequilibrio 0)
    if mark_l <= 0:
        mark_l = entry_l
    if mark_s <= 0:
        mark_s = entry_s

    base_l = _size_base_from_usd(size_l, entry_l or mark_l)
    base_s = _size_base_from_usd(size_s, entry_s or mark_s)

    margen_l = float(margen_im.get("long") or 0)
    margen_s = float(margen_im.get("short") or 0)
    # Sin IM: no inventar margen
    fees_l = float(fees_paid.get("long") or 0)
    fees_s = float(fees_paid.get("short") or 0)

    lev_max_l = round(bc.apalancamiento_inverse_max(s), 2)
    lev_max_s = round(bc.apalancamiento_linear_max(s), 2)
    lev_act_l = leverage_actual.get("long")
    lev_act_s = leverage_actual.get("short")
    if lev_act_l is not None:
        lev_act_l = float(lev_act_l)
    if lev_act_s is not None:
        lev_act_s = float(lev_act_s)

    out["fuente"] = "pesos" if (size_l > 0 or size_s > 0) else "cero"
    out["long"] = {
        "frente": frente_long,
        "symbol": frente_long.replace("_INVERSE", "").replace("_LINEAL", "") if frente_long else None,
        "size_base": round(base_l, 8),
        "size_usd": round(size_l, 4),
        "entry_price": round(entry_l, 6),
        "mark_price": round(mark_l, 6),
        "margen_usd": round(margen_l, 4),
        "leverage_actual": lev_act_l,
        "leverage_max": lev_max_l,
        "fees_paid_usd": round(fees_l, 4),
        "impacto_1pct_usd": _impacto_1pct(size_l),
        "entry_baseline": round(float(baselines.get("long") or 0), 6),
    }
    out["short"] = {
        "frente": frente_short,
        "symbol": frente_short.replace("_INVERSE", "").replace("_LINEAL", "") if frente_short else None,
        "size_base": round(base_s, 8),
        "size_usd": round(size_s, 4),
        "entry_price": round(entry_s, 6),
        "mark_price": round(mark_s, 6),
        "margen_usd": round(margen_s, 4),
        "leverage_actual": lev_act_s,
        "leverage_max": lev_max_s,
        "fees_paid_usd": round(fees_s, 4),
        "impacto_1pct_usd": _impacto_1pct(size_s),
        "entry_baseline": round(float(baselines.get("short") or 0), 6),
    }

    # Ancla global = promedio ponderado de entradas L y S (referencia Beru)
    if size_l > 0 and size_s > 0 and entry_l > 0 and entry_s > 0:
        entry_avg = (entry_l * size_l + entry_s * size_s) / (size_l + size_s)
    elif entry_l > 0:
        entry_avg = entry_l
    elif entry_s > 0:
        entry_avg = entry_s
    else:
        entry_avg = 0.0

    out["global"] = {
        "entry_avg": round(entry_avg, 6),
        "margen_usd": round(margen_l + margen_s, 4),
        "size_usd_long": round(size_l, 4),
        "size_usd_short": round(size_s, 4),
        "size_usd_total": round(size_l + size_s, 4),
        "impacto_1pct_usd": round(_impacto_1pct(size_l) + _impacto_1pct(size_s), 4),
        "fees_paid_usd": round(fees_l + fees_s, 4),
    }

    pts = round(mark_s - mark_l, 6) if (mark_l > 0 and mark_s > 0) else 0.0
    mid = (mark_l + mark_s) / 2.0 if (mark_l > 0 and mark_s > 0) else 0.0
    pct = round((pts / mid) * 100.0, 4) if mid > 0 else 0.0
    out["desequilibrio"] = {
        "puntos": pts,
        "pct": pct,
        "beneficio": _beneficio_desequilibrio(mark_l, mark_s, entry_l, entry_s),
        "mark_long": round(mark_l, 6),
        "mark_short": round(mark_s, 6),
    }

    out["fase_manto"] = _fase_desde_estado(
        size_l=size_l,
        size_s=size_s,
        igris_bloque=igris_bloque,
        progresion=progresion,
    )

    bl = float(baselines.get("long") or 0)
    bs = float(baselines.get("short") or 0)
    mpl, mpcl = _mejora_entrada(bl, entry_l, long=True)
    mps, mpcs = _mejora_entrada(bs, entry_s, long=False)
    out["optimizacion_igris"] = {
        "mejora_pts_long": mpl,
        "mejora_pct_long": mpcl,
        "mejora_pts_short": mps,
        "mejora_pct_short": mpcs,
        "mejora_pts_global": round((mpl + mps) / 2.0, 6) if (bl > 0 or bs > 0) else 0.0,
        "mejora_pct_global": round((mpcl + mpcs) / 2.0, 4) if (bl > 0 or bs > 0) else 0.0,
    }
    return out


def _marks_desde_snap(symbol: str, snap: dict, frente_long: str, frente_short: str) -> dict[str, float]:
    """Marcas Tank (inverse/linear) o fallback telemetría Bridge."""
    s = str(symbol or "").upper()
    marks: dict[str, float] = {}
    inv = (snap.get("inverse_perp") or {}).get("detalle") or {}
    lin = (snap.get("linear_perp") or {}).get("detalle") or {}
    for frente, det in {**inv, **lin}.items():
        if not str(frente).upper().startswith(s):
            continue
        px = float((det or {}).get("precio") or 0)
        if px > 0:
            marks[str(frente)] = px
    # Telemetría por activo (markPrice Bybit)
    por = ((snap.get("igris_posiciones") or {}).get("por_activo") or {}).get(s) or {}
    for lado, key_frente in (("long", frente_long), ("short", frente_short)):
        leg = por.get(lado) or {}
        mk = float(leg.get("mark_price") or 0)
        fr = leg.get("frente") or key_frente
        if mk > 0 and fr:
            marks.setdefault(str(fr), mk)
            marks.setdefault(lado, mk)
    return marks


def _piernas_bridge(symbol: str, snap: dict) -> tuple[dict, dict]:
    """long/short desde igris_posiciones.por_activo[symbol] o piernas globales si coinciden."""
    s = str(symbol or "").upper()
    pos = snap.get("igris_posiciones") or {}
    por = (pos.get("por_activo") or {}).get(s)
    if por:
        return por.get("long") or {}, por.get("short") or {}
    # Fallback: piernas globales solo si el símbolo encaja
    L, S = pos.get("long") or {}, pos.get("short") or {}
    sym_l = str(L.get("symbol") or "").upper()
    sym_s = str(S.get("symbol") or "").upper()
    if sym_l.startswith(s) or sym_s.startswith(s):
        return L, S
    return {}, {}


def desde_estado_vivo(symbol: str, snap: dict | None) -> dict[str, Any]:
    """Extrae AssetDetail desde un snapshot estado_vivo.json (Bridge + pesos + Tank)."""
    from core import igris_manto as im

    snap = snap or {}
    s = str(symbol or "BTC").upper()
    pesos = snap.get("pesos_por_frente") or {}
    fl, fs = im.frentes_bootstrap(s)
    L, S = _piernas_bridge(s, snap)
    marks = _marks_desde_snap(s, snap, fl, fs)

    margen_im = {
        "long": float(L.get("margen_usd") or 0) or 0.0,
        "short": float(S.get("margen_usd") or 0) or 0.0,
    }
    lev_l = L.get("leverage")
    lev_s = S.get("leverage")
    leverage_actual = {
        "long": float(lev_l) if lev_l not in (None, "", 0) else None,
        "short": float(lev_s) if lev_s not in (None, "", 0) else None,
    }
    # No pasar None dentro del dict de forma que .get invente — construir limpio
    lev_kw = {}
    if leverage_actual["long"] is not None:
        lev_kw["long"] = leverage_actual["long"]
    if leverage_actual["short"] is not None:
        lev_kw["short"] = leverage_actual["short"]

    baselines = im.baselines_activo(pesos, s)
    fees = im.fees_activo(pesos, s)

    return construir_asset_detail(
        s,
        pesos=pesos,
        marks=marks,
        igris_bloque=snap.get("igris") or {},
        progresion=snap.get("progresion") or {
            "grado_beru": snap.get("grado_beru"),
            "rango_ejercito": snap.get("rango_ejercito"),
        },
        baselines=baselines,
        fees_paid=fees,
        leverage_actual=lev_kw or None,
        margen_im=margen_im if (margen_im["long"] > 0 or margen_im["short"] > 0) else None,
    )


def catalogar_activos_desde_snap(snap: dict | None) -> list[str]:
    """Activos con masa o en pentiverso — para precomputar Sub-Santuario en Bellion."""
    snap = snap or {}
    bases: set[str] = set()
    for frente in (snap.get("pesos_por_frente") or {}):
        from core import mercado
        bases.add(mercado.activo_de_frente(frente))
    for b in snap.get("activos_pentiverso") or []:
        bases.add(str(b).upper())
    tb = snap.get("ticker_base")
    if tb:
        bases.add(str(tb).upper())
    por = ((snap.get("igris_posiciones") or {}).get("por_activo") or {})
    bases.update(str(k).upper() for k in por)
    return sorted(b for b in bases if b)


def mapa_asset_details(snap: dict | None) -> dict[str, Any]:
    """Precomputa Sub-Santuario por activo (fuente de verdad para el Pergamino)."""
    snap = snap or {}
    return {sym: desde_estado_vivo(sym, snap) for sym in catalogar_activos_desde_snap(snap)}

