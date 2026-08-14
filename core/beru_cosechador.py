"""Beru Cosechador — FUSIONADO en negociador ping-pong (2026-08-13).

Ya no es vida aparte. Tras el oro: una trailing; al fill → oro al otro lado.
Este módulo reexporta / delega para no romper imports.
"""
from __future__ import annotations

from core import beru_negociador


def llamado_tiempo_pct(ancla_red_pct: float, vacio: float | None = None) -> float:
    """Alias del ping-pong: oro a la orilla opuesta."""
    return beru_negociador.oro_orilla_opuesta(ancla_red_pct, vacio)


def pasos_cosechador() -> tuple[float, float]:
    return beru_negociador.pasos_negociador(None)


def activar_primera_vez(llamado_pct: float, paso: float) -> tuple[float, float]:
    return beru_negociador.activar_trailing_unica(llamado_pct, paso)


def avanzar_equivalente(
    oz_pct: float,
    red_pct: float,
    paso: float | None = None,
) -> tuple[float, float]:
    """Sin segunda carta: solo mueve la trailing."""
    p = paso if paso is not None else beru_negociador.paso_trailing_pct()
    oz_n, _ = beru_negociador.activar_trailing_unica(oz_pct, p)
    if oz_pct < 0:
        return oz_n - p, 0.0
    return oz_n + p, 0.0


def toca_llamado_tiempo(precio: float, centro: float, llamado_pct: float) -> bool:
    return beru_negociador.toca_condicional(precio, centro, llamado_pct)


def toca_oz_cosecha(precio: float, centro: float, oz_pct: float) -> bool:
    return beru_negociador.toca_trailing(precio, centro, oz_pct)


def toca_red_cosecha(precio: float, centro: float, red_pct: float) -> bool:
    return beru_negociador.toca_red_negociador(precio, centro, red_pct)
