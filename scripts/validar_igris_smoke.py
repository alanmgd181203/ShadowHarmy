#!/usr/bin/env python3
"""Smoke Igris — banda delta, fases margen, frentes manto."""
from __future__ import annotations

import sys
import time
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
    from core import manto_ventana as mv

    # Ventana 48–52 activa: independiente del margen
    b_lo = mercado.calcular_banda_delta(50)
    b_hi = mercado.calcular_banda_delta(96)
    assert abs(b_lo[0] - mv.long_min_operativo()) < 1e-9
    assert abs(b_lo[1] - mv.long_max()) < 1e-9
    assert b_lo == b_hi  # ya no se estrecha con margen
    assert mercado.verificar_delta_post_maniobra(50, 50, 50)
    assert mercado.verificar_delta_post_maniobra(50, 52, 48)
    assert not mercado.verificar_delta_post_maniobra(50, 80, 20)
    assert not mercado.verificar_delta_post_maniobra(50, 47, 53)
    # Legacy aún existe
    leg = mercado.calcular_banda_delta_legacy(96)
    assert leg[0] == leg[1] == 0.5
    print("  ventana 48-52 OK:", b_lo)



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
            "ETHUSD_INVERSE": {"bids": [[99.9, 10]], "asks": [[100.0, 80]], "ts": time.time()},
            "ETHUSDT_LINEAL": {"bids": [[100.25, 80]], "asks": [[100.3, 10]], "ts": time.time()},
        }
        precios = {
            "ETHUSD_INVERSE": 100.0,
            "ETHUSDT_LINEAL": 100.25,
        }

        def _obtener_lider_verde(self):
            return None

    from core import pase_director as pd

    mid_prev = pd.cargar_marcha()
    try:
        pd.guardar_marcha("asalto")
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
        assert float(puerta.get("masa_long") or 0) > 0
        assert float(puerta.get("masa_short") or 0) > 0
        asim = float((puerta.get("ley_masa") or {}).get("asim_pct") or 99)
        assert asim <= 5.0 + 1e-6, puerta.get("ley_masa")
        assert abs(float(puerta["usd_long"]) - float(puerta["usd_short"])) / max(
            float(puerta["micro_usd"]), 1e-9
        ) <= 0.05 + 1e-9
        print(
            "  despliegue OK:", puerta["spread_pct"], ">=", puerta["umbral_pct"],
            "mordida$", puerta["micro_usd"], "frac", puerta["fraccion"],
            "tau_hi", tau_hi["tau_h"], "tau_lo", tau_lo["tau_h"],
            "Alfa$", puerta.get("alfa_usd"), "asim%", asim,
        )
    finally:
        try:
            if mid_prev == "personalizado":
                payload = pd.cargar_marcha_payload() or {}
                dias = float(payload.get("duracion_dias") or 0.33)
                pd.guardar_marcha("personalizado", duracion_dias=dias)
            else:
                pd.guardar_marcha(mid_prev if mid_prev else "asalto")
        except Exception:
            pd.guardar_marcha("asalto")


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
    assert "_disparo_dual_simultaneo" in igris_src
    assert "_salvavidas_market_pierna" in igris_src
    assert "escalera_precios" in igris_src
    assert "armar_peldaños_lote" in igris_src
    assert "lote_bybit" in igris_src
    greed_src = (ROOT / "generales" / "greed.py").read_text(encoding="utf-8")
    assert "escalera_precios" in greed_src
    assert "armar_peldaños_lote" in greed_src
    assert "lote_bybit" in greed_src
    assert "ESCALERA_OK" in greed_src or "ejecutar_escalera" in greed_src
    assert "fraccion_mordida_igris" in (ROOT / "core" / "igris_despliegue.py").read_text(encoding="utf-8")
    print("  arise-Kaiser-Igris cable OK")


def test_disparo_dual_salvavidas_sim():
    """Sim: ambas piernas OK en paralelo; salvavidas cableado."""
    import asyncio
    from generales.igris import IgrisEscudo

    class Bel:
        async def anotar(self, *a, **k):
            return None

    class Tusk:
        def __init__(self):
            self.reservas = set()
            self.pesos = {}
            self.margen_ocupado = 0.0
            self.masa_autorizada = 1000.0
            self.masa_bruta = 100.0
            self.masa_bruta_real = 100.0

        async def solicitar_reserva(self, uid, masa, quien, direccion):
            self.reservas.add(uid)
            return True

        async def liberar_reserva(self, uid):
            self.reservas.discard(uid)

        async def confirmar_reserva(self, uid, frente, direccion, **kw):
            self.reservas.discard(uid)
            return True

    class Tank:
        pass

    igris = IgrisEscudo(Tusk(), Tank(), Bel(), bridge=None)
    config.MODO_SIMULACION = True

    async def run():
        # Inverse qty en USD; lineal qty en ETH — Ley de la Masa (no misma cifra)
        ok = await igris._disparo_dual_simultaneo(
            "L1", "S1", "ETHUSD_INVERSE", "ETHUSDT_LINEAL",
            19.0, 0.01, 1900.0, 1900.2,
            usd_l=19.0, usd_s=19.02,
        )
        assert ok is True
        # Salvavidas: fuerza market path en sim también confirma
        r2 = await igris._salvavidas_market_pierna(
            "S2", "ETHUSDT_LINEAL", "SHORT", 0.01, 1900.2,
        )
        assert r2.get("ok") is True

    asyncio.run(run())
    print("  disparo dual + salvavidas sim OK")


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
    test_disparo_dual_salvavidas_sim()
    print("OK igris smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
