"""Sala por color — en vigor en el Beru que caza.

El verde conserva la sala de hoy. Amarillo y rojo abren vacío, sangre y red.
Oz, masa y engorde no viven aquí.

- verde: igual que hoy
- amarillo: vacío y sangre 1,7 · red 1,0 larga y 1,1 corta
- rojo: vacío y sangre 2,2 · red 1,4 larga y 1,6 corta
- Oz 0,2 en las tres
- el metro del vacío muerto: verde cada 0,5 · amarillo cada 0,7 · rojo cada 1
- el salto sigue siendo 0,1 y ese extra no engorda
- el engorde y la masa no viven aquí
- la red que nace 0,1 más lejos en cada toque no se toca
"""
from __future__ import annotations

from typing import Any

# Fracciones, como el resto del altar (0,012 = 1,2 %).
SALAS: dict[str, dict[str, float]] = {
    "verde": {
        "vacio": 0.012,
        "sangre": 0.012,
        "oz": 0.002,
        "red_long": 0.007,
        "red_short": 0.008,
        "estiron_paso": 0.005,
    },
    "amarillo": {
        "vacio": 0.017,
        "sangre": 0.017,
        "oz": 0.002,
        "red_long": 0.010,
        "red_short": 0.011,
        "estiron_paso": 0.007,
    },
    "rojo": {
        "vacio": 0.022,
        "sangre": 0.022,
        "oz": 0.002,
        "red_long": 0.014,
        "red_short": 0.016,
        "estiron_paso": 0.010,
    },
}

# El salto del vacío muerto. Igual en las tres. No entra al engorde.
ESTIRON_TICK = 0.001

_ALIASES = {
    "rojo": "rojo",
    "r": "rojo",
    "red": "rojo",
    "feria": "rojo",
    "verde": "verde",
    "v": "verde",
    "green": "verde",
    "amarillo": "amarillo",
    "a": "amarillo",
    "yellow": "amarillo",
}


def color_sala(color: str | None) -> str:
    """Rojo, amarillo o verde. Si no se reconoce, amarillo (como el santo sin medida)."""
    c = str(color or "").strip().lower()
    return _ALIASES.get(c, "amarillo")


def sala(color: str | None) -> dict[str, float]:
    """Copia de la sala. No incluye masa ni engorde."""
    return dict(SALAS[color_sala(color)])


def vacio_pct(color: str | None) -> float:
    return float(sala(color)["vacio"])


def sangre_pct(color: str | None) -> float:
    return float(sala(color)["sangre"])


def oz_pct(color: str | None) -> float:
    return float(sala(color)["oz"])


def estiron_paso_pct(color: str | None) -> float:
    """Cada cuánto camino nace otro 0,1 de vacío muerto."""
    return float(sala(color)["estiron_paso"])


def estiron_extra_pct(color: str | None, camino_pct: float) -> float:
    """Extra de la sangre por el camino ya andado. No engorda.

    camino_pct va en fracción (0,02 = 2 %). El salto es siempre 0,1.
    """
    paso = estiron_paso_pct(color)
    if paso <= 0:
        return 0.0
    n = int(float(camino_pct or 0) // paso)
    if n <= 0:
        return 0.0
    return float(n) * ESTIRON_TICK


def red_pct(color: str | None, direccion: str | None = None) -> float:
    """Larga  y corta. Sin dirección, devuelve la larga."""
    row = sala(color)
    d = str(direccion or "").strip().upper()
    if d == "SHORT":
        return float(row["red_short"])
    return float(row["red_long"])


def resumen(color: str | None) -> dict[str, Any]:
    row = sala(color)
    return {
        "color": color_sala(color),
        "vacio_pct": round(row["vacio"] * 100.0, 2),
        "sangre_pct": round(row["sangre"] * 100.0, 2),
        "oz_pct": round(row["oz"] * 100.0, 2),
        "red_larga_pct": round(row["red_long"] * 100.0, 2),
        "red_corta_pct": round(row["red_short"] * 100.0, 2),
        "estiron_cada_pct": round(row["estiron_paso"] * 100.0, 2),
        "estiron_salto_pct": round(ESTIRON_TICK * 100.0, 2),
        "engorde": "no se toca",
        "masa": "no se toca",
        "cortada": True,
    }
