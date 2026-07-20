"""Plan de crecimiento — equity Monarca → despliegue del ejército (doctrina 23 v2).

Rangos Aspirante→Chamán anclados al pase de batalla Coliseo
(`migracion/PASE_BATALLA_13_SANTOS.md`, firma Monarca 2026-07-19).
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Literal

import core.config as config
from core import beru_capital as bc

NivelMonarca = Literal[
    "ASPIRANTE",
    "APRENDIZ",
    "BRUJO",
    "CHAMAN",
    "CAPITAN",
    "GENERAL",
    "SENOR_SOMBRAS",
]
BeruTierId = Literal["BERUBBY", "PROTO2", "PROTO1", "PLENO"]

# 13 Santos del Grial (sillas fijas — Coliseo 1.6% malla ×1)
SANTOS_GRIAL: tuple[str, ...] = (
    "MNT", "LINK", "AVAX", "LTC", "HYPE", "BCH", "XRP",
    "SOL", "ETH", "ADA", "AAVE", "FIL", "OP",
)
# Estrella Aspirante — pasos 1–5 del pase
ESTRELLA_ASPIRANTE: tuple[str, ...] = ("ETH", "HYPE", "XRP", "MNT", "LTC")

# Techos acumulados Igris del pase (eq < umbral → ese rango)
ASPIRANTE_TECHO_USD = 123.0
APRENDIZ_TECHO_USD = 411.0
BRUJO_TECHO_USD = 1451.0
CHAMAN_TECHO_USD = 3161.0

# eq < umbral → ese nivel
_NIVELES_MONARCA: tuple[tuple[float, NivelMonarca, list[str] | None, str], ...] = (
    (ASPIRANTE_TECHO_USD, "ASPIRANTE", list(ESTRELLA_ASPIRANTE), "off"),
    (APRENDIZ_TECHO_USD, "APRENDIZ", list(SANTOS_GRIAL), "colchon"),
    (BRUJO_TECHO_USD, "BRUJO", list(SANTOS_GRIAL), "colchon"),
    (CHAMAN_TECHO_USD, "CHAMAN", list(SANTOS_GRIAL), "colchon"),
    (10000.0, "CAPITAN", None, "colchon"),
    (100000.0, "GENERAL", None, "colchon_vip"),
    (float("inf"), "SENOR_SOMBRAS", None, "full"),
)

_TIER_BERU_UMBRALES: tuple[tuple[float, BeruTierId]] = (
    # LEGACY — reemplazado por beru_capital.resolver_activo_y_grado (motor X/A_base)
    (25.0, "BERUBBY"),
    (50.0, "PROTO2"),
    (100.0, "PROTO1"),
    (float("inf"), "PLENO"),
)

_TIER_NOMBRES: dict[str, str] = {
    "BERUBBY": "Beru Aspirante",
    "PROTO2": "Aprendiz",
    "PROTO1": "Guerrero",
    "PLENO": "Comandante",
}

_NIVEL_TITULOS: dict[str, str] = {
    "ASPIRANTE": "Aspirante",
    "APRENDIZ": "Aprendiz",
    "BRUJO": "Brujo",
    "CHAMAN": "Chamán",
    "CAPITAN": "Capitán (Invocador)",
    "GENERAL": "General (Nigromante)",
    "SENOR_SOMBRAS": "Señor de las Sombras",
    # Alias legacy (lecturas antiguas / panel)
    "RECLUTA": "Aprendiz",
    "SOLDADO": "Brujo",
}


def _cfg_float(name: str, default: float) -> float:
    return float(getattr(config, name, default))


def _cfg_int(name: str, default: int) -> int:
    return int(getattr(config, name, default))


def _ruta_hist_equity() -> str:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(ruta_base, "data", "plan_equity_hist.json")


def reserva_pct() -> float:
    """Colchón 5% fijo — slippage + fuel Greed."""
    return _cfg_float("MONARCA_RESERVA_PCT", 0.05)


def concentracion_max_pct() -> float:
    return _cfg_float("MONARCA_CONCENTRACION_MAX_PCT", 0.20)


def margen_objetivo_pct() -> float:
    return _cfg_float("MONARCA_MARGEN_OBJETIVO_PCT", 93.0)


def mega_vip_equity_min_usd() -> float:
    return _cfg_float("MONARCA_MEGA_VIP_EQUITY_MIN", 100.0)


def tier_auto_dias() -> int:
    return _cfg_int("MONARCA_TIER_AUTO_DIAS", 3)


def activo_semilla() -> str:
    return str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH")).upper()


def flota_completa() -> list[str]:
    return list(getattr(config, "ACTIVOS_BERU_FLOTA", []) or ["ETH"])


def barcos_desbloqueados_por_nivel(nivel: str) -> list[str]:
    for _umbral, nom, activos, _greed in _NIVELES_MONARCA:
        if nom == nivel:
            return list(activos) if activos is not None else flota_completa()
    return [activo_semilla()]


def tier_beru_instantaneo(equity_usd: float) -> BeruTierId:
    """Tier Beru desde motor dinámico X/A_base (semilla + cola)."""
    res = bc.resolver_activo_y_grado(equity_usd)
    grado = res.get("grado", "BLOQUEADO")
    if grado == "BLOQUEADO":
        return "BERUBBY"
    tid = res.get("tier_id") or bc.tier_id_desde_grado(grado)
    if tid in ("BERUBBY", "PROTO2", "PROTO1", "PLENO"):
        return tid  # type: ignore[return-value]
    return "PROTO1"


def tier_beru_nombre(tier_id: str) -> str:
    return _TIER_NOMBRES.get(tier_id.upper(), tier_id)


def nivel_titulo(nivel: str) -> str:
    return _NIVEL_TITULOS.get(nivel, nivel)


def techos_pase_batalla() -> dict[str, float]:
    """Techos equity del pase 13 Santos (doctrina 23 v2)."""
    return {
        "aspirante_usd": ASPIRANTE_TECHO_USD,
        "aprendiz_usd": APRENDIZ_TECHO_USD,
        "brujo_usd": BRUJO_TECHO_USD,
        "chaman_usd": CHAMAN_TECHO_USD,
        "meta_13_mariscales_usd": CHAMAN_TECHO_USD,
    }


def _nivel_y_barcos_raw(equity_usd: float) -> tuple[str, list[str]]:
    """Solo umbral de cuenta → nivel + lista doctrinal (sin motor Beru)."""
    eq = max(0.0, float(equity_usd))
    for umbral, nom, acts, _greed in _NIVELES_MONARCA:
        if eq < umbral:
            barcos = list(acts) if acts is not None else flota_completa()
            return nom, [a.upper() for a in barcos]
    return "SENOR_SOMBRAS", [a.upper() for a in flota_completa()]


def activos_permitidos(equity_usd: float) -> list[str]:
    """Barcos desbloqueados por rango ∩ flota Beru."""
    _nivel, permitidos = _nivel_y_barcos_raw(equity_usd)
    flota = {a.upper() for a in flota_completa()}
    out = [a for a in permitidos if a in flota]
    if out:
        return out
    return [a for a in ESTRELLA_ASPIRANTE if a in flota] or list(ESTRELLA_ASPIRANTE)


def activo_manto_preferido(equity_usd: float) -> str:
    """Preferido Igris: primer Santo de la estrella aún permitido."""
    permitidos = activos_permitidos(equity_usd)
    for pref in ESTRELLA_ASPIRANTE:
        if pref in permitidos:
            return pref
    return permitidos[0] if permitidos else activo_semilla()


def rank_gate_activo() -> bool:
    return bool(getattr(config, "MONARCA_RANK_GATE", True))


def equity_min_por_caza(asset: str | None = None, tier_id: str | None = None) -> float:
    a = (asset or activo_semilla()).upper()
    tid = tier_id or tier_beru_instantaneo(0)
    cola = bc.cola_activos_con_a_base()
    ab = 0
    for fila in cola:
        if fila["activo"] == a:
            ab = fila["A_base"]
            break
    return bc.equity_minima_recomendada(a, tier_id=tid, a_base=ab)


def equity_min_por_pez(asset: str | None = None, tier_id: str | None = None) -> float:
    """Alias legacy panel."""
    return equity_min_por_caza(asset, tier_id)


def registrar_muestra_equity(equity_usd: float) -> dict[str, Any]:
    """Una muestra por día UTC — base para tier auto 3 días."""
    eq = round(max(0.0, float(equity_usd)), 2)
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ruta = _ruta_hist_equity()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    data: dict[str, Any] = {"muestras": []}
    if os.path.exists(ruta):
        try:
            with open(ruta, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {"muestras": []}
    muestras: list[dict] = list(data.get("muestras") or [])
    if muestras and muestras[-1].get("fecha") == hoy:
        muestras[-1]["equity_usd"] = eq
        muestras[-1]["ts"] = time.time()
    else:
        muestras.append({"fecha": hoy, "equity_usd": eq, "ts": time.time()})
    data["muestras"] = muestras[-60:]
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    if os.path.exists(ruta):
        os.remove(ruta)
    os.rename(tmp, ruta)
    return data


def ultimas_muestras_equity(n: int | None = None) -> list[float]:
    ruta = _ruta_hist_equity()
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    vals = [float(m["equity_usd"]) for m in (data.get("muestras") or []) if "equity_usd" in m]
    if n is not None:
        return vals[-n:]
    return vals


def tier_beru_confirmado(equity_usd: float | None = None) -> BeruTierId:
    """Tier Beru con histéresis: promedio N días si hay historial."""
    dias = tier_auto_dias()
    muestras = ultimas_muestras_equity(dias)
    if len(muestras) >= dias:
        promedio = sum(muestras) / len(muestras)
        return tier_beru_instantaneo(promedio)
    if equity_usd is not None:
        return tier_beru_instantaneo(equity_usd)
    if muestras:
        return tier_beru_instantaneo(muestras[-1])
    return tier_beru_instantaneo(0)


def tier_beru_para_cuenta(equity_usd: float) -> BeruTierId:
    if getattr(config, "MONARCA_NIVEL_AUTO", False):
        registrar_muestra_equity(equity_usd)
        return tier_beru_confirmado(equity_usd)
    return tier_beru_instantaneo(equity_usd)


def nivel_por_equity(equity_usd: float) -> dict[str, Any]:
    """Rango Monarca + cazas desbloqueadas + tier Beru sugerido."""
    eq = max(0.0, float(equity_usd))
    nivel: NivelMonarca = "SENOR_SOMBRAS"
    activos: list[str] = flota_completa()
    greed_modo = "full"

    for _umbral, nom, acts, greed in _NIVELES_MONARCA:
        if eq < _umbral:
            nivel, activos, greed_modo = nom, list(acts) if acts else flota_completa(), greed
            break

    tier_inst = tier_beru_instantaneo(eq)
    tier_aplicado = tier_beru_para_cuenta(eq) if getattr(config, "MONARCA_NIVEL_AUTO", False) else tier_inst
    # Motor Beru: cola filtrada por pase si candado activo
    if rank_gate_activo():
        motor = bc.resolver_activo_y_grado(eq, activos=activos)
    else:
        motor = bc.resolver_activo_y_grado(eq)
    res = reserva_pct()
    eq_deploy = eq * (1.0 - res)
    min_caza = equity_min_por_caza(tier_id=tier_aplicado)
    cazas_por_capital = int(eq_deploy // min_caza) if min_caza > 0 else 0
    cazas_max = min(len(activos), max(1, cazas_por_capital)) if eq > 0 and activos else 0
    piso_soldado = float((motor.get("rangos") or {}).get("SOLDADO", (0, 0))[0] or 0)
    if eq < piso_soldado:
        cazas_max = 0

    manto_pref = activo_manto_preferido(eq) if rank_gate_activo() else activo_semilla()

    return {
        "equity_usd": round(eq, 2),
        "nivel": nivel,
        "nivel_titulo": nivel_titulo(nivel),
        "pase_techos": techos_pase_batalla(),
        "santos_grial": list(SANTOS_GRIAL),
        "estrella_aspirante": list(ESTRELLA_ASPIRANTE),
        "cazas_desbloqueadas": activos,
        "cazas_max": cazas_max,
        "rank_gate": rank_gate_activo(),
        "activo_manto_preferido": manto_pref,
        "tier_instantaneo": tier_inst,
        "tier_aplicado": tier_aplicado,
        "tier_nombre": tier_beru_nombre(tier_aplicado),
        "tier_default": tier_aplicado,
        "grado_beru": motor.get("grado"),
        "activo_motor": motor.get("activo"),
        "costo_base_X": motor.get("X"),
        "A_base": motor.get("A_base"),
        "rangos_motor": motor.get("rangos"),
        "equity_min_por_caza_usd": round(min_caza, 2),
        "equity_min_por_pez_usd": round(min_caza, 2),
        "reserva_pct": res,
        "reserva_usd": round(eq * res, 2),
        "colchon_usd": round(eq * res, 2),
        "equity_desplegable_usd": round(eq_deploy, 2),
        "greed_modo": greed_modo,
        "mega_vip_desde_usd": mega_vip_equity_min_usd(),
        "mega_vip_activo": eq >= mega_vip_equity_min_usd(),
        "margen_objetivo_pct": margen_objetivo_pct(),
        "activo_semilla": activo_semilla(),
        "tier_auto_dias": tier_auto_dias(),
        "nivel_auto": bool(getattr(config, "MONARCA_NIVEL_AUTO", False)),
        "peces_max": cazas_max,
        "peces_techo_nivel": len(activos),
    }


def presupuesto_objetivo(equity_usd: float) -> dict[str, Any]:
    """95% manto Igris · 5% colchón (Greed). Beru no consume margen de apalancamiento."""
    _ = max(0.0, float(equity_usd))
    res = reserva_pct()
    return {
        "manto_pct": round(1.0 - res, 4),
        "colchon_pct": res,
        "beru_pct": 0.0,
        "reserva_pct": res,
        "greed_por_mision_pct": res,
        "margen_objetivo_pct": margen_objetivo_pct(),
        "nota": "95% manto Igris · 5% colchón slippage+Greed · Beru intercambia spot",
    }


def prioridad_convivencia() -> list[str]:
    return [
        "BERU_COSECHA_NEGOCIANDO",
        "BERU_NUEVA_CAZA",
        "IGRIS_BANDA_DELTA",
        "GREED_VIVA_MARGEN_OK",
    ]


def reparto_botin_greed(ganancia_neta_usd: float) -> dict[str, float]:
    """Victorias Greed: mitad retiene Greed, mitad tesorería ejército."""
    g = max(0.0, float(ganancia_neta_usd))
    mitad = g * 0.5
    return {
        "ganancia_neta_usd": round(g, 2),
        "greed_retiene_usd": round(mitad, 2),
        "ejercito_usd": round(mitad, 2),
    }


def reparto_botin_propuesto(ganancia_neta_usd: float) -> dict[str, float]:
    """Botín general → tesorería conjunta."""
    g = max(0.0, float(ganancia_neta_usd))
    return {
        "ganancia_neta_usd": round(g, 2),
        "tesoreria_ejercito_usd": round(g, 2),
        "greed_retiene_usd": 0.0,
    }


def piso_abandono_tier() -> str:
    return "BERUBBY"


def doctrina_multi_beru() -> dict[str, str]:
    return {
        "regla": "1 caza activa por activo",
        "relevo": "COSECHA → generación +1",
        "colision": "fusión → super Beru",
        "piso_abandono": f"{piso_abandono_tier()} ({tier_beru_nombre('BERUBBY')})",
    }


def resumen_plan(equity_usd: float) -> dict[str, Any]:
    nv = nivel_por_equity(equity_usd)
    from core import pase_director as pd
    director = pd.resumen_director(equity_usd) if pd.director_activo() else {"activo": False}
    return {
        **nv,
        "presupuesto": presupuesto_objetivo(equity_usd),
        "concentracion_max_pct": concentracion_max_pct(),
        "prioridad_convivencia": prioridad_convivencia(),
        "doctrina_multi_beru": doctrina_multi_beru(),
        "greed_riesgo_max_pct_cuenta": float(getattr(config, "GREED_RIESGO_MAX_PCT_CUENTA", 0.01)),
        "ultimas_muestras_equity": ultimas_muestras_equity(5),
        "pase_director": director,
    }
