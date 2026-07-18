#!/usr/bin/env python3
"""Ritual nocturno Jess — Gran Consumo bóveda spot 1m + vigilante + ranking.

Uso típico (México, toda la noche):
  python scripts/jess_boveda_coliseo_noche.py --dias 365 --watchdog

Reanudable: checkpoint en data/coliseo/checkpoint.json
Al terminar ingest → Beru Fantasma (Normal 1.6%) → pack zip para Drive.

Monarca (sin Bybit): tras recibir el zip, puede correr:
  python scripts/coliseo_beru_fantasma.py --vacios 0.012,0.016,0.020 --modo ansiedad
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import coliseo_boveda as bov


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
    for _ in range(800):
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
        except Exception as exc:
            raise RuntimeError(f"kline {symbol}: {exc}") from exc
        lst = (resp.get("result") or {}).get("list") or []
        if not lst:
            break
        chunk: list[tuple[int, float, float, float, float]] = []
        for row in lst:
            # [start, open, high, low, close, volume, turnover]
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
        time.sleep(sleep_s)
    rows.sort(key=lambda r: r[0])
    return rows


def ingest_base(
    session,
    base: str,
    *,
    dias: int,
    sleep_s: float,
    con,
) -> dict[str, Any]:
    symbol = f"{base}USDT"
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - dias * 86_400_000
    existing = bov.max_ts(con, base)
    if existing:
        # incremental: desde última vela
        start_ms = max(start_ms, existing * 1000 + 60_000)
    if start_ms >= now_ms - 60_000:
        n = bov.count_candles(con, base)
        bov.set_ingest_meta(con, base, symbol=symbol, last_ts=existing or 0, rows=n, status="ok")
        con.commit()
        return {"base": base, "ok": True, "added": 0, "rows": n, "status": "fresh"}

    bov.write_heartbeat(fase="ingest", detalle=f"Descargando {symbol}…")
    rows = _fetch_klines(session, symbol, start_ms=start_ms, end_ms=now_ms, sleep_s=sleep_s)
    added = bov.upsert_candles(con, base, rows)
    last = bov.max_ts(con, base) or 0
    total = bov.count_candles(con, base)
    bov.set_ingest_meta(con, base, symbol=symbol, last_ts=last, rows=total, status="ok")
    con.commit()
    return {"base": base, "ok": True, "added": added, "rows": total, "status": "ok"}


def _refresh_progreso(flota: list[str], con, results: list[dict]) -> None:
    lines = [
        f"# Coliseo — progreso",
        f"",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Velas totales: **{bov.count_candles(con)}**",
        f"",
        f"| Base | Estado | Filas | Añadidas |",
        f"|------|--------|------:|---------:|",
    ]
    by = {r["base"]: r for r in results}
    for b in flota:
        r = by.get(b) or {}
        st = r.get("status") or r.get("error") or "pendiente"
        lines.append(
            f"| {b} | {st} | {r.get('rows', '—')} | {r.get('added', '—')} |"
        )
    bov.write_progreso(lines)


def run_ingest(*, dias: int, sleep_s: float, only: list[str] | None) -> list[dict]:
    flota = only or _flota()
    session = _session()
    con = bov.connect()
    cp = bov.load_checkpoint()
    cp["fase"] = "ingest"
    results: list[dict] = []
    for i, base in enumerate(flota):
        try:
            r = ingest_base(session, base, dias=dias, sleep_s=sleep_s, con=con)
            results.append(r)
            cp["bases"][base] = {"status": "ok", "rows": r.get("rows"), "ts": time.time()}
            bov.save_checkpoint(cp)
            bov.write_heartbeat(
                fase="ingest",
                detalle=f"{i+1}/{len(flota)} {base} ok rows={r.get('rows')}",
            )
        except Exception as exc:
            err = {"base": base, "ok": False, "error": str(exc)[:240], "status": "error"}
            results.append(err)
            cp["bases"][base] = {"status": "error", "error": str(exc)[:240], "ts": time.time()}
            bov.save_checkpoint(cp)
            bov.write_heartbeat(fase="ingest", detalle=f"{base} ERROR {exc}", ok=False)
        _refresh_progreso(flota, con, results)
    con.close()
    return results


def run_ranking(*, vacio: float, label: str) -> Path:
    """Delega al script de fantasma (Normal por defecto en la noche)."""
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
    bov.write_heartbeat(fase="ranking", detalle=f"Fantasma vacio={vacio}…")
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


def write_manifiesto(ingest_results: list[dict], dias: int) -> None:
    bov.ensure_dirs()
    ok = sum(1 for r in ingest_results if r.get("ok"))
    lines = [
        f"# Manifiesto Coliseo",
        f"",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Días pedidos: **{dias}**",
        f"- Bases OK: **{ok}/{len(ingest_results)}**",
        f"- Bóveda: `data/coliseo/boveda_spot_1m.sqlite`",
        f"- Latidos sim: **0.05%** · path_policy **min** (peor de OHL C / OLHC)",
        f"- Ranking noche: Normal vacío **1.6%** (+ fees spot)",
        f"",
        f"## Instrucciones Monarca",
        f"1. Baja este pack por Drive a tu forja.",
        f"2. Copia `coliseo/` → `data/coliseo/`.",
        f"3. Corre Ansiedad / barrido sin Bybit:",
        f"   `python scripts/coliseo_beru_fantasma.py --vacios 0.010,0.012,0.016,0.020`",
        f"",
    ]
    (bov.COLISEO_DIR / "MANIFIESTO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (bov.COLISEO_DIR / "INSTRUCCIONES_MONARCA.md").write_text(
        "\n".join(lines[lines.index("## Instrucciones Monarca") :]) + "\n",
        encoding="utf-8",
    )


def watchdog_loop(args: argparse.Namespace) -> None:
    """Cada N minutos: si heartbeat viejo o proceso muerto, relanza ingest+ranking."""
    interval = args.watchdog_min * 60
    child: subprocess.Popen | None = None
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "jess_boveda_coliseo_noche.py"),
        "--dias",
        str(args.dias),
        "--sleep",
        str(args.sleep),
        "--once",
    ]
    if args.skip_ranking:
        cmd.append("--skip-ranking")
    if args.only:
        cmd += ["--only", args.only]

    def _start() -> subprocess.Popen:
        bov.write_heartbeat(fase="watchdog", detalle="Lanzando worker…")
        return subprocess.Popen(cmd, cwd=str(ROOT))

    child = _start()
    try:
        while True:
            time.sleep(interval)
            hb = {}
            if bov.HEARTBEAT_PATH.exists():
                try:
                    hb = json.loads(bov.HEARTBEAT_PATH.read_text(encoding="utf-8"))
                except Exception:
                    hb = {}
            age = time.time() - float(hb.get("ts") or 0)
            alive = child.poll() is None
            if not alive:
                # worker terminó
                if child.returncode == 0:
                    bov.write_heartbeat(fase="done", detalle="Worker terminó OK")
                    break
                bov.write_heartbeat(fase="watchdog", detalle="Worker muerto — relanzo", ok=False)
                child = _start()
            elif age > interval * 2:
                bov.write_heartbeat(fase="watchdog", detalle="Heartbeat viejo — reinicio", ok=False)
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
    ap = argparse.ArgumentParser(description="Coliseo nocturno Jess — bóveda + ranking")
    ap.add_argument("--dias", type=int, default=365)
    ap.add_argument("--sleep", type=float, default=0.25, help="Pausa entre páginas Bybit")
    ap.add_argument("--only", type=str, default="", help="Bases CSV (debug)")
    ap.add_argument("--skip-ranking", action="store_true")
    ap.add_argument("--skip-pack", action="store_true")
    ap.add_argument("--once", action="store_true", help="Una pasada (sin vigilante)")
    ap.add_argument("--watchdog", action="store_true", help="Vigilante cada N min")
    ap.add_argument("--watchdog-min", type=int, default=10)
    args = ap.parse_args()

    if args.watchdog and not args.once:
        watchdog_loop(args)
        return 0

    only = [x.strip().upper() for x in args.only.split(",") if x.strip()] or None
    bov.ensure_dirs()
    bov.write_heartbeat(fase="start", detalle=f"dias={args.dias}")

    # Probe Bybit
    try:
        _session().get_kline(category="spot", symbol="BTCUSDT", interval="1", limit=1)
    except Exception as exc:
        msg = str(exc)
        if "403" in msg:
            print("HTTP 403 — este ritual es para México (Jess). Abortando.")
        print(f"Probe falló: {exc}")
        return 2

    results = run_ingest(dias=args.dias, sleep_s=args.sleep, only=only)
    write_manifiesto(results, args.dias)

    if not args.skip_ranking:
        try:
            run_ranking(vacio=float(getattr(config, "BERU_VACIO_NORMAL", 0.016)), label="normal_1p6")
        except Exception as exc:
            bov.write_heartbeat(fase="ranking", detalle=f"Error ranking: {exc}", ok=False)
            print(f"Ranking falló (bóveda igual quedó): {exc}")

    zip_path = None
    if not args.skip_pack:
        zip_path = pack_drive()

    cp = bov.load_checkpoint()
    cp["fase"] = "done"
    bov.save_checkpoint(cp)
    bov.write_heartbeat(
        fase="done",
        detalle=f"Listo. zip={zip_path.name if zip_path else '—'}",
    )
    print("=" * 60)
    print("COLISEO NOCHE — DONE")
    print(f"Bóveda: {bov.BOVEDA_PATH}")
    if zip_path:
        print(f"Pack Drive: {zip_path}")
    print(f"Progreso: {bov.PROGRESO_PATH}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
