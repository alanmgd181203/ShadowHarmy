"""Igris de baja — stub protección de símbolos (cleanup legacy)."""
from __future__ import annotations


def bases_protegidas() -> set[str]:
    return {"MNT"}


def symbols_protegidos() -> set[str]:
    return {"MNTUSD"}


def orden_protegida(symbol: str, **kwargs) -> bool:
    _ = kwargs
    s = str(symbol or "").upper()
    return s in symbols_protegidos() or s.startswith("MNT")
