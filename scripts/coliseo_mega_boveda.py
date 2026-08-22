#!/usr/bin/env python3
"""Mega bóveda Coliseo — velas 1m anuales · catálogo Bybit linear (+ TradeFi/stocks).

TradeFi no es API aparte: acciones/commodities vienen en category=linear (symbolType=stock).

Ejemplos:
  python scripts/coliseo_mega_boveda.py --dias 365 --workers 2
  python scripts/coliseo_mega_boveda.py --solo-tradefi --dias 365
  python scripts/coliseo_mega_boveda.py --watchdog --workers 2

Sin manos · checkpoint propio · reanuda sobre boveda_linear_1m.sqlite existente.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

import core.config as config  # noqa: E402
from core import coliseo_boveda as bov  # noqa: E402
from core import coliseo_catalogo as cat  # noqa: E402
import jess_boveda_coliseo_noche as jess  # noqa: E402

MEGA_DIR = bov.COLISEO_DIR / "mega_boveda"
CATALOG_PATH = MEGA_DIR / "catalogo_linear_usdt.json"
CHECKPOINT_PATH = MEGA_DIR / "checkpoint_mega_1m.json"
PROGRESO_PATH = MEGA_DIR / "PROGRESO_MEGA.md"
LOG_PATH = MEGA_DIR / "mega_boveda.log"

_WRITE_LOCK = threading.Lock()
_RESULTS: list[dict[str, Any]] = []
_RESULTS_LOCK = threading.Lock()


def _log(msg: str) -> None:
    MEGA_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _load_ckpt() -> dict[str, Any]:
    MEGA_DIR.mkdir(parents=True, exist_ok=True)
    if not CHECKPOINT_PATH.exists():
        return {"bases": {}, "fase": "ingest", "updated_ts": 0}
    return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))


def _save_ckpt(data: dict[str, Any]) -> None:
    data["updated_ts"] = time.time()
    CHECKPOINT_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _refresh_catalog(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows = cat.discover_linear_perpetual_usdt(
        incluir_futures=bool(args.incluir_futures),
        solo_tradefi=bool(args.solo_tradefi),
        excluir_tradefi=bool(args.excluir_tradefi),
    )
    if args.only:
        want = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        rows = [r for r in rows if str(r.get("base")).upper() in want]
    only_file = str(getattr(args, "only_file", "") or "").strip()
    if only_file:
        p = Path(only_file)
        if not p.is_file():
            p = ROOT / only_file
        raw = p.read_text(encoding="utf-8")
        want = {
            x.strip().upper()
            for part in raw.replace("\n", ",").replace(";", ",").split(",")
            for x in [part]
            if x.strip() and not x.strip().startswith("#")
        }
        rows = [r for r in rows if str(r.get("base")).upper() in want]
    MEGA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.time(),
        "resumen": cat.resumen_catalogo(rows),
        "activos": rows,
    }
    CATALOG_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return rows


def _min_rows_ok(dias: int) -> int:
    return max(1, int(dias * 1440 * 0.85))


def _write_progreso(catalog: list[dict[str, Any]], results: list[dict[str, Any]]) -> None:
    with _WRITE_LOCK:
        con = bov.connect(bov.boveda_path("linear"))
        total_bars = bov.count_candles(con)
        n_bases = con.execute("SELECT COUNT(DISTINCT base) FROM candles").fetchone()[0]
        con.close()
    ok = sum(1 for r in results if r.get("ok"))
    err = sum(1 for r in results if r.get("ok") is False)
    lines = [
        "# Mega bóveda Beru rango — progreso 1m",
        "",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Catálogo: **{len(catalog)}** pares USDT linear perp",
        f"- Bóveda linear: **{n_bases}** bases · **{total_bars:,}** velas",
        f"- Esta sesión OK/error: **{ok}/{err}**",
        "",
        "| Base | Symbol | TradeFi | Estado | Filas | + | s |",
        "|------|--------|---------|--------|------:|--:|--:|",
    ]
    by_base = {str(r.get("base")): r for r in results}
    for row in catalog[:500]:
        base = str(row.get("base"))
        r = by_base.get(base) or {}
        st = r.get("status") or r.get("error") or "pendiente"
        tf = "sí" if row.get("tradefi") else ""
        lines.append(
            f"| {base} | {row.get('symbol', '')} | {tf} | {st} | "
            f"{r.get('rows', '—')} | {r.get('added', '—')} | {r.get('secs', '—')} |"
        )
    if len(catalog) > 500:
        lines.append(f"| … | +{len(catalog) - 500} más | | | | | |")
    PROGRESO_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pending(
    catalog: list[dict[str, Any]],
    cp: dict[str, Any],
    *,
    dias: int,
    force: bool,
) -> list[dict[str, Any]]:
    min_rows = _min_rows_ok(dias)
    done = cp.get("bases") or {}
    out: list[dict[str, Any]] = []
    con = bov.connect(bov.boveda_path("linear"))
    try:
        for row in catalog:
            base = str(row.get("base") or "").upper()
            ck = str(row.get("ck") or f"{base}@linear")
            meta = done.get(ck) or done.get(base) or {}
            if not force and meta.get("status") == "ok":
                try:
                    if int(meta.get("rows") or 0) >= min_rows:
                        continue
                except (TypeError, ValueError):
                    pass
            n = bov.count_candles(con, base)
            if not force and n >= min_rows:
                continue
            out.append(row)
    finally:
        con.close()
    return out


def run_ingest(args: argparse.Namespace) -> list[dict[str, Any]]:
    bov.set_interval("1")
    catalog = _refresh_catalog(args)
    resumen = cat.resumen_catalogo(catalog)
    _log(
        f"Catálogo: {resumen['total']} pares "
        f"(crypto={resumen['crypto']} tradefi={resumen['tradefi']})"
    )
    cp = _load_ckpt()
    pending = _pending(catalog, cp, dias=args.dias, force=bool(args.force))
    if not pending and not args.force:
        _log("Nada pendiente — todo el catálogo cumple ventana o checkpoint.")
        return []

    _log(f"Pendientes: {len(pending)} · dias={args.dias} · workers={args.workers}")
    jess._hb(
        "mega_ingest",
        f"pendientes={len(pending)} total_cat={len(catalog)} dias={args.dias}",
    )

    results: list[dict[str, Any]] = []

    def _job(row: dict[str, Any]) -> dict[str, Any]:
        base = str(row.get("base") or "").upper()
        symbol = str(row.get("symbol") or "")
        ck = str(row.get("ck") or f"{base}@linear")
        try:
            r = jess.ingest_one(
                base,
                "linear",
                dias=args.dias,
                sleep_s=args.sleep,
                interval="1",
                symbol=symbol,
            )
            r["symbol"] = symbol
            r["tradefi"] = bool(row.get("tradefi"))
            with _RESULTS_LOCK:
                results.append(r)
                cp_local = _load_ckpt()
                cp_local.setdefault("bases", {})[ck] = {
                    "status": "ok",
                    "base": base,
                    "symbol": symbol,
                    "rows": r.get("rows"),
                    "tradefi": bool(row.get("tradefi")),
                    "ts": time.time(),
                }
                _save_ckpt(cp_local)
                _write_progreso(catalog, results)
            jess._hb("mega_ingest", f"OK {symbol} rows={r.get('rows')} +{r.get('added')}")
            _log(f"OK {symbol} rows={r.get('rows')} +{r.get('added')} ({r.get('secs')}s)")
            return r
        except Exception as exc:
            err = {
                "base": base,
                "symbol": symbol,
                "market": "linear",
                "ok": False,
                "error": str(exc)[:240],
                "status": "error",
            }
            with _RESULTS_LOCK:
                results.append(err)
                cp_local = _load_ckpt()
                cp_local.setdefault("bases", {})[ck] = {
                    "status": "error",
                    "base": base,
                    "symbol": symbol,
                    "error": str(exc)[:240],
                    "ts": time.time(),
                }
                _save_ckpt(cp_local)
                _write_progreso(catalog, results)
            jess._hb("mega_ingest", f"ERROR {symbol}: {exc}", ok=False)
            _log(f"ERROR {symbol}: {exc}")
            return err

    workers = max(1, min(int(args.workers), len(pending)))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_job, row) for row in pending]
        for fut in as_completed(futs):
            fut.result()
    return results


def watchdog_loop(args: argparse.Namespace) -> None:
    interval = args.watchdog_min * 60
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "coliseo_mega_boveda.py"),
        "--dias",
        str(args.dias),
        "--sleep",
        str(args.sleep),
        "--workers",
        str(args.workers),
        "--once",
    ]
    if args.only:
        cmd += ["--only", args.only]
    if getattr(args, "only_file", ""):
        cmd += ["--only-file", str(args.only_file)]
    if args.solo_tradefi:
        cmd.append("--solo-tradefi")
    if args.excluir_tradefi:
        cmd.append("--excluir-tradefi")
    if args.incluir_futures:
        cmd.append("--incluir-futures")
    if args.force:
        cmd.append("--force")

    child: subprocess.Popen | None = None

    def _start() -> subprocess.Popen:
        _log("Watchdog: relanzando worker mega bóveda…")
        return subprocess.Popen(cmd, cwd=str(ROOT))

    child = _start()
    try:
        while True:
            time.sleep(interval)
            alive = child.poll() is None
            if not alive:
                if child.returncode == 0:
                    _log("Watchdog: worker terminó OK")
                    break
                _log(f"Watchdog: worker murió rc={child.returncode} — relanzo")
                child = _start()
    finally:
        if child and child.poll() is None:
            child.terminate()


def main() -> int:
    ap = argparse.ArgumentParser(description="Mega bóveda 1m linear USDT (+ TradeFi en linear)")
    ap.add_argument("--dias", type=int, default=365)
    ap.add_argument("--sleep", type=float, default=0.12)
    ap.add_argument("--workers", type=int, default=2, help="Default 2 — catálogo grande")
    ap.add_argument("--only", type=str, default="", help="Bases CSV debug")
    ap.add_argument(
        "--only-file",
        type=str,
        default="",
        help="Archivo txt/csv con bases (una por línea o CSV) — split USA/Jess",
    )
    ap.add_argument("--solo-tradefi", action="store_true", help="Solo symbolType stock/commodity")
    ap.add_argument("--excluir-tradefi", action="store_true", help="Solo crypto")
    ap.add_argument("--incluir-futures", action="store_true", help="Incluir LinearFutures USDT")
    ap.add_argument("--force", action="store_true", help="Re-ingestar aunque checkpoint OK")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watchdog", action="store_true")
    ap.add_argument("--watchdog-min", type=int, default=15)
    args = ap.parse_args()

    if args.watchdog and not args.once:
        watchdog_loop(args)
        return 0

    MEGA_DIR.mkdir(parents=True, exist_ok=True)
    _log(
        f"START dias={args.dias} workers={args.workers} "
        f"solo_tradefi={args.solo_tradefi} excluir_tradefi={args.excluir_tradefi}"
    )
    try:
        jess._session().get_kline(category="linear", symbol="BTCUSDT", interval="1", limit=1)
    except Exception as exc:
        _log(f"Probe Bybit falló: {exc}")
        print(f"Probe falló: {exc}")
        return 2

    results = run_ingest(args)
    ok = sum(1 for r in results if r.get("ok"))
    _log(f"DONE sesión ok={ok}/{len(results)}")
    print("=" * 60)
    print("MEGA BÓVEDA — pasada terminada")
    print(f"Catálogo: {CATALOG_PATH}")
    print(f"Checkpoint: {CHECKPOINT_PATH}")
    print(f"Progreso: {PROGRESO_PATH}")
    print(f"Bóveda: {bov.BOVEDA_LINEAR_PATH}")
    print(f"Esta sesión: {ok}/{len(results)} OK")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
