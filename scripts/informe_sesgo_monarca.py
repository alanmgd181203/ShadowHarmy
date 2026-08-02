#!/usr/bin/env python3
"""Informe Monarca — ceros estructurales vs índice (lectura, sin manos).

Uso:
  python scripts/informe_sesgo_monarca.py
  python scripts/informe_sesgo_monarca.py --backfill   # refresca muestras bases clave (red)
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


def _fila(base: str) -> dict:
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
        }
    return {"base": base, "mares": mares}


def _texto_monarca(filas: list[dict], *, ts: float) -> str:
    lineas = [
        "# Informe Monarca — sesgo estructural vs índice",
        "",
        f"**Fecha:** {time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))}  ",
        "**Qué mide:** cuánto suele cotizar cada mar (spot / lineal / inverso) "
        "respecto al índice Bybit. Cero = mediana histórica; positivo = caro vs índice.",
        "",
        "**Para qué:** el gap eterno no es oportunidad. El reloj del manto y el disparo "
        "deben contar solo cuando el clima **se sale** de este cero.",
        "",
        "| Base | Spot cero % | Lineal cero % | Inverso cero % | Lectura |",
        "|------|-------------|---------------|----------------|---------|",
    ]
    for f in filas:
        m = f["mares"]
        sp = m["spot"].get("cero_pct")
        ln = m["lineal"].get("cero_pct")
        inv = m["inverso"].get("cero_pct")
        ns = m["spot"].get("n_mediano") or m["spot"].get("n_corto") or 0
        nl = m["lineal"].get("n_mediano") or m["lineal"].get("n_corto") or 0
        ni = m["inverso"].get("n_mediano") or m["inverso"].get("n_corto") or 0
        if sp is None and ln is None and inv is None:
            lectura = "sin datos locales"
        elif max(ns, nl, ni) < 15:
            lectura = "pocas muestras — orientar, no ley dura"
        else:
            bits = []
            if inv is not None and inv < -0.02:
                bits.append("inverso suele barato")
            if ln is not None and ln > 0.02:
                bits.append("lineal suele caro")
            if sp is not None and abs(sp) < 0.02:
                bits.append("spot pegado")
            if inv is not None and ln is not None:
                gap = ln - inv
                bits.append(f"gap lineal−inverso≈{gap:+.3f}% estructural")
            lectura = "; ".join(bits) if bits else "ver ceros"
        def fmt(x):
            return "—" if x is None else f"{x:+.4f}"
        lineas.append(
            f"| {f['base']} | {fmt(sp)} (n~{ns}) | {fmt(ln)} (n~{nl}) | "
            f"{fmt(inv)} (n~{ni}) | {lectura} |"
        )
    lineas.extend(
        [
            "",
            "## Como leerlo",
            "",
            "Si el **inverso** sale casi siempre negativo (barato vs indice) y el lineal "
            "un poco arriba, el spread lineal↔inverso **parece** oportunidad todo el dia. "
            "Eso es el sesgo eterno — no Asalto.",
            "",
            "Con el cable de frecuencia/ETA (cero estructural), solo cuentan las veces "
            "que el spread se **aleja** de ese clima normal.",
            "",
            f"JSON maquina: `{OUT_JSON.as_posix()}`",
            "",
        ]
    )
    return "\n".join(lineas)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true", help="Refrescar muestras bases clave")
    ap.add_argument("--dias", type=int, default=30, help="Días de backfill")
    args = ap.parse_args()
    bases = _bases()

    if args.backfill:
        from core import kaiser_backfill as kb

        print(f"[informe] backfill {len(bases)} bases × {args.dias}d …")
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

    filas = [_fila(b) for b in bases]
    ts = time.time()
    payload = {
        "ts": ts,
        "doctrina": "CHECKPOINT_KAISER_INDICE_SESGO",
        "convencion": "signed_pct=(precio-index)/index*100",
        "bases": filas,
        "nota_monarca": (
            "Cero estructural = mediana histórica vs índice. "
            "Oportunidad de manto = salir de ese cero, no el gap eterno."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = _texto_monarca(filas, ts=ts)
    OUT_MD.write_text(md, encoding="utf-8")
    try:
        print(md)
    except UnicodeEncodeError:
        print(md.encode("ascii", "replace").decode("ascii"))
    print(f"\n[informe] escrito {OUT_MD} · {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
