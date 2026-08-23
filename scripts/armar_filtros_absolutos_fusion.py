#!/usr/bin/env python3
"""Arma filtros absolutos del ranking fusionado (solo ojos / bóveda).

Cortes duros (fuera de caza y nevera):
  - min_orden_usd > 6  →  max(minNotional, minQty × precio) en linear
  - extremo de bóveda   →  último close en franja ≤10% o ≥90% del rango
                            (min low … max high) del histórico en candles

Uso:
  python scripts/armar_filtros_absolutos_fusion.py
  python scripts/armar_filtros_absolutos_fusion.py --banda 0.10 --umbral-min 6
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
PARAM = ROOT / "data" / "bybit_parametros_mercado.json"
CK_NORMAL = (
    ROOT
    / "data"
    / "coliseo"
    / "rango_juicio"
    / "matriz"
    / "normal_reciente"
    / "checkpoint_parcial.json"
)
OUT = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_absolutos.json"


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def bases_juicio(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ranking = data.get("ranking") or []
    out: list[str] = []
    seen: set[str] = set()
    for row in ranking:
        a = str(row.get("activo") or "").upper().strip()
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    return out


def min_usd_linear(lin: dict[str, Any] | None, precio: float) -> tuple[float | None, str]:
    """Mínimo real USD: max(notional, minQty × precio)."""
    if not lin:
        return None, "sin_linear"
    mq = _f(lin.get("minOrderQty"))
    mn = _f(lin.get("minNotionalValue") or lin.get("minNotional") or lin.get("minOrderAmt"))
    px = precio if precio > 0 else _f(lin.get("precio_ref"))
    if px <= 0 and mq <= 0 and mn <= 0:
        return None, "sin_dato"
    por_qty = mq * px if (mq > 0 and px > 0) else 0.0
    if mn > 0 or por_qty > 0:
        return max(mn, por_qty), "max(notional, minQty*precio)"
    return None, "sin_dato"


def extremos_base(con: sqlite3.Connection, base: str) -> dict[str, Any]:
    row = con.execute(
        "SELECT MIN(low), MAX(high) FROM candles WHERE base = ?",
        (base,),
    ).fetchone()
    last = con.execute(
        "SELECT close, ts FROM candles WHERE base = ? ORDER BY ts DESC LIMIT 1",
        (base,),
    ).fetchone()
    lo = _f(row[0]) if row else 0.0
    hi = _f(row[1]) if row else 0.0
    close = _f(last[0]) if last else 0.0
    ts = int(last[1]) if last and last[1] is not None else None
    span = hi - lo
    pos = None
    if span > 0 and close > 0:
        pos = (close - lo) / span
    return {
        "min_low": lo or None,
        "max_high": hi or None,
        "last_close": close or None,
        "last_ts": ts,
        "pos_rango": round(pos, 6) if pos is not None else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Filtros absolutos fusion (min>$6 + extremos)")
    ap.add_argument("--banda", type=float, default=0.10, help="Franja extremo (0.10 = diez pct)")
    ap.add_argument("--umbral-min", type=float, default=6.0, help="USD minimo de orden")
    ap.add_argument("--boveda", type=Path, default=BOVEDA)
    ap.add_argument("--param", type=Path, default=PARAM)
    ap.add_argument("--checkpoint", type=Path, default=CK_NORMAL)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    banda = max(0.01, min(0.49, float(args.banda)))
    umbral = float(args.umbral_min)
    bases = bases_juicio(args.checkpoint)
    param = json.loads(args.param.read_text(encoding="utf-8"))
    activos_p = param.get("activos") or {}

    print(f"Bases juicio: {len(bases)}")
    print(f"Bóveda: {args.boveda}")
    t0 = time.time()
    con = sqlite3.connect(f"file:{args.boveda}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")

    activos_out: dict[str, Any] = {}
    n_min = n_ext = n_ambos = n_lev = 0
    for i, base in enumerate(bases, 1):
        ext = extremos_base(con, base)
        px = _f(ext.get("last_close"))
        lin = (activos_p.get(base) or {}).get("linear") if isinstance(activos_p.get(base), dict) else None
        min_u, como = min_usd_linear(lin if isinstance(lin, dict) else None, px)

        pos = ext.get("pos_rango")
        extremo = False
        motivo_ext = None
        if isinstance(pos, (int, float)):
            if pos <= banda:
                extremo = True
                motivo_ext = "cerca_piso_boveda"
            elif pos >= (1.0 - banda):
                extremo = True
                motivo_ext = "cerca_techo_boveda"

        min_out = bool(min_u is not None and min_u > umbral)
        lev_s = None
        if isinstance(lin, dict):
            lev_s = lin.get("maxLeverage")
        if not lev_s and isinstance(activos_p.get(base), dict):
            lev_s = activos_p[base].get("max_leverage_linear")
        lev = _f(lev_s) if lev_s else 0.0
        lev_fuera = bool(lev > 0 and lev < 10.0)
        fuera = bool(min_out or extremo or lev_fuera)
        if min_out and extremo:
            n_ambos += 1
        elif min_out:
            n_min += 1
        elif extremo:
            n_ext += 1
        if lev_fuera:
            n_lev += 1

        motivos: list[str] = []
        if min_out:
            motivos.append(f"min_orden_gt_{int(umbral) if umbral == int(umbral) else umbral}")
        if extremo and motivo_ext:
            motivos.append(motivo_ext)
        if lev_fuera:
            motivos.append("apalanc_lt_10")

        activos_out[base] = {
            "min_orden_usd": round(min_u, 4) if min_u is not None else None,
            "min_orden_como": como,
            "min_orden_fuera": min_out,
            "max_leverage": round(lev, 2) if lev > 0 else None,
            "leverage_fuera": lev_fuera,
            "pos_rango": ext.get("pos_rango"),
            "min_low": ext.get("min_low"),
            "max_high": ext.get("max_high"),
            "last_close": ext.get("last_close"),
            "last_ts": ext.get("last_ts"),
            "extremo_fuera": extremo,
            "fuera": fuera,
            "motivos": motivos,
        }
        if i % 50 == 0 or i == len(bases):
            elapsed = time.time() - t0
            print(f"  {i}/{len(bases)} · fuera min={n_min} ext={n_ext} ambos={n_ambos} · {elapsed:.0f}s")

    con.close()
    payload = {
        "meta": {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "fuente_min": str(args.param.relative_to(ROOT)).replace("\\", "/"),
            "fuente_extremo": str(args.boveda.relative_to(ROOT)).replace("\\", "/"),
            "umbral_min_orden_usd": umbral,
            "umbral_min_leverage": 10.0,
            "banda_extremo": banda,
            "n_activos": len(activos_out),
            "n_fuera_min": n_min + n_ambos,
            "n_fuera_extremo": n_ext + n_ambos,
            "n_fuera_leverage": n_lev,
            "n_fuera_ambos": n_ambos,
            "n_fuera_total": n_min + n_ext + n_ambos + n_lev,
            "nota": (
                "min_orden = max(minNotional, minQty×precio). "
                "extremo = last close en franja baja/alta del rango bóveda. "
                "apalanc = maxLeverage linear Bybit; fuera si < 10x. "
                "Solo estos + oficio/≤BTC eliminan del ranking fusionado."
            ),
        },
        "activos": activos_out,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK → {args.out}")
    print(
        f"Fuera: min>{umbral}={n_min + n_ambos} · extremo={n_ext + n_ambos} "
        f"· ambos={n_ambos} · total={n_min + n_ext + n_ambos}"
    )


if __name__ == "__main__":
    main()
