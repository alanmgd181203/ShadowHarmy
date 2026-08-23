#!/usr/bin/env python3
"""Edad en bóveda → filtro listado reciente (solo crypto).

Regla Monarca: crypto con < 90 días desde la primera vela en bóveda → fuera.
TradeFi (acciones, ETF, commodity, fx) queda exento — pueden existir años antes del listado Bybit.

Actualiza data/coliseo/rango_juicio/filtros_absolutos.json (campos listado_*).

Uso:
  python scripts/armar_edad_listado_fusion.py
  python scripts/armar_edad_listado_fusion.py --meses 3
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
FICHAS = ROOT / "data" / "coliseo" / "rango_juicio" / "santos_ficha.json"
CK = (
    ROOT
    / "data"
    / "coliseo"
    / "rango_juicio"
    / "matriz"
    / "normal_reciente"
    / "checkpoint_parcial.json"
)

TRADEFI_TYPES = frozenset({"stock", "commodity", "etf", "fx", "forex"})


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


def es_tradefi_exento(ficha: dict[str, Any]) -> bool:
    if ficha.get("tradefi"):
        return True
    t = str(ficha.get("symbol_type") or "").lower()
    return t in TRADEFI_TYPES


def edad_listado(
    con: sqlite3.Connection,
    base: str,
    *,
    min_dias: float,
    ficha: dict[str, Any],
) -> dict[str, Any]:
    exento = es_tradefi_exento(ficha)
    row = con.execute(
        "SELECT MIN(ts), COUNT(*) FROM candles WHERE base = ?",
        (base,),
    ).fetchone()
    ts0 = int(row[0]) if row and row[0] is not None else 0
    n = int(row[1] or 0) if row else 0
    now = time.time()
    if ts0 <= 0 or n <= 0:
        return {
            "listado_primer_ts": None,
            "listado_edad_dias": None,
            "listado_reciente_fuera": False if exento else True,
            "listado_tradefi_exento": exento,
            "listado_n_velas": n,
            "listado_sin_historia": True,
        }
    edad_d = (now - ts0) / 86400.0
    reciente = (not exento) and edad_d < min_dias
    return {
        "listado_primer_ts": ts0,
        "listado_edad_dias": round(edad_d, 2),
        "listado_reciente_fuera": reciente,
        "listado_tradefi_exento": exento,
        "listado_n_velas": n,
        "listado_sin_historia": False,
    }


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
    ap = argparse.ArgumentParser(description="Filtro edad listado crypto (<3 meses fuera)")
    ap.add_argument("--meses", type=float, default=3.0)
    ap.add_argument("--boveda", type=Path, default=BOVEDA)
    ap.add_argument("--checkpoint", type=Path, default=CK)
    ap.add_argument("--out", type=Path, default=FILTROS)
    args = ap.parse_args()

    min_dias = max(1.0, float(args.meses) * 30.4375)
    bases = bases_juicio(args.checkpoint)
    fichas = (json.loads(FICHAS.read_text(encoding="utf-8")).get("por_base") or {})
    payload = json.loads(args.out.read_text(encoding="utf-8"))
    activos = payload.setdefault("activos", {})

    con = sqlite3.connect(f"file:{args.boveda}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")

    n_fuera = n_exento = n_ok = n_sin = 0
    t0 = time.time()
    for i, base in enumerate(bases, 1):
        ficha = fichas.get(base) or {}
        row = edad_listado(con, base, min_dias=min_dias, ficha=ficha)
        cur = activos.setdefault(base, {})
        cur.update(row)
        motivos = [m for m in (cur.get("motivos") or []) if m != "listado_lt_90d"]
        if row["listado_reciente_fuera"]:
            motivos.append("listado_lt_90d")
            n_fuera += 1
        elif row.get("listado_tradefi_exento"):
            n_exento += 1
        elif row.get("listado_sin_historia"):
            n_sin += 1
        else:
            n_ok += 1
        cur["motivos"] = motivos
        _recompute_fuera(cur)
        if i % 100 == 0 or i == len(bases):
            print(
                f"  {i}/{len(bases)} · fuera={n_fuera} ok={n_ok} exento={n_exento} "
                f"sin={n_sin} · {time.time() - t0:.0f}s",
                flush=True,
            )

    con.close()
    meta = payload.setdefault("meta", {})
    meta["ts_listado_utc"] = datetime.now(timezone.utc).isoformat()
    meta["listado_min_meses"] = float(args.meses)
    meta["listado_min_dias"] = round(min_dias, 2)
    meta["n_fuera_listado_reciente"] = n_fuera
    meta["n_listado_tradefi_exento"] = n_exento
    meta["nota_listado"] = (
        "Primera vela bóveda 1m. Fuera solo crypto con edad < 3 meses; TradeFi exento."
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK → {args.out} · fuera crypto<{args.meses}m={n_fuera} · "
        f"exento TradeFi={n_exento} · ok={n_ok}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
