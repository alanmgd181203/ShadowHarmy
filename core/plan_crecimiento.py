"""Plan de crecimiento — equity Monarca → despliegue del ejército (doctrina 23 v1)."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Literal

import core.config as config
from core import beru_capital as bc

NivelMonarca = Literal[
    "ASPIRANTE", "RECLUTA", "SOLDADO", "CAPITAN", "GENERAL", "SENOR_SOMBRAS",
]
BeruTierId = Literal["BERUBBY", "PROTO2", "PROTO1", "PLENO"]

# Umbrales equity UTA (USD) — Monarca 2026-07-06
# eq < umbral → ese rango (Recluta desde $100, Soldado desde $500, …)
_NIVELES_MONARCA: tuple[tuple[float, NivelMonarca, list[str] | None, str]] = (
    (100.0, "ASPIRANTE", ["ETH"], "off"),
    (500.0, "RECLUTA", ["ETH"], "colchon"),
    (2000.0, "SOLDADO", ["ETH", "SOL", "FIL", "LTC"], "colchon"),
    (10000.0, "CAPITAN", None, "colchon"),
    (100000.0, "GENERAL", None, "colchon_vip"),
    (float("inf"), "SENOR_SOMBRAS", None, "full"),
)

_TIER_BERU_UMBRALES: tuple[tuple[float, BeruTierId]] = (
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
    "RECLUTA": "Recluta (Aprendiz de brujo)",
    "SOLDADO": "Soldado (Chamán)",
    "CAPITAN": "Capitán (Invocador)",
    "GENERAL": "General (Nigromante)",
    "SENOR_SOMBRAS": "Señor de las Sombras",
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
    eq = max(0.0, float(equity_usd))
    tid: BeruTierId = "PLENO"
    for umbral, tier_id in _TIER_BERU_UMBRALES:
        if eq < umbral:
            tid = tier_id
            break
    return tid


def tier_beru_nombre(tier_id: str) -> str:
    return _TIER_NOMBRES.get(tier_id.upper(), tier_id)


def nivel_titulo(nivel: str) -> str:
    return _NIVEL_TITULOS.get(nivel, nivel)


def equity_min_por_caza(asset: str | None = None, tier_id: str | None = None) -> float:
    a = (asset or activo_semilla()).upper()
    tid = tier_id or tier_beru_instantaneo(0)
    return bc.equity_minima_recomendada(a, tier_id=tid)


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
    res = reserva_pct()
    eq_deploy = eq * (1.0 - res)
    min_caza = equity_min_por_caza(tier_id=tier_aplicado)
    cazas_por_capital = int(eq_deploy // min_caza) if min_caza > 0 else 0
    cazas_max = min(len(activos), max(1, cazas_por_capital)) if eq > 0 and activos else 0
    if eq < 25:
        cazas_max = 1 if eq > 0 else 0

    return {
        "equity_usd": round(eq, 2),
        "nivel": nivel,
        "nivel_titulo": nivel_titulo(nivel),
        "cazas_desbloqueadas": activos,
        "cazas_max": cazas_max,
        "tier_instantaneo": tier_inst,
        "tier_aplicado": tier_aplicado,
        "tier_nombre": tier_beru_nombre(tier_aplicado),
        "tier_default": tier_aplicado,
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
    return {
        **nv,
        "presupuesto": presupuesto_objetivo(equity_usd),
        "concentracion_max_pct": concentracion_max_pct(),
        "prioridad_convivencia": prioridad_convivencia(),
        "doctrina_multi_beru": doctrina_multi_beru(),
        "greed_riesgo_max_pct_cuenta": float(getattr(config, "GREED_RIESGO_MAX_PCT_CUENTA", 0.01)),
        "ultimas_muestras_equity": ultimas_muestras_equity(5),
    }
