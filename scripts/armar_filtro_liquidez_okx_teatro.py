#!/usr/bin/env python3
"""Liquidez OKX SWAP para teatro piedra — libro propio, no Bybit.

Escanea solo elegibles actuales del teatro OKX:
  min orden < $1.50 · calor > BTC (juicio Bybit reutilizado)

Regla: walk orderbook 50 niveles · probe USD · slip >= umbral → fuera.
Salida: data/coliseo/rango_juicio/filtros_liquidez_okx.json

Uso:
  python -u scripts/armar_filtro_liquidez_okx_teatro.py
  python -u scripts/armar_filtro_liquidez_okx_teatro.py --probe-usd 30 --slip-max 1.0
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.ancla import simular_compra_notional_usd, simular_venta_base  # noqa: E402
from core import okx_rest  # noqa: E402

CATALOGO = ROOT / "data" / "coliseo" / "rango_juicio" / "teatro_okx_catalogo.json"
CK_N = ROOT / "data" / "coliseo" / "rango_juicio" / "matriz" / "normal_reciente" / "checkpoint_parcial.json"
CK_F = ROOT / "data" / "coliseo" / "rango_juicio" / "matriz" / "feria_reciente" / "checkpoint_parcial.json"
OUT = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_liquidez_okx.json"

MIN_USD_TOPE = 1.5
EMPATE_EPS = 1e-6


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def build_calor_map() -> tuple[dict[str, float], float]:
    n = json.loads(CK_N.read_text(encoding="utf-8"))
    f = json.loads(CK_F.read_text(encoding="utf-8"))
    nmap = {str(r["activo"]).upper(): _f(r.get("calor")) for r in (n.get("ranking") or [])}
    fmap = {str(r["activo"]).upper(): _f(r.get("calor")) for r in (f.get("ranking") or [])}
    out: dict[str, float] = {}
    for a in set(nmap) | set(fmap):
        cn = nmap.get(a)
        cf = fmap.get(a)
        if cn is None and cf is None:
            continue
        if cn is None:
            out[a] = cf
        elif cf is None:
            out[a] = cn
        elif abs(cn - cf) < EMPATE_EPS:
            out[a] = cn
        else:
            out[a] = max(cn, cf)
    piso = out.get("BTC", 0.0)
    return out, piso


def elegibles_okx(rows: list[dict[str, Any]], calor: dict[str, float], piso_btc: float) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        act = str(r.get("activo") or "").upper()
        min_u = _f(r.get("min_usd"))
        if min_u >= MIN_USD_TOPE - 1e-9:
            continue
        cm = calor.get(act)
        if cm is None or cm <= piso_btc + 1e-12:
            continue
        out.append(r)
    return out


def tickers_okx_vol() -> dict[str, float]:
    out: dict[str, float] = {}
    for row in okx_rest.tickers_swap_usdt():
        inst = str(row.get("instId") or "")
        if not inst.endswith("-USDT-SWAP"):
            continue
        base = inst.split("-")[0].upper()
        vol = _f(row.get("volCcy24h"))
        if vol <= 0:
            vol = _f(row.get("vol24h")) * _f(row.get("last"))
        out[base] = vol
    return out


def evaluar_libro_okx(
    row: dict[str, Any],
    *,
    probe_usd: float,
    slip_max: float,
    turnover_min: float,
    vol24h: float,
) -> dict[str, Any]:
    act = str(row.get("activo") or "").upper()
    inst_id = str(row.get("instId") or f"{act}-USDT-SWAP")
    if vol24h < turnover_min:
        return {
            "activo": act,
            "instId": inst_id,
            "liquidez_fuera": True,
            "motivos_liq": ["turnover_bajo"],
            "turnover24h": vol24h,
            "slip_buy_pct": None,
            "slip_sell_pct": None,
            "probe_usd": probe_usd,
            "mar": "okx",
        }
    try:
        bids, asks = okx_rest.order_book(inst_id, sz=50)
    except Exception as exc:
        return {
            "activo": act,
            "instId": inst_id,
            "liquidez_fuera": True,
            "motivos_liq": ["orderbook_error"],
            "turnover24h": vol24h,
            "error": str(exc)[:160],
            "slip_buy_pct": None,
            "slip_sell_pct": None,
            "probe_usd": probe_usd,
            "mar": "okx",
        }
    buy = simular_compra_notional_usd(asks, probe_usd, inverse=False)
    qty = _f(buy.get("qty_base"))
    sell = (
        simular_venta_base(bids, qty, inverse=False)
        if qty > 0
        else {"slippage_pct": 0.0, "agotado": True}
    )
    sb = _f(buy.get("slippage_pct"))
    ss = _f(sell.get("slippage_pct"))
    agotado = bool(buy.get("agotado") or sell.get("agotado") or qty <= 0)
    motivos: list[str] = []
    if agotado:
        motivos.append("libro_agotado")
    if sb >= slip_max or ss >= slip_max:
        motivos.append("slip_ge_1pct")
    return {
        "activo": act,
        "instId": inst_id,
        "liquidez_fuera": bool(motivos),
        "motivos_liq": motivos,
        "turnover24h": round(vol24h, 2),
        "slip_buy_pct": round(sb, 4),
        "slip_sell_pct": round(ss, 4),
        "probe_usd": probe_usd,
        "agotado": agotado,
        "mar": "okx",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Liquidez OKX teatro piedra")
    ap.add_argument("--probe-usd", type=float, default=50.0)
    ap.add_argument("--slip-max", type=float, default=1.0)
    ap.add_argument("--turnover-min", type=float, default=500_000.0)
    ap.add_argument("--sleep", type=float, default=0.09)
    ap.add_argument("--only", default="", help="CSV bases (debug)")
    args = ap.parse_args()

    if not CATALOGO.exists():
        print(f"Falta {CATALOGO}", file=sys.stderr)
        return 1

    rows = json.loads(CATALOGO.read_text(encoding="utf-8")).get("activos") or []
    calor, piso_btc = build_calor_map()
    if args.only.strip():
        only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        targets = [r for r in rows if str(r.get("activo") or "").upper() in only]
    else:
        targets = elegibles_okx(rows, calor, piso_btc)

    print(
        f"OKX liquidez · {len(targets)} elegibles · probe=${args.probe_usd:.0f} · "
        f"slip>={args.slip_max}% · vol24h>={args.turnover_min/1e6:.2f}M",
        flush=True,
    )
    print("Tickers OKX SWAP…", flush=True)
    vols = tickers_okx_vol()
    print(f"  {len(vols)} tickers", flush=True)

    activos: dict[str, Any] = {}
    n_out = 0
    for i, row in enumerate(targets, 1):
        act = str(row.get("activo") or "").upper()
        ev = evaluar_libro_okx(
            row,
            probe_usd=float(args.probe_usd),
            slip_max=float(args.slip_max),
            turnover_min=float(args.turnover_min),
            vol24h=_f(vols.get(act)),
        )
        activos[act] = ev
        if ev["liquidez_fuera"]:
            n_out += 1
            print(
                f"  [{i}/{len(targets)}] {act} FUERA · {ev.get('motivos_liq')} · "
                f"slip {ev.get('slip_buy_pct')}/{ev.get('slip_sell_pct')} · "
                f"vol={(_f(ev.get('turnover24h'))/1e6):.2f}M",
                flush=True,
            )
        elif i % 25 == 0 or i == len(targets):
            print(f"  [{i}/{len(targets)}] ok · fuera_liq={n_out}", flush=True)
        time.sleep(max(0.0, float(args.sleep)))

    payload = {
        "meta": {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "mar": "okx",
            "fuente": "okx_public_books+tickers",
            "probe_usd": float(args.probe_usd),
            "slip_max_pct": float(args.slip_max),
            "turnover_min_usd": float(args.turnover_min),
            "min_usd_tope": MIN_USD_TOPE,
            "piso_btc_calor": round(piso_btc, 6),
            "n_escaneados": len(targets),
            "n_fuera_liquidez": n_out,
            "n_elegibles_post_liq": len(targets) - n_out,
        },
        "activos": activos,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK · fuera={n_out}/{len(targets)} · vivos={len(targets)-n_out} -> {OUT}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
