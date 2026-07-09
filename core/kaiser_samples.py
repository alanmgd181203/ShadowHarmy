"""Muestreo de desvíos Kaiser — persistencia local para perfiles multietiqueta."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import core.config as config

ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = ROOT / "data" / "kaiser" / "samples"


def _ruta_muestras(base: str, edge: str) -> Path:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    safe = f"{base.upper()}_{edge}".replace("/", "_")
    return SAMPLES_DIR / f"{safe}.jsonl"


def append_sample(
    base: str,
    edge: str,
    *,
    signed_pct: float,
    abs_pct: float | None = None,
    ts: float | None = None,
    huerfana: bool = False,
    ref_tipo: str = "index",
    extra: dict | None = None,
) -> None:
    ts = ts or time.time()
    abs_pct = abs_pct if abs_pct is not None else abs(signed_pct)
    row = {
        "ts": ts,
        "base": base.upper(),
        "edge": edge,
        "signed_pct": round(signed_pct, 6),
        "abs_pct": round(abs_pct, 6),
        "huerfana": huerfana,
        "ref_tipo": ref_tipo,
    }
    if extra:
        row.update(extra)
    path = _ruta_muestras(base, edge)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")
    _trim_archivo(path)


def _trim_archivo(path: Path) -> None:
    max_days = getattr(config, "KAISER_SAMPLE_MAX_DAYS", 400)
    cutoff = time.time() - max_days * 86400
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    kept = []
    for ln in lines:
        try:
            row = json.loads(ln)
            if float(row.get("ts", 0)) >= cutoff:
                kept.append(ln)
        except json.JSONDecodeError:
            continue
    max_lines = getattr(config, "KAISER_SAMPLE_MAX_LINES", 25000)
    if len(kept) > max_lines:
        kept = kept[-max_lines:]
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def load_samples(base: str, edge: str, since_ts: float = 0) -> list[dict]:
    path = _ruta_muestras(base, edge)
    if not path.exists():
        return []
    out: list[dict] = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            row = json.loads(ln)
            if float(row.get("ts", 0)) >= since_ts:
                out.append(row)
    except (OSError, json.JSONDecodeError):
        return []
    out.sort(key=lambda r: r["ts"])
    return out


def bulk_append_samples(rows: list[dict], base: str, edge: str) -> int:
    if not rows:
        return 0
    path = _ruta_muestras(base, edge)
    with open(path, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    _trim_archivo(path)
    return len(rows)


def bases_con_muestras() -> list[str]:
    if not SAMPLES_DIR.exists():
        return []
    bases: set[str] = set()
    for p in SAMPLES_DIR.glob("*.jsonl"):
        name = p.stem
        if "_" in name:
            bases.add(name.split("_", 1)[0])
    return sorted(bases)
