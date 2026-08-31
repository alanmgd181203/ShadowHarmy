#!/usr/bin/env python3
"""Escanea sellos Beru rango → despiertos.json para el teatro fusionado.

Criterio: carpeta data/beru/rango/{SANTO}/ con manos_informe (wake hecho).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RANGO_DIR = ROOT / "data" / "beru" / "rango"
OUT = ROOT / "data" / "coliseo" / "rango_juicio" / "despiertos.json"
VIVO = ROOT / "data" / "beru" / "rango_vivo.json"

SKIP_NAMES = frozenset(
    {
        "checkpoint_doctrina_normal.json",
        "preparar_sanidad.json",
        "lote_despertar_ejercito.json",
        "sanidad_lap.json",
        "ojos_flota_eventos.jsonl",
    }
)


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return default


def _leer_vivo_ahora() -> set[str]:
    if not VIVO.exists():
        return set()
    try:
        j = json.loads(VIVO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    out: set[str] = set()
    for row in j.get("activos") or []:
        a = str(row.get("activo") or "").upper().strip()
        if a:
            out.add(a)
    foco = str(j.get("activo_foco") or "").upper().strip()
    if foco:
        out.add(foco)
    return out


def escanear() -> dict[str, Any]:
    vivos_ahora = _leer_vivo_ahora()
    santos: dict[str, dict[str, Any]] = {}
    if not RANGO_DIR.is_dir():
        return {"santos": {}, "lista": []}

    for p in sorted(RANGO_DIR.iterdir()):
        if not p.is_dir():
            continue
        act = p.name.upper()
        informe = p / "manos_informe.json"
        if not informe.is_file():
            continue
        try:
            raw = json.loads(informe.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        snap = raw.get("snapshot") or {}
        vivo = snap.get("vivo") or {}
        cero = _f(vivo.get("cero"))
        estado = str(vivo.get("estado") or "").upper() or None
        ts = _f(raw.get("ts"))
        santos[act] = {
            "activo": act,
            "despierto": True,
            "estado": estado,
            "cero": cero if cero > 0 else None,
            "manos": bool(raw.get("manos")),
            "en_vivo_ahora": act in vivos_ahora,
            "ts_informe": ts if ts > 0 else None,
            "cosechas": int(vivo.get("cosechas") or 0),
        }

    lista = sorted(santos.keys())
    return {"santos": santos, "lista": lista}


def main() -> int:
    data = escanear()
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "n_despiertos": len(data["lista"]),
        "n_vivos_ahora": sum(1 for s in data["santos"].values() if s.get("en_vivo_ahora")),
        "santos": data["santos"],
        "lista": data["lista"],
        "nota": "Santo con manos_informe = despertado al menos una vez. en_vivo_ahora desde rango_vivo.json.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK -> {OUT} · despiertos={payload['n_despiertos']} · vivos_ahora={payload['n_vivos_ahora']}")
    if payload["lista"]:
        print("  " + ", ".join(payload["lista"][:20]) + ("…" if len(payload["lista"]) > 20 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
