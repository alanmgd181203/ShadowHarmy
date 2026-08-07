#!/usr/bin/env python3
"""Smoke frío: metas del pase por etapas vs acumulado del mismo barco.

Sin Bybit / sin manos. Demuestra:
1) Etapas — equity bajo abre Soldado, no salta a Mariscal.
2) Acumulado — sync marca Soldado con ~delta; Capitán exige Soldado+Capitán.
3) meta_engorde_usd — need = acum hasta el grado en foco (alineado con sync).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
    # Equity un poco mayor: varios Soldados, sigue sin Mariscal en potencia
    eq2 = 123.0
    assert pd.potencia_n(eq2) == 5
    plan2 = pd.plan_lote(eq2, marcha_id="asalto", pasos_logrados=[])
    assert all(p["grado"] == "SOLDADO" for p in (plan2.get("lote") or []))
    assert not any(p["grado"] == "MARISCAL" for p in pd.pasos_en_potencia(eq2))
    print("  etapas (Soldado, no Mariscal) OK")


def test_acumulado_sync_mismo_activo():
    """Soldado ETH ~14; Capitán ETH exige cobertura acumulada 14+12."""
    delta_sol = float(pd.paso_por_n(1)["delta_usd"])  # 14
    delta_cap = float(pd.paso_por_n(37)["delta_usd"])  # 12
    acum_cap = pd.need_acum_activo_hasta_paso("ETH", 37)
    assert abs(delta_sol - 14.0) < 1e-9
    assert abs(delta_cap - 12.0) < 1e-9
    assert abs(acum_cap - (delta_sol + delta_cap)) < 1e-9

    eq = float(pd.paso_por_n(37)["acum_usd"])  # potencia incluye Capitán ETH
    assert pd.potencia_n(eq) >= 37

    ruta = pd._ruta_progreso()
    previo = None
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            previo = f.read()
    # Smoke toca disco: forzar escritura aunque MODO_TESTNET esté en True
    prev_force = os.environ.get("PASE_PROGRESO_FORCE_WRITE")
    os.environ["PASE_PROGRESO_FORCE_WRITE"] = "1"
    try:
        # Solo pasos previos al Capitán ETH ya "logrados" en disco (lote lleno → cola Capitán)
        pd.guardar_progreso(list(range(1, 37)))

        # have = solo Soldado → sync NO marca Capitán
        plan_corto = pd.sincronizar_logrados_desde_tusk(
            _tusk_eth(delta_sol), eq, marcha_id="asalto",
        )
        logs_corto = set(plan_corto["pasos_logrados"])
        assert 1 in logs_corto
        assert 37 not in logs_corto, "con have=delta Soldado, Capitán aún no logable"

        # have = acum Soldado+Capitán → sync marca Capitán
        plan_lleno = pd.sincronizar_logrados_desde_tusk(
            _tusk_eth(acum_cap), eq, marcha_id="asalto",
        )
        assert 37 in set(plan_lleno["pasos_logrados"]), "acum Soldado+Capitán marca Capitán"
        print("  acumulado sync ETH (Soldado->Capitan) OK")
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


def test_meta_engorde_alineada_acum():
    """
    Documenta y fija: need_usd = acum hasta el paso en foco (no solo delta del grado).

    Caso atolladero histórico: have ≥ delta Capitán pero < acum → con need=delta
    restante=0 y Capitán no logable. Tras arreglo: restante = acum − have > 0.
    """
    eq = float(pd.paso_por_n(11)["acum_usd"])  # potencia hasta AVAX Capitán
    assert pd.potencia_n(eq) == 11
    logs = list(range(1, 11))  # Soldado AVAX (n=10) logrado → cola = Capitán
    plan = pd.plan_lote(eq, marcha_id="asalto", pasos_logrados=logs)
    foco = plan["foco"]
    assert foco and foco["activo"] == "AVAX" and foco["grado"] == "CAPITAN"
    assert int(foco["n"]) == 11

    delta_sol = float(pd.paso_por_n(10)["delta_usd"])
    delta_cap = float(pd.paso_por_n(11)["delta_usd"])
    acum = pd.need_acum_activo_hasta_paso("AVAX", 11)
    assert abs(acum - (delta_sol + delta_cap)) < 1e-9

    # Frentes AVAX reales del manto
    from core import igris_manto as im
    fl, fs = im.frentes_bootstrap("AVAX")

    class TuskParc:
        pesos = {
            fl: {"long": delta_sol, "precio_medio_long": 1.0},
            fs: {"short": 0.0, "precio_medio_short": 1.0},
        }

    have = delta_sol  # ya cubre delta Capitán solo, pero no el acum
    assert have + 1e-9 >= delta_cap, "precondición: have ≥ delta grado (atasco potencial)"
    assert have + 1e-9 < acum, "precondición: have < acum (Capitán no sync-logable)"

    meta = pd.meta_engorde_usd(
        eq, "AVAX", tusk=TuskParc(), marcha_id="asalto", pasos_logrados=logs,
    )
    assert meta["ok"] is True
    assert int(meta["paso_n"]) == 11
    assert abs(float(meta["delta_paso_usd"]) - delta_cap) < 1e-6
    # Fijo: need = acum (no delta del paso)
    assert abs(float(meta["need_usd"]) - acum) < 1e-6, (
        f"need debe ser acum={acum}, no delta={delta_cap}; got {meta['need_usd']}"
    )
    restante_esp = acum - have
    assert abs(float(meta["restante_usd"]) - restante_esp) < 1e-6
    assert float(meta["restante_usd"]) > 1e-6, (
        "arreglo anti-atasco: con have=Soldado, Capitán aún pide restante > 0"
    )
    assert meta["meta_llena"] is False

    # Cuando have = acum → restante 0 (meta llena; sync podría marcar)
    class TuskFull:
        pesos = {
            fl: {"long": acum, "precio_medio_long": 1.0},
            fs: {"short": 0.0, "precio_medio_short": 1.0},
        }

    meta2 = pd.meta_engorde_usd(
        eq, "AVAX", tusk=TuskFull(), marcha_id="asalto", pasos_logrados=logs,
    )
    assert float(meta2["restante_usd"]) <= 1e-6
    assert meta2["meta_llena"] is True

    # Soldado solo: need = delta (acum de un solo grado)
    meta_sol = pd.meta_engorde_usd(
        14.0, "ETH", tusk=_tusk_eth(0), marcha_id="asalto", pasos_logrados=[],
    )
    assert abs(float(meta_sol["need_usd"]) - 14.0) < 1e-6
    assert abs(float(meta_sol["delta_paso_usd"]) - 14.0) < 1e-6
    print("  meta_engorde acum!=delta (anti-atasco Capitan) OK")


def main():
    print("[SMOKE] pase metas por etapas vs acumulado")
    test_etapas_no_salto_mariscal()
    test_acumulado_sync_mismo_activo()
    test_meta_engorde_alineada_acum()
    print("[OK] validar_pase_metas_etapas_smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
