import asyncio
import sys
import os
import signal
import traceback

# === [PARCHE DE POSICIONAMIENTO ANDROID/WINDOWS] ===
ruta_maestra = os.path.dirname(os.path.abspath(__file__))
if ruta_maestra not in sys.path:
    sys.path.insert(0, ruta_maestra)

try:
    import core.config as config
    from generales.tusk import TuskBoveda
    from generales.greed import GreedFrancotirador
    from core.bellion import BellionAuditor
    from generales.tank import TankCluster
    from generales.beru import BeruCazador
    from generales.igris import IgrisEscudo
    from generales.kaiser import KaiserVocero
    from core.dashboard import PanelDeControl
    from core.bridge import BybitBridge
except ImportError as e:
    print(f"\n[!] ERROR DE RUTA: {e}")
    sys.exit(1)


async def refrescar_dashboard(panel):
    while True:
        panel.refrescar()
        await asyncio.sleep(1)


async def publicar_estado_vivo(bellion, tusk, beru, igris, tank, kaiser):
    await asyncio.sleep(2)
    while True:
        await bellion.publicar_estado_vivo(tusk, beru.legion, igris, tank, kaiser)
        await asyncio.sleep(1)


async def vigilancia_apagado(shutdown_event, bellion, tusk, beru):
    """3.3.1 — muerte digna: sella estado al recibir señal de apagado."""
    await shutdown_event.wait()
    await bellion.ley_de_sucesion(tusk.export_for_bellion(), beru.legion)
    await bellion.anotar("BELLION", "SUCESION", "Estado sellado — Lilit regresa a las sombras.")


def _instalar_senales_apagado(loop, shutdown_event):
    def _handler(sig, frame):
        loop.call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handler)


async def arise():
    print("\n" + "═" * 45)
    print(f"    {config.SISTEMA_NOMBRE} VIBRANDO    ")
    print(f"      FASE: {config.FASE_ACTUAL}      ")
    print("═" * 45)

    shutdown_event = asyncio.Event()
    _instalar_senales_apagado(asyncio.get_running_loop(), shutdown_event)

    try:
        api_key = getattr(config, "API_KEY", None)
        api_secret = getattr(config, "API_SECRET", None)

        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
        bridge = BybitBridge(tank, tusk, bellion, api_key, api_secret)
        binance_ref = None
        if getattr(config, "BINANCE_REF_ENABLED", True):
            from core.binance_ref import BinanceRefBridge
            binance_ref = BinanceRefBridge(tank, bellion)

        # 3.3.2 — recovery desde cristal de memoria
        estado_prev = bellion.cargar_estado()
        if estado_prev:
            tusk.restaurar_desde_bellion(estado_prev.get("boveda", {}))
            print(f"[BELLION] Recovery: bóveda restaurada.")

        beru = BeruCazador(tusk, bellion, tank, bridge=bridge, kaiser=kaiser)
        igris = IgrisEscudo(tusk, beru, bridge=bridge)
        kaiser = KaiserVocero(tank, bellion)
        greed = GreedFrancotirador(tusk, bellion, tank, bridge=bridge, kaiser=kaiser)

        if estado_prev and estado_prev.get("legion"):
            beru.restaurar_legion(estado_prev.get("legion", []))
            print(f"[BELLION] Recovery: {len(beru.legion)} barcos en legión.")

        from core.validacion import advertir_gates
        advertir_gates()

        panel = PanelDeControl(tusk, beru, igris, tank)

        print(f"\n[⚔️] Núcleo dual LTC+BTC | ref operativa: {config.TICKER_BASE} | sim={config.MODO_SIMULACION}")

        await asyncio.gather(
            tusk.latido_persistencia(beru.legion),
            tusk.hilo_reconciliacion(bridge),
            tank.vigilar_aguas(),
            bridge.conectar(),
            bridge.hilo_sentidos_extra(),
            *( [binance_ref.conectar()] if binance_ref else [] ),
            bridge.hilo_sincronizacion_nav(),
            beru.hilo_beru_berserker(),
            igris.vigilar_manto_operativo(),
            greed.vigilancia_oportunidades(),
            kaiser.vigilar_indicadores(),
            refrescar_dashboard(panel),
            publicar_estado_vivo(bellion, tusk, beru, igris, tank, kaiser),
            vigilancia_apagado(shutdown_event, bellion, tusk, beru),
        )

    except Exception:
        print(f"\n[!] ERROR CRÍTICO EN EL DESPERTAR:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(arise())
    except KeyboardInterrupt:
        print("\n[🌑] Lilit de Hierro regresa a las sombras. Sesión finalizada.")
