#!/usr/bin/env python3
"""Informe Monarca — sesgo estructural detallado (lectura, sin manos).

Incluye:
  - Ceros spot / lineal / inverso vs índice
  - % del tiempo que el gap lineal-inverso VIVE en el desfase (abrumador o no)
  - Episodios de VOLTEO (cuando se sale al lado opuesto del cero)

Uso (Jess / ojos calientes):
  git pull
  python scripts/informe_sesgo_monarca.py
  python scripts/informe_sesgo_monarca.py --ventana corto
  python scripts/informe_sesgo_monarca.py --backfill --dias 30

Escribe:
  migracion/INFORME_SESGO_ESTRUCTURAL.md
  data/informe_sesgo_estructural.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import kaiser_sesgo_index as ksi
from core.kaiser_sesgo_index import MARES_EDGE, perfil_sesgo_edge

OUT_JSON = ROOT / "data" / "informe_sesgo_estructural.json"
OUT_MD = ROOT / "migracion" / "INFORME_SESGO_ESTRUCTURAL.md"


def _bases() -> list[str]:
    bases = [str(b).upper() for b in (getattr(config, "ACTIVOS_PENTIVERSO", None) or [])]
    for b in getattr(config, "ACTIVOS_TRINIDAD", None) or []:
        bu = str(b).upper()
        if bu not in bases:
            bases.append(bu)
    for extra in ("MNT", "BTC", "ETH", "LTC"):
        if extra not in bases:
            bases.append(extra)
    return bases[:16]


def _fmt(x: float | None, digits: int = 4) -> str:
    if x is None:
        return "—"
    return f"{x:+.{digits}f}"


def _pct(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{float(x) * 100:.1f}%"


def _fila(base: str, *, ventana: str) -> dict:
    mares = {}
    for mar, edge in MARES_EDGE.items():
        p = perfil_sesgo_edge(base, edge)
        pl = p.get("plazos") or {}
        med = pl.get("mediano") or {}
        corto = pl.get("corto") or {}
        mares[mar] = {
            "cero_pct": p.get("cero_estructural_pct"),
            "fuente": p.get("fuente_cero"),
            "etiquetas": p.get("etiquetas") or [],
            "n_mediano": int(med.get("n") or 0),
            "n_corto": int(corto.get("n") or 0),
            "media_mediano": med.get("media_pct"),
            "p10_mediano": med.get("p10_pct"),
            "p90_mediano": med.get("p90_pct"),
        }
    analisis = ksi.analisis_residencia_y_volteos(base, ventana=ventana)
    return {"base": base, "mares": mares, "analisis_manto": analisis}


def _texto_monarca(filas: list[dict], *, ts: float, ventana: str) -> str:
    lineas = [
        "# Informe Monarca — sesgo estructural (detallado)",
        "",
        f"**Fecha:** {time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))}  ",
        f"**Ventana analisis gap:** {ventana}  ",
        "**Que mide:** ceros vs indice Bybit + **% del tiempo** que el gap "
        "lineal↔inverso vive en ese desfase + **volteos** (lado opuesto del cero).",
        "",
        "**Para que:** el gap eterno no es oportunidad. Hay que saber si el desfase "
        "es abrumador y que pasa cuando se voltea (planear / aprovechar).",
        "",
        "## 1. Ceros por mar (vs indice)",
        "",
        "| Base | Spot cero % | Lineal cero % | Inverso cero % | Gap est. lineal-inv |",
        "|------|-------------|---------------|----------------|---------------------|",
    ]
    for f in filas:
        m = f["mares"]
        sp = m["spot"].get("cero_pct")
        ln = m["lineal"].get("cero_pct")
        inv = m["inverso"].get("cero_pct")
        ns = m["spot"].get("n_mediano") or 0
        nl = m["lineal"].get("n_mediano") or 0
        ni = m["inverso"].get("n_mediano") or 0
        gap = None
        if ln is not None and inv is not None:
            gap = float(ln) - float(inv)
        lineas.append(
            f"| {f['base']} | {_fmt(sp)} (n~{ns}) | {_fmt(ln)} (n~{nl}) | "
            f"{_fmt(inv)} (n~{ni}) | {_fmt(gap, 3)} |"
        )

    lineas.extend(
        [
            "",
            "## 2. Residencia — ¿cuanto tiempo vive en el desfase?",
            "",
            "Veredicto: **abrumador** ≥85% · **dominante** ≥65% · **mitad_mitad** ≥45% · "
            "si no → **inestable**.",
            "",
            "| Base | % en desfase | % clima normal | % volteado | Veredicto | n |",
            "|------|--------------|----------------|------------|-----------|---|",
        ]
    )
    for f in filas:
        a = f.get("analisis_manto") or {}
        if not a.get("ok"):
            lineas.append(
                f"| {f['base']} | — | — | — | sin_datos | {a.get('n', 0)} |"
            )
            continue
        lineas.append(
            f"| {f['base']} | {_pct(a.get('pct_tiempo_en_desfase'))} | "
            f"{_pct(a.get('pct_tiempo_clima_normal'))} | "
            f"{_pct(a.get('pct_tiempo_volteado'))} | "
            f"**{a.get('veredicto_residencia')}** | {a.get('n')} |"
        )

    lineas.extend(
        [
            "",
            "## 3. Volteos — cuando se sale del clima natural",
            "",
            "Volteo = el gap va al **lado opuesto** del cero estructural (mas alla de epsilon). "
            "Esos episodios son los candidatos a planear / aprovechar; no el gap eterno.",
            "",
            "| Base | Episodios | Duracion media (h) | Exceso medio % | Lectura |",
            "|------|-----------|--------------------|----------------|---------|",
        ]
    )
    for f in filas:
        a = f.get("analisis_manto") or {}
        if not a.get("ok"):
            lineas.append(f"| {f['base']} | — | — | — | {a.get('motivo', 'sin_datos')} |")
            continue
        v = a.get("volteos") or {}
        lineas.append(
            f"| {f['base']} | {v.get('n_episodios', 0)} | "
            f"{v.get('duracion_media_h') if v.get('duracion_media_h') is not None else '—'} | "
            f"{_fmt(v.get('exceso_medio_pct'), 4)} | {a.get('lectura', '')} |"
        )

    # Detalle top bases con volteos
    lineas.extend(["", "## 4. Muestra de episodios (hasta 5 por base con volteos)", ""])
    alguno = False
    for f in filas:
        a = f.get("analisis_manto") or {}
        eps = (a.get("volteos") or {}).get("episodios_muestra") or []
        if not eps:
            continue
        alguno = True
        lineas.append(f"### {f['base']}")
        lineas.append("")
        for e in eps[:5]:
            t0 = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(e["ts_inicio"])))
            lineas.append(
                f"- desde {t0}: {e['duracion_h']}h · "
                f"gap medio {_fmt(e.get('gap_medio_pct'))}% · "
                f"exceso max {_fmt(e.get('exceso_max_pct'))}%"
            )
        lineas.append("")
    if not alguno:
        lineas.append("_Sin episodios de volteo fuertes en la ventana (o datos insuficientes)._")
        lineas.append("")

    lineas.extend(
        [
            "## Como leerlo (Monarca)",
            "",
            "1. Si **% en desfase** es abrumador/dominante → el spread 'bonito' casi siempre "
            "es clima normal; sin cero estructural el ETA mentia hacia Asalto.",
            "2. Los **volteos** son raros: ahi el gap se pone en contra del sesgo. "
            "Ahi se planifica / aprovecha; el resto es mantenimiento del cero.",
            "3. Cable activo: `MANTO_CERO_ESTRUCTURAL=true` (frecuencia/ETA + puerta Igris).",
            "",
            f"JSON maquina: `{OUT_JSON.as_posix()}`",
            "",
            "### Jess — regenerar",
            "",
            "```bash",
            "git pull",
            "python scripts/informe_sesgo_monarca.py",
            "# opcional: python scripts/informe_sesgo_monarca.py --ventana corto",
            "# opcional: python scripts/informe_sesgo_monarca.py --backfill --dias 30",
            "git add migracion/INFORME_SESGO_ESTRUCTURAL.md data/informe_sesgo_estructural.json",
            'git commit -m "Informe sesgo detallado: residencia + volteos."',
            "git push",
            "```",
            "",
        ]
    )
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true", help="Refrescar muestras bases clave")
    ap.add_argument("--dias", type=int, default=30, help="Dias de backfill")
    ap.add_argument(
        "--ventana",
        default="mediano",
        choices=("dia", "corto", "mediano", "largo"),
        help="Ventana para % residencia / volteos",
    )
    args = ap.parse_args()
    bases = _bases()

    if args.backfill:
        from core import kaiser_backfill as kb

        print(f"[informe] backfill {len(bases)} bases x {args.dias}d ...")
        for b in bases:
            try:
                r = kb.backfill_base_sesgo_index(b, dias=args.dias)
                print(
                    " ",
                    b,
                    "ok=" + str(r.get("ok")),
                    {
                        k: (v or {}).get("filas_nuevas")
                        for k, v in (r.get("mares") or {}).items()
                    },
                )
            except Exception as e:
                print(" ", b, "ERR", str(e)[:120])

    filas = [_fila(b, ventana=args.ventana) for b in bases]
    ts = time.time()
    payload = {
        "ts": ts,
        "version": "detallado_residencia_volteos_v1",
        "doctrina": "CHECKPOINT_KAISER_INDICE_SESGO",
        "convencion": "signed_pct=(precio-index)/index*100",
        "ventana_analisis": args.ventana,
        "bases": filas,
        "nota_monarca": (
            "Cero = mediana vs indice. "
            "% en desfase = cuanto tiempo vive el gap en ese clima. "
            "Volteos = lado opuesto del cero (planear/aprovechar)."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = _texto_monarca(filas, ts=ts, ventana=args.ventana)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        print(md)
    except UnicodeEncodeError:
        print(md.encode("ascii", "replace").decode("ascii"))
    print(f"\n[informe] escrito {OUT_MD} · {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
