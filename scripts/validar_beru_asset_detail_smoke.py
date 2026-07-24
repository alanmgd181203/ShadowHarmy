#!/usr/bin/env python3
"""
Smoke Sub-Santuario Beru — core/beru_asset_detail.py

Verifica:
  A) Estado cero
  B) Flota por activo + composición caza/neg
  C) Red engorde (frontera)
  D) Crónica append / load
  E) mapa_asset_details + enriquecer_legion

Uso: python scripts/validar_beru_asset_detail_smoke.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import beru_asset_detail as bad  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _barco(**kw):
    base = dict(
        uid="BERU_SEM_ETH_1",
        estado="NEGOCIANDO",
        direccion="LONG",
        masa=25.0,
        masa_congelada=25.0,
        centro_manto=3000.0,
        centro_local=3000.0,
        oz_adan=3015.0,
        red_adan=2970.0,
        oz_pct=0.005,
        red_pct=-0.01,
        frente_asignado="ETHUSDT_SPOT",
        precio_entrada_real=3000.0,
        precio_salida_real=0.0,
        tier_id="PROTO1",
        modo_combate="CAZA",
        capa=1,
        generacion=1,
        es_super_beru=False,
        ciclo_infinito=False,
        neg_post_cazador=False,
        neg_toques_ciclo=0,
        ancla_cosecha_pct=0.0,
        max_favor=0.0,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_cero() -> None:
    s = bad.snapshot_cero("ETH")
    _assert(s["symbol"] == "ETH", "symbol")
    _assert(s["fuente"] == "cero", "fuente")
    _assert(s["n_barcos"] == 0, "barcos 0")
    _assert(s["composicion"]["pct_caza"] == 0, "pct caza")
    print("  A) estado cero OK")


def test_flota_composicion() -> None:
    leg = [
        _barco(uid="BERU_SEM_ETH_CAZA", modo_combate="CAZA", estado="NEGOCIANDO"),
        _barco(
            uid="BERU_SEM_ETH_NEG",
            modo_combate="NEGOCIADOR",
            estado="ESPERANDO_CONDICIONAL",
            neg_post_cazador=True,
            oz_adan=2985.0,
            red_adan=3010.0,
        ),
        _barco(
            uid="BERU_SEM_BTC_1",
            frente_asignado="BTCUSDT_SPOT",
            centro_manto=100000.0,
            oz_adan=100100.0,
            red_adan=99000.0,
            precio_entrada_real=100000.0,
        ),
    ]
    flota = bad.flota_resumen(leg, semilla="ETH")
    acts = {a["activo"]: a for a in flota["activos"]}
    _assert("ETH" in acts and "BTC" in acts, "activos ETH+BTC")
    _assert(acts["ETH"]["n_caza"] >= 1, "eth caza")
    _assert(acts["ETH"]["n_negociando"] >= 1, "eth neg")
    _assert(acts["ETH"]["es_semilla"] is True, "semilla ETH")
    snap = bad.snapshot_activo("ETH", leg, precio_mark=3010.0, semilla="ETH")
    _assert(snap["n_barcos"] == 2, f"eth barcos {snap['n_barcos']}")
    _assert(snap["masa_total_usd"] > 0, "masa")
    _assert(snap["pnl_est_usd"] is not None, "pnl")
    _assert(len(snap["grafica"]["niveles"]) >= 1, "grafica")
    print("  B) flota composición OK")


def test_red_engorde() -> None:
    # Dos cazas LONG: frontera = red más baja
    a = _barco(uid="BERU_A", red_adan=2970.0, red_pct=-0.01, estado="NEGOCIANDO", modo_combate="CAZA")
    b = _barco(uid="BERU_B", red_adan=2950.0, red_pct=-0.0167, estado="NEGOCIANDO", modo_combate="CAZA")
    re = bad.red_engorde_de_legion([a, b], "ETH")
    _assert(re is not None, "red existe")
    _assert(re["uid"] == "BERU_B", f"frontera {re['uid']}")
    _assert(re["precio"] == 2950.0, "precio frontera")
    print("  C) red engorde OK")


def test_cronica() -> None:
    prev = bad.CRONICA_DIR
    with tempfile.TemporaryDirectory() as td:
        bad.CRONICA_DIR = Path(td)
        try:
            bad.append_cronica("ETH", {"tipo": "COSECHA", "detalle": "botín test", "precio": 3010})
            bad.append_cronica("ETH", {"tipo": "MEGA_RESET", "detalle": "nuevo 0"})
            rows = bad._cargar_cronica("ETH", limit=10)
            _assert(len(rows) == 2, f"rows {len(rows)}")
            _assert(rows[-1]["tipo"] == "MEGA_RESET", "ultimo mega")
            snap = bad.snapshot_activo("ETH", [], semilla="ETH")
            _assert(len(snap["cronica"]) == 2, "cronica en snapshot")
        finally:
            bad.CRONICA_DIR = prev
    print("  D) crónica OK")


def test_mapa_y_enriquecer() -> None:
    leg = [_barco()]
    m = bad.mapa_asset_details(leg, precios={"ETH": 3010.0}, semilla="ETH")
    _assert("ETH" in m, "mapa ETH")
    _assert(m["ETH"]["fuente"] == "legion", "fuente legion")
    enr = bad.enriquecer_legion_resumen(leg, semilla="ETH")
    _assert(len(enr) == 1 and enr[0]["activo"] == "ETH", "enriquecer")
    _assert(bad.activo_de_legionario(leg[0], "ETH") == "ETH", "activo_de_legionario")
    print("  E) mapa + enriquecer OK")


def main() -> None:
    print("Smoke Sub-Santuario Beru")
    test_cero()
    test_flota_composicion()
    test_red_engorde()
    test_cronica()
    test_mapa_y_enriquecer()
    print("PASS 5/5")


if __name__ == "__main__":
    main()
