import asyncio
import time
from collections import deque

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
from core.models import MarketContext
from generales.capitanes import CapitanAnsiedad, CapitanCazador, CapitanBerserker
import core.config as config  # Fuente única de sensibilidad

# === [SUBTEMA: LA HIDRA (NODOS DE PERCEPCIÓN)] ===

class TankNode:
    """Cabeza de la Hidra adaptada para la realidad."""
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.estado_foco = "ROJO"
        self.latencia_ms = 999.0
        self.jitter_ms = 0.0  # Sensor de turbulencia real
        self.ultima_actualizacion = time.time() 
        
        # Precios de los 5 Mares de LTC
        self.p_usdt_lineal = self.p_usdc_lineal = self.p_inverse = 0.0
        self.p_usdt_spot = self.p_usdc_spot = 0.0
        
        # Muros de Liquidez (Se llenarán con datos reales)
        self.muros = {f: {"ask": 0.0, "bid": 0.0} for f in [
            "LTCUSDT_LINEAL", "LTCUSDC_LINEAL", "LTCUSD_INVERSE", "LTCUSDT_SPOT", "LTCUSDC_SPOT"
        ]}

    def inyectar_verdad_real(self, f_key: str, price: float, latency: float):
        """Inyecta datos reales del flujo de Bybit."""
        ahora = time.time()
        # Calculamos la estabilidad de la señal en Zacatecas
        delta = abs(latency - self.latencia_ms)
        self.jitter_ms = (self.jitter_ms * 0.8) + (delta * 0.2)
        
        self.latencia_ms, self.ultima_actualizacion = latency, ahora

        if f_key == "LTCUSDT_LINEAL": self.p_usdt_lineal = price
        elif f_key == "LTCUSDC_LINEAL": self.p_usdc_lineal = price
        elif f_key == "LTCUSD_INVERSE": self.p_inverse = price
        elif f_key == "LTCUSDT_SPOT": self.p_usdt_spot = price
        elif f_key == "LTCUSDC_SPOT": self.p_usdc_spot = price


class TankCluster:
    def __init__(self, tusk, bellion, ticker_base="LTC"):
        self.tusk, self.bel, self.ticker_base = tusk, bellion, ticker_base
        self.nodos = [TankNode(i) for i in range(1, 5)]
        self.historial_precios = deque(maxlen=30) 
        self.capitan_activo = CapitanCazador 
        self.tsunami_activado = False

    # === [SUBTEMA: BUCLE MAESTRO (VIGILANCIA DE AGUAS)] ===

    async def vigilar_aguas(self):
        """Proyecta la Verdad en la Bóveda en tiempo real."""
        print(f"[TANK] Hidra acechando el Pentiverso ({config.FASE_ACTUAL}).")
        while True:
            self._auditar_semaforos()
            lider = self._obtener_lider_verde()
            if lider and lider.p_usdt_lineal > 0:
                await self.tusk.actualizar_precios(lider.p_usdt_lineal, lider.p_usdt_spot, lider.p_inverse)
                ahora = time.time()
                self.historial_precios.append((ahora, lider.p_usdt_lineal))
                while self.historial_precios and (ahora - self.historial_precios[0][0]) > 30:
                    self.historial_precios.popleft()
                await self.evaluar_clima()
            await asyncio.sleep(0.5) 

    # === [SUBTEMA: CONTROL DE CLIMA E INERCIA] ===

    async def evaluar_clima(self):
        """Determina qué Capitán toma el timón según la volatilidad."""
        if len(self.historial_precios) < 10: return
        p_ini, p_fin = self.historial_precios[0][1], self.historial_precios[-1][1]
        inercia = abs(p_fin - p_ini) / max(p_ini, 1.0)

        if inercia >= 0.02:
            if not self.tsunami_activado:
                self.capitan_activo, self.tsunami_activado = CapitanBerserker, True
                await self.bel.anotar("TANK", "ALERTA", f"¡TSUNAMI! {inercia*100:.2f}%.")
        elif inercia <= 0.001:
            if self.capitan_activo != CapitanAnsiedad:
                self.capitan_activo, self.tsunami_activado = CapitanAnsiedad, False
                await self.bel.anotar("TANK", "CLIMA", "Aguas estancadas.")
        else:
            if self.tsunami_activado and inercia > 0.005: return 
            if self.capitan_activo != CapitanCazador:
                self.capitan_activo, self.tsunami_activado = CapitanCazador, False
                await self.bel.anotar("TANK", "CLIMA", "Aguas normales.")


# === [SUBTEMA: LIDERAZGO Y SEMÁFOROS] ===

    def _auditar_semaforos(self):
        """Auditoría adaptada a la latencia del estanque real."""
        ahora = time.time()
        for nodo in self.nodos:
            # Compara el tiempo actual contra la última actualización recibida
            if (ahora - nodo.ultima_actualizacion) > config.TOLERANCIA_COMA_S:
                nodo.estado_foco, nodo.latencia_ms = "CONGELADO", 999.0
                continue
            
            # Semáforo de salud según la configuración de config.py
            if nodo.latencia_ms <= config.UMBRAL_VERDE_MS: 
                nodo.estado_foco = "VERDE"
            elif nodo.latencia_ms <= config.UMBRAL_AMARILLO_MS: 
                nodo.estado_foco = "AMARILLO"
            else: 
                nodo.estado_foco = "ROJO"

    def _obtener_lider_verde(self):
        """Busca al nodo con la verdad más fresca y rápida."""
        verdes = [n for n in self.nodos if n.estado_foco == "VERDE"]
        if verdes: return min(verdes, key=lambda n: n.latencia_ms)
        amarillos = [n for n in self.nodos if n.estado_foco == "AMARILLO"]
        return min(amarillos, key=lambda n: n.latencia_ms) if amarillos else None

    # === [SUBTEMA: VISIÓN ESPECULATIVA Y BIZANTINA] ===

    async def vision_especulativa(self):
        """Entrega el mapa de los 5 mares con auditoría bizantina."""
        lider = self._obtener_lider_verde()
        if not lider: return None, "ROJO"
        ahora_ms = time.time() * 1000
        frentes = {"LTCUSDT_LINEAL": lider.p_usdt_lineal, "LTCUSDC_LINEAL": lider.p_usdc_lineal, 
                   "LTCUSD_INVERSE": lider.p_inverse, "LTCUSDT_SPOT": lider.p_usdt_spot, 
                   "LTCUSDC_SPOT": lider.p_usdc_spot}
        ctx_map = {f: MarketContext(symbol=f.split("_")[0], market_type=f.split("_")[1], 
                   last_price=p, spread=0.01, depth_ask=lider.muros[f]["ask"], depth_bid=lider.muros[f]["bid"], 
                   volatilidad=0.005, timestamp=ahora_ms, local_arrival=ahora_ms, 
                   muro_ask_volumen=lider.muros[f]["ask"], muro_bid_volumen=lider.muros[f]["bid"]) 
                   for f, p in frentes.items()}

        # Auditoría Bizantina contra Glitches
        auditores = [n for n in self.nodos if n.estado_foco in ["VERDE", "AMARILLO"] and n.node_id != lider.node_id]
        estado_consenso = "VERDE_SEGURO"
        for auditor in auditores:
            if abs(lider.p_usdt_lineal - auditor.p_usdt_lineal) / max(lider.p_usdt_lineal, 1.0) > config.TOLERANCIA_GLITCH:
                estado_consenso, lider.latencia_ms = "GLITCH_DETECTADO", lider.latencia_ms + 500.0
                break
        return ctx_map, estado_consenso
