import asyncio
import time
import uuid

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

    # === EL ALTAR (BUCLE PRINCIPAL) ===

    async def arbitrar(self):
        """El pulso del Juez. Procesa intenciones según prioridad."""
        print(f"[GREED] Altar activo bajo protocolo {config.FASE_ACTUAL}.")

        asyncio.create_task(self._radar_escuadron_suicida())

        while True:
            intencion = await self.altar.get()
            self.dedupe_set.discard(intencion.dedupe_key)

            if not self._es_valida_internamente(intencion):
                if intencion.tipo not in ["COSECHA", "PODAR_MANTO", "LIMPIAR_ESPEJOS"]:
                    await self.tusk.liberar_reserva(intencion.uid)
                self.altar.task_done()
                continue

            ctx_map, estado_semaforo = await self.tank.vision_especulativa()
            if estado_semaforo in ["GLITCH_DETECTADO", "ROJO"]:
                if intencion.tipo not in ["COSECHA", "PODAR_MANTO", "LIMPIAR_ESPEJOS"]:
                    await self.tusk.liberar_reserva(intencion.uid)
                self.altar.task_done()
                continue

            # Enrutamiento Táctico
            if intencion.general == "BERU":
                if intencion.tipo == "CAZA":
                    await self._ejecutar_caza_multiverse(intencion, ctx_map)
                elif intencion.tipo == "COSECHA":
                    await self._ejecutar_cosecha_multiverse(intencion, ctx_map)
            elif intencion.general == "IGRIS":
                if intencion.tipo == "PODAR_MANTO":
                    await self._ejecutar_poda_cirugia(intencion, ctx_map)
                elif intencion.tipo == "LIMPIAR_ESPEJOS":
                    await self._ejecutar_limpieza_espejos(intencion, ctx_map)
                elif intencion.tipo == "REBALANCEO_IGRIS":
                    await self._ejecutar_rebalanceo(intencion, ctx_map)
                elif intencion.tipo == "ENGORDAR_MANTO":
                    await self._ejecutar_engorde_manto(intencion, ctx_map)
                else:
                    await self.tusk.liberar_reserva(intencion.uid)
            else:
                await self._ejecutar_ataque_autonomo(intencion, ctx_map)

            self.altar.task_done()

    # === BANDA ADAPTATIVA (CANDADO DE DELTA) ===

    def _calcular_banda(self):
        """Banda general de tolerancia al desbalance según margen usado."""
        margen = self.tusk.margen_ocupado
        if margen <= config.DELTA_MARGEN_RELAJADO:
            tolerancia = config.DELTA_TOLERANCIA_MAX
        elif margen >= config.DELTA_MARGEN_PARANOICO:
            tolerancia = 0.0
        else:
            progreso = (margen - config.DELTA_MARGEN_RELAJADO) / (config.DELTA_MARGEN_PARANOICO - config.DELTA_MARGEN_RELAJADO)
            tolerancia = config.DELTA_TOLERANCIA_MAX * (1.0 - progreso)
        return (0.50 - tolerancia, 0.50 + tolerancia)

    def _calcular_banda_frente(self, frente):
        """
        Banda por frente: banda general × factor de personalidad (slippage).
        Monedas calientes tienen banda más apretada.
        """
        margen = self.tusk.margen_ocupado
        if margen <= config.DELTA_MARGEN_RELAJADO:
            tolerancia_base = config.DELTA_TOLERANCIA_MAX
        elif margen >= config.DELTA_MARGEN_PARANOICO:
            tolerancia_base = 0.0
        else:
            progreso = (margen - config.DELTA_MARGEN_RELAJADO) / (config.DELTA_MARGEN_PARANOICO - config.DELTA_MARGEN_RELAJADO)
            tolerancia_base = config.DELTA_TOLERANCIA_MAX * (1.0 - progreso)

        factor = config.SLIPPAGE_FACTOR.get(frente, config.SLIPPAGE_FACTOR_DEFAULT)
        tolerancia = tolerancia_base * factor
        return (0.50 - tolerancia, 0.50 + tolerancia)

    def _verificar_delta_post_maniobra(self, masa_long_nueva, masa_short_nueva):
        """Verifica si tras una maniobra el ratio queda dentro de banda general."""
        total = masa_long_nueva + masa_short_nueva
        if total <= 0:
            return True
        ratio = masa_long_nueva / total
        banda_min, banda_max = self._calcular_banda()
        return banda_min <= ratio <= banda_max

    def _verificar_delta_frente(self, frente, masa_long_frente, masa_short_frente):
        """Verifica que un frente específico no exceda su banda local."""
        total = masa_long_frente + masa_short_frente
        if total <= 0:
            return True
        ratio = masa_long_frente / total
        banda_min, banda_max = self._calcular_banda_frente(frente)
        return banda_min <= ratio <= banda_max

    # === REBALANCEO IGRIS ===

    async def _ejecutar_rebalanceo(self, intencion, ctx_map):
        """
        Rebalanceo inteligente: evalúa reducir el lado pesado vs abrir en el flaco.
        Elige la opción con mejor precio. Respeta banda adaptativa.
        Puede hacer ambas patas si conviene.
        """
        frentes_disponibles = ["LTCUSD_INVERSE", "LTCUSDT_LINEAL", "LTCUSDC_LINEAL"]
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        masa_disponible = intencion.masa

        # Dirección que Igris pidió reforzar
        dir_refuerzo = intencion.direccion
        dir_reducir = "SHORT" if dir_refuerzo == "LONG" else "LONG"
        dir_key_reducir = "short" if dir_refuerzo == "LONG" else "long"

        # Opción A: Reducir el lado pesado (cerrar del gordo)
        frentes_pesados = {f: p[dir_key_reducir] for f, p in self.tusk.pesos.items() if p[dir_key_reducir] > 0}
        puede_reducir = len(frentes_pesados) > 0

        # Opción B: Abrir en el lado flaco (mejor precio)
        _, precio_apertura = self._escanear_mejor_precio(frentes_disponibles, ctx_map, masa_disponible, dir_refuerzo == "LONG")
        puede_abrir = precio_apertura > 0

        masa_aplicada = 0.0

        # Intentar reducir del lado pesado
        if puede_reducir:
            frente_gordo = max(frentes_pesados, key=frentes_pesados.get)
            masa_reduccion = min(masa_disponible * 0.5, frentes_pesados[frente_gordo])

            # Simular el resultado
            nuevo_l = peso_l - (masa_reduccion if dir_key_reducir == "long" else 0)
            nuevo_s = peso_s - (masa_reduccion if dir_key_reducir == "short" else 0)

            if self._verificar_delta_post_maniobra(nuevo_l, nuevo_s) and masa_reduccion > 0:
                self.tusk.pesos[frente_gordo][dir_key_reducir] -= masa_reduccion
                masa_aplicada += masa_reduccion
                peso_l, peso_s = nuevo_l, nuevo_s
                await self.bel.anotar("GREED", "REBALANCEO_CORTE", f"Reducido {masa_reduccion:.4f} {dir_reducir} de {frente_gordo}")

        # Intentar abrir en el lado flaco con lo que queda
        masa_restante = masa_disponible - masa_aplicada
        if puede_abrir and masa_restante > 0:
            mejor_f, _ = self._escanear_mejor_precio(frentes_disponibles, ctx_map, masa_restante, dir_refuerzo == "LONG")
            dir_key_abrir = "long" if dir_refuerzo == "LONG" else "short"

            nuevo_l = peso_l + (masa_restante if dir_refuerzo == "LONG" else 0)
            nuevo_s = peso_s + (masa_restante if dir_refuerzo == "SHORT" else 0)

            if self._verificar_delta_post_maniobra(nuevo_l, nuevo_s):
                await self.tusk.confirmar_reserva(intencion.uid, mejor_f, dir_refuerzo)
                await self.bel.anotar("GREED", "REBALANCEO_APERTURA", f"Abierto {masa_restante:.4f} {dir_refuerzo} en {mejor_f}")
                return

        # Si no pudo abrir, liberar lo que sobre
        await self.tusk.liberar_reserva(intencion.uid)

    # === ENGORDAR MANTO ===

    async def _ejecutar_engorde_manto(self, intencion, ctx_map):
        """
        Engorda el manto: abre posición en la dirección indicada por Igris.
        Sin crear BeruShip — solo mueve masa en Tusk.
        Respeta banda general + banda por frente (personalidad slippage).
        """
        frentes_disponibles = ["LTCUSD_INVERSE", "LTCUSDT_LINEAL", "LTCUSDC_LINEAL"]
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        masa = intencion.masa
        dir_principal = intencion.direccion

        # Simular apertura solo en la dirección pedida
        nuevo_l = peso_l + (masa if dir_principal == "LONG" else 0)
        nuevo_s = peso_s + (masa if dir_principal == "SHORT" else 0)

        if self._verificar_delta_post_maniobra(nuevo_l, nuevo_s):
            mejor_f, _ = self._escanear_mejor_precio(frentes_disponibles, ctx_map, masa, dir_principal == "LONG")

            # Verificar banda local del frente elegido
            pesos_f = self.tusk.pesos.get(mejor_f, {"long": 0.0, "short": 0.0})
            fl = pesos_f["long"] + (masa if dir_principal == "LONG" else 0)
            fs = pesos_f["short"] + (masa if dir_principal == "SHORT" else 0)

            if self._verificar_delta_frente(mejor_f, fl, fs):
                await self.tusk.confirmar_reserva(intencion.uid, mejor_f, dir_principal)
                await self.bel.anotar("GREED", "ENGORDE", f"+{masa:.4f} {dir_principal} en {mejor_f}")
                return

        # Si no cabe en una dirección, dividir entre ambas
        mitad = masa * 0.5
        mejor_f_l, _ = self._escanear_mejor_precio(frentes_disponibles, ctx_map, mitad, True)
        mejor_f_s, _ = self._escanear_mejor_precio(frentes_disponibles, ctx_map, mitad, False)

        nuevo_l_mix = peso_l + mitad
        nuevo_s_mix = peso_s + mitad

        if self._verificar_delta_post_maniobra(nuevo_l_mix, nuevo_s_mix):
            # Verificar banda local de ambos frentes
            pf_l = self.tusk.pesos.get(mejor_f_l, {"long": 0.0, "short": 0.0})
            pf_s = self.tusk.pesos.get(mejor_f_s, {"long": 0.0, "short": 0.0})

            ok_l = self._verificar_delta_frente(mejor_f_l, pf_l["long"] + mitad, pf_l["short"])
            ok_s = self._verificar_delta_frente(mejor_f_s, pf_s["long"], pf_s["short"] + mitad)

            if ok_l and ok_s:
                await self.tusk.confirmar_reserva(intencion.uid, mejor_f_l, "LONG")
                uid_mitad = f"{intencion.uid}_S"
                if await self.tusk.solicitar_reserva(uid_mitad, mitad, "GREED", "SHORT"):
                    await self.tusk.confirmar_reserva(uid_mitad, mejor_f_s, "SHORT")
                await self.bel.anotar("GREED", "ENGORDE_DUAL", f"+{mitad:.4f} L en {mejor_f_l} | +{mitad:.4f} S en {mejor_f_s}")
                return

        await self.tusk.liberar_reserva(intencion.uid)
        await self.bel.anotar("GREED", "ENGORDE_BLOQUEADO", "Banda general o local no permite crecer")

    # === RADAR DEL ESCUADRÓN SUICIDA ===

    async def _radar_escuadron_suicida(self):
        """Busca ineficiencias de precio (regalos) para disparos autónomos."""
        while True:
            ctx_map, estado = await self.tank.vision_especulativa()

            if estado == "VERDE_SEGURO":
                p_usdt = ctx_map.get("LTCUSDT_LINEAL").last_price
                p_usdc = ctx_map.get("LTCUSDC_LINEAL").last_price

                if p_usdt > 0.0 and p_usdc > 0.0:
                    desviacion = abs(p_usdt - p_usdc) / p_usdt

                    if desviacion >= config.UMBRAL_REGALO_SQUAD and self.tusk.masa_autorizada > 0.0:
                        uid_regalo = f"SUICIDE_{int(time.time())}"
                        direccion = "SHORT" if p_usdc > p_usdt else "LONG"

                        intencion = IntencionAccion(
                            prioridad=0, uid=uid_regalo, general="GREED_SQUAD",
                            tipo="ATAQUE_OPORTUNISTA", masa=self.tusk.masa_autorizada * 0.5,
                            direccion=direccion
                        )

                        if await self.tusk.solicitar_reserva(uid_regalo, intencion.masa, "GREED"):
                            await self.altar.put(intencion)
                            await self.bel.anotar("GREED", "ESCUADRON_SUICIDA", f"Botín detectado: {desviacion*100:.2f}%")

            await asyncio.sleep(0.1)

    # === MANIOBRAS DE ALIVIO (PODA Y ESPEJOS) ===

    async def _ejecutar_poda_cirugia(self, intencion, ctx_map):
        """Reduce peso en el muelle más saturado para recuperar margen."""
        dir_key = "long" if intencion.direccion == "LONG" else "short"
        frentes_activos = {f: p[dir_key] for f, p in self.tusk.pesos.items() if p[dir_key] > 0}

        if not frentes_activos:
            await self.tusk.liberar_reserva(intencion.uid)
            return

        mejor_frente = max(frentes_activos, key=frentes_activos.get)
        masa_extraida = min(intencion.masa, self.tusk.pesos[mejor_frente][dir_key])

        self.tusk.pesos[mejor_frente][dir_key] -= masa_extraida

        await self.tusk.liberar_reserva(intencion.uid)
        await self.bel.anotar("GREED", "PODA", f"Extirpados {masa_extraida:.4f} LTC de {mejor_frente}")

    async def _ejecutar_limpieza_espejos(self, intencion, ctx_map):
        """Cancela masa enfrentada (L/S) para optimizar la Masa Bruta."""
        m_l = max(self.tusk.pesos, key=lambda f: self.tusk.pesos[f]["long"])
        m_s = max(self.tusk.pesos, key=lambda f: self.tusk.pesos[f]["short"])

        limpieza_l = min(intencion.masa, self.tusk.pesos[m_l]["long"])
        limpieza_s = min(intencion.masa, self.tusk.pesos[m_s]["short"])

        self.tusk.pesos[m_l]["long"] -= limpieza_l
        self.tusk.pesos[m_s]["short"] -= limpieza_s

        await self.tusk.liberar_reserva(intencion.uid)
        await self.bel.anotar("GREED", "LIMPIEZA", f"Espejos reducidos: {min(limpieza_l, limpieza_s):.4f} LTC.")

    # === LOGÍSTICA DE COMBATE (CAZA Y COSECHA) ===

    async def _ejecutar_cosecha_multiverse(self, intencion, ctx_map):
        """Cosecha justificada con retorno táctico al combate si no hay botín."""
        barco = intencion.barco_ref
        is_long_cosecha = not (barco.direccion == "LONG")

        mejor_frente, p_ef = self._escanear_mejor_precio(
            ["LTCUSD_INVERSE", "LTCUSDT_LINEAL", "LTCUSDC_LINEAL"],
            ctx_map, intencion.masa, is_long_cosecha
        )

        beneficio = abs(p_ef - barco.precio_entrada_real) / barco.precio_entrada_real

        if beneficio < config.UMBRAL_COSECHA_MIN:
            barco.estado = "NEGOCIANDO"
            await self.bel.anotar("GREED", "PACIENCIA", f"Beneficio {beneficio*100:.2f}% insuficiente. Retornando a combate.")
            return

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

        # Verificar banda del frente antes de anclar
        pesos_frente = self.tusk.pesos.get(mejor_f, {"long": 0.0, "short": 0.0})
        nuevo_l = pesos_frente["long"] + (intencion.masa if is_long else 0)
        nuevo_s = pesos_frente["short"] + (intencion.masa if not is_long else 0)

        if not self._verificar_delta_frente(mejor_f, nuevo_l, nuevo_s):
            await self.tusk.liberar_reserva(intencion.uid)
            await self.bel.anotar("GREED", "CAZA_BLOQUEADA", f"Banda de {mejor_f} no permite {intencion.direccion}")
            return

        await self.tusk.confirmar_reserva(intencion.uid, mejor_f, intencion.direccion)
        if intencion.barco_ref:
            intencion.barco_ref.frente_asignado = mejor_f
            intencion.barco_ref.precio_entrada_real = p_ef
            intencion.barco_ref.estado = "NEGOCIANDO"
        await self.bel.anotar("GREED", "CAZA", f"Anclado en {mejor_f} @ {p_ef:.2f}")

    # === CEREBRO DE ARBITRAJE Y PRECIOS ===

    def _escanear_mejor_precio(self, frentes, ctx_map, masa, is_long):
        """Analiza los frentes y penaliza según la profundidad del muro."""
        analisis = {}
        for f in frentes:
            ctx = ctx_map.get(f)
            if not ctx or ctx.last_price <= 0:
                continue
            muro = ctx.muro_ask_volumen if is_long else ctx.muro_bid_volumen
            penalidad = 0.0001 if muro > (masa * 10) else 0.0015
            p_ef = ctx.last_price * (1 + penalidad) if is_long else ctx.last_price * (1 - penalidad)
            analisis[f] = p_ef
        if not analisis:
            return "LTCUSDT_LINEAL", 0.0
        ganador = min(analisis, key=analisis.get) if is_long else max(analisis, key=analisis.get)
        return ganador, analisis[ganador]

    def _es_valida_internamente(self, intencion: IntencionAccion) -> bool:
        """Verifica si el contrato aún es aire fresco según config.py."""
        return (time.time() - intencion.timestamp) * 1000 <= config.TTL_ORDEN_MS

    # === ATAQUE SIMULADO ===

    async def _ejecutar_ataque_autonomo(self, intencion, ctx_map):
        """Ataque de Hierro: Un disparo, un muerto. Recarga de 10s para simulación."""
        try:
            ahora = time.time()

            if hasattr(self, '_ultima_recarga') and (ahora - self._ultima_recarga) < 10:
                return

            mensaje = f"Impacto de Hierro | Masa: {intencion.masa:.4f} LTC | Dir: {intencion.direccion}"
            await self.bel.anotar("GREED", "DISPARO_SIMULADO", mensaje)

            self._ultima_recarga = ahora
            await self.tusk.liberar_reserva(intencion.uid)

        except Exception as e:
            await self.bel.anotar("GREED", "ERROR_DISPARO", str(e))
