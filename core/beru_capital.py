"""Beru — motor dinámico de capital (5 Reglas Universales del Monarca).

Cálculo usa apalancamiento PROMEDIO (proyección de rangos).
Ejecución en exchange: Igris usa el MÁXIMO por contrato (inverse/lineal).

Ley de Fricción (esfuerzo de mercado para extraer G_min):
  Soldado 0.8% · Capitán 0.4% · General 0.2% · Mariscal 0.1%.

Cada tope de grado se calcula DIRECTO con su fricción (sin ×2/×4/×8 sobre X).
"""
from __future__ import annotations

import math
from typing import Any, Literal

import core.config as config
from core import beru_tier

GradoBeru = Literal["BLOQUEADO", "SOLDADO", "CAPITAN", "GENERAL", "MARISCAL"]

# Fricción de mercado por grado (fracción)
FRICCION_POR_GRADO: dict[str, float] = {
    "SOLDADO": 0.008,
    "CAPITAN": 0.004,
    "GENERAL": 0.002,
    "MARISCAL": 0.001,
}

# Alias legacy tiers ↔ grados fricción
_GRADO_A_TIER = {
    "SOLDADO": "BERUBBY",
    "CAPITAN": "PROTO2",
    "GENERAL": "PROTO1",
    "MARISCAL": "PLENO",
}
_TIER_A_GRADO = {v: k for k, v in _GRADO_A_TIER.items()}


def apalancamiento_linear_max(asset: str) -> float:
    mp = getattr(config, "MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET", {}) or {}
    default = float(getattr(config, "MANTO_LEVERAGE_DEFAULT", 25.0))
    return float(mp.get(asset.upper(), default))


def apalancamiento_inverse_max(asset: str) -> float:
    mp = getattr(config, "MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET", {}) or {}
    default = float(getattr(config, "MANTO_LEVERAGE_DEFAULT", 25.0))
    return float(mp.get(asset.upper(), default))


def apalancamiento_manto_promedio(asset: str) -> float:
    """Cálculo de rangos — promedio inverso + lineal."""
    return (apalancamiento_linear_max(asset) + apalancamiento_inverse_max(asset)) / 2.0


def apalancamiento_ejecucion(frente_o_asset: str, category: str | None = None) -> float:
    """Ejecución Igris — máximo del contrato concreto."""
    a = frente_o_asset.upper().replace("USDT_LINEAL", "").replace("USDC_LINEAL", "")
    a = a.replace("USD_INVERSE", "").replace("USDT_SPOT", "").replace("USDC_SPOT", "")
    if not a or a == frente_o_asset.upper():
        a = frente_o_asset.upper()
    cat = (category or "").lower()
    if "inverse" in cat or frente_o_asset.upper().endswith("_INVERSE"):
        return apalancamiento_inverse_max(a)
    if "linear" in cat or "LINEAL" in frente_o_asset.upper():
        return apalancamiento_linear_max(a)
    return max(apalancamiento_linear_max(a), apalancamiento_inverse_max(a))


def g_min_usd(asset: str) -> float:
    """G_min Bybit por Santo — archivo sync (spot USDT → linear → piso/default)."""
    from core import g_min as gm

    return gm.g_min_usd(asset)


def friccion_soldado_pct() -> float:
    return float(getattr(config, "BERU_FRICCION_SOLDADO_PCT", FRICCION_POR_GRADO["SOLDADO"]))


def friccion_grado_pct(grado: str) -> float:
    g = str(grado).upper()
    if g in FRICCION_POR_GRADO:
        # Soldado configurable; resto derivados ×½ cada salto
        if g == "SOLDADO":
            return friccion_soldado_pct()
        base = friccion_soldado_pct()
        # 0.8 → 0.4 → 0.2 → 0.1
        escala = {"CAPITAN": 2, "GENERAL": 4, "MARISCAL": 8}[g]
        return base / escala
    return friccion_soldado_pct()


def colchon_tusk_pct() -> float:
    """Parte del capital que NO es margen del volumen base (5% → margen = 95%)."""
    return float(getattr(config, "MONARCA_RESERVA_PCT", 0.05))


def notional_por_pierna_para_friccion(asset: str, friccion: float) -> float:
    """Notional por pierna para que esa fricción extraiga G_min."""
    g = g_min_usd(asset)
    f = float(friccion)
    if f <= 0:
        return 0.0
    return g / f


def notional_por_pierna_base(asset: str) -> float:
    """Notional por pierna para fricción Soldado (0.8%) = G_min."""
    return notional_por_pierna_para_friccion(asset, friccion_soldado_pct())


def notional_por_pierna_grado(asset: str, grado: str) -> float:
    """Notional por pierna L o S para el grado (Soldado…Mariscal)."""
    g = str(grado or "SOLDADO").upper()
    if g not in FRICCION_POR_GRADO:
        g = "SOLDADO"
    return notional_por_pierna_para_friccion(asset, friccion_grado_pct(g))


def notional_manto_ls_grado(asset: str, grado: str) -> float:
    """Meta nocional L+S del manto para ese grado (2 × pierna)."""
    return 2.0 * notional_por_pierna_grado(asset, grado)


def margen_bidireccional_para_friccion(asset: str, friccion: float) -> float:
    """Margen L+S = 2 × (G_min / fricción) / apalancamiento."""
    lev = max(apalancamiento_manto_promedio(asset), 1.0)
    return 2.0 * notional_por_pierna_para_friccion(asset, friccion) / lev


def margen_volumen_base(asset: str) -> float:
    """Margen L+S del Volumen Base Soldado (antes de reserva 5%)."""
    return margen_bidireccional_para_friccion(asset, friccion_soldado_pct())


def capital_requerido_exacto(asset: str, friccion: float) -> float:
    """capital = margen_LS / 0.95  (reserva Tusk ≥5%)."""
    margen = margen_bidireccional_para_friccion(asset, friccion)
    denom = max(1.0 - colchon_tusk_pct(), 1e-9)
    return margen / denom


def _redondeo_grado(capital: float, *, modo: str) -> int:
    """Soldado: ceil (seguridad). Topes Capitán/General/Mariscal: round."""
    c = float(capital)
    if modo == "ceil":
        return max(1, int(math.ceil(c - 1e-12)))
    return max(1, int(round(c)))


def costo_grado(asset: str, grado: str) -> int:
    """Capital entero del grado — fricción propia, sin escalares sobre X."""
    g = str(grado).upper()
    fric = friccion_grado_pct(g)
    exacto = capital_requerido_exacto(asset, fric)
    modo = "ceil" if g == "SOLDADO" else "round"
    return _redondeo_grado(exacto, modo=modo)


def costo_base_x(asset: str) -> int:
    """Regla 4 — X = capital Soldado (fricción 0.8%, ceil)."""
    return costo_grado(asset, "SOLDADO")


def rangos_activo(asset: str, a_base: float | int = 0) -> dict[str, Any]:
    """Rangos por fricción independiente (prohibido ×2/×4/×8 sobre X)."""
    ab = int(a_base)
    x = costo_grado(asset, "SOLDADO")
    tope_c = costo_grado(asset, "CAPITAN")
    tope_g = costo_grado(asset, "GENERAL")
    tope_m = costo_grado(asset, "MARISCAL")

    # Garantizar monotonía tras redondeos independientes
    tope_c = max(tope_c, x)
    tope_g = max(tope_g, tope_c)
    tope_m = max(tope_m, tope_g)

    mariscal = ab + tope_m
    return {
        "activo": asset.upper(),
        "X": x,
        "A_base": ab,
        "G_min": g_min_usd(asset),
        "lev_promedio": round(apalancamiento_manto_promedio(asset), 2),
        "margen_volumen_base_usd": round(margen_volumen_base(asset), 4),
        "reserva_garantizada_pct": round(colchon_tusk_pct() * 100, 2),
        "costos_friccion": {
            "SOLDADO": x,
            "CAPITAN": tope_c,
            "GENERAL": tope_g,
            "MARISCAL": tope_m,
        },
        "SOLDADO": (ab + x, ab + tope_c - 1),
        "CAPITAN": (ab + tope_c, ab + tope_g - 1),
        "GENERAL": (ab + tope_g, ab + tope_m - 1),
        "MARISCAL": mariscal,
        "A_base_siguiente": mariscal,
        "friccion": {
            "SOLDADO": friccion_grado_pct("SOLDADO") * 100,
            "CAPITAN": friccion_grado_pct("CAPITAN") * 100,
            "GENERAL": friccion_grado_pct("GENERAL") * 100,
            "MARISCAL": friccion_grado_pct("MARISCAL") * 100,
        },
        "friccion_soldado_pct": friccion_grado_pct("SOLDADO") * 100,
    }


def grado_en_rango(equity_usd: float, asset: str, a_base: float | int = 0) -> GradoBeru:
    eq = float(equity_usd)
    r = rangos_activo(asset, a_base)
    lo_s, hi_s = r["SOLDADO"]
    lo_c, hi_c = r["CAPITAN"]
    lo_g, hi_g = r["GENERAL"]
    mar = r["MARISCAL"]
    if eq < lo_s:
        return "BLOQUEADO"
    if lo_s <= eq <= hi_s:
        return "SOLDADO"
    if lo_c <= eq <= hi_c:
        return "CAPITAN"
    if lo_g <= eq <= hi_g:
        return "GENERAL"
    if eq >= mar:
        return "MARISCAL"
    # hueco teórico entre hi_g y mar — tratar como GENERAL hasta graduación exacta
    return "GENERAL"


def tier_id_desde_grado(grado: str) -> str:
    return _GRADO_A_TIER.get(grado.upper(), "PROTO1")


def grado_desde_tier(tier_id: str) -> str:
    return _TIER_A_GRADO.get(str(tier_id).upper(), "GENERAL")


def cola_activos_con_a_base(
    activos: list[str] | None = None,
    a_base_inicial: float | int = 0,
) -> list[dict[str, Any]]:
    """Encadena A_base: graduación Mariscal de uno = A_base del siguiente."""
    catalogo = activos or list(getattr(config, "ACTIVOS_BERU_FLOTA", []) or ["ETH"])
    ab = int(a_base_inicial)
    out: list[dict[str, Any]] = []
    for a in catalogo:
        fila = rangos_activo(a, ab)
        out.append(fila)
        ab = int(fila["A_base_siguiente"])
    return out


def resolver_activo_y_grado(
    equity_usd: float,
    activos: list[str] | None = None,
) -> dict[str, Any]:
    """Dado equity, encuentra activo activo en la cola y su grado Beru."""
    eq = max(0.0, float(equity_usd))
    cola = cola_activos_con_a_base(activos)
    if not cola:
        return {"grado": "BLOQUEADO", "activo": None, "X": 0, "A_base": 0}

    # Por defecto: primer activo cuyo Mariscal aún no se superó, o el último
    elegido = cola[0]
    for fila in cola:
        if eq < fila["MARISCAL"] or eq < fila["SOLDADO"][0]:
            # si aún no alcanza Soldado de este activo, puede ser el anterior graduado
            if eq < fila["SOLDADO"][0] and fila is not cola[0]:
                break
            elegido = fila
            if eq < fila["MARISCAL"]:
                break
        elegido = fila

    # Si equity está antes del Soldado del primero → bloqueado
    if eq < cola[0]["SOLDADO"][0]:
        return {
            "grado": "BLOQUEADO",
            "activo": cola[0]["activo"],
            "X": cola[0]["X"],
            "A_base": cola[0]["A_base"],
            "rangos": cola[0],
            "cola": cola,
        }

    grado = grado_en_rango(eq, elegido["activo"], elegido["A_base"])
    return {
        "grado": grado,
        "activo": elegido["activo"],
        "X": elegido["X"],
        "A_base": elegido["A_base"],
        "rangos": elegido,
        "cola": cola,
        "tier_id": tier_id_desde_grado(grado) if grado != "BLOQUEADO" else "BERUBBY",
    }


def telemetria_progresion(equity_usd: float) -> dict[str, Any]:
    """Snapshot para panel / estado_vivo — grado, X, rango ejército, inanición."""
    from core import plan_crecimiento as pc

    eq = max(0.0, float(equity_usd))
    motor = resolver_activo_y_grado(eq)
    plan = pc.nivel_por_equity(eq)
    cola0 = (motor.get("cola") or cola_activos_con_a_base())[:1]
    piso_soldado = float(cola0[0]["SOLDADO"][0]) if cola0 else float(motor.get("X") or 0)
    x = int(motor.get("X") or (cola0[0]["X"] if cola0 else 0))

    if eq <= 0 or eq < piso_soldado:
        rango_id = "inanicion"
        rango_titulo = "Nivel 0 / Inanición"
        grado = "BLOQUEADO"
    else:
        rango_id = str(plan.get("nivel", "ASPIRANTE")).lower()
        rango_titulo = str(plan.get("nivel_titulo") or plan.get("nivel") or "—")
        grado = str(motor.get("grado") or "BLOQUEADO")

    friccion = None
    if grado in FRICCION_POR_GRADO:
        friccion = round(friccion_grado_pct(grado) * 100, 2)

    return {
        "equity_usd": round(eq, 2),
        "grado_beru": grado,
        "costo_base_X": x,
        "A_base": motor.get("A_base", 0),
        "activo_motor": motor.get("activo"),
        "G_min": g_min_usd(str(motor.get("activo") or getattr(config, "BERU_ACTIVO_SEMILLA", "ETH"))),
        "rango_ejercito": rango_titulo,
        "rango_ejercito_id": rango_id,
        "piso_soldado_usd": piso_soldado,
        "rango_inanicion": [0, max(0, piso_soldado - 1)],
        "friccion_pct": friccion,
        "rangos_activo": motor.get("rangos"),
        "tier_id": (
            motor.get("tier_id") or tier_id_desde_grado(grado)
        ) if grado != "BLOQUEADO" else "BERUBBY",
    }


# --- API legacy (compat panel / smokes) ---

def notional_por_pierna_objetivo() -> float:
    """Legacy — preferir notional_por_pierna_base(activo)."""
    semilla = str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH")).upper()
    return notional_por_pierna_base(semilla)


def margen_manto_pleno(asset: str) -> float:
    """Margen L+S al esfuerzo Mariscal (fricción 0.1%)."""
    return round(margen_bidireccional_para_friccion(asset, friccion_grado_pct("MARISCAL")), 2)


def margen_manto_por_tier(asset: str, tier_id: str | None = None) -> float:
    tier = beru_tier.tier_por_id(tier_id)
    # escala_manto 8/4/2/1 ↔ Soldado…Mariscal
    return round(margen_manto_pleno(asset) / max(tier.escala_manto, 1.0), 2)


def margen_manto_beru_100(asset: str) -> float:
    return margen_manto_por_tier(asset, getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))


def pnl_por_1pct_con_margen(asset: str, margen_manto_usd: float) -> float:
    lev = max(apalancamiento_manto_promedio(asset), 1.0)
    por_pierna = max(margen_manto_usd, 0) / 2.0
    notional = por_pierna * lev
    return round(notional * 0.01, 2)


def equity_minima_recomendada(
    asset: str,
    *,
    tier_id: str | None = None,
    incluir_spot_beru: bool = False,
    a_base: float | int = 0,
) -> float:
    """Piso Soldado = A_base + X."""
    r = rangos_activo(asset, a_base)
    base = float(r["SOLDADO"][0])
    if incluir_spot_beru:
        base += float(getattr(config, "BERU_SPOT_COLCHON_USD", 0.0))
    # Si piden tier concreto, usar piso de ese grado
    if tier_id:
        grado = grado_desde_tier(tier_id)
        if grado == "CAPITAN":
            base = float(r["CAPITAN"][0])
        elif grado == "GENERAL":
            base = float(r["GENERAL"][0])
        elif grado == "MARISCAL":
            base = float(r["MARISCAL"])
    return round(base, 2)


def fila_capital(asset: str, tier_id: str | None = None, a_base: float | int = 0) -> dict[str, Any]:
    tid = tier_id or str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))
    tier = beru_tier.tier_por_id(tid)
    r = rangos_activo(asset, a_base)
    return {
        "activo": asset.upper(),
        "tier": tier.id,
        "tier_nombre": tier.nombre,
        "grado": grado_desde_tier(tid),
        "X": r["X"],
        "A_base": r["A_base"],
        "rangos": {
            "SOLDADO": r["SOLDADO"],
            "CAPITAN": r["CAPITAN"],
            "GENERAL": r["GENERAL"],
            "MARISCAL": r["MARISCAL"],
        },
        "lev_promedio": r["lev_promedio"],
        "G_min": r["G_min"],
        "margen_manto_pleno_usd": margen_manto_pleno(asset),
        "margen_manto_tier_usd": margen_manto_por_tier(asset, tid),
        "equity_min_usd": equity_minima_recomendada(asset, tier_id=tid, a_base=a_base),
        "es_semilla": asset.upper() == str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH")).upper(),
    }


def tabla_flota_beru(activos: list[str] | None = None) -> list[dict[str, Any]]:
    cola = cola_activos_con_a_base(activos)
    out: list[dict[str, Any]] = []
    for fila in cola:
        for tid in beru_tier.BERU_TIERS:
            out.append(fila_capital(fila["activo"], tid, a_base=fila["A_base"]))
    return out


def resumen_capital() -> dict[str, Any]:
    from core import g_min as gm

    semilla = str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH")).upper()
    cola = cola_activos_con_a_base()
    sem = next((c for c in cola if c["activo"] == semilla), cola[0] if cola else rangos_activo(semilla))
    det = gm.detalle_g_min(semilla)
    g_sem = float(sem.get("G_min") if isinstance(sem, dict) else g_min_usd(semilla))
    return {
        "activo_semilla": semilla,
        "motor": "5_REGLAS_UNIVERSALES",
        "G_min_default": float(getattr(config, "G_MIN_USD_DEFAULT", 1.0)),
        "G_min_piso": float(getattr(config, "G_MIN_USD_PISO", 1.0)),
        "G_min_semilla": g_sem,
        "G_min_detalle_semilla": det,
        "pleno_pnl_1pct_como_10x_gmin": round(10.0 * g_sem, 4),
        "friccion_soldado_pct": friccion_soldado_pct() * 100,
        "colchon_tusk_pct": colchon_tusk_pct() * 100,
        "semilla_rangos": sem,
        "semilla": {**(sem if isinstance(sem, dict) else {}), "G_min": g_sem},
        "cola_graduacion": cola,
        "tiers": beru_tier.resumen_tiers(),
        "capitanes": {
            "ansiedad_vacio_pct": float(getattr(config, "BERU_VACIO_ANSIEDAD", 0.012)) * 100,
            "normal_vacio_pct": float(getattr(config, "BERU_VACIO_NORMAL", 0.016)) * 100,
        },
        "nota_pase": "ranking/pase NO regenerado — pendiente tras mínimos reales + análisis Monarca",
    }


def construir_greed_leverage_por_frente() -> dict[str, float]:
    out: dict[str, float] = {}
    activos = set(getattr(config, "MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET", {}) or {})
    activos |= set(getattr(config, "MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET", {}) or {})
    for a in activos:
        out[f"{a}USDT_LINEAL"] = apalancamiento_linear_max(a)
        out[f"{a}USDC_LINEAL"] = apalancamiento_linear_max(a)
        out[f"{a}USD_INVERSE"] = apalancamiento_inverse_max(a)
    return out
