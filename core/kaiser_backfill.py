"""Backfill histórico Kaiser — klines mark vs index (1h) para plazo largo."""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core.kaiser_samples import bulk_append_samples, load_samples


def _session():
    from pybit.unified_trading import HTTP
    return HTTP(testnet=config.TESTNET)


def backfill_base_perp_index(
    base: str,
    *,
    dias: int | None = None,
    interval: str = "60",
) -> dict[str, Any]:
    """Descarga mark + index kline y escribe muestras hourly."""
    dias = dias or getattr(config, "KAISER_BACKFILL_DIAS", 365)
    symbol = f"{base.upper()}USDT"
    edge = "perp_vs_index"
    session = _session()
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - dias * 86400000

    try:
        mark_list: list = []
        idx_by_ts: dict[str, float] = {}
        cursor_end = end_ms
        max_iters = 20
        for _ in range(max_iters):
            if cursor_end <= start_ms:
                break
            mark = session.get_mark_price_kline(
                category="linear", symbol=symbol, interval=interval,
                start=start_ms, end=cursor_end, limit=1000,
            )
            index = session.get_index_price_kline(
                category="linear", symbol=symbol, interval=interval,
                start=start_ms, end=cursor_end, limit=1000,
            )
            chunk_m = (mark.get("result") or {}).get("list") or []
            chunk_i = (index.get("result") or {}).get("list") or []
            if not chunk_m:
                break
            mark_list.extend(chunk_m)
            for row in chunk_i:
                if len(row) >= 5:
                    idx_by_ts[row[0]] = float(row[4])
            oldest = int(chunk_m[-1][0])
            if oldest <= start_ms:
                break
            cursor_end = oldest - 1
    except Exception as exc:
        return {"base": base, "ok": False, "error": str(exc)[:200]}

    huerfanas = set(getattr(config, "ACTIVOS_HUERFANOS", []) or [])
    rows: list[dict] = []
    seen_ts: set[int] = set()
    for row in mark_list:
        if len(row) < 5:
            continue
        ts_ms, mark_close = row[0], float(row[4])
        ts_i = int(int(ts_ms) / 1000)
        if ts_i in seen_ts:
            continue
        seen_ts.add(ts_i)
        idx_close = idx_by_ts.get(ts_ms)
        if not idx_close or idx_close <= 0:
            continue
        signed = (mark_close - idx_close) / idx_close * 100
        rows.append({
            "ts": ts_i,
            "base": base.upper(),
            "edge": edge,
            "signed_pct": round(signed, 6),
            "abs_pct": round(abs(signed), 6),
            "huerfana": base.upper() in huerfanas,
            "ref_tipo": "index_kline",
            "source": "backfill",
        })

    if not rows:
        return {"base": base, "ok": False, "error": "sin filas kline"}

    existing = load_samples(base, edge, since_ts=rows[0]["ts"] - 1)
    exist_ts = {int(r["ts"]) for r in existing if r.get("source") == "backfill"}
    nuevas = [r for r in rows if int(r["ts"]) not in exist_ts]
    n = bulk_append_samples(nuevas, base, edge)
    return {"base": base, "ok": True, "filas_nuevas": n, "filas_total": len(rows)}


def backfill_bases(bases: list[str] | None = None) -> list[dict]:
    bases = bases or (
        list(config.ACTIVOS_PENTIVERSO)
        + list(getattr(config, "ACTIVOS_TRINIDAD", []) or [])[:10]
    )
    cap = getattr(config, "KAISER_BACKFILL_MAX_BASES", 12)
    results = []
    for base in bases[:cap]:
        results.append(backfill_base_perp_index(base))
    return results
