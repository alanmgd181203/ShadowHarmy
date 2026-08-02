"""Tusk tesorería — visión real de la bóveda UTA (Bybit).

Lee equity, disponible, monedas (MNT/stables), short-hedge y calcula
**oxígeno de guerra**: lo que el ejército puede desplegar sin mentirse.

Doctrina: colchón Monarca (MONARCA_RESERVA_PCT + reserva extra opcional).
El short MNT a alto lev suele comer ~IM (ej. 2% a 50×); Bybit ya lo refleja
en totalAvailableBalance — aquí lo hacemos visible.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config

_STABLES = frozenset({"USDT", "USDC", "USDE", "USD1", "USD"})
_FEE_ASSETS = frozenset({"MNT"})  # descuento fees Bybit


def _f(x: Any, default: float = 0.0) -> float:
    try:
        if x in ("", None):
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def reserva_monarca_pct() -> float:
    """Colchón doctrinal 5% + extra Monarca (apertura / paranoia)."""
    base = float(getattr(config, "MONARCA_RESERVA_PCT", 0.05) or 0.0)
    extra = float(getattr(config, "TUSK_RESERVA_MONARCA_EXTRA_PCT", 0.0) or 0.0)
    return max(0.0, min(0.50, base + extra))


def oxigeno_guerra_usd(
    equity: float,
    disponible: float,
    *,
    reserva_pct: float | None = None,
) -> dict[str, float]:
    """Oxígeno de guerra: el IM del hedge cuenta *dentro* del colchón.

    colchón_objetivo = reserva × equity
    ya_reservado ≈ equity − disponible  (IM hedge + resto en UTA)
    Si ya_reservado < colchón → solo falta el resto del colchón.
    Si ya_reservado ≥ colchón → no se resta extra (el hedge ya comió el colchón o más).

    Equivale a: min(disponible, equity × (1 − reserva)).
    """
    eq = max(0.0, float(equity))
    disp = max(0.0, float(disponible))
    res = reserva_monarca_pct() if reserva_pct is None else max(0.0, min(0.50, float(reserva_pct)))
    colchon_obj = round(eq * res, 6)
    ya_reservado = round(max(0.0, eq - disp), 6)
    extra_colchon = round(max(0.0, colchon_obj - ya_reservado), 6)
    ox = round(max(0.0, disp - extra_colchon), 4)
    return {
        "reserva_pct": res,
        "colchon_objetivo_usd": round(colchon_obj, 4),
        "ya_reservado_usd": round(ya_reservado, 4),
        "extra_colchon_usd": round(extra_colchon, 4),
        "oxigeno_bruto_usd": round(disp, 4),
        "oxigeno_guerra_usd": ox,
    }


def parse_coins(account: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Desglose por moneda del UNIFIED account."""
    out: list[dict[str, Any]] = []
    if not account:
        return out
    for c in account.get("coin") or []:
        coin = str(c.get("coin") or "").upper()
        if not coin:
            continue
        usd = _f(c.get("usdValue"))
        eq = _f(c.get("equity"))
        wb = _f(c.get("walletBalance"))
        # collateralSwitch / availableToBorrow etc. varían por versión API
        out.append({
            "coin": coin,
            "usd_value": round(usd, 4),
            "equity": round(eq, 8),
            "wallet_balance": round(wb, 8),
            "es_stable": coin in _STABLES,
            "es_fee_asset": coin in _FEE_ASSETS,
        })
    out.sort(key=lambda r: -r["usd_value"])
    return out


def parse_hedge_shorts(
    posiciones: list[dict[str, Any]] | None,
    *,
    bases: tuple[str, ...] = ("MNT",),
) -> list[dict[str, Any]]:
    """Shorts abiertos sobre bases de fee-asset (hedge del saco spot)."""
    bases_u = {b.upper() for b in bases}
    hedges: list[dict[str, Any]] = []
    for p in posiciones or []:
        size = _f(p.get("size"))
        if size <= 0:
            continue
        side = str(p.get("side") or "")
        if side not in ("Sell", "Short"):
            continue
        symbol = str(p.get("symbol") or "").upper()
        base = None
        for b in bases_u:
            if symbol.startswith(b):
                base = b
                break
        if base is None:
            continue
        notional = abs(_f(p.get("positionValue")))
        if notional <= 0:
            # fallback size * mark
            notional = abs(size * _f(p.get("markPrice") or p.get("avgPrice")))
        hedges.append({
            "symbol": symbol,
            "base": base,
            "side": "SHORT",
            "size": size,
            "notional_usd": round(notional, 4),
            "position_im_usd": round(_f(p.get("positionIM")), 4),
            "leverage": _f(p.get("leverage")) or None,
            "liq_price": _f(p.get("liqPrice")) or None,
            "avg_price": _f(p.get("avgPrice")) or None,
            "mark_price": _f(p.get("markPrice")) or None,
            "u_pnl": round(_f(p.get("unrealisedPnl")), 4),
            "category": str(p.get("category") or p.get("_category") or ""),
        })
    return hedges


def estado_tesoreria(
    *,
    equity: float,
    disponible: float,
    mm_rate: float | None,
    im_rate: float | None = None,
) -> str:
    """sana | justa | ahogada — para oído / panel."""
    if equity <= 0:
        return "ahogada"
    ratio_disp = disponible / equity if equity > 0 else 0.0
    mm = float(mm_rate) if mm_rate is not None else 0.0
    if mm >= 0.8 or ratio_disp < 0.15:
        return "ahogada"
    if mm >= 0.5 or ratio_disp < 0.40:
        return "justa"
    return "sana"


def construir_tesoreria(
    account: dict[str, Any] | None,
    *,
    posiciones: list[dict[str, Any]] | None = None,
    reserva_pct: float | None = None,
) -> dict[str, Any]:
    """Snapshot de bóveda para Tusk / estado_vivo.tusk_tesoreria."""
    account = account or {}
    equity = _f(account.get("totalEquity"))
    disponible = _f(account.get("totalAvailableBalance"))
    im_total = _f(account.get("totalInitialMargin"))
    mm_total = _f(account.get("totalMaintenanceMargin"))
    mm_rate = _f(account.get("accountMMRate"), default=-1.0)
    im_rate = _f(account.get("accountIMRate"), default=-1.0)
    if mm_rate < 0:
        mm_rate_v: float | None = None
    else:
        mm_rate_v = mm_rate
    if im_rate < 0:
        im_rate_v: float | None = None
    else:
        im_rate_v = im_rate

    coins = parse_coins(account)
    mnt = next((c for c in coins if c["coin"] == "MNT"), None)
    stables_usd = round(sum(c["usd_value"] for c in coins if c["es_stable"]), 4)
    mnt_usd = round((mnt or {}).get("usd_value") or 0.0, 4)

    hedges = parse_hedge_shorts(posiciones)
    im_hedge = round(sum(h["position_im_usd"] for h in hedges), 4)
    notional_hedge = round(sum(h["notional_usd"] for h in hedges), 4)

    res = reserva_monarca_pct() if reserva_pct is None else max(0.0, min(0.50, float(reserva_pct)))
    o2 = oxigeno_guerra_usd(equity, disponible, reserva_pct=res)

    # “Como dólares”: equity marcada; hedge visible
    hedge_ok = False
    if mnt_usd > 1.0 and notional_hedge > 0:
        # ±15% de match notional vs spot MNT
        hedge_ok = abs(notional_hedge - mnt_usd) / max(mnt_usd, 1.0) <= 0.15

    estado = estado_tesoreria(
        equity=equity, disponible=disponible, mm_rate=mm_rate_v, im_rate=im_rate_v,
    )

    out: dict[str, Any] = {
        "ts": time.time(),
        "fuente": "uta",
        "equity_usd": round(equity, 4),
        "disponible_usd": round(disponible, 4),
        "im_total_usd": round(im_total, 4),
        "mm_total_usd": round(mm_total, 4),
        "account_mm_rate": mm_rate_v,
        "account_im_rate": im_rate_v,
        "coins": coins[:24],
        "stables_usd": stables_usd,
        "mnt_usd": mnt_usd,
        "hedge_shorts": hedges,
        "im_hedge_usd": im_hedge,
        "notional_hedge_usd": notional_hedge,
        "hedge_match_ok": hedge_ok,
        "reserva_monarca_pct": round(res, 4),
        "colchon_objetivo_usd": o2["colchon_objetivo_usd"],
        "ya_reservado_usd": o2["ya_reservado_usd"],
        "extra_colchon_usd": o2["extra_colchon_usd"],
        "oxigeno_bruto_usd": o2["oxigeno_bruto_usd"],
        "oxigeno_guerra_usd": o2["oxigeno_guerra_usd"],
        "estado": estado,
        "nota": (
            "Oxígeno = min(disponible, equity×(1−reserva)). "
            "El IM del hedge cuenta dentro del colchón Monarca, no encima."
        ),
    }

    # Checkpoint bóveda MNT — solo cálculo; manos OFF
    if getattr(config, "TUSK_BOVEDA_MNT_DOCTRINA", True):
        try:
            from core import tusk_boveda_mnt as bm

            spot_mark = None
            if mnt and _f(mnt.get("equity")) > 0 and mnt_usd > 0:
                # usd/qty aprox si wallet_balance ≈ qty
                qty = _f(mnt.get("wallet_balance") or mnt.get("equity"))
                if qty > 0:
                    spot_mark = mnt_usd / qty
            out["boveda_mnt"] = bm.construir_bloque_boveda_mnt(
                mnt_usd=mnt_usd,
                hedges=hedges,
                spot_mark=spot_mark,
                equity_vivo=equity,
            )
        except Exception as e:
            out["boveda_mnt"] = {"error": str(e)[:160], "manos_permitidas": False}

    return out


def tesoreria_simulada(
    equity: float,
    *,
    disponible: float | None = None,
    mnt_usd: float = 0.0,
    hedge_notional: float = 0.0,
    hedge_im: float = 0.0,
    leverage: float = 50.0,
) -> dict[str, Any]:
    """Para smokes / sim: arma un account mínimo."""
    disp = float(disponible if disponible is not None else max(0.0, equity - hedge_im))
    account = {
        "totalEquity": equity,
        "totalAvailableBalance": disp,
        "totalInitialMargin": hedge_im,
        "totalMaintenanceMargin": hedge_im * 0.5,
        "accountMMRate": (hedge_im * 0.5 / equity) if equity > 0 else 0.0,
        "accountIMRate": (hedge_im / equity) if equity > 0 else 0.0,
        "coin": [],
    }
    if mnt_usd > 0:
        account["coin"].append({
            "coin": "MNT", "usdValue": mnt_usd, "equity": mnt_usd, "walletBalance": mnt_usd,
        })
    stables = max(0.0, equity - mnt_usd)
    if stables > 0:
        account["coin"].append({
            "coin": "USDT", "usdValue": stables, "equity": stables, "walletBalance": stables,
        })
    posiciones = []
    if hedge_notional > 0:
        im = hedge_im if hedge_im > 0 else hedge_notional / max(leverage, 1.0)
        posiciones.append({
            "symbol": "MNTUSDT",
            "side": "Sell",
            "size": 1.0,
            "positionValue": hedge_notional,
            "positionIM": im,
            "leverage": leverage,
            "markPrice": 1.0,
            "unrealisedPnl": 0.0,
            "liqPrice": 0.0,
        })
    return construir_tesoreria(account, posiciones=posiciones)
