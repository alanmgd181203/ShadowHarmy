#!/usr/bin/env python3
"""Monedas muertas (pico alto → precio basura) → fuera absoluto.

Regla Monarca:
  - Pico histórico ≥ $5 y precio actual < $0.10 → fuera
  - Pico histórico ≥ $2 y precio actual < $0.01 → fuera

Pico = MAX(high) en bóveda 1m. Actual = último close.
Sirve para sacar del ranking activos muertos / liquidación brusca.

Actualiza data/coliseo/rango_juicio/filtros_absolutos.json (campos muerta_*).

Uso:
  python scripts/armar_filtro_muertas_fusion.py
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BOVEDA = ROOT / "data" / "coliseo" / "boveda_linear_1m.sqlite"
FILTROS = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_absolutos.json"
CK = (
    ROOT
    / "data"
    / "coliseo"
    / "rango_juicio"
    / "matriz"
    / "normal_reciente"
    / "checkpoint_parcial.json"
)

PICO5 = 5.0
LAST5 = 0.10
PICO2 = 2.0
LAST2 = 0.01


def bases_juicio(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[str] = []
    seen: set[str] = set()
    for row in data.get("ranking") or []:
        a = str(row.get("activo") or "").upper().strip()
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    return out


def clasificar_muerta(pico: float | None, last: float | None) -> dict[str, Any]:
    if pico is None or last is None:
        return {
            "muerta_pico_usd": None,
            "muerta_last_usd": None,
            "muerta_fuera": False,
            "muerta_motivo": None,
            "muerta_sin_historia": True,
        }
    motivo: str | None = None
    if pico >= PICO5 and last < LAST5:
        motivo = "pico5_lt_0.1"
    elif pico >= PICO2 and last < LAST2:
        motivo = "pico2_lt_0.01"
    return {
        "muerta_pico_usd": round(float(pico), 8),
        "muerta_last_usd": round(float(last), 8),
        "muerta_fuera": motivo is not None,
        "muerta_motivo": motivo,
        "muerta_sin_historia": False,
    }


def cargar_pico_y_last(
    con: sqlite3.Connection, bases: list[str]
) -> dict[str, tuple[float | None, float | None]]:
    """Una pasada agregada + join de último close (sin N+1)."""
    if not bases:
        return {}
    wanted = set(bases)
    picos: dict[str, float] = {}
    for base, hi in con.execute("SELECT base, MAX(high) FROM candles GROUP BY base"):
        b = str(base or "").upper().strip()
        if b in wanted and hi is not None:
            picos[b] = float(hi)

    lasts: dict[str, float] = {}
    sql = """
        SELECT c.base, c.close
        FROM candles c
        INNER JOIN (
            SELECT base, MAX(ts) AS mts FROM candles GROUP BY base
        ) t ON c.base = t.base AND c.ts = t.mts
    """
    for base, close in con.execute(sql):
        b = str(base or "").upper().strip()
        if b in wanted and close is not None:
            lasts[b] = float(close)

    out: dict[str, tuple[float | None, float | None]] = {}
    for b in bases:
        out[b] = (picos.get(b), lasts.get(b))
    return out


def _recompute_fuera(cur: dict[str, Any]) -> None:
    cur["fuera"] = bool(
        cur.get("min_orden_fuera")
        or cur.get("extremo_fuera")
        or cur.get("liquidez_fuera")
        or cur.get("pico_masa_fuera")
        or cur.get("leverage_fuera")
        or cur.get("rango_anual_fuera")
        or cur.get("listado_reciente_fuera")
        or cur.get("muerta_fuera")
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Filtro monedas muertas (pico→basura)")
    ap.add_argument("--boveda", type=Path, default=BOVEDA)
    ap.add_argument("--checkpoint", type=Path, default=CK)
    ap.add_argument("--out", type=Path, default=FILTROS)
    args = ap.parse_args()

    bases = bases_juicio(args.checkpoint)
    payload = json.loads(args.out.read_text(encoding="utf-8"))
    activos = payload.setdefault("activos", {})

    con = sqlite3.connect(f"file:{args.boveda}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    t0 = time.time()
    print(f"Leyendo bóveda ({len(bases)} bases)…", flush=True)
    mapa = cargar_pico_y_last(con, bases)
    con.close()
    print(f"  agregados listos · {time.time() - t0:.1f}s", flush=True)

    n_fuera = n_ok = n_sin = 0
    n_r1 = n_r2 = 0
    ejemplos: list[tuple[str, float, float, str]] = []
    motivos_drop = ("muerta_pico5_lt_0.1", "muerta_pico2_lt_0.01")

    for base in bases:
        pico, last = mapa.get(base, (None, None))
        row = clasificar_muerta(pico, last)
        cur = activos.setdefault(base, {})
        cur.update(row)
        motivos = [m for m in (cur.get("motivos") or []) if m not in motivos_drop]
        if row["muerta_fuera"] and row["muerta_motivo"] == "pico5_lt_0.1":
            motivos.append("muerta_pico5_lt_0.1")
            n_fuera += 1
            n_r1 += 1
            if len(ejemplos) < 12:
                ejemplos.append((base, float(pico or 0), float(last or 0), "pico5_lt_0.1"))
        elif row["muerta_fuera"] and row["muerta_motivo"] == "pico2_lt_0.01":
            motivos.append("muerta_pico2_lt_0.01")
            n_fuera += 1
            n_r2 += 1
            if len(ejemplos) < 12:
                ejemplos.append((base, float(pico or 0), float(last or 0), "pico2_lt_0.01"))
        elif row.get("muerta_sin_historia"):
            n_sin += 1
        else:
            n_ok += 1
        cur["motivos"] = motivos
        _recompute_fuera(cur)

    meta = payload.setdefault("meta", {})
    meta["ts_muertas_utc"] = datetime.now(timezone.utc).isoformat()
    meta["muerta_pico5_usd"] = PICO5
    meta["muerta_last5_usd"] = LAST5
    meta["muerta_pico2_usd"] = PICO2
    meta["muerta_last2_usd"] = LAST2
    meta["n_fuera_muertas"] = n_fuera
    meta["n_fuera_muertas_pico5"] = n_r1
    meta["n_fuera_muertas_pico2"] = n_r2
    meta["n_muertas_sin_historia"] = n_sin
    meta["nota_muertas"] = (
        "Fuera si pico boveda >=$5 y last<$0.10, o pico>=$2 y last<$0.01 "
        "(monedas muertas / liquidacion brusca)."
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK -> {args.out} · fuera={n_fuera} (pico5={n_r1} pico2={n_r2}) · "
        f"ok={n_ok} · sin={n_sin} · {time.time() - t0:.1f}s",
        flush=True,
    )
    for base, pico, last, motivo in ejemplos:
        print(f"  ej {base}: pico={pico:.6g} last={last:.6g} · {motivo}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
