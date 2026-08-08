"""G_min por Santo — peaje real Bybit (spot USDT → linear → piso).

Fuente limpia: data/bybit_minimos_orden.json (sync).
Respaldo: data/bybit_parametros_mercado.json (Jess/Kaiser).
Config legado G_MIN_USD_BY_ASSET solo si el Santo no aparece en archivo.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import core.config as config

ROOT = Path(__file__).resolve().parents[1]
PATH_MINIMOS = ROOT / "data" / "bybit_minimos_orden.json"
PATH_PARAMETROS = ROOT / "data" / "bybit_parametros_mercado.json"

_cache: dict[str, Any] = {
    "g_by_asset": {},
    "detalle": {},
    "mtime_key": None,
    "loaded_at": 0.0,
    "fuente": None,
}


def _piso() -> float:
    return float(getattr(config, "G_MIN_USD_PISO", 1.0))


def _default() -> float:
    return float(getattr(config, "G_MIN_USD_DEFAULT", 1.0))


def _f(x: Any, default: float | None = None) -> float | None:
    if x is None:
        return default
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if v <= 0:
        return default
    return v


def _min_usd_de_pierna(pierna: dict[str, Any] | None) -> float | None:
    if not pierna or not isinstance(pierna, dict):
        return None
    for key in ("min_usd_est", "minNotionalValue", "minNotional", "minOrderAmt", "min_order_amt"):
        v = _f(pierna.get(key))
        if v is not None:
            return v
    qty = _f(pierna.get("minOrderQty") or pierna.get("minQty"))
    px = _f(pierna.get("precio_ref"))
    if qty is not None and px is not None:
        return round(qty * px, 6)
    return None


def _g_min_desde_fila(fila: dict[str, Any]) -> tuple[float | None, str]:
    """Prioridad doctrinal: spot USDT → linear → inverse."""
    if fila.get("G_min") is not None:
        g = _f(fila.get("G_min"))
        if g is not None:
            return g, str(fila.get("G_min_fuente") or "archivo_G_min")
    spot = _min_usd_de_pierna(fila.get("spot_usdt") if isinstance(fila.get("spot_usdt"), dict) else None)
    if spot is not None:
        return spot, "spot_usdt"
    lin = _min_usd_de_pierna(fila.get("linear") if isinstance(fila.get("linear"), dict) else None)
    if lin is not None:
        return lin, "linear"
    inv = _min_usd_de_pierna(fila.get("inverse") if isinstance(fila.get("inverse"), dict) else None)
    if inv is not None:
        return inv, "inverse"
    return None, "sin_pierna"


def _mtime_key() -> tuple:
    parts = []
    for p in (PATH_MINIMOS, PATH_PARAMETROS):
        try:
            parts.append((str(p), p.stat().st_mtime_ns if p.is_file() else 0))
        except OSError:
            parts.append((str(p), 0))
    return tuple(parts)


def _cargar_activos(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    act = raw.get("activos") if isinstance(raw, dict) else None
    return act if isinstance(act, dict) else None


def _rellenar_desde(activos: dict[str, Any], etiqueta: str) -> tuple[dict[str, float], dict[str, Any]]:
    g_map: dict[str, float] = {}
    detalle: dict[str, Any] = {}
    for base, fila in activos.items():
        b = str(base or "").upper()
        if not b or not isinstance(fila, dict):
            continue
        bruto, fuente_leg = _g_min_desde_fila(fila)
        if bruto is None:
            continue
        g = max(bruto, _piso())
        g_map[b] = g
        detalle[b] = {
            "G_min": g,
            "bruto": bruto,
            "fuente_pierna": fuente_leg,
            "archivo": etiqueta,
            "piso": _piso(),
        }
    return g_map, detalle


def recargar(*, forzar: bool = False) -> dict[str, float]:
    """Lee archivo(s) y rellena caché G_min por base. minimos_orden gana sobre parametros."""
    key = _mtime_key()
    if not forzar and _cache["mtime_key"] == key and _cache["g_by_asset"] is not None:
        return dict(_cache["g_by_asset"])

    g_map: dict[str, float] = {}
    detalle: dict[str, Any] = {}
    fuente_global: str | None = None

    activos_min = _cargar_activos(PATH_MINIMOS)
    if activos_min:
        g_map, detalle = _rellenar_desde(activos_min, "bybit_minimos_orden")
        fuente_global = "bybit_minimos_orden"
    else:
        activos_par = _cargar_activos(PATH_PARAMETROS)
        if activos_par:
            g_map, detalle = _rellenar_desde(activos_par, "bybit_parametros_mercado")
            fuente_global = "bybit_parametros_mercado"

    _cache["g_by_asset"] = g_map
    _cache["detalle"] = detalle
    _cache["mtime_key"] = key
    _cache["loaded_at"] = time.time()
    _cache["fuente"] = fuente_global
    return dict(g_map)


def g_min_usd(asset: str) -> float:
    """G_min del Santo: archivo vivo → diccionario legado config → default."""
    a = str(asset or "").upper().strip()
    if not a:
        return max(_default(), _piso())

    mp = recargar()
    if a in mp:
        return float(mp[a])

    legado = getattr(config, "G_MIN_USD_BY_ASSET", {}) or {}
    if a in legado:
        return max(float(legado[a]), _piso())

    return max(_default(), _piso())


def detalle_g_min(asset: str) -> dict[str, Any]:
    """Telemetría: de dónde salió el peaje (sin inventar si no hay dato)."""
    a = str(asset or "").upper().strip()
    recargar()
    d = dict((_cache.get("detalle") or {}).get(a) or {})
    g = g_min_usd(a)
    return {
        "activo": a,
        "G_min": g,
        "archivo": d.get("archivo") or _cache.get("fuente"),
        "fuente_pierna": d.get("fuente_pierna"),
        "bruto": d.get("bruto"),
        "piso": _piso(),
        "default": _default(),
        "hay_dato_archivo": a in (_cache.get("g_by_asset") or {}),
    }


def mapa_g_min() -> dict[str, float]:
    return recargar()


def invalidar_cache() -> None:
    _cache["mtime_key"] = None
    _cache["g_by_asset"] = {}
    _cache["detalle"] = {}
