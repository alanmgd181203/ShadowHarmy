import asyncio
import time

from core import greed_mision as mision
from core import greed_vip as vip
from core import mercado
from core import manto_jurisdiccion as mj
import core.config as config
from core.manto_touch import registrar_toque_greed
from core import greed_basis as basis


class GreedFrancotirador:
    def __init__(self, tusk, bellion, tank_cluster, bridge=None, kaiser=None, igris=None):
        """
        Greed: francotirador de arbitraje / VIP / basis.
        El manto L/S es jurisdicción exclusiva de Igris (doctrina 2026-07-12).
        """
        self.tusk = tusk
        self.bel = bellion
        self.tank = tank_cluster
        self.bridge = bridge
        self.kaiser = kaiser
        self.igris = igris
        self._ultimo_disparo = 0.0
        self._ultimo_intento_oid: dict[str, float] = {}
        self._vip_estado: dict[str, dict] = {}
        self._basis_estado: dict[str, dict] = {}

    async def vigilancia_oportunidades(self):
        kaiser_on = getattr(config, "GREED_KAISER_ENABLED", True)
        msg = "Kaiser+Ancla+VIP" if kaiser_on and self.kaiser else "legacy/VIP"
        print(f"[GREED] Radar {msg} ({config.FASE_ACTUAL}) — sin jurisdicción de manto.")
        while True:
            try:
                # Drenar cola legado sin ejecutar (Igris ya no emite)
                mj.consumir_ordenes_manto(self.tusk)
                if kaiser_on and self.kaiser:
                    await self._radar_kaiser()
                elif getattr(config, "GREED_LEGACY_SQUAD_ENABLED", False):
                    await self._radar_escuadron_suicida()
            except Exception as e:
                await self.bel.anotar("GREED", "ERROR", f"Radar: {e}")
            intervalo = float(getattr(config, "GREED_LOOP_INTERVAL_S", 0))
            if intervalo > 0:
                await asyncio.sleep(intervalo)
            else:
                await asyncio.sleep(0)

    def _tank_semaforo(self) -> str:
        lider = self.tank._obtener_lider_verde()
        return lider.estado_foco if lider else "ROJO"

    def _abortadas_oids(self, slice_greed: dict) -> set[str]:
        out: set[str] = set()
        for ab in slice_greed.get("abortadas") or []:
            out.add(mision.oid_oportunidad(ab))
        return out

    def _limpiar_vip_abortadas(self, abort_oids: set[str]) -> None:
        for oid in list(self._vip_estado.keys()):
            if oid in abort_oids:
                del self._vip_estado[oid]

    async def _radar_kaiser(self):
        semaforo = self._tank_semaforo()
        equity = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0)
        pausa, _ = mision.vetos_globales(
            tank_semaforo=semaforo,
            margen_ocupado_pct=float(self.tusk.margen_ocupado),
            equity=equity,
        )
        if pausa:
            return

        slice_g = self.kaiser.consumir_greed()
        digest = self.kaiser.snapshot()
        vivas = slice_g.get("oportunidades_vivas") or []
        abort_oids = self._abortadas_oids(slice_g)
        self._limpiar_vip_abortadas(abort_oids)

        if not vivas and not self._vip_estado and not self._basis_estado:
            return

        await self._procesar_salidas_basis(vivas)

        cooldown = float(getattr(config, "GREED_REINTENTO_COOLDOWN_S", 2.0))
        ahora = time.time()

        planes = mision.planes_desde_kaiser(
            digest,
            vivas,
            equity=equity,
            margen_ocupado_pct=float(self.tusk.margen_ocupado),
            masa_autorizada=float(self.tusk.masa_autorizada),
            tank_semaforo=semaforo,
            abortadas_oids=abort_oids,
            vip_oids_activos=set(self._vip_estado.keys()),
        )
        oids_basis = set(self._basis_estado.keys())
        planes = [
            p for p in planes
            if not (p.get("es_basis") and p.get("oid") in oids_basis)
        ]
        if len(self._basis_estado) >= basis.max_holds_abiertos():
            planes = [p for p in planes if not p.get("es_basis")]
        margen = float(self.tusk.margen_ocupado)
        planes = mision.filtrar_planes_ley_marcial(
            planes, margen, vip_oids_activos=set(self._vip_estado.keys()),
        )

        # Continuar misiones VIP activas aunque no estén en top planes
        oids_en_planes = {p["oid"] for p in planes}
        for oid, estado in list(self._vip_estado.items()):
            if oid not in oids_en_planes and oid not in abort_oids:
                op = mision.op_viva_por_oid(vivas, oid)
                if op:
                    plan = mision.resolver_plan(
                        op, digest,
                        equity=equity,
                        margen_ocupado_pct=float(self.tusk.margen_ocupado),
                        masa_autorizada=float(self.tusk.masa_autorizada),
                        tank_semaforo=semaforo,
                    )
                    if plan.get("ok") and plan.get("es_vip"):
                        planes.insert(0, plan)

        if not planes:
            return

        # Ley marcial: sin planes VIP y sin estado VIP activo → radar inerte
        if margen >= float(getattr(config, "MURO_LEY_MARCIAL", 95.0)):
            if not self._vip_estado and not any(p.get("es_vip") for p in planes):
                return

        global_cd = float(getattr(config, "GREED_DISPARO_COOLDOWN_S", 1.0))
        if (ahora - self._ultimo_disparo) < global_cd:
            return

        max_int = int(getattr(config, "GREED_MAX_INTENTOS_POR_CICLO", 1))
        intentos = 0
        for plan in planes:
            if intentos >= max_int:
                break
            oid = plan["oid"]
            if (ahora - self._ultimo_intento_oid.get(oid, 0)) < cooldown:
                continue
            if plan.get("es_vip"):
                await self._ejecutar_plan_vip(plan, vivas)
            elif plan.get("modo") == "BASIS_HOLD" or plan.get("es_basis"):
                await self._ejecutar_entrada_basis(plan)
            else:
                await self._ejecutar_plan_normal(plan)
            self._ultimo_intento_oid[oid] = time.time()
            self._ultimo_disparo = time.time()
            intentos += 1

        self.tusk.greed_basis_abiertos = basis.resumen_holds(self._basis_estado)

    async def _procesar_salidas_basis(self, vivas: list[dict]):
        for oid, hold in list(self._basis_estado.items()):
            op = mision.op_basis_por_hold(hold, vivas)
            salir, motivo = basis.debe_salir_basis(hold, op)
            registrar_toque_greed(self.tusk, hold.get("frentes") or [], motivo="BASIS_HOLD")
            if not salir:
                continue
            await self._ejecutar_salida_basis(hold, motivo)
            self._basis_estado.pop(oid, None)

    async def _ejecutar_entrada_basis(self, plan: dict):
        if len(self._basis_estado) >= basis.max_holds_abiertos():
            return
        oid = plan["oid"]
        if oid in self._basis_estado:
            return
        notional = float(plan["notional_usd"])
        piernas = plan.get("piernas_entrada") or plan.get("piernas") or []
        if len(piernas) < 2:
            return
        uid = f"BASIS_IN_{plan['base']}_{int(time.time() * 1000)}"
        if not await self.tusk.solicitar_reserva(uid, notional, "GREED", "LONG"):
            return
        await self.bel.anotar(
            "GREED", "BASIS_ENTRADA",
            f"{plan['tipo_spread']} {plan['base']} ${notional:.2f} spread {plan.get('op', {}).get('spread_bruto_pct', 0):.2f}%",
        )
        sim = config.MODO_SIMULACION or not self.bridge
        ok = await self._ejecutar_piernas(uid, notional, piernas, simulado=sim, tag="BASIS_ENTRADA")
        if not ok:
            return
        hold = basis.crear_hold(plan, plan.get("op") or {})
        self._basis_estado[oid] = hold
        registrar_toque_greed(self.tusk, hold.get("frentes") or [], motivo="BASIS_HOLD")

    async def _ejecutar_salida_basis(self, hold: dict, motivo: str):
        notional = float(hold.get("notional_usd") or hold.get("deployed_usd") or 0)
        piernas = hold.get("piernas_salida") or []
        if not piernas or notional <= 0:
            return
        uid = f"BASIS_OUT_{hold['base']}_{int(time.time() * 1000)}"
        if not await self.tusk.solicitar_reserva(uid, notional, "GREED", "SHORT"):
            return
        spread_ent = float(hold.get("spread_entrada_pct") or 0)
        await self.bel.anotar(
            "GREED", "BASIS_SALIDA",
            f"{hold['tipo_spread']} {hold['base']} ${notional:.2f} | {motivo} | spread_ent {spread_ent:.2f}%",
        )
        sim = config.MODO_SIMULACION or not self.bridge
        await self._ejecutar_piernas(uid, notional, piernas, simulado=sim, tag="BASIS_SALIDA")

    async def _ejecutar_plan_normal(self, plan: dict):
        notional = float(plan["notional_usd"])
        piernas = plan.get("piernas") or (plan.get("op") or {}).get("piernas")
        base = plan["base"]
        tipo = plan["tipo_spread"]
        m = plan.get("mordida") or {}

        uid = f"GREED_{base}_{int(time.time() * 1000)}"
        if not await self.tusk.solicitar_reserva(uid, notional, "GREED", "LONG"):
            return

        if piernas and len(piernas) > 2:
            ruta = plan.get("via_quote") or plan.get("ruta_id") or tipo
            await self.bel.anotar(
                "GREED", "MISION_MULTICRUCE",
                f"{tipo} {base} via {ruta} ${notional:.2f} | "
                f"{len(piernas)} piernas | calor {m.get('calor', 0):.2f}",
            )
            sim = config.MODO_SIMULACION or not self.bridge
            await self._ejecutar_piernas(uid, notional, piernas, simulado=sim)
            return

        frente_buy = plan["frente_long"]
        frente_sell = plan["frente_short"]
        await self.bel.anotar(
            "GREED", "MISION_KAISER",
            f"{tipo} {base} ${notional:.2f} | calor {m.get('calor', 0):.2f} "
            f"frac {m.get('fraccion', 0):.2f} | buy:{frente_buy} sell:{frente_sell}",
        )
        sim = config.MODO_SIMULACION or not self.bridge
        await self._ejecutar_dos_piernas(uid, notional, frente_buy, frente_sell, simulado=sim)

    async def _ejecutar_plan_vip(self, plan: dict, vivas: list[dict]):
        oid = plan["oid"]
        op = mision.op_viva_por_oid(vivas, oid) or plan["op"]
        ruta = plan.get("ruta_idonea")
        neto = vip.neto_efectivo_ruta(op, ruta)

        if not vip.debe_continuar(neto):
            await self.bel.anotar(
                "GREED", "VIP_STOP",
                f"{oid} neto {neto:.2f}% < {vip.neto_continuar_min()}%",
            )
            self._vip_estado.pop(oid, None)
            return

        equity = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0)
        estado = self._vip_estado.get(oid)
        if not estado:
            estado = vip.crear_estado_vip(
                plan,
                equity=equity,
                margen_ocupado_pct=float(self.tusk.margen_ocupado),
            )
            self._vip_estado[oid] = estado
            await self.bel.anotar(
                "GREED", "VIP_INICIO",
                f"{estado['modo']} {oid} neto {neto:.2f}% techo ${estado['techo_vip_usd']:.2f}",
            )

        if not vip.puede_escalar(estado):
            return

        micro = vip.siguiente_micro_usd(estado)
        if micro <= 0:
            return

        base = estado["base"]
        frente_buy = estado["frente_buy"]
        frente_sell = estado["frente_sell"]
        uid = f"VIP_{base}_{estado['micros_total']}_{int(time.time() * 1000)}"

        if not await self.tusk.solicitar_reserva(uid, micro, "GREED", "LONG"):
            return

        sim = config.MODO_SIMULACION or not self.bridge
        ok = await self._ejecutar_dos_piernas(
            uid, micro, frente_buy, frente_sell, simulado=sim,
        )
        if not ok:
            await self.bel.anotar("GREED", "VIP_HUMO", f"{oid} micro falló — abort resto")
            self._vip_estado.pop(oid, None)
            return

        estado = vip.tras_fill_ok(estado, micro, neto)
        self._vip_estado[oid] = estado
        techo = vip.techo_activo(estado)
        tag = "MEGA" if estado.get("mega_desbloqueado") else estado["modo"]
        await self.bel.anotar(
            "GREED", "VIP_MICRO",
            f"{tag} {oid} +${micro:.2f} ({estado['sondas_ok']} sondas) "
            f"total ${estado['deployed_usd']:.2f}/{techo:.2f} neto {neto:.2f}%",
        )

        micros_ciclo = int(getattr(config, "GREED_VIP_MICROS_POR_CICLO", 1))
        if estado["sondas_ok"] < vip.sondas_requeridas() and micros_ciclo > 1:
            for _ in range(micros_ciclo - 1):
                if not vip.puede_escalar(estado) or not vip.debe_continuar(neto):
                    break
                await self._micro_vip_extra(estado, oid, neto, vivas)

    async def _micro_vip_extra(self, estado: dict, oid: str, neto: float, vivas: list[dict]):
        micro = vip.siguiente_micro_usd(estado)
        uid = f"VIP_{estado['base']}_{estado['micros_total']}_{int(time.time() * 1000)}"
        if not await self.tusk.solicitar_reserva(uid, micro, "GREED", "LONG"):
            return
        sim = config.MODO_SIMULACION or not self.bridge
        ok = await self._ejecutar_dos_piernas(
            uid, micro, estado["frente_buy"], estado["frente_sell"], simulado=sim,
        )
        if not ok:
            self._vip_estado.pop(oid, None)
            return
        self._vip_estado[oid] = vip.tras_fill_ok(estado, micro, neto)

    async def _radar_escuadron_suicida(self):
        """
        Legacy USDT×USDC solo pentiverso — DUPLICA Kaiser+matriz usdt_vs_usdc.
        Mantener APAGADO (GREED_LEGACY_SQUAD_ENABLED=false). No es Beru; es arbitraje Greed.
        """
        from core import greed_sizing as sizing

        ctx_map, estado = await self.tank.vision_especulativa()
        if estado != "VERDE_SEGURO" or not ctx_map:
            return

        regalo = mercado.escanear_mejor_regalo_usdt_usdc(ctx_map)
        if not regalo:
            return

        desviacion, f_usdt, f_usdc, p_usdt, p_usdc = regalo
        if desviacion < config.UMBRAL_REGALO_SQUAD:
            return
        equity = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0)
        lev = sizing.apalancamiento_ruta([f_usdt, f_usdc])
        cap_1pct = sizing.cap_notional_1pct_riesgo(equity, lev)
        masa_legacy = min(
            self.tusk.masa_autorizada * float(getattr(config, "GREED_SQUAD_MASA_FRACCION", 0.5)),
            cap_1pct,
        )
        if masa_legacy <= 0:
            return
        if (time.time() - self._ultimo_disparo) < config.GREED_SQUAD_COOLDOWN_S:
            return

        if p_usdc > p_usdt:
            frente_buy, frente_sell = f_usdt, f_usdc
        else:
            frente_buy, frente_sell = f_usdc, f_usdt

        uid = f"SUICIDE_{int(time.time())}"
        if not await self.tusk.solicitar_reserva(uid, masa_legacy, "GREED", "LONG"):
            return

        await self.bel.anotar(
            "GREED", "ESCUADRON_SUICIDA",
            f"USDT×USDC {frente_buy}↔{frente_sell} {desviacion*100:.2f}% | ${masa_legacy:.2f}",
        )
        sim = config.MODO_SIMULACION or not self.bridge
        await self._ejecutar_dos_piernas(uid, masa_legacy, frente_buy, frente_sell, simulado=sim)
        self._ultimo_disparo = time.time()

    async def _ejecutar_piernas(
        self,
        uid: str,
        masa: float,
        piernas: list[dict],
        *,
        simulado: bool = False,
        tag: str = "MULTICRUCE",
    ) -> bool:
        """Multicruce / basis Greed — piernas secuenciales."""
        if not piernas:
            return False
        notional_por_leg = masa / len(piernas)
        frentes_tocados: list[str] = []

        for i, leg in enumerate(piernas):
            frente = str(leg["frente"])
            side = str(leg.get("side", "Buy"))
            frentes_tocados.append(frente)
            leg_uid = uid if i == 0 else f"{uid}_L{i}"
            dir_res = "LONG" if side.upper() == "BUY" else "SHORT"

            if simulado:
                if i > 0:
                    if not await self.tusk.solicitar_reserva(leg_uid, notional_por_leg, "GREED", dir_res):
                        continue
                await self.tusk.confirmar_reserva(leg_uid, frente, dir_res)
                continue

            sym = mercado.frente_a_symbol(frente)
            cat = mercado.frente_a_category(frente)
            if i > 0:
                if not await self.tusk.solicitar_reserva(leg_uid, notional_por_leg, "GREED", dir_res):
                    await self.bel.anotar("GREED", "MULTICRUCE_ABORT", f"Pierna {i} sin reserva")
                    return False
            res = await self.bridge.place_order(sym, side, notional_por_leg, category=cat)
            if not res.exito:
                if i > 0:
                    await self.tusk.liberar_reserva(leg_uid)
                else:
                    await self.tusk.liberar_reserva(uid)
                await self.bel.anotar("GREED", "MULTICRUCE_ABORT", f"Pierna {i} rechazada: {res.mensaje}")
                return False
            await self.bridge.esperar_fill(sym, order_id=res.order_id, category=cat)
            await self.tusk.confirmar_reserva(leg_uid, frente, dir_res, fill_confirmado=True)

        registrar_toque_greed(
            self.tusk, frentes_tocados,
            motivo=f"{tag}_SIM" if simulado else tag,
        )
        evento = "DISPARO_SIMULADO" if simulado else f"{tag}_EJECUTADO"
        await self.bel.anotar(
            "GREED", evento,
            f"{len(piernas)} piernas | Masa:{masa:.4f} | {' → '.join(frentes_tocados)}",
        )
        return True

    async def _ejecutar_dos_piernas(
        self,
        uid: str,
        masa: float,
        frente_buy: str,
        frente_sell: str,
        *,
        simulado: bool = False,
    ) -> bool:
        mitad = masa * 0.5

        if simulado:
            await self.tusk.confirmar_reserva(uid, frente_buy, "LONG")
            uid_s = f"{uid}_S"
            if await self.tusk.solicitar_reserva(uid_s, mitad, "GREED", "SHORT"):
                await self.tusk.confirmar_reserva(uid_s, frente_sell, "SHORT")
            registrar_toque_greed(self.tusk, [frente_buy, frente_sell], motivo="SIMULADO")
            await self.bel.anotar(
                "GREED", "DISPARO_SIMULADO",
                f"buy:{frente_buy} sell:{frente_sell} | Masa:{masa:.4f}",
            )
            return True

        sym_l = mercado.frente_a_symbol(frente_buy)
        cat_l = mercado.frente_a_category(frente_buy)
        sym_s = mercado.frente_a_symbol(frente_sell)
        cat_s = mercado.frente_a_category(frente_sell)

        res_l = await self.bridge.place_order(sym_l, "Buy", mitad, category=cat_l)
        res_s = await self.bridge.place_order(sym_s, "Sell", mitad, category=cat_s)

        if not res_l.exito or not res_s.exito:
            await self.tusk.liberar_reserva(uid)
            await self.bel.anotar("GREED", "ARBITRAJE_FALLIDO", "Una pata rechazada")
            return False

        await self.bridge.esperar_fill(sym_l, order_id=res_l.order_id, category=cat_l)
        await self.bridge.esperar_fill(sym_s, order_id=res_s.order_id, category=cat_s)
        await self.tusk.confirmar_reserva(uid, frente_buy, "LONG", fill_confirmado=True)
        uid_s = f"{uid}_S"
        if await self.tusk.solicitar_reserva(uid_s, mitad, "GREED", "SHORT"):
            await self.tusk.confirmar_reserva(uid_s, frente_sell, "SHORT", fill_confirmado=True)
        registrar_toque_greed(self.tusk, [frente_buy, frente_sell], motivo="ARBITRAJE")
        await self.bel.anotar(
            "GREED", "ARBITRAJE_EJECUTADO", f"buy:{frente_buy} sell:{frente_sell}",
        )
        return True
