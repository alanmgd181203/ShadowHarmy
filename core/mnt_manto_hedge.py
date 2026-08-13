"""MNT Santo vs legado sucio (mega-cirugía 2026-08-12).

Manto (Igris): long inverso + short lineal. MNT es Santo, no saco.
Short inverso MNT si aparece = tumor legado (Tusk no lo reconstruye).
Igris no planta ese short. El have del pase no lo cuenta.

Si queda sucio en cuenta: modo hedge aísla el long del manto para no
comérselo. No es mandato de volver a abrir el short.
"""
from __future__ import annotations

from typing import Any

import core.config as config


def bases_boveda() -> set[str]:
    """Activos cuyo short inverso NO es manto (legado sucio, no saco)."""
    raw = getattr(config, "IGRIS_BOVEDA_BASES", None)
    if isinstance(raw, (list, tuple, set)):
        out = {str(x).upper() for x in raw if str(x).strip()}
    else:
        s = str(raw or getattr(config, "IGRIS_PROTEGER_BASES", "MNT") or "MNT")
        out = {x.strip().upper() for x in s.split(",") if x.strip()}
    return out or {"MNT"}


def activo_de_frente(frente: str | None) -> str:
    f = str(frente or "").upper()
    for suf in ("_INVERSE", "_LINEAL", "_SPOT"):
        if f.endswith(suf):
            f = f[: -len(suf)]
            break
    for q in ("USDT", "USDC", "USD"):
        if f.endswith(q) and len(f) > len(q):
            return f[: -len(q)]
    return f


def es_frente_inverse(frente: str | None) -> bool:
    fu = str(frente or "").upper()
    return "INVERSE" in fu or (
        fu.endswith("USD") and "USDT" not in fu and "USDC" not in fu
    )


def es_inverse_boveda(frente: str | None) -> bool:
    """True si el frente inverso pertenece a una base de bóveda (p.ej. MNTUSD_INVERSE)."""
    if not es_frente_inverse(frente):
        return False
    return activo_de_frente(frente) in bases_boveda()


def requiere_hedge_bidireccional(frente: str | None) -> bool:
    """Abrir long de manto en este frente exige modo Both Sides + positionIdx."""
    return es_inverse_boveda(frente)


def position_idx_para(direccion: str, *, hedge: bool) -> int | None:
    """Bybit: 0 one-way · 1 Buy/long · 2 Sell/short en hedge."""
    if not hedge:
        return None
    d = str(direccion or "").upper()
    if d in ("LONG", "BUY"):
        return 1
    if d in ("SHORT", "SELL"):
        return 2
    return None


def lado_cuenta_como_manto(activo: str, frente: str, lado: str) -> bool:
    """
    Qué pierna entra al nocional/ventana del *pase* (no bóveda).

    MNT inverso: solo LONG = manto; SHORT inverso = legado sucio (excluido).
    Resto: L en inverse + S en lineal del par §E (y lo desplegado en ese frente).
    """
    act = str(activo or "").upper()
    fu = str(frente or "").upper()
    la = str(lado or "").lower()
    if la not in ("long", "short"):
        return False
    if act in bases_boveda() and es_frente_inverse(fu):
        return la == "long"
    # Par §E genérico: inverse aporta long; lineal aporta short
    if es_frente_inverse(fu):
        return la == "long"
    if "LINEAL" in fu or fu.endswith("USDT") or "USDT_" in fu:
        return la == "short"
    return True


def pesos_sin_boveda_short(pesos: dict | None) -> dict:
    """Copia de pesos con short inverso de bóveda a 0 (ventana / engorde canal)."""
    out: dict[str, Any] = {}
    for frente, row in (pesos or {}).items():
        if not isinstance(row, dict):
            continue
        if es_inverse_boveda(frente):
            r = dict(row)
            r["short"] = 0.0
            # no tocar precio_medio_short de bóveda en manto
            out[str(frente)] = r
        else:
            out[str(frente)] = row
    return out


def amenaza_netting_boveda(
    frente: str,
    direccion: str,
    *,
    modo_hedge: bool,
) -> str | None:
    """
    Si queda short legado y no hay hedge: abrir LONG lo nettea → prohibido.
    Con hedge: OK. Igris no abre SHORT inverso (no reconstruir el tumor).
    """
    if not es_inverse_boveda(frente):
        return None
    d = str(direccion or "").upper()
    if d in ("SHORT", "SELL"):
        return "short_inverso_es_boveda_no_manto"
    if d in ("LONG", "BUY") and not modo_hedge:
        return "long_sin_hedge_comeria_short_boveda"
    return None


def pares_hedge_boveda() -> list[tuple[str, str]]:
    """
    (symbol Bybit, category) a forzar Both Sides.
    Inverso es crítico (bóveda short + manto long). Lineal también por coherencia.
    """
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for base in sorted(bases_boveda()):
        for symbol, category in (
            (f"{base}USD", "inverse"),
            (f"{base}USDT", "linear"),
        ):
            key = (symbol, category)
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


async def asegurar_hedge_bases_boveda(bridge) -> dict[str, Any]:
    """Activa modo bidireccional (mode=3) en todos los pares de bóveda."""
    if not getattr(config, "IGRIS_MNT_HEDGE_OBLIGATORIO", False):
        return {"ok": True, "skipped": True, "pares": []}
    resultados: list[dict[str, Any]] = []
    ok_all = True
    for symbol, category in pares_hedge_boveda():
        try:
            r = await bridge.asegurar_modo_hedge(symbol, category=category)
            row = {
                "symbol": symbol,
                "category": category,
                "ok": bool(getattr(r, "exito", False)),
                "mensaje": str(getattr(r, "mensaje", "") or ""),
            }
        except Exception as e:
            row = {
                "symbol": symbol,
                "category": category,
                "ok": False,
                "mensaje": str(e),
            }
        resultados.append(row)
        if not row["ok"]:
            ok_all = False
    return {"ok": ok_all, "skipped": False, "pares": resultados}
