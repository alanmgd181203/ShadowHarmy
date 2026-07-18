#!/usr/bin/env python3
"""Coliseo — Fase 1: vacío Adán + activos eficientes (cascada de horizontes).

Fase 1 (ahora): barrido vacío 0.8%…2.0%, Mariscal, 1 Beru/activo.
  Cascada: --dias 1 → 7 → 30 → 365. Tras 1d/7d: --top N para no quemar año en perdedores.

Fase 2 (después): malla oz/red ×2, sub-Berus/tiers, legión/Mega — NO mezclar aún.

Uso:
  python scripts/coliseo_beru_fantasma.py --dias 1
  python scripts/coliseo_beru_fantasma.py --dias 7 --top 8
  python scripts/coliseo_beru_fantasma.py --dias 365 --only BTC,ETH,SOL,...
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


def _fmt_secs(s: float) -> str:
    s = max(0, int(s))
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{sec:02d}s"
    return f"{sec}s"


class _BarraProgreso:
    """Barra ASCII + % + ETA (sin dependencias extra)."""

    def __init__(self, total: int, ancho: int = 28):
        self.total = max(1, total)
        self.hecho = 0
        self.ancho = ancho
        self.t0 = time.time()

    def tick(self, etiqueta: str = "") -> None:
        self.hecho += 1
        frac = min(1.0, self.hecho / self.total)
        filled = int(self.ancho * frac)
        bar = "#" * filled + "-" * (self.ancho - filled)
        elapsed = time.time() - self.t0
        rate = self.hecho / elapsed if elapsed > 0 else 0.0
        eta = (self.total - self.hecho) / rate if rate > 0 else 0.0
        pct = frac * 100.0
        msg = (
            f"\r  [{bar}] {pct:5.1f}%  {self.hecho}/{self.total}"
            f"  eta {_fmt_secs(eta)}  ok {_fmt_secs(elapsed)}"
        )
        if etiqueta:
            msg += f"  | {etiqueta[:40]}"
        # pad to clear previous longer line
        sys.stdout.write(msg.ljust(100))
        sys.stdout.flush()
        if self.hecho >= self.total:
            sys.stdout.write("\n")
            sys.stdout.flush()


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


def _ventanas(candles, now_ts: int, horizonte_dias: int) -> tuple[list, list, list]:
    """Recorta la estela al horizonte y arma dia/semana/anio dentro de ese techo."""
    base = _window(candles, now_ts, horizonte_dias) if horizonte_dias < 400 else candles
    d1 = min(1, horizonte_dias)
    d7 = min(7, horizonte_dias)
    # "anio" = todo lo disponible bajo el horizonte
    return _window(base, now_ts, d1), _window(base, now_ts, d7), base


def rank_for_vacio(
    vacio: float,
    *,
    path_policy: str,
    fee_pct: float,
    slip_bps: float,
    only: list[str] | None,
    horizonte_dias: int,
    barra: _BarraProgreso | None = None,
) -> dict[str, Any]:
    con = bov.connect()
    margenes = _margen_map()
    flota = _flota(con, only)
    now_ts = int(time.time())
    por_activo: list[dict[str, Any]] = []

    for base in flota:
        t0 = time.time()
        candles = bov.load_candles(con, base)
        if len(candles) < 50:
            por_activo.append(
                {
                    "activo": base,
                    "datos": "INSUFICIENTES",
                    "margen_usd": margenes.get(base, 12.5),
                }
            )
            if barra:
                barra.tick(f"v{vacio*100:.1f}% {base} (sin datos)")
            continue
        margen = margenes.get(base, 12.5)
        c_dia, c_sem, c_anio = _ventanas(candles, now_ts, horizonte_dias)
        if len(c_anio) < 30:
            por_activo.append(
                {
                    "activo": base,
                    "datos": "INSUFICIENTES",
                    "margen_usd": margen,
                }
            )
            if barra:
                barra.tick(f"v{vacio*100:.1f}% {base} (corto)")
            continue

        kw = dict(
            activo=base,
            vacio=vacio,
            margen_usd=margen,
            fee_pct=fee_pct,
            slip_bps=slip_bps,
            path_policy=path_policy,  # type: ignore[arg-type]
        )
        r_anio = simular_desde_velas(c_anio, **kw)
        r_sem = simular_desde_velas(c_sem, **kw) if c_sem else r_anio
        r_dia = simular_desde_velas(c_dia, **kw) if c_dia else r_sem
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
        if barra:
            barra.tick(
                f"v{vacio*100:.1f}% {base} calor={calor:.2f} ({por_activo[-1]['secs']}s)"
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
            "version": "beru_fantasma_v2_fase1",
            "fase": 1,
            "horizonte_dias": horizonte_dias,
            "vacio": vacio,
            "vacio_pct": vacio * 100,
            "path_policy": path_policy,
            "fee_pct": fee_pct,
            "slip_bps": slip_bps,
            "abismo": "acoplado_a_vacio",
            "metrica": "botin_neto / margen_usd",
            "pesos_calor": {"dia": 0.20, "semana": 0.50, "anio": 0.30},
            "n": len(por_activo),
            "fase2_aplazada": [
                "malla_oz_red_x2",
                "sub_berus_tiers",
                "legion_fusiones_mega",
            ],
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
        f"# Ranking Beru Fantasma — vacío {meta['vacio_pct']:.1f}% · horizonte {meta['horizonte_dias']}d",
        f"",
        f"- UTC: `{meta['ts_utc']}` · **Fase 1** (vacío + activos)",
        f"- Métrica: **botín neto / dólar de manto**",
        f"- Path: `{meta['path_policy']}` · fee `{meta['fee_pct']*100:.2f}%/pierna` · slip `{meta['slip_bps']} bps`",
        f"- Calor: día 20% · **semana 50%** · año 30%",
        f"",
        f"| # | Activo | Calor | Semáforo | Efi 7d | Efi H | Efi 1d | Margen |",
        f"|---|--------|------:|----------|-------:|------:|-------:|-------:|",
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
    ap = argparse.ArgumentParser(description="Coliseo Fase 1 — vacío Adán + ranking activos")
    ap.add_argument(
        "--vacios",
        type=str,
        default=",".join(str(v) for v in VACIOS_BARRIDO_DEFAULT),
        help="Vacíos Adán (fracción). Default 0.8%%…2.0%% paso 0.2%%",
    )
    ap.add_argument(
        "--dias",
        type=int,
        default=1,
        help="Horizonte de estela: 1 → 7 → 30 → 365 (cascada). Default 1 (smoke rápido)",
    )
    ap.add_argument(
        "--top",
        type=int,
        default=0,
        help="Tras el barrido, escribe top N activos (promedio calor) para el siguiente --only",
    )
    ap.add_argument("--path-policy", choices=["min", "ohlc", "olhc"], default="min")
    ap.add_argument(
        "--fee-pct",
        type=float,
        default=float(getattr(config, "BERU_RAIL_FEE_USDT_PCT", 0.10)) / 100.0,
    )
    ap.add_argument("--slip-bps", type=float, default=2.0)
    ap.add_argument("--only", type=str, default="", help="Activos CSV (poda tras --top)")
    ap.add_argument("--quick", action="store_true", help="Alias de --dias 30")
    ap.add_argument("--out-dir", type=str, default="")
    args = ap.parse_args()

    if not bov.BOVEDA_PATH.exists():
        print(f"Sin bóveda: {bov.BOVEDA_PATH}")
        return 2

    horizonte = 30 if args.quick else max(1, int(args.dias))
    vacios = [float(x.strip()) for x in args.vacios.split(",") if x.strip()]
    only = [x.strip().upper() for x in args.only.split(",") if x.strip()] or None
    out_dir = Path(args.out_dir) if args.out_dir else bov.COLISEO_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("COLISEO FASE 1 — vacio Adan + activos (sin malla x2 / sin sub-Berus)")
    print(f"Horizonte: {horizonte}d | Vacios %: {[round(v*100,1) for v in vacios]}")
    print(f"Fee {args.fee_pct*100:.2f}%/pierna | slip {args.slip_bps} bps | path {args.path_policy}")
    # Contar trabajos totales (vacios x activos) para la barra
    con0 = bov.connect()
    n_activos = len(_flota(con0, only))
    con0.close()
    total_jobs = max(1, len(vacios) * n_activos)
    print(f"Trabajos: {len(vacios)} vacios x {n_activos} activos = {total_jobs}")
    print("=" * 60)

    barra = _BarraProgreso(total_jobs)
    summary = []
    calor_por_activo: dict[str, list[float]] = {}

    for v in vacios:
        label = f"h{horizonte}d_v{str(round(v*100,1)).replace('.', 'p')}"
        print(f"\n>>> Vacio {v*100:.1f}% · {horizonte}d")
        report = rank_for_vacio(
            v,
            path_policy=args.path_policy,
            fee_pct=args.fee_pct,
            slip_bps=args.slip_bps,
            only=only,
            horizonte_dias=horizonte,
            barra=barra,
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
            calor_por_activo.setdefault(row["activo"], []).append(float(row["calor"]))
        print(f"    -> {out_md.name} · top {summary[-1]['top']}")

    # Vacío dorado + ranking de activos (promedio de calor en el barrido)
    activos_rank = sorted(
        (
            {
                "activo": a,
                "calor_medio": sum(vals) / len(vals),
                "n_vacios": len(vals),
            }
            for a, vals in calor_por_activo.items()
        ),
        key=lambda x: x["calor_medio"],
        reverse=True,
    )
    dorado = max(summary, key=lambda x: x["mediana_calor"]) if summary else None
    top_n = activos_rank[: args.top] if args.top > 0 else activos_rank[:8]
    only_sugerido = ",".join(x["activo"] for x in top_n)

    comp = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "fase": 1,
        "horizonte_dias": horizonte,
        "barrido_vacios": summary,
        "vacio_dorado_flota": dorado,
        "activos_por_calor_medio": activos_rank,
        "top_sugerido_siguiente": {
            "n": len(top_n),
            "activos": [x["activo"] for x in top_n],
            "only_cli": only_sugerido,
            "comando_siguiente": (
                f"python scripts/coliseo_beru_fantasma.py --dias { _siguiente_horizonte(horizonte) }"
                f" --only {only_sugerido}"
                if only_sugerido
                else None
            ),
        },
        "fase2_aplazada": [
            "ensanchamiento oz/red 0.2%/0.1%",
            "sub-Berus Soldado..Mariscal",
            "legion / fusiones / Mega",
        ],
        "notas": {
            "fee": "0.1%/pierna",
            "slip_bps": args.slip_bps,
            "calor": "20/50/30",
            "vacios": "0.8%…2.0% (sin 0.6%)",
            "cascada": "1d → 7d → 30d → 365d; poda con --top / --only",
        },
    }
    (out_dir / "comparativa_vacios.json").write_text(
        json.dumps(comp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    _write_comparativa_md(comp, out_dir / "comparativa_vacios.md")
    (out_dir / "top_activos_siguiente.txt").write_text(only_sugerido + "\n", encoding="utf-8")
    print("\nComparativa:", out_dir / "comparativa_vacios.md")
    if only_sugerido:
        print("Top para siguiente horizonte:", only_sugerido)
        print(
            "Comando:",
            comp["top_sugerido_siguiente"]["comando_siguiente"],
        )
    return 0


def _siguiente_horizonte(d: int) -> int:
    if d <= 1:
        return 7
    if d <= 7:
        return 30
    if d <= 30:
        return 365
    return 365


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
        f"# Comparativa Fase 1 — horizonte {comp['horizonte_dias']}d",
        "",
        f"- UTC: `{comp['ts_utc']}`",
        "",
        "## Vacíos (mediana de calor de la flota)",
        "",
        "| Vacío % | Top activo | Calor top | Mediana calor |",
        "|--------:|------------|----------:|--------------:|",
    ]
    for row in comp.get("barrido_vacios") or []:
        lines.append(
            f"| {row['vacio_pct']:.1f} | {row['top']} | {row['calor_top']:.3f} | {row['mediana_calor']:.3f} |"
        )
    dorado = comp.get("vacio_dorado_flota") or {}
    lines += [
        "",
        f"**Vacío dorado (esta pasada):** {dorado.get('vacio_pct', '—')}% "
        f"(mediana calor {dorado.get('mediana_calor', '—')})",
        "",
        "## Activos por calor medio (en todos los vacíos de esta pasada)",
        "",
        "| # | Activo | Calor medio |",
        "|---|--------|------------:|",
    ]
    for i, row in enumerate(comp.get("activos_por_calor_medio") or [], 1):
        lines.append(f"| {i} | {row['activo']} | {row['calor_medio']:.3f} |")
    top = comp.get("top_sugerido_siguiente") or {}
    lines += [
        "",
        "## Siguiente paso (cascada)",
        "",
        f"No gastes el año en toda la flota. Usa el top:",
        f"",
        f"```",
        f"{top.get('comando_siguiente') or '—'}",
        f"```",
        "",
        "## Fase 2 (aplazada — no correr aún)",
        "",
    ]
    for x in comp.get("fase2_aplazada") or []:
        lines.append(f"- {x}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
