import asyncio
import uuid
import time

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
from core.models import BeruShip, IntencionAccion
import core.config as config


class BeruCazador:
    def __init__(self, tusk, greed, bellion, tank):
        """
        Beru: El Cazador del Pentiverso.
        Evolucionado para la fase de Cuarzo con resonancia piezoeléctrica.
        """
        self.tusk = tusk
        self.greed = greed
        self.bel = bellion
        self.tank = tank  
        self.legion = []

    # === [SUBTEMA: PULSO VITAL Y GENERACIÓN] ===

    async def hilo_beru_berserker(self):
        """Corazón de Beru: Pulso de 10ms para reacción instantánea."""
        while True:
            # Diapasón central de precios (USDT_PERP)
            precio = self.tusk.ultimo_precio 

            # 🛡️ SEGURO DEL CAÑÓN: Previene el "Barco Fantasma" al arrancar
            if precio <= 0.0:
                await asyncio.sleep(0.01)
                continue

            # 1. Asegurar que siempre haya una semilla acechando
            if not any(b.estado == "ACECHANDO" for b in self.legion):
                self.plantar_semilla_adan(precio)

            await self.auditar_gatillos_adan(precio)
            await self.sincronizar_mejoras_greed()
            await self.ejecutar_acordeon_asimetrico(precio)
            await self.evaluar_colisiones_y_fusion()
            self.limpiar_legion()

            await asyncio.sleep(0.01)

    def plantar_semilla_adan(self, precio_actual):
        """Genera un nuevo acechador con el ADN del clima actual."""
        nuevo_uid = f"BERU_SEM_{int(time.time())}"
        cap_actual = self.tank.capitan_activo
        
        semilla = BeruShip(
            uid=nuevo_uid, centro_local=precio_actual, masa=0.0,
            direccion="LONG", estado="ACECHANDO", generacion=1,
            adn_capitan=cap_actual  
        )
        # 🛡️ COBRE: Memoria para el rastreo dinámico del Negociador
        semilla.max_favor = 0.0 
        self.legion.append(semilla)


# === [SUBTEMA: ACECHO Y MATERIALIZACIÓN (GATILLOS)] ===

async def auditar_gatillos_adan(self, precio_actual):
        """Detecta el cruce del vacío y dispara en CONTRATENDENCIA."""
        for beru in self.legion:
            if beru.estado == "ACECHANDO":
                distancia = (precio_actual - beru.centro_local) / max(beru.centro_local, 0.0001)

                if abs(distancia) < 0.0005: continue

                # Si el precio escapa del Vacío de Adán (0.5%)
                if abs(distancia) >= beru.adn_capitan.vacio_adan:
                    masa_fresca = self.tusk.masa_autorizada
                    if masa_fresca <= 0.0: continue 

                    # 🛡️ COBRE: Contratendencia (Sube -> SHORT | Baja -> LONG)
                    beru.direccion = "SHORT" if distancia > 0 else "LONG"
                    beru.estado = "ESPERANDO_MATERIALIZACION"
                    
                    if await self.tusk.solicitar_reserva(beru.uid, masa_fresca, "BERU", beru.direccion):
                        beru.masa = masa_fresca
                        
                        # 📐 Geometría de Adán: Red al 1.1% y Oz al 0.9% del centro original
                        beru.red_adan = beru.centro_local * (1.011 if distancia > 0 else 0.989)
                        beru.oz_adan = beru.centro_local * (0.989 if distancia > 0 else 1.011)
                        
                        deseo = IntencionAccion(
                            prioridad=1, uid=beru.uid, general="BERU", tipo="CAZA", 
                            masa=masa_fresca, direccion=beru.direccion,
                            barco_ref=beru, precio_oz_objetivo=precio_actual
                        )
                        await self.greed.altar.put(deseo)


# === [SUBTEMA: RESONANCIA Y MEJORA (SINCRO GREED)] ===

    async def sincronizar_mejoras_greed(self):
        """Absorbe los 'regalos' de precio efectivo tras la materialización."""
        for beru in self.legion:
            if beru.estado == "NEGOCIANDO" and beru.oz == 0.0:
                cap = beru.adn_capitan
                m = cap.margen_apertura 
                p_real = beru.precio_entrada_real
                beru.centro_local = p_real 
                
                if beru.direccion == "LONG":
                    beru.oz, beru.red = p_real * (1 - m), p_real * (1 + m)
                else:
                    beru.oz, beru.red = p_real * (1 + m), p_real * (1 - m)
                
                await self.bel.anotar("BERU", "RESONANCIA", f"{beru.uid} sincronizado @ {p_real:.2f}")

    # === [SUBTEMA: COMBATE ACTIVO (ACORDEÓN)] ===

async def ejecutar_acordeon_asimetrico(self, precio_actual):
        """El Negociador: Engorda en el abismo y asegura botín con la regla 1.1/0.9."""
        for beru in self.legion:
            if beru.estado != "NEGOCIANDO": continue
            
            # 🔴 1. EL ENGORDE (0.1% adicional si toca la Red Extrema/Adán)
            toca_red = (beru.direccion == "SHORT" and precio_actual >= beru.red_adan) or \
                       (beru.direccion == "LONG" and precio_actual <= beru.red_adan)
            
            if toca_red:
                masa_extra = beru.masa * 0.001 # El 0.1% de tu plano maestro
                if await self.tusk.solicitar_reserva(f"E_{beru.uid}", masa_extra, "BERU", beru.direccion):
                    beru.masa += masa_extra
                    # Estiramos la red un 0.1% adicional para el siguiente nivel de engorde
                    beru.red_adan *= (1.001 if beru.direccion == "SHORT" else 0.999)
                    await self.bel.anotar("BERU", "ENGORDE", f"{beru.uid} inyectado 0.1%.")

            # 🟢 2. EL NEGOCIADOR (Rastreo de ganancia máxima desde el centro)
            ganancia = (beru.centro_local - precio_actual)/beru.centro_local if beru.direccion == "SHORT" else (precio_actual - beru.centro_local)/beru.centro_local
            
            if ganancia > beru.max_favor:
                beru.max_favor = ganancia # Registramos el pico de la presa

            # Activamos el rastreo si ya ganamos al menos 1%
            if beru.max_favor >= 0.01:
                # La Oz se coloca a -1.1% del pico de ganancia máxima
                factor_oz = 1 - (beru.max_favor - 0.011) if beru.direccion == "SHORT" else 1 + (beru.max_favor - 0.011)
                beru.oz_adan = beru.centro_local * factor_oz
                
                # Si el precio retrocede y toca la Oz -> Se cierra la cacería
                toca_oz = (beru.direccion == "SHORT" and precio_actual >= beru.oz_adan) or \
                          (beru.direccion == "LONG" and precio_actual <= beru.oz_adan)
                
                if toca_oz:
                    await self.ejecutar_cosecha_y_relevo(beru, precio_actual)

# === [SUBTEMA: SALIDA Y RELEVO (COSECHA)] ===

    async def ejecutar_cosecha_y_relevo(self, beru_actual, precio_actual):
        """Inicia el fin del ciclo de vida y genera la siguiente generación."""
        uid_cosecha = f"COSECHA_{str(uuid.uuid4())[:4]}"
        
        deseo = IntencionAccion(
            prioridad=0, uid=uid_cosecha, general="BERU", tipo="COSECHA", 
            masa=beru_actual.masa, barco_ref=beru_actual
        )
        await self.greed.altar.put(deseo)
        beru_actual.estado = "ESPERANDO_SUELTA"

        # RELEVO GENERACIONAL
        nuevo_uid = f"BERU_GEN_{beru_actual.generacion + 1}_{int(time.time())}"
        
        # 🔴 SOLDADURA DE SEGURIDAD: Solo relevamos si hay masa autorizada > 0
        masa_fresca = self.tusk.masa_autorizada
        if masa_fresca > 0 and await self.tusk.solicitar_reserva(nuevo_uid, masa_fresca, "BERU", beru_actual.direccion):
            beru_nuevo = BeruShip(
                uid=nuevo_uid, centro_local=precio_actual, masa=masa_fresca, 
                direccion=beru_actual.direccion, estado="ACECHANDO",
                generacion=beru_actual.generacion + 1, adn_capitan=self.tank.capitan_activo 
            )
            self.legion.append(beru_nuevo)



    # === [SUBTEMA: OPTIMIZACIÓN Y FUSIÓN] ===

async def evaluar_colisiones_y_fusion(self):
        """Fusión por Precio Promedio: Consolida la legión y resetea el centro local."""
        activos = [b for b in self.legion if b.estado == "NEGOCIANDO"]
        if len(activos) < 2: return

        for direccion in ["LONG", "SHORT"]:
            grupo = [b for b in activos if b.direccion == direccion]
            if len(grupo) < 2: continue
            
            masa_total = sum(b.masa for b in grupo)
            p_promedio = sum(b.centro_local * b.masa for b in grupo) / masa_total
            
            # Si el precio actual toca el promedio de la expedición (colisión)
            if abs(self.tusk.ultimo_precio - p_promedio) / p_promedio < 0.0005:
                lider = grupo[0]
                lider.masa = masa_total
                lider.centro_local = p_promedio # Nuevo 0 Absoluto para la legión fusionada
                lider.max_favor = 0.0
                lider.es_super_beru = True
                
                for b in grupo[1:]:
                    b.estado = "FUSIONADO"
                
                await self.bel.anotar("BERU", "SUPER_FUSION", f"Masa consolidada en {p_promedio:.2f}")