import asyncio
import sys
import os
import signal
import traceback

# === [PARCHE DE POSICIONAMIENTO ANDROID/WINDOWS] ===
ruta_maestra = os.path.dirname(os.path.abspath(__file__))
if ruta_maestra not in sys.path:
    sys.path.insert(0, ruta_maestra)

# === [SUBTEMA: IMPORTACIONES ESTRUCTURALES] ===
try:
    import core.config as config
    from generales.tusk import TuskBoveda
    from generales.greed import GreedFrancotirador
    from core.bellion import BellionAuditor      
    from generales.tank import TankCluster      
    from generales.beru import BeruCazador
    from generales.igris import IgrisEscudo
    from core.dashboard import PanelDeControl
    from core.bridge import BybitBridge
except ImportError as e:
    print(f"\n[!] ERROR DE RUTA: {e}")
    sys.exit(1)

# === [SUBTEMA: PROYECCIÓN] ===
async def refrescar_dashboard(panel):
    """Mantiene viva la interfaz sin bloquear el resto del bot."""
    while True:
        panel.refrescar()
        await asyncio.sleep(1)

async def publicar_estado_vivo(bellion, tusk, beru, igris):
    """Publica snapshot para el panel Streamlit cada segundo."""
    await asyncio.sleep(2)
    while True:
        await bellion.publicar_estado_vivo(tusk, beru.legion, igris)
        await asyncio.sleep(1)

# === [SUBTEMA: ORQUESTACIÓN DEL DESPERTAR] ===
async def arise():
    print("\n" + "═"*45)
    print(f"    {config.SISTEMA_NOMBRE} VIBRANDO    ")
    print(f"      FASE: {config.FASE_ACTUAL}      ")
    print("═"*45)
    
    try:
        # 🛡️ 0. CREDENCIALES (Asegúrate de que existan en config o cámbialas aquí)
        # Puedes agregarlas a core/config.py como API_KEY y API_SECRET
        api_key = getattr(config, 'API_KEY', None) 
        api_secret = getattr(config, 'API_SECRET', None)

        # 1. Instanciamos a los generales
        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion, ticker_base="LTC")
        
        # ⛓️ CONEXIÓN DE HIERRO: El puente ahora recibe todo el equipo y las llaves
        bridge = BybitBridge(tank, tusk, bellion, api_key, api_secret) 

        greed = GreedFrancotirador(tusk, bellion, tank, bridge=bridge)
        beru = BeruCazador(tusk, greed, bellion, tank)
        igris = IgrisEscudo(tusk, beru)
        panel = PanelDeControl(tusk, beru, igris)
        
        print(f"\n[⚔️] Núcleo de Hierro templado. Iniciando Invasión Dinámica...")

        # 2. Lanzamos el enjambre en paralelo
        # Hemos añadido 'bridge.hilo_sincronizacion_nav()' al gather
        await asyncio.gather(
            tusk.latido_persistencia(beru.legion), 
            tusk.hilo_reconciliacion(bridge),
            tank.vigilar_aguas(),                  
            bridge.conectar(),
            bridge.hilo_sincronizacion_nav(),
            beru.hilo_beru_berserker(),            
            igris.vigilar_manto_operativo(),       
            greed.arbitrar(),                      
            refrescar_dashboard(panel),
            publicar_estado_vivo(bellion, tusk, beru, igris),
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