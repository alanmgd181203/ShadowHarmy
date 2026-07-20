#!/usr/bin/env python3
"""Smoke lote Bybit — minOrderQty + qtyStep desde BD Jess."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import lote_bybit as lote
from core import escalera_precios as esc


def test_filtros_btc():
    f = lote.filtros_lote("BTCUSDT_LINEAL")
    assert f.get("ok") is True, f"BD ausente o BTC sin linear: {f}"
    assert float(f["qtyStep"]) == 0.001
    assert float(f["minOrderQty"]) == 0.001
    print("  filtros BTC linear OK", f["qtyStep"], f["minOrderQty"])


def test_cuantizar_btc():
    # 0.0027 → floor 0.002
    q = lote.cuantizar_qty(0.0027, min_qty=0.001, qty_step=0.001, mode="floor")
    assert abs(q - 0.002) < 1e-9, q
    # bajo mínimo → 0
    assert lote.cuantizar_qty(0.0004, min_qty=0.001, qty_step=0.001) == 0.0
    # exactamente mínimo
    assert abs(lote.cuantizar_qty(0.001, min_qty=0.001, qty_step=0.001) - 0.001) < 1e-9
    print("  cuantizar BTC OK")


def test_usd_a_qty_btc():
    # ~$130 a $65000 ≈ 0.002 BTC
    r = lote.cuantizar_presupuesto_usd(130.0, 65000.0, "BTCUSDT_LINEAL")
    assert r["ok"] is True
    assert abs(r["qty"] - 0.002) < 1e-9, r
    print("  USD->qty BTC OK", r["qty"], r["usd"])


def test_escalera_lote_btc():
    # 0.008 BTC → varios peldaños múltiplo de 0.001
    p = esc.armar_peldaños_lote(
        0.008, 65000.0, "Buy",
        frente="BTCUSDT_LINEAL", unidad="qty", n_max=4,
    )
    assert len(p) >= 2, p
    for x in p:
        assert abs(round(x["tamaño"] / 0.001) * 0.001 - x["tamaño"]) < 1e-9
        assert x["tamaño"] + 1e-12 >= 0.001
    print("  escalera lote BTC OK", [x["tamaño"] for x in p])


def test_paso_minimo():
    paso = lote.paso_minimo_usd("BTCUSDT_LINEAL", 65000.0)
    # 0.001 * 65000 = 65 (más notional $5)
    assert paso >= 60.0, paso
    print("  paso mínimo BTC ~$", round(paso, 2))


def main():
    print("[SMOKE] lote_bybit + escalera cuantizada")
    bd = Path("data/bybit_parametros_mercado.json")
    if not bd.exists():
        print("[SKIP] sin data/bybit_parametros_mercado.json — Jess debe sync")
        return 0
    test_filtros_btc()
    test_cuantizar_btc()
    test_usd_a_qty_btc()
    test_escalera_lote_btc()
    test_paso_minimo()
    print("[OK] lote_bybit smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
