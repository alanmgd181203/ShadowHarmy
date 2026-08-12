#!/usr/bin/env python3
"""Ritual nocturno Jess — bóveda velas 1s (historial Igris) / 1m (Coliseo spot).

Historial Igris (L/S 1s; spot Bybit no da 1s):
  python scripts/jess_noche_historial_igris.py --dias 7 --watchdog

Coliseo spot 1m:
  python scripts/jess_boveda_coliseo_noche.py --dias 365 --solo-spot --interval 1 --watchdog
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
_DICT_CACHE: dict[str, Any] | None = None


def _session():
    from pybit.unified_trading import HTTP
    return HTTP(testnet=False)


def _load_dict() -> dict[str, Any]:
    global _DICT_CACHE
    if _DICT_CACHE is not None:
        return _DICT_CACHE
    dict_path = ROOT / "config" / "diccionario_beru_flota_manto.json"
    if dict_path.exists():
        _DICT_CACHE = json.loads(dict_path.read_text(encoding="utf-8"))
    else:
        _DICT_CACHE = {}
    return _DICT_CACHE


def _flota() -> list[str]:
    meta = (_load_dict().get("meta") or {})
    acts = meta.get("activos") or []
    if acts:
        return [str(a).upper() for a in acts]
    return [str(a).upper() for a in (getattr(config, "ACTIVOS_BERU_FLOTA", []) or [])]


def _symbol_for(base: str, market: str) -> str:
    """Símbolo Bybit: spot/linear = BASEUSDT · inverse = BASEUSD (diccionario)."""
    bu = base.upper()
    m = market.lower()
    activos = (_load_dict().get("activos") or {})
    row = activos.get(bu) or {}
    if m == "inverse":
        return str(row.get("symbol_inverse") or f"{bu}USD")
    if m == "linear":
        return str(row.get("symbol_linear") or f"{bu}USDT")
    return f"{bu}USDT"


def _hb(fase: str, detalle: str, ok: bool = True) -> None:
    with _HB_LOCK:
        bov.write_heartbeat(fase=fase, detalle=detalle, ok=ok)


def _fetch_klines(
    session,
    symbol: str,
    *,
    category: str,
    start_ms: int,
    end_ms: int,
    sleep_s: float,
    interval: str = "1",
) -> list[tuple[int, float, float, float, float]]:
    """Bybit kline — interval 1 (1m) o 1s · páginas de 1000 hacia atrás."""
    iv = (interval or "1").strip()
    rows: list[tuple[int, float, float, float, float]] = []
    cursor_end = end_ms
    seen: set[int] = set()
    fail_streak = 0
    for _ in range(9000 if iv == "1s" else 900):
        if cursor_end <= start_ms:
            break
        try:
            resp = session.get_kline(
                category=category,
                symbol=symbol,
                interval=iv,
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
                raise RuntimeError(f"kline {category}/{symbol}: {exc}") from exc
            continue

        ret = resp.get("retCode")
        if ret not in (0, "0", None) and int(ret or -1) != 0:
            fail_streak += 1
            wait = min(30.0, 0.5 * (2 ** fail_streak))
            time.sleep(wait)
            if fail_streak >= 8:
                raise RuntimeError(
                    f"kline {category}/{symbol} retCode={ret} {resp.get('retMsg')}"
                )
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


def ingest_one(
    base: str,
    market: str,
    *,
    dias: int,
    sleep_s: float,
    interval: str = "1",
) -> dict[str, Any]:
    """Descarga un activo×mercado y escribe a su bóveda bajo lock."""
    symbol = _symbol_for(base, market)
    category = market.lower()
    iv = (interval or bov.get_interval()).strip()
    session = _session()
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - dias * 86_400_000
    db = bov.boveda_path(category)
    step_ms = 1000 if iv == "1s" else 60_000
    fresh_ms = 2_000 if iv == "1s" else 60_000

    with _WRITE_LOCK:
        con = bov.connect(db)
        existing = bov.max_ts(con, base)
        con.close()

    if existing:
        start_ms = max(start_ms, existing * 1000 + step_ms)
    if start_ms >= now_ms - fresh_ms:
        with _WRITE_LOCK:
            con = bov.connect(db)
            n = bov.count_candles(con, base)
            bov.set_ingest_meta(
                con, base, symbol=symbol, last_ts=existing or 0, rows=n, status="ok"
            )
            con.commit()
            con.close()
        return {
            "base": base,
            "market": category,
            "ok": True,
            "added": 0,
            "rows": n,
            "status": "fresh",
            "interval": iv,
        }

    _hb("ingest", f"Descargando {category}/{symbol} interval={iv}…")
    t0 = time.time()
    rows = _fetch_klines(
        session,
        symbol,
        category=category,
        start_ms=start_ms,
        end_ms=now_ms,
        sleep_s=sleep_s,
        interval=iv,
    )
    with _WRITE_LOCK:
        con = bov.connect(db)
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
        "market": category,
        "ok": True,
        "added": added,
        "rows": total,
        "status": "ok",
        "secs": round(time.time() - t0, 1),
        "interval": iv,
    }


def _job_key(base: str, market: str) -> str:
    return bov.ck_key(base, market)


def _legacy_spot_ok(cp: dict, base: str) -> bool:
    """Checkpoint viejo guardaba solo BASE (spot)."""
    meta = (cp.get("bases") or {}).get(base) or {}
    return (meta or {}).get("status") == "ok"


def _refresh_progreso(
    flota: list[str], markets: list[str], results: list[dict]
) -> None:
    totals: list[str] = []
    with _WRITE_LOCK:
        for m in markets:
            con = bov.connect(bov.boveda_path(m))
            totals.append(f"{m}={bov.count_candles(con)}")
            con.close()
    lines = [
        f"# Historial / Coliseo — progreso bóveda ({bov.interval_label()})",
        f"",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Intervalo: **{bov.interval_label()}**",
        f"- Velas: **{', '.join(totals)}**",
        f"- Flota Igris (diccionario manto): **{len(flota)}** · mercados: `{','.join(markets)}`",
        f"",
        f"| Base | Mar | Estado | Filas | Añadidas | Seg |",
        f"|------|-----|--------|------:|---------:|----:|",
    ]
    by = {(r["base"], r.get("market", "spot")): r for r in results}
    for b in flota:
        for m in markets:
            r = by.get((b, m)) or {}
            st = r.get("status") or r.get("error") or "pendiente"
            lines.append(
                f"| {b} | {m} | {st} | {r.get('rows', '—')} | {r.get('added', '—')} | {r.get('secs', '—')} |"
            )
    bov.write_progreso(lines)


def run_ingest(
    *,
    dias: int,
    sleep_s: float,
    workers: int,
    only: list[str] | None,
    markets: list[str],
    interval: str = "1",
) -> list[dict]:
    flota = only or _flota()
    iv = bov.set_interval(interval)
    # Orden: spot primero, luego linear, inverse (prioridad Monarca)
    order = [m for m in ("spot", "linear", "inverse") if m in markets]
    # Spot no soporta 1s en Bybit mainnet — saltear
    if iv == "1s":
        order = [m for m in order if m != "spot"]
        if not order:
            order = ["linear", "inverse"]
    jobs: list[tuple[str, str]] = [(b, m) for m in order for b in flota]

    cp = bov.load_checkpoint()
    done_ok: set[str] = set()
    for k, meta in (cp.get("bases") or {}).items():
        if (meta or {}).get("status") != "ok":
            continue
        done_ok.add(str(k))
        if "@" not in str(k):
            done_ok.add(bov.ck_key(str(k), "spot"))

    pending: list[tuple[str, str]] = []
    for b, m in jobs:
        key = _job_key(b, m)
        if key in done_ok:
            continue
        if m == "spot" and _legacy_spot_ok(cp, b):
            continue
        pending.append((b, m))

    if not pending:
        pending = list(jobs)  # refresh incremental

    results: list[dict] = []
    results_lock = threading.Lock()
    workers = max(1, min(workers, len(pending) or 1))

    _hb(
        "ingest",
        f"Flota {len(flota)} · mercados {order} · pendientes {len(pending)} · workers={workers}",
    )

    def _job(pair: tuple[str, str]) -> dict[str, Any]:
        base, market = pair
        try:
            r = ingest_one(base, market, dias=dias, sleep_s=sleep_s, interval=iv)
            with results_lock:
                results.append(r)
                cp_local = bov.load_checkpoint()
                cp_local["fase"] = "ingest"
                cp_local.setdefault("bases", {})[_job_key(base, market)] = {
                    "status": "ok",
                    "market": market,
                    "rows": r.get("rows"),
                    "ts": time.time(),
                }
                bov.save_checkpoint(cp_local)
                _refresh_progreso(flota, order, list(results))
            _hb(
                "ingest",
                f"OK {market}/{base} rows={r.get('rows')} +{r.get('added')} ({r.get('secs')}s)",
            )
            return r
        except Exception as exc:
            err = {
                "base": base,
                "market": market,
                "ok": False,
                "error": str(exc)[:240],
                "status": "error",
            }
            with results_lock:
                results.append(err)
                cp_local = bov.load_checkpoint()
                cp_local.setdefault("bases", {})[_job_key(base, market)] = {
                    "status": "error",
                    "market": market,
                    "error": str(exc)[:240],
                    "ts": time.time(),
                }
                bov.save_checkpoint(cp_local)
                _refresh_progreso(flota, order, list(results))
            _hb("ingest", f"ERROR {market}/{base}: {exc}", ok=False)
            return err

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_job, p) for p in pending]
        for fut in as_completed(futs):
            fut.result()

    by = {(r["base"], r.get("market", "spot")): r for r in results}
    ordered = [by[p] for p in jobs if p in by]
    extras = [r for r in results if (r["base"], r.get("market", "spot")) not in dict.fromkeys(jobs)]
    return ordered + extras


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
    label = bov.interval_label()
    zip_path = bov.COLISEO_DIR / f"ShadowHarmy_Coliseo_{label}_{stamp}.zip"
    # Rutas del intervalo activo (1s / 1m) — no las constantes legacy 1m
    include = [
        bov.boveda_path("spot"),
        bov.boveda_path("linear"),
        bov.boveda_path("inverse"),
        bov.checkpoint_path(),
        bov.PROGRESO_PATH,
        bov.HEARTBEAT_PATH,
        bov.COLISEO_DIR / "MANIFIESTO.md",
        bov.COLISEO_DIR / "INSTRUCCIONES_MONARCA.md",
        bov.COLISEO_DIR / "NOTA_MONARCA_NOCHE_1s.md",
    ]
    include += list(bov.COLISEO_DIR.glob("ranking_*.json"))
    include += list(bov.COLISEO_DIR.glob("ranking_*.md"))
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in include:
            if p.exists() and p.is_file():
                zf.write(p, arcname=f"coliseo/{p.name}")
    return zip_path


def write_manifiesto(
    ingest_results: list[dict],
    dias: int,
    workers: int,
    markets: list[str],
    ritual: str,
) -> None:
    bov.ensure_dirs()
    ok = sum(1 for r in ingest_results if r.get("ok"))
    titulo = (
        "Historial flota Igris (bóveda noche)"
        if ritual == "historial_igris"
        else "Coliseo (bóveda only)"
    )
    lines = [
        f"# Manifiesto {titulo}",
        f"",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Ritual: **{ritual}** · días: **{dias}** · workers: **{workers}** · intervalo: **{bov.interval_label()}**",
        f"- Mercados: `{','.join(markets)}`",
        f"- Pares OK: **{ok}/{len(ingest_results)}**",
        f"- Spot: `{bov.boveda_path('spot').name}`",
        f"- Linear: `{bov.boveda_path('linear').name}`",
        f"- Inverse: `{bov.boveda_path('inverse').name}`",
        f"- **NO es 4.0.3 Asalto** (sin manos Igris)",
        f"- Simulación Fantasma: **NO** en esta noche (correr después en forja)",
        f"",
        f"## Instrucciones Monarca",
        f"1. Baja este pack por Drive a tu forja.",
        f"2. Copia `coliseo/` → `data/coliseo/`.",
        f"3. Teatro paralelo (sin Bybit), si aplica:",
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
        "--markets",
        args.markets,
        "--ritual",
        args.ritual,
        "--interval",
        str(getattr(args, "interval", "1")),
        "--once",
    ]
    if args.with_ranking:
        cmd.append("--with-ranking")
    if args.skip_pack:
        cmd.append("--skip-pack")
    if args.only:
        cmd += ["--only", args.only]
    if args.solo_spot:
        cmd.append("--solo-spot")

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


def _parse_markets(raw: str, solo_spot: bool) -> list[str]:
    if solo_spot:
        return ["spot"]
    parts = [x.strip().lower() for x in (raw or "").split(",") if x.strip()]
    out: list[str] = []
    for p in parts:
        if p not in bov.MARKETS:
            raise SystemExit(f"Mercado inválido: {p} (válidos: {','.join(bov.MARKETS)})")
        if p not in out:
            out.append(p)
    return out or ["spot"]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Noche Jess — bóveda velas 1s/1m flota Igris / Coliseo (sin manos)"
    )
    ap.add_argument("--dias", type=int, default=365)
    ap.add_argument(
        "--interval",
        type=str,
        default="1",
        help="Bybit kline: 1 (minuto) o 1s (segundo). Default 1.",
    )
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
        help="Puentes paralelos (pares distintos). Default 3 — no subir mucho.",
    )
    ap.add_argument("--only", type=str, default="", help="Bases CSV (debug)")
    ap.add_argument(
        "--markets",
        type=str,
        default="spot",
        help="Mercados CSV: spot,linear,inverse (default spot = Coliseo clásico)",
    )
    ap.add_argument(
        "--solo-spot",
        action="store_true",
        help="Solo spot (alias Coliseo clásico)",
    )
    ap.add_argument(
        "--ritual",
        type=str,
        default="coliseo",
        help="Etiqueta manifiesto: coliseo | historial_igris",
    )
    ap.add_argument(
        "--with-ranking",
        action="store_true",
        help="Opcional: al terminar, corre Fantasma Normal 1.6 pct (mas lento)",
    )
    ap.add_argument("--skip-pack", action="store_true")
    ap.add_argument("--once", action="store_true", help="Una pasada (sin vigilante)")
    ap.add_argument("--watchdog", action="store_true", help="Vigilante cada N min")
    ap.add_argument("--watchdog-min", type=int, default=10)
    ap.add_argument("--skip-ranking", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    markets = _parse_markets(args.markets, args.solo_spot)
    iv = bov.set_interval(args.interval)
    if iv == "1s":
        # Spot no tiene 1s; forzar L/S si el usuario pidió spot en la mezcla
        markets = [m for m in markets if m != "spot"] or ["linear", "inverse"]
        # 1s es denso: si alguien deja 365 por error, aun así avanza con checkpoint
        args.sleep = max(float(args.sleep), 0.08)
    args.markets = ",".join(markets)

    if args.watchdog and not args.once:
        watchdog_loop(args)
        return 0

    only = [x.strip().upper() for x in args.only.split(",") if x.strip()] or None
    bov.ensure_dirs()
    _hb(
        "start",
        f"ritual={args.ritual} dias={args.dias} interval={iv} markets={args.markets} "
        f"workers={args.workers} sleep={args.sleep}",
    )

    try:
        probe_cat = "linear" if iv == "1s" else "spot"
        probe_sym = "ETHUSDT" if iv == "1s" else "BTCUSDT"
        _session().get_kline(
            category=probe_cat, symbol=probe_sym, interval=iv, limit=1
        )
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
        markets=markets,
        interval=iv,
    )
    write_manifiesto(results, args.dias, args.workers, markets, args.ritual)

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
    print(f"NOCHE BÓVEDA DONE — ritual={args.ritual} (sin manos / no 4.0.3)")
    print(f"Mercados: {args.markets}")
    print(f"Spot: {bov.BOVEDA_PATH}")
    if "linear" in markets:
        print(f"Linear: {bov.BOVEDA_LINEAR_PATH}")
    if "inverse" in markets:
        print(f"Inverse: {bov.BOVEDA_INVERSE_PATH}")
    if zip_path:
        print(f"Pack Drive: {zip_path}")
    print(f"Progreso: {bov.PROGRESO_PATH}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
