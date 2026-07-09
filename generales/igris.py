import asyncio
import time
import uuid

from core import mercado
from core import igris_manto as im
from core.manto_touch import limpiar_toques_expirados, rebalanceo_en_pausa_por_greed
import core.config as config


class IgrisEscudo:
    def __init__(self, tusk, beru, bridge=None):
        """
        Igris: El Escudo — dueño del manto (derivados).
        Decide maniobra y frente; ejecuta vía Bridge directamente.
        """
        self.tusk = tusk
        self.beru = beru
        self.tank = beru.tank
        self.bridge = bridge
        self.bel = beru.bel

        self.ultimo_movimiento = time.time()
        self.cooldown_maniobra_s = 5.0

    def calcular_banda_delta(self):
        return mercado.calcular_banda_delta(self.tusk.margen_ocupado)

    async def vigilar_manto_operativo(self):
        print(f"[IGRIS] Vigilancia activa bajo protocolo {config.FASE_ACTUAL}.")
        while True:
            _, estado = await self.tank.vision_especulativa()
            if estado != "ROJO":
                await self.auditar_manto_global()
            await asyncio.sleep(1)

    async def auditar_manto_global(self):
        limpiar_toques_expirados(self.tusk)
        margen_actual = self.tusk.margen_ocupado
        peso_l_total = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s_total = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l_total + peso_s_total
        en_cooldown = (time.time() - self.ultimo_movimiento) <= self.cooldown_maniobra_s

        if margen_actual >= config.MURO_LEY_MARCIAL:
            await self.bel.anotar("IGRIS", "LEY_MARCIAL", f"Margen Crítico: {margen_actual}%.")
            dir_poda = "LONG" if peso_l_total >= peso_s_total else "SHORT"
            await self._ejecutar_maniobra("PODAR_MANTO", dir_poda, masa_bruta * 0.15)
            return

        if margen_actual > config.RANGO_LIMPIEZA_MAX and peso_l_total > 0 and peso_s_total > 0:
            masa_espejo = min(peso_l_total, peso_s_total, self.tusk.masa_autorizada * 2)
            await self.bel.anotar("IGRIS", "LIMPIEZA", f"Margen {margen_actual}%. Reduciendo masa bruta.")
            await self._ejecutar_maniobra("LIMPIAR_ESPEJOS", "AMBAS", masa_espejo)
            return

        if en_cooldown:
            return

        # 3.5.2 — Bootstrap: primer par L/S cuando no hay manto
        if masa_bruta == 0 and margen_actual < config.RANGO_PISO_IDEAL:
            await self._bootstrap_manto()
            return

        if masa_bruta > 0 and not rebalanceo_en_pausa_por_greed(self.tusk):
            ratio_l = peso_l_total / masa_bruta
            banda_min, banda_max = self.calcular_banda_delta()
            if ratio_l > banda_max:
                await self.bel.anotar("IGRIS", "REBALANCEO", f"Delta {ratio_l*100:.1f}% > banda {banda_max*100:.1f}%")
                await self._ejecutar_maniobra("REBALANCEO_IGRIS", "SHORT", self.tusk.masa_autorizada)
                return
            if ratio_l < banda_min:
                await self.bel.anotar("IGRIS", "REBALANCEO", f"Delta {ratio_l*100:.1f}% < banda {banda_min*100:.1f}%")
                await self._ejecutar_maniobra("REBALANCEO_IGRIS", "LONG", self.tusk.masa_autorizada)
                return

        if margen_actual < config.RANGO_EXPANSION_MIN:
            dir_engorde = "LONG" if peso_l_total <= peso_s_total else "SHORT"
            await self._ejecutar_maniobra("ENGORDAR_MANTO", dir_engorde, self.tusk.masa_autorizada)

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

    async def _bootstrap_manto(self):
        """Primer par L/S — inverse LONG + lineal SHORT (doctrina §E)."""
        masa_pata = self.tusk.masa_autorizada * config.BOOTSTRAP_MANTO_FRACCION
        if masa_pata <= 0:
            return

        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map or estado in ("GLITCH_DETECTADO", "ROJO"):
            return

        ok, mot = im.bootstrap_viable(ctx_map)
        if not ok:
            return

        frente_l, frente_s = im.frentes_bootstrap()
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

    async def _engorde(self, uid, direccion, masa, ctx_map):
        margen = self.tusk.margen_ocupado
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())

        nuevo_l = peso_l + (masa if direccion == "LONG" else 0)
        nuevo_s = peso_s + (masa if direccion == "SHORT" else 0)

        if mercado.verificar_delta_post_maniobra(margen, nuevo_l, nuevo_s):
            mejor_f, precio = await self._radar_manto(ctx_map, masa, direccion == "LONG")
            pf = self.tusk.pesos.get(mejor_f, {"long": 0.0, "short": 0.0})
            fl = pf["long"] + (masa if direccion == "LONG" else 0)
            fs = pf["short"] + (masa if direccion == "SHORT" else 0)
            if mercado.verificar_delta_frente(margen, mejor_f, fl, fs):
                if await self._materializar_en_frente(uid, mejor_f, direccion, masa, precio):
                    await self.bel.anotar("IGRIS", "ENGORDE", f"+{masa:.4f} {direccion} en {mejor_f}")
                    return True

        mitad = masa * 0.5
        mejor_f_l, precio_l = await self._radar_manto(ctx_map, mitad, True)
        mejor_f_s, precio_s = await self._radar_manto(ctx_map, mitad, False)
        if mercado.verificar_delta_post_maniobra(margen, peso_l + mitad, peso_s + mitad):
            pf_l = self.tusk.pesos.get(mejor_f_l, {"long": 0.0, "short": 0.0})
            pf_s = self.tusk.pesos.get(mejor_f_s, {"long": 0.0, "short": 0.0})
            ok_l = mercado.verificar_delta_frente(margen, mejor_f_l, pf_l["long"] + mitad, pf_l["short"])
            ok_s = mercado.verificar_delta_frente(margen, mejor_f_s, pf_s["long"], pf_s["short"] + mitad)
            if ok_l and ok_s:
                if await self._materializar_en_frente(uid, mejor_f_l, "LONG", mitad, precio_l):
                    uid_s = f"{uid}_S"
                    if await self.tusk.solicitar_reserva(uid_s, mitad, "IGRIS", "SHORT"):
                        if await self._materializar_en_frente(uid_s, mejor_f_s, "SHORT", mitad, precio_s):
                            await self.bel.anotar("IGRIS", "ENGORDE_DUAL", f"+{mitad:.4f} L/S en {mejor_f_l}/{mejor_f_s}")
                            return True
                    await self.tusk.liberar_reserva(uid_s)

        await self.bel.anotar("IGRIS", "ENGORDE_BLOQUEADO", "Banda no permite crecer")
        return False
