#!/usr/bin/env python3
"""
Ciclo integrado Beru — ETH referencia, simulación local (sin exchange).

Escenarios:
  A) Capa 1 SHORT → engorde frontera → cosecha Hoz → red_residual → clon Capa 2
  B) Fusión por colisión oz_adan (dos negociadores ETH)
  C) Mega Beru intacto (ESPERANDO_CONDICIONAL)

Uso: python scripts/validar_ciclo_beru_eth.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import core.config as config  # noqa: E402
from core import mercado as mercado_mod  # noqa: E402
from core import beru_cazador  # noqa: E402
from core.models import MarketContext, BeruShip  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402
from generales.beru import BeruCazador  # noqa: E402
from generales.capitanes import CapitanNormal  # noqa: E402


# --- ETH referencia Monarca ---
ETH_CENTRO = 3500.0
ETH_GATILLO_PCT = 0.008  # +0.8% Normal
ETH_PRECIO_GATILLO = ETH_CENTRO * (1.0 + ETH_GATILLO_PCT)  # 3528


class TankEthMock:
    """Tank mínimo — precio ETH configurable por paso."""

    def __init__(self, precio: float = ETH_CENTRO):
        self.precio = precio
        self.capitan_activo = CapitanNormal
        self._modo_cosecha = False
        self.libros: dict = {}

    def _obtener_lider_verde(self):
        return type("NodoVerde", (), {"estado_foco": "VERDE", "latencia_ms": 50.0, "libros": {}})()

    def set_precio(self, p: float) -> None:
        self.precio = p

    def modo_cosecha(self, activo: bool = True) -> None:
        self._modo_cosecha = activo

    async def vision_especulativa(self):
        ahora = time.time() * 1000
        p = self.precio * (1.015 if self._modo_cosecha else 1.0)
        ctx_map = {}
        for f in config.FRENTES_CASA:
            sym, mtype = f.split("_")
            ctx_map[f] = MarketContext(
                symbol=sym, market_type=mtype,
                last_price=p, spread=0.01,
                depth_ask=500_000.0, depth_bid=500_000.0,
                volatilidad=0.005, timestamp=ahora, local_arrival=ahora,
                muro_ask_volumen=500_000.0, muro_bid_volumen=500_000.0,
            )
        return ctx_map, "VERDE_SEGURO"


def _setup_eth_env() -> None:
    config.MODO_SIMULACION = True
    config.TICKER_BASE = "ETH"
    config.FRENTES_CASA = ["ETHUSDT_SPOT", "ETHUSDC_SPOT"]
    config.FRENTE_PRINCIPAL = "ETHUSDT_LINEAL"
    config.BERU_MODO_COMBATE_DEFAULT = "CAZA"
    config.BERU_TIER_DEFAULT = "PROTO1"
    mercado_mod.verificar_delta_frente = lambda *a, **k: True


def _setup_tusk_manto(tusk: TuskBoveda) -> None:
    tusk.masa_autorizada = 200.0
    tusk.margen_ocupado = 100.0
    tusk.precio_spot = ETH_CENTRO
    tusk.ultimo_precio = ETH_CENTRO
    tusk.pesos = {
        "ETHUSDT_LINEAL": {
            "long": 0.0, "short": 0.0,
            "precio_medio_long": ETH_CENTRO,
            "precio_medio_short": ETH_CENTRO,
        },
    }
    tusk.tier_beru_aplicado = "PROTO1"


async def escenario_a_clonacion_residual(beru: BeruCazador, tank: TankEthMock) -> dict:
    """Capa 1 → engorde → cosecha → red_residual → Capa 2 $5."""
    resultados: dict = {"nombre": "A_clonacion_residual", "ok": False, "pasos": []}

    beru.plantar_semilla_adan(ETH_CENTRO)
    semilla = beru.legion[0]
    semilla.modo_combate = "CAZA"

    # Gatillo SHORT +0.8%
    tank.set_precio(ETH_PRECIO_GATILLO)
    await beru.auditar_gatillos_adan(ETH_PRECIO_GATILLO)
    capa1 = next((b for b in beru.legion if b.capa == 1 and b.estado == "NEGOCIANDO"), None)
    if not capa1:
        resultados["error"] = "Capa 1 no materializó tras gatillo ETH +0.8%"
        return resultados
    await beru.sincronizar_materializacion()
    resultados["pasos"].append(
        f"Capa1 SHORT @ {ETH_PRECIO_GATILLO:.2f} masa=${capa1.masa:.0f} "
        f"oz={capa1.oz_adan:.2f} red={capa1.red_adan:.2f}"
    )

    # Engorde frontera — toque red
    tank.set_precio(capa1.red_adan + 1.0)
    await beru.ejecutar_acordeon_asimetrico(capa1.red_adan + 1.0)
    masa_tras_engorde = capa1.masa
    resultados["pasos"].append(
        f"Engorde frontera red {capa1.red_adan:.2f} -> masa ${masa_tras_engorde:.0f}"
    )

    n_residuales_antes = len(beru._redes_residuales)
    red_para_clon = capa1.red_adan

    # Cosecha Hoz (beneficio simulado)
    umbral_prev = config.UMBRAL_COSECHA_MIN
    config.UMBRAL_COSECHA_MIN = 0.001
    tank.modo_cosecha(True)
    tank.set_precio(capa1.oz_adan - 5.0)
    await beru.ejecutar_acordeon_asimetrico(capa1.oz_adan - 5.0)
    tank.modo_cosecha(False)
    config.UMBRAL_COSECHA_MIN = umbral_prev

    negociadores = [b for b in beru.legion if getattr(b, "ciclo_infinito", False)]
    residuales = [r for r in beru._redes_residuales if r.activa]
    resultados["pasos"].append(
        f"Cosecha oz {capa1.oz_adan:.2f} -> neg={len(negociadores)} "
        f"red_residual={len(residuales)} @ {red_para_clon:.2f}"
    )

    if not residuales:
        resultados["error"] = "No se registró red_residual tras cosecha"
        return resultados

    red_res = residuales[-1].precio

    # Clon Capa 2 — toque red_residual
    tank.set_precio(red_res + 0.5)
    await beru.ejecutar_acordeon_asimetrico(red_res + 0.5)

    capa2 = next((b for b in beru.legion if b.capa >= 2 and b.estado == "NEGOCIANDO"), None)
    if not capa2:
        capa2 = next(
            (b for b in beru.legion if b.masa == beru_cazador.mordida_usd() and b.estado == "NEGOCIANDO" and b.modo_combate == "CAZA"),
            None,
        )
    if not capa2:
        resultados["error"] = f"Capa 2 no nació al tocar red_residual {red_res:.2f}"
        return resultados

    resultados["pasos"].append(
        f"Clon Capa{capa2.capa} @ red_residual {red_res:.2f} masa=${capa2.masa:.0f}"
    )
    resultados["ok"] = (
        len(negociadores) >= 1
        and capa2.masa == beru_cazador.mordida_usd()
        and len(residuales) > n_residuales_antes
    )
    return resultados


async def escenario_b_fusion_colision(beru: BeruCazador) -> dict:
    """Dos negociadores con misma Hoz → fusión $70."""
    from core import beru_negociador
    from generales.capitanes import CapitanNormal

    resultados: dict = {"nombre": "B_fusion_colision", "ok": False, "pasos": []}
    centro = ETH_CENTRO
    vacio = CapitanNormal.vacio_adan
    ancla_a, ancla_b = 0.01, 0.012
    paso_oz = 0.001
    cond_a = beru_negociador.oz_condicional_pct(ancla_a, vacio)
    oz_a, red_a = beru_negociador.activar_primera_vez(cond_a, paso_oz)
    cond_b = beru_negociador.oz_condicional_pct(ancla_b, vacio)
    oz_b, red_b = beru_negociador.activar_primera_vez(cond_b, paso_oz)
    oz_p = beru_cazador.precio_desde_pct(centro, oz_a)

    def _neg(uid: str, ancla: float, oz_pct: float, red_pct: float) -> BeruShip:
        return BeruShip(
            uid=uid, centro_local=centro, centro_manto=centro,
            masa=35.0, masa_congelada=35.0, direccion="SHORT",
            estado="NEGOCIANDO", modo_combate="NEGOCIADOR",
            ciclo_infinito=True, ancla_cosecha_pct=ancla,
            neg_oz_pct=oz_pct, neg_red_pct=red_pct,
            oz_adan=oz_p, adn_capitan=CapitanNormal, tier_id="PROTO1",
        )

    b1 = _neg("ETH_NEG_A", ancla_a, oz_a, red_a)
    b2 = _neg("ETH_NEG_B", ancla_b, oz_b, red_b)
    beru.legion.extend([b1, b2])

    await beru.evaluar_colisiones_y_fusion()

    activos = [b for b in beru.legion if b.estado == "NEGOCIANDO" and b.modo_combate == "NEGOCIADOR"]
    fusionados = [b for b in beru.legion if b.estado == "FUSIONADO"]
    resultados["pasos"].append(f"Activos={len(activos)} fusionados={len(fusionados)}")

    if len(activos) == 1 and activos[0].masa_congelada == 70.0:
        resultados["ok"] = True
        resultados["pasos"].append(f"Líder {activos[0].uid} masa=${activos[0].masa_congelada:.0f}")
    else:
        resultados["error"] = "Fusión colisión no consolidó a un solo Beru $70"
    return resultados


async def escenario_c_mega_beru() -> dict:
    """Mega Beru en ESPERANDO_CONDICIONAL — lógica sagrada intacta."""
    from core import beru_fusion
    from generales.capitanes import CapitanNormal

    resultados: dict = {"nombre": "C_mega_beru", "ok": False, "pasos": []}
    anclas = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10]
    barcos = []
    for i, a in enumerate(anclas):
        barcos.append(BeruShip(
            uid=f"ETH_MEGA_{i}", centro_local=ETH_CENTRO, centro_manto=ETH_CENTRO,
            masa=35.0, masa_congelada=35.0, direccion="SHORT",
            estado="ESPERANDO_CONDICIONAL", modo_combate="NEGOCIADOR",
            ciclo_infinito=True, ancla_cosecha_pct=a,
            adn_capitan=CapitanNormal, tier_id="PROTO1",
        ))

    grupos = beru_fusion.grupos_mega_beru(barcos)
    if len(grupos) != 1:
        resultados["error"] = f"Esperaba 1 grupo Mega, got {len(grupos)}"
        return resultados

    lider, victimas, prom = grupos[0]
    beru_fusion.aplicar_mega_beru(lider, victimas, prom, CapitanNormal.vacio_adan)
    resultados["pasos"].append(
        f"Mega {lider.uid} prom={prom*100:.2f}% masa=${lider.masa_congelada:.0f} "
        f"super={lider.es_super_beru}"
    )
    resultados["ok"] = (
        lider.es_super_beru
        and lider.masa_congelada == 35.0 * 3
        and lider.estado == "ESPERANDO_CONDICIONAL"
    )
    return resultados


async def escenario_d_engorde_no_frontera(beru: BeruCazador, tank: TankEthMock) -> dict:
    """Beru intermedio no engorda; solo el de red extrema."""
    resultados: dict = {"nombre": "D_engorde_frontera", "ok": False, "pasos": []}
    from generales.capitanes import CapitanNormal

    centro = ETH_CENTRO
    b_frente = BeruShip(
        uid="ETH_FRON", centro_local=centro, centro_manto=centro,
        masa=10.0, direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA",
        oz_adan=3524.0, red_adan=3540.0, oz_pct=0.007, red_pct=0.011,
        capa=1, adn_capitan=CapitanNormal, tier_id="PROTO1",
        precio_entrada_real=3528.0, sincronizado=True,
    )
    b_inter = BeruShip(
        uid="ETH_INTER", centro_local=centro, centro_manto=centro,
        masa=5.0, direccion="SHORT", estado="NEGOCIANDO", modo_combate="CAZA",
        oz_adan=3520.0, red_adan=3530.0, oz_pct=0.006, red_pct=0.009,
        capa=2, adn_capitan=CapitanNormal, tier_id="PROTO1",
        precio_entrada_real=3525.0, sincronizado=True,
    )
    beru.legion.extend([b_frente, b_inter])
    masa_inter_antes = b_inter.masa

    tank.set_precio(3530.5)
    await beru.ejecutar_acordeon_asimetrico(3530.5)

    if b_inter.masa != masa_inter_antes:
        resultados["error"] = f"Intermedio engordó (${b_inter.masa}) — debía quedar en ${masa_inter_antes}"
        return resultados

    resultados["pasos"].append(f"Intermedio sin engorde @ red {b_inter.red_adan:.2f} OK")
    resultados["ok"] = True
    return resultados


async def main() -> int:
    _setup_eth_env()
    print(f"\n=== CICLO BERU ETH (sim) | centro={ETH_CENTRO} | tier=PROTO1/General ===\n")

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    _setup_tusk_manto(tusk)
    tank = TankEthMock(ETH_CENTRO)

    escenarios = []

    beru_a = BeruCazador(tusk, bellion, tank, bridge=None)
    escenarios.append(await escenario_a_clonacion_residual(beru_a, tank))

    beru_b = BeruCazador(tusk, bellion, tank, bridge=None)
    escenarios.append(await escenario_b_fusion_colision(beru_b))

    escenarios.append(await escenario_c_mega_beru())

    beru_d = BeruCazador(tusk, bellion, tank, bridge=None)
    escenarios.append(await escenario_d_engorde_no_frontera(beru_d, tank))

    todo_ok = True
    for e in escenarios:
        tag = "OK" if e.get("ok") else "FAIL"
        print(f"  [{tag}] {e['nombre']}")
        for p in e.get("pasos", []):
            print(f"       · {p}")
        if e.get("error"):
            print(f"       ! {e['error']}")
            todo_ok = False
        elif not e.get("ok"):
            todo_ok = False

    reporte = {
        "ts": time.time(),
        "activo": "ETH",
        "centro_usd": ETH_CENTRO,
        "tier": "PROTO1",
        "ok": todo_ok,
        "escenarios": escenarios,
    }
    ruta = os.path.join(ROOT, "data", "validacion_ciclo_beru_eth.json")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)

    print(f"\nResultado global: {'OK' if todo_ok else 'FAIL'}")
    print(f"Reporte: {ruta}\n")
    return 0 if todo_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
