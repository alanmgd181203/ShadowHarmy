"""Protección de colateral MNT + canal Igris exclusivo (segundo frente).

Doctrina Monarca: MNTUSD es colateral intacto; el manto dual ETH corre
en canal paralelo sin tocarlo ni mezclarlo en el lote de engorde.
"""
from __future__ import annotations

from typing import Iterable

import core.config as config


def _csv_upper(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip().upper() for x in str(raw).split(",") if x.strip()]


def activos_exclusivos() -> list[str]:
    """Si no vacío: Igris solo opera estos activos (p. ej. ETH)."""
    raw = getattr(config, "IGRIS_ACTIVOS_EXCLUSIVOS", None)
    if isinstance(raw, (list, tuple)):
        return [str(x).upper() for x in raw if str(x).strip()]
    return _csv_upper(str(raw or ""))


def bases_protegidas() -> set[str]:
    """Bases intocables (colateral). Default MNT."""
    raw = getattr(config, "IGRIS_PROTEGER_BASES", None)
    if isinstance(raw, (list, tuple, set)):
        out = {str(x).upper() for x in raw if str(x).strip()}
    else:
        out = set(_csv_upper(str(raw or "MNT")))
    return out or {"MNT"}


def simbolos_protegidos() -> set[str]:
    """Símbolos Bybit que nunca se cancelan/cierran (cleanup / manos)."""
    raw = getattr(config, "IGRIS_PROTEGER_SYMBOLS", None)
    if isinstance(raw, (list, tuple, set)):
        out = {str(x).upper() for x in raw if str(x).strip()}
    else:
        out = set(_csv_upper(str(raw or "")))
    # Semillas desde bases protegidas (inverse + lineales comunes)
    for base in bases_protegidas():
        for suf in ("USD", "USDT", "USDC"):
            out.add(f"{base}{suf}")
    return out


def base_de_symbol(symbol: str | None) -> str:
    s = str(symbol or "").upper()
    for suf in ("USDT", "USDC", "USD"):
        if s.endswith(suf) and len(s) > len(suf):
            return s[: -len(suf)]
    return s


def simbolo_protegido(symbol: str | None) -> bool:
    s = str(symbol or "").upper()
    if not s:
        return False
    if s in simbolos_protegidos():
        return True
    return base_de_symbol(s) in bases_protegidas()


def base_protegida(base: str | None) -> bool:
    return str(base or "").upper() in bases_protegidas()


def filtrar_activos_trabajo(activos: Iterable[str]) -> list[str]:
    """Aplica exclusivos + excluye bases protegidas del lote de manto."""
    exclusivos = set(activos_exclusivos())
    prot = bases_protegidas()
    out: list[str] = []
    seen: set[str] = set()
    for a in activos:
        act = str(a or "").upper()
        if not act or act in seen:
            continue
        if act in prot:
            continue
        if exclusivos and act not in exclusivos:
            continue
        seen.add(act)
        out.append(act)
    if not out and exclusivos:
        # Canal paralelo forzado aunque el pase no liste el activo
        for act in sorted(exclusivos):
            if act not in prot:
                out.append(act)
    return out
