"""Campos de Iron → factor de masa de Beru. No planta.

Guerra ×1 · sangre (+1 %…+5 %) ×2 · masacre (+5 %+) ×3.
Iron actualiza el sello; Beru solo lee el factor.

Ganancia = (realizado + flotante) / posición actual (notional vivo).
No usar la pierna histórica gorda: si ya se desengordó, pedir 1 %/5 %
sobre esa bolsa vieja aleja de más el campo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SANGRE_PCT = 0.01
MASACRE_PCT = 0.05

_RAIZ = Path(__file__).resolve().parents[2]
_DIR = _RAIZ / "data" / "hiron" / "campos"


def ganancia_fraccion(
    realizado: float,
    flotante: float,
    posicion_usd: float,
) -> float:
    """(realizado + flotante) / posición actual. Bolsa muerta → 0."""
    base = abs(float(posicion_usd or 0))
    if base <= 1e-9:
        return 0.0
    return (float(realizado or 0) + float(flotante or 0)) / base


def campo_de_ganancia(ganancia_frac: float) -> str:
    g = float(ganancia_frac or 0)
    if g >= MASACRE_PCT:
        return "masacre"
    if g >= SANGRE_PCT:
        return "sangre"
    return "guerra"


def factor_de_ganancia(ganancia_frac: float) -> float:
    nombre = campo_de_ganancia(ganancia_frac)
    if nombre == "masacre":
        return 3.0
    if nombre == "sangre":
        return 2.0
    return 1.0


def factor_de_campo(nombre: str | None) -> float:
    n = str(nombre or "guerra").strip().lower()
    if n in ("masacre", "masacre_real", "x3", "3"):
        return 3.0
    if n in ("sangre", "x2", "2"):
        return 2.0
    return 1.0


def _ruta(activo: str) -> Path:
    act = str(activo or "").strip().upper()
    return _DIR / f"{act}.json"


def publicar(
    activo: str,
    *,
    realizado: float,
    flotante: float,
    posicion_usd: float,
    pierna_hist_usd: float = 0.0,
) -> dict[str, Any]:
    """Iron escribe el campo del Santo. Beru lo lee después.

    ``posicion_usd`` = notional vivo ahora (manda el %).
    ``pierna_hist_usd`` solo se anota para lectura; no divide.
    """
    act = str(activo or "").strip().upper()
    if not act:
        return {}
    g = ganancia_fraccion(realizado, flotante, posicion_usd)
    campo = campo_de_ganancia(g)
    factor = factor_de_ganancia(g)
    fila = {
        "activo": act,
        "campo": campo,
        "factor": factor,
        "ganancia_frac": round(g, 6),
        "realizado": float(realizado or 0),
        "flotante": float(flotante or 0),
        "posicion_usd": float(posicion_usd or 0),
        "pierna_hist_usd": float(pierna_hist_usd or 0),
        # alias viejo: misma cifra que posición (no pierna histórica)
        "pierna_usd": float(posicion_usd or 0),
    }
    _DIR.mkdir(parents=True, exist_ok=True)
    _ruta(act).write_text(json.dumps(fila, ensure_ascii=False), encoding="utf-8")
    return fila


def leer(activo: str | None) -> dict[str, Any]:
    act = str(activo or "").strip().upper()
    if not act:
        return {}
    path = _ruta(act)
    if not path.exists():
        return {}
    try:
        dato = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}
    return dato if isinstance(dato, dict) else {}


def factor_para(activo: str | None = None, beru: Any | None = None) -> float:
    """Factor vivo: atributo en Beru > sello Iron > env > 1."""
    if beru is not None:
        raw = getattr(beru, "iron_campo_factor", None)
        if raw is not None:
            try:
                f = float(raw)
                if f > 0:
                    return f
            except (TypeError, ValueError):
                pass
        nombre = getattr(beru, "iron_campo", None)
        if nombre:
            return factor_de_campo(str(nombre))
    act = str(activo or "").strip().upper()
    if not act and beru is not None:
        from core import beru_rango as br

        act = str(br.activo_desde_beru(beru) or "").upper()
    sello = leer(act) if act else {}
    if sello:
        try:
            f = float(sello.get("factor") or 0)
            if f > 0:
                return f
        except (TypeError, ValueError):
            pass
        if sello.get("campo"):
            return factor_de_campo(str(sello.get("campo")))
    env = os.getenv("BERU_RANGO_IRON_CAMPO_FACTOR")
    if env is not None and str(env).strip() != "":
        try:
            f = float(env)
            if f > 0:
                return f
        except (TypeError, ValueError):
            pass
    return 1.0
