"""Greed — detección de multicruces spot (USDT/USDC/EUR/MNT vía puente)."""
from __future__ import annotations

from typing import Any

import core.config as config


def _pct_diff(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.0
    return abs(a - b) / min(a, b)


def _parse_par(p: dict) -> tuple[str, str, str]:
    """Retorna (base, quote, frente)."""
    sym = str(p.get("symbol", "")).upper()
    base = str(p.get("baseCoin") or "").upper()
    quote = str(p.get("quoteCoin") or "").upper()
    frente = str(p.get("frente") or f"{sym}_SPOT")
    if not base or not quote:
        for b in sorted(
            set(getattr(config, "ACTIVOS_TRINIDAD", []) or []) | set(config.ACTIVOS_PENTIVERSO),
            key=len,
            reverse=True,
        ):
            if sym.startswith(b):
                rest = sym[len(b):]
                if rest:
                    return b, rest, frente
        if sym.endswith("USDT"):
            return sym[:-4], "USDT", frente
        if sym.endswith("USDC"):
            return sym[:-4], "USDC", frente
        if sym.endswith("EUR"):
            return sym[:-3], "EUR", frente
        if sym.endswith("MNT"):
            return sym[:-3], "MNT", frente
    return base, quote, frente


class SpotIndex:
    """Índice base/quote → precio (unidades quote por 1 base)."""

    def __init__(self, precios: dict, spot_pares: list[dict] | None = None):
        self.precios = precios or {}
        self._frente: dict[tuple[str, str], str] = {}
        self._price: dict[tuple[str, str], float] = {}
        for p in spot_pares or getattr(config, "SPOT_ALL_PARES", []) or []:
            base, quote, frente = _parse_par(p)
            if not base or not quote:
                continue
            self._frente[(base, quote)] = frente
            px = float(self.precios.get(frente, 0) or 0)
            if px > 0:
                self._price[(base, quote)] = px

    def frente(self, base: str, quote: str) -> str | None:
        return self._frente.get((base.upper(), quote.upper()))

    def precio(self, base: str, quote: str) -> float:
        return float(self._price.get((base.upper(), quote.upper()), 0) or 0)

    def usdt_por_quote(self, quote: str) -> float:
        """Cuántos USDT cuesta 1 unidad de quote (EUR, MNT, USDC…)."""
        q = quote.upper()
        if q == "USDT":
            return 1.0
        direct = self.precio(q, "USDT")
        if direct > 0:
            return direct
        inv = self.precio("USDT", q)
        if inv > 0:
            return 1.0 / inv
        if q == "USDC":
            p = self.precio("USDC", "USDT")
            if p > 0:
                return p
        if q == "EUR":
            eur_per_usdc = self.precio("USDC", "EUR")
            usdc_per_usdt = self.precio("USDC", "USDT")
            if eur_per_usdc > 0 and usdc_per_usdt > 0:
                return usdc_per_usdt / eur_per_usdc
        if q == "MNT":
            return self.precio("MNT", "USDT")
        return 0.0


def _piernas_via_mnt(base: str, idx: SpotIndex, *, sintetico_barato: bool) -> list[dict] | None:
    fd = idx.frente(base, "USDT")
    fb = idx.frente(base, "MNT")
    fm = idx.frente("MNT", "USDT")
    if not all([fd, fb, fm]):
        return None
    if sintetico_barato:
        return [
            {"frente": fm, "side": "Buy", "rol": "puente_mnt"},
            {"frente": fb, "side": "Buy", "rol": "base_via_mnt"},
            {"frente": fd, "side": "Sell", "rol": "salida_usdt"},
        ]
    return [
        {"frente": fd, "side": "Buy", "rol": "entrada_usdt"},
        {"frente": fb, "side": "Sell", "rol": "base_via_mnt"},
        {"frente": fm, "side": "Sell", "rol": "puente_mnt"},
    ]


def _piernas_via_eur(base: str, idx: SpotIndex, *, sintetico_barato: bool) -> list[dict] | None:
    fd = idx.frente(base, "USDT")
    fb = idx.frente(base, "EUR")
    f_uc = idx.frente("USDC", "USDT")
    f_ue = idx.frente("USDC", "EUR")
    if not all([fd, fb, f_uc, f_ue]):
        return None
    if sintetico_barato:
        return [
            {"frente": f_uc, "side": "Buy", "rol": "usdc_puente"},
            {"frente": f_ue, "side": "Sell", "rol": "usdc_a_eur"},
            {"frente": fb, "side": "Buy", "rol": "base_via_eur"},
            {"frente": fd, "side": "Sell", "rol": "salida_usdt"},
        ]
    return [
        {"frente": fd, "side": "Buy", "rol": "entrada_usdt"},
        {"frente": fb, "side": "Sell", "rol": "base_via_eur"},
        {"frente": f_ue, "side": "Buy", "rol": "eur_a_usdc"},
        {"frente": f_uc, "side": "Sell", "rol": "usdc_puente"},
    ]


def _piernas_via_usdc(base: str, idx: SpotIndex, *, sintetico_barato: bool) -> list[dict] | None:
    fd = idx.frente(base, "USDT")
    fb = idx.frente(base, "USDC")
    f_uc = idx.frente("USDC", "USDT")
    if not all([fd, fb, f_uc]):
        return None
    if sintetico_barato:
        return [
            {"frente": f_uc, "side": "Buy", "rol": "puente_usdc"},
            {"frente": fb, "side": "Buy", "rol": "base_via_usdc"},
            {"frente": fd, "side": "Sell", "rol": "salida_usdt"},
        ]
    return [
        {"frente": fd, "side": "Buy", "rol": "entrada_usdt"},
        {"frente": fb, "side": "Sell", "rol": "base_via_usdc"},
        {"frente": f_uc, "side": "Sell", "rol": "puente_usdc"},
    ]


def _fila_multicruce(
    base: str,
    via: str,
    *,
    directo: float,
    sintetico: float,
    piernas: list[dict],
) -> dict[str, Any]:
    sp = _pct_diff(directo, sintetico) * 100.0
    sint_barato = sintetico < directo
    tipo = f"multicruce_{len(piernas)}p"
    frentes_unicos = list(dict.fromkeys(p["frente"] for p in piernas))
    return {
        "tipo": tipo,
        "base": base.upper(),
        "via_quote": via.upper(),
        "spread_pct": round(sp, 4),
        "precio_directo_usdt": round(directo, 8),
        "precio_sintetico_usdt": round(sintetico, 8),
        "sintetico_barato": sint_barato,
        "n_piernas": len(piernas),
        "piernas": piernas,
        "frentes": {
            "compra": piernas[0]["frente"],
            "venta": piernas[-1]["frente"],
            "todos": frentes_unicos,
        },
        "ruta_id": f"{base.upper()}:via_{via.upper()}",
    }


def calcular_filas_multicruce(
    precios: dict,
    *,
    spot_pares: list[dict] | None = None,
    bases: list[str] | None = None,
    quotes_via: tuple[str, ...] | None = None,
    umbral_pct: float | None = None,
    top_n: int | None = None,
) -> list[dict]:
    """
    Triangular / multi-pierna: base/USDT vs base/QUOTE × (QUOTE→USDT).
    Greed ejecuta; Beru no participa.
    """
    if not getattr(config, "GREED_MULTICRUCE_ENABLED", True):
        return []

    idx = SpotIndex(precios, spot_pares)
    umbral = umbral_pct if umbral_pct is not None else float(
        getattr(config, "GREED_MULTICRUCE_UMBRAL_PCT", 0.15),
    )
    top_n = top_n or int(getattr(config, "GREED_MULTICRUCE_TOP_N", 20))
    quotes = quotes_via or tuple(getattr(config, "GREED_MULTICRUCE_VIA_QUOTES", ("USDC", "MNT", "EUR")))

    if bases is None:
        semilla = str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH")).upper()
        spot_pares = spot_pares or getattr(config, "SPOT_ALL_PARES", []) or []
        bases_spot: list[str] = []
        for p in spot_pares:
            bc = str(p.get("baseCoin") or "").upper()
            qc = str(p.get("quoteCoin") or "").upper()
            sym = str(p.get("symbol") or "")
            if bc and (qc == "USDT" or sym.endswith("USDT")):
                bases_spot.append(bc)
        bases = list(dict.fromkeys([
            *bases_spot,
            *getattr(config, "ACTIVOS_PENTIVERSO", ()),
            semilla,
            *getattr(config, "ACTIVOS_TRINIDAD", ()),
        ]))

    filas: list[dict] = []
    builders = {
        "USDC": _piernas_via_usdc,
        "MNT": _piernas_via_mnt,
        "EUR": _piernas_via_eur,
    }

    for base in bases:
        b = base.upper()
        directo = idx.precio(b, "USDT")
        if directo <= 0:
            continue
        for via in quotes:
            builder = builders.get(via.upper())
            if not builder:
                continue
            p_via = idx.precio(b, via.upper())
            usdt_pq = idx.usdt_por_quote(via.upper())
            if p_via <= 0 or usdt_pq <= 0:
                continue
            sintetico = p_via * usdt_pq
            sp = _pct_diff(directo, sintetico) * 100.0
            if sp < umbral:
                continue
            sint_barato = sintetico < directo
            piernas = builder(b, idx, sintetico_barato=sint_barato)
            if not piernas:
                continue
            filas.append(_fila_multicruce(
                b, via.upper(),
                directo=directo, sintetico=sintetico, piernas=piernas,
            ))

    filas.sort(key=lambda r: r["spread_pct"], reverse=True)
    return filas[:top_n]
