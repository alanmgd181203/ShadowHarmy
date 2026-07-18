#!/usr/bin/env python3
"""Coliseo — ranking Beru Fantasma v2 (100%: caza + negociador + ciclo).

Barrido vacío Adán: 0.6% … 2.0% (paso 0.2%).
Métrica: botín neto / dólar de manto.
Calor: día 20% · semana 50% · año 30%.

Uso:
  python scripts/coliseo_beru_fantasma.py
  python scripts/coliseo_beru_fantasma.py --vacios 0.012,0.016 --only BTC,ETH
  python scripts/coliseo_beru_fantasma.py --slip-bps 2 --path-policy min
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
    VACIOS_BARRIDO_DEFAULT,
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
        out[str(a).upper()] = float(
            row.get("margen_volumen_base_usd") or row.get("X") or 12.5
        )
    return out


def _flota(con, only: list[str] | None) -> list[str]:
    rows = con.execute("SELECT DISTINCT base FROM candles ORDER BY base").fetchall()
    bases = [str(r[0]).upper() for r in rows] if rows else [
        str(a).upper() for a in (getattr(config, "ACTIVOS_BERU_FLOTA", []) or [])
    ]
    if only:
        want = set(only)
        return [b for b in bases if b in want]
    return bases


def _window(candles, now_ts: int, days: int):
    since = now_ts - days * 86_400
    return [c for c in candles if c[0] >= since]


def rank_for_vacio(
    vacio: float,
    *,
    path_policy: str,
    fee_pct: float,
    slip_bps: float,
    only: list[str] | None,
    quick: bool,
) -> dict[str, Any]:
    con = bov.connect()
    margenes = _margen_map()
    flota = _flota(con, only)
    now_ts = int(time.time())
    por_activo: list[dict[str, Any]] = []

    for i, base in enumerate(flota, 1):
        t0 = time.time()
        candles = bov.load_candles(con, base)
        print(f"  [{i}/{len(flota)}] {base} velas={len(candles)}…", flush=True)
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
        # quick: solo 7d + 30d proxy si --quick; else full
        if quick:
            c_anio = _window(candles, now_ts, 30)
            c_sem = _window(candles, now_ts, 7)
            c_dia = _window(candles, now_ts, 1)
        else:
            c_anio = candles
            c_sem = _window(candles, now_ts, 7)
            c_dia = _window(candles, now_ts, 1)

        kw = dict(
            activo=base,
            vacio=vacio,
            margen_usd=margen,
            fee_pct=fee_pct,
            slip_bps=slip_bps,
            path_policy=path_policy,  # type: ignore[arg-type]
        )
        r_anio = simular_desde_velas(c_anio, **kw)
        r_sem = simular_desde_velas(c_sem, **kw)
        r_dia = simular_desde_velas(c_dia, **kw)
        calor = calor_eficiencia(r_dia.eficiencia, r_sem.eficiencia, r_anio.eficiencia)
        por_activo.append(
            {
                "activo": base,
                "datos": "OK",
                "margen_usd": margen,
                "vacio_pct": vacio * 100,
                "secs": round(time.time() - t0, 1),
                "dia": {
                    "cosechas": r_dia.cosechas,
                    "toques_neg": r_dia.toques_neg,
                    "botin_neto": r_dia.botin_neto,
                    "eficiencia": r_dia.eficiencia,
                },
                "semana": {
                    "cosechas": r_sem.cosechas,
                    "toques_neg": r_sem.toques_neg,
                    "botin_neto": r_sem.botin_neto,
                    "eficiencia": r_sem.eficiencia,
                },
                "anio": {
                    "cosechas": r_anio.cosechas,
                    "toques_neg": r_anio.toques_neg,
                    "ciclos_infinito": r_anio.ciclos_infinito,
                    "botin_neto": r_anio.botin_neto,
                    "fees": r_anio.fees,
                    "eficiencia": r_anio.eficiencia,
                },
                "calor": calor,
                "path_policy": r_anio.path_policy,
            }
        )
        print(
            f"      calor={calor:.3f} efi7d={r_sem.eficiencia:.2f} "
            f"efi1a={r_anio.eficiencia:.2f} ({por_activo[-1]['secs']}s)",
            flush=True,
        )
    con.close()

    valid = [x for x in por_activo if x.get("datos") == "OK"]
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
            "version": "beru_fantasma_v2",
            "vacio": vacio,
            "vacio_pct": vacio * 100,
            "path_policy": path_policy,
            "fee_pct": fee_pct,
            "slip_bps": slip_bps,
            "abismo": "acoplado_a_vacio",
            "metrica": "botin_neto / margen_usd",
            "pesos_calor": {"dia": 0.20, "semana": 0.50, "anio": 0.30},
            "quick": quick,
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
        f"# Ranking Beru Fantasma v2 — vacío {meta['vacio_pct']:.1f}%",
        f"",
        f"- UTC: `{meta['ts_utc']}`",
        f"- Métrica: **botín neto / dólar de manto**",
        f"- Path: `{meta['path_policy']}` · fee `{meta['fee_pct']*100:.2f}%/pierna` · slip `{meta['slip_bps']} bps`",
        f"- Calor: día 20% · **semana 50%** · año 30%",
        f"",
        f"| # | Activo | Calor | Semáforo | Efi 7d | Efi 1a | Efi 1d | Margen |",
        f"|---|--------|------:|----------|-------:|-------:|-------:|-------:|",
    ]
    for row in report["ranking"]:
        if row.get("datos") != "OK":
            lines.append(
                f"| — | {row['activo']} | — | GRIS | — | — | — | {row.get('margen_usd')} |"
            )
            continue
        lines.append(
            f"| {row.get('rank_calor')} | {row['activo']} | {row['calor']:.3f} | "
            f"{row.get('semaforo_calor')} | {row['semana']['eficiencia']:.3f} | "
            f"{row['anio']['eficiencia']:.3f} | {row['dia']['eficiencia']:.3f} | "
            f"{row['margen_usd']:.1f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Coliseo Beru Fantasma v2")
    ap.add_argument(
        "--vacios",
        type=str,
        default=",".join(str(v) for v in VACIOS_BARRIDO_DEFAULT),
        help="Lista de vacíos Adán (fracción). Default 0.6%%…2.0%% paso 0.2%%",
    )
    ap.add_argument("--path-policy", choices=["min", "ohlc", "olhc"], default="min")
    ap.add_argument(
        "--fee-pct",
        type=float,
        default=float(getattr(config, "BERU_RAIL_FEE_USDT_PCT", 0.10)) / 100.0,
    )
    ap.add_argument("--slip-bps", type=float, default=2.0, help="Slippage conservador (default 2 bps)")
    ap.add_argument("--only", type=str, default="", help="Activos CSV (prueba rápida)")
    ap.add_argument("--quick", action="store_true", help="Solo 30d como 'año' (smoke)")
    ap.add_argument("--out-dir", type=str, default="", help="Carpeta salida (default data/coliseo)")
    args = ap.parse_args()

    if not bov.BOVEDA_PATH.exists():
        print(f"Sin bóveda: {bov.BOVEDA_PATH}")
        print("Copia el pack de Jess a data/coliseo/")
        return 2

    vacios = [float(x.strip()) for x in args.vacios.split(",") if x.strip()]
    only = [x.strip().upper() for x in args.only.split(",") if x.strip()] or None
    out_dir = Path(args.out_dir) if args.out_dir else bov.COLISEO_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("COLISEO — Beru Fantasma v2 (100%)")
    print(f"Vacíos: {[round(v*100,1) for v in vacios]} %")
    print(f"Fee {args.fee_pct*100:.2f}%/pierna · slip {args.slip_bps} bps · path {args.path_policy}")
    print("=" * 60)

    summary = []
    mejores_por_activo: dict[str, dict[str, Any]] = {}

    for v in vacios:
        label = f"v{str(round(v*100,1)).replace('.', 'p')}"
        print(f"\n>>> Vacío {v*100:.1f}%")
        report = rank_for_vacio(
            v,
            path_policy=args.path_policy,
            fee_pct=args.fee_pct,
            slip_bps=args.slip_bps,
            only=only,
            quick=args.quick,
        )
        out_json = out_dir / f"ranking_{label}.json"
        out_md = out_dir / f"ranking_{label}.md"
        out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_md(report, out_md)
        top = next((r for r in report["ranking"] if r.get("datos") == "OK"), None)
        summary.append(
            {
                "vacio_pct": v * 100,
                "top": top["activo"] if top else "—",
                "calor_top": top["calor"] if top else 0,
                "mediana_calor": _median(
                    [float(r["calor"]) for r in report["ranking"] if r.get("datos") == "OK"]
                ),
            }
        )
        for row in report["ranking"]:
            if row.get("datos") != "OK":
                continue
            a = row["activo"]
            prev = mejores_por_activo.get(a)
            if prev is None or float(row["calor"]) > float(prev["calor"]):
                mejores_por_activo[a] = {
                    "activo": a,
                    "vacio_pct_optimo": v * 100,
                    "calor": row["calor"],
                    "efi_semana": row["semana"]["eficiencia"],
                    "margen_usd": row["margen_usd"],
                }
        print(f"    -> {out_md.name} · top {summary[-1]['top']}")

    comp = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "barrido": summary,
        "vacio_dorado_flota": max(summary, key=lambda x: x["mediana_calor"]) if summary else None,
        "vacio_optimo_por_activo": sorted(
            mejores_por_activo.values(),
            key=lambda x: float(x["calor"]),
            reverse=True,
        ),
        "notas": {
            "fee": "0.1%/pierna (0.2% round-trip)",
            "slip_bps": args.slip_bps,
            "calor": "20/50/30",
            "abismo": "acoplado al vacío Adán",
            "fusiones": "no simuladas (1 Beru por activo)",
        },
    }
    (out_dir / "comparativa_vacios.json").write_text(
        json.dumps(comp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_comparativa_md(comp, out_dir / "comparativa_vacios.md")
    print("\nComparativa:", out_dir / "comparativa_vacios.md")
    return 0


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    m = len(s) // 2
    if len(s) % 2:
        return s[m]
    return (s[m - 1] + s[m]) / 2.0


def _write_comparativa_md(comp: dict[str, Any], path: Path) -> None:
    lines = [
        "# Comparativa vacíos Adán — Coliseo",
        "",
        f"- UTC: `{comp['ts_utc']}`",
        "",
        "## Por vacío (mediana de calor de la flota)",
        "",
        "| Vacío % | Top activo | Calor top | Mediana calor |",
        "|--------:|------------|----------:|--------------:|",
    ]
    for row in comp.get("barrido") or []:
        lines.append(
            f"| {row['vacio_pct']:.1f} | {row['top']} | {row['calor_top']:.3f} | {row['mediana_calor']:.3f} |"
        )
    dorado = comp.get("vacio_dorado_flota") or {}
    lines += [
        "",
        f"**Vacío dorado (flota):** {dorado.get('vacio_pct', '—')}% "
        f"(mediana calor {dorado.get('mediana_calor', '—')})",
        "",
        "## Vacío óptimo por activo (mejor calor en el barrido)",
        "",
        "| Activo | Vacío óptimo % | Calor | Efi 7d | Margen |",
        "|--------|---------------:|------:|-------:|-------:|",
    ]
    for row in comp.get("vacio_optimo_por_activo") or []:
        lines.append(
            f"| {row['activo']} | {row['vacio_pct_optimo']:.1f} | {row['calor']:.3f} | "
            f"{row['efi_semana']:.3f} | {row['margen_usd']:.1f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
