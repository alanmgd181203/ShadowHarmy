"""Mar de Beru — OKX por defecto (sin pentiverso / sin inverso).

Mapeo interno: frente ``ETHUSDT_LINEAL`` ↔ instId OKX ``ETH-USDT-SWAP``.
"""
from __future__ import annotations

import os

import core.config as config

_MARES = frozenset({"okx", "bybit"})


def mar_activo() -> str:
    m = str(getattr(config, "BERU_MAR", None) or os.getenv("BERU_MAR", "okx") or "okx")
    m = m.strip().lower()
    return m if m in _MARES else "okx"


def es_okx() -> bool:
    return mar_activo() == "okx"


def base_desde_frente(frente: str) -> str:
    f = str(frente or "").upper()
    if "_" in f:
        sym = f.rsplit("_", 1)[0]
    else:
        sym = f
    for suf in ("USDT", "USDC", "USD"):
        if sym.endswith(suf) and len(sym) > len(suf):
            return sym[: -len(suf)]
    return sym


def frente_lineal(activo: str) -> str:
    return f"{str(activo or '').strip().upper()}USDT_LINEAL"


def activo_a_inst_id(activo: str) -> str:
    return f"{str(activo or '').strip().upper()}-USDT-SWAP"


def inst_id_a_activo(inst_id: str) -> str:
    s = str(inst_id or "").upper()
    if s.endswith("-USDT-SWAP"):
        return s[: -len("-USDT-SWAP")]
    if s.endswith("USDT"):
        return s[: -len("USDT")]
    return s


def symbol_legacy(activo: str) -> str:
    """Símbolo estilo Bybit (altar/rituales legacy)."""
    return f"{str(activo or '').strip().upper()}USDT"
