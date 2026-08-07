#!/usr/bin/env python3
"""Informe Monarca — ETA de despliegue del manto (2 marchas operativas).

Usa el indicador YA cableado con cero estructural (no gap eterno):
  Asalto / Personalizado (legado táctico·forzada → asalto al normalizar).

Uso (Jess, con muestras calientes):
  git pull
  python scripts/informe_eta_marchas.py
  python scripts/informe_eta_marchas.py --equity 1525
  python scripts/informe_eta_marchas.py --meta 100   # fuerza meta USD por activo

Escribe:
  migracion/INFORME_ETA_MARCHAS.md
  data/informe_eta_marchas.json
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
from core import manto_frecuencia as mf
from core import pase_director as pd

OUT_JSON = ROOT / "data" / "informe_eta_marchas.json"
OUT_MD = ROOT / "migracion" / "INFORME_ETA_MARCHAS.md"

MARCHAS_ORDEN = ("asalto", "personalizado")
TITULOS = {
    "asalto": "Asalto (tablas / market)",
    "personalizado": "Personalizado (~T calib)",
}


def _bases() -> list[str]:
    bases = [str(b).upper() for b in (getattr(config, "ACTIVOS_PENTIVERSO", None) or [])]
    for b in getattr(config, "ACTIVOS_TRINIDAD", None) or []:
        bu = str(b).upper()
        if bu not in bases:
            bases.append(bu)
    for extra in ("MNT", "BTC", "ETH", "LTC"):
        if extra not in bases:
            bases.append(extra)
    # Priorizar bases con historial tipico del informe sesgo
    prefer = ["BTC", "MNT", "ETH", "LTC", "DOGE", "AAVE", "BCH", "ETC", "SOL", "XRP"]
    ordered = [b for b in prefer if b in bases]
    for b in bases:
        if b not in ordered:
            ordered.append(b)
    return ordered[:14]


def _meta_para(base: str, marcha_id: str, equity: float, meta_fija: float | None) -> float:
    if meta_fija is not None and meta_fija > 0:
        return float(meta_fija)
    if equity > 0:
        me = pd.meta_engorde_usd(equity, base, marcha_id=marcha_id)
        m = float(me.get("need_fill_usd") or me.get("need_usd") or 0)
        if m > 0:
            return m
    return float(getattr(config, "MANTO_FREQ_META_DEFAULT_USD", 100.0) or 100.0)


def _fmt_h(h: float | None) -> str:
    if h is None:
        return "—"
    if h < 24:
        return f"{h:.1f}h"
    return f"{h/24:.1f}d ({h:.0f}h)"


def _fila_base(base: str, equity: float, meta_fija: float | None) -> dict:
    cero = ksi.cero_estructural_manto(base)
    fees = mf.fees_be_activo(base)
    freq = mf.frecuencia_activo(base)
    por_marcha = {}
    for mid in MARCHAS_ORDEN:
        meta = _meta_para(base, mid, equity, meta_fija)
        eta = mf.eta_despliegue_horas(base, meta, marcha_id=mid)
        por_marcha[mid] = {
            "meta_usd": meta,
            "eta": eta,
            "titulo": TITULOS[mid],
        }
    return {
        "base": base,
        "fees_be_pct": round(fees, 6),
        "cero_estructural": cero,
        "frecuencia": {
            "ok": freq.get("ok"),
            "modo_sugerido": freq.get("modo_sugerido"),
            "score_paciencia": freq.get("score_paciencia"),
            "pct_fees": (freq.get("contadores") or {}).get("fees", {}).get("pct_blend"),
            "pct_medio": (freq.get("contadores") or {}).get("medio_fees", {}).get("pct_blend"),
            "pct_tablas": (freq.get("contadores") or {}).get("tablas", {}).get("pct_blend"),
        },
        "marchas": por_marcha,
    }


def _texto_monarca(filas: list[dict], *, ts: float, equity: float, meta_fija: float | None) -> str:
    lineas = [
        "# Informe Monarca — ETA manto (2 marchas operativas)",
        "",
        f"**Fecha:** {time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))}  ",
        f"**Equity ref:** {equity:.0f} USD  " if equity > 0 else "**Equity ref:** (meta fija / default)  ",
        f"**Meta fija:** {meta_fija} USD  " if meta_fija else "",
        "**Ley:** oportunidades = exceso vs **cero estructural** "
        f"(`MANTO_CERO_ESTRUCTURAL={getattr(config, 'MANTO_CERO_ESTRUCTURAL', True)}`).",
        "",
        "Marchas operativas:",
        "- **Asalto** — entrar ya (umbral tablas / market; peaje aceptado)",
        "- **Personalizado** — el Monarca fija ~T; calib viva de umbral por par",
        "",
        "Legado táctico/forzada → se normaliza a asalto (fuera del altar).",
        "",
        "## Tabla ETA (base / opt / pes)",
        "",
        "| Base | Cero gap % | Fees % | Asalto | Personalizado | Modo sugerido |",
        "|------|------------|--------|--------|---------------|---------------|",
    ]
    for f in filas:
        cero = (f.get("cero_estructural") or {}).get("cero_pct")
        cero_s = f"{cero:+.3f}" if cero is not None else "—"
        fees = f.get("fees_be_pct")
        fees_s = f"{fees:.3f}" if fees is not None else "—"
        cells = []
        for mid in MARCHAS_ORDEN:
            eta = ((f.get("marchas") or {}).get(mid) or {}).get("eta") or {}
            if not eta.get("ok"):
                cells.append(eta.get("motivo", "sin_tasa")[:12])
            else:
                cells.append(
                    f"{_fmt_h(eta.get('eta_h'))} "
                    f"[{_fmt_h(eta.get('eta_h_opt'))}–{_fmt_h(eta.get('eta_h_pes'))}]"
                )
        while len(cells) < 2:
            cells.append("—")
        modo = (f.get("frecuencia") or {}).get("modo_sugerido") or "—"
        lineas.append(
            f"| {f['base']} | {cero_s} | {fees_s} | {cells[0]} | {cells[1]} | {modo} |"
        )

    lineas.extend(
        [
            "",
            "## Detalle por base (ops/h y meta)",
            "",
        ]
    )
    for f in filas:
        lineas.append(f"### {f['base']}")
        lineas.append("")
        cero = f.get("cero_estructural") or {}
        lineas.append(
            f"- Cero gap: `{cero.get('cero_pct')}` (fuente: {cero.get('fuente')}) · "
            f"fees BE: `{f.get('fees_be_pct')}%`"
        )
        fr = f.get("frecuencia") or {}
        lineas.append(
            f"- Freq blend fees/medio/tablas: "
            f"{fr.get('pct_fees')} / {fr.get('pct_medio')} / {fr.get('pct_tablas')} · "
            f"modo sugerido: **{fr.get('modo_sugerido')}**"
        )
        for mid in MARCHAS_ORDEN:
            block = (f.get("marchas") or {}).get(mid) or {}
            eta = block.get("eta") or {}
            lineas.append(
                f"- **{TITULOS[mid]}**: meta `${block.get('meta_usd')}` · "
                f"ops/h `{eta.get('ops_por_hora')}` · "
                f"bocados `{eta.get('bocados_est')}` · "
                f"ETA `{_fmt_h(eta.get('eta_h'))}` "
                f"(opt {_fmt_h(eta.get('eta_h_opt'))} / pes {_fmt_h(eta.get('eta_h_pes'))}) · "
                f"{'OK' if eta.get('ok') else eta.get('motivo')}"
            )
        lineas.append("")

    lineas.extend(
        [
            "## Como leerlo (Monarca)",
            "",
            "1. Si ves **sin_tasa**: faltan muestras `lineal_vs_inverse` en esa base "
            "(ojos/Kaiser deben muestrear el edge de manto; el sesgo vs indice solo no basta).",
            "2. ETA mas largo que el calculo viejo = correcto: ya no cuenta el gap eterno.",
            "3. Elige marcha mirando la fila de tus Santos / MNT: paciencia vs velocidad.",
            "4. Opt/pes = ritmo ×1.5 / ×0.5 de oportunidades (rango, no promesa).",
            "",
            f"JSON: `{OUT_JSON.as_posix()}`",
            "",
            "### Jess — regenerar y subir",
            "",
            "```bash",
            "git pull",
            "python scripts/informe_eta_marchas.py --equity 1525",
            "git add migracion/INFORME_ETA_MARCHAS.md data/informe_eta_marchas.json",
            'git commit -m "Informe ETA manto: 3 marchas con cero estructural."',
            "git push",
            "```",
            "",
        ]
    )
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--equity", type=float, default=1525.0, help="Equity USD para meta engorde pase")
    ap.add_argument("--meta", type=float, default=None, help="Forzar meta USD igual en todos")
    ap.add_argument("--bases", type=str, default="", help="CSV bases (default pentiverso+MNT)")
    args = ap.parse_args()

    bases = [b.strip().upper() for b in args.bases.split(",") if b.strip()] or _bases()
    filas = [_fila_base(b, float(args.equity or 0), args.meta) for b in bases]
    ts = time.time()
    payload = {
        "ts": ts,
        "version": "eta_3_marchas_cero_v1",
        "equity_usd": args.equity,
        "meta_fija_usd": args.meta,
        "manto_cero_estructural": bool(getattr(config, "MANTO_CERO_ESTRUCTURAL", True)),
        "bases": filas,
        "nota_monarca": (
            "ETA = meta / (mordida × ops/h). Ops cuentan exceso vs cero, no gap eterno."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = _texto_monarca(filas, ts=ts, equity=float(args.equity or 0), meta_fija=args.meta)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        print(md)
    except UnicodeEncodeError:
        print(md.encode("ascii", "replace").decode("ascii"))
    print(f"\n[informe] escrito {OUT_MD} · {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
