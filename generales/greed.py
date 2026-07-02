import asyncio
import time
import uuid

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
from core.models import IntencionAccion
import core.config as config

class GreedFrancotirador:
    def __init__(self, tusk, bellion, tank_cluster):
        """
        Greed: El Ejecutor del Pentiverso.
        Juez y parte en la materialización de masa y arbitraje.
        """
        self.tusk = tusk
        self.bel = bellion
        self.tank = tank_cluster  
        self.altar = asyncio.PriorityQueue()
        self.dedupe_set = set()

# === [SUBTEMA: EL ALTAR (BUCLE PRINCIPAL DE ARBITRAJE)] ===

    async def arbitrar(self):
        """El pulso del Juez. Procesa intenciones según prioridad."""
        print(f"[GREED] Altar activo bajo protocolo {config.FASE_ACTUAL}.")
        
        asyncio.create_task(self._radar_escuadron_suicida())

        while True:
            intencion = await self.altar.get()
            self.dedupe_set.discard(intencion.dedupe_key)

            # 1. Validación de frescura (TTL centralizado en config.py)
            if not self._es_valida_internamente(intencion):
                if intencion.tipo not in ["COSECHA", "PODAR_MANTO", "LIMPIAR_ESPEJOS"]: 
                    await self.tusk.liberar_reserva(intencion.uid)
                self.altar.task_done()
                continue

            # 2. Validación de visión (Semaforo de la Hidra)
            ctx_map, estado_semaforo = await self.tank.vision_especulativa()
            if estado_semaforo in ["GLITCH_DETECTADO", "ROJO"]:
                if intencion.tipo not in ["COSECHA", "PODAR_MANTO", "LIMPIAR_ESPEJOS"]:
                    await self.tusk.liberar_reserva(intencion.uid)
                self.altar.task_done()
                continue

            # 3. Enrutamiento Táctico
            if intencion.general == "BERU":
                if intencion.tipo == "CAZA": await self._ejecutar_caza_multiverse(intencion, ctx_map)
                elif intencion.tipo == "COSECHA": await self._ejecutar_cosecha_multiverse(intencion, ctx_map)
            elif intencion.general == "IGRIS":
                if intencion.tipo == "PODAR_MANTO": await self._ejecutar_poda_cirugia(intencion, ctx_map)
                elif intencion.tipo == "LIMPIAR_ESPEJOS": await self._ejecutar_limpieza_espejos(intencion, ctx_map)
                else: await self._ejecutar_caza_multiverse(intencion, ctx_map)
            else:
                await self._ejecutar_ataque_autonomo(intencion, ctx_map)
                
            self.altar.task_done()


# === [SUBTEMA: RADAR DEL ESCUADRÓN SUICIDA] ===

    async def _radar_escuadron_suicida(self):
        """Busca ineficiencias de precio (regalos) para disparos autónomos."""
        while True:
            ctx_map, estado = await self.tank.vision_especulativa()
            
            # 🛡️ COBRE: Solo operamos en verde y con precios confirmados
            if estado == "VERDE_SEGURO":
                p_usdt = ctx_map.get("LTCUSDT_LINEAL").last_price
                p_usdc = ctx_map.get("LTCUSDC_LINEAL").last_price
                
                # SEGURO ANTI-FANTASMAS: No disparamos a ceros
                if p_usdt > 0.0 and p_usdc > 0.0:
                    desviacion = abs(p_usdt - p_usdc) / p_usdt

                    # 🎯 Solo disparamos si la desviación es real y Tusk tiene oxígeno
                    if desviacion >= config.UMBRAL_REGALO_SQUAD and self.tusk.masa_autorizada > 0.0:
                        uid_regalo = f"SUICIDE_{int(time.time())}"
                        direccion = "SHORT" if p_usdc > p_usdt else "LONG" 
                        
                        # Disparo con el 50% de la potencia autorizada para no agotar el manto
                        intencion = IntencionAccion(
                            prioridad=0, uid=uid_regalo, general="GREED_SQUAD",
                            tipo="ATAQUE_OPORTUNISTA", masa=self.tusk.masa_autorizada * 0.5, 
                            direccion=direccion
                        )
                        
                        if await self.tusk.solicitar_reserva(uid_regalo, intencion.masa, "GREED"):
                            await self.altar.put(intencion)
                            await self.bel.anotar("GREED", "ESCUADRON_SUICIDA", f"Botín detectado: {desviacion*100:.2f}%")

            await asyncio.sleep(0.1) # Latido del radar


# === [SUBTEMA: MANIOBRAS DE ALIVIO (PODA Y ESPEJOS)] ===

    async def _ejecutar_poda_cirugia(self, intencion, ctx_map):
        """Reduce peso en el muelle más saturado para recuperar margen."""
        dir_key = "long" if intencion.direccion == "LONG" else "short"
        # Filtramos frentes que tengan masa real en esa dirección
        frentes_activos = {f: p[dir_key] for f, p in self.tusk.pesos.items() if p[dir_key] > 0}
        
        if not frentes_activos:
            # Si no hay nada que podar, devolvemos el permiso a la bóveda
            await self.tusk.liberar_reserva(intencion.uid)
            return

        mejor_frente = max(frentes_activos, key=frentes_activos.get)
        masa_extraida = min(intencion.masa, self.tusk.pesos[mejor_frente][dir_key])
        
        # ✂️ Ejecutamos la poda en el registro de Tusk
        self.tusk.pesos[mejor_frente][dir_key] -= masa_extraida
        
        # COBRE: Usamos liberar_reserva para devolver la masa al cofre libre
        await self.tusk.liberar_reserva(intencion.uid)
        await self.bel.anotar("GREED", "PODA", f"Extirpados {masa_extraida:.4f} LTC de {mejor_frente}")

    async def _ejecutar_limpieza_espejos(self, intencion, ctx_map):
        """Cancela masa enfrentada (L/S) para optimizar la Masa Bruta."""
        # Buscamos los muelles con más carga en cada dirección
        m_l = max(self.tusk.pesos, key=lambda f: self.tusk.pesos[f]["long"])
        m_s = max(self.tusk.pesos, key=lambda f: self.tusk.pesos[f]["short"])

        limpieza_l = min(intencion.masa, self.tusk.pesos[m_l]["long"])
        limpieza_s = min(intencion.masa, self.tusk.pesos[m_s]["short"])
        
        # Reducimos ambos lados para bajar la Masa Bruta sin afectar el Delta
        self.tusk.pesos[m_l]["long"] -= limpieza_l
        self.tusk.pesos[m_s]["short"] -= limpieza_s

        await self.tusk.liberar_reserva(intencion.uid)
        await self.bel.anotar("GREED", "LIMPIEZA", f"Espejos reducidos: {min(limpieza_l, limpieza_s):.4f} LTC.")


# === [SUBTEMA: LOGÍSTICA DE COMBATE (CAZA Y COSECHA)] ===

    async def _ejecutar_cosecha_multiverse(self, intencion, ctx_map):
        """Cosecha justificada con retorno táctico al combate si no hay botín."""
        barco = intencion.barco_ref
        is_long_cosecha = not (barco.direccion == "LONG")
        
        # Escaneo de frentes para el mejor precio de salida
        mejor_frente, p_ef = self._escanear_mejor_precio(
            ["LTCUSD_INVERSE", "LTCUSDT_LINEAL", "LTCUSDC_LINEAL"], 
            ctx_map, intencion.masa, is_long_cosecha
        )

        beneficio = abs(p_ef - barco.precio_entrada_real) / barco.precio_entrada_real

        # ⚖️ JUSTIFICACIÓN: Si no hay beneficio suficiente, el barco vuelve a NEGOCIAR
        if beneficio < config.UMBRAL_COSECHA_MIN: 
            barco.estado = "NEGOCIANDO"
            await self.bel.anotar("GREED", "PACIENCIA", f"Beneficio {beneficio*100:.2f}% insuficiente. Retornando a combate.")
            return 

        # Si hay beneficio, procedemos con el cierre atómico
        if await self.tusk.solicitar_reserva(intencion.uid, intencion.masa, "GREED", "LONG" if is_long_cosecha else "SHORT"):
            await self.tusk.consumar_cosecha_atomica(intencion.uid, mejor_frente, barco)
            
            barco.frente_salida = mejor_frente
            barco.precio_salida_real = p_ef
            barco.estado = "COSECHADO"
            
            await self.bel.anotar("GREED", "COSECHA", f"Botín asegurado @ {beneficio*100:.2f}%")

    async def _ejecutar_caza_multiverse(self, intencion, ctx_map):
        """Materializa el acecho de Beru en el mejor muelle disponible."""
        is_long = intencion.direccion == "LONG"
        mejor_f, p_ef = self._escanear_mejor_precio(["LTCUSD_INVERSE", "LTCUSDT_LINEAL", "LTCUSDC_LINEAL"], ctx_map, intencion.masa, is_long)
        
        await self.tusk.confirmar_reserva(intencion.uid, mejor_f, intencion.direccion)
        if intencion.barco_ref:
            intencion.barco_ref.frente_asignado = mejor_f
            intencion.barco_ref.precio_entrada_real = p_ef
            intencion.barco_ref.estado = "NEGOCIANDO"
        await self.bel.anotar("GREED", "CAZA", f"Anclado en {mejor_f} @ {p_ef:.2f}")


# === [SUBTEMA: CEREBRO DE ARBITRAJE Y PRECIOS] ===

    def _escanear_mejor_precio(self, frentes, ctx_map, masa, is_long):
        """Analiza los frentes y penaliza según la profundidad del muro."""
        analisis = {}
        for f in frentes:
            ctx = ctx_map.get(f)
            if not ctx or ctx.last_price <= 0: continue
            muro = ctx.muro_ask_volumen if is_long else ctx.muro_bid_volumen
            penalidad = 0.0001 if muro > (masa * 10) else 0.0015
            p_ef = ctx.last_price * (1 + penalidad) if is_long else ctx.last_price * (1 - penalidad)
            analisis[f] = p_ef
        if not analisis: return "LTCUSDT_LINEAL", 0.0
        ganador = min(analisis, key=analisis.get) if is_long else max(analisis, key=analisis.get)
        return ganador, analisis[ganador]

    def _es_valida_internamente(self, intencion: IntencionAccion) -> bool:
        """Verifica si el contrato aún es aire fresco según config.py."""
        return (time.time() - intencion.timestamp) * 1000 <= config.TTL_ORDEN_MS

# === [SUBTEMA: EJECUCIÓN DE ATAQUE SIMULADO CON SEGURO] ===
    async def _ejecutar_ataque_autonomo(self, intencion, ctx_map):
        """Ataque de Hierro: Un disparo, un muerto. Recarga de 10s para simulación."""
        try:
            ahora = time.time()
            
            # 🛡️ SEGURO TÉRMICO: Evita ráfagas infinitas en el entorno de pruebas.
            if hasattr(self, '_ultima_recarga') and (ahora - self._ultima_recarga) < 10:
                return 

            # Registramos el impacto en los anales de Bellion
            mensaje = f"Impacto de Hierro | Masa: {intencion.masa:.4f} LTC | Dir: {intencion.direccion}"
            await self.bel.anotar("GREED", "DISPARO_SIMULADO", mensaje)
            
            # ⏳ Activamos el cronómetro de enfriamiento
            self._ultima_recarga = ahora
            
            # 🔄 CIERRE DE CICLO: Devolvemos la energía de la sombra a la bóveda 
            await self.tusk.liberar_reserva(intencion.uid)
            
            print(f"\n[🔥] GREED: Objetivo neutralizado. Entrando en fase de recarga (10s)...")
            
        except Exception as e:
            await self.bel.anotar("GREED", "ERROR_DISPARO", str(e))