#!/usr/bin/env python3
"""Limpia campo de entrenamiento: cierra ETH inverse+lineal en TESTNET.

MNT / colateral intocable. Aborta si MODO_TESTNET!=True o si el símbolo es protegido.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["MODO_TESTNET"] = "True"
os.environ.setdefault("MODO_SIMULACION", "False")

import core.config as config
from core import igris_proteccion as iprot
from pybit.unified_trading import HTTP


PROHIBIDOS = ("MNT",)


def _assert_campo_seguro() -> None:
    if not config.TESTNET:
        raise SystemExit("ABORT: solo testnet")
    if not config.API_KEY_TESTNET or config.API_KEY != config.API_KEY_TESTNET:
        raise SystemExit("ABORT: llaves activas no son TESTNET")
    if not config.API_SECRET:
        raise SystemExit("ABORT: sin secret testnet")


def _protegido(symbol: str, category: str) -> bool:
    sym = (symbol or "").upper()
    if any(p in sym for p in PROHIBIDOS):
        return True
    if iprot.simbolo_protegido(sym) or iprot.base_protegida("MNT"):
        if "MNT" in sym:
            return True
    if category.lower() not in ("linear", "inverse"):
        return True
    return False


def _listar(session: HTTP, category: str, symbol: str) -> list[dict]:
    r = session.get_positions(category=category, symbol=symbol)
    if r.get("retCode") != 0:
        print(f"  aviso get_positions {category} {symbol}: {r.get('retMsg')}")
        return []
    out = []
    for row in (r.get("result") or {}).get("list") or []:
        size = float(row.get("size") or 0)
        if size > 0:
            out.append(row)
    return out


def _cancelar_abiertas(session: HTTP, category: str, symbol: str) -> int:
    if _protegido(symbol, category):
        print(f"  SKIP cancel protegido {symbol}")
        return 0
    n = 0
    try:
        r = session.cancel_all_orders(category=category, symbol=symbol)
        if r.get("retCode") == 0:
            n = 1
            print(f"  cancel_all {category} {symbol}: OK")
        else:
            print(f"  cancel_all {category} {symbol}: {r.get('retMsg')}")
    except Exception as e:
        print(f"  cancel_all error {symbol}: {e}")
    return n


def _cerrar(session: HTTP, category: str, symbol: str, side: str, qty: float) -> bool:
    if _protegido(symbol, category):
        print(f"  BLOQUEADO colateral: no tocar {symbol}")
        return False
    # Cerrar: lado opuesto
    close_side = "Sell" if side == "Buy" else "Buy"
    params = {
        "category": category,
        "symbol": symbol,
        "side": close_side,
        "orderType": "Market",
        "qty": str(qty),
        "reduceOnly": True,
        "orderLinkId": f"SA-CLEAN-{int(time.time()*1000)%10_000_000}",
    }
    print(f"  CERRAR {category} {symbol}: {side} size={qty} → {close_side} Market reduceOnly")
    r = session.place_order(**params)
    if r.get("retCode") == 0:
        print(f"    OK orderId={((r.get('result') or {}).get('orderId'))}")
        return True
    print(f"    FAIL {r.get('retMsg')}")
    return False


def main() -> int:
    _assert_campo_seguro()
    print("=" * 52)
    print("  Limpieza campo TESTNET — solo ETH")
    print("  MNT / colateral: INTOCABLE")
    print(f"  key={str(config.API_KEY)[:6]}… testnet={config.TESTNET}")
    print("=" * 52)

    session = HTTP(
        testnet=True,
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
    )

    # Blindaje: jamás consultar/cerrar MNT en este ritual
    objetivos = [
        ("inverse", "ETHUSD"),
        ("linear", "ETHUSDT"),
    ]

    print("\n[1] Estado antes:")
    abiertas: list[tuple[str, str, dict]] = []
    for cat, sym in objetivos:
        rows = _listar(session, cat, sym)
        if not rows:
            print(f"  {cat} {sym}: limpio")
        for row in rows:
            print(
                f"  {cat} {sym}: side={row.get('side')} size={row.get('size')} "
                f"avg={row.get('avgPrice')}"
            )
            abiertas.append((cat, sym, row))

    print("\n[2] Cancelar órdenes pendientes ETH…")
    for cat, sym in objetivos:
        _cancelar_abiertas(session, cat, sym)

    print("\n[3] Cerrar posiciones…")
    ok_n = fail_n = 0
    for cat, sym, row in abiertas:
        if _cerrar(session, cat, sym, str(row.get("side")), float(row.get("size") or 0)):
            ok_n += 1
        else:
            fail_n += 1

    time.sleep(1.5)

    print("\n[4] Radar después:")
    resto = 0
    for cat, sym in objetivos:
        rows = _listar(session, cat, sym)
        if not rows:
            print(f"  {cat} {sym}: LIMPIO")
        for row in rows:
            resto += 1
            print(
                f"  AUN ABIERTA {cat} {sym}: side={row.get('side')} size={row.get('size')}"
            )

    # Doble check: no hubo MNT
    print("\n[5] Candado MNT:")
    for cat, sym in (("inverse", "MNTUSD"), ("linear", "MNTUSDT")):
        print(f"  no tocado deliberadamente: {cat} {sym}")

    limpio = resto == 0
    print("\n" + ("RADAR_LIMPIO" if limpio else "RADAR_CON_RESTOS"))
    print(f"cierres_ok={ok_n} fallos={fail_n} restos={resto}")
    return 0 if limpio else 2


if __name__ == "__main__":
    raise SystemExit(main())
