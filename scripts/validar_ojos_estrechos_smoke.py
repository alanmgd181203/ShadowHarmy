"""Smoke — ojos estrechos Santos last price (sin orderbook)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.config as config
from core import ojos_estrechos


def test_bases_santos_incluyen_pase():
    bases = ojos_estrechos.bases_santos()
    for a in ("MNT", "ETH", "BCH", "OP"):
        assert a in bases, a
    assert "MNT" in ojos_estrechos.SANTOS_PASE


def test_aplicar_apaga_books():
    prev_bases = list(getattr(config, "BRIDGE_WS_BASES", None) or [])
    prev_books = bool(getattr(config, "BRIDGE_WS_SUBSCRIBE_BOOKS", True))
    prev_bn = bool(getattr(config, "BINANCE_REF_ENABLED", True))
    try:
        out = ojos_estrechos.aplicar_ojos_last_price_santos(["MNT", "ETH"])
        assert out == ["MNT", "ETH"]
        assert config.BRIDGE_WS_BASES == ["MNT", "ETH"]
        assert config.BRIDGE_WS_SUBSCRIBE_BOOKS is False
        assert config.BINANCE_REF_ENABLED is False
    finally:
        config.BRIDGE_WS_BASES = prev_bases
        config.BRIDGE_WS_SUBSCRIBE_BOOKS = prev_books
        config.BINANCE_REF_ENABLED = prev_bn


def test_arise_ojos_importa_estrechos():
    src = (ROOT / "scripts" / "arise_ojos_tusk.py").read_text(encoding="utf-8")
    assert "ojos_estrechos" in src
    assert "aplicar_ojos_last_price_santos" in src


def main() -> int:
    test_bases_santos_incluyen_pase()
    test_aplicar_apaga_books()
    test_arise_ojos_importa_estrechos()
    print("validar_ojos_estrechos_smoke: OK (Santos · books OFF)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
