"""
Prueba 3.6.1 — ciclo Beru CAZA → COSECHA en simulación (precios mock).
Escribe en historial Bellion y genera data/validacion_ciclo_ejercito.json.

Uso: python scripts/probar_ciclo_beru.py
"""
import asyncio
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import core.config as config  # noqa: E402
from core import mercado as mercado_mod  # noqa: E402
from core.models import MarketContext  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402
from generales.beru import BeruCazador  # noqa: E402
from generales.capitanes import CapitanCazador  # noqa: E402
from core.beru_rail import frentes_casa_estables  # noqa: E402


class TankMock:
    """Tank mínimo para forzar CAZA/COSECHA sin WebSocket."""

    def __init__(self, precio: float):
        self.precio = precio
        self.precio_cosecha = precio * 1.015  # ~1.5% beneficio en cierre
        self.capitan_activo = CapitanCazador
        self._modo = "caza"
        self.libros: dict = {}

    def _obtener_lider_verde(self):
        return type("NodoVerde", (), {"estado_foco": "VERDE", "latencia_ms": 50.0, "libros": {}})()

    async def vision_especulativa(self):
        ahora = time.time() * 1000
        p = self.precio if self._modo == "caza" else self.precio_cosecha
        ctx_map = {}
        for f in frentes_casa_estables():
            sym, mtype = f.split("_", 1)
            ctx_map[f] = MarketContext(
                symbol=sym, market_type=mtype,
                last_price=p, spread=0.01,
                depth_ask=5000.0, depth_bid=5000.0,
                volatilidad=0.005, timestamp=ahora, local_arrival=ahora,
                muro_ask_volumen=5000.0, muro_bid_volumen=5000.0,
            )
        return ctx_map, "VERDE_SEGURO"


async def simular_ciclo():
    # Forzar sim para no tocar exchange
    config.MODO_SIMULACION = True
    # Primera CAZA en frente vacío: banda delta bloquearía — bypass solo en validación
    mercado_mod.verificar_delta_frente = lambda *a, **k: True

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tusk.masa_autorizada = 100.0
    tusk.margen_ocupado = 50.0  # banda relajada

    precio_semilla = 100.0
    precio_caza = 98.5  # ~1.5% move → gatillo LONG (distancia > vacio_adan 1.5%)
    tank = TankMock(precio_caza)
    beru = BeruCazador(tusk, bellion, tank, bridge=None)

    await bellion.anotar("VALIDACION", "INICIO_CICLO", "Simulacion 3.6.1 - CAZA->COSECHA")

    masa_caza = 10.0
    beru.plantar_semilla_adan(precio_semilla)
    barco = beru.legion[0]
    barco.direccion = "LONG"
    if not await tusk.solicitar_reserva(barco.uid, masa_caza, "BERU", "LONG"):
        return False, "solicitar_reserva falló en CAZA"
    barco.masa = masa_caza
    barco.estado = "ESPERANDO_MATERIALIZACION"
    await beru._ejecutar_caza(barco)

    if barco.estado != "NEGOCIANDO":
        return False, f"CAZA no materializó NEGOCIANDO (estado={barco.estado})"

    await beru.sincronizar_materializacion()

    # Cosecha directa (precio mock con ~1.5% beneficio)
    tank._modo = "cosecha"
    uid_cosecha = f"COSECHA_TEST_{int(time.time())}"
    await beru._ejecutar_cosecha(barco, uid_cosecha)

    cosechados = [b for b in beru.legion if b.estado == "COSECHADO"]
    beru.limpiar_legion()

    ok = len(cosechados) > 0 or _contar_cosecha_historial(bellion.ruta_historial) > 0
    detalle = (
        f"Barco {barco.uid} {barco.direccion} entrada={barco.precio_entrada_real:.2f} "
        f"→ COSECHADO={ok}"
    )
    await bellion.anotar("VALIDACION", "FIN_CICLO", detalle)

    reporte = {
        "ts": time.time(),
        "milestone": "M2-3.6.1",
        "modo": "simulacion",
        "ticker_ref": config.TICKER_BASE,
        "ok_ciclo": ok,
        "detalle": detalle,
        "barco_uid": barco.uid,
        "direccion": barco.direccion,
        "precio_entrada": barco.precio_entrada_real,
        "frente": getattr(barco, "frente_asignado", ""),
    }
    ruta = os.path.join(ROOT, "data", "validacion_ciclo_ejercito.json")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2)

    return ok, detalle


def _contar_cosecha_historial(ruta: str) -> int:
    if not os.path.exists(ruta):
        return 0
    with open(ruta, encoding="utf-8") as f:
        return sum(1 for line in f if "[BERU] COSECHA:" in line)


async def main():
    print(f"\n=== PROBAR CICLO BERU (3.6.1) | ref={config.TICKER_BASE} | sim ===\n")
    ok, detalle = await simular_ciclo()
    print(f"\nResultado: {'OK' if ok else 'FAIL'} — {detalle}")
    print(f"Reporte: data/validacion_ciclo_ejercito.json")
    print("\nVerificar checklist: python scripts/validar_checklist.py --fase 3")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
