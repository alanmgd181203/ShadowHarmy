#!/usr/bin/env python3
"""Rango de precio último año (bóveda 1m) → sombreado panel teatro.

Métrica: (max_high − min_low) / last_close × 100 en ~365 días.
  (last_close = último cierre en la ventana; no el promedio — el avg aplastaba
   caídas fuertes: HOME ~900% vs precio actual salía como “rojo 247%”.)
  · verde    ≤ 200%  — rango moderado vs precio de hoy
  · amarillo ≤ 500%  — movido
  · rojo     ≤ 800%  — muy explosivo (sombreado · sigue en ranking)
  · fuera    > 800%  — eliminar del panel (filtro duro)

Actualiza data/coliseo/rango_juicio/filtros_absolutos.json (campos rango_anual_*).

Uso:
  python scripts/armar_rango_anual_fusion.py
  python scripts/armar_rango_anual_fusion.py --dias 365
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

VERDE_MAX = 200.0
AMARILLO_MAX = 500.0
ROJO_MAX = 800.0


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


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


def rango_anual(con: sqlite3.Connection, base: str, *, ts_min: int) -> dict[str, Any]:
    row = con.execute(
        """
        SELECT MIN(low), MAX(high), AVG(close), COUNT(*)
        FROM candles
        WHERE base = ? AND ts >= ?
        """,
        (base, ts_min),
    ).fetchone()
    last_row = con.execute(
        """
        SELECT close FROM candles
        WHERE base = ? AND ts >= ?
        ORDER BY ts DESC LIMIT 1
        """,
        (base, ts_min),
    ).fetchone()
    if not row or not row[3]:
        return {
            "rango_anual_pct": None,
            "rango_anual_banda": None,
            "rango_anual_fuera": False,
            "rango_anual_n": 0,
        }
    lo = _f(row[0])
    hi = _f(row[1])
    avg = _f(row[2])
    n = int(row[3] or 0)
    last = _f(last_row[0]) if last_row else 0.0
    if last <= 0 or hi <= 0 or lo <= 0 or hi < lo:
        return {
            "rango_anual_pct": None,
            "rango_anual_banda": None,
            "rango_anual_fuera": False,
            "rango_anual_n": n,
        }
    # Denominador = precio de hoy (no el promedio: el avg esconde caídas).
    pct = (hi - lo) / last * 100.0
    pct_r = round(pct, 2)
    if pct > ROJO_MAX:
        banda, fuera = "fuera", True
    elif pct > AMARILLO_MAX:
        banda, fuera = "rojo", False
    elif pct > VERDE_MAX:
        banda, fuera = "amarillo", False
    else:
        banda, fuera = "verde", False
    return {
        "rango_anual_pct": pct_r,
        "rango_anual_banda": banda,
        "rango_anual_fuera": fuera,
        "rango_anual_min_low": lo,
        "rango_anual_max_high": hi,
        "rango_anual_avg_close": round(avg, 8),
        "rango_anual_last_close": round(last, 8),
        "rango_anual_n": n,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Rango anual bóveda → sombreado teatro")
    ap.add_argument("--dias", type=int, default=365)
    ap.add_argument("--boveda", type=Path, default=BOVEDA)
    ap.add_argument("--checkpoint", type=Path, default=CK)
    ap.add_argument("--out", type=Path, default=FILTROS)
    args = ap.parse_args()

    bases = bases_juicio(args.checkpoint)
    ts_min = int(time.time()) - int(args.dias) * 86400
    payload = json.loads(args.out.read_text(encoding="utf-8"))
    activos = payload.setdefault("activos", {})

    con = sqlite3.connect(f"file:{args.boveda}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")

    n_verde = n_amarillo = n_rojo = n_fuera = n_sin = 0
    t0 = time.time()
    for i, base in enumerate(bases, 1):
        row = rango_anual(con, base, ts_min=ts_min)
        cur = activos.setdefault(base, {})
        cur.update(row)
        motivos = [m for m in (cur.get("motivos") or []) if not str(m).startswith("rango_anual_gt_")]
        if row["rango_anual_fuera"]:
            motivos.append("rango_anual_gt_800")
            n_fuera += 1
        elif row["rango_anual_banda"] == "verde":
            n_verde += 1
        elif row["rango_anual_banda"] == "amarillo":
            n_amarillo += 1
        elif row["rango_anual_banda"] == "rojo":
            n_rojo += 1
        else:
            n_sin += 1
        cur["motivos"] = motivos
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
        if i % 50 == 0 or i == len(bases):
            print(
                f"  {i}/{len(bases)} · V={n_verde} A={n_amarillo} R={n_rojo} "
                f"X={n_fuera} ?={n_sin} · {time.time() - t0:.0f}s",
                flush=True,
            )

    con.close()
    meta = payload.setdefault("meta", {})
    meta["ts_rango_anual_utc"] = datetime.now(timezone.utc).isoformat()
    meta["rango_anual_dias"] = int(args.dias)
    meta["rango_anual_verde_max_pct"] = VERDE_MAX
    meta["rango_anual_amarillo_max_pct"] = AMARILLO_MAX
    meta["rango_anual_rojo_max_pct"] = ROJO_MAX
    meta["n_rango_verde"] = n_verde
    meta["n_rango_amarillo"] = n_amarillo
    meta["n_rango_rojo"] = n_rojo
    meta["n_fuera_rango_anual"] = n_fuera
    meta["nota_rango_anual"] = (
        "(max−min)/last_close ×100 en bóveda 1m (precio de hoy, no promedio). "
        "Sombra verde≤200% · amarillo≤500% · rojo≤800% (visible) · fuera>800%."
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK → {args.out} · verde={n_verde} amarillo={n_amarillo} "
        f"rojo={n_rojo} fuera>{ROJO_MAX}%={n_fuera}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
