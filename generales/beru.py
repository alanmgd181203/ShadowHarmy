import asyncio
import uuid
import time

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

    # === PULSO VITAL Y GENERACIÓN ===

    async def hilo_beru_berserker(self):
        """Corazón de Beru: Pulso de 10ms para reacción instantánea."""
        while True:
            precio = self.tusk.ultimo_precio

            if precio <= 0.0:
                await asyncio.sleep(0.01)
                continue

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
        self.legion.append(semilla)

    # === ACECHO Y MATERIALIZACIÓN (GATILLOS) ===

    async def auditar_gatillos_adan(self, precio_actual):
        """Detecta el cruce del vacío y dispara en CONTRATENDENCIA."""
        for beru in self.legion:
            if beru.estado == "ACECHANDO":
                distancia = (precio_actual - beru.centro_local) / max(beru.centro_local, 0.0001)

                if abs(distancia) < 0.0005:
                    continue

                if abs(distancia) >= beru.adn_capitan.vacio_adan:
                    masa_fresca = self.tusk.masa_autorizada
                    if masa_fresca <= 0.0:
                        continue

                    beru.direccion = "SHORT" if distancia > 0 else "LONG"
                    beru.estado = "ESPERANDO_MATERIALIZACION"

                    if await self.tusk.solicitar_reserva(beru.uid, masa_fresca, "BERU", beru.direccion):
                        beru.masa = masa_fresca

                        beru.red_adan = beru.centro_local * (1.011 if distancia > 0 else 0.989)
                        beru.oz_adan = beru.centro_local * (0.989 if distancia > 0 else 1.011)

                        deseo = IntencionAccion(
                            prioridad=1, uid=beru.uid, general="BERU", tipo="CAZA",
                            masa=masa_fresca, direccion=beru.direccion,
                            barco_ref=beru, precio_oz_objetivo=precio_actual
                        )
                        await self.greed.altar.put(deseo)

    # === RESONANCIA Y MEJORA (SINCRO GREED) ===

    async def sincronizar_mejoras_greed(self):
        """Absorbe el precio real de Greed y recentra el barco tras materialización."""
        for beru in self.legion:
            if beru.estado == "NEGOCIANDO" and not beru.sincronizado:
                p_real = beru.precio_entrada_real
                if p_real <= 0.0:
                    continue
                beru.centro_local = p_real
                beru.sincronizado = True
                await self.bel.anotar("BERU", "RESONANCIA", f"{beru.uid} sincronizado @ {p_real:.2f}")

    # === COMBATE ACTIVO (ACORDEÓN) ===

    async def ejecutar_acordeon_asimetrico(self, precio_actual):
        """El Negociador: Engorda en el abismo y asegura botín con la regla 1.1/0.9."""
        for beru in self.legion:
            if beru.estado != "NEGOCIANDO":
                continue

            # ENGORDE: si el precio toca la Red Extrema/Adán
            toca_red = (beru.direccion == "SHORT" and precio_actual >= beru.red_adan) or \
                       (beru.direccion == "LONG" and precio_actual <= beru.red_adan)

            if toca_red:
                masa_extra = beru.masa * 0.001
                if await self.tusk.solicitar_reserva(f"E_{beru.uid}", masa_extra, "BERU", beru.direccion):
                    beru.masa += masa_extra
                    beru.red_adan *= (1.001 if beru.direccion == "SHORT" else 0.999)
                    await self.bel.anotar("BERU", "ENGORDE", f"{beru.uid} inyectado 0.1%.")

            # NEGOCIADOR: rastreo de ganancia máxima desde el centro
            if beru.direccion == "SHORT":
                ganancia = (beru.centro_local - precio_actual) / beru.centro_local
            else:
                ganancia = (precio_actual - beru.centro_local) / beru.centro_local

            if ganancia > beru.max_favor:
                beru.max_favor = ganancia

            if beru.max_favor >= 0.01:
                if beru.direccion == "SHORT":
                    factor_oz = 1 - (beru.max_favor - 0.011)
                else:
                    factor_oz = 1 + (beru.max_favor - 0.011)
                beru.oz_adan = beru.centro_local * factor_oz

                toca_oz = (beru.direccion == "SHORT" and precio_actual >= beru.oz_adan) or \
                          (beru.direccion == "LONG" and precio_actual <= beru.oz_adan)

                if toca_oz:
                    await self.ejecutar_cosecha_y_relevo(beru, precio_actual)

    # === SALIDA Y RELEVO (COSECHA) ===

    async def ejecutar_cosecha_y_relevo(self, beru_actual, precio_actual):
        """Inicia el fin del ciclo de vida y genera la siguiente generación."""
        uid_cosecha = f"COSECHA_{str(uuid.uuid4())[:4]}"

        deseo = IntencionAccion(
            prioridad=0, uid=uid_cosecha, general="BERU", tipo="COSECHA",
            masa=beru_actual.masa, barco_ref=beru_actual
        )
        await self.greed.altar.put(deseo)
        beru_actual.estado = "ESPERANDO_SUELTA"

        nuevo_uid = f"BERU_GEN_{beru_actual.generacion + 1}_{int(time.time())}"

        masa_fresca = self.tusk.masa_autorizada
        if masa_fresca > 0 and await self.tusk.solicitar_reserva(nuevo_uid, masa_fresca, "BERU", beru_actual.direccion):
            beru_nuevo = BeruShip(
                uid=nuevo_uid, centro_local=precio_actual, masa=masa_fresca,
                direccion=beru_actual.direccion, estado="ACECHANDO",
                generacion=beru_actual.generacion + 1, adn_capitan=self.tank.capitan_activo
            )
            self.legion.append(beru_nuevo)

    # === OPTIMIZACIÓN Y FUSIÓN ===

    async def evaluar_colisiones_y_fusion(self):
        """
        Fusión dual:
          Trigger 1 — Contacto: precio toca el centro de un Beru → ese Beru absorbe
                      a todos los que están "peor" que él (más arriba para LONG,
                      más abajo para SHORT). Bola de nieve progresiva.
          Trigger 2 — Promedio: precio toca el promedio ponderado de la dirección →
                      fusiona solo los que están del lado perdedor del promedio.
        """
        precio = self.tusk.ultimo_precio
        activos = [b for b in self.legion if b.estado == "NEGOCIANDO"]
        if len(activos) < 2:
            return

        for direccion in ["LONG", "SHORT"]:
            grupo = [b for b in activos if b.direccion == direccion]
            if len(grupo) < 2:
                continue

            # --- TRIGGER 1: Fusión por contacto (bola de nieve) ---
            # Para LONGs: precio baja y toca un centro → ese + todos los de ARRIBA
            # Para SHORTs: precio sube y toca un centro → ese + todos los de ABAJO
            tocado = None
            for b in grupo:
                if abs(precio - b.centro_local) / max(b.centro_local, 0.0001) < 0.0005:
                    tocado = b
                    break

            if tocado:
                if direccion == "LONG":
                    victimas = [b for b in grupo if b.centro_local >= tocado.centro_local and b is not tocado]
                else:
                    victimas = [b for b in grupo if b.centro_local <= tocado.centro_local and b is not tocado]

                if victimas:
                    todos = [tocado] + victimas
                    masa_total = sum(b.masa for b in todos)
                    p_promedio = sum(b.centro_local * b.masa for b in todos) / masa_total

                    tocado.masa = masa_total
                    tocado.centro_local = p_promedio
                    tocado.max_favor = 0.0
                    tocado.es_super_beru = True

                    for b in victimas:
                        b.estado = "FUSIONADO"

                    await self.bel.anotar(
                        "BERU", "FUSION_CONTACTO",
                        f"{tocado.uid} absorbe {len(victimas)} barcos @ {p_promedio:.2f}"
                    )
                continue

            # --- TRIGGER 2: Fusión por promedio (red de seguridad) ---
            masa_total = sum(b.masa for b in grupo)
            p_promedio = sum(b.centro_local * b.masa for b in grupo) / masa_total

            if abs(precio - p_promedio) / max(p_promedio, 0.0001) < 0.0005:
                if direccion == "LONG":
                    perdedores = [b for b in grupo if b.centro_local >= p_promedio]
                else:
                    perdedores = [b for b in grupo if b.centro_local <= p_promedio]

                if len(perdedores) < 2:
                    continue

                lider = perdedores[0]
                masa_fusionada = sum(b.masa for b in perdedores)
                p_fusionado = sum(b.centro_local * b.masa for b in perdedores) / masa_fusionada

                lider.masa = masa_fusionada
                lider.centro_local = p_fusionado
                lider.max_favor = 0.0
                lider.es_super_beru = True

                for b in perdedores[1:]:
                    b.estado = "FUSIONADO"

                await self.bel.anotar(
                    "BERU", "SUPER_FUSION",
                    f"{lider.uid} absorbe {len(perdedores)-1} perdedores @ {p_fusionado:.2f}"
                )

    # === LIMPIEZA DE LEGIÓN ===

    def limpiar_legion(self):
        """Expurga barcos muertos: COSECHADO, FUSIONADO, ESPERANDO_SUELTA confirmados."""
        self.legion = [
            b for b in self.legion
            if b.estado not in ("COSECHADO", "FUSIONADO", "ESPERANDO_SUELTA")
        ]
