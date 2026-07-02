import asyncio
import json
import time
import ssl
import websockets
from pybit.unified_trading import HTTP
import core.config as config 

# === [EL PUENTE DE LA HIDRA: VISIÓN HÍBRIDA] ===

class BybitBridge:
    def __init__(self, tank_cluster, tusk, bellion, api_key=None, api_secret=None):
        self.tank = tank_cluster
        self.tusk = tusk
        self.bel = bellion
        
        # 🌐 COBRE: Ojos en la Realidad (Mainnet)
        # Esto garantiza que los nodos siempre estén en VERDE y con precios reales.
        self.url = "wss://stream.bybit.com/v5/public/linear"
            
        self.symbols = ["LTCUSDT"]
        self.session = None
        
        if api_key and api_secret:
            # 🛡️ Las Manos se quedan en la simulación (Testnet)
            self.session = HTTP(
                testnet=config.TESTNET, 
                api_key=api_key, 
                api_secret=api_secret
            )

    async def conectar(self):
        """Mantiene la conexión WebSocket activa con la Mainnet."""
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        while True:
            try:
                # ping_interval=20 evita que el servidor nos desconecte por inactividad
                async with websockets.connect(self.url, ssl=ssl_context, ping_interval=20) as websocket:
                    sub_msg = json.dumps({"op": "subscribe", "args": [f"tickers.{s}" for s in self.symbols]})
                    await websocket.send(sub_msg)
                    
                    async for message in websocket:
                        data = json.loads(message)
                        if "data" in data: 
                            await self._procesar_latido(data)
                        elif "ret_msg" in data or "op" in data:
                            # Mantenemos viva la marca de tiempo de los nodos
                            for nodo in self.tank.nodos:
                                nodo.ultima_actualizacion = time.time()

            except Exception as e:
                await self.bel.anotar("BRIDGE", "RECONEXIÓN", f"Error de red: {str(e)}")
                await asyncio.sleep(5)

    async def _procesar_latido(self, payload):
        """Distribuye el precio real de Mainnet a todos los nodos del Tank."""
        ticker = payload.get("data", {})
        precio_raw = ticker.get("lastPrice")
        
        if not precio_raw:
            return 

        precio = float(precio_raw)
        ts_server = int(payload.get("ts", time.time() * 1000))
        # Latencia real entre Fresnillo y los servidores de Bybit
        latencia_local = abs((time.time() * 1000) - ts_server)

        for nodo in self.tank.nodos:
            nodo.ultima_actualizacion = time.time()
            nodo.latencia_ms = latencia_local
            nodo.p_usdt_lineal = precio 

    async def hilo_sincronizacion_nav(self):
        """Sincroniza el balance y calcula el Oxígeno real de la cuenta."""
        if not self.session: return
        
        while True:
            try:
                response = self.session.get_wallet_balance(accountType="UNIFIED")
                if response['retCode'] == 0:
                    data = response['result']['list'][0]
                    nav_total = float(data.get('totalEquity', 0.0))
                    disponible = float(data.get('totalAvailableBalance', 0.0))
                    
                    # Cálculo de Oxígeno: Capital comprometido vs Capital total
                    margen_ocupado = ((nav_total - disponible) / nav_total * 100) if nav_total > 0 else 0.0
                    await self.tusk.actualizar_nav_real(nav_total, margen_ocupado)
            except:
                pass
                
            await asyncio.sleep(30)