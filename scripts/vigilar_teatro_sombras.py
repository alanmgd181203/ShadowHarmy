#!/usr/bin/env python3
"""Guardián del teatro de sombras — DEFAULT OFF / solo tras orden GO.

NO arrancar por costumbre. Requiere --confirmar-go explícito.

Uso (ejemplo, tras GO del Monarca — óptica Tank por defecto):
  python3 scripts/vigilar_teatro_sombras.py --confirmar-go --horas 8

Demo sintético (sin mercado):
  python3 scripts/vigilar_teatro_sombras.py --confirmar-go --sintetico --segundos 60

Sin --confirmar-go: imprime ayuda y sale 0 (no lanza caffeinate).
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
OUT = ROOT / "data" / "logs" / "teatro_sombras"
FINAL = OUT / "resumen_monarca.json"
HEARTBEAT = OUT / "heartbeat.json"
GUARDIAN_LOG = OUT / "guardian.log"
GUARDIAN_PID = OUT / "guardian.pid"
RUNNER = ROOT / "scripts" / "teatro_sombras_igris.py"


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
    return bool((data.get("meta") or {}).get("sellado"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Guardián teatro sombras (OFF por defecto; exige --confirmar-go)"
    )
    ap.add_argument(
        "--confirmar-go",
        action="store_true",
        help="Obligatorio: el Monarca ordenó soltar el teatro",
    )
    ap.add_argument("--horas", type=float, default=8.0)
    ap.add_argument("--segundos", type=float, default=0.0)
    ap.add_argument(
        "--durar-hasta",
        type=str,
        default="",
        help="Deadline local YYYY-MM-DDTHH:MM:SS (preferible vs --horas en overnight)",
    )
    ap.add_argument("--intervalo", type=float, default=5.0)
    ap.add_argument("--activo", type=str, default="ETH")
    ap.add_argument("--max-relaunch", type=int, default=10)
    ap.add_argument("--poll-s", type=float, default=20.0)
    ap.add_argument(
        "--sintetico",
        action="store_true",
        help="Demo sin mercado (no pasa --optica-tank al runner)",
    )
    ap.add_argument(
        "--con-libros",
        action="store_true",
        help="Con óptica Tank: suscribir orderbooks (pesado)",
    )
    ap.add_argument(
        "--sin-caffeinate",
        action="store_true",
        help="No usar caffeinate (útil en Linux/VPS)",
    )
    args = ap.parse_args()

    if not args.confirmar_go:
        print(
            "[guardián teatro] OFF por doctrina.\n"
            " Solo tras orden GO del Monarca (óptica Tank):\n"
            "   python3 scripts/vigilar_teatro_sombras.py --confirmar-go --durar-hasta 2026-08-05T06:00:00\n"
            "   python3 scripts/vigilar_teatro_sombras.py --confirmar-go --horas 8\n"
            " Demo sintético:\n"
            "   python3 scripts/vigilar_teatro_sombras.py --confirmar-go --sintetico --segundos 60\n"
            " Preparar sin batida:\n"
            "   python3 scripts/teatro_sombras_igris.py --preparar\n"
            " Ver migracion/TEATRO_SOMBRAS_IGRIS.md",
            flush=True,
        )
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    # Campo limpio al GO: quitar sello viejo para que esta noche escriba de cero
    if FINAL.exists():
        try:
            FINAL.unlink()
            log("sello previo quitado (nueva batida)")
        except OSError as e:
            log(f"AVISO: no pude quitar sello previo: {e}")

    GUARDIAN_PID.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    optica = "sintetico" if args.sintetico else "tank"
    deadline = (args.durar_hasta or "").strip()
    log(
        f"guardián teatro ON pid={os.getpid()} "
        f"durar_hasta={deadline or '-'} horas={args.horas} optica={optica} (post-GO)"
    )

    relaunches = 0
    while True:
        if deadline:
            # Parse laxo: epoch o ISO local
            try:
                dl_ts = float(deadline)
            except ValueError:
                from datetime import datetime as _dt

                dl_ts = None
                for fmt in (
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M",
                    "%Y-%m-%d %H:%M",
                ):
                    try:
                        dl_ts = _dt.strptime(deadline, fmt).timestamp()
                        break
                    except ValueError:
                        continue
                if dl_ts is None:
                    log(f"ABORT: no entiendo --durar-hasta={deadline}")
                    return 2
            if time.time() >= dl_ts:
                log("deadline alcanzado — guardián no relanza más")
                return 0 if done() else 1

        if done():
            log("sello completo — guardián termina")
            return 0
        if relaunches > args.max_relaunch:
            log(f"ABORT: demasiados relances ({relaunches})")
            return 1

        cmd = [
            sys.executable, "-u", str(RUNNER),
            "--go",
            "--activo", str(args.activo),
            "--intervalo", str(args.intervalo),
        ]
        if args.sintetico:
            cmd.append("--sintetico")
        else:
            # GO serio: óptica Tank viva (doctrina guardián)
            cmd.append("--optica-tank")
            if args.con_libros:
                cmd.append("--con-libros")
        # Tras un crash: no borrar decisiones.jsonl; el runner aún resetea contadores
        # en memoria — el jsonl acumula historia de la noche.
        if relaunches > 0:
            cmd.append("--sin-campo-limpio")
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
            fout.write(f"\n##### GUARDIÁN TEATRO {time.strftime('%Y-%m-%d %H:%M:%S')} #####\n")
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
            log(f"watch pid={proc.pid} code={code} hb={hb.get('msg')} ciclos={hb.get('ciclos')}")
            if deadline:
                try:
                    dl_check = float(deadline)
                except ValueError:
                    from datetime import datetime as _dt

                    dl_check = None
                    for fmt in (
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M",
                        "%Y-%m-%d %H:%M",
                    ):
                        try:
                            dl_check = _dt.strptime(deadline, fmt).timestamp()
                            break
                        except ValueError:
                            continue
                if dl_check is not None and time.time() >= dl_check and done():
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    log("deadline + sello — guardián termina")
                    return 0
            if done():
                try:
                    proc.terminate()
                except Exception:
                    pass
                log("sello detectado")
                return 0
            if code is not None:
                break
            time.sleep(max(5.0, float(args.poll_s)))

        log(f"corrida terminó exit={code}")
        if done():
            return 0
        if deadline:
            try:
                dl_ts2 = float(deadline)
            except ValueError:
                from datetime import datetime as _dt

                dl_ts2 = None
                for fmt in (
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M",
                    "%Y-%m-%d %H:%M",
                ):
                    try:
                        dl_ts2 = _dt.strptime(deadline, fmt).timestamp()
                        break
                    except ValueError:
                        continue
            if dl_ts2 is not None and time.time() >= dl_ts2:
                log("deadline tras exit — no relanzo")
                return 1
        relaunches += 1
        log(f"relance en 5s (#{relaunches})…")
        time.sleep(5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("guardián interrumpido")
        raise SystemExit(130)
