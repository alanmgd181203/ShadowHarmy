#!/usr/bin/env python3
"""Perfil Kaiser + metaverso — smoke y backfill opcional."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import kaiser_perfil as perfil
from core import metaverso_grafo as mv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", action="store_true", help="Intentar kline Bybit (LTC/BTC)")
    parser.add_argument("--base", default="LTC")
    args = parser.parse_args()

    if args.backfill:
        from core.kaiser_backfill import backfill_base_perp_index
        r = backfill_base_perp_index(args.base)
        print("backfill:", r)

    p = perfil.perfil_par(args.base, "perp_vs_index")
    print("perfil", args.base, "corto:", p["plazos"]["corto"]["etiquetas"])
    print("perfil", args.base, "largo:", p["plazos"]["largo"]["etiquetas"])
    print("resumen:", p["etiquetas_resumen"])

    matriz_fake = [
        {"base": "LTC", "tipo": "usdt_vs_usdc", "spread_pct": 0.35},
        {"base": "LTC", "tipo": "spot_vs_perp", "spread_pct": 0.28},
        {"base": "LTC", "tipo": "perp_vs_index", "spread_pct": 0.15, "desvio_signed_pct": 0.15},
    ]
    perfiles = {args.base.upper(): {"perp_vs_index": p, "usdt_vs_usdc": p, "spot_vs_perp": p}}
    o = mv.oportunidades_metaverso(matriz_fake, [args.base], perfiles)
    import json
    print("metaverso:", json.dumps(o.get(args.base.upper(), {}), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
