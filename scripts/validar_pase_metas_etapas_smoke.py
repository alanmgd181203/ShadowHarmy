#!/usr/bin/env python3
"""Smoke frío: metas del pase — capital vs nocional por grado.

Sin Bybit / sin manos. Demuestra:
1) Etapas — equity bajo abre Soldado, no salta a Mariscal (capital).
2) Sync — paso logrado solo si nocional del grado cubre (no capital 14).
3) meta_engorde_usd — need = nocional L+S del grado; capital queda en delta/need_capital.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc
from core import pase_director as pd


def _tusk_eth(have_usd: float):
    class Tusk:
        pesos = {
            "ETHUSD_INVERSE": {"long": float(have_usd), "precio_medio_long": 1.0},
            "ETHUSDT_LINEAL": {"short": 0.0, "precio_medio_short": 1.0},
        }

    return Tusk()


def test_etapas_no_salto_mariscal():
    """Equity que solo abre primeros pasos → ETH Soldado, nunca Mariscal."""
    eq = 14.0
    assert pd.potencia_n(eq) == 1
    plan = pd.plan_lote(eq, marcha_id="asalto", pasos_logrados=[])
    trabajo = list(plan["trabajo"] or [])
    assert trabajo, "debe haber trabajo con equity=Soldado ETH"
    assert any(
        str(p["activo"]).upper() == "ETH" and p["grado"] == "SOLDADO" for p in trabajo
    )
    assert abs(float(next(p for p in trabajo if p["activo"] == "ETH")["delta_usd"]) - 14.0) < 1e-9
    assert not any(p["grado"] == "MARISCAL" for p in trabajo)
    assert not any(
        str(p["activo"]).upper() == "ETH" and p["grado"] != "SOLDADO" for p in plan.get("lote") or []
    )
    eq2 = 123.0
    assert pd.potencia_n(eq2) == 5
    plan2 = pd.plan_lote(eq2, marcha_id="asalto", pasos_logrados=[])
    assert all(p["grado"] == "SOLDADO" for p in (plan2.get("lote") or []))
    assert not any(p["grado"] == "MARISCAL" for p in pd.pasos_en_potencia(eq2))
    print("  etapas (Soldado, no Mariscal) OK")


def test_sync_nocional_grado():
    """Soldado ETH no se marca con capital~14; exige ~1250 L+S. Capitán exige ~2500."""
    need_sol = pd.need_notional_grado_usd("ETH", "SOLDADO")
    need_cap = pd.need_notional_grado_usd("ETH", "CAPITAN")
    assert abs(need_sol - bc.notional_manto_ls_grado("ETH", "SOLDADO")) < 1e-6
    assert need_sol >= 1000.0, f"Soldado ETH nocional L+S demasiado bajo: {need_sol}"
    assert need_cap > need_sol

    eq = float(pd.paso_por_n(37)["acum_usd"])
    assert pd.potencia_n(eq) >= 37

    ruta = pd._ruta_progreso()
    previo = None
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            previo = f.read()
    prev_force = os.environ.get("PASE_PROGRESO_FORCE_WRITE")
    os.environ["PASE_PROGRESO_FORCE_WRITE"] = "1"
    try:
        pd.guardar_progreso([])

        # have = capital viejo (14) → NO marca Soldado
        plan_corto = pd.sincronizar_logrados_desde_tusk(
            _tusk_eth(14.0), eq, marcha_id="asalto",
        )
        assert 1 not in set(plan_corto["pasos_logrados"]), (
            "con have=14 capital, Soldado nocional aún no logable"
        )

        # have = nocional Soldado → marca paso 1; Capitán aún no
        pd.guardar_progreso([])
        plan_sol = pd.sincronizar_logrados_desde_tusk(
            _tusk_eth(need_sol), eq, marcha_id="asalto",
        )
        logs_sol = set(plan_sol["pasos_logrados"])
        assert 1 in logs_sol
        assert 37 not in logs_sol, "con have=Soldado nocional, Capitán aún no"

        # have = Capitán → marca Capitán
        pd.guardar_progreso(list(range(1, 37)))
        plan_cap = pd.sincronizar_logrados_desde_tusk(
            _tusk_eth(need_cap), eq, marcha_id="asalto",
        )
        assert 37 in set(plan_cap["pasos_logrados"])
        print("  sync nocional ETH (Soldado->Capitan) OK", need_sol, need_cap)
    finally:
        if prev_force is None:
            os.environ.pop("PASE_PROGRESO_FORCE_WRITE", None)
        else:
            os.environ["PASE_PROGRESO_FORCE_WRITE"] = prev_force
        if previo is None:
            if os.path.exists(ruta):
                os.remove(ruta)
        else:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(previo)


def test_meta_engorde_nocional():
    """meta.need_usd = nocional del grado; capital en need_capital / delta_paso."""
    eq = 14.0
    pierna = pd.need_notional_por_pierna_usd("ETH", "SOLDADO")
    need_ls = pd.need_notional_grado_usd("ETH", "SOLDADO")
    meta = pd.meta_engorde_usd(eq, "ETH", tusk=_tusk_eth(0), marcha_id="asalto", pasos_logrados=[])
    assert meta["ok"] is True
    assert abs(float(meta["need_usd"]) - need_ls) < 1e-6
    assert abs(float(meta["need_notional_pierna_usd"]) - pierna) < 1e-6
    assert abs(float(meta["delta_paso_usd"]) - 14.0) < 1e-6
    assert abs(float(meta["need_capital_usd"]) - 14.0) < 1e-6
    assert abs(float(meta["restante_usd"]) - need_ls) < 1e-6
    assert pierna >= 600.0, f"pierna Soldado ETH ~625; got {pierna}"

    # Capitán AVAX: have = Soldado nocional → aún pide restante hasta Capitán
    eq2 = float(pd.paso_por_n(11)["acum_usd"])
    logs = list(range(1, 11))
    need_sol = pd.need_notional_grado_usd("AVAX", "SOLDADO")
    need_cap = pd.need_notional_grado_usd("AVAX", "CAPITAN")
    from core import igris_manto as im
    fl, fs = im.frentes_bootstrap("AVAX")

    class TuskParc:
        pesos = {
            fl: {"long": need_sol, "precio_medio_long": 1.0},
            fs: {"short": 0.0, "precio_medio_short": 1.0},
        }

    meta_c = pd.meta_engorde_usd(
        eq2, "AVAX", tusk=TuskParc(), marcha_id="asalto", pasos_logrados=logs,
    )
    assert meta_c["ok"] and meta_c["grado"] == "CAPITAN"
    assert abs(float(meta_c["need_usd"]) - need_cap) < 1e-6
    assert float(meta_c["restante_usd"]) > 1e-6
    assert abs(float(meta_c["restante_usd"]) - (need_cap - need_sol)) < 1e-6
    print("  meta_engorde nocional OK", pierna, "pierna /", need_ls, "L+S")


def main():
    print("[SMOKE] pase metas capital vs nocional")
    test_etapas_no_salto_mariscal()
    test_sync_nocional_grado()
    test_meta_engorde_nocional()
    print("[OK] validar_pase_metas_etapas_smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
