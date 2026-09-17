#!/usr/bin/env python3
"""Smoke — mapeo get_positions OKX → forma Bybit (sin credenciales)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.okx_bridge import OkxBridge, _map_okx_position_row, pos_side_entrada


def test_pos_side_entrada():
    assert pos_side_entrada(side="Buy", position_idx=1) == "long"
    assert pos_side_entrada(side="Sell", position_idx=2) == "short"
    assert pos_side_entrada(side="Sell", position_idx=None) == "short"
    assert pos_side_entrada(side="Buy", position_idx=None) == "long"
    # Nunca net: short no puede quedar ambiguo
    assert pos_side_entrada(side="Sell", position_idx=0) == "short"


def test_map_long_net():
    row = {
        "instId": "KORU-USDT-SWAP",
        "pos": "0.02",
        "posSide": "net",
        "avgPx": "19.52",
        "markPx": "19.50",
        "lever": "10",
    }
    m = _map_okx_position_row(row)
    assert m is not None
    assert m["symbol"] == "KORUUSDT"
    assert m["side"] == "Buy"
    assert float(m["size"]) == 0.02
    assert float(m["avgPrice"]) == 19.52


def test_map_hedge_short():
    row = {
        "instId": "DGAI-USDT-SWAP",
        "pos": "24",
        "posSide": "short",
        "avgPx": "0.91",
        "markPx": "0.91",
        "lever": "5",
    }
    m = _map_okx_position_row(row)
    assert m is not None
    assert m["side"] == "Sell"


def test_map_flat():
    assert _map_okx_position_row({"instId": "ETH-USDT-SWAP", "pos": "0"}) is None


def test_get_positions_inverse_empty():
    class _Tank:
        nodos = []

    b = OkxBridge(_Tank(), None, None)
    r = b.get_positions(category="inverse")
    assert r.get("retCode") == 0
    assert r.get("result", {}).get("list") == []


def test_sz_okx_sin_polvo_float():
    from core import lote_okx

    f = "KORUUSDT_LINEAL"
    assert lote_okx.sz_okx_str(0.41000000000000003, f) == "0.41"
    assert lote_okx.cuantizar_qty(0.35000000000000003, f) == 0.35
    assert lote_okx.cuantizar_qty(0.35, f) == lote_okx.cuantizar_qty(0.3500001, f)


def main() -> int:
    test_pos_side_entrada()
    test_map_long_net()
    test_map_hedge_short()
    test_map_flat()
    test_get_positions_inverse_empty()
    test_sz_okx_sin_polvo_float()
    print("OK validar_okx_positions_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
