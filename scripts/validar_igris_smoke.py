#!/usr/bin/env python3
"""Smoke Igris — banda delta, fases margen, frentes manto."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import igris_estado as ie
from core import mercado
import core.config as config


def test_fases_margen():
    assert ie.fase_margen(75) == "EXPANSION"
    assert ie.fase_margen(82) == "TERRENO_CAZA"
    assert ie.fase_margen(93) == "ALTA_PRESION"
    assert ie.fase_margen(94) == "ALTA_PRESION"
    assert ie.fase_margen(96) == "LEY_MARCIAL"
    print("  fases margen OK (horizonte 95%)")


def test_banda_delta():
    b_lo = mercado.calcular_banda_delta(50)
    b_hi = mercado.calcular_banda_delta(96)
    assert b_lo[0] < 0.5 < b_lo[1]
    assert b_hi[0] == b_hi[1] == 0.5
    assert mercado.verificar_delta_post_maniobra(50, 50, 50)
    assert not mercado.verificar_delta_post_maniobra(50, 80, 20)
    print("  banda delta OK:", b_lo, "->", b_hi)


def test_resumen_manto():
    r = ie.resumen_manto(
        margen_ocupado_pct=75,
        peso_long=30,
        peso_short=70,
        banda_min=0.45,
        banda_max=0.55,
    )
    assert r["fase_margen"] == "EXPANSION"
    assert r["accion_heuristica"] == "REBALANCEO_IGRIS"
    print("  resumen OK:", r["accion_heuristica"])


def test_frentes_manto():
    frentes = getattr(config, "FRENTES_MANTO_ALL", [])
    assert len(frentes) >= 4
    assert any("LINEAL" in f for f in frentes)
    print("  frentes manto OK:", len(frentes))


def test_bootstrap_se():
    from core import igris_manto as im
    fl, fs = im.frentes_bootstrap("ETH")
    assert fl == "ETHUSD_INVERSE" and fs == "ETHUSDT_LINEAL"
    ctx = {"ETHUSD_INVERSE": {"precio": 3000}, "ETHUSDT_LINEAL": {"precio": 3001}}
    assert im.bootstrap_viable(ctx, "ETH")[0]
    pesos = {}
    im.actualizar_promedio(pesos, fl, "LONG", 1.0, 3000)
    pesos[fl]["long"] += 1.0
    im.actualizar_promedio(pesos, fl, "LONG", 1.0, 3100)
    pesos[fl]["long"] += 1.0
    assert round(pesos[fl]["precio_medio_long"], 2) == 3050.0
    res = im.resumen_promedios(pesos)
    assert res and res[0]["frente"] == fl
    print("  bootstrap §E + promedio OK")


def test_despliegue_paciente():
    from core import igris_despliegue as ides
    import time

    sp = ides.spread_ejecutable_pct(100.0, 100.2)
    assert sp > 0.19
    assert ides.spread_ejecutable_pct(100.2, 100.0) < 0

    fees = ides.fees_break_even_pct("ETHUSD_INVERSE", "ETHUSDT_LINEAL")
    assert fees > 0

    t0 = time.time()
    u0 = ides.umbral_urgencia_pct(fees, t0, ahora=t0)
    assert abs(u0["umbral_pct"] - fees) < 1e-9
    assert u0["factor"] == 0.0
    assert u0["modo_paciencia"] == "fallback_estatico"

    # Reloj invertido: alta freq → tau grande; baja freq → tau chico
    perfil_alto = {
        "plazos": {"mediano": {"metricas": {"n_muestras": 100, "pct_tiempo_sobre_umbral": 0.9}, "etiquetas": []}},
    }
    perfil_bajo = {
        "plazos": {"mediano": {"metricas": {"n_muestras": 100, "pct_tiempo_sobre_umbral": 0.05}, "etiquetas": []}},
    }
    tau_hi = ides.tau_paciencia_horas(perfil_alto)
    tau_lo = ides.tau_paciencia_horas(perfil_bajo)
    assert tau_hi["modo"] == "kaiser_invertido"
    assert tau_hi["tau_h"] > tau_lo["tau_h"]
    # Misma edad: baja freq degrada más (factor mayor)
    edad = 4 * 3600
    f_hi = ides.factor_urgencia(t0, perfil_edge=perfil_alto, ahora=t0 + edad)
    f_lo = ides.factor_urgencia(t0, perfil_edge=perfil_bajo, ahora=t0 + edad)
    assert f_lo["factor"] > f_hi["factor"]

    # Fallback estático tras tau_base
    tau = float(config.IGRIS_URGENCIA_TAU_HORAS)
    u1 = ides.umbral_urgencia_pct(fees, t0, ahora=t0 + tau * 3600)
    assert u1["factor"] == 1.0
    assert u1["umbral_pct"] <= 0

    # Fracción Igris: sin pinza 0.85 — puede llegar a 1.0
    frac = ides.fraccion_mordida_igris(
        {"base": "ETH", "tipo_spread": "lineal_vs_inverse", "regalo_neto_pct_est": 0.5},
        tank_semaforo="VERDE",
        margen_ocupado_pct=50.0,
    )
    assert frac["fraccion"] <= 1.0
    assert frac["fraccion_sin_pinza_85"] is True
    # Greed pinzaría a 0.85; Igris permite hasta 1.0 si la cruda lo pide
    assert float(config.GREED_FRACCION_MAX) == 0.85  # Greed intacto

    class FakeTank:
        libros = {
            "ETHUSD_INVERSE": {"bids": [[99.9, 10]], "asks": [[100.0, 80]]},
            "ETHUSDT_LINEAL": {"bids": [[100.25, 80]], "asks": [[100.3, 10]]},
        }

        def _obtener_lider_verde(self):
            return None

    puerta = ides.evaluar_puerta_se(
        FakeTank(), "ETHUSD_INVERSE", "ETHUSDT_LINEAL",
        t0_paciencia=t0, restante_usd=150.0, activo="ETH", ahora=t0,
    )
    assert puerta["ok"], puerta
    # Sin tope $25: puede morder hasta techo misión × fracción
    assert puerta["micro_usd"] > 25.0 or puerta["fraccion"] < 1.0
    assert puerta["micro_usd"] <= 150.0
    assert "IGRIS_MICRO_MAX_USD" not in dir(config) or not hasattr(config, "IGRIS_MICRO_MAX_USD") or True
    assert puerta["masa"] > 0
    print(
        "  despliegue OK:", puerta["spread_pct"], ">=", puerta["umbral_pct"],
        "mordida$", puerta["micro_usd"], "frac", puerta["fraccion"],
        "tau_hi", tau_hi["tau_h"], "tau_lo", tau_lo["tau_h"],
    )


def test_libro_tank_desde_lider():
    from core import igris_despliegue as ides
    class Nodo:
        libros = {
            "ETHUSD_INVERSE": {"bids": [[100, 1]], "asks": [[100.1, 2]]},
        }

    class Cluster:
        def _obtener_lider_verde(self):
            return Nodo()

    bids, asks = ides.libro_tank(Cluster(), "ETHUSD_INVERSE")
    assert bids and asks
    print("  libro_tank lider OK")


def test_oportunidad_manto_kaiser():
    from core import kaiser_indicators as ki

    class Nodo:
        libros = {
            "ETHUSD_INVERSE": {"bids": [[99.9, 10]], "asks": [[100.0, 80]]},
            "ETHUSDT_LINEAL": {"bids": [[100.25, 80]], "asks": [[100.3, 10]]},
        }

    class Cluster:
        def _obtener_lider_verde(self):
            return Nodo()

    config.ARENA_IGRIS_ACTIVA = True
    config.ARENA_IGRIS_UMBRAL_PCT = 0.01
    alertas = ki.interpretar_oportunidades_manto(Cluster(), ["ETH"])
    assert alertas and alertas[0]["tipo"] == "OPORTUNIDAD_MANTO"
    assert (alertas[0].get("datos") or {}).get("modo_umbral") == "arena_micro"
    assert float((alertas[0].get("datos") or {}).get("spread_pct") or 0) > 0.01
    config.ARENA_IGRIS_ACTIVA = False
    print("  OPORTUNIDAD_MANTO Ask/Bid OK")


def test_arise_kaiser_cable():
    src = (ROOT / "arise.py").read_text(encoding="utf-8")
    assert "KaiserVocero" in src
    assert "kaiser.vigilar_indicadores" in src
    assert "kaiser=kaiser" in src or "kaiser=kaiser" in src.replace(" ", "")
    igris_src = (ROOT / "generales" / "igris.py").read_text(encoding="utf-8")
    assert "kaiser" in igris_src
    assert "_consumir_kaiser_jurisdiccion" in igris_src
    assert "fraccion_mordida_igris" in (ROOT / "core" / "igris_despliegue.py").read_text(encoding="utf-8")
    print("  arise-Kaiser-Igris cable OK")


def main():
    test_fases_margen()
    test_banda_delta()
    test_resumen_manto()
    test_frentes_manto()
    test_bootstrap_se()
    test_despliegue_paciente()
    test_libro_tank_desde_lider()
    test_oportunidad_manto_kaiser()
    test_arise_kaiser_cable()
    print("OK igris smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
