#!/usr/bin/env python3
"""Kaiser / mantenimiento — refresca parametros Bybit (lev max + minimos).

Pensado para correr de vez en cuando (cron, o futuro gancho Kaiser) cuando
Bybit mueva filtros. Requiere red que no reciba 403.

Uso:
  python scripts/kaiser_actualizar_parametros_bybit.py
  python scripts/kaiser_actualizar_parametros_bybit.py --no-prices
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_bpm():
    path = ROOT / "scripts" / "bybit_parametros_mercado.py"
    spec = importlib.util.spec_from_file_location("bybit_parametros_mercado", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-prices", action="store_true", help="No pedir tickers (min_usd parcial)")
    args = ap.parse_args()
    bpm = _load_bpm()

    print("Kaiser refresh — parametros Bybit…")
    try:
        linear = bpm.page_instruments("linear", quote_coin="USDT")
        inverse = bpm.page_instruments("inverse")
        spot_usdt = bpm.page_instruments("spot", quote_coin="USDT")
        spot_usdc = bpm.page_instruments("spot", quote_coin="USDC")
    except Exception as e:
        print(f"FAIL API: {e}")
        return 2

    db = bpm.construir_base_parametros(
        linear=linear,
        inverse=inverse,
        spot_usdt=spot_usdt,
        spot_usdc=spot_usdc,
        fetch_prices=not args.no_prices,
    )
    path = bpm.guardar_base(db)
    m = db["meta"]
    print(
        f"OK → {path}\n"
        f"  bases={m['n_bases']} linear={m['n_linear']} inverse={m['n_inverse']} "
        f"spotUSDT={m['n_spot_usdt']} spotUSDC={m['n_spot_usdc']}"
    )
    for a in ("BTC", "ETH", "LTC", "SOL", "XRP"):
        row = (db.get("activos") or {}).get(a) or {}
        print(
            f"  {a}: lev L/I={row.get('max_leverage_linear')}/{row.get('max_leverage_inverse')} "
            f"piso_manto≈{row.get('piso_manto_usd')} "
            f"spotUSDT_min≈{(row.get('spot_usdt') or {}).get('min_usd_est')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
