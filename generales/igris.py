import asyncio
import time
import uuid

from core import mercado
from core import igris_manto as im
from core import beru_capital as bc
from core import manto_jurisdiccion as mj
from core.manto_touch import limpiar_toques_expirados, rebalanceo_en_pausa_por_greed
import core.config as config


class IgrisEscudo:
    def __init__(self, tusk, tank, bellion, bridge=None, greed=None):
        """
        Igris: El Escudo — orquestador del manto.
        Ejecuta solo hasta zona ideal 85–90%; luego YIELD a Greed.
        """
        self.tusk = tusk
        self.tank = tank
        self.bridge = bridge
        self.bel = bellion
        self.greed = greed

        self.ultimo_movimiento = time.time()
        self.cooldown_maniobra_s = 5.0
        self._ultimo_log_engorde_bloqueado = 0.0
        self._engorde_fail_until = 0.0

        self._capital_pre_vuelo = 0.0
        self._rango_progresion: str | None = None
        self._ejecucion_directa_activa = True  # False = yield a Greed

    def calcular_banda_delta(self):
        return mercado.calcular_banda_delta(self.tusk.margen_ocupado)

    def masa_paso_engorde(self) -> float:
        """Paso de engorde: preferir doblar el manto actual; techo = fracción de masa auth."""
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l + peso_s
        masa_auth = float(self.tusk.masa_autorizada)
        fraccion = float(getattr(config, "ENGORDE_PASO_FRACCION", 0.05))
        paso_min = float(getattr(config, "ENGORDE_PASO_MIN", 0.1))
        techo = max(masa_auth * fraccion, paso_min)
        if masa_bruta > 0:
            # Doblar el escudo actual (L+S), sin saltar al techo de un golpe
            return min(techo, max(masa_bruta, paso_min))
        return min(masa_auth, techo)

    async def vigilar_manto_operativo(self):
        print(f"[IGRIS] Vigilancia activa bajo protocolo {config.FASE_ACTUAL}.")
        while True:
            _, estado = await self.tank.vision_especulativa()
            if estado != "ROJO":
                await self.auditar_manto_global()
            await asyncio.sleep(1)

    async def auditar_manto_global(self):
        if not await self._auditoria_pre_despliegue():
            return

        limpiar_toques_expirados(self.tusk)
        margen_actual = float(self.tusk.margen_ocupado)
        peso_l_total = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s_total = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l_total + peso_s_total
        en_cooldown = (time.time() - self.ultimo_movimiento) <= self.cooldown_maniobra_s
        if time.time() < self._engorde_fail_until:
            en_cooldown = True

        # --- Jurisdicción: si ya cedió a Greed, Igris NO ejecuta en exchange ---
        if (
            mj.igris_yield_activo()
            and mj.greed_es_ejecutor()
            and (self.tusk.manto_cedido_a_greed or not self._ejecucion_directa_activa)
        ):
            if mj.bajo_piso(margen_actual):
                mj.emitir_orden_manto(
                    self.tusk,
                    mj.ORDEN_RESTAURAR_MANTO,
                    margen=margen_actual,
                    meta_min=mj.piso_ideal(),
                    meta_max=mj.muro_marcial(),
                )
                await self.bel.anotar(
                    "IGRIS", "ORDEN_GREED",
                    f"Restaurar manto a 85–95% (actual {margen_actual:.1f}%) — sin tocar exchange.",
                )
            elif mj.sobre_muro(margen_actual):
                mj.emitir_orden_manto(
                    self.tusk, mj.ORDEN_PODA_EMERGENCIA, margen=margen_actual,
                )
                await self.bel.anotar(
                    "IGRIS", "ORDEN_GREED",
                    f"Poda emergencia ≥95% (actual {margen_actual:.1f}%) — delegado a Greed.",
                )
            return

        # Bootstrap siempre es orquestación de Igris (aún sin manto)
        if masa_bruta == 0 and margen_actual < mj.piso_ideal():
            await self._bootstrap_manto()
            return

        if en_cooldown:
            return

        # Llevar manto a zona ideal 85–90%
        if margen_actual < mj.piso_ideal():
            if masa_bruta > 0 and not rebalanceo_en_pausa_por_greed(self.tusk):
                ratio_l = peso_l_total / masa_bruta
                banda_min, banda_max = self.calcular_banda_delta()
                if ratio_l > banda_max:
                    await self.bel.anotar("IGRIS", "REBALANCEO", f"Delta {ratio_l*100:.1f}% > banda")
                    await self._ejecutar_maniobra("REBALANCEO_IGRIS", "SHORT", self.tusk.masa_autorizada)
                    return
                if ratio_l < banda_min:
                    await self.bel.anotar("IGRIS", "REBALANCEO", f"Delta {ratio_l*100:.1f}% < banda")
                    await self._ejecutar_maniobra("REBALANCEO_IGRIS", "LONG", self.tusk.masa_autorizada)
                    return
            dir_engorde = "LONG" if peso_l_total <= peso_s_total else "SHORT"
            await self._ejecutar_maniobra("ENGORDAR_MANTO", dir_engorde, self.masa_paso_engorde())
            return

        # Entró en zona ideal → YIELD a Greed
        if mj.en_zona_ideal(margen_actual) and mj.igris_yield_activo() and mj.greed_es_ejecutor():
            self._ejecucion_directa_activa = False
            self.tusk.manto_cedido_a_greed = True
            await self.bel.anotar(
                "IGRIS", "YIELD_MANTO",
                f"Margen {margen_actual:.1f}% en zona 85–90% — ejecución cedida a Greed.",
            )
            return

        # Sin Greed ejecutor: comportamiento legacy acotado (no podar ≥95 aquí si Greed on)
        if not mj.greed_es_ejecutor():
            if margen_actual >= config.MURO_LEY_MARCIAL:
                await self.bel.anotar("IGRIS", "LEY_MARCIAL", f"Margen Crítico: {margen_actual}%.")
                dir_poda = "LONG" if peso_l_total >= peso_s_total else "SHORT"
                await self._ejecutar_maniobra("PODAR_MANTO", dir_poda, masa_bruta * 0.15)
                return
            if margen_actual > config.RANGO_LIMPIEZA_MAX and peso_l_total > 0 and peso_s_total > 0:
                masa_espejo = min(peso_l_total, peso_s_total, self.tusk.masa_autorizada * 2)
                await self._ejecutar_maniobra("LIMPIAR_ESPEJOS", "AMBAS", masa_espejo)

    async def _radar_manto(self, ctx_map, masa, is_long):
        return mercado.escanear_mejor_precio(config.FRENTES_MANTO_ALL, ctx_map, masa, is_long)

    async def _materializar_en_frente(self, uid, frente, direccion, masa, precio_fill: float = 0.0):
        """Orden real (live) o confirmación simulada en Tusk."""
        if not config.MODO_SIMULACION and self.bridge:
            side = "Buy" if direccion == "LONG" else "Sell"
            sym = mercado.frente_a_symbol(frente)
            cat = mercado.frente_a_category(frente)
            res = await self.bridge.place_order(sym, side, masa, category=cat)
            if not res.exito:
                await self.tusk.liberar_reserva(uid)
                await self.bel.anotar("IGRIS", "ORDEN_FALLIDA", f"{frente} {direccion}: {res.mensaje}")
                return False
            fill = await self.bridge.esperar_fill(sym, order_id=res.order_id, category=cat)
            if not fill.exito:
                await self.tusk.liberar_reserva(uid)
                return False
            px = float(getattr(fill, "precio", 0) or getattr(fill, "avg_price", 0) or precio_fill or 0)
            await self.tusk.confirmar_reserva(uid, frente, direccion, fill_confirmado=True, precio_fill=px)
        else:
            await self.tusk.confirmar_reserva(
                uid, frente, direccion, precio_fill=precio_fill if precio_fill > 0 else None,
            )
        return True

    async def _auditoria_pre_despliegue(self) -> bool:
        """Candado de bóveda — umbrales dinámicos desde motor X/A_base."""
        capital = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        self._capital_pre_vuelo = capital
        res = bc.resolver_activo_y_grado(capital)
        grado = res.get("grado", "BLOQUEADO")
        mapa = {
            "BLOQUEADO": "BLOQUEADO",
            "SOLDADO": "ASPIRANTE",
            "CAPITAN": "CAPITAN",
            "GENERAL": "GENERAL",
            "MARISCAL": "MARISCAL",
        }
        self._rango_progresion = mapa.get(grado, "BLOQUEADO")
        if grado == "BLOQUEADO":
            return False
        return True

    async def _asegurar_apalancamiento_aspirante_eth(self) -> bool:
        """Ejecución: apalancamiento MÁXIMO por contrato (no promedio)."""
        if config.MODO_SIMULACION or not self.bridge:
            return True

        pares = (
            ("ETHUSD", "inverse", bc.apalancamiento_inverse_max("ETH")),
            ("ETHUSDT", "linear", bc.apalancamiento_linear_max("ETH")),
        )
        for sym, cat, lev in pares:
            res = await self.bridge.set_leverage(sym, lev, category=cat)
            if not res.exito:
                await self.bel.anotar(
                    "IGRIS", "LEVERAGE_FALLIDO",
                    f"No se pudo fijar {lev}x en {sym} ({cat}): {res.mensaje}",
                )
                return False
        return True

    async def _bootstrap_manto(self):
        """Primer par L/S — inverse LONG + lineal SHORT (doctrina §E)."""
        if not await self._auditoria_pre_despliegue():
            return

        rango = self._rango_progresion

        if rango == "CAPITAN":
            # TODO: [Monarca] — Lógica de sizing y despliegue de unidades ($26–$50.99)
            return
        if rango == "GENERAL":
            # TODO: [Monarca] — Lógica de sizing y despliegue de unidades ($51–$100.99)
            return
        if rango == "MARISCAL":
            # TODO: [Monarca] — Lógica de sizing y despliegue de unidades (≥ $101)
            return

        if rango != "ASPIRANTE":
            return

        # Fase 1 — Aspirante: ETH forzado, ignora TICKER_BASE
        frente_l, frente_s = "ETHUSD_INVERSE", "ETHUSDT_LINEAL"

        if not await self._asegurar_apalancamiento_aspirante_eth():
            return

        # TODO: [Monarca] — Lógica de sizing Aspirante ($12.5–$25.99) a refinar
        masa_pata = self.tusk.masa_autorizada * config.BOOTSTRAP_MANTO_FRACCION
        if masa_pata <= 0:
            return

        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map or estado in ("GLITCH_DETECTADO", "ROJO"):
            return

        ok, mot = im.bootstrap_viable(ctx_map, "ETH")
        if not ok:
            return

        precio_l = im.precio_ctx(ctx_map, frente_l)
        precio_s = im.precio_ctx(ctx_map, frente_s)

        uid_l = f"IGRIS_BOOT_L_{str(uuid.uuid4())[:4]}"
        uid_s = f"IGRIS_BOOT_S_{str(uuid.uuid4())[:4]}"

        if not await self.tusk.solicitar_reserva(uid_l, masa_pata, "IGRIS", "LONG"):
            return
        if not await self._materializar_en_frente(uid_l, frente_l, "LONG", masa_pata, precio_l):
            return

        if not await self.tusk.solicitar_reserva(uid_s, masa_pata, "IGRIS", "SHORT"):
            return
        if await self._materializar_en_frente(uid_s, frente_s, "SHORT", masa_pata, precio_s):
            self.ultimo_movimiento = time.time()
            await self.bel.anotar(
                "IGRIS", "BOOTSTRAP_MANTO",
                f"Escudo §E L {frente_l} / S {frente_s} · {masa_pata:.4f} c/u",
            )

    async def _ejecutar_maniobra(self, tipo, direccion, masa_req):
        if masa_req <= 0:
            return

        uid = f"IGRIS_{tipo}_{str(uuid.uuid4())[:4]}"
        if tipo not in ("PODAR_MANTO", "LIMPIAR_ESPEJOS"):
            if not await self.tusk.solicitar_reserva(uid, masa_req, "IGRIS", direccion):
                return

        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map or estado in ("GLITCH_DETECTADO", "ROJO"):
            if tipo not in ("PODAR_MANTO", "LIMPIAR_ESPEJOS"):
                await self.tusk.liberar_reserva(uid)
            return

        ok = False
        if tipo == "PODAR_MANTO":
            ok = await self._poda(uid, direccion, masa_req, ctx_map)
        elif tipo == "LIMPIAR_ESPEJOS":
            ok = await self._espejos(uid, masa_req, ctx_map)
        elif tipo == "REBALANCEO_IGRIS":
            ok = await self._rebalanceo(uid, direccion, masa_req, ctx_map)
        elif tipo == "ENGORDAR_MANTO":
            ok = await self._engorde(uid, direccion, masa_req, ctx_map)

        if ok:
            self.ultimo_movimiento = time.time()
        elif tipo not in ("PODAR_MANTO", "LIMPIAR_ESPEJOS"):
            await self.tusk.liberar_reserva(uid)

    async def _poda(self, uid, direccion, masa, ctx_map):
        dir_key = "long" if direccion == "LONG" else "short"
        frentes = {f: p[dir_key] for f, p in self.tusk.pesos.items() if p[dir_key] > 0}
        if not frentes:
            await self.tusk.liberar_reserva(uid)
            return False

        frente = max(frentes, key=frentes.get)
        extraida = min(masa, self.tusk.pesos[frente][dir_key])

        if not config.MODO_SIMULACION and self.bridge:
            side = "Sell" if dir_key == "long" else "Buy"
            sym = mercado.frente_a_symbol(frente)
            cat = mercado.frente_a_category(frente)
            res = await self.bridge.place_order(sym, side, extraida, category=cat)
            if not res.exito:
                await self.tusk.liberar_reserva(uid)
                return False
            fill = await self.bridge.esperar_fill(sym, order_id=res.order_id, category=cat)
            if not fill.exito:
                await self.tusk.liberar_reserva(uid)
                return False

        self.tusk.pesos[frente][dir_key] -= extraida
        await self.tusk.liberar_reserva(uid)
        await self.bel.anotar("IGRIS", "PODA", f"Extirpados {extraida:.4f} de {frente}")
        return True

    async def _espejos(self, uid, masa, ctx_map):
        m_l = max(self.tusk.pesos, key=lambda f: self.tusk.pesos[f]["long"])
        m_s = max(self.tusk.pesos, key=lambda f: self.tusk.pesos[f]["short"])
        lim_l = min(masa, self.tusk.pesos[m_l]["long"])
        lim_s = min(masa, self.tusk.pesos[m_s]["short"])

        if not config.MODO_SIMULACION and self.bridge:
            sym_l, cat_l = mercado.frente_a_symbol(m_l), mercado.frente_a_category(m_l)
            sym_s, cat_s = mercado.frente_a_symbol(m_s), mercado.frente_a_category(m_s)
            res_l = await self.bridge.place_order(sym_l, "Sell", lim_l, category=cat_l)
            res_s = await self.bridge.place_order(sym_s, "Buy", lim_s, category=cat_s)
            if not res_l.exito or not res_s.exito:
                await self.tusk.liberar_reserva(uid)
                return False
            await self.bridge.esperar_fill(sym_l, order_id=res_l.order_id, category=cat_l)
            await self.bridge.esperar_fill(sym_s, order_id=res_s.order_id, category=cat_s)

        self.tusk.pesos[m_l]["long"] -= lim_l
        self.tusk.pesos[m_s]["short"] -= lim_s
        await self.tusk.liberar_reserva(uid)
        await self.bel.anotar("IGRIS", "LIMPIEZA", f"Espejos reducidos: {min(lim_l, lim_s):.4f}")
        return True

    async def _rebalanceo(self, uid, direccion, masa, ctx_map):
        margen = self.tusk.margen_ocupado
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        dir_refuerzo = direccion
        dir_key_reducir = "short" if dir_refuerzo == "LONG" else "long"
        dir_reducir = "SHORT" if dir_refuerzo == "LONG" else "LONG"

        frentes_pesados = {f: p[dir_key_reducir] for f, p in self.tusk.pesos.items() if p[dir_key_reducir] > 0}
        masa_aplicada = 0.0

        if frentes_pesados:
            frente_g = max(frentes_pesados, key=frentes_pesados.get)
            masa_red = min(masa * 0.5, frentes_pesados[frente_g])
            nuevo_l = peso_l - (masa_red if dir_key_reducir == "long" else 0)
            nuevo_s = peso_s - (masa_red if dir_key_reducir == "short" else 0)
            if mercado.verificar_delta_post_maniobra(margen, nuevo_l, nuevo_s) and masa_red > 0:
                self.tusk.pesos[frente_g][dir_key_reducir] -= masa_red
                masa_aplicada += masa_red
                peso_l, peso_s = nuevo_l, nuevo_s
                await self.bel.anotar("IGRIS", "REBALANCEO_CORTE", f"Reducido {masa_red:.4f} {dir_reducir} de {frente_g}")

        masa_rest = masa - masa_aplicada
        mejor_f, precio = await self._radar_manto(ctx_map, masa_rest, dir_refuerzo == "LONG")
        if precio <= 0 or masa_rest <= 0:
            await self.tusk.liberar_reserva(uid)
            return masa_aplicada > 0

        nuevo_l = peso_l + (masa_rest if dir_refuerzo == "LONG" else 0)
        nuevo_s = peso_s + (masa_rest if dir_refuerzo == "SHORT" else 0)
        if mercado.verificar_delta_post_maniobra(margen, nuevo_l, nuevo_s):
            if await self._materializar_en_frente(uid, mejor_f, dir_refuerzo, masa_rest, precio):
                await self.bel.anotar("IGRIS", "REBALANCEO_APERTURA", f"Abierto {masa_rest:.4f} {dir_refuerzo} en {mejor_f}")
                return True

        await self.tusk.liberar_reserva(uid)
        return masa_aplicada > 0

    def _precio_ctx_o_reflejo(self, ctx_map, frente: str) -> float:
        """Precio del frente; si lineal está ciego, refleja inverse/spot del mismo activo."""
        ctx = ctx_map.get(frente) if ctx_map else None
        px = float(getattr(ctx, "last_price", 0) or 0) if ctx else 0.0
        if px > 0:
            return px
        asset = frente.split("_")[0].replace("USDT", "").replace("USDC", "").replace("USD", "")
        # Heurística: prefijos de activo en frentes tipo LTCUSDT / LTCUSD
        for f, c in (ctx_map or {}).items():
            if not c or float(getattr(c, "last_price", 0) or 0) <= 0:
                continue
            sym = str(getattr(c, "symbol", "") or f)
            if asset and asset in sym:
                return float(c.last_price)
        return 0.0

    def _frente_ancla_manto(self) -> str | None:
        """Frente donde ya hay peso — engorde dual debe crecer ahí, no saltar de activo."""
        mejor, masa = None, 0.0
        for f, p in self.tusk.pesos.items():
            m = float(p.get("long", 0) or 0) + float(p.get("short", 0) or 0)
            if m > masa:
                mejor, masa = f, m
        return mejor if masa > 0 else None

    async def _engorde(self, uid, direccion, masa, ctx_map):
        margen = self.tusk.margen_ocupado
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l + peso_s
        motivo = "desconocido"

        # Bajo el piso ideal y manto equilibrado → dual L/S en el mismo frente
        banda_min, banda_max = mercado.calcular_banda_delta(margen)
        ratio = (peso_l / masa_bruta) if masa_bruta > 0 else 0.5
        priorizar_dual = masa_bruta > 0 and banda_min <= ratio <= banda_max and margen < mj.piso_ideal()

        if not priorizar_dual:
            nuevo_l = peso_l + (masa if direccion == "LONG" else 0)
            nuevo_s = peso_s + (masa if direccion == "SHORT" else 0)
            if mercado.verificar_delta_post_maniobra(margen, nuevo_l, nuevo_s):
                mejor_f, precio = await self._radar_manto(ctx_map, masa, direccion == "LONG")
                if precio <= 0:
                    motivo = "sin precio radar"
                else:
                    pf = self.tusk.pesos.get(mejor_f, {"long": 0.0, "short": 0.0})
                    fl = pf["long"] + (masa if direccion == "LONG" else 0)
                    fs = pf["short"] + (masa if direccion == "SHORT" else 0)
                    if mercado.verificar_delta_frente(margen, mejor_f, fl, fs):
                        if await self._materializar_en_frente(uid, mejor_f, direccion, masa, precio):
                            await self.bel.anotar("IGRIS", "ENGORDE", f"+{masa:.4f} {direccion} en {mejor_f}")
                            return True
                        motivo = "materializar unilateral falló"
                    else:
                        motivo = "banda frente unilateral"
            else:
                motivo = "banda global unilateral"

        mitad = masa * 0.5
        ancla = self._frente_ancla_manto()
        mejor_f_l, precio_l = await self._radar_manto(ctx_map, mitad, True)
        mejor_f_s, precio_s = await self._radar_manto(ctx_map, mitad, False)
        # Forzar mismo frente: ancla del manto o el mejor long (evita L en LTC y S en BTC)
        frente_dual = ancla or mejor_f_l or mejor_f_s
        if frente_dual:
            px = self._precio_ctx_o_reflejo(ctx_map, frente_dual)
            if px <= 0:
                px = precio_l if precio_l > 0 else precio_s
            precio_l = precio_s = px
            mejor_f_l = mejor_f_s = frente_dual

        if precio_l <= 0 or precio_s <= 0:
            motivo = "sin precio para dual (lineal ciego; esperando mar)"
        elif not mercado.verificar_delta_post_maniobra(margen, peso_l + mitad, peso_s + mitad):
            motivo = "banda global dual"
        else:
            pf = self.tusk.pesos.get(mejor_f_l, {"long": 0.0, "short": 0.0})
            ok_frentes = mercado.verificar_delta_frente(
                margen, mejor_f_l, pf["long"] + mitad, pf["short"] + mitad,
            )
            if not ok_frentes:
                motivo = f"banda frente dual ({mejor_f_l})"
            else:
                # Reserva original era masa completa: partir en dos mitades reales
                await self.tusk.liberar_reserva(uid)
                if not await self.tusk.solicitar_reserva(uid, mitad, "IGRIS", "LONG"):
                    motivo = "reserva L dual"
                elif await self._materializar_en_frente(uid, mejor_f_l, "LONG", mitad, precio_l):
                    uid_s = f"{uid}_S"
                    if await self.tusk.solicitar_reserva(uid_s, mitad, "IGRIS", "SHORT"):
                        if await self._materializar_en_frente(uid_s, mejor_f_s, "SHORT", mitad, precio_s):
                            await self.bel.anotar(
                                "IGRIS", "ENGORDE_DUAL",
                                f"+{mitad:.4f} L/S en {mejor_f_l}",
                            )
                            return True
                        motivo = "materializar S dual"
                    else:
                        motivo = "reserva S dual"
                        await self.tusk.liberar_reserva(uid_s)
                else:
                    motivo = "materializar L dual"

        # Fallo: cooldown largo + log con causa real (no martillar el panel)
        fail_cd = float(getattr(config, "ENGORDE_FAIL_COOLDOWN_S", 30.0))
        self.ultimo_movimiento = time.time()
        self._engorde_fail_until = time.time() + fail_cd
        log_cd = float(getattr(config, "ENGORDE_BLOQUEADO_LOG_S", 60.0))
        ahora = time.time()
        if ahora - self._ultimo_log_engorde_bloqueado >= log_cd:
            self._ultimo_log_engorde_bloqueado = ahora
            await self.bel.anotar(
                "IGRIS", "ENGORDE_BLOQUEADO",
                f"{motivo} (margen {margen:.2f}% · paso {masa:.4f})",
            )
        return False
