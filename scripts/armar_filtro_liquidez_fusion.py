#!/usr/bin/env python3
"""Corta libro fino del ranking fusionado (ojos Bybit, sin manos).

Regla Monarca: si ~1% de slippage se come Oz/Red → fuera absoluto.
Prueba: walk orderbook linear 50 niveles con mordida probe USD;
también peaje de volumen 24h muy bajo.

Actualiza data/coliseo/rango_juicio/filtros_absolutos.json (campos liquidez_*).

Uso:
  python -u scripts/armar_filtro_liquidez_fusion.py
  python -u scripts/armar_filtro_liquidez_fusion.py --probe-usd 50 --slip-max 1.0
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.ancla import simular_compra_notional_usd, simular_venta_base  # noqa: E402

API = "https://api.bybit.com"
FILTROS = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_absolutos.json"
FICHAS = ROOT / "data" / "coliseo" / "rango_juicio" / "santos_ficha.json"
CK_N = ROOT / "data" / "coliseo" / "rango_juicio" / "matriz" / "normal_reciente" / "checkpoint_parcial.json"
CK_F = ROOT / "data" / "coliseo" / "rango_juicio" / "matriz" / "feria_reciente" / "checkpoint_parcial.json"
STABLES = {"USDC", "USDE", "USD1", "RLUSD", "USDT"}


def _get(path: str, *, timeout: float = 45) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"User-Agent": "ShadowHarmy-LiquidezFusion/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def es_oficio(activo: str, fichas: dict[str, Any]) -> bool:
    a = str(activo or "").upper()
    f = fichas.get(a) or {}
    t = str(f.get("symbol_type") or "").lower()
    if f.get("tradefi"):
        return True
    if t in ("stock", "commodity", "etf", "fx", "forex"):
        return True
    if a in STABLES:
        return True
    if a.endswith(("2L", "3L")) or a.startswith("CSOP"):
        return True
    return False


def vivos_fusion(filtros: dict[str, Any], fichas: dict[str, Any]) -> list[str]:
    n = json.loads(CK_N.read_text(encoding="utf-8"))
    f = json.loads(CK_F.read_text(encoding="utf-8"))
    nmap = {str(r["activo"]).upper(): r for r in (n.get("ranking") or [])}
    fmap = {str(r["activo"]).upper(): r for r in (f.get("ranking") or [])}
    rows: list[tuple[str, float]] = []
    for a in set(nmap) | set(fmap):
        cn = _f(nmap[a]["calor"]) if a in nmap else None
        cf = _f(fmap[a]["calor"]) if a in fmap else None
        if cn is None and cf is None:
            continue
        cm = max(x for x in (cn, cf) if x is not None)
        rows.append((a, cm))
    btc = next((cm for a, cm in rows if a == "BTC"), 0.0)
    out: list[str] = []
    for a, cm in rows:
        if es_oficio(a, fichas):
            continue
        x = (filtros.get("activos") or {}).get(a) or {}
        if x.get("min_orden_fuera") or x.get("extremo_fuera") or x.get("leverage_fuera"):
            continue
        if cm <= btc:
            continue
        out.append(a)
    return sorted(out)


def tickers_linear() -> dict[str, dict[str, float]]:
    data = _get("/v5/market/tickers?category=linear")
    out: dict[str, dict[str, float]] = {}
    for row in (data.get("result") or {}).get("list") or []:
        sym = str(row.get("symbol") or "")
        if not sym.endswith("USDT"):
            continue
        base = sym[:-4].upper()
        out[base] = {
            "turnover24h": _f(row.get("turnover24h")),
            "last": _f(row.get("lastPrice")),
        }
    return out


def orderbook_linear(symbol: str) -> tuple[list, list]:
    data = _get(f"/v5/market/orderbook?category=linear&symbol={symbol}&limit=50")
    res = data.get("result") or {}
    bids = [[_f(p), _f(q)] for p, q in (res.get("b") or [])]
    asks = [[_f(p), _f(q)] for p, q in (res.get("a") or [])]
    return bids, asks


def evaluar_libro(
    base: str,
    *,
    probe_usd: float,
    slip_max: float,
    turnover_min: float,
    tick: dict[str, float] | None,
) -> dict[str, Any]:
    to = _f((tick or {}).get("turnover24h"))
    if to < turnover_min:
        return {
            "liquidez_fuera": True,
            "motivos_liq": ["turnover_bajo"],
            "turnover24h": to,
            "slip_buy_pct": None,
            "slip_sell_pct": None,
            "probe_usd": probe_usd,
        }
    try:
        bids, asks = orderbook_linear(f"{base}USDT")
    except Exception as e:
        return {
            "liquidez_fuera": True,
            "motivos_liq": ["orderbook_error"],
            "turnover24h": to,
            "error": str(e)[:120],
            "slip_buy_pct": None,
            "slip_sell_pct": None,
            "probe_usd": probe_usd,
        }
    buy = simular_compra_notional_usd(asks, probe_usd, inverse=False)
    qty = _f(buy.get("qty_base"))
    sell = simular_venta_base(bids, qty, inverse=False) if qty > 0 else {"slippage_pct": 0.0, "agotado": True}
    sb = _f(buy.get("slippage_pct"))
    ss = _f(sell.get("slippage_pct"))
    agotado = bool(buy.get("agotado") or sell.get("agotado") or qty <= 0)
    motivos: list[str] = []
    if agotado:
        motivos.append("libro_agotado")
    if sb >= slip_max or ss >= slip_max:
        motivos.append("slip_ge_1pct")
    return {
        "liquidez_fuera": bool(motivos),
        "motivos_liq": motivos,
        "turnover24h": to,
        "slip_buy_pct": round(sb, 4),
        "slip_sell_pct": round(ss, 4),
        "probe_usd": probe_usd,
        "agotado": agotado,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Filtro liquidez fusion")
    ap.add_argument("--probe-usd", type=float, default=50.0)
    ap.add_argument("--slip-max", type=float, default=1.0, help="pct; >= deja fuera")
    ap.add_argument(
        "--turnover-min",
        type=float,
        default=500_000.0,
        help="USDT 24h minimo",
    )
    ap.add_argument("--sleep", type=float, default=0.08)
    ap.add_argument("--only", default="", help="CSV bases (opcional)")
    args = ap.parse_args()

    payload = json.loads(FILTROS.read_text(encoding="utf-8"))
    activos = payload.setdefault("activos", {})
    fichas = (json.loads(FICHAS.read_text(encoding="utf-8")).get("por_base") or {})

    if args.only.strip():
        bases = [x.strip().upper() for x in args.only.split(",") if x.strip()]
    else:
        bases = vivos_fusion(payload, fichas)

    print(f"Liquidez · {len(bases)} vivos · probe=${args.probe_usd:.0f} · slip>={args.slip_max}%", flush=True)
    print("Tickers linear…", flush=True)
    ticks = tickers_linear()
    print(f"  {len(ticks)} tickers", flush=True)

    n_out = 0
    for i, base in enumerate(bases, 1):
        row = evaluar_libro(
            base,
            probe_usd=float(args.probe_usd),
            slip_max=float(args.slip_max),
            turnover_min=float(args.turnover_min),
            tick=ticks.get(base),
        )
        cur = activos.setdefault(base, {})
        cur["liquidez_fuera"] = bool(row["liquidez_fuera"])
        cur["turnover24h"] = row.get("turnover24h")
        cur["slip_buy_pct"] = row.get("slip_buy_pct")
        cur["slip_sell_pct"] = row.get("slip_sell_pct")
        cur["probe_usd"] = row.get("probe_usd")
        motivos = list(cur.get("motivos") or [])
        motivos = [m for m in motivos if m not in ("turnover_bajo", "libro_agotado", "slip_ge_1pct", "orderbook_error")]
        for m in row.get("motivos_liq") or []:
            if m not in motivos:
                motivos.append(m)
        cur["motivos"] = motivos
        cur["fuera"] = bool(
            cur.get("min_orden_fuera")
            or cur.get("extremo_fuera")
            or cur.get("liquidez_fuera")
            or cur.get("pico_masa_fuera")
            or cur.get("leverage_fuera")
            or cur.get("rango_anual_fuera")
            or cur.get("listado_reciente_fuera")
            or cur.get("muerta_fuera")
        )
        if row["liquidez_fuera"]:
            n_out += 1
            print(
                f"  [{i}/{len(bases)}] {base} FUERA · {row.get('motivos_liq')} · "
                f"slip {row.get('slip_buy_pct')}/{row.get('slip_sell_pct')} · "
                f"to={(_f(row.get('turnover24h'))/1e6):.2f}M",
                flush=True,
            )
        elif i % 20 == 0 or i == len(bases):
            print(
                f"  [{i}/{len(bases)}] ok · fuera_liq={n_out}",
                flush=True,
            )
        time.sleep(max(0.0, float(args.sleep)))

    meta = payload.setdefault("meta", {})
    meta["ts_liquidez_utc"] = datetime.now(timezone.utc).isoformat()
    meta["probe_usd"] = float(args.probe_usd)
    meta["slip_max_pct"] = float(args.slip_max)
    meta["turnover_min_usd"] = float(args.turnover_min)
    meta["n_fuera_liquidez"] = n_out
    meta["n_liquidez_escaneados"] = len(bases)

    FILTROS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK · liquidez fuera={n_out}/{len(bases)} → {FILTROS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
