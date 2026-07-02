import asyncio
import time
import uuid

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
from core.models import IntencionAccion
import core.config as config  # La fuente de verdad central

class IgrisEscudo:
    def __init__(self, tusk, beru):
        """
        Igris: El Escudo de la Legión. 
        Maestro de la optimización de Masa Bruta y Delta-Neutralidad.
        """
        self.tusk = tusk
        self.beru = beru
        self.greed = beru.greed
        self.bel = beru.bel

        # Leyes de Equilibrio (Ratios de Delta Neta)
        self.limite_long_max = 0.52  # 52%
        self.limite_long_min = 0.48  # 48%
        
        # Gestión de Cooldown para evitar sobre-operación
        self.ultimo_movimiento = time.time()
        self.cooldown_maniobra_s = 5.0



# === [SUBTEMA: VIGILANCIA DEL MANTO (BUCLE)] ===

    async def vigilar_manto_operativo(self):
        """Bucle de vigilancia continua del Pentiverso."""
        print(f"[IGRIS] Vigilancia activa bajo protocolo {config.FASE_ACTUAL}.")
        while True:
            # Observamos el mercado a través de los ojos de la Hidra
            ctx_map, estado = await self.beru.tank.vision_especulativa()
            
            # Solo operamos si hay visión estable
            if estado != "ROJO":
                await self.auditar_manto_global()
            
            await asyncio.sleep(1)



# === [SUBTEMA: AUDITORÍA GLOBAL (LÓGICA DE CONTROL)] ===

    async def auditar_manto_global(self):
        """Calcula la salud del sistema y decide la maniobra necesaria."""
        margen_actual = self.tusk.margen_ocupado
        
        # Sumatoria de masa en los 5 mares de LTC
        peso_l_total = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s_total = sum(f["short"] for f in self.tusk.pesos.values())
        
        masa_bruta = peso_l_total + peso_s_total
        tiempo_actual = time.time()
        en_cooldown = (tiempo_actual - self.ultimo_movimiento) <= self.cooldown_maniobra_s

        # 1. 🚨 LEY MARCIAL (Muro de Poda)
        if margen_actual >= config.MURO_LEY_MARCIAL:
            await self.bel.anotar("IGRIS", "LEY_MARCIAL", f"Margen Crítico: {margen_actual}%.")
            dir_poda = "LONG" if peso_l_total >= peso_s_total else "SHORT"
            await self._delegar_maniobra("PODAR_MANTO", prioridad=0, direccion=dir_poda, masa_req=masa_bruta * 0.15)
            return

        # 2. 💎 LIMPIEZA DE ESPEJOS (Optimización de Masa Bruta)
        if margen_actual > config.RANGO_LIMPIEZA_MAX and peso_l_total > 0 and peso_s_total > 0:
            masa_espejo = min(peso_l_total, peso_s_total, self.tusk.masa_autorizada * 2)
            await self.bel.anotar("IGRIS", "LIMPIEZA", f"Margen {margen_actual}%. Reduciendo masa bruta.")
            await self._delegar_maniobra("LIMPIAR_ESPEJOS", prioridad=1, direccion="AMBAS", masa_req=masa_espejo)
            return

        if en_cooldown: return

        # 3. ⚖️ REBALANCEO (Delta Neta)
        if masa_bruta > 0:
            ratio_l = peso_l_total / masa_bruta
            if ratio_l > self.limite_long_max:
                await self._delegar_maniobra("REBALANCEO_IGRIS", prioridad=1, direccion="SHORT", masa_req=self.tusk.masa_autorizada)
                return
            elif ratio_l < self.limite_long_min:
                await self._delegar_maniobra("REBALANCEO_IGRIS", prioridad=1, direccion="LONG", masa_req=self.tusk.masa_autorizada)
                return

        # 4. 📈 ENGORDAR MANTO (Crecimiento en Zona Dulce)
        if margen_actual < config.RANGO_EXPANSION_MIN:
            dir_engorde = "LONG" if peso_l_total <= peso_s_total else "SHORT"
            await self._delegar_maniobra("ENGORDAR_MANTO", prioridad=2, direccion=dir_engorde, masa_req=self.tusk.masa_autorizada)



   # === [SUBTEMA: MANIOBRAS TÁCTICAS (DELEGACIÓN)] ===

    async def _delegar_maniobra(self, tipo_maniobra: str, prioridad: int, direccion: str, masa_req: float):
        """Sella la intención táctica y la envía al Ejecutor (Greed)."""
        if masa_req <= 0: return

        uid_maniobra = f"IGRIS_{tipo_maniobra}_{str(uuid.uuid4())[:4]}"

        # Poda y Limpieza liberan oxígeno, no necesitan reserva previa
        if tipo_maniobra not in ["PODAR_MANTO", "LIMPIAR_ESPEJOS"]:
            reserva_exitosa = await self.tusk.solicitar_reserva(uid_maniobra, masa_req, "IGRIS", direccion)
            if not reserva_exitosa: return 

        intencion = IntencionAccion(
            prioridad=prioridad, uid=uid_maniobra, general="IGRIS",
            tipo=tipo_maniobra, masa=masa_req, direccion=direccion  
        )

        await self.greed.altar.put(intencion)
        self.ultimo_movimiento = time.time()