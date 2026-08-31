#!/usr/bin/env python3
"""Auditoría doctrinal feria lineal — más allá del smoke."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANGO = ROOT / "data" / "beru" / "rango"
LISTA = RANGO / "feria_ejercito_147.txt"

FERIA = {
    "perfil": "feria",
    "vacio_pct": 0.022,
    "oz_gap_pct": 0.004,
    "red_pct": 0.012,
    "engorde_paso_pct": 0.002,
    "engorde_usd": 1.0,
    "masa_usd": 5.0,
}


def cargar_lista() -> list[str]:
    if LISTA.is_file():
        raw = LISTA.read_text(encoding="utf-8").strip()
        return sorted({s.strip().upper() for s in raw.replace("\n", ",").split(",") if s.strip()})
    return sorted(
        p.parent.name
        for p in RANGO.glob("*/manos_feria_informe.json")
    )


def auditar() -> int:
    santos = cargar_lista()
    ok = fail = sin_inf = 0
    problemas: list[str] = []

    for s in santos:
        path = RANGO / s / "manos_feria_informe.json"
        err_path = RANGO / s / "manos_feria_stderr.log"
        if not path.is_file():
            sin_inf += 1
            tail = ""
            if err_path.is_file():
                tail = err_path.read_text(encoding="utf-8", errors="replace")[-200:]
            problemas.append(f"{s}: SIN_INFORME stderr_tail={tail!r}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail += 1
            problemas.append(f"{s}: JSON_ROTO {exc}")
            continue
        snap = data.get("snapshot") or {}
        geo = snap.get("geometria") or {}
        vivo = snap.get("vivo") or {}
        errs = []
        if str(data.get("perfil_beru") or geo.get("perfil") or "").lower() != FERIA["perfil"]:
            errs.append(f"perfil={data.get('perfil_beru') or geo.get('perfil')}")
        for k, want in (
            ("vacio_pct", FERIA["vacio_pct"]),
            ("oz_gap_pct", FERIA["oz_gap_pct"]),
            ("engorde_paso_pct", FERIA["engorde_paso_pct"]),
            ("engorde_usd", FERIA["engorde_usd"]),
            ("masa_usd", FERIA["masa_usd"]),
        ):
            got = float(geo.get(k) or 0)
            if abs(got - want) > 1e-9:
                errs.append(f"{k}={got} want={want}")
        rl = float(geo.get("red_activacion_long_pct") or 0)
        rs = float(geo.get("red_activacion_short_pct") or 0)
        if abs(rl - FERIA["red_pct"]) > 1e-9 or abs(rs - FERIA["red_pct"]) > 1e-9:
            errs.append(f"red L/S={rl}/{rs} want={FERIA['red_pct']}")
        if abs(rl - rs) > 1e-12:
            errs.append(f"red ASIMETRICA L={rl} S={rs}")
        est = str(vivo.get("estado") or "")
        if est not in ("ACECHANDO", "CAZANDO"):
            errs.append(f"estado={est!r}")
        if errs:
            fail += 1
            problemas.append(f"{s}: " + "; ".join(errs))
        else:
            ok += 1

    print(f"[AUDIT FERIA] lista={len(santos)} OK={ok} FAIL={fail} SIN_INF={sin_inf}")
    for p in problemas[:40]:
        print(f"  !! {p}")
    if len(problemas) > 40:
        print(f"  ... +{len(problemas) - 40} mas")
    return 0 if fail == 0 and sin_inf == 0 else 1


if __name__ == "__main__":
    raise SystemExit(auditar())
