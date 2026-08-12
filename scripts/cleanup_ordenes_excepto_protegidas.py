#!/usr/bin/env python3
"""Cleanup seguro: cancela órdenes abiertas NO protegidas (MNTUSD intacto).

No cierra posiciones. Solo cancel_order de restos del lote mezclado.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("IGRIS_PROTEGER_BASES", "MNT")
os.environ.setdefault("IGRIS_PROTEGER_SYMBOLS", "MNTUSD")

import core.config as config  # noqa: E402
from core import igris_proteccion as iprot  # noqa: E402
from pybit.unified_trading import HTTP  # noqa: E402


def main() -> int:
    # Cleanup real: no heredar MODO_SIMULACION=True del .env
    os.environ["MODO_SIMULACION"] = "False"
    import importlib
    importlib.reload(config)
    config.MODO_SIMULACION = False

    session = HTTP(
        testnet=False,
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
    )
    canceladas = 0
    protegidas = 0
    for category in ("linear", "inverse"):
        try:
            resp = session.get_open_orders(category=category, settleCoin="USDT" if category == "linear" else None)
        except TypeError:
            kwargs = {"category": category}
            if category == "linear":
                kwargs["settleCoin"] = "USDT"
            resp = session.get_open_orders(**kwargs)
        if resp.get("retCode") != 0:
            print(f"[!] get_open_orders {category}: {resp.get('retMsg')}")
            continue
        for o in resp.get("result", {}).get("list", []) or []:
            sym = str(o.get("symbol") or "").upper()
            oid = o.get("orderId")
            if not sym or not oid:
                continue
            if iprot.simbolo_protegido(sym):
                protegidas += 1
                print(f"  KEEP {category} {sym} {oid} (protegido)")
                continue
            try:
                r = session.cancel_order(category=category, symbol=sym, orderId=oid)
                ok = r.get("retCode") == 0
                canceladas += int(ok)
                print(f"  {'OK' if ok else 'FAIL'} cancel {category} {sym} {oid} · {r.get('retMsg')}")
            except Exception as e:
                print(f"  FAIL cancel {sym}: {e}")
    print(f"[CLEANUP] canceladas={canceladas} · protegidas_intactas={protegidas}")
    print(f"[CLEANUP] bases_protegidas={sorted(iprot.bases_protegidas())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
