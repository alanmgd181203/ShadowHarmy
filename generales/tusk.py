import asyncio
import time
import json
import os
import core.config as config 

class TuskBoveda:
    def __init__(self, bellion):
        """
        Tusk: El Tesorero de Hierro. 
        Gestiona el capital, las sombras (Berus) y la persistencia atómica.
        """
        self.bel = bellion 
        self._lock = asyncio.Lock()
        
        # 🛡️ RUTA DE PERSISTENCIA
        ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ruta_data = os.path.join(ruta_base, "data", "tusk_data.json")

        # Visión de Precios
        self.precio_perp = self.precio_spot = self.precio_inverse = self.ultimo_precio = 0.0    
        
        # 🟢 MUELLES DINÁMICOS: Se llenan al vuelo según la moneda que cace Beru
        self.pesos = {} 

        # 💉 MASA OPERATIVA (Inicialmente simulada, lista para NAV Real)
        self.masa_bruta = 100.0         # Para visualización en Dashboard
        self.masa_bruta_real = 100.0    # Capital total bajo gestión
        self.margen_ocupado = 0.0       # % de uso en Bybit
        self.masa_autorizada = 100.0    # Energía disponible para nuevas sombras
        
        self.masa_reservada_ltc = 0.0   # Masa en tránsito (no confirmada aún)
        self.referencia_escalon = 0.0   # Nivel de potencia actual
        self.reservas_activas = {}      # Registro de soldados (Sombras) en combate
        
        self.total_ciclos_consumados = 0
        self._verificar_infraestructura()

    # === [SUBTEMA: INFRAESTRUCTURA Y PERSISTENCIA] ===

    def _verificar_infraestructura(self):
        """Asegura que el cofre de datos exista."""
        os.makedirs(os.path.dirname(self.ruta_data), exist_ok=True)
        if not os.path.exists(self.ruta_data):
            with open(self.ruta_data, "w") as f:
                json.dump({"total_ciclos_consumados": 0, "reservas": {}}, f)

    async def latido_persistencia(self, legion):
        """Guarda el estado cada 10s con blindaje contra corrupciones."""
        while True:
            try:
                data = {
                    "total_ciclos_consumados": self.total_ciclos_consumados,
                    "reservas": {}
                }
                if legion:
                    for barco in legion:
                        if hasattr(barco, '__dict__'):
                            data["reservas"][barco.uid] = vars(barco)
                
                # Sellado atómico: escribe en temporal y luego renombra
                ruta_temp = self.ruta_data + ".tmp"
                with open(ruta_temp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                
                if os.path.exists(ruta_temp):
                    if os.path.exists(self.ruta_data): os.remove(self.ruta_data)
                    os.rename(ruta_temp, self.ruta_data)
            except Exception:
                pass # Silenciado para no manchar la consola de la terminal
            await asyncio.sleep(10)

# === [SUBTEMA: GESTIÓN DE CAPITAL Y PRECIOS] ===

    async def actualizar_precios(self, p_perp, p_spot, p_inv):
        """Inyecta la verdad de los precios desde Tank."""
        async with self._lock:
            self.precio_perp, self.precio_spot, self.precio_inverse = p_perp, p_spot, p_inv
            self.ultimo_precio = p_perp 

    async def actualizar_nav_real(self, balance_total: float, margen_real: float):
        """
        Inyecta el balance real desde Bybit. 
        Actualiza la masa bruta y recalcula el oxígeno disponible.
        """
        async with self._lock:
            # 1. Seteamos la realidad: lo que dice Bybit que tenemos
            self.masa_bruta = balance_total
            self.masa_bruta_real = balance_total
            self.margen_ocupado = margen_real
            
            # 2. Recalculamos la potencia de disparo basada en la realidad del capital
            base = config.ESCALON_POTENCIA_BASE
            factor_seguro = max(config.FACTOR_MASA_AUTORIZADA, 0.001)
            
            # 🛡️ CÁLCULO DE HIERRO: El escalón se basa en el margen libre real
            self.referencia_escalon = (margen_real // base) * base
            self.masa_autorizada = self.referencia_escalon / factor_seguro
            
            # 3. Registro en Bellion para auditoría (solo cada 50 eventos para no saturar)
            if self.total_ciclos_consumados % 50 == 0:
                await self.bel.anotar("TUSK", "NAV_SYNC", f"Capital: {balance_total:.2f} | Oxígeno: {self.masa_autorizada:.2f}%")

    async def auditar_escalones_universales(self, margen_real: float):
        """Ajuste rápido de potencia si el margen fluctúa sin cambio de balance total."""
        async with self._lock:
            self.margen_ocupado = margen_real
            base = config.ESCALON_POTENCIA_BASE
            factor_seguro = max(config.FACTOR_MASA_AUTORIZADA, 0.001)
            
            self.referencia_escalon = (margen_real // base) * base
            self.masa_autorizada = self.referencia_escalon / factor_seguro

    # === [SUBTEMA: LOGÍSTICA DE SOMBRAS (PUENTE DE HIERRO)] ===

    async def solicitar_reserva(self, uid: str, masa: float, general: str, direccion: str = "LONG") -> bool:
        """Puente para que Beru pida masa al sistema dinámico."""
        async with self._lock:
            # 1. Filtro de Oxígeno
            if self.masa_autorizada < masa: 
                return False

            # 2. Materialización de la sombra para Beru
            if uid not in self.reservas_activas:
                self.reservas_activas[uid] = type('Sombra', (object,), {
                    'uid': uid, 'masa': masa, 'direccion': direccion, 'estado': 'ACECHANDO'
                })
            
            # 3. Reserva de energía
            self.masa_autorizada -= masa
            self.masa_reservada_ltc += masa
            return True

    async def confirmar_reserva(self, uid: str, frente: str, direccion: str, fill_confirmado=True):
        """
        Fija el peso de la sombra en un muelle real.
        En MODO_SIMULACION=False, requiere fill_confirmado=True (caller debe verificar).
        """
        if not config.MODO_SIMULACION and not fill_confirmado:
            await self.bel.anotar("TUSK", "ANCLAJE_RECHAZADO",
                                  f"Modo live: fill no confirmado para {uid} en {frente}")
            return False

        async with self._lock:
            if uid in self.reservas_activas:
                sombra = self.reservas_activas[uid]
                dir_key = "long" if direccion == "LONG" else "short"

                if frente not in self.pesos:
                    self.pesos[frente] = {"long": 0.0, "short": 0.0}

                self.pesos[frente][dir_key] += sombra.masa
                await self.bel.anotar("TUSK", "ANCLAJE", f"Masa {sombra.masa:.4f} fijada en {frente}.")
                return True
        return False

    async def liberar_reserva(self, uid: str):
        """Devuelve la masa al cofre si la misión falla."""
        async with self._lock:
            if uid in self.reservas_activas:
                sombra = self.reservas_activas.pop(uid)
                self.masa_autorizada += sombra.masa
                self.masa_reservada_ltc = max(0.0, self.masa_reservada_ltc - sombra.masa)

    async def consumar_cosecha_atomica(self, uid_reserva, frente_salida, barco_ref):
        """Cierra el ciclo y recupera la energía tras una victoria."""
        async with self._lock:
            if uid_reserva in self.reservas_activas:
                sombra = self.reservas_activas.pop(uid_reserva)
                self.masa_reservada_ltc -= sombra.masa
                self.masa_autorizada += sombra.masa # Recuperamos el oxígeno
                self.total_ciclos_consumados += 1
                await self.bel.anotar("TUSK", "ÉXITO", f"Ciclo {self.total_ciclos_consumados} sellado.")