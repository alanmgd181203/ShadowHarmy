#!/usr/bin/env python3
"""Coliseo — ranking Beru Fantasma sobre la bóveda 1m (sin Bybit).

Métrica corona: botín neto / dólar de manto.
Horizontes: 1d · 7d · 365d → semáforos + calor (semana manda).

Uso:
  python scripts/coliseo_beru_fantasma.py
  python scripts/coliseo_beru_fantasma.py --vacios 0.010,0.012,0.016,0.020
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import coliseo_boveda as bov
from core.coliseo_beru_fantasma import (
    calor_eficiencia,
    semaforo,
    simular_desde_velas,
)


def _margen_map() -> dict[str, float]:
    path = ROOT / "config" / "diccionario_beru_flota_manto.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, float] = {}
    for a, row in (data.get("activos") or {}).items():
        out[str(a).upper()] = float(row.get("margen_volumen_base_usd") or row.get("X") or 12.5)
    return out


def _flota(con) -> list[str]:
    rows = con.execute("SELECT DISTINCT base FROM candles ORDER BY base").fetchall()
    if rows:
        return [str(r[0]).upper() for r in rows]
    return [str(a).upper() for a in (getattr(config, "ACTIVOS_BERU_FLOTA", []) or [])]


def _window_candles(candles, now_ts: int, days: int):
    since = now_ts - days * 86_400
    return [c for c in candles if c[0] >= since]


def rank_for_vacio(
    vacio: float,
    *,
    path_policy: str,
    fee_pct: float,
) -> dict[str, Any]:
    con = bov.connect()
    margenes = _margen_map()
    flota = _flota(con)
    now_ts = int(time.time())
    por_activo: list[dict[str, Any]] = []

    for base in flota:
        candles = bov.load_candles(con, base)
        if len(candles) < 100:
            por_activo.append(
                {
                    "activo": base,
                    "datos": "INSUFICIENTES",
                    "margen_usd": margenes.get(base, 12.5),
                }
            )
            continue
        margen = margenes.get(base, 12.5)
        kwargs = dict(
            activo=base,
            vacio=vacio,
            margen_usd=margen,
            fee_pct=fee_pct,
            path_policy=path_policy,  # type: ignore[arg-type]
        )
        # year / week / day on same stream lengths
        r_anio = simular_desde_velas(candles, **kwargs)
        r_sem = simular_desde_velas(_window_candles(candles, now_ts, 7), **kwargs)
        r_dia = simular_desde_velas(_window_candles(candles, now_ts, 1), **kwargs)
        calor = calor_eficiencia(r_dia.eficiencia, r_sem.eficiencia, r_anio.eficiencia)
        por_activo.append(
            {
                "activo": base,
                "datos": "OK",
                "margen_usd": margen,
                "vacio_pct": vacio * 100,
                "dia": {
                    "cosechas": r_dia.cosechas,
                    "botin_neto": r_dia.botin_neto,
                    "eficiencia": r_dia.eficiencia,
                },
                "semana": {
                    "cosechas": r_sem.cosechas,
                    "botin_neto": r_sem.botin_neto,
                    "eficiencia": r_sem.eficiencia,
                },
                "anio": {
                    "cosechas": r_anio.cosechas,
                    "botin_neto": r_anio.botin_neto,
                    "eficiencia": r_anio.eficiencia,
                    "fees": r_anio.fees,
                },
                "calor": calor,
                "path_policy": r_anio.path_policy,
            }
        )
    con.close()

    valid = [x for x in por_activo if x.get("datos") == "OK"]
    # ranks por horizonte
    for key in ("dia", "semana", "anio"):
        ordered = sorted(valid, key=lambda x: float(x[key]["eficiencia"]), reverse=True)
        for i, row in enumerate(ordered, start=1):
            row[f"rank_{key}"] = i
            row[f"semaforo_{key}"] = semaforo(i, len(ordered))
    ordered_calor = sorted(valid, key=lambda x: float(x["calor"]), reverse=True)
    for i, row in enumerate(ordered_calor, start=1):
        row["rank_calor"] = i
        row["semaforo_calor"] = semaforo(i, len(ordered_calor))

    return {
        "meta": {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "vacio": vacio,
            "vacio_pct": vacio * 100,
            "path_policy": path_policy,
            "fee_pct": fee_pct,
            "metrica": "botin_neto / margen_usd",
            "pesos_calor": {"dia": 0.20, "semana": 0.50, "anio": 0.30},
            "n": len(por_activo),
        },
        "ranking": sorted(
            por_activo,
            key=lambda x: float(x.get("calor") or -1e9),
            reverse=True,
        ),
    }


def write_md(report: dict[str, Any], path: Path) -> None:
    meta = report["meta"]
    lines = [
        f"# Ranking Beru Fantasma — vacío {meta['vacio_pct']:.1f}%",
        f"",
        f"- UTC: `{meta['ts_utc']}`",
        f"- Métrica: **botín neto / dólar de manto**",
        f"- Path: `{meta['path_policy']}` · fee pierna `{meta['fee_pct']*100:.2f}%`",
        f"",
        f"| # | Activo | Calor | Semáforo | Efi 7d | Efi 1a | Efi 1d | Margen |",
        f"|---|--------|------:|----------|-------:|-------:|-------:|-------:|",
    ]
    for row in report["ranking"]:
        if row.get("datos") != "OK":
            lines.append(f"| — | {row['activo']} | — | GRIS | — | — | — | {row.get('margen_usd')} |")
            continue
        lines.append(
            f"| {row.get('rank_calor')} | {row['activo']} | {row['calor']:.3f} | "
            f"{row.get('semaforo_calor')} | {row['semana']['eficiencia']:.3f} | "
            f"{row['anio']['eficiencia']:.3f} | {row['dia']['eficiencia']:.3f} | "
            f"{row['margen_usd']:.1f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vacios", type=str, default="0.016")
    ap.add_argument("--path-policy", choices=["min", "ohlc", "olhc"], default="min")
    ap.add_argument("--fee-pct", type=float, default=float(getattr(config, "BERU_RAIL_FEE_USDT_PCT", 0.10)) / 100.0)
    ap.add_argument("--out", type=str, default="")
    args = ap.parse_args()

    if not bov.BOVEDA_PATH.exists():
        print(f"Sin bóveda: {bov.BOVEDA_PATH}")
        print("Corre primero: python scripts/jess_boveda_coliseo_noche.py")
        return 2

    vacios = [float(x.strip()) for x in args.vacios.split(",") if x.strip()]
    bov.ensure_dirs()
    summary = []
    for v in vacios:
        label = f"v{str(v).replace('.', 'p')}"
        report = rank_for_vacio(v, path_policy=args.path_policy, fee_pct=args.fee_pct)
        out_json = Path(args.out) if args.out and len(vacios) == 1 else bov.COLISEO_DIR / f"ranking_{label}.json"
        out_md = out_json.with_suffix(".md")
        out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_md(report, out_md)
        top = next((r for r in report["ranking"] if r.get("datos") == "OK"), None)
        summary.append((v, top["activo"] if top else "—", top["calor"] if top else 0))
        print(f"vacío {v*100:.1f}% → {out_json.name} · top {summary[-1][1]} calor={summary[-1][2]}")

    # Comparativa número dorado
    if len(vacios) > 1:
        comp = {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "candidatos": [
                {"vacio": v, "top": a, "calor_top": c} for v, a, c in summary
            ],
            "nota": "Comparar mediana de calor flota entre vacíos en ranking_*.json",
        }
        (bov.COLISEO_DIR / "comparativa_vacios.json").write_text(
            json.dumps(comp, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
