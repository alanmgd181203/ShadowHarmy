import asyncio
import time
import uuid

from core import mercado
from core import igris_manto as im
from core import igris_despliegue as ides
from core import beru_capital as bc
from core import manto_jurisdiccion as mj
from core.manto_touch import limpiar_toques_expirados, rebalanceo_en_pausa_por_greed
import core.config as config


class IgrisEscudo:
    def __init__(self, tusk, tank, bellion, bridge=None, greed=None, kaiser=None):
        """
        Igris: El Escudo — gobernador absoluto del manto L/S.
        Despliegue paciente §E dual; Kaiser alimenta perfiles/urgencia; horizonte 95% (colchón).
        """
        self.tusk = tusk
        self.tank = tank
        self.bridge = bridge
        self.bel = bellion
        self.greed = greed
        self.kaiser = kaiser

        self.ultimo_movimiento = time.time()
        self.cooldown_maniobra_s = 5.0
        self._ultimo_log_engorde_bloqueado = 0.0
        self._engorde_fail_until = 0.0
        self._ultimo_log_espera_spread = 0.0

        # Paciencia / urgencia: se reinicia tras cada micro-mordida dual exitosa
        self._paciencia_t0 = time.time()
        # Misión Beru simétrica: objetivo por pata (USD notional) + Doctrina B (seguir al 95%)
        self._bloque_objetivo_usd = 0.0
        self._bloque_inyectado_usd = 0.0
        self._mision_beru_completa = False

        self._capital_pre_vuelo = 0.0
        self._rango_progresion: str | None = None
        self._activo_beru: str | None = None
        self._rangos_beru: dict | None = None
        self._ejecucion_directa_activa = True  # siempre True — sin yield
        self._alertas_kaiser_cache: list = []
        self._bootstrap_inicial_hecho = False
        self._ultimo_heartbeat_evento = 0.0

    def calcular_banda_delta(self):
        """Ventana 48–52 (crecimiento) o legacy por margen si flag off."""
        from core import manto_ventana as mv

        if mv.ventana_activa():
            return mv.banda_crecimiento()
        return mercado.calcular_banda_delta_legacy(self.tusk.margen_ocupado)

    def _umbral_capital_grado(self, rangos: dict, grado: str) -> float:
        """Capital aislado que exige el grado (costos_friccion / rangos_activo)."""
        costos = rangos.get("costos_friccion") or {}
        g = str(grado).upper()
        if g in costos:
            return float(costos[g])
        if g == "MARISCAL":
            return float(rangos.get("MARISCAL") or rangos.get("X") or 0)
        if g == "GENERAL":
            return float((rangos.get("GENERAL") or (0, 0))[0] - int(rangos.get("A_base") or 0))
        if g == "CAPITAN":
            return float((rangos.get("CAPITAN") or (0, 0))[0] - int(rangos.get("A_base") or 0))
        return float(rangos.get("X") or costos.get("SOLDADO") or 0)

    def _masa_pata_desde_beru(self, activo: str, precio: float) -> float:
        """
        Masa por pierna apuntando al umbral Beru del grado objetivo.
        margen_usd = umbral * (1 - reserva_5%); notional_pata = margen*lev/2; masa = notional/precio.
        Sin tope BOOTSTRAP_MANTO_FRACCION (0.25 erradicado).
        """
        capital = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        from core import plan_crecimiento as pc
        permitidos = pc.activos_permitidos(capital) if pc.rank_gate_activo() else None
        motor = bc.resolver_activo_y_grado(capital, activos=permitidos)
        a_base = int(motor.get("A_base") or 0)
        if pc.rank_gate_activo():
            activo_m = pc.activo_manto_preferido(capital)
        else:
            activo_m = str(motor.get("activo") or activo or config.TICKER_BASE).upper()
        grado = str(motor.get("grado") or "SOLDADO")
        rangos = bc.rangos_activo(activo_m, a_base=a_base)
        self._rangos_beru = rangos
        self._activo_beru = activo_m

        umbral = self._umbral_capital_grado(rangos, grado if grado != "BLOQUEADO" else "SOLDADO")
        # Horizonte: usar hasta 95% del umbral como margen (oxígeno 5% del capital del grado)
        reserva = bc.colchon_tusk_pct()
        margen_usd = max(0.0, umbral * (1.0 - reserva))
        lev = max(bc.apalancamiento_manto_promedio(activo_m), 1.0)
        notional_pata = (margen_usd * lev) / 2.0
        masa_auth = float(self.tusk.masa_autorizada)
        if precio <= 0:
            return max(0.0, masa_auth)
        masa = notional_pata / float(precio)
        # Solo limita la bóveda Tusk (oxígeno), nunca la fracción 0.25
        return max(0.0, min(masa, masa_auth)) if masa_auth > 0 else max(0.0, masa)

    def masa_paso_engorde(self) -> float:
        """Paso de engorde orientado a umbral Beru + techo de masa auth."""
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l + peso_s
        masa_auth = float(self.tusk.masa_autorizada)
        fraccion = float(getattr(config, "ENGORDE_PASO_FRACCION", 0.05))
        paso_min = float(getattr(config, "ENGORDE_PASO_MIN", 0.1))

        capital = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        from core import plan_crecimiento as pc
        permitidos = pc.activos_permitidos(capital) if pc.rank_gate_activo() else None
        motor = bc.resolver_activo_y_grado(capital, activos=permitidos)
        if pc.rank_gate_activo():
            activo = pc.activo_manto_preferido(capital)
        else:
            activo = str(motor.get("activo") or self._activo_beru or config.TICKER_BASE).upper()
        rangos = bc.rangos_activo(activo, a_base=int(motor.get("A_base") or 0))
        self._rangos_beru = rangos
        umbral = self._umbral_capital_grado(rangos, str(motor.get("grado") or "SOLDADO"))
        # Hueco de capital hacia el umbral del grado (aprox. en unidades de masa auth)
        hueco_frac = 0.0
        if umbral > 0 and capital < umbral:
            hueco_frac = (umbral - capital) / umbral
        techo_auth = max(masa_auth * fraccion, paso_min)
        techo_beru = max(paso_min, masa_auth * max(hueco_frac, fraccion))
        techo = min(masa_auth, max(techo_auth, techo_beru)) if masa_auth > 0 else techo_beru
        if masa_bruta > 0:
            return min(techo, max(masa_bruta, paso_min))
        return techo

    async def vigilar_manto_operativo(self):
        evento = getattr(config, "IGRIS_EVENT_DRIVEN", False)
        modo = "event-driven Kaiser→Igris" if evento else "escaneo continuo"
        print(
            f"[IGRIS] Vigilancia activa ({modo}) — horizonte {mj.techo_ideal():.0f}% "
            f"(colchón oxígeno, rebase táctico permitido)."
        )
        while True:
            _, estado = await self.tank.vision_especulativa()
            if estado != "ROJO":
                await self.auditar_manto_global()
            await asyncio.sleep(1)

    def _tipos_evento_manto(self) -> frozenset[str]:
        return frozenset({"OPORTUNIDAD_MANTO", "MATRIZ_SPREAD"})

    def _alertas_evento_para_activo(self, alertas: list, activo: str) -> list:
        """Alertas Kaiser relevantes para despliegue §E del activo."""
        activo_u = (activo or "").upper()
        tipos = self._tipos_evento_manto()
        out = []
        for a in alertas or []:
            if str(a.get("base", "")).upper() != activo_u:
                continue
            if str(a.get("tipo") or "") not in tipos:
                meta = a.get("datos") or a.get("meta") or {}
                if str(meta.get("tipo") or "") != "lineal_vs_inverse":
                    continue
            out.append(a)
        return out

    def _tiene_evento_manto(self, alertas: list | None = None) -> bool:
        alertas = alertas if alertas is not None else self._alertas_kaiser_cache
        activo = self._activo_despliegue()
        return bool(self._alertas_evento_para_activo(alertas, activo))

    def _consumir_kaiser_jurisdiccion(self) -> list:
        """Alertas Kaiser solo del activo bajo mando del manto (§E lineal_vs_inverse)."""
        if not self.kaiser:
            return []
        activo = self._activo_despliegue()
        try:
            raw = self.kaiser.consumir("IGRIS")
        except Exception:
            raw = []
        filtradas = ides.filtrar_alertas_jurisdiccion(raw, activo)
        self._alertas_kaiser_cache = filtradas
        return filtradas

    def _perfiles_kaiser(self) -> dict | None:
        if not self.kaiser:
            return None
        return getattr(self.kaiser, "perfiles", None) or None

    def _pipeline_ms_kaiser(self) -> float | None:
        if not self.kaiser:
            return None
        dig = getattr(self.kaiser, "ultimo_digest", None) or {}
        pipe = dig.get("pipeline") or {}
        ms = pipe.get("total_ms")
        return float(ms) if ms is not None else None

    def _tank_semaforo(self) -> str:
        lider = None
        if hasattr(self.tank, "_obtener_lider_verde"):
            try:
                lider = self.tank._obtener_lider_verde()
            except Exception:
                lider = None
        return getattr(lider, "estado_foco", None) or "VERDE"

    async def auditar_manto_global(self):
        if not await self._auditoria_pre_despliegue():
            return

        self._ejecucion_directa_activa = True
        if hasattr(self.tusk, "manto_cedido_a_greed"):
            self.tusk.manto_cedido_a_greed = False

        limpiar_toques_expirados(self.tusk)
        alertas = self._consumir_kaiser_jurisdiccion()
        event_driven = getattr(config, "IGRIS_EVENT_DRIVEN", False)

        margen_actual = float(self.tusk.margen_ocupado)
        peso_l_total = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s_total = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l_total + peso_s_total
        en_cooldown = (time.time() - self.ultimo_movimiento) <= self.cooldown_maniobra_s
        if time.time() < self._engorde_fail_until:
            en_cooldown = True

        activo = self._activo_despliegue()
        eventos_activo = self._alertas_evento_para_activo(alertas, activo)

        # Bootstrap — vacío: en event-driven solo con señal Kaiser o primer arranque
        if masa_bruta == 0:
            if event_driven:
                bootstrap_ok = (
                    bool(eventos_activo)
                    or (
                        getattr(config, "IGRIS_BOOTSTRAP_ON_START", True)
                        and not self._bootstrap_inicial_hecho
                    )
                )
                if bootstrap_ok:
                    self._bootstrap_inicial_hecho = True
                    await self._bootstrap_manto()
                elif time.time() - self._ultimo_heartbeat_evento > float(
                    getattr(config, "IGRIS_EVENT_HEARTBEAT_S", 300)
                ):
                    self._ultimo_heartbeat_evento = time.time()
                    await self.bel.anotar(
                        "IGRIS", "EVENT_IDLE",
                        f"Sin oportunidad Kaiser para {activo} — escudo en espera.",
                    )
            else:
                await self._bootstrap_manto()
            return

        if event_driven and not eventos_activo:
            return

        if en_cooldown:
            return

        # Rebalanceo + engorde (ventana 48–52 / long-primero). El 95% NO aborta la puerta.
        if masa_bruta > 0 and not rebalanceo_en_pausa_por_greed(self.tusk):
            ratio_l = peso_l_total / masa_bruta
            banda_min, banda_max = self.calcular_banda_delta()
            if ratio_l > banda_max:
                await self.bel.anotar(
                    "IGRIS", "REBALANCEO",
                    f"Delta long {ratio_l*100:.1f}% > techo {banda_max*100:.0f}% (ventana 48-52)",
                )
                await self._ejecutar_maniobra("REBALANCEO_IGRIS", "SHORT", self.tusk.masa_autorizada)
                return
            if ratio_l < banda_min:
                await self.bel.anotar(
                    "IGRIS", "REBALANCEO",
                    f"Delta long {ratio_l*100:.1f}% < piso {banda_min*100:.0f}% (ventana 48-52)",
                )
                await self._ejecutar_maniobra("REBALANCEO_IGRIS", "LONG", self.tusk.masa_autorizada)
                return

        from core import manto_ventana as mv
        dir_engorde = mv.direccion_engorde_preferida(peso_l_total, peso_s_total)
        ok_engorde = await self._ejecutar_maniobra_engorde(dir_engorde)

        # Ley Marcial: poda el exceso en ciclos posteriores si ya estamos sobre el horizonte
        # y no acabamos de disparar una mordida (la puerta no se cierra al disparar).
        margen_post = float(self.tusk.margen_ocupado)
        if mj.sobre_muro(margen_post) and not ok_engorde:
            await self.bel.anotar(
                "IGRIS", "LEY_MARCIAL",
                f"Colchón: margen {margen_post:.1f}% ≥ horizonte {mj.muro_marcial():.0f}% — poda táctica.",
            )
            dir_poda = "LONG" if peso_l_total >= peso_s_total else "SHORT"
            await self._ejecutar_maniobra("PODAR_MANTO", dir_poda, max(masa_bruta * 0.15, 0.0))

    async def _ejecutar_maniobra_engorde(self, direccion: str) -> bool:
        """Engorde dual; retorna True si materializó (para diferir poda)."""
        masa = self.masa_paso_engorde()
        if masa <= 0:
            return False
        uid = f"IGRIS_ENGORDAR_MANTO_{str(uuid.uuid4())[:4]}"
        if not await self.tusk.solicitar_reserva(uid, masa, "IGRIS", direccion):
            return False
        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map or estado in ("GLITCH_DETECTADO", "ROJO"):
            await self.tusk.liberar_reserva(uid)
            return False
        ok = await self._engorde(uid, direccion, masa, ctx_map)
        if ok:
            self.ultimo_movimiento = time.time()
        else:
            await self.tusk.liberar_reserva(uid)
        return ok

    async def _radar_manto(self, ctx_map, masa, is_long):
        return mercado.escanear_mejor_precio(config.FRENTES_MANTO_ALL, ctx_map, masa, is_long)

    async def _materializar_en_frente(
        self,
        uid,
        frente,
        direccion,
        masa,
        precio_fill: float = 0.0,
        *,
        force_market: bool = False,
        fill_timeout_s: float | None = None,
    ) -> dict:
        """
        Orden real / virtual / sim.
        Retorna {ok, masa, precio} — masa puede ser parcial si escalera llenó solo algunos peldaños.
        """
        from core import escalera_precios as esc

        virtual = (
            getattr(config, "ARENA_IGRIS_ACTIVA", False)
            and getattr(config, "ARENA_IGRIS_FILLS_VIRTUALES", True)
        )
        if virtual:
            await self.tusk.confirmar_reserva(
                uid, frente, direccion, fill_confirmado=True,
                precio_fill=precio_fill if precio_fill > 0 else None,
            )
            return {"ok": True, "masa": float(masa), "precio": float(precio_fill or 0)}
        if not config.MODO_SIMULACION and self.bridge:
            side = "Buy" if direccion == "LONG" else "Sell"
            sym = mercado.frente_a_symbol(frente)
            cat = mercado.frente_a_category(frente)
            timeout = float(
                fill_timeout_s
                if fill_timeout_s is not None
                else getattr(config, "IGRIS_DUAL_FILL_TIMEOUT_S", 20)
            )

            usar_esc = (
                (not force_market)
                and esc.escalera_activa("IGRIS")
                and float(precio_fill or 0) > 0
                and float(masa) > 0
            )
            if usar_esc:
                n_max, mid = esc.n_y_marcha_para_general()
                if n_max <= 1 and mid == "asalto":
                    usar_esc = False

            if usar_esc:
                px = float(precio_fill)
                peldaños = esc.armar_peldaños_lote(
                    float(masa),
                    px,
                    side,  # type: ignore[arg-type]
                    frente=frente,
                    unidad="qty",
                    n_max=n_max,
                    marcha_id=mid,
                )
                rungs = [{"tamaño": p["tamaño"], "precio": p["precio"]} for p in peldaños]
                if len(rungs) >= 2:
                    resultado = await esc.ejecutar_escalera(
                        self.bridge,
                        symbol=sym,
                        side=side,  # type: ignore[arg-type]
                        category=cat,
                        peldaños=rungs,
                        bel=self.bel,
                        general="IGRIS",
                        fill_timeout_s=float(
                            getattr(config, "ESCALERA_FILL_TIMEOUT_S", 12) or 12
                        ),
                    )
                    filled = float(resultado.get("filled_tamaño") or 0)
                    if filled <= 0:
                        await self.tusk.liberar_reserva(uid)
                        return {"ok": False, "masa": 0.0, "precio": 0.0}
                    avg = float(resultado.get("avg_price") or px)
                    await self.tusk.confirmar_reserva(
                        uid, frente, direccion, fill_confirmado=True,
                        precio_fill=avg, fee_usd=0.0,
                    )
                    await self.bel.anotar(
                        "IGRIS", "ESCALERA_OK",
                        f"{direccion} {frente} · {resultado.get('n_filled')} peldaños · "
                        f"masa {filled:.6f}/{float(masa):.6f}",
                    )
                    return {"ok": True, "masa": filled, "precio": avg}

            if force_market:
                order_type, price = "Market", None
            else:
                order_type, price = self._orden_tipo_manto(precio_fill)
            from core import lote_bybit as lote

            filt = lote.filtros_lote(frente)
            masa_q = lote.cuantizar_qty(
                float(masa),
                min_qty=float(filt.get("minOrderQty") or 0),
                qty_step=float(filt.get("qtyStep") or 0),
                mode="floor",
            )
            if masa_q <= 0:
                await self.tusk.liberar_reserva(uid)
                await self.bel.anotar(
                    "IGRIS", "ORDEN_FALLIDA",
                    f"{frente} {direccion}: qty bajo minOrderQty/qtyStep",
                )
                return {"ok": False, "masa": 0.0, "precio": 0.0}
            res = await self.bridge.place_order(
                sym, side, masa_q, category=cat, order_type=order_type, price=price,
            )
            if not res.exito:
                await self.tusk.liberar_reserva(uid)
                await self.bel.anotar("IGRIS", "ORDEN_FALLIDA", f"{frente} {direccion}: {res.mensaje}")
                return {"ok": False, "masa": 0.0, "precio": 0.0}
            fill = await self.bridge.esperar_fill(
                sym, order_id=res.order_id, category=cat, timeout_s=timeout,
            )
            if not fill.exito:
                if order_type == "Limit" and res.order_id:
                    try:
                        await self.bridge.cancel_order(sym, order_id=res.order_id, category=cat)
                    except Exception:
                        pass
                await self.tusk.liberar_reserva(uid)
                return {"ok": False, "masa": 0.0, "precio": 0.0}
            datos = getattr(fill, "datos", None) or {}
            px = float(
                datos.get("avgPrice")
                or getattr(fill, "precio", 0)
                or getattr(fill, "avg_price", 0)
                or precio_fill
                or 0
            )
            fee = float(datos.get("cumExecFee") or 0)
            filled_m = float(datos.get("cumExecQty") or masa)
            await self.tusk.confirmar_reserva(
                uid, frente, direccion, fill_confirmado=True, precio_fill=px, fee_usd=fee,
            )
            return {"ok": True, "masa": filled_m, "precio": px}

        await self.tusk.confirmar_reserva(
            uid, frente, direccion, precio_fill=precio_fill if precio_fill > 0 else None,
        )
        return {"ok": True, "masa": float(masa), "precio": float(precio_fill or 0)}

    def _orden_tipo_manto(self, precio_fill: float) -> tuple[str, float | None]:
        """Táctico → Limit@Ask/Bid · Forzada/Asalto → Market (Asalto force; Forzada mix vía umbral)."""
        try:
            from core import pase_director as pd
            if not pd.director_activo():
                return "Market", None
            perfil = pd.perfil_marcha()
            if perfil.get("force_market"):
                return "Market", None
            if str(perfil.get("id")) == "tactico" and float(precio_fill or 0) > 0:
                return "Limit", float(precio_fill)
        except Exception:
            pass
        return "Market", None

    async def _salvavidas_market_pierna(
        self, uid, frente, direccion, masa, precio_ref: float = 0.0,
    ) -> dict:
        """Pierna huérfana / desbalance: Market para equilibrar."""
        await self.bel.anotar(
            "IGRIS", "SALVAVIDAS_MARKET",
            f"{direccion} {frente} — equilibrar · masa {float(masa):.6f}",
        )
        if float(masa) <= 0:
            return {"ok": False, "masa": 0.0, "precio": 0.0}
        if not await self.tusk.solicitar_reserva(uid, masa, "IGRIS", direccion):
            await self.bel.anotar(
                "IGRIS", "SALVAVIDAS_FALLIDO",
                f"Sin reserva Tusk para {direccion} {frente}",
            )
            return {"ok": False, "masa": 0.0, "precio": 0.0}
        return await self._materializar_en_frente(
            uid, frente, direccion, masa, precio_ref,
            force_market=True,
            fill_timeout_s=float(getattr(config, "IGRIS_DUAL_FILL_TIMEOUT_S", 20)),
        )

    async def _disparo_dual_simultaneo(
        self,
        uid_l: str,
        uid_s: str,
        frente_l: str,
        frente_s: str,
        masa: float,
        ask_l: float,
        bid_s: float,
    ) -> bool:
        """
        Ambas piernas a la vez. Escalera de precios si activa.
        Si una llena más que la otra → Market en la deficitaria. Cancel implícito en escalera.
        """
        timeout = float(getattr(config, "IGRIS_DUAL_FILL_TIMEOUT_S", 20))
        r_l, r_s = await asyncio.gather(
            self._materializar_en_frente(
                uid_l, frente_l, "LONG", masa, ask_l, fill_timeout_s=timeout,
            ),
            self._materializar_en_frente(
                uid_s, frente_s, "SHORT", masa, bid_s, fill_timeout_s=timeout,
            ),
        )
        ok_l = bool(r_l.get("ok"))
        ok_s = bool(r_s.get("ok"))
        masa_l = float(r_l.get("masa") or 0)
        masa_s = float(r_s.get("masa") or 0)

        if ok_l and ok_s:
            # Equilibrio fino si la escalera llenó distinto
            diff = masa_l - masa_s
            tol = max(float(masa) * 0.05, 1e-8)
            salvavidas = bool(getattr(config, "IGRIS_DUAL_SALVAVIDAS_MARKET", True))
            if salvavidas and abs(diff) > tol:
                if diff > 0:
                    # Falta short
                    uid_fix = f"{uid_s}_EQ"
                    r = await self._salvavidas_market_pierna(
                        uid_fix, frente_s, "SHORT", abs(diff), bid_s,
                    )
                    return bool(r.get("ok"))
                uid_fix = f"{uid_l}_EQ"
                r = await self._salvavidas_market_pierna(
                    uid_fix, frente_l, "LONG", abs(diff), ask_l,
                )
                return bool(r.get("ok"))
            return True

        salvavidas = bool(getattr(config, "IGRIS_DUAL_SALVAVIDAS_MARKET", True))
        if not salvavidas:
            await self.bel.anotar(
                "IGRIS", "DUAL_INCOMPLETO",
                f"L={ok_l}({masa_l}) S={ok_s}({masa_s}) · salvavidas off",
            )
            return False

        if ok_l and not ok_s:
            r = await self._salvavidas_market_pierna(
                uid_s, frente_s, "SHORT", masa_l or masa, bid_s,
            )
            return bool(r.get("ok"))
        if ok_s and not ok_l:
            r = await self._salvavidas_market_pierna(
                uid_l, frente_l, "LONG", masa_s or masa, ask_l,
            )
            return bool(r.get("ok"))

        await self.bel.anotar(
            "IGRIS", "DUAL_FALLIDO",
            f"Ninguna pierna llenó · L={frente_l} S={frente_s}",
        )
        return False

    async def _auditoria_pre_despliegue(self) -> bool:
        """Candado de bóveda — umbrales dinámicos desde motor X/A_base (rangos_activo)."""
        # Solo la arena (o live_testnet explícito) salta el grado Beru
        sin_rangos = (
            (
                getattr(config, "ARENA_IGRIS_ACTIVA", False)
                and getattr(config, "ARENA_IGRIS_SIN_RANGOS", False)
            )
            or getattr(config, "LIVE_IGRIS_TESTNET", False)
        )
        if sin_rangos:
            self._rango_progresion = self._rango_progresion or "GENERAL"
            if not self._activo_beru:
                self._activo_beru = str(config.TICKER_BASE or "ETH").upper()
            self._capital_pre_vuelo = float(
                self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0
            )
            return True
        capital = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        self._capital_pre_vuelo = capital
        from core import plan_crecimiento as pc

        permitidos = None
        if pc.rank_gate_activo():
            permitidos = pc.activos_permitidos(capital)
        res = bc.resolver_activo_y_grado(capital, activos=permitidos)
        grado = res.get("grado", "BLOQUEADO")
        mapa = {
            "BLOQUEADO": "BLOQUEADO",
            "SOLDADO": "ASPIRANTE",
            "CAPITAN": "CAPITAN",
            "GENERAL": "GENERAL",
            "MARISCAL": "MARISCAL",
        }
        self._rango_progresion = mapa.get(grado, "BLOQUEADO")
        # Preferido del pase / foco director
        from core import pase_director as pd
        if pd.director_activo() and grado != "BLOQUEADO":
            self._activo_beru = pd.activo_manto_foco(capital, tusk=self.tusk)
        elif pc.rank_gate_activo() and grado != "BLOQUEADO":
            pref = pc.activo_manto_preferido(capital)
            self._activo_beru = pref
        else:
            self._activo_beru = (
                str(res.get("activo") or config.TICKER_BASE).upper()
                if res.get("activo")
                else str(config.TICKER_BASE).upper()
            )
        plan_nv = pc.nivel_por_equity(capital)
        self._nivel_monarca = plan_nv.get("nivel", "ASPIRANTE")
        if res.get("rangos"):
            self._rangos_beru = res["rangos"]
        elif self._activo_beru and grado != "BLOQUEADO":
            self._rangos_beru = bc.rangos_activo(
                self._activo_beru, a_base=int(res.get("A_base") or 0),
            )
        if grado == "BLOQUEADO":
            return False
        return True

    async def arena_inyectar_activo(self, activo: str, *, origen: str = "ARENA") -> dict:
        """
        Despliegue dual §E para un activo (arena aislada / prueba por evento).
        Ignora cola Beru cuando ARENA_IGRIS_SIN_RANGOS.
        """
        activo_u = (activo or "").upper()
        self._activo_beru = activo_u
        self._rango_progresion = "GENERAL"
        self._bloque_objetivo_usd = 0.0
        self._bloque_inyectado_usd = 0.0
        ok = await self._inyectar_dual_paciente(origen=origen)
        return {"activo": activo_u, "ok": ok}

    async def live_inyectar_activo(
        self,
        activo: str,
        *,
        max_usd: float | None = None,
        origen: str = "LIVE_TESTNET",
    ) -> dict:
        """
        Dual §E en testnet real (Bridge place_order). Tope de notional por pata.
        Requiere MODO_SIMULACION=False y ARENA_IGRIS_ACTIVA=False.
        """
        activo_u = (activo or "").upper()
        self._activo_beru = activo_u
        self._rango_progresion = "GENERAL"
        self._bloque_objetivo_usd = 0.0
        self._bloque_inyectado_usd = 0.0
        cap = float(
            max_usd
            if max_usd is not None
            else getattr(config, "LIVE_IGRIS_MORDIDA_MAX_USD", 12.0)
        )
        ok = await self._inyectar_dual_paciente(origen=origen, restante_usd_cap=cap)
        return {"activo": activo_u, "ok": ok, "max_usd": cap}

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

    def _activo_despliegue(self) -> str:
        """Activo del manto: foco del director de pase, o legado ETH en grado Soldado."""
        from core import plan_crecimiento as pc
        from core import pase_director as pd

        sin_rangos = (
            (
                getattr(config, "ARENA_IGRIS_ACTIVA", False)
                and getattr(config, "ARENA_IGRIS_SIN_RANGOS", False)
            )
            or getattr(config, "LIVE_IGRIS_TESTNET", False)
        )
        if sin_rangos:
            return (self._activo_beru or config.TICKER_BASE or "ETH").upper()

        eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        if pd.director_activo():
            try:
                pd.sincronizar_logrados_desde_tusk(self.tusk, eq)
            except Exception:
                pass
            return pd.activo_manto_foco(eq, tusk=self.tusk)

        if pc.rank_gate_activo():
            return pc.activo_manto_preferido(eq)
        rango = self._rango_progresion or ""
        if rango == "ASPIRANTE":
            return "ETH"
        return (self._activo_beru or config.TICKER_BASE or "ETH").upper()

    def _asegurar_bloque_usd(self, activo: str, precio_ref: float) -> float:
        """
        Misión simétrica: objetivo = notional por pata ($L = $S).
        Con director de pase: meta = delta_usd del paso × fill − ya desplegado.
        Sin director: Beru-grade + Doctrina B hacia horizonte 95%.
        """
        if self._bloque_objetivo_usd > 0 and self._bloque_inyectado_usd < self._bloque_objetivo_usd:
            return max(0.0, self._bloque_objetivo_usd - self._bloque_inyectado_usd)

        from core import pase_director as pd

        # Ranking → meta USD (pase): no engordar de más el paso foco
        if pd.director_activo():
            eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
            try:
                pd.sincronizar_logrados_desde_tusk(self.tusk, eq)
            except Exception:
                pass
            meta = pd.meta_engorde_usd(eq, activo, tusk=self.tusk)
            if not meta.get("ok"):
                self._bloque_objetivo_usd = 0.0
                self._bloque_inyectado_usd = 0.0
                return 0.0
            restante_total = float(meta.get("restante_usd") or 0.0)
            if restante_total <= 0:
                self._bloque_objetivo_usd = 0.0
                self._bloque_inyectado_usd = 0.0
                return 0.0
            # Dual L+S: cada pata lleva la mitad del restante del paso
            objetivo = restante_total / 2.0
            self._bloque_objetivo_usd = objetivo
            self._bloque_inyectado_usd = 0.0
            return objetivo

        masa_pata = self._masa_pata_desde_beru(activo, precio_ref)
        fraccion_legacy = float(getattr(config, "BOOTSTRAP_MANTO_FRACCION", 0) or 0)
        if fraccion_legacy > 0:
            masa_pata = min(masa_pata, float(self.tusk.masa_autorizada) * fraccion_legacy)
        objetivo = max(0.0, masa_pata * max(precio_ref, 0.0))

        # Doctrina B: si misión Beru ya se marcó, empujar hueco hacia horizonte 95%
        if self._mision_beru_completa:
            margen = float(self.tusk.margen_ocupado)
            horizonte = float(mj.techo_ideal())
            hueco_pct = max(0.0, horizonte - margen) / 100.0
            equity = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
            lev = max(bc.apalancamiento_manto_promedio(activo), 1.0)
            objetivo_h = max(objetivo, (equity * hueco_pct * lev) / 2.0) if hueco_pct > 0 else objetivo
            if hueco_pct <= 0:
                paso = self.masa_paso_engorde()
                objetivo_h = max(objetivo * 0.1, paso * max(precio_ref, 0.0))
            objetivo = max(objetivo_h, 0.0)

        self._bloque_objetivo_usd = objetivo
        self._bloque_inyectado_usd = 0.0
        return objetivo

    async def _anotar_espera_spread(self, tag: str, puerta: dict) -> None:
        log_cd = float(getattr(config, "IGRIS_ESPERA_LOG_S", 60.0))
        ahora = time.time()
        if ahora - self._ultimo_log_espera_spread < log_cd:
            return
        self._ultimo_log_espera_spread = ahora
        await self.bel.anotar(
            "IGRIS", tag,
            f"{puerta.get('motivo')} · spread={puerta.get('spread_pct', '—')} "
            f"umbral={puerta.get('umbral_pct', '—')} tau_h={puerta.get('tau_h', '—')} "
            f"freq={puerta.get('pct_frecuencia', '—')} modo={puerta.get('modo_paciencia', '—')} "
            f"frac={puerta.get('fraccion', '—')} calor={puerta.get('calor', '—')} "
            f"askL={puerta.get('ask_long', 0):.4f} bidS={puerta.get('bid_short', 0):.4f}",
        )

    async def _inyectar_dual_paciente(self, *, origen: str, restante_usd_cap: float | None = None) -> bool:
        """
        Ritual único bootstrap/engorde: dual §E, Ask/Bid, fees±urgencia invertida,
        mordida = techo_misión × fracción(confianza) hasta 100%.
        """
        activo = self._activo_despliegue()
        frente_l, frente_s = im.frentes_bootstrap(activo)

        if activo == "ETH" and origen == "BOOTSTRAP":
            if not await self._asegurar_apalancamiento_aspirante_eth():
                return False

        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map or estado in ("GLITCH_DETECTADO", "ROJO"):
            return False

        ask_guess = ides.best_ask(ides.libro_tank(self.tank, frente_l)[1])
        bid_guess = ides.best_bid(ides.libro_tank(self.tank, frente_s)[0])
        precio_ref = 0.0
        if ask_guess > 0 and bid_guess > 0:
            precio_ref = (ask_guess + bid_guess) / 2.0
        else:
            pl = im.precio_ctx(ctx_map, frente_l)
            ps = im.precio_ctx(ctx_map, frente_s)
            precio_ref = (pl + ps) / 2.0 if pl > 0 and ps > 0 else max(pl, ps)
        if precio_ref <= 0:
            return False

        restante = self._asegurar_bloque_usd(activo, precio_ref)
        if restante_usd_cap is not None and restante_usd_cap > 0:
            restante = min(restante, restante_usd_cap)
        if restante <= 0:
            if (
                self._bloque_objetivo_usd > 0
                and self._bloque_inyectado_usd >= self._bloque_objetivo_usd - 1e-6
            ):
                self._mision_beru_completa = True
            self._bloque_objetivo_usd = 0.0
            self._bloque_inyectado_usd = 0.0
            restante = self._asegurar_bloque_usd(activo, precio_ref)
        if restante <= 0:
            return False

        puerta = ides.evaluar_puerta_se(
            self.tank, frente_l, frente_s,
            t0_paciencia=self._paciencia_t0,
            restante_usd=restante,
            activo=activo,
            perfiles=self._perfiles_kaiser(),
            tank_semaforo=self._tank_semaforo(),
            pipeline_ms=self._pipeline_ms_kaiser(),
            margen_ocupado_pct=float(self.tusk.margen_ocupado),
        )
        if not puerta.get("ok"):
            await self._anotar_espera_spread(
                "BOOTSTRAP_ESPERA_SPREAD" if origen == "BOOTSTRAP" else "ENGORDE_ESPERA_SPREAD",
                puerta,
            )
            wait = float(getattr(config, "IGRIS_ESPERA_COOLDOWN_S", 5.0))
            self._engorde_fail_until = time.time() + wait
            return False

        masa = float(puerta["masa"])
        micro_usd = float(puerta["micro_usd"])
        ask_l = float(puerta["ask_long"])
        bid_s = float(puerta["bid_short"])

        # Sin abortar por horizonte 95%: la puerta de asimetría dispara aunque rebase.
        margen = self.tusk.margen_ocupado
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        if not mercado.verificar_delta_post_maniobra(margen, peso_l + masa, peso_s + masa):
            if (
                (
                    getattr(config, "ARENA_IGRIS_ACTIVA", False)
                    and getattr(config, "ARENA_IGRIS_SIN_BANDA_DELTA", True)
                )
                or getattr(config, "LIVE_IGRIS_TESTNET", False)
            ):
                pass  # arena/live verificación: no contaminar dual por delta global
            else:
                await self._anotar_espera_spread(
                    "ENGORDE_ESPERA_SPREAD",
                    {**puerta, "motivo": "banda_delta_dual"},
                )
                return False

        uid_l = f"IGRIS_{origen[:4]}_L_{str(uuid.uuid4())[:4]}"
        uid_s = f"IGRIS_{origen[:4]}_S_{str(uuid.uuid4())[:4]}"

        if not await self.tusk.solicitar_reserva(uid_l, masa, "IGRIS", "LONG"):
            return False
        if not await self.tusk.solicitar_reserva(uid_s, masa, "IGRIS", "SHORT"):
            await self.tusk.liberar_reserva(uid_l)
            return False

        # Disparo dual simultáneo + salvavidas Market si una pierna queda huérfana
        if not await self._disparo_dual_simultaneo(
            uid_l, uid_s, frente_l, frente_s, masa, ask_l, bid_s,
        ):
            return False

        self._bloque_inyectado_usd += micro_usd
        if self._bloque_inyectado_usd >= self._bloque_objetivo_usd - 1e-6:
            from core import pase_director as pd
            if pd.director_activo():
                eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
                try:
                    marked = pd.marcar_foco_si_bloque_completo(eq, activo)
                    if marked:
                        await self.bel.anotar(
                            "IGRIS", "PASE_PASO",
                            f"Paso logrado · foco {activo} · logrados {marked.get('pasos_logrados')}",
                        )
                except Exception:
                    pass
                await self.bel.anotar(
                    "IGRIS", "MISION_PASE",
                    f"Bloque pase cumplido (${self._bloque_objetivo_usd:.1f}/pata) — "
                    f"siguiente foco o solo ventana.",
                )
            elif not self._mision_beru_completa:
                self._mision_beru_completa = True
                await self.bel.anotar(
                    "IGRIS", "MISION_BERU",
                    f"Rango simétrico cumplido (${self._bloque_objetivo_usd:.1f}/pata) — Doctrina B → horizonte 95%.",
                )
            self._bloque_objetivo_usd = 0.0
            self._bloque_inyectado_usd = 0.0

        self._paciencia_t0 = time.time()
        self.ultimo_movimiento = time.time()

        tag = "BOOTSTRAP_MANTO" if origen == "BOOTSTRAP" else "ENGORDE_DUAL"
        await self.bel.anotar(
            "IGRIS", tag,
            f"§E L {frente_l}@{ask_l:.4f} / S {frente_s}@{bid_s:.4f} | "
            f"mordida ${micro_usd:.2f} frac={puerta.get('fraccion')} calor={puerta.get('calor')} | "
            f"spread={puerta.get('spread_pct')}>=umbral={puerta.get('umbral_pct')} "
            f"tau={puerta.get('tau_h')}h | "
            f"bloque {self._bloque_inyectado_usd:.1f}/{self._bloque_objetivo_usd:.1f} USD",
        )
        return True

    async def _bootstrap_manto(self):
        """Primer par L/S — solo dual §E paciente (Ask/Bid + fees + micro)."""
        if not await self._auditoria_pre_despliegue():
            return
        rango = self._rango_progresion
        if rango == "BLOQUEADO" or not rango:
            return
        await self._inyectar_dual_paciente(origen="BOOTSTRAP")

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
            r = await self._materializar_en_frente(uid, mejor_f, dir_refuerzo, masa_rest, precio)
            if r.get("ok"):
                await self.bel.anotar("IGRIS", "REBALANCEO_APERTURA", f"Abierto {masa_rest:.4f} {dir_refuerzo} en {mejor_f}")
                return True

        await self.tusk.liberar_reserva(uid)
        return masa_aplicada > 0

    async def _engorde(self, uid, direccion, masa, ctx_map):
        """
        Engorde estricto dual §E — nunca una sola pata.
        Libera la reserva unilateral del maniobra e inyecta L inverse + S lineal.
        """
        await self.tusk.liberar_reserva(uid)

        # Cap del paso: masa pedida × precio ref del par (si hay libro)
        activo = self._activo_despliegue()
        frente_l, frente_s = im.frentes_bootstrap(activo)
        ask_l = ides.best_ask(ides.libro_tank(self.tank, frente_l)[1])
        bid_s = ides.best_bid(ides.libro_tank(self.tank, frente_s)[0])
        if ask_l > 0 and bid_s > 0:
            px = (ask_l + bid_s) / 2.0
        else:
            px = self._precio_ctx_o_reflejo(ctx_map, frente_s) or self._precio_ctx_o_reflejo(ctx_map, frente_l)
        cap_usd = float(masa) * float(px) if masa > 0 and px > 0 else None

        ok = await self._inyectar_dual_paciente(origen="ENGORDE", restante_usd_cap=cap_usd)
        if ok:
            return True

        fail_cd = float(getattr(config, "IGRIS_ESPERA_COOLDOWN_S", 5.0))
        self.ultimo_movimiento = time.time()
        self._engorde_fail_until = time.time() + fail_cd
        return False

    def _precio_ctx_o_reflejo(self, ctx_map, frente: str) -> float:
        """Precio del frente; si lineal está ciego, refleja inverse/spot del mismo activo."""
        ctx = ctx_map.get(frente) if ctx_map else None
        px = float(getattr(ctx, "last_price", 0) or 0) if ctx else 0.0
        if px > 0:
            return px
        if isinstance(ctx, dict):
            px = float(ctx.get("precio") or ctx.get("last") or 0)
            if px > 0:
                return px
        asset = frente.split("_")[0].replace("USDT", "").replace("USDC", "").replace("USD", "")
        for f, c in (ctx_map or {}).items():
            if isinstance(c, dict):
                px_c = float(c.get("precio") or c.get("last") or 0)
            else:
                px_c = float(getattr(c, "last_price", 0) or 0) if c else 0.0
            if px_c <= 0:
                continue
            sym = str(getattr(c, "symbol", "") if not isinstance(c, dict) else c.get("symbol") or f)
            if asset and asset in sym:
                return px_c
        return 0.0
