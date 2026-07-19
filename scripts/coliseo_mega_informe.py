#!/usr/bin/env python3
"""Informe mega Coliseo — pase de batalla, comparaciones, gráficas de eficiencia."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.coliseo_beru_fantasma import semaforo
from core.coliseo_beru_legion import TIERS_ORDEN

MEGA = ROOT / "data" / "coliseo" / "mega"
CKPT = MEGA / "checkpoint.json"
OUT_MD = MEGA / "INFORME_PASE_BATALLA.md"
OUT_JSON = MEGA / "pase_batalla.json"
CHARTS = MEGA / "charts"


def _load_jobs() -> list[dict[str, Any]]:
    if not CKPT.exists():
        return []
    ckpt = json.loads(CKPT.read_text(encoding="utf-8"))
    return list((ckpt.get("jobs_done") or {}).values())


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    m = n // 2
    return s[m] if n % 2 else 0.5 * (s[m - 1] + s[m])


def _charts(jobs: list[dict[str, Any]]) -> list[str]:
    """Genera PNGs; si falta matplotlib, salta."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        return [f"(sin matplotlib: {e})"]

    CHARTS.mkdir(parents=True, exist_ok=True)
    made: list[str] = []

    # 1) calor por activo — barrido PLENO malla x1, mejor vacío
    barrido = [j for j in jobs if j.get("fase") == "barrido" and float(j.get("malla_scale", 1)) == 1.0]
    if barrido:
        by_a: dict[str, list[float]] = defaultdict(list)
        for j in barrido:
            by_a[j["activo"]].append(float(j["calor_pase"]))
        ranking = sorted(((a, _median(v)) for a, v in by_a.items()), key=lambda x: -x[1])
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar([x[0] for x in ranking], [x[1] for x in ranking], color="#4a7c59")
        ax.set_title("Calor pase (mediana vacíos) — malla ×1 · Mariscal+legión")
        ax.set_ylabel("calor (3d/mes/año)")
        ax.tick_params(axis="x", rotation=60)
        fig.tight_layout()
        p = CHARTS / "calor_malla_x1.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        made.append(str(p.relative_to(ROOT)))

    # 2) vacío dorado: mediana flota por vacío × malla
    fig, ax = plt.subplots(figsize=(10, 5))
    for malla, color in ((1.0, "#2c5f2d"), (2.0, "#97bc62")):
        sub = [j for j in jobs if j.get("fase") == "barrido" and abs(float(j.get("malla_scale", 1)) - malla) < 0.01]
        by_v: dict[float, list[float]] = defaultdict(list)
        for j in sub:
            by_v[round(float(j["vacio_pct"]), 1)].append(float(j["calor_pase"]))
        xs = sorted(by_v.keys())
        ys = [_median(by_v[x]) for x in xs]
        ax.plot(xs, ys, marker="o", label=f"malla ×{malla:g}", color=color)
    ax.set_xlabel("Vacío Adán %")
    ax.set_ylabel("Mediana calor flota")
    ax.set_title("Barrido de vacíos — legión")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = CHARTS / "vacios_vs_calor.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    made.append(str(p.relative_to(ROOT)))

    # 3) ranking de rangos (tiers) en vacío dorado x1
    ckpt = json.loads(CKPT.read_text(encoding="utf-8")) if CKPT.exists() else {}
    dorados = (ckpt.get("vacios_dorados") or {}).get("x1") or []
    if dorados:
        v0 = float(dorados[0]) * 100
        tier_jobs = [
            j
            for j in jobs
            if j.get("fase") == "tier"
            and abs(float(j.get("malla_scale", 1)) - 1.0) < 0.01
            and abs(float(j["vacio_pct"]) - v0) < 0.15
        ]
        # heatmap-like: activo × tier calor
        activos = sorted({j["activo"] for j in tier_jobs})
        tiers = list(TIERS_ORDEN)
        import numpy as np

        mat = np.zeros((len(activos), len(tiers)))
        for i, a in enumerate(activos):
            for k, t in enumerate(tiers):
                hits = [j["calor_pase"] for j in tier_jobs if j["activo"] == a and j["tier_id"] == t]
                mat[i, k] = float(hits[0]) if hits else 0.0
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(mat, aspect="auto", cmap="YlGn")
        ax.set_xticks(range(len(tiers)))
        ax.set_xticklabels([t for t in tiers])
        ax.set_yticks(range(len(activos)))
        ax.set_yticklabels(activos)
        ax.set_title(f"Pase de batalla — calor por rango · vacío ~{v0:.1f}% · malla ×1")
        fig.colorbar(im, ax=ax, fraction=0.03)
        fig.tight_layout()
        p = CHARTS / "heatmap_rangos_x1.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        made.append(str(p.relative_to(ROOT)))

    # 4) efi mensual flota (promedio)
    mes_map: dict[str, list[float]] = defaultdict(list)
    for j in barrido:
        for m in j.get("meses") or []:
            mes_map[m["mes"]].append(float(m["eficiencia"]))
    if mes_map:
        xs = sorted(mes_map.keys())
        ys = [sum(mes_map[x]) / len(mes_map[x]) for x in xs]
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(xs, ys, marker="o", color="#1b4f72")
        ax.set_title("Eficiencia media flota por mes (barrido malla ×1)")
        ax.tick_params(axis="x", rotation=60)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        p = CHARTS / "efi_mensual_flota.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        made.append(str(p.relative_to(ROOT)))

    # 5) malla x1 vs x2 por activo (calor medio)
    fig, ax = plt.subplots(figsize=(11, 5))
    act = sorted({j["activo"] for j in jobs if j.get("fase") == "barrido"})
    c1, c2 = [], []
    for a in act:
        v1 = [j["calor_pase"] for j in jobs if j.get("fase") == "barrido" and j["activo"] == a and abs(float(j.get("malla_scale", 1)) - 1) < 0.01]
        v2 = [j["calor_pase"] for j in jobs if j.get("fase") == "barrido" and j["activo"] == a and abs(float(j.get("malla_scale", 1)) - 2) < 0.01]
        c1.append(_median(v1) if v1 else 0)
        c2.append(_median(v2) if v2 else 0)
    import numpy as np

    x = np.arange(len(act))
    w = 0.4
    ax.bar(x - w / 2, c1, w, label="malla ×1", color="#2c5f2d")
    ax.bar(x + w / 2, c2, w, label="malla ×2", color="#97bc62")
    ax.set_xticks(x)
    ax.set_xticklabels(act, rotation=60)
    ax.legend()
    ax.set_title("Malla ×1 vs ×2 — calor mediano por activo")
    fig.tight_layout()
    p = CHARTS / "malla_x1_vs_x2.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    made.append(str(p.relative_to(ROOT)))

    return made


def build_informe(jobs: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    ckpt = json.loads(CKPT.read_text(encoding="utf-8")) if CKPT.exists() else {}
    charts = _charts(jobs)

    # Pase de batalla: mejor calor por activo×rango en vacío dorado x1
    dorados_x1 = (ckpt.get("vacios_dorados") or {}).get("x1") or []
    v0 = float(dorados_x1[0]) * 100 if dorados_x1 else 1.4
    tier_jobs = [
        j
        for j in jobs
        if j.get("fase") == "tier"
        and abs(float(j.get("malla_scale", 1)) - 1.0) < 0.01
        and abs(float(j["vacio_pct"]) - v0) < 0.2
    ]
    # ranking rangos: para cada activo, mejor tier
    best_by_asset: dict[str, dict[str, Any]] = {}
    for j in tier_jobs:
        a = j["activo"]
        if a not in best_by_asset or float(j["calor_pase"]) > float(best_by_asset[a]["calor_pase"]):
            best_by_asset[a] = j
    pase = sorted(best_by_asset.values(), key=lambda x: -float(x["calor_pase"]))
    for i, row in enumerate(pase, 1):
        row["rank"] = i
        row["semaforo"] = semaforo(i, len(pase))

    # comparativa vacíos
    lines = [
        "# Informe Mega Coliseo — Pase de batalla Beru",
        "",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Status checkpoint: `{ckpt.get('status')}`",
        f"- Jobs: **{len(jobs)}**",
        f"- Vacíos dorados malla×1: `{[round(v*100,1) for v in dorados_x1]}`",
        f"- Vacíos dorados malla×2: `{[round(v*100,1) for v in (ckpt.get('vacios_dorados') or {}).get('x2') or []]}`",
        f"- Outliers re-run: `{ckpt.get('outliers') or []}`",
        "",
        "## Qué se midió",
        "",
        "Legión al máximo (capas + fusión hoz + Mega), contabilidad masa seca, "
        "indicador **calor pase** = 3d 20% · mes 50% · año 30%. "
        "Dos campañas: malla oz/red normal y ×2. Sub-Berus Soldado→Mariscal sobre los 2 vacíos dorados.",
        "",
        "## Pase de batalla (ranking de rangos)",
        "",
        f"Vacío de referencia ~**{v0:.1f}%** · malla ×1 · mejor rango por activo.",
        "",
        "| # | Activo | Rango | Tier | Calor | Efi año | Plata $ | Capas | Fusiones | Megas | Semáforo |",
        "|---|--------|-------|------|------:|--------:|--------:|------:|---------:|------:|----------|",
    ]
    for row in pase:
        lines.append(
            f"| {row['rank']} | {row['activo']} | {row.get('rango')} | {row.get('tier_id')} | "
            f"{float(row['calor_pase']):.2f} | {float(row['efi_anio']):.1f} | "
            f"{float(row['botin_neto']):.0f} | {row.get('n_capas', 0)} | "
            f"{row.get('n_fusiones', 0)} | {row.get('n_megas', 0)} | {row['semaforo']} |"
        )

    lines += ["", "## Gráficas", ""]
    for c in charts:
        lines.append(f"- `{c}`")

    lines += [
        "",
        "## Conclusiones (auto)",
        "",
        "1. El pase de batalla ordena **activo × rango** para despertar legión, no solo el coin.",
        "2. Comparar gráficas malla ×1 vs ×2: si ×2 gana en mediana, conviene red más ancha en vivo.",
        "3. Outliers (masa_cap / efi extrema) deben leerse con el job `outlier` path=min.",
        "4. El desglose mensual está en cada job JSON bajo `meses`.",
        "",
        "## Cómo reanudar / repetir",
        "",
        "```text",
        "python scripts/coliseo_mega_campana.py --resume",
        "python scripts/coliseo_mega_informe.py",
        "```",
        "",
    ]

    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "vacios_dorados": ckpt.get("vacios_dorados"),
        "outliers": ckpt.get("outliers"),
        "pase_batalla": pase,
        "charts": charts,
        "n_jobs": len(jobs),
    }
    return "\n".join(lines) + "\n", payload


def main() -> int:
    jobs = _load_jobs()
    if not jobs:
        print("Sin jobs en checkpoint. Corre primero coliseo_mega_campana.py")
        return 2
    md, payload = build_informe(jobs)
    MEGA.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Informe: {OUT_MD}")
    print(f"JSON: {OUT_JSON}")
    print(f"Jobs: {len(jobs)} · charts: {len(payload.get('charts') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
