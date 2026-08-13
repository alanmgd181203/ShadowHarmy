"""Igris — registro L/S y bocado asimétrico (mega-cirugía 2026-08-12).

Desigualdad chica se corrige en el *siguiente* bocado.
Quien recibe el ajuste fino = pierna con paso mínimo USD más pequeño (duda V5: Alfa Ley Masa intacta).
"""
from __future__ import annotations

from typing import Any

import core.config as config
from core import lote_bybit as lote
from core import manto_ventana as mv
from core import igris_manto as im


def usd_piernas_activo(tusk, activo: str) -> tuple[float, float]:
    """USD L/S del manto (sin bóveda). Preferir helper del pase (Jess)."""
    try:
        from core import pase_director as pd

        return pd.usd_piernas_manto_activo(tusk, activo)
    except Exception:
        pass
    act = (activo or "").upper()
    fl, fs = im.frentes_bootstrap(act)
    pesos = getattr(tusk, "pesos", None) or {}
    try:
        from core import mnt_manto_hedge as mmh
        pesos = mmh.pesos_sin_boveda_short(pesos)
    except Exception:
        pass
    subset = {fl: pesos.get(fl) or {}, fs: pesos.get(fs) or {}}
    return mv.usd_piernas_desde_pesos(subset)


def pierna_paso_mas_fino(
    frente_l: str,
    frente_s: str,
    px_l: float,
    px_s: float,
) -> str:
    """Devuelve 'long' | 'short' según paso mínimo USD más chico."""
    pl = lote.paso_minimo_usd(frente_l, px_l) if px_l > 0 else 1e9
    ps = lote.paso_minimo_usd(frente_s, px_s) if px_s > 0 else 1e9
    if pl <= ps:
        return "long"
    return "short"


def bocado_asimetrico_usd(
    usd_l_have: float,
    usd_s_have: float,
    restante_total_ls: float,
    *,
    frente_l: str = "",
    frente_s: str = "",
    px_l: float = 0.0,
    px_s: float = 0.0,
) -> dict[str, Any]:
    """
    Reparte el próximo dual (USD por pierna) para acercar L≈S.
    restante_total_ls = need L+S aún faltante (ambas piernas).
    """
    rest = max(0.0, float(restante_total_ls or 0))
    if rest <= 0:
        return {
            "ok": False,
            "motivo": "sin_restante",
            "usd_long": 0.0,
            "usd_short": 0.0,
            "ajuste": "none",
        }

    # Mitad simétrica base del restante total
    half = rest / 2.0
    ul = float(usd_l_have or 0)
    us = float(usd_s_have or 0)
    diff = ul - us  # >0 long gordo

    # Corrección: dar más a la pierna floja (acotado al half)
    corr = min(abs(diff) * 0.5, half * 0.9)
    usd_l = half
    usd_s = half
    ajuste = "simetrico"
    fino = "long"
    if frente_l and frente_s and px_l > 0 and px_s > 0:
        fino = pierna_paso_mas_fino(frente_l, frente_s, px_l, px_s)

    if abs(diff) > float(getattr(config, "IGRIS_BOCADO_CORR_MIN_USD", 1.0) or 1.0):
        if diff > 0:
            # long gordo → más short
            usd_s = half + corr
            usd_l = max(0.0, half - corr)
            ajuste = "mas_short"
        else:
            usd_l = half + corr
            usd_s = max(0.0, half - corr)
            ajuste = "mas_long"
        # Si la pierna que debería crecer no es la de paso fino, igual aplicamos
        # el sesgo de equilibrio; el fill fino lo hace lote_bybit al cuantizar.
        ajuste = f"{ajuste}|fino={fino}"

    return {
        "ok": True,
        "usd_long": round(usd_l, 6),
        "usd_short": round(usd_s, 6),
        "half_usd": round(half, 6),
        "diff_have_usd": round(diff, 6),
        "ajuste": ajuste,
        "pierna_paso_fino": fino,
    }
