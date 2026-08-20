#!/usr/bin/env python3
"""Teatro visual Beru rango — bóveda de velas + HTML con Play y crónica.

Ejemplo:
  python scripts/teatro_beru_rango.py --activo ETH --dias 3
  python scripts/teatro_beru_rango.py --activo HYPE --dias 7 --abrir
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.teatro_beru_rango import correr_teatro


def main() -> int:
    ap = argparse.ArgumentParser(description="Teatro visual Beru rango")
    ap.add_argument("--activo", default="HYPE")
    ap.add_argument("--dias", type=int, default=3)
    ap.add_argument("--market", default="auto", choices=["auto", "spot", "linear"])
    ap.add_argument("--abrir", action="store_true", help="Abre el HTML al terminar")
    ap.add_argument("--out", default="", help="Carpeta de salida")
    args = ap.parse_args()

    out = Path(args.out) if args.out else None
    print(
        f"[TEATRO] Beru rango · {args.activo.upper()} · {args.dias}d · velas {args.market}",
        flush=True,
    )
    try:
        sim = asyncio.run(
            correr_teatro(
                activo=args.activo,
                dias=args.dias,
                market=args.market,
                out_dir=out,
            )
        )
    except FileNotFoundError as exc:
        print(f"FALLO: {exc}", flush=True)
        return 1

    paths = sim.get("paths") or {}
    print(
        f"OK · fuente={sim.get('fuente_velas')} · velas={sim['n_velas']} · "
        f"latidos={sim['n_latidos']} · eventos={sim['n_eventos']} · "
        f"cosechas={sim['cosechas']}",
        flush=True,
    )
    print(f"  HTML:    {paths.get('html')}", flush=True)
    print(f"  Cronica: {paths.get('cronica')}", flush=True)
    print(f"  JSON:    {paths.get('json')}", flush=True)
    print(
        "Abre el HTML, dale Play y lee la columna derecha: "
        "cada vez que arma Oz/Red o cosecha, explica precios y por que.",
        flush=True,
    )
    if args.abrir and paths.get("html"):
        webbrowser.open(Path(paths["html"]).resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
