"""Backfill histórico Kaiser — klines vs índice Bybit (1h) para sesgo estructural.

Mares necesarios ahora (no todo el metaverso):
  - lineal mark vs index  → perp_vs_index
  - spot close vs index   → spot_vs_index
  - inverse mark vs index → inverse_vs_index

Bases: pentiverso + trinidad (cap) + MNT (bóveda). Más pares = cuando metaverso.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core.kaiser_samples import bulk_append_samples, load_samples


def _session():
    """Klines de mercado son públicos — mainnet evita bloqueos testnet/geo en lectura."""
    from pybit.unified_trading import HTTP
    # No usar TESTNET aquí: el índice/histórico es el mismo mapa de precios;
    # testnet a menudo 403 desde USA o rate-limit distinto.
    return HTTP(testnet=False)


def _huerfanas() -> set[str]:
    return set(getattr(config, "ACTIVOS_HUERFANOS", []) or [])


def bases_backfill_necesarias() -> list[str]:
    """Solo lo necesario ahora — no todo Spot All / metaverso.

    Prioridad: pentiverso + MNT (bóveda) · luego trinidad hasta el cap.
    """
    out: list[str] = []
    seen: set[str] = set()
    cap = int(getattr(config, "KAISER_BACKFILL_MAX_BASES", 12) or 12)

    def _add(b: str) -> None:
        if not b:
            return
        bu = str(b).upper()
        if bu not in seen and len(out) < cap:
            seen.add(bu)
            out.append(bu)

    for b in list(config.ACTIVOS_PENTIVERSO) + ["MNT"]:
        _add(b)
    for b in list(getattr(config, "ACTIVOS_TRINIDAD", []) or []):
        _add(b)
    return out


def _paged_kline(
    session,
    *,
    getter_name: str,
    category: str,
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    max_iters: int = 20,
) -> list:
    """Páginas hacia atrás; lista cruda Bybit (ts, o, h, l, c, …)."""
    getter = getattr(session, getter_name)
    out: list = []
    cursor_end = end_ms
    for _ in range(max_iters):
        if cursor_end <= start_ms:
            break
        resp = getter(
            category=category,
            symbol=symbol,
            interval=interval,
            start=start_ms,
            end=cursor_end,
            limit=1000,
        )
        chunk = (resp.get("result") or {}).get("list") or []
        if not chunk:
            break
        out.extend(chunk)
        oldest = int(chunk[-1][0])
        if oldest <= start_ms:
            break
        cursor_end = oldest - 1
    return out


def _index_by_ts(
    session,
    *,
    symbol_linear: str,
    interval: str,
    start_ms: int,
    end_ms: int,
) -> dict[str, float]:
    """Index kline del lineal USDT (misma base)."""
    chunk = _paged_kline(
        session,
        getter_name="get_index_price_kline",
        category="linear",
        symbol=symbol_linear,
        interval=interval,
        start_ms=start_ms,
        end_ms=end_ms,
    )
    out: dict[str, float] = {}
    for row in chunk:
        if len(row) >= 5:
            try:
                out[str(row[0])] = float(row[4])
            except (TypeError, ValueError):
                continue
    return out


def _rows_precio_vs_index(
    *,
    base: str,
    edge: str,
    price_rows: list,
    idx_by_ts: dict[str, float],
    close_idx: int = 4,
) -> list[dict]:
    """Convención: signed = (precio − index) / index × 100."""
    huerf = _huerfanas()
    rows: list[dict] = []
    seen: set[int] = set()
    for row in price_rows:
        if len(row) <= close_idx:
            continue
        try:
            ts_ms = row[0]
            px = float(row[close_idx])
        except (TypeError, ValueError, IndexError):
            continue
        ts_i = int(int(ts_ms) / 1000)
        if ts_i in seen:
            continue
        seen.add(ts_i)
        idx = idx_by_ts.get(str(ts_ms))
        if not idx or idx <= 0 or px <= 0:
            continue
        signed = (px - idx) / idx * 100.0
        rows.append({
            "ts": ts_i,
            "base": base.upper(),
            "edge": edge,
            "signed_pct": round(signed, 6),
            "abs_pct": round(abs(signed), 6),
            "huerfana": base.upper() in huerf,
            "ref_tipo": "index_kline",
            "source": "backfill",
        })
    return rows


def _persist_edge(base: str, edge: str, rows: list[dict]) -> dict[str, Any]:
    if not rows:
        return {"edge": edge, "ok": False, "error": "sin filas", "filas_nuevas": 0}
    existing = load_samples(base, edge, since_ts=rows[0]["ts"] - 1)
    exist_ts = {int(r["ts"]) for r in existing if r.get("source") == "backfill"}
    nuevas = [r for r in rows if int(r["ts"]) not in exist_ts]
    n = bulk_append_samples(nuevas, base, edge)
    return {"edge": edge, "ok": True, "filas_nuevas": n, "filas_total": len(rows)}


def backfill_base_perp_index(
    base: str,
    *,
    dias: int | None = None,
    interval: str = "60",
) -> dict[str, Any]:
    """Compat: solo lineal mark vs index."""
    r = backfill_base_sesgo_index(base, dias=dias, interval=interval, mares=("lineal",))
    lin = (r.get("mares") or {}).get("lineal") or {}
    return {
        "base": base,
        "ok": bool(r.get("ok") and lin.get("ok")),
        "filas_nuevas": lin.get("filas_nuevas", 0),
        "filas_total": lin.get("filas_total", 0),
        "error": r.get("error") or lin.get("error"),
    }


def backfill_base_sesgo_index(
    base: str,
    *,
    dias: int | None = None,
    interval: str = "60",
    mares: tuple[str, ...] = ("lineal", "spot", "inverso"),
) -> dict[str, Any]:
    """Descarga histórico necesario: lineal + spot + inverso vs mismo índice."""
    dias = dias or getattr(config, "KAISER_BACKFILL_DIAS", 365)
    bu = base.upper()
    symbol_lin = f"{bu}USDT"
    symbol_inv = f"{bu}USD"
    session = _session()
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - int(dias) * 86400000

    try:
        idx_by_ts = _index_by_ts(
            session,
            symbol_linear=symbol_lin,
            interval=interval,
            start_ms=start_ms,
            end_ms=end_ms,
        )
        if not idx_by_ts:
            return {"base": bu, "ok": False, "error": "sin index kline", "mares": {}}

        out_mares: dict[str, Any] = {}

        if "lineal" in mares:
            mark_list = _paged_kline(
                session,
                getter_name="get_mark_price_kline",
                category="linear",
                symbol=symbol_lin,
                interval=interval,
                start_ms=start_ms,
                end_ms=end_ms,
            )
            rows = _rows_precio_vs_index(
                base=bu, edge="perp_vs_index", price_rows=mark_list, idx_by_ts=idx_by_ts,
            )
            out_mares["lineal"] = _persist_edge(bu, "perp_vs_index", rows)

        if "spot" in mares:
            try:
                spot_list = _paged_kline(
                    session,
                    getter_name="get_kline",
                    category="spot",
                    symbol=symbol_lin,
                    interval=interval,
                    start_ms=start_ms,
                    end_ms=end_ms,
                )
                rows = _rows_precio_vs_index(
                    base=bu, edge="spot_vs_index", price_rows=spot_list, idx_by_ts=idx_by_ts,
                )
                out_mares["spot"] = _persist_edge(bu, "spot_vs_index", rows)
            except Exception as exc:
                out_mares["spot"] = {"edge": "spot_vs_index", "ok": False, "error": str(exc)[:160]}

        if "inverso" in mares:
            try:
                inv_list = _paged_kline(
                    session,
                    getter_name="get_mark_price_kline",
                    category="inverse",
                    symbol=symbol_inv,
                    interval=interval,
                    start_ms=start_ms,
                    end_ms=end_ms,
                )
                rows = _rows_precio_vs_index(
                    base=bu, edge="inverse_vs_index", price_rows=inv_list, idx_by_ts=idx_by_ts,
                )
                out_mares["inverso"] = _persist_edge(bu, "inverse_vs_index", rows)
            except Exception as exc:
                out_mares["inverso"] = {
                    "edge": "inverse_vs_index", "ok": False, "error": str(exc)[:160],
                }

        ok_any = any(bool(m.get("ok")) for m in out_mares.values())
        return {"base": bu, "ok": ok_any, "mares": out_mares}
    except Exception as exc:
        return {"base": bu, "ok": False, "error": str(exc)[:200], "mares": {}}


def backfill_bases(bases: list[str] | None = None) -> list[dict]:
    """Backfill sesgo completo (3 mares) para bases necesarias."""
    bases = bases or bases_backfill_necesarias()
    results = []
    for base in bases:
        results.append(backfill_base_sesgo_index(base))
    return results
