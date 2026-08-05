#!/usr/bin/env python3
"""4×10min arise_igris_sim — resumible; guarda parte tras cada marcha.

Reanuda marchas ya selladas (report_* + SUCESION en log).
Uso:
  python3 scripts/run_marchas_10m.py
  python3 scripts/run_marchas_10m.py --segundos 600
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from core import pase_director as pd  # noqa: E402

OUT_DIR = ROOT / "data" / "logs" / "marchas_10m"
REPORT = ROOT / "data" / "arise_igris_sim_report.json"
PARCIAL = OUT_DIR / "resumen_parcial.json"
FINAL = OUT_DIR / "resumen_monarca.json"
HEARTBEAT = OUT_DIR / "heartbeat.json"

MARCHAS = [
    ("tactico", None),
    ("marcha_forzada", None),
    ("asalto", None),
    ("personalizado", 0.007),  # ~10 min T calibración
]

TAG_KEYS = (
    "BOOTSTRAP_MANTO",
    "BOOTSTRAP_LOTE",
    "ENGORDE_DUAL",
    "ENGORDE_LOTE",
    "ErrCode: 10002",
    "RECONEXIÓN",
    "SUCESION",
    "Traceback",
)


def _beat(msg: str, **extra) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pid": os.getpid(),
        "msg": msg,
        **extra,
    }
    HEARTBEAT.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_parcial() -> dict:
    if not PARCIAL.exists():
        return {
            "ts_start": time.time(),
            "segundos_por_marcha": None,
            "corridas": [],
            "reanudaciones": 0,
        }
    try:
        data = json.loads(PARCIAL.read_text(encoding="utf-8"))
    except Exception:
        data = {"ts_start": time.time(), "corridas": [], "reanudaciones": 0}
    data.setdefault("corridas", [])
    data.setdefault("reanudaciones", 0)
    return data


def _save_parcial(resumen: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    resumen["ts_parcial"] = time.time()
    PARCIAL.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")


def snap_from_report() -> dict:
    if not REPORT.exists():
        return {}
    try:
        return json.loads(REPORT.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": str(e)}


def count_tags(log: Path) -> dict[str, int]:
    if not log.exists():
        return {}
    t = log.read_text(encoding="utf-8", errors="replace")
    return {k: t.count(k) for k in TAG_KEYS}


def marcha_sellada(mid: str) -> bool:
    """Sello = reporte copiado + ritual con SUCESION (o exit previo OK en parcial)."""
    rep = OUT_DIR / f"report_{mid}.json"
    log = OUT_DIR / f"sim_{mid}.log"
    if rep.exists() and log.exists() and count_tags(log).get("SUCESION", 0) > 0:
        return True
    parcial = _load_parcial()
    for c in parcial.get("corridas") or []:
        if c.get("marcha_id") == mid and c.get("ok") and not c.get("error"):
            return True
    return False


def entry_from_disk(mid: str, dias) -> dict | None:
    rep_path = OUT_DIR / f"report_{mid}.json"
    log = OUT_DIR / f"sim_{mid}.log"
    if not rep_path.exists():
        return None
    try:
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
    except Exception:
        rep = {}
    meta = rep.get("meta_engorde") or {}
    return {
        "marcha_id": mid,
        "duracion_dias_calibracion": dias,
        "wall_s": None,
        "exit_code": 0,
        "ok": True,
        "reanudado": True,
        "report_duracion_s": rep.get("duracion_s"),
        "equity_usd": rep.get("equity_usd"),
        "n_frentes_peso": rep.get("n_frentes_peso"),
        "have_usd": meta.get("have_usd"),
        "restante_usd": meta.get("restante_usd"),
        "activo_meta": meta.get("activo"),
        "tags": count_tags(log),
        "log": str(log.relative_to(ROOT)),
        "report_copy": str(rep_path.relative_to(ROOT)),
    }


def run_one(mid: str, dias, seg: int) -> dict:
    print("\n" + "=" * 60)
    print(f"MARCHA {mid} dias={dias} — arranque {time.strftime('%H:%M:%S')}")
    print("=" * 60, flush=True)
    _beat("marcha_start", marcha=mid)

    if mid == "personalizado":
        pd.guardar_marcha(mid, duracion_dias=float(dias))
    else:
        pd.guardar_marcha(mid)

    if REPORT.exists():
        REPORT.unlink()

    log = OUT_DIR / f"sim_{mid}.log"
    rep_copy = OUT_DIR / f"report_{mid}.json"
    # Append marker if re-running after failure mid-log
    with open(log, "a", encoding="utf-8") as fout:
        fout.write(f"\n\n##### RELANZADO {time.strftime('%Y-%m-%d %H:%M:%S')} mid={mid} #####\n")

    t0 = time.time()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    with open(log, "a", encoding="utf-8") as fout:
        proc = subprocess.run(
            [sys.executable, "-u", str(ROOT / "scripts" / "arise_igris_sim.py"), "--segundos", str(seg)],
            cwd=str(ROOT),
            stdout=fout,
            stderr=subprocess.STDOUT,
            env=env,
        )
    dt = time.time() - t0
    rep = snap_from_report()
    if REPORT.exists():
        rep_copy.write_text(REPORT.read_text(encoding="utf-8"), encoding="utf-8")
    meta = rep.get("meta_engorde") or {}
    tags = count_tags(log)
    ok = (
        proc.returncode == 0
        and tags.get("SUCESION", 0) > 0
        and rep_copy.exists()
    )
    entry = {
        "marcha_id": mid,
        "duracion_dias_calibracion": dias,
        "wall_s": round(dt, 1),
        "exit_code": proc.returncode,
        "ok": ok,
        "report_duracion_s": rep.get("duracion_s"),
        "equity_usd": rep.get("equity_usd"),
        "n_frentes_peso": rep.get("n_frentes_peso"),
        "have_usd": meta.get("have_usd"),
        "restante_usd": meta.get("restante_usd"),
        "activo_meta": meta.get("activo"),
        "tags": tags,
        "log": str(log.relative_to(ROOT)),
        "report_copy": str(rep_copy.relative_to(ROOT)) if rep_copy.exists() else None,
    }
    if not ok:
        entry["error"] = (
            f"sellado incompleto exit={proc.returncode} "
            f"sucesion={tags.get('SUCESION', 0)} report={rep_copy.exists()}"
        )
    _beat("marcha_end", marcha=mid, ok=ok, wall_s=entry["wall_s"])
    return entry


def upsert_corrida(resumen: dict, entry: dict) -> None:
    mid = entry["marcha_id"]
    corridas = [c for c in resumen.get("corridas") or [] if c.get("marcha_id") != mid]
    corridas.append(entry)
    # Orden canónico
    order = {m: i for i, (m, _) in enumerate(MARCHAS)}
    corridas.sort(key=lambda c: order.get(c.get("marcha_id"), 99))
    resumen["corridas"] = corridas


def main() -> int:
    ap = argparse.ArgumentParser(description="Batida 4 marchas × N segundos (resumible)")
    ap.add_argument("--segundos", type=int, default=int(os.getenv("MARCHAS_10M_SEG", "600") or 600))
    ap.add_argument(
        "--fresh",
        action="store_true",
        help="Ignora sellos previos y borra reports/logs de esta batida",
    )
    args = ap.parse_args()
    seg = max(30, int(args.segundos))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.fresh:
        for mid, _ in MARCHAS:
            for p in (OUT_DIR / f"sim_{mid}.log", OUT_DIR / f"report_{mid}.json"):
                if p.exists():
                    p.unlink()
        if PARCIAL.exists():
            PARCIAL.unlink()
        if FINAL.exists():
            FINAL.unlink()

    resumen = _load_parcial()
    resumen["segundos_por_marcha"] = seg
    if FINAL.exists() and all(marcha_sellada(m) for m, _ in MARCHAS):
        print("Ya hay sello completo — nada que hacer.", flush=True)
        _beat("already_done")
        return 0

    resumen["reanudaciones"] = int(resumen.get("reanudaciones") or 0) + 1
    _save_parcial(resumen)
    _beat("run_start", reanudacion=resumen["reanudaciones"])

    try:
        for mid, dias in MARCHAS:
            if marcha_sellada(mid):
                existing = entry_from_disk(mid, dias)
                if existing:
                    upsert_corrida(resumen, existing)
                    _save_parcial(resumen)
                    print(f"[SKIP] {mid} ya sellada", flush=True)
                continue

            try:
                entry = run_one(mid, dias, seg)
            except Exception as e:
                entry = {
                    "marcha_id": mid,
                    "duracion_dias_calibracion": dias,
                    "ok": False,
                    "error": f"excepcion: {type(e).__name__}: {e}",
                }
                print(f"[FAIL] {mid}: {entry['error']}", flush=True)

            upsert_corrida(resumen, entry)
            _save_parcial(resumen)
            print(json.dumps(entry, ensure_ascii=False, indent=2), flush=True)

            if not entry.get("ok"):
                # Salir ≠0 para que el guardián relance y reanude
                _beat("need_relaunch", marcha=mid, error=entry.get("error"))
                print(f"[GUARDIÁN] Marcha {mid} incompleta — exit 2 para relance", flush=True)
                return 2

        try:
            pd.guardar_marcha("marcha_forzada")
        except Exception:
            pass
        resumen["ts_end"] = time.time()
        resumen["marcha_restored"] = "marcha_forzada"
        FINAL.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
        _save_parcial(resumen)
        _beat("done")
        print("\nSELLADO resumen →", FINAL, flush=True)
        return 0
    except KeyboardInterrupt:
        _save_parcial(resumen)
        _beat("interrupted")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
