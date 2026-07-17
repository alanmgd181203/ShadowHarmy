import asyncio
import uuid
import time

from core.models import BeruShip
from core import mercado
from core import beru_tier
from core import beru_rail
from core import beru_cazador
from core import beru_negociador
from core import beru_fusion
from core import beru_mega_reset
from core import beru_residual
import core.config as config


class BeruCazador:
    def __init__(self, tusk, bellion, tank, bridge=None, kaiser=None):
        """
        Beru: El Cazador — dueño de la casa (spot).
        Decide frente stable (USDT/USDC/…), ejecuta CAZA/COSECHA vía Bridge.
        """
        self.tusk = tusk
        self.bel = bellion
        self.tank = tank
        self.bridge = bridge
        self.kaiser = kaiser
        self.legion = []
        self._redes_residuales: list[beru_residual.RedResidual] = []

    def _tier_efectivo(self) -> str:
        tid = getattr(self.tusk, "tier_beru_aplicado", None)
        if tid:
            return str(tid)
        return str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))

    def _tier_barco(self, beru: BeruShip) -> beru_tier.BeruGridTier:
        tid = getattr(beru, "tier_id", None) or self._tier_efectivo()
        return beru_tier.tier_por_id(tid)

    def _modo_barco(self, beru: BeruShip) -> beru_tier.ModoCombate:
        m = getattr(beru, "modo_combate", None) or getattr(config, "BERU_MODO_COMBATE_DEFAULT", "NEGOCIADOR")
        return "CAZA" if str(m).upper() == "CAZA" else "NEGOCIADOR"

    def _precio_casa(self):
        """Beru acecha en spot; si no hay spot aún, usa perp como respaldo."""
        if self.tusk.precio_spot > 0:
            return self.tusk.precio_spot
        return self.tusk.ultimo_precio

    # === PULSO VITAL Y GENERACIÓN ===

    async def hilo_beru_berserker(self):
        while True:
            precio = self._precio_casa()
            if precio <= 0.0:
                await asyncio.sleep(0.01)
                continue

            if any(getattr(b, "ciclo_infinito", False) for b in self.legion):
                pass
            elif not any(
                b.estado in ("ACECHANDO", "ESPERANDO_CONDICIONAL", "ESPERANDO_ABISMO")
                for b in self.legion
            ):
                self.plantar_semilla_adan(precio)

            await self.auditar_gatillos_adan(precio)
            await self.sincronizar_materializacion()
            await self.ejecutar_acordeon_asimetrico(precio)
            await self.evaluar_colisiones_y_fusion()
            self.limpiar_legion()
            await asyncio.sleep(0.01)

    def _centro_cazador(self, beru: BeruShip | None = None) -> float:
        if beru and beru.centro_manto > 0:
            return beru.centro_manto
        return beru_cazador.centro_manto_desde_tusk(self.tusk)

    def _siguiente_capa(self, direccion: str) -> int:
        numeradas = [
            b.capa for b in self.legion
            if b.direccion == direccion
            and b.estado not in ("FUSIONADO", "ACECHANDO")
        ]
        return max(numeradas, default=0) + 1

    def _aplicar_grid_cazador(self, beru: BeruShip, touch_pct: float) -> None:
        centro = self._centro_cazador(beru)
        beru.centro_manto = centro
        tier = self._tier_barco(beru)
        paso_oz, _ = tier.pasos("CAZA")
        beru.oz_pct, beru.red_pct = beru_cazador.niveles_desde_toque(
            touch_pct, paso_oz=paso_oz, paso_red_clon=tier.distancia_clon_pct,
        )
        beru.oz_adan, beru.red_adan = beru_cazador.sincronizar_precios_grid(
            centro, beru.oz_pct, beru.red_pct,
        )

    def _registrar_red_residual(self, beru: BeruShip) -> None:
        red = float(beru.red_adan or 0)
        if red <= 0 and beru.centro_manto > 0:
            _, red = beru_cazador.sincronizar_precios_grid(
                beru.centro_manto, beru.oz_pct, beru.red_pct,
            )
        rr = beru_residual.registrar_desde_barco(beru, red)
        if rr:
            self._redes_residuales.append(rr)

    def plantar_semilla_adan(self, precio_actual):
        nuevo_uid = f"BERU_SEM_{str(getattr(config, 'BERU_ACTIVO_SEMILLA', '') or 'X')}_{time.time_ns()}"
        semilla = BeruShip(
            uid=nuevo_uid, centro_local=precio_actual, masa=0.0,
            direccion="LONG", estado="ACECHANDO", generacion=1,
            adn_capitan=self.tank.capitan_activo,
            tier_id=self._tier_efectivo(),
            modo_combate=str(getattr(config, "BERU_MODO_COMBATE_DEFAULT", "NEGOCIADOR")),
            centro_manto=beru_cazador.centro_manto_desde_tusk(self.tusk),
        )
        self.legion.append(semilla)

    # === ACECHO Y CAZA (EJECUCIÓN DIRECTA) ===

    async def auditar_gatillos_adan(self, precio_actual):
        for beru in self.legion:
            if beru.estado != "ACECHANDO":
                continue
            if self._modo_barco(beru) == "CAZA":
                await self._auditar_gatillo_cazador(beru, precio_actual)
            else:
                await self._auditar_gatillo_negociador(beru, precio_actual)

    async def _auditar_gatillo_cazador(self, beru: BeruShip, precio_actual: float):
        """Gatillo ±vacío/2 desde el 0 del manto (no desde semilla)."""
        centro = self._centro_cazador(beru)
        if centro <= 0:
            return
        touch_pct = beru_cazador.pct_desde_precio(centro, precio_actual)
        if abs(touch_pct) < 0.0005:
            return
        vacio = beru.adn_capitan.vacio_adan
        if not beru_cazador.distancia_gatillo_cumplida(touch_pct, vacio):
            return
        if any(
            b.estado in ("NEGOCIANDO", "ESPERANDO_MATERIALIZACION")
            and b.direccion == ("SHORT" if touch_pct > 0 else "LONG")
            and b.capa == 1
            and self._modo_barco(b) == "CAZA"
            for b in self.legion
        ):
            return

        masa_fresca = beru_cazador.capa1_masa_usd(self.tusk.masa_autorizada)
        if masa_fresca <= 0.0:
            return

        beru.direccion = "SHORT" if touch_pct > 0 else "LONG"
        beru.capa = 1
        beru.estado = "ESPERANDO_MATERIALIZACION"
        self._aplicar_grid_cazador(beru, touch_pct)

        if await self.tusk.solicitar_reserva(beru.uid, masa_fresca, "BERU", beru.direccion):
            beru.masa = masa_fresca
            await self._ejecutar_caza(beru)

    async def _auditar_gatillo_negociador(self, beru: BeruShip, precio_actual: float):
        distancia = (precio_actual - beru.centro_local) / max(beru.centro_local, 0.0001)
        if abs(distancia) < 0.0005:
            return
        if abs(distancia) < beru.adn_capitan.vacio_adan:
            return

        masa_fresca = self.tusk.masa_autorizada
        if masa_fresca <= 0.0:
            return

        beru.direccion = "SHORT" if distancia > 0 else "LONG"
        beru.estado = "ESPERANDO_MATERIALIZACION"

        if await self.tusk.solicitar_reserva(beru.uid, masa_fresca, "BERU", beru.direccion):
            beru.masa = masa_fresca
            tier = self._tier_barco(beru)
            paso_oz, paso_red = tier.pasos("NEGOCIADOR")
            beru.red_adan, beru.oz_adan = beru_tier.precios_red_oz(
                beru.centro_local, beru.direccion,
                paso_oz=paso_oz, paso_red=paso_red,
            )
            await self._ejecutar_caza(beru)

    async def _radar_casa(self, ctx_map, masa, is_long):
        lider = self.tank._obtener_lider_verde()
        libros = (lider.libros if lider else {}) or {}
        frente, p_ef, meta = beru_rail.elegir_mejor_rail(
            ctx_map, masa, is_long,
            libros=libros,
            kaiser=self.kaiser,
        )
        if meta.get("candidatos", 0) > 1:
            await self.bel.anotar(
                "BERU", "RAIL_ELEGIDO",
                f"{frente} ({meta.get('candidatos')} stables) fee~{meta.get('fee_pct', 0):.2f}%",
            )
        return frente, p_ef

    async def _ejecutar_caza(self, beru):
        ctx_map, estado = await self.tank.vision_especulativa()
        if estado in ("GLITCH_DETECTADO", "ROJO") or not ctx_map:
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ACECHANDO"
            return

        is_long = beru.direccion == "LONG"
        mejor_f, p_ef = await self._radar_casa(ctx_map, beru.masa, is_long)
        if p_ef <= 0:
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ACECHANDO"
            return

        margen = self.tusk.margen_ocupado
        pesos_f = self.tusk.pesos.get(mejor_f, {"long": 0.0, "short": 0.0})
        nuevo_l = pesos_f["long"] + (beru.masa if is_long else 0)
        nuevo_s = pesos_f["short"] + (beru.masa if not is_long else 0)
        if not mercado.verificar_delta_frente(margen, mejor_f, nuevo_l, nuevo_s):
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ACECHANDO"
            await self.bel.anotar("BERU", "CAZA_BLOQUEADA", f"Banda de {mejor_f} no permite {beru.direccion}")
            return

        categoria = mercado.frente_a_category(mejor_f)
        symbol = mercado.frente_a_symbol(mejor_f)

        if not config.MODO_SIMULACION and self.bridge:
            side = "Buy" if is_long else "Sell"
            # Spot: Long = USD (quoteCoin); Short margen = monedas base (= masa_usd / precio)
            market_unit = None
            qty_orden = beru.masa
            is_lev = None
            if categoria == "spot":
                if getattr(config, "BERU_SPOT_MARGEN_ENABLED", False) or getattr(
                    config, "LIVE_BERU_TESTNET", False
                ):
                    is_lev = 1
                if is_long:
                    market_unit = "quoteCoin"
                    qty_orden = beru.masa
                else:
                    # Short spot: qty en base; masa doctrinal es USD
                    px = float(p_ef) if p_ef and p_ef > 0 else 0.0
                    qty_orden = (beru.masa / px) if px > 0 else beru.masa
            resultado = await self.bridge.place_order(
                symbol, side, qty_orden, category=categoria,
                market_unit=market_unit, is_leverage=is_lev,
            )
            if not resultado.exito:
                await self.tusk.liberar_reserva(beru.uid)
                beru.estado = "ACECHANDO"
                await self.bel.anotar("BERU", "CAZA_ORDEN_FALLIDA", resultado.mensaje)
                return
            fill = await self.bridge.esperar_fill(symbol, order_id=resultado.order_id, category=categoria)
            if not fill.exito:
                await self.tusk.liberar_reserva(beru.uid)
                beru.estado = "ACECHANDO"
                return
            p_ef = fill.datos.get("avgPrice", p_ef)
            qty_base = float(fill.datos.get("cumExecQty") or 0)
            if qty_base > 0:
                beru.qty_base_ejecutada = qty_base
            await self.tusk.confirmar_reserva(
                beru.uid, mejor_f, beru.direccion, fill_confirmado=True, precio_fill=p_ef,
            )
        else:
            await self.tusk.confirmar_reserva(beru.uid, mejor_f, beru.direccion)

        beru.frente_asignado = mejor_f
        beru.precio_entrada_real = p_ef
        beru.estado = "NEGOCIANDO"
        await self.bel.anotar("BERU", "CAZA", f"Anclado en {mejor_f} @ {p_ef:.2f}")

    async def sincronizar_materializacion(self):
        for beru in self.legion:
            if beru.estado == "NEGOCIANDO" and not beru.sincronizado and beru.precio_entrada_real > 0:
                if self._modo_barco(beru) == "CAZA":
                    beru.centro_manto = self._centro_cazador(beru)
                else:
                    beru.centro_local = beru.precio_entrada_real
                beru.sincronizado = True
                await self.bel.anotar("BERU", "RESONANCIA", f"{beru.uid} sincronizado @ {beru.precio_entrada_real:.2f}")

    # === COMBATE ACTIVO (ACORDEÓN) ===

    async def ejecutar_acordeon_asimetrico(self, precio_actual):
        await self._pulsar_clonacion_residual(precio_actual)
        await self._acordeon_cazador_capas(precio_actual)
        await self._pulsar_negociador_post_cazador(precio_actual)
        for beru in self.legion:
            if beru.estado != "NEGOCIANDO":
                continue
            if self._modo_barco(beru) == "CAZA":
                continue
            if getattr(beru, "neg_post_cazador", False) or getattr(beru, "ciclo_infinito", False):
                continue
            await self._acordeon_negociador_legacy(beru, precio_actual)

    async def _pulsar_negociador_post_cazador(self, precio_actual: float):
        for beru in self.legion:
            if not getattr(beru, "ciclo_infinito", False):
                continue
            centro = beru.centro_manto or beru_cazador.centro_manto_desde_tusk(self.tusk)
            if centro <= 0:
                continue
            paso_oz, paso_red = beru_negociador.pasos_negociador(
                getattr(beru, "tier_id", None) or self._tier_efectivo(),
            )
            vacio = beru.adn_capitan.vacio_adan

            if beru.estado == "ESPERANDO_ABISMO":
                # Reciclaje: espera recompra +2% con vacío Adán (sin orden en exchange)
                if beru.fase_reciclaje == "ESPERANDO_RECOMPRA" and beru.trigger_recompra > 0:
                    trig = beru.trigger_recompra
                    if not beru.bracket_armado:
                        if not beru_negociador.precio_cerca_de_trigger(precio_actual, trig):
                            continue
                        beru.bracket_armado = True
                        await self.bel.anotar(
                            "BERU", "ADAN_RECOMPRA",
                            f"{beru.uid} cerca de recompra {trig:.4f} — armado en memoria.",
                        )
                    if not beru_negociador.toca_trigger_precio(
                        precio_actual, trig, beru.direccion, modo="RECOMPRA",
                    ):
                        continue
                    # Recompra mismo volumen — sin engorde
                    beru.masa = beru.volumen_reciclaje or beru.masa_congelada
                    touch_pct = beru_cazador.pct_desde_precio(centro, precio_actual)
                    self._aplicar_grid_cazador(beru, touch_pct)
                    beru.modo_combate = "CAZA"
                    beru.estado = "NEGOCIANDO"
                    beru.fase_reciclaje = "RECICLANDO"
                    beru.bracket_armado = False
                    # Tras recompra, ancla salida −2% otra vez
                    if precio_actual > 0:
                        beru.precio_entrada_real = precio_actual
                        beru.trigger_salida = beru_negociador.trigger_salida_precio(
                            precio_actual, beru.direccion,
                        )
                    await self.bel.anotar(
                        "BERU", "RECOMPRA_RECICLO",
                        f"{beru.uid} @ {precio_actual:.4f} vol ${beru.masa:.2f} "
                        f"(sin engorde) · salida {beru.trigger_salida:.4f}.",
                    )
                    continue

                if not beru_negociador.cruzo_gatillo_caza(
                    precio_actual, centro, vacio, beru.direccion,
                ):
                    continue
                touch_pct = beru_cazador.pct_desde_precio(centro, precio_actual)
                self._aplicar_grid_cazador(beru, touch_pct)
                beru.modo_combate = "CAZA"
                beru.estado = "NEGOCIANDO"
                beru.masa = beru.masa_congelada
                await self.bel.anotar(
                    "BERU", "CAZA_FANTASMA",
                    f"{beru.uid} abismo cruzado @ {touch_pct*100:.2f}% "
                    f"oz {beru.oz_pct*100:.2f}% red {beru.red_pct*100:.2f}% "
                    f"(${beru.masa_congelada:.0f} sin engorde).",
                )
                continue

            if beru.estado == "ESPERANDO_CONDICIONAL":
                cond = beru_negociador.oz_condicional_pct(beru.ancla_cosecha_pct, vacio)
                beru.neg_oz_pct = cond
                # Vacío Adán: no armar bracket hasta estar a ≤0.5% del trigger −2%
                if not beru.bracket_armado:
                    if not beru_negociador.cerca_condicional(precio_actual, centro, cond):
                        continue
                    beru.bracket_armado = True
                    beru.fase_reciclaje = "ARMADO_ADAN"
                    await self.bel.anotar(
                        "BERU", "ADAN_ARMADO",
                        f"{beru.uid} precio cerca de cond {cond*100:.2f}% — bracket en memoria.",
                    )
                if not beru_negociador.toca_condicional(precio_actual, centro, cond):
                    continue
                oz_n, red_n = beru_negociador.activar_primera_vez(cond, paso_oz)
                beru.neg_oz_pct, beru.neg_red_pct = oz_n, red_n
                beru.oz_adan, beru.red_adan = beru_negociador.sincronizar_grid(centro, oz_n, red_n)
                beru.estado = "NEGOCIANDO"
                beru.modo_combate = "NEGOCIADOR"
                beru.neg_toques_ciclo = 0
                beru.fase_reciclaje = "NEGOCIANDO"
                await self.bel.anotar(
                    "BERU", "NEG_ACTIVADO",
                    f"{beru.uid} cond {cond*100:.2f}% → oz {oz_n*100:.2f}% red {red_n*100:.2f}%.",
                )
                continue

            if beru.estado != "NEGOCIANDO" or beru.modo_combate != "NEGOCIADOR":
                continue

            if beru.neg_red_pct != 0.0 and beru_negociador.toca_red_negociador(
                precio_actual, centro, beru.neg_red_pct,
            ):
                if beru_mega_reset.debe_resetear_por_red(beru):
                    await self._reset_mega_por_red(beru, precio_actual)
                else:
                    await self._flip_neg_a_caza(beru, precio_actual)
                continue

            if not beru_negociador.toca_oz_negociador(precio_actual, centro, beru.neg_oz_pct):
                continue

            if beru_negociador.es_sexto_toque(beru.neg_toques_ciclo):
                oz_n, red_n = beru_negociador.resorte_sexto_toque(beru.neg_oz_pct, paso_oz)
                beru.neg_toques_ciclo = 0
                await self.bel.anotar(
                    "BERU", "NEG_RESORTE",
                    f"{beru.uid} 6.º toque — oz {oz_n*100:.2f}% red {red_n*100:.2f}%.",
                )
            else:
                oz_n, red_n = beru_negociador.avanzar_toque_oz(
                    beru.neg_oz_pct, beru.neg_red_pct, paso_oz, paso_red,
                )
                beru.neg_toques_ciclo += 1
                await self.bel.anotar(
                    "BERU", "NEG_TOQUE",
                    f"{beru.uid} toque {beru.neg_toques_ciclo}/5 — oz {oz_n*100:.2f}% red {red_n*100:.2f}%.",
                )

            beru.neg_oz_pct, beru.neg_red_pct = oz_n, red_n
            beru.oz_adan, beru.red_adan = beru_negociador.sincronizar_grid(centro, oz_n, red_n)

    async def _reset_mega_por_red(self, beru: BeruShip, precio_actual: float):
        """Mega Beru: toque red → cosecha a bóveda + semilla nueva en el 0 local (masa 0)."""
        masa_suelta = float(beru.masa or beru.masa_congelada or 0)
        direccion = beru.direccion
        tier = getattr(beru, "tier_id", "") or self._tier_efectivo()
        generacion = beru.generacion + 1

        await self._soltar_mega_a_boveda(beru)

        nuevo_uid = f"BERU_MEGA0_{int(time.time())}"
        semilla = beru_mega_reset.crear_semilla_reinicio(
            precio_actual,
            direccion=direccion,
            tier_id=tier,
            adn_capitan=self.tank.capitan_activo,
            generacion=generacion,
            uid=nuevo_uid,
        )
        self.legion.append(semilla)
        await self.bel.anotar(
            "BERU", "MEGA_RESET",
            f"{beru.uid} red @ {precio_actual:.2f} → bóveda ${masa_suelta:.0f} · "
            f"nuevo 0 · {nuevo_uid} acecha (masa $0).",
        )

    async def _soltar_mega_a_boveda(self, beru: BeruShip):
        """Capital del Mega vuelve al margen cruzado (bóveda Tusk); sin reserva exclusiva."""
        masa = float(beru.masa or beru.masa_congelada or 0)
        if masa <= 0:
            beru.estado = "COSECHADO"
            return
        uid_cosecha = f"MEGA_SUELTA_{beru.uid}"
        beru.estado = "ESPERANDO_SUELTA"
        await self._ejecutar_cosecha(beru, uid_cosecha, forzar=True)
        if beru.estado == "COSECHADO":
            return
        if beru.uid in self.tusk.reservas_activas:
            await self.tusk.liberar_reserva(beru.uid)
        beru.masa = 0.0
        beru.masa_congelada = 0.0
        beru.estado = "COSECHADO"

    async def _flip_neg_a_caza(self, beru: BeruShip, precio_actual: float):
        """Red negociador tocada = oz cazador → esperar cruce de abismo hacia gatillo."""
        beru.estado = "ESPERANDO_ABISMO"
        beru.modo_combate = "CAZA"
        beru.neg_toques_ciclo = 0
        beru.neg_red_pct = 0.0
        beru.neg_oz_pct = 0.0
        await self.bel.anotar(
            "BERU", "VUELTA_CAZA",
            f"{beru.uid} red negociador tocada @ {precio_actual:.2f} — "
            f"recorriendo abismo (${beru.masa_congelada:.0f} fijos).",
        )

    async def _flip_caza_a_neg(self, beru: BeruShip, precio_actual: float):
        """Oz cazador tocada = red negociador → armar condicional al otro lado."""
        vacio = beru.adn_capitan.vacio_adan
        ancla = beru.oz_pct
        cond = beru_negociador.oz_condicional_pct(ancla, vacio)
        beru.ancla_cosecha_pct = ancla
        beru.neg_oz_pct = cond
        beru.neg_red_pct = 0.0
        beru.neg_toques_ciclo = 0
        beru.estado = "ESPERANDO_CONDICIONAL"
        beru.modo_combate = "NEGOCIADOR"
        beru.oz_pct = 0.0
        beru.red_pct = 0.0
        await self.bel.anotar(
            "BERU", "VUELTA_NEG",
            f"{beru.uid} oz cazador {ancla*100:.2f}% → condicional {cond*100:.2f}%.",
        )

    async def _pulsar_clonacion_residual(self, precio_actual: float):
        """Toque de red_residual → Capa N+1 con masa base ($5)."""
        for rr in list(self._redes_residuales):
            if not rr.activa:
                continue
            if not beru_residual.toca_residual(precio_actual, rr):
                continue
            rr.activa = False
            await self._parir_desde_residual(rr, precio_actual)

    async def _parir_desde_residual(self, residual: beru_residual.RedResidual, precio_actual: float):
        direccion = residual.direccion
        capa = self._siguiente_capa(direccion)
        centro = residual.centro_manto or beru_cazador.centro_manto_desde_tusk(self.tusk)
        if centro <= 0:
            return
        touch_pct = beru_cazador.pct_desde_precio(centro, precio_actual)
        masa = beru_cazador.mordida_usd()
        if masa <= 0:
            return
        nuevo_uid = f"BERU_CAPA{capa}_{str(getattr(config, 'BERU_ACTIVO_SEMILLA', '') or 'X')}_{time.time_ns()}"
        barco = BeruShip(
            uid=nuevo_uid,
            centro_local=precio_actual,
            centro_manto=centro,
            masa=masa,
            direccion=direccion,
            estado="ESPERANDO_MATERIALIZACION",
            generacion=1,
            adn_capitan=self.tank.capitan_activo,
            tier_id=residual.tier_id or self._tier_efectivo(),
            modo_combate="CAZA",
            capa=capa,
        )
        self._aplicar_grid_cazador(barco, touch_pct)
        if not await self.tusk.solicitar_reserva(nuevo_uid, masa, "BERU", direccion):
            residual.activa = True
            return
        await self._ejecutar_caza(barco)
        if barco.estado == "NEGOCIANDO":
            self.legion.append(barco)
            await self.bel.anotar(
                "BERU", "CLON_RESIDUAL",
                f"{nuevo_uid} capa{capa} @ red_residual {residual.precio:.2f} (${masa:.0f}).",
            )

    async def _acordeon_cazador_capas(self, precio_actual: float):
        for beru in self.legion:
            if beru.estado != "NEGOCIANDO" or self._modo_barco(beru) != "CAZA":
                continue

            if getattr(beru, "ciclo_infinito", False):
                if beru_cazador.toca_oz(precio_actual, beru.direccion, beru.oz_adan):
                    await self._flip_caza_a_neg(beru, precio_actual)
                continue

            if beru_cazador.toca_oz(precio_actual, beru.direccion, beru.oz_adan):
                await self._cosecha_capa_cazador(beru, precio_actual)
                continue

            if beru_cazador.toca_red(precio_actual, beru.direccion, beru.red_adan):
                if not beru_cazador.es_frontera_red(beru, self.legion, self._modo_barco):
                    continue
                # Bloqueo de sizing en reciclaje — solo excepciones A/B
                if getattr(beru, "engorde_bloqueado", False):
                    if self._puede_desbloquear_engorde(beru, precio_actual):
                        beru.engorde_bloqueado = False
                        await self.bel.anotar(
                            "BERU", "ENGORDE_DESBLOQUEADO",
                            f"{beru.uid} red extrema o fusión — permiso de engorde restaurado.",
                        )
                    else:
                        continue
                masa_extra = beru_cazador.mordida_usd()
                if await self.tusk.solicitar_reserva(f"E_{beru.uid}", masa_extra, "BERU", beru.direccion):
                    beru.masa += masa_extra
                    beru.oz_pct, beru.red_pct = beru_cazador.mover_niveles_cazador(
                        beru.direccion, beru.oz_pct, beru.red_pct,
                    )
                    c = beru.centro_manto or self._centro_cazador(beru)
                    beru.oz_adan, beru.red_adan = beru_cazador.sincronizar_precios_grid(
                        c, beru.oz_pct, beru.red_pct,
                    )
                    if beru.red_adan:
                        beru.red_extrema = beru.red_adan
                    await self.bel.anotar(
                        "BERU", "ENGORDE_FRONTERA",
                        f"{beru.uid} capa{beru.capa} red+oz +0.1% (+${masa_extra:.0f}).",
                    )

    def _puede_desbloquear_engorde(self, beru: BeruShip, precio_actual: float) -> bool:
        """Excepción A: red más extrema. B: toque precio Beru fusionado (reset 0)."""
        red_ext = float(getattr(beru, "red_extrema", 0) or beru.red_adan or 0)
        if red_ext > 0 and beru_cazador.toca_red(precio_actual, beru.direccion, red_ext):
            return True
        ref = float(getattr(beru, "precio_fusion_ref", 0) or 0)
        if ref > 0 and abs(precio_actual - ref) / ref <= 0.0001:
            beru.centro_manto = precio_actual
            beru.centro_local = precio_actual
            return True
        # Super Beru fusionado en legión como referencia de reset
        for b in self.legion:
            if not getattr(b, "es_super_beru", False):
                continue
            if b.estado in ("FUSIONADO", "COSECHADO"):
                continue
            px = float(b.oz_adan or b.centro_local or 0)
            if px > 0 and abs(precio_actual - px) / px <= 0.0001:
                beru.centro_manto = precio_actual
                beru.centro_local = precio_actual
                return True
        return False

    async def _iniciar_reciclaje_post_venta(self, beru: BeruShip, precio_venta: float):
        """Tras venta total: nuevo 0 = precio venta; recompra +2%; mismo volumen; sin engorde."""
        vol = float(beru.masa_congelada or beru.volumen_reciclaje or beru.masa or 0)
        if vol <= 0:
            return
        beru.centro_local = precio_venta
        beru.centro_manto = precio_venta
        beru.volumen_reciclaje = vol
        beru.masa_congelada = vol
        beru.masa = vol
        beru.engorde_bloqueado = True
        beru.ciclo_infinito = True
        beru.bracket_armado = False
        beru.trigger_recompra = beru_negociador.trigger_recompra_precio(
            precio_venta, beru.direccion,
        )
        # Ancla de recompra en % desde el nuevo 0
        ancla = beru_cazador.pct_desde_precio(precio_venta, beru.trigger_recompra)
        beru.ancla_cosecha_pct = ancla
        # Condicional de "caza reciclaje" = tocar +2%; luego salida otra vez −2%
        beru.neg_oz_pct = ancla
        beru.neg_red_pct = 0.0
        beru.estado = "ESPERANDO_ABISMO"
        beru.modo_combate = "CAZA"
        beru.fase_reciclaje = "ESPERANDO_RECOMPRA"
        await self.bel.anotar(
            "BERU", "RECICLAJE",
            f"{beru.uid} nuevo 0 @ {precio_venta:.4f} · recompra "
            f"{beru.trigger_recompra:.4f} (+2%) · vol ${vol:.2f} sin engorde.",
        )

    async def _cosecha_capa_cazador(self, beru: BeruShip, precio_actual: float):
        self._registrar_red_residual(beru)
        if beru.red_adan:
            beru.red_extrema = max(float(beru.red_extrema or 0), float(beru.red_adan))
        if beru.capa <= 1:
            ancla = beru.oz_pct
            centro = beru.centro_manto or self._centro_cazador(beru)
            masa_gel = beru.masa
            # Trigger salida −2% desde ancla de caza (en memoria, no en exchange)
            if beru.precio_entrada_real > 0:
                beru.trigger_salida = beru_negociador.trigger_salida_precio(
                    beru.precio_entrada_real, beru.direccion,
                )
            await self.ejecutar_cosecha_y_relevo(
                beru, precio_actual,
                relevo_modo="NEGOCIADOR",
                ancla_cosecha_pct=ancla,
                centro_manto=centro,
                masa_congelada=masa_gel,
            )
            return
        uid_cosecha = f"COSECHA_{str(uuid.uuid4())[:4]}"
        beru.estado = "ESPERANDO_SUELTA"
        await self._ejecutar_cosecha(beru, uid_cosecha)
        if beru.estado == "COSECHADO":
            await self.bel.anotar(
                "BERU", "COSECHA_CAPA",
                f"Capa {beru.capa} cosechada — red_residual {beru.red_adan:.2f} en memoria.",
            )
            # Reciclaje: si tenía volumen congelado / bloqueo, reinicia ciclo
            if getattr(beru, "engorde_bloqueado", False) or beru.volumen_reciclaje > 0:
                px = float(beru.precio_salida_real or precio_actual)
                await self._iniciar_reciclaje_post_venta(beru, px)

    async def _acordeon_negociador_legacy(self, beru: BeruShip, precio_actual: float):
        toca_red = (
            (beru.direccion == "SHORT" and precio_actual >= beru.red_adan)
            or (beru.direccion == "LONG" and precio_actual <= beru.red_adan)
        )
        if toca_red:
            masa_extra = beru.masa * 0.001
            if await self.tusk.solicitar_reserva(f"E_{beru.uid}", masa_extra, "BERU", beru.direccion):
                beru.masa += masa_extra
                tier = self._tier_barco(beru)
                _, paso_red = tier.pasos("NEGOCIADOR")
                beru.red_adan = beru_tier.mover_red(beru.red_adan, beru.direccion, paso_red)
                if tier.id == "BERUBBY" and tier.oz_tras_toque_red:
                    beru.oz_adan = beru_tier.oz_berubby_tras_toque_red(
                        beru.centro_local, beru.direccion, tier.oz_tras_toque_red,
                    )
                await self.bel.anotar(
                    "BERU", "ENGORDE",
                    f"{beru.uid} red +{paso_red*100:.2f}% (NEGOCIADOR).",
                )

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
            toca_oz = (
                (beru.direccion == "SHORT" and precio_actual >= beru.oz_adan)
                or (beru.direccion == "LONG" and precio_actual <= beru.oz_adan)
            )
            if toca_oz:
                await self.ejecutar_cosecha_y_relevo(beru, precio_actual)

    # === COSECHA (EJECUCIÓN DIRECTA) ===

    async def ejecutar_cosecha_y_relevo(
        self,
        beru_actual,
        precio_actual,
        relevo_modo: str | None = None,
        ancla_cosecha_pct: float | None = None,
        centro_manto: float | None = None,
        masa_congelada: float | None = None,
    ):
        uid_cosecha = f"COSECHA_{str(uuid.uuid4())[:4]}"
        beru_actual.estado = "ESPERANDO_SUELTA"
        await self._ejecutar_cosecha(beru_actual, uid_cosecha)

        if relevo_modo == "NEGOCIADOR" and ancla_cosecha_pct is not None:
            await self._crear_negociador_post_cazador(
                beru_actual, precio_actual, ancla_cosecha_pct, centro_manto,
                masa_congelada=masa_congelada or beru_actual.masa,
            )
            return

        modo_relevo = relevo_modo or getattr(beru_actual, "modo_combate", "") or str(
            getattr(config, "BERU_MODO_COMBATE_DEFAULT", "NEGOCIADOR")
        )
        nuevo_uid = f"BERU_GEN_{beru_actual.generacion + 1}_{int(time.time())}"
        masa_fresca = self.tusk.masa_autorizada
        if masa_fresca > 0 and await self.tusk.solicitar_reserva(
            nuevo_uid, masa_fresca, "BERU", beru_actual.direccion
        ):
            self.legion.append(BeruShip(
                uid=nuevo_uid, centro_local=precio_actual, masa=masa_fresca,
                direccion=beru_actual.direccion, estado="ACECHANDO",
                generacion=beru_actual.generacion + 1, adn_capitan=self.tank.capitan_activo,
                tier_id=getattr(beru_actual, "tier_id", "") or self._tier_efectivo(),
                modo_combate=modo_relevo,
                centro_manto=beru_cazador.centro_manto_desde_tusk(self.tusk),
            ))

    async def _crear_negociador_post_cazador(
        self,
        beru_cazador_ref: BeruShip,
        precio_actual: float,
        ancla_pct: float,
        centro_manto: float | None,
        masa_congelada: float = 0.0,
    ):
        centro = centro_manto or beru_cazador.centro_manto_desde_tusk(self.tusk)
        vacio = beru_cazador_ref.adn_capitan.vacio_adan
        cond = beru_negociador.oz_condicional_pct(ancla_pct, vacio)
        nuevo_uid = f"BERU_NEG_{int(time.time())}"
        self.legion.append(BeruShip(
            uid=nuevo_uid,
            centro_local=precio_actual,
            centro_manto=centro,
            masa=masa_congelada,
            masa_congelada=masa_congelada,
            direccion=beru_cazador_ref.direccion,
            estado="ESPERANDO_CONDICIONAL",
            generacion=beru_cazador_ref.generacion + 1,
            adn_capitan=self.tank.capitan_activo,
            tier_id=getattr(beru_cazador_ref, "tier_id", "") or self._tier_efectivo(),
            modo_combate="NEGOCIADOR",
            neg_post_cazador=True,
            ciclo_infinito=True,
            engorde_bloqueado=True,
            volumen_reciclaje=masa_congelada,
            bracket_armado=False,
            ancla_cosecha_pct=ancla_pct,
            neg_oz_pct=cond,
            trigger_salida=getattr(beru_cazador_ref, "trigger_salida", 0.0) or 0.0,
            red_extrema=float(getattr(beru_cazador_ref, "red_extrema", 0) or beru_cazador_ref.red_adan or 0),
            fase_reciclaje="ESPERANDO_SALIDA",
        ))
        await self.bel.anotar(
            "BERU", "CICLO_INFINITO",
            f"Ancla {ancla_pct*100:.2f}% -> cond −2% @ {cond*100:.2f}% "
            f"(${masa_congelada:.0f} congelados, Adán en memoria, sin engorde).",
        )

    async def _ejecutar_cosecha(self, barco, uid_cosecha, forzar: bool = False):
        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map or estado in ("GLITCH_DETECTADO", "ROJO"):
            barco.estado = "NEGOCIANDO" if not forzar else "ESPERANDO_SUELTA"
            return

        is_long_cosecha = barco.direccion != "LONG"
        mejor_f, p_ef = await self._radar_casa(ctx_map, barco.masa, is_long_cosecha)

        beneficio = (
            abs(p_ef - barco.precio_entrada_real) / barco.precio_entrada_real
            if barco.precio_entrada_real > 0 else 0
        )
        if not forzar and beneficio < config.UMBRAL_COSECHA_MIN:
            barco.estado = "NEGOCIANDO"
            await self.bel.anotar("BERU", "PACIENCIA", f"Beneficio {beneficio*100:.2f}% insuficiente.")
            return

        if not await self.tusk.solicitar_reserva(
            uid_cosecha, barco.masa, "BERU", "LONG" if is_long_cosecha else "SHORT"
        ):
            barco.estado = "NEGOCIANDO"
            return

        categoria = mercado.frente_a_category(mejor_f)
        symbol = mercado.frente_a_symbol(mejor_f)

        if not config.MODO_SIMULACION and self.bridge:
            side = "Sell" if barco.direccion == "LONG" else "Buy"
            market_unit = "quoteCoin" if categoria == "spot" and barco.direccion != "LONG" else None
            qty_orden = barco.masa
            is_lev = None
            if categoria == "spot":
                if getattr(config, "BERU_SPOT_MARGEN_ENABLED", False) or getattr(
                    config, "LIVE_BERU_TESTNET", False
                ):
                    is_lev = 1
                if barco.direccion == "LONG":
                    qty_orden = float(getattr(barco, "qty_base_ejecutada", 0) or 0)
                    if qty_orden <= 0 and barco.precio_entrada_real > 0:
                        qty_orden = barco.masa / barco.precio_entrada_real
                else:
                    # Cerrar short: recomprar en quote USD
                    market_unit = "quoteCoin"
                    qty_orden = barco.masa
            resultado = await self.bridge.place_order(
                symbol, side, qty_orden, category=categoria,
                market_unit=market_unit, is_leverage=is_lev,
            )
            if not resultado.exito:
                await self.tusk.liberar_reserva(uid_cosecha)
                barco.estado = "NEGOCIANDO"
                return
            fill = await self.bridge.esperar_fill(symbol, order_id=resultado.order_id, category=categoria)
            if not fill.exito:
                await self.tusk.liberar_reserva(uid_cosecha)
                barco.estado = "NEGOCIANDO"
                return
            p_ef = fill.datos.get("avgPrice", p_ef)

        await self.tusk.consumar_cosecha_atomica(uid_cosecha, mejor_f, barco)
        barco.frente_salida = mejor_f
        barco.precio_salida_real = p_ef
        barco.estado = "COSECHADO"
        await self.bel.anotar("BERU", "COSECHA", f"Botín asegurado @ {beneficio*100:.2f}%")
        if getattr(barco, "ciclo_infinito", False) or getattr(barco, "engorde_bloqueado", False):
            await self._iniciar_reciclaje_post_venta(barco, float(p_ef or 0))

    async def _fusion_negociadores_ciclo(self):
        """Colisión estricta oz_adan + Mega Beru (sagrado)."""
        for grupo in beru_fusion.grupos_colision_oz(self.legion):
            lider, victimas = beru_fusion.fusionar_colision_oz(grupo)
            centro = lider.centro_manto or beru_cazador.centro_manto_desde_tusk(self.tusk)
            if centro > 0:
                if self._modo_barco(lider) == "NEGOCIADOR":
                    lider.oz_adan, lider.red_adan = beru_negociador.sincronizar_grid(
                        centro, lider.neg_oz_pct, lider.neg_red_pct,
                    )
                else:
                    lider.oz_adan, lider.red_adan = beru_cazador.sincronizar_precios_grid(
                        centro, lider.oz_pct, lider.red_pct,
                    )
            for v in victimas:
                v.estado = "FUSIONADO"
            lider.engorde_bloqueado = True
            lider.volumen_reciclaje = float(lider.masa_congelada or lider.masa or 0)
            lider.precio_fusion_ref = float(lider.oz_adan or 0)
            lider.es_super_beru = True
            tag = "NEG" if self._modo_barco(lider) == "NEGOCIADOR" else "CAZA"
            await self.bel.anotar(
                "BERU", "FUSION_COLISION",
                f"{lider.uid} <- {len(victimas) + 1} {tag} oz~{lider.oz_adan:.2f} "
                f"${lider.masa_congelada:.0f} (reciclaje volumen sumado).",
            )

        for lider, victimas, prom in beru_fusion.grupos_mega_beru(self.legion):
            vacio = lider.adn_capitan.vacio_adan
            beru_fusion.aplicar_mega_beru(lider, victimas, prom, vacio)
            for v in victimas:
                v.estado = "FUSIONADO"
            await self.bel.anotar(
                "BERU", "MEGA_BERU",
                f"{lider.uid} prom ancla {prom * 100:.2f}% <- {len(victimas) + 1} barcos "
                f"(${lider.masa_congelada:.0f}) · cond {lider.neg_oz_pct * 100:.2f}%.",
            )

    # === FUSIÓN Y LIMPIEZA ===

    async def evaluar_colisiones_y_fusion(self):
        await self._fusion_negociadores_ciclo()
        precio = self._precio_casa()
        activos = [
            b for b in self.legion
            if b.estado == "NEGOCIANDO"
            and self._modo_barco(b) != "CAZA"
            and not getattr(b, "neg_post_cazador", False)
            and not getattr(b, "ciclo_infinito", False)
        ]
        if len(activos) < 2:
            return

        for direccion in ["LONG", "SHORT"]:
            grupo = [b for b in activos if b.direccion == direccion]
            if len(grupo) < 2:
                continue

            tocado = None
            for b in grupo:
                if abs(precio - b.centro_local) / max(b.centro_local, 0.0001) < 0.0005:
                    tocado = b
                    break

            if tocado:
                victimas = (
                    [b for b in grupo if b.centro_local >= tocado.centro_local and b is not tocado]
                    if direccion == "LONG"
                    else [b for b in grupo if b.centro_local <= tocado.centro_local and b is not tocado]
                )
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
                    await self.bel.anotar("BERU", "FUSION_CONTACTO", f"{tocado.uid} absorbe {len(victimas)} barcos")
                continue

            masa_total = sum(b.masa for b in grupo)
            p_promedio = sum(b.centro_local * b.masa for b in grupo) / masa_total
            if abs(precio - p_promedio) / max(p_promedio, 0.0001) >= 0.0005:
                continue
            perdedores = (
                [b for b in grupo if b.centro_local >= p_promedio]
                if direccion == "LONG"
                else [b for b in grupo if b.centro_local <= p_promedio]
            )
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
            await self.bel.anotar("BERU", "SUPER_FUSION", f"{lider.uid} absorbe {len(perdedores)-1} perdedores")

    def limpiar_legion(self):
        self.legion = [
            b for b in self.legion
            if b.estado not in ("COSECHADO", "FUSIONADO", "ESPERANDO_SUELTA")
        ]
        self._redes_residuales = [r for r in self._redes_residuales if r.activa]

    def restaurar_legion(self, legion_data):
        """Recovery desde estado_hierro.json."""
        from generales.capitanes import CapitanCazador
        self.legion = []
        for item in legion_data or []:
            try:
                adn = item.get("adn_capitan")
                if isinstance(adn, dict):
                    from generales.capitanes import ADN_Capitan
                    adn = ADN_Capitan(**adn)
                else:
                    adn = CapitanCazador
                self.legion.append(BeruShip(
                    uid=item["uid"],
                    centro_local=item.get("centro_local", 0.0),
                    masa=item.get("masa", 0.0),
                    direccion=item.get("direccion", "LONG"),
                    estado=item.get("estado", "ACECHANDO"),
                    red_adan=item.get("red_adan", 0.0),
                    oz_adan=item.get("oz_adan", 0.0),
                    max_favor=item.get("max_favor", 0.0),
                    generacion=item.get("generacion", 1),
                    es_super_beru=item.get("es_super_beru", False),
                    frente_asignado=item.get("frente_asignado", "INDEFINIDO"),
                    precio_entrada_real=item.get("precio_entrada_real", 0.0),
                    sincronizado=item.get("sincronizado", False),
                    adn_capitan=adn,
                    tier_id=item.get("tier_id", ""),
                    modo_combate=item.get("modo_combate", ""),
                    centro_manto=item.get("centro_manto", 0.0),
                    oz_pct=item.get("oz_pct", 0.0),
                    red_pct=item.get("red_pct", 0.0),
                    capa=item.get("capa", 1),
                    neg_post_cazador=item.get("neg_post_cazador", False),
                    ancla_cosecha_pct=item.get("ancla_cosecha_pct", 0.0),
                    neg_oz_pct=item.get("neg_oz_pct", 0.0),
                    neg_red_pct=item.get("neg_red_pct", 0.0),
                    neg_toques_ciclo=item.get("neg_toques_ciclo", 0),
                    ciclo_infinito=item.get("ciclo_infinito", False),
                    masa_congelada=item.get("masa_congelada", 0.0),
                ))
            except (KeyError, TypeError):
                continue
