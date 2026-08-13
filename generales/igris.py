import asyncio
import time
import uuid

from core import mercado
from core import igris_manto as im
from core import igris_despliegue as ides
from core import beru_capital as bc
from core import manto_jurisdiccion as mj
from core.manto_touch import limpiar_toques_expirados, rebalanceo_en_pausa_por_greed
from core import igris_leverage as ilev
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
        # Override temporal: engorde/bootstrap del lote en paralelo (varios Santos por latido)
        self._override_activo: str | None = None
        # Densidad máxima: no re-martillar set_leverage en cada dual
        self._lev_force_gate = ilev.LeverageForceGate()
        self._engorde_fail_until_por: dict[str, float] = {}
        # Aire entre duales OK (mismo Santo): no ametrallar libro / ensanchar spread
        self._engorde_ritmo_until_por: dict[str, float] = {}
        self._engorde_ritmo_until = 0.0
        # Candado: no otro par Market hasta confirmar fills L+S del dual anterior
        self._dual_fills_ok_por: dict[str, bool] = {}

        self._capital_pre_vuelo = 0.0
        self._rango_progresion: str | None = None
        self._activo_beru: str | None = None
        self._rangos_beru: dict | None = None
        self._ejecucion_directa_activa = True  # siempre True — sin yield
        self._alertas_kaiser_cache: list = []
        self._bootstrap_inicial_hecho = False
        self._ultimo_heartbeat_evento = 0.0
        # Último candado Ley de la Masa (solo lectura → estado_vivo; no dispara órdenes)
        self._ultimo_ley_masa: dict | None = None

    def snapshot_ley_masa(self) -> dict:
        """Campos ligeros para panel — sin re-evaluar puerta ni enviar órdenes."""
        snap = self._ultimo_ley_masa
        if not snap:
            return {
                "ok": None,
                "motivo": "sin_puerta_aun",
                "bloqueado": None,
                "asim_pct": None,
                "activo": None,
            }
        return dict(snap)

    def _registrar_ley_masa(self, activo: str, puerta: dict) -> None:
        ley = puerta.get("ley_masa") if isinstance(puerta, dict) else None
        if not isinstance(ley, dict):
            ley = {}
        motivo = str(ley.get("motivo") or puerta.get("motivo") or "—")
        ok = ley.get("ok")
        if ok is None and puerta.get("motivo") in (
            "ley_masa_fallida",
            "asimetr_masa_usd",
            "sin_precio_ley_masa",
        ):
            ok = False
        self._ultimo_ley_masa = {
            "ok": ok,
            "motivo": motivo,
            "bloqueado": False if ok is True else (True if ok is False else None),
            "asim_pct": ley.get("asim_pct"),
            "asim_max_pct": ley.get("asim_max_pct"),
            "alfa_usd": ley.get("alfa_usd") or puerta.get("alfa_usd"),
            "masa_absoluta_usd": ley.get("masa_absoluta_usd") or puerta.get("micro_usd"),
            "activo": (activo or "").upper() or None,
            "puerta_ok": bool(puerta.get("ok")) if isinstance(puerta, dict) else None,
            "ts": time.time(),
        }

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
        # Horizonte capital→nocional: IM pierna a pierna (sin lev promedio)
        reserva = bc.colchon_tusk_pct()
        margen_usd = max(0.0, umbral * (1.0 - reserva))
        det = bc.margen_piernas_para_friccion(activo_m, bc.friccion_soldado_pct())
        im_ref = float(det["im_total_usd"] or 0)
        if im_ref > 0:
            notional_pata = float(det["notional_pierna_usd"]) * (margen_usd / im_ref)
        else:
            notional_pata = 0.0
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
        from core import igris_mision as imis

        sueno = imis.sueno_mision_activo()
        modo = (
            "sueño+misión (sargento)"
            if sueno
            else (
                "event-driven Kaiser→Igris"
                if getattr(config, "IGRIS_EVENT_DRIVEN", False)
                else "escaneo continuo (legado)"
            )
        )
        print(
            f"[IGRIS] Vigilancia activa ({modo}) — horizonte {mj.techo_ideal():.0f}% "
            f"(colchón oxígeno; §A no pilotéa)."
        )
        while True:
            if sueno:
                await self._latido_sueno_mision()
            else:
                await self.auditar_manto_global()
                await asyncio.sleep(1)

    async def _latido_sueno_mision(self) -> None:
        """Duerme; sargento encola; ejecuta una misión; vuelve a dormir."""
        from core import igris_mision as imis

        m = await imis.sacar_mision(timeout=imis.poll_sueno_s())
        if m is None and imis.sargento_auto():
            for mision in imis.construir_misiones_sargento(self.tusk):
                await imis.encolar(mision)
            m = await imis.sacar_mision(timeout=0.05)
        if m is None:
            imis.marcar_sueno(True)
            return
        await self._ejecutar_mision(m)

    async def _ejecutar_mision(self, m: dict) -> None:
        from core import igris_mision as imis

        imis.set_mision_activa(m)
        imis.marcar_sueno(False)
        tipo = str(m.get("tipo") or "").lower()
        act = (m.get("activo") or "").upper() or None
        try:
            if tipo == "dormir":
                await self.bel.anotar("IGRIS", "MISION_DORMIR", f"origen={m.get('origen')}")
                return
            if tipo == "reducir":
                ok, motivo = imis.reducir_permitido(m)
                if not ok:
                    await self.bel.anotar(
                        "IGRIS", "REDUCIR_ESPERA_CONFIRMA",
                        f"{act or '—'}: {motivo} — no ejecuta sin confirmación",
                    )
                    return
                # Cableado: sin bisturí de campo hasta duda V11 / orden fina
                await self.bel.anotar(
                    "IGRIS", "REDUCIR_CABLEADO",
                    f"{act or '—'}: misión reducir confirmada — ejecución fina pendiente (duda V11)",
                )
                return
            if tipo in ("sembrar", "engordar", "corregir"):
                if act:
                    self._override_activo = act
                self._reset_bloque_mision()
                cap = float(m.get("usd_objetivo") or 0) or None
                origen = "BOOTSTRAP" if tipo == "sembrar" else "ENGORDE"
                ok = await self._inyectar_dual_paciente(
                    origen=origen, restante_usd_cap=cap,
                )
                await self.bel.anotar(
                    "IGRIS", "MISION_OK" if ok else "MISION_FALLIDA",
                    f"{tipo} {act or '—'} · origen={m.get('origen')}",
                )
                return
            await self.bel.anotar("IGRIS", "MISION_DESCONOCIDA", str(tipo))
        finally:
            self._override_activo = None
            imis.set_mision_activa(None)
            imis.marcar_sueno(True)

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
        """Compat: jurisdicción del activo actual (preferir lote vía auditar_manto_global)."""
        return self._consumir_kaiser_lote([self._activo_despliegue()])

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

    def _marcar_fail_cooldown(self, activo: str | None = None) -> None:
        wait = float(getattr(config, "IGRIS_ESPERA_COOLDOWN_S", 5.0))
        until = time.time() + wait
        act = (activo or self._override_activo or self._activo_despliegue() or "").upper()
        if act:
            self._engorde_fail_until_por[act] = until
        # legado: no bloquear todo el lote; solo el Santo que falló
        self._engorde_fail_until = until

    def _marcar_ritmo_engorde(self, activo: str | None = None) -> None:
        """Tras dual OK con ambas piernas llenas: aire antes del siguiente dual."""
        wait = float(getattr(config, "IGRIS_ENGORDE_RITMO_S", 15.0) or 0.0)
        if wait <= 0:
            return
        until = time.time() + wait
        act = (activo or self._override_activo or self._activo_despliegue() or "").upper()
        if act:
            self._engorde_ritmo_until_por[act] = until
        self._engorde_ritmo_until = until

    def _marcar_dual_fills(self, activo: str | None, ok_ambos: bool) -> None:
        act = (activo or self._override_activo or self._activo_despliegue() or "").upper()
        if not act:
            return
        self._dual_fills_ok_por[act] = bool(ok_ambos)

    def _dual_previo_confirmado(self, activo: str | None = None) -> bool:
        """True si no hay dual pendiente o ambas piernas Market del anterior llenaron."""
        act = (activo or self._override_activo or self._activo_despliegue() or "").upper()
        if not act:
            return True
        return bool(self._dual_fills_ok_por.get(act, True))

    def _engorde_en_espera(self, activo: str | None = None, ahora: float | None = None) -> bool:
        """True si fallo de puerta, ritmo post-dual o dual previo incompleto bloquean."""
        now = float(ahora if ahora is not None else time.time())
        act = (activo or self._override_activo or self._activo_despliegue() or "").upper()
        if act:
            if not self._dual_previo_confirmado(act):
                return True
            if now < float(self._engorde_fail_until_por.get(act, 0.0)):
                return True
            if now < float(self._engorde_ritmo_until_por.get(act, 0.0)):
                return True
        elif now < float(self._engorde_fail_until) or now < float(self._engorde_ritmo_until):
            return True
        return False

    async def auditar_manto_global(self):
        """Despliega el manto sobre TODO el lote en trabajo (paralelo), no de par en par."""
        if not await self._auditoria_pre_despliegue():
            return

        self._ejecucion_directa_activa = True
        if hasattr(self.tusk, "manto_cedido_a_greed"):
            self.tusk.manto_cedido_a_greed = False

        limpiar_toques_expirados(self.tusk)
        event_driven = getattr(config, "IGRIS_EVENT_DRIVEN", False)
        activos = self._activos_lote_trabajo()
        alertas = self._consumir_kaiser_lote(activos)

        pesos_manto = self._pesos_canal_manto()
        peso_l_total = sum(float((f or {}).get("long") or 0) for f in pesos_manto.values())
        peso_s_total = sum(float((f or {}).get("short") or 0) for f in pesos_manto.values())
        masa_bruta = peso_l_total + peso_s_total
        # Polvo heredado de bóveda (p.ej. LTC 0.1/0.1): en sim no bloquea bootstrap del lote
        masa_trabajo = masa_bruta
        if getattr(config, "MODO_SIMULACION", False) and masa_bruta > 0:
            from core import manto_ventana as mv
            usd_l0, usd_s0 = mv.usd_piernas_desde_pesos(pesos_manto)
            if (usd_l0 + usd_s0) < float(getattr(config, "IGRIS_SIM_POLVO_USD_MAX", 2.0) or 2.0):
                masa_trabajo = 0.0
        ahora = time.time()
        en_cooldown_rebalance = (ahora - self.ultimo_movimiento) <= self.cooldown_maniobra_s

        hay_eventos_lote = any(
            self._alertas_evento_para_activo(alertas, a) for a in activos
        )

        # Bootstrap — vacío o polvo: sembrar puerta en cada Santo del lote (paralelo)
        if masa_trabajo == 0:
            bootstrap_ok = True
            if event_driven:
                bootstrap_ok = (
                    hay_eventos_lote
                    or (
                        getattr(config, "IGRIS_BOOTSTRAP_ON_START", True)
                        and not self._bootstrap_inicial_hecho
                    )
                )
            if not bootstrap_ok:
                if ahora - self._ultimo_heartbeat_evento > float(
                    getattr(config, "IGRIS_EVENT_HEARTBEAT_S", 300)
                ):
                    self._ultimo_heartbeat_evento = ahora
                    await self.bel.anotar(
                        "IGRIS", "EVENT_IDLE",
                        f"Sin oportunidad Kaiser en lote ({len(activos)} Santos) — escudo en espera.",
                    )
                return

            self._bootstrap_inicial_hecho = True
            sembrados = 0
            for act in activos:
                # Con señales: solo Santos con evento. Sin señales (arranque): todo el lote.
                if event_driven and hay_eventos_lote:
                    if not self._alertas_evento_para_activo(alertas, act):
                        continue
                if self._engorde_en_espera(act, ahora):
                    continue
                self._override_activo = act
                self._reset_bloque_mision()
                try:
                    if await self._inyectar_dual_paciente(origen="BOOTSTRAP"):
                        sembrados += 1
                finally:
                    self._override_activo = None
            if sembrados:
                await self.bel.anotar(
                    "IGRIS", "BOOTSTRAP_LOTE",
                    f"Semilla dual en {sembrados}/{len(activos)} Santos del lote paralelo.",
                )
            return

        if event_driven and not hay_eventos_lote:
            return

        # Rebalanceo global (ventana). Monarca: no bloquea engorde dual Asalto.
        if (
            masa_bruta > 0
            and not en_cooldown_rebalance
            and not rebalanceo_en_pausa_por_greed(self.tusk)
        ):
            from core import manto_ventana as mv

            usd_l, usd_s = mv.usd_piernas_desde_pesos(pesos_manto)
            if usd_l + usd_s <= 0:
                usd_l, usd_s = float(peso_l_total), float(peso_s_total)
            ratio_l = mv.ratio_long_usd(usd_l, usd_s)
            banda_min, banda_max = self.calcular_banda_delta()
            no_bloquea = getattr(config, "IGRIS_VENTANA_NO_BLOQUEA_ENGORDE", True)
            if ratio_l > banda_max:
                await self.bel.anotar(
                    "IGRIS", "REBALANCEO",
                    f"Delta long {ratio_l*100:.1f}% > techo {banda_max*100:.0f}% (ventana 48-52 USD)",
                )
                await self._ejecutar_maniobra("REBALANCEO_IGRIS", "SHORT", self.tusk.masa_autorizada)
                if not no_bloquea:
                    return
            elif ratio_l < banda_min:
                await self.bel.anotar(
                    "IGRIS", "REBALANCEO",
                    f"Delta long {ratio_l*100:.1f}% < piso {banda_min*100:.0f}% (ventana 48-52 USD)",
                )
                await self._ejecutar_maniobra("REBALANCEO_IGRIS", "LONG", self.tusk.masa_autorizada)
                if not no_bloquea:
                    return

        from core import manto_ventana as mv
        from core import pase_director as pd

        usd_l, usd_s = mv.usd_piernas_desde_pesos(pesos_manto)
        if usd_l + usd_s <= 0:
            usd_l, usd_s = float(peso_l_total), float(peso_s_total)
        dir_engorde = mv.direccion_engorde_preferida(usd_l, usd_s)

        ok_engorde = False
        intentos = 0
        for act in activos:
            if self._engorde_en_espera(act, ahora):
                continue
            if event_driven and not self._alertas_evento_para_activo(alertas, act):
                continue
            if pd.director_activo():
                try:
                    eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0)
                    meta = pd.meta_engorde_usd(eq, act, tusk=self.tusk)
                    if float(meta.get("restante_usd") or 0) <= 0:
                        continue
                except Exception:
                    pass

            intentos += 1
            self._override_activo = act
            self._reset_bloque_mision()
            try:
                # Dual directo (sin reserva unilateral que abortaba por GLITCH)
                if await self._inyectar_dual_paciente(origen="ENGORDE"):
                    ok_engorde = True
            finally:
                self._override_activo = None

        if intentos:
            await self.bel.anotar(
                "IGRIS", "ENGORDE_LOTE",
                f"Latido paralelo · {intentos} Santos con puerta · "
                f"{'mordida' if ok_engorde else 'sin fill'} · lote={len(activos)}",
            )

        # ≥95%: solo aviso de lectura. §A no pilotéa (IGRIS_OXIGENO_PILOTO=false).
        margen_post = float(self.tusk.margen_ocupado)
        if mj.sobre_muro(margen_post) and not ok_engorde:
            if getattr(config, "IGRIS_OXIGENO_PILOTO", False):
                pass  # legado: aquí irían conductas §A — congelado
            await self.bel.anotar(
                "IGRIS", "OXIGENO_BAJO",
                f"Colchón: margen {margen_post:.1f}% ≥ horizonte {mj.muro_marcial():.0f}% "
                f"— aviso lectura · sin poda (IGRIS_PODA_AUTO=off).",
            )

    async def _ejecutar_maniobra_engorde(self, direccion: str) -> bool:
        """Engorde dual; retorna True si materializó."""
        masa = self.masa_paso_engorde()
        if masa <= 0:
            return False
        uid = f"IGRIS_ENGORDAR_MANTO_{str(uuid.uuid4())[:4]}"
        if not await self.tusk.solicitar_reserva(uid, masa, "IGRIS", direccion):
            return False
        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map:
            await self.tusk.liberar_reserva(uid)
            return False
        if estado == "ROJO":
            await self.tusk.liberar_reserva(uid)
            return False
        if estado == "GLITCH_DETECTADO" and not getattr(config, "MODO_SIMULACION", False):
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
            from core import igris_proteccion as iprot
            from core import mnt_manto_hedge as mmh

            exclusivos = iprot.activos_exclusivos()
            if exclusivos and mercado.activo_de_frente(frente) not in exclusivos:
                await self.tusk.liberar_reserva(uid)
                await self.bel.anotar(
                    "IGRIS", "FUERA_CANAL",
                    f"Abortado {frente}: canal exclusivo={exclusivos}",
                )
                return {"ok": False, "masa": 0.0, "precio": 0.0}

            # MNT Santo: long inverso + short lineal. Short inverso = legado sucio, no plantar.
            hedge_ok = False
            position_idx = None
            reduce_only = None
            if mmh.requiere_hedge_bidireccional(frente) or mmh.es_inverse_boveda(frente):
                amenaza = mmh.amenaza_netting_boveda(frente, direccion, modo_hedge=False)
                if amenaza == "short_inverso_es_boveda_no_manto":
                    await self.tusk.liberar_reserva(uid)
                    await self.bel.anotar(
                        "IGRIS", "BOVEDA_NO_MANTO",
                        f"Abortado {frente} SHORT: short inverso es legado sucio, no manto.",
                    )
                    return {"ok": False, "masa": 0.0, "precio": 0.0}
                if getattr(config, "IGRIS_MNT_HEDGE_OBLIGATORIO", False):
                    hr = await self.bridge.asegurar_modo_hedge(sym, category=cat or "inverse")
                    hedge_ok = bool(hr.exito)
                    if not hedge_ok:
                        await self.tusk.liberar_reserva(uid)
                        await self.bel.anotar(
                            "IGRIS", "HEDGE_REQUERIDO",
                            f"Sin modo bidireccional en {sym}: {hr.mensaje} — "
                            f"abrir long comería el short de bóveda.",
                        )
                        return {"ok": False, "masa": 0.0, "precio": 0.0}
                else:
                    hedge_ok = True
                amenaza = mmh.amenaza_netting_boveda(frente, direccion, modo_hedge=hedge_ok)
                if amenaza:
                    await self.tusk.liberar_reserva(uid)
                    await self.bel.anotar(
                        "IGRIS", "BOVEDA_NETTING",
                        f"Abortado {frente}/{direccion}: {amenaza}",
                    )
                    return {"ok": False, "masa": 0.0, "precio": 0.0}
                position_idx = mmh.position_idx_para(direccion, hedge=True)
                reduce_only = False  # abrir carril aislado; nunca reduceOnly

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

            px_ref = float(precio_fill or price or 0)
            aseg = lote.asegurar_qty_min_notional(
                float(masa), px_ref, frente, mode="ceil",
            )
            masa_q = float(aseg.get("qty") or 0)
            if not aseg.get("ok") or masa_q <= 0:
                await self.tusk.liberar_reserva(uid)
                await self.bel.anotar(
                    "IGRIS", "ORDEN_FALLIDA",
                    f"{frente} {direccion}: bajo minNotional "
                    f"(~{aseg.get('min_usd', 5)} USD) · {aseg.get('motivo')}",
                )
                self._marcar_fail_cooldown(self._override_activo or self._activo_despliegue())
                return {"ok": False, "masa": 0.0, "precio": 0.0}
            res = await self.bridge.place_order(
                sym, side, masa_q, category=cat, order_type=order_type, price=price,
                position_idx=position_idx, reduce_only=reduce_only,
            )
            if not res.exito:
                await self.tusk.liberar_reserva(uid)
                msg = str(res.mensaje or "")
                await self.bel.anotar("IGRIS", "ORDEN_FALLIDA", f"{frente} {direccion}: {msg}")
                if "110094" in msg or "minimum order value" in msg.lower():
                    self._marcar_fail_cooldown(
                        self._override_activo or self._activo_despliegue()
                    )
                return {"ok": False, "masa": 0.0, "precio": 0.0}
            fill = await self.bridge.esperar_fill(
                sym,
                order_id=res.order_id,
                link_id=getattr(res, "link_id", None) or None,
                category=cat,
                timeout_s=timeout,
            )
            if not fill.exito and order_type == "Market":
                # Reintento corto: history/exec a veces va detrás del Market ya hecho.
                fill = await self.bridge.esperar_fill(
                    sym,
                    order_id=res.order_id,
                    link_id=getattr(res, "link_id", None) or None,
                    category=cat,
                    timeout_s=min(8.0, max(3.0, float(timeout) * 0.25)),
                    intervalo_s=0.8,
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
        """Asalto → Market · personalizado → Limit si hay precio (legado táctico unificado)."""
        try:
            from core import pase_director as pd
            if not pd.director_activo():
                return "Market", None
            perfil = pd.perfil_marcha()
            if perfil.get("force_market"):
                return "Market", None
            # personalizado: Preferir Limit al precio de oportunidad cuando hay ref
            if str(perfil.get("id")) == "personalizado" and float(precio_fill or 0) > 0:
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
        masa_l: float,
        masa_s: float,
        ask_l: float,
        bid_s: float,
        *,
        usd_l: float = 0.0,
        usd_s: float = 0.0,
    ) -> bool:
        """
        Ambas piernas a la vez con qty nativa por frente (Ley de la Masa).
        Equilibrio post-fill en USD, no en unidades de contrato mezcladas.
        Solo True si ambas piernas llenaron (o salvavidas cerró el hueco).
        """
        from core import lote_bybit as lote

        activo = (self._override_activo or self._activo_despliegue() or "").upper()
        timeout = float(getattr(config, "IGRIS_DUAL_FILL_TIMEOUT_S", 20))
        lim = lote.asim_masa_lim_activo()
        r_l, r_s = await asyncio.gather(
            self._materializar_en_frente(
                uid_l, frente_l, "LONG", float(masa_l), ask_l, fill_timeout_s=timeout,
            ),
            self._materializar_en_frente(
                uid_s, frente_s, "SHORT", float(masa_s), bid_s, fill_timeout_s=timeout,
            ),
        )
        ok_l = bool(r_l.get("ok"))
        ok_s = bool(r_s.get("ok"))
        filled_l = float(r_l.get("masa") or 0)
        filled_s = float(r_s.get("masa") or 0)
        px_l = float(r_l.get("precio") or ask_l or 0)
        px_s = float(r_s.get("precio") or bid_s or 0)
        filt_l = lote.filtros_lote(frente_l)
        filt_s = lote.filtros_lote(frente_s)
        usd_fill_l = lote.qty_a_usd(filled_l, px_l, filt_l) if filled_l > 0 else 0.0
        usd_fill_s = lote.qty_a_usd(filled_s, px_s, filt_s) if filled_s > 0 else 0.0
        usd_ref = max(
            (usd_fill_l + usd_fill_s) / 2.0 if (usd_fill_l + usd_fill_s) > 0 else 0.0,
            float(usd_l or 0),
            float(usd_s or 0),
            1e-9,
        )

        async def _cerrar(ok: bool) -> bool:
            self._marcar_dual_fills(activo, ok)
            if not ok:
                self._marcar_fail_cooldown(activo)
                await self.bel.anotar(
                    "IGRIS", "DUAL_FILLS_PENDIENTE",
                    f"{activo}: no ambas piernas llenas — bloqueado nuevo par Market",
                )
            return ok

        if ok_l and ok_s:
            diff_usd = usd_fill_l - usd_fill_s
            tol = max(usd_ref * lim, 1e-6)
            # Cirugía: no empatar $ al toque — siguiente bocado asimétrico
            empate = bool(getattr(config, "IGRIS_DUAL_SALVAVIDAS_EMPATE", False))
            if empate and abs(diff_usd) > tol:
                if diff_usd > 0:
                    conv = lote.qty_espejo_usd(abs(diff_usd), bid_s, frente_s, mode="ceil")
                    if not conv.get("ok") or float(conv.get("qty") or 0) <= 0:
                        await self.bel.anotar(
                            "IGRIS", "LEY_MASA_BLOQUEO",
                            f"Equilibrio S no cuantiza · diff=${diff_usd:.2f}",
                        )
                        return await _cerrar(False)
                    uid_fix = f"{uid_s}_EQ"
                    r = await self._salvavidas_market_pierna(
                        uid_fix, frente_s, "SHORT", float(conv["qty"]), bid_s,
                    )
                    return await _cerrar(bool(r.get("ok")))
                conv = lote.qty_espejo_usd(abs(diff_usd), ask_l, frente_l, mode="ceil")
                if not conv.get("ok") or float(conv.get("qty") or 0) <= 0:
                    await self.bel.anotar(
                        "IGRIS", "LEY_MASA_BLOQUEO",
                        f"Equilibrio L no cuantiza · diff=${diff_usd:.2f}",
                    )
                    return await _cerrar(False)
                uid_fix = f"{uid_l}_EQ"
                r = await self._salvavidas_market_pierna(
                    uid_fix, frente_l, "LONG", float(conv["qty"]), ask_l,
                )
                return await _cerrar(bool(r.get("ok")))
            if abs(diff_usd) > tol:
                await self.bel.anotar(
                    "IGRIS", "BOCADO_DIFERIDO",
                    f"{activo}: diff=${diff_usd:.2f} → siguiente bocado corrige (sin empate Market)",
                )
            return await _cerrar(True)

        emerg = bool(
            getattr(config, "IGRIS_DUAL_SALVAVIDAS_EMERGENCIA", True)
            or getattr(config, "IGRIS_DUAL_SALVAVIDAS_MARKET", True)
        )
        if not emerg:
            await self.bel.anotar(
                "IGRIS", "DUAL_INCOMPLETO",
                f"L={ok_l}(${usd_fill_l:.2f}) S={ok_s}(${usd_fill_s:.2f}) · emergencia off",
            )
            return await _cerrar(False)

        if ok_l and not ok_s:
            usd_target = usd_fill_l if usd_fill_l > 0 else float(usd_s or usd_l or 0)
            conv = lote.qty_espejo_usd(usd_target, bid_s, frente_s, mode="ceil")
            if not conv.get("ok"):
                await self.bel.anotar(
                    "IGRIS", "LEY_MASA_BLOQUEO",
                    f"Salvavidas S bloqueado · no espejo ${usd_target:.2f}",
                )
                return await _cerrar(False)
            r = await self._salvavidas_market_pierna(
                uid_s, frente_s, "SHORT", float(conv["qty"]), bid_s,
            )
            return await _cerrar(bool(r.get("ok")))
        if ok_s and not ok_l:
            usd_target = usd_fill_s if usd_fill_s > 0 else float(usd_l or usd_s or 0)
            conv = lote.qty_espejo_usd(usd_target, ask_l, frente_l, mode="ceil")
            if not conv.get("ok"):
                await self.bel.anotar(
                    "IGRIS", "LEY_MASA_BLOQUEO",
                    f"Salvavidas L bloqueado · no espejo ${usd_target:.2f}",
                )
                return await _cerrar(False)
            r = await self._salvavidas_market_pierna(
                uid_l, frente_l, "LONG", float(conv["qty"]), ask_l,
            )
            return await _cerrar(bool(r.get("ok")))

        # Market pudo llenar en Bybit aunque el Bridge no viera history a tiempo.
        try:
            if hasattr(self.tusk, "reconciliar_con_exchange") and self.bridge:
                await self.tusk.reconciliar_con_exchange(self.bridge)
        except Exception:
            pass
        try:
            pesos = getattr(self.tusk, "pesos", None) or {}
            masa_l2 = float((pesos.get(frente_l) or {}).get("long") or 0)
            masa_s2 = float((pesos.get(frente_s) or {}).get("short") or 0)
            if masa_l2 > 0 and masa_s2 > 0:
                await self.bel.anotar(
                    "IGRIS", "DUAL_OK_RECON",
                    f"Bridge timeout pero Tusk ve L+S · L={masa_l2} S={masa_s2}",
                )
                self._marcar_ritmo_engorde(activo)
                return await _cerrar(True)
        except Exception:
            pass
        await self.bel.anotar(
            "IGRIS", "DUAL_FALLIDO",
            f"Ninguna pierna llenó · L={frente_l} S={frente_s}",
        )
        return await _cerrar(False)

    async def _auditoria_pre_despliegue(self) -> bool:
        """Candado de bóveda — umbrales dinámicos desde motor X/A_base (rangos_activo)."""
        # Solo la arena salta el grado Beru (Mundo A / LIVE_TESTNET abolido)
        sin_rangos = (
            getattr(config, "ARENA_IGRIS_ACTIVA", False)
            and getattr(config, "ARENA_IGRIS_SIN_RANGOS", False)
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
        origen: str = "LIVE_MAINNET",
    ) -> dict:
        """
        Dual §E mainnet (Bridge place_order) con tope de notional por pata.
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
            else float(getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0) or 5.0)
        )
        ok = await self._inyectar_dual_paciente(origen=origen, restante_usd_cap=cap)
        return {"activo": activo_u, "ok": ok, "max_usd": cap}

    async def _asegurar_apalancamiento_max(
        self, activo: str | None = None, *, origen: str = "ENGORDE"
    ) -> bool:
        """Fuerza densidad máxima del Santo (inv+lin). Avisa si Bybit baja el techo.

        No bloquea el manto: True salvo sim/sin bridge. Fallo parcial → aviso Bellion.
        """
        if config.MODO_SIMULACION or not self.bridge:
            return True
        if not ilev.force_max_on():
            return True
        act = (activo or self._override_activo or self._activo_despliegue() or "").upper()
        if not act:
            return True
        if not self._lev_force_gate.due(act):
            return True
        try:
            await ilev.forzar_max_leverage_activo(self.bridge, self.bel, act)
        except Exception as e:
            await self.bel.anotar(
                "IGRIS", "LEVERAGE_MAX_AVISO",
                f"{act} · excepción forzando máx ({origen}): {e}",
            )
        self._lev_force_gate.mark(act)
        return True

    async def _asegurar_apalancamiento_aspirante_eth(self) -> bool:
        """Compat: ETH bootstrap usa el ritual general de densidad máxima."""
        return await self._asegurar_apalancamiento_max("ETH", origen="BOOTSTRAP")

    async def forzar_densidad_maxima_lote(self, activos: list[str] | None = None) -> dict:
        """Arranque Arise / ritual Monarca: todo el lote a máx apalancamiento."""
        if config.MODO_SIMULACION or not self.bridge:
            return {"ok": True, "omitido": True}
        return await ilev.forzar_max_leverage_lote(self.bridge, self.bel, activos)

    def _pesos_canal_manto(self) -> dict:
        """Pesos del manto operable: exclusivos o lote; short bóveda MNT = 0 en ventana."""
        from core import mnt_manto_hedge as mmh
        from core import igris_manto as im

        pesos = getattr(self.tusk, "pesos", None) or {}
        exclusivos = [
            str(a).upper()
            for a in (getattr(config, "IGRIS_ACTIVOS_EXCLUSIVOS", None) or [])
            if a
        ]
        if exclusivos:
            out = {}
            for act in exclusivos:
                try:
                    fl, fs = im.frentes_bootstrap(act)
                except Exception:
                    continue
                if fl in pesos:
                    out[fl] = pesos[fl]
                if fs in pesos:
                    out[fs] = pesos[fs]
            return mmh.pesos_sin_boveda_short(out)
        # Sin exclusivos: todos los pesos, pero short inverso bóveda fuera de la ventana
        return mmh.pesos_sin_boveda_short(dict(pesos))

    def _activos_lote_trabajo(self) -> list[str]:
        """Todos los Santos/activos del lote abierto (paralelo), no un solo foco."""
        from core import igris_proteccion as iprot
        from core import pase_director as pd

        if not pd.director_activo():
            return iprot.filtrar_activos_trabajo([self._activo_despliegue()])
        eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        try:
            pd.sincronizar_logrados_desde_tusk(self.tusk, eq)
        except Exception:
            pass
        plan = pd.plan_lote(eq)
        trabajo = list(plan.get("trabajo") or [])
        if not trabajo:
            return iprot.filtrar_activos_trabajo([self._activo_despliegue()])
        # Orden: 1) sin espejo dual (reponer huérfanos/SOL) 2) más atrasados
        scored: list[tuple[int, float, int, str]] = []
        for i, p in enumerate(trabajo):
            act = str(p["activo"]).upper()
            need = max(
                pd.need_notional_grado_usd(act, str(p.get("grado") or "SOLDADO")),
                1.0,
            )
            have = pd.notional_manto_usd(self.tusk, act)
            sin_espejo = 0 if not self._espejo_dual_completo(act) else 1
            scored.append((sin_espejo, have / need, i, act))
        scored.sort()
        # únicos preservando orden
        out: list[str] = []
        seen: set[str] = set()
        for _, __, ___, act in scored:
            if act not in seen:
                seen.add(act)
                out.append(act)
        # Canal exclusivo (si hay). MNT es Santo: entra al lote salvo pausa explícita.
        return iprot.filtrar_activos_trabajo(out)

    def _espejo_dual_completo(self, activo: str) -> bool:
        """True si el Santo ya tiene L inverso + S lineal vivos."""
        try:
            fl, fs = im.frentes_bootstrap(str(activo).upper())
            pesos = getattr(self.tusk, "pesos", None) or {}
            pl = float((pesos.get(fl) or {}).get("long") or 0)
            ps = float((pesos.get(fs) or {}).get("short") or 0)
            return pl > 0 and ps > 0
        except Exception:
            return True

    def _reset_bloque_mision(self) -> None:
        self._bloque_objetivo_usd = 0.0
        self._bloque_inyectado_usd = 0.0

    def _consumir_kaiser_lote(self, activos: list[str]) -> list:
        """Alertas Kaiser de todos los activos del lote en trabajo."""
        if not self.kaiser:
            self._alertas_kaiser_cache = []
            return []
        try:
            raw = self.kaiser.consumir("IGRIS")
        except Exception:
            raw = []
        from core import igris_despliegue as ides

        filtradas: list = []
        for act in activos:
            filtradas.extend(ides.filtrar_alertas_jurisdiccion(raw, act))
        # dedupe por id/mensaje
        seen: set[str] = set()
        out: list = []
        for a in filtradas:
            key = str(a.get("id") or a.get("mensaje") or id(a))
            if key in seen:
                continue
            seen.add(key)
            out.append(a)
        self._alertas_kaiser_cache = out
        return out

    def _activo_despliegue(self) -> str:
        """Activo del manto en este micro-disparo (override de lote o foco legado)."""
        from core import igris_proteccion as iprot

        if self._override_activo:
            act = str(self._override_activo).upper()
            filtrado = iprot.filtrar_activos_trabajo([act])
            return filtrado[0] if filtrado else (iprot.activos_exclusivos() or ["ETH"])[0]
        from core import plan_crecimiento as pc
        from core import pase_director as pd

        exclusivos = iprot.activos_exclusivos()
        if exclusivos:
            return exclusivos[0]

        sin_rangos = (
            getattr(config, "ARENA_IGRIS_ACTIVA", False)
            and getattr(config, "ARENA_IGRIS_SIN_RANGOS", False)
        )
        if sin_rangos:
            act = (self._activo_beru or config.TICKER_BASE or "ETH").upper()
            filtrado = iprot.filtrar_activos_trabajo([act])
            return filtrado[0] if filtrado else "ETH"

        eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        if pd.director_activo():
            try:
                pd.sincronizar_logrados_desde_tusk(self.tusk, eq)
            except Exception:
                pass
            act = pd.activo_manto_foco(eq, tusk=self.tusk)
            filtrado = iprot.filtrar_activos_trabajo([act])
            if filtrado:
                return filtrado[0]
            if exclusivos:
                return exclusivos[0]
            return "ETH"

        if pc.rank_gate_activo():
            act = pc.activo_manto_preferido(eq)
            filtrado = iprot.filtrar_activos_trabajo([act])
            return filtrado[0] if filtrado else "ETH"
        rango = self._rango_progresion or ""
        if rango == "ASPIRANTE":
            return "ETH"
        act = (self._activo_beru or config.TICKER_BASE or "ETH").upper()
        filtrado = iprot.filtrar_activos_trabajo([act])
        return filtrado[0] if filtrado else "ETH"

    def _asegurar_bloque_usd(self, activo: str, precio_ref: float) -> float:
        """
        Misión simétrica: objetivo = notional por pata ($L = $S).
        Con director de pase: meta = nocional L+S del grado − ya desplegado
        (p.ej. Soldado ETH ~1250 → ~625/pata). Capital delta_usd queda en el ranking.
        Sin director: Beru-grade + Doctrina B hacia horizonte 95%.
        """
        if self._bloque_objetivo_usd > 0 and self._bloque_inyectado_usd < self._bloque_objetivo_usd:
            return max(0.0, self._bloque_objetivo_usd - self._bloque_inyectado_usd)

        from core import pase_director as pd

        # Ranking → meta nocional del grado: no engordar de más el paso foco
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
            # Dual L+S: cada pata lleva la mitad del restante nocional del grado
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
            det = bc.margen_piernas_para_friccion(activo, bc.friccion_soldado_pct())
            im_ref = float(det["im_total_usd"] or 0)
            # Hueco de margen → nocional de una pata (escala el manto Soldado)
            if im_ref > 0 and hueco_pct > 0:
                notional_pata_h = float(det["notional_pierna_usd"]) * (
                    (equity * hueco_pct) / im_ref
                )
            else:
                notional_pata_h = 0.0
            objetivo_h = max(objetivo, notional_pata_h) if hueco_pct > 0 else objetivo
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
        extra = ""
        if puerta.get("motivo") in ("libro_stale", "libro_divergente_ticker"):
            extra = (
                f" edadL={puerta.get('edad_libro_long_s', '—')} "
                f"edadS={puerta.get('edad_libro_short_s', '—')} "
                f"lim={puerta.get('stale_lim_s', '—')}"
            )
            if puerta.get("divergencia"):
                extra += f" div={puerta['divergencia'].get('div_pct')}%"
        await self.bel.anotar(
            "IGRIS", tag,
            f"{puerta.get('motivo')} · spread={puerta.get('spread_pct', '—')} "
            f"umbral={puerta.get('umbral_pct', '—')} tau_h={puerta.get('tau_h', '—')} "
            f"freq={puerta.get('pct_frecuencia', '—')} modo={puerta.get('modo_paciencia', '—')} "
            f"frac={puerta.get('fraccion', '—')} calor={puerta.get('calor', '—')} "
            f"askL={puerta.get('ask_long', 0):.4f} bidS={puerta.get('bid_short', 0):.4f}"
            f"{extra}",
        )

    def _intentar_reconciliar_dual_fills(self, activo: str | None = None) -> bool:
        """Si hubo dual incompleto pero Tusk ya muestra L y S, liberar candado."""
        act = (activo or self._override_activo or self._activo_despliegue() or "").upper()
        if not act or self._dual_previo_confirmado(act):
            return True
        try:
            fl, fs = im.frentes_bootstrap(act)
            pesos = getattr(self.tusk, "pesos", None) or {}
            pl = pesos.get(fl) or {}
            ps = pesos.get(fs) or {}
            masa_l = float(pl.get("long") or 0)
            masa_s = float(ps.get("short") or 0)
            if masa_l > 0 and masa_s > 0:
                self._marcar_dual_fills(act, True)
                return True
        except Exception:
            pass
        return False

    async def _inyectar_dual_paciente(self, *, origen: str, restante_usd_cap: float | None = None) -> bool:
        """
        Ritual único bootstrap/engorde: dual §E, Ask/Bid, fees±urgencia invertida,
        mordida = techo_misión × fracción(confianza) hasta 100%.
        No dispara otro Market pair si el dual anterior no confirmó fills L+S.
        """
        activo = self._activo_despliegue()
        self._intentar_reconciliar_dual_fills(activo)
        if self._engorde_en_espera(activo):
            return False
        frente_l, frente_s = im.frentes_bootstrap(activo)

        # Densidad máxima siempre (Asalto/personalizado): no solo ETH bootstrap
        await self._asegurar_apalancamiento_max(activo, origen=origen)

        ctx_map, estado = await self.tank.vision_especulativa()
        if not ctx_map:
            await self._anotar_espera_spread(
                "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                {"motivo": "tank_sin_vision", "spread_pct": "—", "umbral_pct": "—",
                 "ask_long": 0, "bid_short": 0},
            )
            return False
        if estado == "ROJO":
            asalto_sin_rojo = getattr(config, "IGRIS_ASALTO_SIN_TANK_ROJO", True)
            if asalto_sin_rojo:
                try:
                    from core import pase_director as pd
                    pm = pd.perfil_marcha() if pd.director_activo() else {}
                    asalto_sin_rojo = bool(pm.get("force_market")) or str(pm.get("id")) == "asalto"
                except Exception:
                    asalto_sin_rojo = True
            if not asalto_sin_rojo:
                await self._anotar_espera_spread(
                    "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                    {"motivo": "tank_rojo", "spread_pct": "—", "umbral_pct": "—",
                     "ask_long": 0, "bid_short": 0, "modo_paciencia": estado},
                )
                return False
        # Sim: glitch de consenso (nodos congelados/divergentes) no bloquea fill ilusorio
        if estado == "GLITCH_DETECTADO" and not getattr(config, "MODO_SIMULACION", False):
            asalto_sin_rojo = getattr(config, "IGRIS_ASALTO_SIN_TANK_ROJO", True)
            if asalto_sin_rojo:
                try:
                    from core import pase_director as pd
                    pm = pd.perfil_marcha() if pd.director_activo() else {}
                    asalto_sin_rojo = bool(pm.get("force_market")) or str(pm.get("id")) == "asalto"
                except Exception:
                    asalto_sin_rojo = True
            if not asalto_sin_rojo:
                await self._anotar_espera_spread(
                    "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                    {"motivo": "tank_glitch", "spread_pct": "—", "umbral_pct": "—",
                     "ask_long": 0, "bid_short": 0, "modo_paciencia": estado},
                )
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
            # Ojos estrechos: visión puede no traer todos los frentes del lote
            pl = ides.precio_ticker_frente(self.tank, frente_l)
            ps = ides.precio_ticker_frente(self.tank, frente_s)
            precio_ref = (pl + ps) / 2.0 if pl > 0 and ps > 0 else max(pl, ps)
        if precio_ref <= 0:
            await self._anotar_espera_spread(
                "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                {"motivo": "sin_precio_ref", "spread_pct": "—", "umbral_pct": "—",
                 "ask_long": 0, "bid_short": 0},
            )
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

        # Ojos frescos: si el muro WS está viejo/divergente, muleta REST antes de la puerta
        from core import igris_ojos as ojos

        diag = await ojos.asegurar_libros_frescos(
            self.tank, self.bridge, [frente_l, frente_s],
        )
        if not diag.get("ok"):
            # Aun sin REST OK: la puerta devolverá libro_stale — anotar una vez vía puerta
            pass
        elif any(r.get("ok") for r in (diag.get("rest") or [])):
            await self.bel.anotar(
                "IGRIS", "OJOS_REST",
                f"{activo}: muleta REST rellenó libro · "
                f"{[r.get('frente') for r in diag.get('rest') or [] if r.get('ok')]}",
            )

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
        self._registrar_ley_masa(activo, puerta)
        if not puerta.get("ok"):
            await self._anotar_espera_spread(
                "BOOTSTRAP_ESPERA_SPREAD" if origen == "BOOTSTRAP" else "ENGORDE_ESPERA_SPREAD",
                puerta,
            )
            self._marcar_fail_cooldown(activo)
            return False

        micro_usd = float(puerta["micro_usd"])
        masa_l = float(puerta.get("masa_long") or 0)
        masa_s = float(puerta.get("masa_short") or 0)
        usd_l = float(puerta.get("usd_long") or micro_usd)
        usd_s = float(puerta.get("usd_short") or micro_usd)
        ask_l = float(puerta["ask_long"])
        bid_s = float(puerta["bid_short"])

        # Bocado asimétrico: corrige registro L/S en este dual (no salvavidas empate)
        if getattr(config, "IGRIS_BOCADO_ASIMETRICO", True) and restante > 0:
            from core import igris_bocado as iboc
            from core import lote_bybit as lote

            ulh, ush = iboc.usd_piernas_activo(self.tusk, activo)
            boc = iboc.bocado_asimetrico_usd(
                ulh, ush, float(restante) * 2.0,
                frente_l=frente_l, frente_s=frente_s, px_l=ask_l, px_s=bid_s,
            )
            if boc.get("ok") and str(boc.get("ajuste") or "").startswith("mas_"):
                cl = lote.cuantizar_presupuesto_usd(
                    float(boc["usd_long"]), ask_l, frente_l, mode="ceil",
                )
                cs = lote.cuantizar_presupuesto_usd(
                    float(boc["usd_short"]), bid_s, frente_s, mode="ceil",
                )
                if cl.get("ok") and cs.get("ok"):
                    masa_l = float(cl["qty"])
                    masa_s = float(cs["qty"])
                    usd_l = float(cl["usd"])
                    usd_s = float(cs["usd"])
                    micro_usd = max(usd_l, usd_s)
                    await self.bel.anotar(
                        "IGRIS", "BOCADO_ASIM",
                        f"{activo}: {boc.get('ajuste')} · "
                        f"L=${usd_l:.2f} S=${usd_s:.2f} (have Δ={boc.get('diff_have_usd')})",
                    )

        if masa_l <= 0 or masa_s <= 0:
            # Candado duro: sin qtys nativas de Ley de la Masa no hay disparo
            self._registrar_ley_masa(
                activo,
                {**puerta, "ok": False, "motivo": "sin_masa_nativa", "ley_masa": puerta.get("ley_masa") or {"ok": False, "motivo": "sin_masa_nativa"}},
            )
            await self.bel.anotar(
                "IGRIS", "LEY_MASA_BLOQUEO",
                f"Sin masa_long/short · puerta={puerta.get('motivo')} · "
                f"asim={((puerta.get('ley_masa') or {}).get('asim_pct'))}",
            )
            return False

        # Reserva Tusk en USD (unidad de paridad del manto), no en coin mezclado
        masa_reserva = max(micro_usd, usd_l, usd_s)
        piso_min = float(puerta.get("piso_mordida_usd") or 0)
        if getattr(config, "IGRIS_RESERVA_AJUSTAR_A_AUTH", True):
            auth = float(getattr(self.tusk, "masa_autorizada", 0) or 0)
            frac = float(getattr(config, "IGRIS_RESERVA_AUTH_FRAC", 0.92) or 0.92)
            cap = max(0.0, auth * frac)
            if masa_reserva > cap + 1e-9 and cap > 0:
                if piso_min > 0 and cap + 1e-9 < piso_min:
                    await self._anotar_espera_spread(
                        "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                        {
                            **puerta,
                            "motivo": "reserva_auth_bajo_piso",
                            "micro_usd": masa_reserva,
                            "auth_cap": round(cap, 4),
                            "piso_mordida_usd": piso_min,
                        },
                    )
                    return False
                scale = cap / masa_reserva
                micro_usd = round(micro_usd * scale, 4)
                usd_l = round(usd_l * scale, 4)
                usd_s = round(usd_s * scale, 4)
                masa_l = masa_l * scale
                masa_s = masa_s * scale
                masa_reserva = max(micro_usd, usd_l, usd_s)
                await self.bel.anotar(
                    "IGRIS", "RESERVA_AJUSTADA_AUTH",
                    f"{activo}: mordida→${masa_reserva:.2f} (auth_cap=${cap:.2f})",
                )

        # Sin abortar por horizonte 95%: la puerta de asimetría dispara aunque rebase.
        # Banda Δ en USD del Santo en foco (nunca qty inversa vs lineal mezclada —
        # eso bloqueaba el lote completo con ETH "634 L / 0.33 S" en unidades distintas).
        # Short inverso MNT legado (sucio) fuera del manto vía pesos_sin_boveda_short.
        from core import manto_ventana as mv
        from core import mnt_manto_hedge as mmh

        pesos = mmh.pesos_sin_boveda_short(getattr(self.tusk, "pesos", None) or {})
        pesos_act = {
            frente_l: pesos.get(frente_l) or {},
            frente_s: pesos.get(frente_s) or {},
        }
        usd_l0, usd_s0 = mv.usd_piernas_desde_pesos(pesos_act)
        banda_ok = mv.verificar_post_maniobra(
            usd_l0 + float(usd_l), usd_s0 + float(usd_s), operativo=True,
        )
        if not banda_ok:
            if (
                (
                    getattr(config, "ARENA_IGRIS_ACTIVA", False)
                    and getattr(config, "ARENA_IGRIS_SIN_BANDA_DELTA", True)
                )
                or getattr(config, "IGRIS_VENTANA_NO_BLOQUEA_ENGORDE", True)
            ):
                pass  # Asalto: dual §E manda; ventana no castra mordida
            else:
                await self._anotar_espera_spread(
                    "ENGORDE_ESPERA_SPREAD",
                    {**puerta, "motivo": "banda_delta_dual"},
                )
                return False

        uid_l = f"IGRIS_{origen[:4]}_L_{str(uuid.uuid4())[:4]}"
        uid_s = f"IGRIS_{origen[:4]}_S_{str(uuid.uuid4())[:4]}"

        if not await self.tusk.solicitar_reserva(uid_l, masa_reserva, "IGRIS", "LONG"):
            await self._anotar_espera_spread(
                "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                {**puerta, "motivo": "reserva_long_denegada", "micro_usd": masa_reserva},
            )
            return False
        # Espejo: misma masa ya cubierta por el corte L — no cobrar oxígeno 2×
        if not await self.tusk.solicitar_reserva(
            uid_s, masa_reserva, "IGRIS", "SHORT", consumir_auth=False,
        ):
            await self.tusk.liberar_reserva(uid_l)
            await self._anotar_espera_spread(
                "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                {**puerta, "motivo": "reserva_short_denegada", "micro_usd": masa_reserva},
            )
            return False

        # Disparo dual: qty nativa por pierna (Alfa Lineal → Espejo Inverso)
        if not await self._disparo_dual_simultaneo(
            uid_l, uid_s, frente_l, frente_s, masa_l, masa_s, ask_l, bid_s,
            usd_l=usd_l, usd_s=usd_s,
        ):
            await self._anotar_espera_spread(
                "ENGORDE_ESPERA_SPREAD" if origen == "ENGORDE" else "BOOTSTRAP_ESPERA_SPREAD",
                {**puerta, "motivo": "disparo_dual_fallido"},
            )
            return False

        self._bloque_inyectado_usd += micro_usd
        if self._bloque_inyectado_usd >= self._bloque_objetivo_usd - 1e-6:
            from core import pase_director as pd
            if pd.director_activo():
                eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
                try:
                    marked = pd.marcar_foco_si_bloque_completo(eq, activo, tusk=self.tusk)
                    if marked:
                        await self.bel.anotar(
                            "IGRIS", "PASE_PASO",
                            f"Paso logrado · {activo} · logrados {marked.get('pasos_logrados')}",
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
        self._marcar_ritmo_engorde(activo)

        tag = "BOOTSTRAP_MANTO" if origen == "BOOTSTRAP" else "ENGORDE_DUAL"
        await self.bel.anotar(
            "IGRIS", tag,
            f"§E L {frente_l}@{ask_l:.4f} / S {frente_s}@{bid_s:.4f} | "
            f"masa ${micro_usd:.2f} (Alfa ${float(puerta.get('alfa_usd') or 0):.2f}) "
            f"qty L={masa_l:g}/S={masa_s:g} "
            f"USD L=${usd_l:.2f}/S=${usd_s:.2f} | "
            f"frac={puerta.get('fraccion')} calor={puerta.get('calor')} | "
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

        # Poda/espejos auto desarmados de raíz (ley Monarca 2026-08-09)
        if tipo in ("PODAR_MANTO", "LIMPIAR_ESPEJOS") and not getattr(
            config, "IGRIS_PODA_AUTO", False
        ):
            await self.bel.anotar(
                "IGRIS", "PODA_DESARMADA",
                f"Maniobra {tipo} bloqueada · IGRIS_PODA_AUTO=false",
            )
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
            from core import mnt_manto_hedge as mmh

            # No podar short inverso legado (saneo = mano del Monarca, no auto)
            if mmh.es_inverse_boveda(frente) and dir_key == "short":
                await self.tusk.liberar_reserva(uid)
                await self.bel.anotar(
                    "IGRIS", "BOVEDA_NO_PODA",
                    f"No se poda short bóveda {frente}",
                )
                return False
            position_idx = None
            reduce_only = None
            if mmh.requiere_hedge_bidireccional(frente):
                hr = await self.bridge.asegurar_modo_hedge(sym, category=cat or "inverse")
                if not hr.exito:
                    await self.tusk.liberar_reserva(uid)
                    return False
                # Cerrar long manto = Sell en idx 1 reduceOnly
                position_idx = 1 if dir_key == "long" else 2
                reduce_only = True
            res = await self.bridge.place_order(
                sym, side, extraida, category=cat,
                position_idx=position_idx, reduce_only=reduce_only,
            )
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

        self.ultimo_movimiento = time.time()
        self._marcar_fail_cooldown(activo)
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
