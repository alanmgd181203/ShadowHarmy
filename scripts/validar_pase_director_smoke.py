#!/usr/bin/env python3
"""Smoke director del pase — potencia, lote/reserva=1, fill=1, 2 marchas."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import pase_director as pd


def test_potencia():
    assert pd.potencia_n(13) == 0
    assert pd.potencia_n(14) == 1
    assert pd.potencia_n(123) == 5
    assert pd.potencia_n(1500) == 28
    assert pd.potencia_n(3161) == 52
    print("  potencia OK")


def test_lote_reserva_1():
    # 10 pasos potencia (~277), reserva 1 → lote 9
    eq = 277.0
    assert pd.potencia_n(eq) == 10
    assert set(pd.MARCHAS.keys()) == {"asalto", "personalizado"}
    assert pd.MARCHAS_UI == ("asalto", "personalizado")
    for mid in pd.MARCHAS_UI:
        assert pd.MARCHAS[mid]["reserva_pasos"] == 1
        assert abs(float(pd.MARCHAS[mid]["fill_ratio"]) - 1.0) < 1e-9
    plan = pd.plan_lote(eq, marcha_id="asalto", pasos_logrados=[])
    assert plan["reserva_pasos"] == 1
    assert plan["lote_techo_n"] == 9
    assert len(plan["lote"]) == 9
    assert len(plan["cola_fina"]) == 1
    assert len(plan["trabajo"]) == 9
    plan2 = pd.plan_lote(eq, marcha_id="asalto", pasos_logrados=list(range(1, 10)))
    assert plan2["lote_lleno"] is True
    assert len(plan2["trabajo"]) == 1
    assert plan2["foco"]["n"] == 10
    print("  lote reserva=1 OK")


def test_umbrales():
    fees = 0.10
    # Legado → asalto
    assert pd.normalizar_marcha("tactico") == "asalto"
    assert pd.normalizar_marcha("marcha_forzada") == "asalto"
    t = pd.umbral_por_marcha(fees, marcha_id="tactico")
    assert t["umbral_pct"] == 0.0 and t["force_market"] is True
    f = pd.umbral_por_marcha(fees, marcha_id="marcha_forzada", t0_paciencia=None)
    assert f["umbral_pct"] == 0.0 and f["force_market"] is True
    a = pd.umbral_por_marcha(fees, marcha_id="asalto")
    assert a["umbral_pct"] == 0.0
    assert a["force_market"] is True
    assert a["modo_paciencia"] == "marcha_asalto"
    print("  umbrales marcha OK")


def test_beru_gate():
    assert pd.beru_puede_cazar("ETH", 100, pasos_logrados=[]) is False
    assert pd.beru_puede_cazar("ETH", 100, pasos_logrados=[1]) is True
    assert pd.beru_puede_cazar("HYPE", 100, pasos_logrados=[1]) is False
    print("  beru gate OK")


def test_persist_marcha():
    previo = pd.cargar_marcha_payload()
    try:
        # Legado se persiste como asalto
        pd.guardar_marcha("tactico")
        assert pd.cargar_marcha() == "asalto"
        assert pd.perfil_marcha()["fill_ratio"] == 1.0
        pd.guardar_marcha("marcha_forzada")
        assert pd.cargar_marcha() == "asalto"
        try:
            pd.guardar_marcha("personalizado")
            raise AssertionError("personalizado sin dias debe fallar")
        except ValueError:
            pass
        payload = pd.guardar_marcha("personalizado", duracion_dias=3.0, equity_usd=277.0)
        assert payload["marcha_id"] == "personalizado"
        assert payload.get("duracion_dias") == 3.0
        assert pd.cargar_marcha() == "personalizado"
        assert pd.normalizar_marcha("custom") == "personalizado"
        print("  persist marcha + personalizado OK")
    finally:
        # No dejar el altar del Monarca en estado de smoke
        if previo and previo.get("marcha_id"):
            mid = str(previo.get("marcha_id"))
            dias = previo.get("duracion_dias")
            eq = previo.get("equity_usd")
            try:
                if mid == "personalizado" or pd.normalizar_marcha(mid) == "personalizado":
                    if dias and float(dias) > 0:
                        pd.guardar_marcha("personalizado", duracion_dias=float(dias), equity_usd=eq)
                    else:
                        pd.guardar_marcha("asalto", equity_usd=eq)
                else:
                    pd.guardar_marcha(pd.normalizar_marcha(mid), equity_usd=eq)
            except Exception:
                pd.guardar_marcha("asalto")
        else:
            pd.guardar_marcha("asalto")


def test_meta_fill_100():
    class FakeTusk:
        pesos = {}

    eq = 14.0
    meta = pd.meta_engorde_usd(eq, "ETH", tusk=FakeTusk(), marcha_id="asalto", pasos_logrados=[])
    assert meta["ok"]
    assert abs(meta["restante_usd"] - 14.0) < 1e-6
    assert abs(meta["fill_ratio"] - 1.0) < 1e-9
    print("  meta fill 100% OK")


def test_resumen():
    r = pd.resumen_director(411)
    assert r["marcha_id"] in pd.MARCHAS
    assert r["potencia_n"] == 13
    print("  resumen OK", r["marcha_titulo"], "potencia", r["potencia_n"])


def main():
    print("[SMOKE] Pase director — 2 marchas operativas")
    test_potencia()
    test_lote_reserva_1()
    test_umbrales()
    test_beru_gate()
    test_persist_marcha()
    test_meta_fill_100()
    test_resumen()
    print("[OK] pase_director smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
