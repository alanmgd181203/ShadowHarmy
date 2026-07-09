"""Matriz de spreads y panorama — precios Tank (presente, sin predicción)."""
from __future__ import annotations

import time

from core.activo import base_desde_bybit_linear
import core.config as config


def _pct_diff(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.0
    return abs(a - b) / min(a, b)


def _spot_vs_index(spot: float, index_px: float) -> float | None:
    if spot <= 0 or index_px <= 0:
        return None
    return (index_px - spot) / spot


def _entrada(tipo: str, base: str, spread_pct: float, **extra) -> dict:
    row = {"tipo": tipo, "base": base, "spread_pct": round(spread_pct * 100, 4), **extra}
    return row


def _bases_con_par_lineal_inverse(precios: dict) -> list[str]:
    """Activos con precio vivo en lineal USDT e inverse USD."""
    bases = []
    seen = set()
    for f, p in precios.items():
        if p <= 0 or not f.endswith("USDT_LINEAL"):
            continue
        base = f[: -len("USDT_LINEAL")]
        inv = f"{base}USD_INVERSE"
        if precios.get(inv, 0) > 0 and base not in seen:
            seen.add(base)
            bases.append(base)
    return bases


def calcular_matriz_spreads(
    precios: dict,
    funding: dict | None = None,
    index_prices: dict | None = None,
    *,
    bases_trinidad: list[str] | None = None,
    top_n: int | None = None,
) -> list[dict]:
    """
    Cruza precios vivos Tank: lineal↔inverso, spot↔perp, basis futuro↔perp, índice↔spot.
    Retorna lista ordenada por |spread| descendente.
    """
    funding = funding or {}
    index_prices = index_prices or {}
    bases_cfg = bases_trinidad or getattr(config, "ACTIVOS_TRINIDAD", []) or list(config.ACTIVOS_PENTIVERSO)
    # Ampliar bases con spot USDT vivos (Greed omnimercado)
    for p in getattr(config, "SPOT_ALL_PARES", []) or []:
        bc = str(p.get("baseCoin") or "").upper()
        qc = str(p.get("quoteCoin") or "").upper()
        sym = str(p.get("symbol") or "")
        if bc and (qc == "USDT" or sym.endswith("USDT")):
            bases_cfg = list(bases_cfg) + [bc]
    bases_live = _bases_con_par_lineal_inverse(precios)
    bases = list(dict.fromkeys(list(bases_cfg) + bases_live))
    top_n = top_n or getattr(config, "MATRIZ_SPREADS_TOP_N", 50)

    filas: list[dict] = []

    for base in bases:
        p_lin = precios.get(f"{base}USDT_LINEAL", 0.0)
        p_inv = precios.get(f"{base}USD_INVERSE", 0.0)
        p_spot = precios.get(f"{base}USDT_SPOT", 0.0)
        f_lin = f"{base}USDT_LINEAL"

        if p_lin > 0 and p_inv > 0:
            sp = _pct_diff(p_lin, p_inv)
            filas.append(_entrada(
                "lineal_vs_inverse", base, sp,
                precio_lineal=p_lin, precio_inverse=p_inv,
                funding=funding.get(f_lin),
            ))

        if p_spot > 0 and p_lin > 0:
            sp = _pct_diff(p_spot, p_lin)
            filas.append(_entrada(
                "spot_vs_perp", base, sp,
                precio_spot=p_spot, precio_perp=p_lin,
                funding=funding.get(f_lin),
            ))

        idx = index_prices.get(f_lin, 0.0)
        if p_spot > 0 and idx > 0:
            raw = _spot_vs_index(p_spot, idx)
            if raw is not None:
                filas.append(_entrada(
                    "spot_vs_index", base, abs(raw),
                    precio_spot=p_spot, index_price=idx,
                    desvio_signed_pct=round(raw * 100, 4),
                ))

        if p_lin > 0 and idx > 0:
            raw_p = (p_lin - idx) / idx
            filas.append(_entrada(
                "perp_vs_index", base, abs(raw_p),
                precio_perp=p_lin, index_price=idx,
                desvio_signed_pct=round(raw_p * 100, 4),
            ))

    # Basis: futuros dated vs perp (solo trinidad / pentiverso conocidos)
    perp_sym = {p["symbol"]: p for p in getattr(config, "LINEAR_PERP_PARES", []) if p.get("symbol")}
    for fut in getattr(config, "LINEAR_FUTURES_PARES", []):
        sym = fut.get("symbol", "")
        frente_fut = fut.get("frente", "")
        if not sym.startswith(tuple(bases)) and sym not in perp_sym:
            continue
        base = sym.split("-")[0].replace("USDT", "").replace("USDC", "")
        if base not in bases:
            for b in bases:
                if sym.startswith(b):
                    base = b
                    break
        p_fut = precios.get(frente_fut, 0.0)
        p_perp = precios.get(f"{base}USDT_LINEAL", 0.0)
        if p_fut > 0 and p_perp > 0:
            sp = _pct_diff(p_fut, p_perp)
            filas.append(_entrada(
                "basis_fut_vs_perp", base, sp,
                futuro=sym, precio_fut=p_fut, precio_perp=p_perp,
            ))

    # USDT vs USDC (mismo activo, pentiverso)
    for base in config.ACTIVOS_PENTIVERSO:
        pu = precios.get(f"{base}USDT_SPOT", 0.0) or precios.get(f"{base}USDT_LINEAL", 0.0)
        pc = precios.get(f"{base}USDC_SPOT", 0.0)
        if pu > 0 and pc > 0:
            sp = _pct_diff(pu, pc)
            filas.append(_entrada("usdt_vs_usdc", base, sp, precio_usdt=pu, precio_usdc=pc))

    # Multicruces spot — Greed (USDC/MNT/EUR vía puente); ver core/greed_multicruce.py
    try:
        from core import greed_multicruce as mc

        filas_mc = mc.calcular_filas_multicruce(precios)
        seen = {(r.get("base"), r.get("tipo")) for r in filas}
        for row in filas_mc:
            key = (row.get("base"), row.get("tipo"))
            if key not in seen:
                filas.append(row)
                seen.add(key)
    except Exception:
        pass

    filas.sort(key=lambda r: r["spread_pct"], reverse=True)
    cap = top_n + int(getattr(config, "GREED_MULTICRUCE_TOP_N", 20))
    return filas[:cap]


def _spot_bases_desde_config() -> set[str]:
    out: set[str] = set()
    for p in getattr(config, "SPOT_ALL_PARES", []):
        sym = p.get("symbol", "")
        if sym.endswith("USDT"):
            out.add(sym[:-4])
    return out


def calcular_desvios_indice(
    precios: dict,
    index_prices: dict | None = None,
    *,
    top_n: int | None = None,
) -> list[dict]:
    """Fase 1: perp Bybit vs indexPrice (todos los lineales vivos)."""
    index_prices = index_prices or {}
    huerfanas = set(getattr(config, "ACTIVOS_HUERFANOS", []) or [])
    spot_bases = _spot_bases_desde_config()
    top_n = top_n or getattr(config, "DESVIO_INDICE_TOP_N", 40)

    filas: list[dict] = []
    for p in getattr(config, "LINEAR_PERP_PARES", []):
        sym = p.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        frente = p.get("frente", f"{sym}_LINEAL")
        local = precios.get(frente, 0.0)
        idx = index_prices.get(frente, 0.0)
        if local <= 0 or idx <= 0:
            continue
        base = base_desde_bybit_linear(sym)
        raw = (local - idx) / idx
        filas.append({
            "base": base,
            "symbol": sym,
            "precio_local": local,
            "index_price": idx,
            "desvio_pct": round(abs(raw) * 100, 4),
            "desvio_signed_pct": round(raw * 100, 4),
            "huerfana": base in huerfanas,
            "tiene_spot_bybit": base in spot_bases,
        })

    filas.sort(key=lambda r: r["desvio_pct"], reverse=True)
    return filas[:top_n]


def calcular_panorama_global(
    precios: dict,
    index_prices: dict | None,
    ref_binance: dict,
    *,
    top_n: int | None = None,
) -> list[dict]:
    """Fase 2: Bybit local vs índice Bybit vs mid Binance."""
    index_prices = index_prices or {}
    ref_binance = ref_binance or {}
    stale_s = getattr(config, "REF_STALE_S", 30.0)
    ahora = time.time()
    top_n = top_n or getattr(config, "PANORAMA_TOP_N", 30)
    huerfanas = set(getattr(config, "ACTIVOS_HUERFANOS", []) or [])

    filas: list[dict] = []
    for base in getattr(config, "BASES_PANORAMA", []) or []:
        frente = f"{base}USDT_LINEAL"
        local = precios.get(frente, 0.0)
        if local <= 0:
            continue
        idx = index_prices.get(frente, 0.0)
        ref = ref_binance.get(base.upper(), {})
        bmid = float(ref.get("mid") or 0)
        bts = float(ref.get("ts") or 0)
        stale = (bts <= 0) or ((ahora - bts) > stale_s)

        desvio_index = None
        if idx > 0:
            desvio_index = round((local - idx) / idx * 100, 4)

        desvio_binance = None
        if bmid > 0:
            desvio_binance = round((local - bmid) / bmid * 100, 4)

        ancla = bmid if bmid > 0 else idx
        desvio_global = None
        if ancla > 0:
            desvio_global = round((local - ancla) / ancla * 100, 4)

        estado = "OK"
        if stale and bmid <= 0:
            estado = "SIN_BINANCE"
        elif stale:
            estado = "BINANCE_STALE"
        if desvio_global is not None and abs(desvio_global) >= getattr(config, "DESVIO_ALERTA_PCT", 0.5):
            estado = "DESALINEADO"

        filas.append({
            "base": base,
            "precio_bybit": local,
            "index_bybit": idx if idx > 0 else None,
            "mid_binance": bmid if bmid > 0 else None,
            "desvio_index_pct": desvio_index,
            "desvio_binance_pct": desvio_binance,
            "desvio_global_pct": desvio_global,
            "huerfana": base in huerfanas,
            "binance_stale": stale,
            "estado": estado,
        })

    filas.sort(
        key=lambda r: abs(r["desvio_global_pct"] or 0),
        reverse=True,
    )
    return filas[:top_n]
