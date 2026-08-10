"""Canal Igris + bóveda MNT (colateral ≠ exclusión permanente del ranking).

Doctrina Monarca 2026-08-08:
- MNT *sí* es Santo del pase (puede recibir manto dual cuando el canal lo permite).
- El short inverso MNT de *bóveda* no se mezcla con el long del manto.
- `IGRIS_PROTEGER_*` / bases bóveda: no *reducir* colateral en cleanup.
- `IGRIS_ACTIVOS_EXCLUSIVOS`: canal paralelo temporal (p.ej. solo ETH en Asalto).
- `IGRIS_BOVEDA_EN_LOTE=false` (2026-08-09): pausa engorde de bases bóveda (MNT)
  para no chambeár encima del short de colateral hasta hedge firme.
"""
from __future__ import annotations

from typing import Iterable

import core.config as config
from core import mnt_manto_hedge as mmh


def _csv_upper(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [x.strip().upper() for x in str(raw).split(",") if x.strip()]


def activos_exclusivos() -> list[str]:
    """Si no vacío: Igris solo opera estos activos (p. ej. ETH en Asalto)."""
    raw = getattr(config, "IGRIS_ACTIVOS_EXCLUSIVOS", None)
    if isinstance(raw, (list, tuple)):
        return [str(x).upper() for x in raw if str(x).strip()]
    return _csv_upper(str(raw or ""))


def bases_protegidas() -> set[str]:
    """Bases de bóveda/colateral (cleanup no cierra). MNT sigue siendo Santo."""
    return set(mmh.bases_boveda())


def bases_excluidas_lote() -> set[str]:
    """Activos que Igris no engorda en este canal (pausa temporal o CSV)."""
    out: set[str] = set()
    raw = getattr(config, "IGRIS_EXCLUIR_BASES", None)
    if isinstance(raw, (list, tuple, set)):
        out |= {str(x).upper() for x in raw if str(x).strip()}
    else:
        out |= set(_csv_upper(str(raw or "")))
    if not bool(getattr(config, "IGRIS_BOVEDA_EN_LOTE", True)):
        out |= bases_protegidas()
    return out


def simbolos_protegidos() -> set[str]:
    """Símbolos Bybit que cleanup no cancela a ciegas (bóveda)."""
    raw = getattr(config, "IGRIS_PROTEGER_SYMBOLS", None)
    if isinstance(raw, (list, tuple, set)):
        out = {str(x).upper() for x in raw if str(x).strip()}
    else:
        out = set(_csv_upper(str(raw or "")))
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
    """Exclusivos del canal; opcionalmente salta bóveda / CSV excluido."""
    exclusivos = set(activos_exclusivos())
    excluidos = bases_excluidas_lote()
    out: list[str] = []
    seen: set[str] = set()
    for a in activos:
        act = str(a or "").upper()
        if not act or act in seen:
            continue
        if act in excluidos:
            continue
        if exclusivos and act not in exclusivos:
            continue
        seen.add(act)
        out.append(act)
    if not out and exclusivos:
        for act in sorted(exclusivos):
            if act in excluidos:
                continue
            out.append(act)
    return out
