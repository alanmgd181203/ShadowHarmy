#!/usr/bin/env python3
"""Ritual nocturno Jess — SOLO Gran Consumo bóveda spot 1m (máx. velocidad).

Uso típico (México, toda la noche):
  python scripts/jess_boveda_coliseo_noche.py --dias 365 --watchdog

- Descarga flota Beru (~22) spot USDT 1m · ~1 año
- 3 puentes en paralelo (activos distintos) + pausa corta + backoff si Bybit frena
- Reanudable + vigilante cada 10 min
- Al terminar: zip para Drive (SIN simulación; el Coliseo es después)

Opcional teatro esa misma máquina:
  ... --with-ranking
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import coliseo_boveda as bov

_WRITE_LOCK = threading.Lock()
_HB_LOCK = threading.Lock()


def _session():
    from pybit.unified_trading import HTTP
    return HTTP(testnet=bool(getattr(config, "TESTNET", False)))


def _flota() -> list[str]:
    dict_path = ROOT / "config" / "diccionario_beru_flota_manto.json"
    if dict_path.exists():
        meta = json.loads(dict_path.read_text(encoding="utf-8")).get("meta") or {}
        acts = meta.get("activos") or []
        if acts:
            return [str(a).upper() for a in acts]
    return [str(a).upper() for a in (getattr(config, "ACTIVOS_BERU_FLOTA", []) or [])]


def _hb(fase: str, detalle: str, ok: bool = True) -> None:
    with _HB_LOCK:
        bov.write_heartbeat(fase=fase, detalle=detalle, ok=ok)


def _fetch_klines(
    session,
    symbol: str,
    *,
    start_ms: int,
    end_ms: int,
    sleep_s: float,
) -> list[tuple[int, float, float, float, float]]:
    """Bybit spot kline interval=1, páginas de 1000 hacia atrás."""
    rows: list[tuple[int, float, float, float, float]] = []
    cursor_end = end_ms
    seen: set[int] = set()
    fail_streak = 0
    for _ in range(900):
        if cursor_end <= start_ms:
            break
        try:
            resp = session.get_kline(
                category="spot",
                symbol=symbol,
                interval="1",
                start=start_ms,
                end=cursor_end,
                limit=1000,
            )
            fail_streak = 0
        except Exception as exc:
            fail_streak += 1
            wait = min(30.0, sleep_s * (2 ** fail_streak))
            _hb("ingest", f"{symbol} retry {fail_streak}: {exc} → sleep {wait:.1f}s", ok=False)
            time.sleep(wait)
            if fail_streak >= 8:
                raise RuntimeError(f"kline {symbol}: {exc}") from exc
            continue

        ret = resp.get("retCode")
        if ret not in (0, "0", None) and int(ret or -1) != 0:
            # rate limit / soft error
            fail_streak += 1
            wait = min(30.0, 0.5 * (2 ** fail_streak))
            time.sleep(wait)
            if fail_streak >= 8:
                raise RuntimeError(f"kline {symbol} retCode={ret} {resp.get('retMsg')}")
            continue

        lst = (resp.get("result") or {}).get("list") or []
        if not lst:
            break
        chunk: list[tuple[int, float, float, float, float]] = []
        for row in lst:
            ts = int(int(row[0]) / 1000)
            if ts < start_ms // 1000 or ts in seen:
                continue
            seen.add(ts)
            chunk.append(
                (ts, float(row[1]), float(row[2]), float(row[3]), float(row[4]))
            )
        if not chunk:
            break
        rows.extend(chunk)
        oldest_ms = int(lst[-1][0])
        if oldest_ms <= start_ms:
            break
        cursor_end = oldest_ms - 1
        if sleep_s > 0:
            time.sleep(sleep_s)
    rows.sort(key=lambda r: r[0])
    return rows


def ingest_base(
    base: str,
    *,
    dias: int,
    sleep_s: float,
) -> dict[str, Any]:
    """Descarga un activo (sesión propia) y escribe a la bóveda bajo lock."""
    symbol = f"{base}USDT"
    session = _session()
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - dias * 86_400_000

    with _WRITE_LOCK:
        con = bov.connect()
        existing = bov.max_ts(con, base)
        con.close()

    if existing:
        start_ms = max(start_ms, existing * 1000 + 60_000)
    if start_ms >= now_ms - 60_000:
        with _WRITE_LOCK:
            con = bov.connect()
            n = bov.count_candles(con, base)
            bov.set_ingest_meta(
                con, base, symbol=symbol, last_ts=existing or 0, rows=n, status="ok"
            )
            con.commit()
            con.close()
        return {"base": base, "ok": True, "added": 0, "rows": n, "status": "fresh"}

    _hb("ingest", f"Descargando {symbol}…")
    t0 = time.time()
    rows = _fetch_klines(
        session, symbol, start_ms=start_ms, end_ms=now_ms, sleep_s=sleep_s
    )
    with _WRITE_LOCK:
        con = bov.connect()
        added = bov.upsert_candles(con, base, rows)
        last = bov.max_ts(con, base) or 0
        total = bov.count_candles(con, base)
        bov.set_ingest_meta(
            con, base, symbol=symbol, last_ts=last, rows=total, status="ok"
        )
        con.commit()
        con.close()

    return {
        "base": base,
        "ok": True,
        "added": added,
        "rows": total,
        "status": "ok",
        "secs": round(time.time() - t0, 1),
    }


def _refresh_progreso(flota: list[str], results: list[dict]) -> None:
    with _WRITE_LOCK:
        con = bov.connect()
        total = bov.count_candles(con)
        con.close()
    lines = [
        f"# Coliseo — progreso (solo bóveda)",
        f"",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Velas totales: **{total}**",
        f"",
        f"| Base | Estado | Filas | Añadidas | Seg |",
        f"|------|--------|------:|---------:|----:|",
    ]
    by = {r["base"]: r for r in results}
    for b in flota:
        r = by.get(b) or {}
        st = r.get("status") or r.get("error") or "pendiente"
        lines.append(
            f"| {b} | {st} | {r.get('rows', '—')} | {r.get('added', '—')} | {r.get('secs', '—')} |"
        )
    bov.write_progreso(lines)


def run_ingest(
    *,
    dias: int,
    sleep_s: float,
    workers: int,
    only: list[str] | None,
) -> list[dict]:
    flota = only or _flota()
    # Priorizar incompletos (reanudación)
    cp = bov.load_checkpoint()
    done_ok = {
        b
        for b, meta in (cp.get("bases") or {}).items()
        if (meta or {}).get("status") == "ok"
    }
    pending = [b for b in flota if b not in done_ok] or list(flota)
    # Si todos ok pero queremos refresh incremental, procesar todos
    if len(done_ok) >= len(flota):
        pending = list(flota)

    results: list[dict] = []
    results_lock = threading.Lock()
    workers = max(1, min(workers, len(pending)))

    _hb("ingest", f"Flota {len(flota)} · pendientes {len(pending)} · workers={workers}")

    def _job(base: str) -> dict[str, Any]:
        try:
            r = ingest_base(base, dias=dias, sleep_s=sleep_s)
            with results_lock:
                results.append(r)
                cp_local = bov.load_checkpoint()
                cp_local["fase"] = "ingest"
                cp_local.setdefault("bases", {})[base] = {
                    "status": "ok",
                    "rows": r.get("rows"),
                    "ts": time.time(),
                }
                bov.save_checkpoint(cp_local)
                _refresh_progreso(flota, list(results))
            _hb("ingest", f"OK {base} rows={r.get('rows')} +{r.get('added')} ({r.get('secs')}s)")
            return r
        except Exception as exc:
            err = {
                "base": base,
                "ok": False,
                "error": str(exc)[:240],
                "status": "error",
            }
            with results_lock:
                results.append(err)
                cp_local = bov.load_checkpoint()
                cp_local.setdefault("bases", {})[base] = {
                    "status": "error",
                    "error": str(exc)[:240],
                    "ts": time.time(),
                }
                bov.save_checkpoint(cp_local)
                _refresh_progreso(flota, list(results))
            _hb("ingest", f"ERROR {base}: {exc}", ok=False)
            return err

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_job, b) for b in pending]
        for fut in as_completed(futs):
            fut.result()

    # Orden estable en progreso
    by = {r["base"]: r for r in results}
    return [by[b] for b in flota if b in by] + [r for r in results if r["base"] not in flota]


def run_ranking(*, vacio: float, label: str) -> Path:
    out = bov.COLISEO_DIR / f"ranking_{label}.json"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "coliseo_beru_fantasma.py"),
        "--vacios",
        str(vacio),
        "--out",
        str(out),
        "--path-policy",
        "min",
    ]
    _hb("ranking", f"Fantasma vacio={vacio}…")
    subprocess.check_call(cmd, cwd=str(ROOT))
    return out


def pack_drive() -> Path:
    bov.ensure_dirs()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    zip_path = bov.COLISEO_DIR / f"ShadowHarmy_Coliseo_{stamp}.zip"
    include = [
        bov.BOVEDA_PATH,
        bov.CHECKPOINT_PATH,
        bov.PROGRESO_PATH,
        bov.HEARTBEAT_PATH,
        bov.COLISEO_DIR / "MANIFIESTO.md",
        bov.COLISEO_DIR / "INSTRUCCIONES_MONARCA.md",
    ]
    include += list(bov.COLISEO_DIR.glob("ranking_*.json"))
    include += list(bov.COLISEO_DIR.glob("ranking_*.md"))
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in include:
            if p.exists():
                zf.write(p, arcname=f"coliseo/{p.name}")
    return zip_path


def write_manifiesto(ingest_results: list[dict], dias: int, workers: int) -> None:
    bov.ensure_dirs()
    ok = sum(1 for r in ingest_results if r.get("ok"))
    lines = [
        f"# Manifiesto Coliseo (bóveda only)",
        f"",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Días pedidos: **{dias}** · workers: **{workers}**",
        f"- Bases OK: **{ok}/{len(ingest_results)}**",
        f"- Bóveda: `data/coliseo/boveda_spot_1m.sqlite`",
        f"- Simulación: **NO** en esta noche (correr después en forja)",
        f"",
        f"## Instrucciones Monarca",
        f"1. Baja este pack por Drive a tu forja.",
        f"2. Copia `coliseo/` → `data/coliseo/`.",
        f"3. Teatro paralelo (sin Bybit):",
        f"   `python scripts/coliseo_beru_fantasma.py --vacios 0.010,0.012,0.016,0.020`",
        f"",
    ]
    (bov.COLISEO_DIR / "MANIFIESTO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (bov.COLISEO_DIR / "INSTRUCCIONES_MONARCA.md").write_text(
        "\n".join(lines[lines.index("## Instrucciones Monarca") :]) + "\n",
        encoding="utf-8",
    )


def watchdog_loop(args: argparse.Namespace) -> None:
    interval = args.watchdog_min * 60
    child: subprocess.Popen | None = None
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "jess_boveda_coliseo_noche.py"),
        "--dias",
        str(args.dias),
        "--sleep",
        str(args.sleep),
        "--workers",
        str(args.workers),
        "--once",
    ]
    if args.with_ranking:
        cmd.append("--with-ranking")
    if args.skip_pack:
        cmd.append("--skip-pack")
    if args.only:
        cmd += ["--only", args.only]

    def _start() -> subprocess.Popen:
        _hb("watchdog", "Lanzando worker de descarga…")
        return subprocess.Popen(cmd, cwd=str(ROOT))

    child = _start()
    try:
        while True:
            time.sleep(interval)
            hb: dict[str, Any] = {}
            if bov.HEARTBEAT_PATH.exists():
                try:
                    hb = json.loads(bov.HEARTBEAT_PATH.read_text(encoding="utf-8"))
                except Exception:
                    hb = {}
            age = time.time() - float(hb.get("ts") or 0)
            alive = child.poll() is None
            if not alive:
                if child.returncode == 0:
                    _hb("done", "Worker terminó OK")
                    break
                _hb("watchdog", "Worker muerto — relanzo", ok=False)
                child = _start()
            elif age > interval * 2:
                _hb("watchdog", "Heartbeat viejo — reinicio", ok=False)
                try:
                    child.terminate()
                    child.wait(timeout=30)
                except Exception:
                    child.kill()
                child = _start()
    finally:
        if child and child.poll() is None:
            child.terminate()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Coliseo nocturno Jess — SOLO descarga bóveda (rápido)"
    )
    ap.add_argument("--dias", type=int, default=365)
    ap.add_argument(
        "--sleep",
        type=float,
        default=0.12,
        help="Pausa entre páginas Bybit por puente (default 0.12s)",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Puentes paralelos (activos distintos). Default 3 — no subir mucho.",
    )
    ap.add_argument("--only", type=str, default="", help="Bases CSV (debug)")
    ap.add_argument(
        "--with-ranking",
        action="store_true",
        help="Opcional: al terminar, corre Fantasma Normal 1.6% (más lento)",
    )
    ap.add_argument("--skip-pack", action="store_true")
    ap.add_argument("--once", action="store_true", help="Una pasada (sin vigilante)")
    ap.add_argument("--watchdog", action="store_true", help="Vigilante cada N min")
    ap.add_argument("--watchdog-min", type=int, default=10)
    # compat flags antiguos
    ap.add_argument("--skip-ranking", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.watchdog and not args.once:
        watchdog_loop(args)
        return 0

    only = [x.strip().upper() for x in args.only.split(",") if x.strip()] or None
    bov.ensure_dirs()
    _hb("start", f"dias={args.dias} workers={args.workers} sleep={args.sleep} (bóveda only)")

    try:
        _session().get_kline(category="spot", symbol="BTCUSDT", interval="1", limit=1)
    except Exception as exc:
        if "403" in str(exc):
            print("HTTP 403 — este ritual es para México (Jess). Abortando.")
        print(f"Probe falló: {exc}")
        return 2

    results = run_ingest(
        dias=args.dias,
        sleep_s=args.sleep,
        workers=args.workers,
        only=only,
    )
    write_manifiesto(results, args.dias, args.workers)

    if args.with_ranking:
        try:
            run_ranking(
                vacio=float(getattr(config, "BERU_VACIO_NORMAL", 0.016)),
                label="normal_1p6",
            )
        except Exception as exc:
            _hb("ranking", f"Error ranking: {exc}", ok=False)
            print(f"Ranking falló (bóveda igual quedó): {exc}")

    zip_path = None
    if not args.skip_pack:
        zip_path = pack_drive()

    cp = bov.load_checkpoint()
    cp["fase"] = "done"
    bov.save_checkpoint(cp)
    _hb("done", f"Bóveda lista. zip={zip_path.name if zip_path else '—'}")
    print("=" * 60)
    print("COLISEO NOCHE — BÓVEDA DONE (sin simulación)")
    print(f"Bóveda: {bov.BOVEDA_PATH}")
    if zip_path:
        print(f"Pack Drive: {zip_path}")
    print(f"Progreso: {bov.PROGRESO_PATH}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
