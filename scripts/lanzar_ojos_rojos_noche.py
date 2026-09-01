#!/usr/bin/env python3
"""Noche — ojos papel todos los rojos piedra OKX, en lotes (no tumbar WS).

Sin manos · sin capital · MODO_SIMULACION.
Parte 72 Santos en varios procesos (~18 WS cada uno).

Uso:
  python scripts/lanzar_ojos_rojos_noche.py
  python scripts/lanzar_ojos_rojos_noche.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASIG = ROOT / "data" / "beru" / "rango" / "piedra_asignacion.json"
LOG_DIR = ROOT / "data" / "beru"
MANIFEST = ROOT / "data" / "beru" / "rango" / "ojos_rojos_papel_manifest.json"
OJOS = ROOT / "scripts" / "arise_beru_rango_ojos.py"
CHUNK = 18


def _rojos() -> list[str]:
    data = json.loads(ASIG.read_text(encoding="utf-8"))
    out: list[str] = []
    for base, row in sorted((data.get("activos") or {}).items()):
        if isinstance(row, dict) and str(row.get("semaforo") or "").lower() == "rojo":
            out.append(str(base).upper())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, default=CHUNK)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rojos = _rojos()
    if not rojos:
        print("Sin rojos en piedra_asignacion.json", file=sys.stderr)
        return 1

    chunk = max(6, int(args.chunk))
    lotes: list[list[str]] = [
        rojos[i : i + chunk] for i in range(0, len(rojos), chunk)
    ]

    env_base = {
        **os.environ,
        "BERU_MAR": "okx",
        "BERU_RANGO_PERFIL": "piedra",
        "BERU_RANGO_MANOS": "false",
        "MODO_SIMULACION": "true",
        "PYTHONUTF8": "1",
    }

    procs: list[dict] = []
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Rojos: {len(rojos)} en {len(lotes)} lotes (chunk={chunk})")
    for i, lote in enumerate(lotes):
        tag = f"lote{i+1}"
        out_log = LOG_DIR / f"_ojos_rojos_{tag}_stdout.log"
        err_log = LOG_DIR / f"_ojos_rojos_{tag}_stderr.log"
        cmd = [
            sys.executable,
            "-u",
            str(OJOS),
            "--santos",
            ",".join(lote),
        ]
        print(f"  {tag}: {len(lote)} Santos -> {out_log.name}")
        if args.dry_run:
            continue
        p = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            env=env_base,
            stdout=out_log.open("w", encoding="utf-8"),
            stderr=err_log.open("w", encoding="utf-8"),
        )
        procs.append(
            {
                "lote": tag,
                "pid": p.pid,
                "n": len(lote),
                "santos": lote,
                "stdout": str(out_log),
                "stderr": str(err_log),
            }
        )

    if args.dry_run:
        return 0

    MANIFEST.write_text(
        json.dumps(
            {
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "mar": "okx",
                "perfil": "piedra",
                "manos": "OFF",
                "n_rojos": len(rojos),
                "n_lotes": len(lotes),
                "chunk": chunk,
                "procesos": procs,
                "nota": "Revisar manana: río=WS en logs, ojos_eventos.jsonl por Santo",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Manifest: {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
