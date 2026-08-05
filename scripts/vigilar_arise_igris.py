#!/usr/bin/env python3
"""Guardián 4.0.3 arise_igris — DEFAULT OFF / solo tras --confirmar-go.

Mantiene el ritual parcial vivo: relanza si cae, caffeinate, deadline ~12h.

  # Sin GO: solo imprime ayuda
  python3 scripts/vigilar_arise_igris.py

  # Smoke ojos (el runner puede ir directo; guardián opcional)
  python3 scripts/arise_igris.py --solo-ojos --segundos 90

  # GO ~12h (manos ON; mainnet exige --permitir-mainnet-manos)
  python3 scripts/vigilar_arise_igris.py --confirmar-go \\
      --durar-hasta 2026-08-05T18:30:00 --permitir-mainnet-manos

PID: data/logs/arise_igris/guardian.pid
Heartbeat: data/logs/arise_igris/heartbeat.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "logs" / "arise_igris"
REPORT = ROOT / "data" / "arise_igris_report.json"
HEARTBEAT = OUT / "heartbeat.json"
GUARDIAN_LOG = OUT / "guardian.log"
GUARDIAN_PID = OUT / "guardian.pid"
RUNNER = ROOT / "scripts" / "arise_igris.py"


def log(msg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(GUARDIAN_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _parse_deadline(raw: str) -> float | None:
    s = (raw or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return None


def sellado_limpio() -> bool:
    """True si el reporte indica cierre voluntario (no bloqueo) tras deadline."""
    if not HEARTBEAT.exists():
        return False
    try:
        hb = json.loads(HEARTBEAT.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(hb.get("sellado")) and not hb.get("bloqueo")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Guardián arise_igris 4.0.3 (OFF por defecto; exige --confirmar-go)"
    )
    ap.add_argument(
        "--confirmar-go",
        action="store_true",
        help="Obligatorio: el Monarca ordenó soltar el ejército parcial",
    )
    ap.add_argument("--horas", type=float, default=12.0)
    ap.add_argument("--segundos", type=float, default=0.0)
    ap.add_argument(
        "--durar-hasta",
        type=str,
        default="",
        help="Deadline local YYYY-MM-DDTHH:MM:SS (preferible vs --horas)",
    )
    ap.add_argument("--max-relaunch", type=int, default=8)
    ap.add_argument("--poll-s", type=float, default=25.0)
    ap.add_argument(
        "--solo-ojos",
        action="store_true",
        help="Pasar --solo-ojos al ritual (sin manos Igris)",
    )
    ap.add_argument(
        "--permitir-mainnet-manos",
        action="store_true",
        help="Pasar flag de seguridad mainnet al ritual",
    )
    ap.add_argument(
        "--sin-caffeinate",
        action="store_true",
        help="No usar caffeinate (Linux/VPS)",
    )
    args = ap.parse_args()

    if not args.confirmar_go:
        print(
            "[guardián arise_igris] OFF por doctrina.\n"
            " Solo tras orden GO del Monarca:\n"
            "   python3 scripts/vigilar_arise_igris.py --confirmar-go \\\n"
            "       --durar-hasta 2026-08-05T18:30:00 --permitir-mainnet-manos\n"
            " Smoke ojos (sin guardián):\n"
            "   python3 scripts/arise_igris.py --solo-ojos --segundos 90\n"
            " Ver migracion/CHECKPOINT_IGRIS_LIVE_4_0_3.md",
            flush=True,
        )
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    GUARDIAN_PID.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    # Campo limpio: no heredar sellado/bloqueo del smoke previo
    for stale in (HEARTBEAT,):
        if stale.exists():
            try:
                stale.unlink()
                log(f"quitado stale {stale.name}")
            except OSError as e:
                log(f"AVISO: no pude quitar {stale.name}: {e}")

    deadline = (args.durar_hasta or "").strip()
    dl_ts = _parse_deadline(deadline) if deadline else None
    if deadline and dl_ts is None:
        log(f"ABORT: no entiendo --durar-hasta={deadline}")
        return 2

    log(
        f"guardián arise_igris ON pid={os.getpid()} "
        f"durar_hasta={deadline or '-'} horas={args.horas} "
        f"solo_ojos={args.solo_ojos} mainnet_flag={args.permitir_mainnet_manos}"
    )

    relaunches = 0
    while True:
        if dl_ts is not None and time.time() >= dl_ts:
            log("deadline alcanzado — guardián no relanza más")
            return 0

        if relaunches > args.max_relaunch:
            log(f"ABORT: demasiados relances ({relaunches})")
            return 1

        cmd = [sys.executable, "-u", str(RUNNER)]
        if args.solo_ojos:
            cmd.append("--solo-ojos")
        if args.permitir_mainnet_manos:
            cmd.append("--permitir-mainnet-manos")
        if deadline:
            cmd.extend(["--durar-hasta", deadline])
        elif args.segundos > 0:
            cmd.extend(["--segundos", str(args.segundos)])
        else:
            cmd.extend(["--horas", str(args.horas)])

        full = cmd if args.sin_caffeinate else ["caffeinate", "-i", *cmd]
        log(f"lanzando #{relaunches + 1}: {' '.join(full)}")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        with open(OUT / "orquestador.log", "a", encoding="utf-8") as fout:
            fout.write(f"\n##### GUARDIÁN ARISE_IGRIS {time.strftime('%Y-%m-%d %H:%M:%S')} #####\n")
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
            hb: dict = {}
            if HEARTBEAT.exists():
                try:
                    hb = json.loads(HEARTBEAT.read_text(encoding="utf-8"))
                except Exception:
                    hb = {}
            log(
                f"watch pid={proc.pid} code={code} hb={hb.get('msg')} "
                f"books={hb.get('books_eth')} bloqueo={hb.get('bloqueo')}"
            )
            if hb.get("bloqueo"):
                try:
                    proc.terminate()
                except Exception:
                    pass
                log("bloqueo del ritual (sin libros / gate) — no zombie, no relanzo")
                return 2
            if dl_ts is not None and time.time() >= dl_ts:
                try:
                    proc.terminate()
                except Exception:
                    pass
                log("deadline — terminando orquestador")
                try:
                    proc.wait(timeout=30)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                return 0
            if code is not None:
                break
            time.sleep(max(5.0, float(args.poll_s)))

        log(f"corrida terminó exit={code}")
        if code == 2 or (HEARTBEAT.exists() and json.loads(HEARTBEAT.read_text(encoding="utf-8") or "{}").get("bloqueo")):
            log("exit por bloqueo — no relanzo")
            return 2
        if dl_ts is not None and time.time() >= dl_ts:
            log("deadline tras exit — no relanzo")
            return 0 if sellado_limpio() or REPORT.exists() else 1
        # exit 0 limpio antes de deadline → relanzar para cubrir la ventana
        relaunches += 1
        log(f"relance en 8s (#{relaunches})…")
        time.sleep(8)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("guardián interrumpido")
        raise SystemExit(130)
