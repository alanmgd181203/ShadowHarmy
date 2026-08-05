#!/usr/bin/env python3
"""Guardián: mantiene la batida 4×10min viva; relanza si se cae; guarda heartbeat.

Uso:
  python3 scripts/vigilar_marchas_10m.py
  python3 scripts/vigilar_marchas_10m.py --segundos 600 --fresh

Deja PID en data/logs/marchas_10m/guardian.pid
Parte: resumen_parcial.json (mientras) → resumen_monarca.json (al sellar)
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "logs" / "marchas_10m"
FINAL = OUT / "resumen_monarca.json"
PARCIAL = OUT / "resumen_parcial.json"
HEARTBEAT = OUT / "heartbeat.json"
GUARDIAN_LOG = OUT / "guardian.log"
GUARDIAN_PID = OUT / "guardian.pid"
RUNNER = ROOT / "scripts" / "run_marchas_10m.py"


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(GUARDIAN_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def done() -> bool:
    if not FINAL.exists():
        return False
    try:
        data = json.loads(FINAL.read_text(encoding="utf-8"))
    except Exception:
        return False
    ids = {c.get("marcha_id") for c in data.get("corridas") or [] if c.get("ok")}
    return ids >= {"tactico", "marcha_forzada", "asalto", "personalizado"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--segundos", type=int, default=600)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--max-relaunch", type=int, default=20)
    ap.add_argument("--poll-s", type=float, default=15.0)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    GUARDIAN_PID.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    log(f"guardián arranca pid={os.getpid()} seg={args.segundos} fresh={args.fresh}")

    relaunches = 0
    first = True

    while True:
        if done():
            log("sello completo — guardián termina")
            return 0

        if relaunches > args.max_relaunch:
            log(f"ABORT: demasiados relances ({relaunches})")
            return 1

        cmd = [sys.executable, "-u", str(RUNNER), "--segundos", str(args.segundos)]
        if first and args.fresh:
            cmd.append("--fresh")
        first = False

        # caffeinate evita sueño idle del Mac mientras corre el batallón
        full = ["caffeinate", "-i", *cmd]
        log(f"lanzando corrida #{relaunches + 1}: {' '.join(full)}")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        with open(OUT / "orquestador.log", "a", encoding="utf-8") as fout:
            fout.write(f"\n##### GUARDIÁN LANZA {time.strftime('%Y-%m-%d %H:%M:%S')} #####\n")
            proc = subprocess.Popen(
                full,
                cwd=str(ROOT),
                stdout=fout,
                stderr=subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )

        (OUT / "orquestador.pid").write_text(str(proc.pid) + "\n", encoding="utf-8")

        while True:
            code = proc.poll()
            hb = {}
            if HEARTBEAT.exists():
                try:
                    hb = json.loads(HEARTBEAT.read_text(encoding="utf-8"))
                except Exception:
                    hb = {}
            log(
                f"watch pid={proc.pid} code={code} hb={hb.get('msg')} "
                f"marcha={hb.get('marcha')} parcial={PARCIAL.exists()} final={FINAL.exists()}"
            )
            if done():
                try:
                    proc.terminate()
                except Exception:
                    pass
                log("sello detectado — saliendo")
                return 0
            if code is not None:
                break
            time.sleep(max(5.0, float(args.poll_s)))

        log(f"corrida terminó exit={code}")
        if done():
            log("sello completo tras corrida")
            return 0
        # exit 0 pero incompleto → también relanzar
        relaunches += 1
        log(f"relance en 5s (#{relaunches})…")
        time.sleep(5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("guardián interrumpido")
        raise SystemExit(130)
