#!/usr/bin/env python3
"""Smoke Beru OKX — mar, lotes, plan altar (sin manos)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("BERU_MAR", "okx")

import core.config as config  # noqa: E402
from core import beru_mar  # noqa: E402
from core import beru_rango_altar as altar  # noqa: E402
from core import lote_beru  # noqa: E402
from core.models import BeruShip  # noqa: E402


def test_mar_mapping():
  assert beru_mar.mar_activo() == "okx"
  assert beru_mar.activo_a_inst_id("ETH") == "ETH-USDT-SWAP"
  assert beru_mar.inst_id_a_activo("HYPE-USDT-SWAP") == "HYPE"
  assert beru_mar.frente_lineal("UNI") == "UNIUSDT_LINEAL"


def test_lote_masa():
  pack = lote_beru.masa_a_qty(5.0, 3000.0, "ETHUSDT_LINEAL", mode="ceil")
  assert pack.get("ok"), pack
  assert float(pack["qty"]) > 0


def test_plan_trailing():
  b = BeruShip(
    uid="SMOKE",
    centro_local=100.0,
    masa=5.0,
    direccion="SHORT",
    estado="CAZANDO",
    oz_adan=98.0,
    altar_revision=1,
  )
  plan = altar.plan_trailing_entrada(b, activo="ETH", masa_usd=5.0, trigger_price=98.0)
  assert plan.side == "Sell"
  assert plan.qty > 0
  assert plan.trigger_price > 0
  assert plan.link_id.startswith("BRG-")


def main():
  assert str(config.BERU_MAR).lower() == "okx"
  test_mar_mapping()
  test_lote_masa()
  test_plan_trailing()
  print("validar_beru_okx_smoke: OK")


if __name__ == "__main__":
  main()
