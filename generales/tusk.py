import asyncio
import time
import json
import os
import core.config as config 

class TuskBoveda:
    def __init__(self, bellion):
        """
        Tusk: El Tesorero de Hierro. 
        Gestiona el capital, las sombras (Berus) y la persistencia atómica.
        """
        self.bel = bellion 
        self._lock = asyncio.Lock()
        
        # 🛡️ RUTA DE PERSISTENCIA
        ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ruta_data = os.path.join(ruta_base, "data", "tusk_data.json")

        # Visión de Precios
        self.precio_perp = self.precio_spot = self.precio_inverse = self.ultimo_precio = 0.0    
        
        # 🟢 MUELLES DINÁMICOS: Se llenan al vuelo según la moneda que cace Beru
        self.pesos = {} 

        # 💉 MASA OPERATIVA (Inicialmente simulada, lista para NAV Real)
        self.masa_bruta = 100.0         # Para visualización en Dashboard
        self.masa_bruta_real = 100.0    # Capital total bajo gestión
        self.margen_ocupado = 0.0       # % de uso en Bybit
        self.masa_autorizada = 100.0    # Energía disponible para nuevas sombras
        self.total_maintenance_margin_usd = None  # Lectura cruda wallet UNIFIED (Bybit)
        self.account_mm_rate = None               # accountMMRate crudo (Bybit)
        self.telemetria_posiciones_manto: dict | None = None  # Panel — posiciones Long/Short
        self.tesoreria: dict | None = None        # Visión UTA: MNT/hedge/oxígeno de guerra
        self.disponible_uta_usd: float | None = None
        
        self.masa_reservada_ltc = 0.0   # Masa en tránsito (no confirmada aún)
        self.referencia_escalon = 0.0   # Nivel de potencia actual
        self.reservas_activas = {}      # Registro de soldados (Sombras) en combate
        
        self.total_ciclos_consumados = 0
        self.toques_greed_manto: dict = {}
        self.greed_basis_abiertos: list = []
        self.nivel_monarca = "ASPIRANTE"
        self.tier_beru_aplicado = str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))
        # Jurisdicción manto Igris→Greed
        self.cola_ordenes_manto: list = []
        self.manto_cedido_a_greed: bool = False
        self._verificar_infraestructura()

    # === [SUBTEMA: INFRAESTRUCTURA Y PERSISTENCIA] ===

    def _verificar_infraestructura(self):
        """Asegura que el cofre de datos exista."""
        os.makedirs(os.path.dirname(self.ruta_data), exist_ok=True)
        if not os.path.exists(self.ruta_data):
            with open(self.ruta_data, "w") as f:
                json.dump({"total_ciclos_consumados": 0, "reservas": {}}, f)

    async def latido_persistencia(self, legion):
        """Guarda el estado cada 10s con blindaje contra corrupciones."""
        while True:
            try:
                data = {
                    "total_ciclos_consumados": self.total_ciclos_consumados,
                    "reservas": {}
                }
                if legion:
                    for barco in legion:
                        if hasattr(barco, '__dict__'):
                            data["reservas"][barco.uid] = vars(barco)
                
                # Sellado atómico: escribe en temporal y luego renombra
                ruta_temp = self.ruta_data + ".tmp"
                with open(ruta_temp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                
                if os.path.exists(ruta_temp):
                    if os.path.exists(self.ruta_data): os.remove(self.ruta_data)
                    os.rename(ruta_temp, self.ruta_data)
            except Exception:
                pass # Silenciado para no manchar la consola de la terminal
            await asyncio.sleep(10)

# === [SUBTEMA: GESTIÓN DE CAPITAL Y PRECIOS] ===

    async def actualizar_precios(self, p_perp, p_spot, p_inv):
        """Inyecta la verdad de los precios desde Tank."""
        async with self._lock:
            self.precio_perp, self.precio_spot, self.precio_inverse = p_perp, p_spot, p_inv
            self.ultimo_precio = p_perp 

    async def actualizar_nav_real(
        self,
        balance_total: float,
        margen_real: float,
        *,
        total_maintenance_margin: float | None = None,
        account_mm_rate: float | None = None,
        disponible_uta: float | None = None,
        wallet_account: dict | None = None,
        posiciones: list | None = None,
    ):
        """
        Inyecta el balance real desde Bybit.
        Con TUSK_TESORERIA_ACTIVA: masa_autorizada = oxígeno de guerra (disponible − colchón).
        """
        async with self._lock:
            self.masa_bruta = balance_total
            self.masa_bruta_real = balance_total
            self.margen_ocupado = margen_real
            if total_maintenance_margin is not None:
                self.total_maintenance_margin_usd = total_maintenance_margin
            if account_mm_rate is not None:
                self.account_mm_rate = account_mm_rate
            if disponible_uta is not None:
                self.disponible_uta_usd = float(disponible_uta)

            base = config.ESCALON_POTENCIA_BASE
            factor_seguro = max(config.FACTOR_MASA_AUTORIZADA, 0.001)
            self.referencia_escalon = (balance_total // base) * base
            masa_escalon = self.referencia_escalon / factor_seguro

            tesoreria_on = bool(getattr(config, "TUSK_TESORERIA_ACTIVA", True))
            if tesoreria_on and wallet_account is not None:
                from core import tusk_tesoreria as tt
                self.tesoreria = tt.construir_tesoreria(
                    wallet_account, posiciones=posiciones,
                )
                # Oxígeno de guerra manda (disponible UTA − colchón); no el escalón /10
                self.masa_autorizada = max(
                    0.0, float(self.tesoreria.get("oxigeno_guerra_usd") or 0.0),
                )
            elif tesoreria_on and disponible_uta is not None:
                from core import tusk_tesoreria as tt
                o2 = tt.oxigeno_guerra_usd(balance_total, float(disponible_uta))
                self.masa_autorizada = float(o2["oxigeno_guerra_usd"])
                self.tesoreria = {
                    "ts": time.time(),
                    "fuente": "disponible_solo",
                    "equity_usd": round(balance_total, 4),
                    "disponible_usd": round(float(disponible_uta), 4),
                    "oxigeno_guerra_usd": o2["oxigeno_guerra_usd"],
                    "colchon_objetivo_usd": o2["colchon_objetivo_usd"],
                    "ya_reservado_usd": o2["ya_reservado_usd"],
                    "extra_colchon_usd": o2["extra_colchon_usd"],
                    "reserva_monarca_pct": o2["reserva_pct"],
                    "masa_escalon_ref": round(masa_escalon, 4),
                    "estado": tt.estado_tesoreria(
                        equity=balance_total,
                        disponible=float(disponible_uta),
                        mm_rate=account_mm_rate,
                    ),
                    "nota": (
                        "Oxígeno = min(disponible, equity×(1−reserva)). "
                        "IM hedge dentro del colchón."
                    ),
                }
            else:
                self.masa_autorizada = masa_escalon
            if self.tesoreria is not None and "masa_escalon_ref" not in self.tesoreria:
                self.tesoreria["masa_escalon_ref"] = round(masa_escalon, 4)

            from core import plan_crecimiento as pc
            plan = pc.nivel_por_equity(balance_total)
            self.nivel_monarca = plan["nivel"]
            self.tier_beru_aplicado = plan["tier_aplicado"]

            if self.total_ciclos_consumados % 50 == 0:
                ox_txt = ""
                if self.tesoreria:
                    ox_txt = (
                        f" | O2 guerra: {self.tesoreria.get('oxigeno_guerra_usd')} "
                        f"({self.tesoreria.get('estado')})"
                    )
                await self.bel.anotar(
                    "TUSK", "NAV_SYNC",
                    f"Capital: {balance_total:.2f} | Masa auth: {self.masa_autorizada:.2f} "
                    f"| Margen: {margen_real:.2f}%{ox_txt}",
                )

    def snapshot_tesoreria(self) -> dict:
        """Bloque para estado_vivo / panel."""
        if self.tesoreria:
            return dict(self.tesoreria)
        return {
            "ts": time.time(),
            "fuente": "cero",
            "equity_usd": float(self.masa_bruta_real or self.masa_bruta or 0),
            "disponible_usd": self.disponible_uta_usd,
            "oxigeno_guerra_usd": float(self.masa_autorizada or 0),
            "masa_autorizada": float(self.masa_autorizada or 0),
            "estado": "justa",
            "nota": "Sin snapshot UTA aún — esperando NAV.",
        }

    async def auditar_escalones_universales(self, margen_real: float):
        """Ajuste rápido de potencia si el margen fluctúa sin cambio de balance total."""
        async with self._lock:
            self.margen_ocupado = margen_real
            base = config.ESCALON_POTENCIA_BASE
            factor_seguro = max(config.FACTOR_MASA_AUTORIZADA, 0.001)
            
            self.referencia_escalon = (margen_real // base) * base
            self.masa_autorizada = self.referencia_escalon / factor_seguro

    # === [SUBTEMA: LOGÍSTICA DE SOMBRAS (PUENTE DE HIERRO)] ===

    async def solicitar_reserva(
        self,
        uid: str,
        masa: float,
        general: str,
        direccion: str = "LONG",
        *,
        consumir_auth: bool = True,
    ) -> bool:
        """Puente para que Beru/Igris pidan masa al sistema dinámico.

        consumir_auth=False: registra la pierna espejo sin restar otra vez el oxígeno
        (dual L+S = un corte de aire, no dos).
        """
        async with self._lock:
            masa_f = float(masa or 0)
            # 1. Filtro de Oxígeno (solo si consume)
            if consumir_auth and self.masa_autorizada < masa_f:
                return False

            # 2. Materialización de la sombra (masa siempre registrada; auth aparte)
            if uid not in self.reservas_activas:
                self.reservas_activas[uid] = type('Sombra', (object,), {
                    'uid': uid,
                    'masa': masa_f,
                    'direccion': direccion,
                    'estado': 'ACECHANDO',
                    'consumio_auth': bool(consumir_auth),
                })

            # 3. Reserva de energía (oxígeno) — Beru neutro no consume
            if consumir_auth:
                self.masa_autorizada -= masa_f
                self.masa_reservada_ltc += masa_f
            return True

    async def confirmar_reserva(
        self,
        uid: str,
        frente: str,
        direccion: str,
        fill_confirmado=True,
        precio_fill: float | None = None,
        fee_usd: float | None = None,
    ):
        """
        Fija el peso de la sombra en un muelle real.
        En MODO_SIMULACION=False, requiere fill_confirmado=True (caller debe verificar).
        """
        if not config.MODO_SIMULACION and not fill_confirmado:
            await self.bel.anotar("TUSK", "ANCLAJE_RECHAZADO",
                                  f"Modo live: fill no confirmado para {uid} en {frente}")
            return False

        async with self._lock:
            if uid in self.reservas_activas:
                sombra = self.reservas_activas[uid]
                dir_key = "long" if direccion == "LONG" else "short"

                from core import igris_manto as im
                im.asegurar_peso(self.pesos, frente)

                if precio_fill and precio_fill > 0:
                    im.actualizar_promedio(
                        self.pesos, frente, direccion, sombra.masa, precio_fill,
                        fee_usd=float(fee_usd or 0),
                    )
                elif fee_usd and fee_usd > 0:
                    key_fee = "fees_paid_long" if direccion == "LONG" else "fees_paid_short"
                    self.pesos[frente][key_fee] = float(self.pesos[frente].get(key_fee) or 0) + float(fee_usd)
                self.pesos[frente][dir_key] += sombra.masa
                # Ya anclada: sale del tránsito
                self.reservas_activas.pop(uid, None)
                if getattr(sombra, "consumio_auth", True):
                    self.masa_reservada_ltc = max(0.0, self.masa_reservada_ltc - sombra.masa)
                await self.bel.anotar("TUSK", "ANCLAJE", f"Masa {sombra.masa:.4f} fijada en {frente}.")
                return True
        return False

    async def liberar_reserva(self, uid: str):
        """Devuelve la masa al cofre si la misión falla (solo si consumió oxígeno)."""
        async with self._lock:
            if uid in self.reservas_activas:
                sombra = self.reservas_activas.pop(uid)
                if getattr(sombra, "consumio_auth", True):
                    self.masa_autorizada += sombra.masa
                    self.masa_reservada_ltc = max(0.0, self.masa_reservada_ltc - sombra.masa)

    async def consumar_cosecha_atomica(self, uid_reserva, frente_salida, barco_ref):
        """Cierra el ciclo y recupera la energía tras una victoria."""
        async with self._lock:
            if uid_reserva in self.reservas_activas:
                sombra = self.reservas_activas.pop(uid_reserva)
                self.masa_reservada_ltc -= sombra.masa
                self.masa_autorizada += sombra.masa
                self.total_ciclos_consumados += 1
                await self.bel.anotar("TUSK", "ÉXITO", f"Ciclo {self.total_ciclos_consumados} sellado.")

    # === RECONCILIACIÓN CON EXCHANGE (Fase 2.4) ===

    async def reconciliar_con_exchange(self, bridge):
        """
        Compara posiciones reales (linear + inverse) con pesos internos.
        Corrige discrepancias y registra en Bellion.
        Solo opera si MODO_SIMULACION=False y hay sesión activa.
        Guardar tamaño nativo + precio medio (linear) para que Igris vea acumulado USD.
        """
        if config.MODO_SIMULACION or not bridge or not bridge.session:
            return True

        from core import igris_manto as im

        try:
            posiciones_reales: dict[str, dict] = {}
            queries = (
                {"category": "linear", "settleCoin": "USDT"},
                {"category": "inverse"},
            )
            errores = 0
            for kwargs in queries:
                try:
                    response = bridge.session.get_positions(**kwargs)
                except Exception as e:
                    errores += 1
                    await self.bel.anotar(
                        "TUSK", "RECONCILIACIÓN_ERROR",
                        f"{kwargs}: {e}",
                    )
                    continue
                if response.get("retCode") != 0:
                    errores += 1
                    await self.bel.anotar(
                        "TUSK", "RECONCILIACIÓN_ERROR",
                        f"{kwargs}: {response.get('retMsg', '?')}",
                    )
                    continue
                cat = str(kwargs.get("category") or "")
                for pos in response.get("result", {}).get("list", []) or []:
                    symbol = str(pos.get("symbol") or "")
                    side = str(pos.get("side") or "")
                    size = float(pos.get("size") or 0)
                    if size <= 0 or not symbol:
                        continue
                    frente = self._symbol_a_frente(symbol, category=cat)
                    avg = float(pos.get("avgPrice") or pos.get("markPrice") or 0)
                    if frente not in posiciones_reales:
                        posiciones_reales[frente] = {
                            "long": 0.0,
                            "short": 0.0,
                            "precio_medio_long": 0.0,
                            "precio_medio_short": 0.0,
                        }
                    dir_key = "long" if side == "Buy" else "short"
                    px_key = "precio_medio_long" if dir_key == "long" else "precio_medio_short"
                    prev_sz = float(posiciones_reales[frente][dir_key])
                    prev_px = float(posiciones_reales[frente].get(px_key) or 0)
                    posiciones_reales[frente][dir_key] = prev_sz + size
                    if avg > 0:
                        new_sz = prev_sz + size
                        if prev_sz > 0 and prev_px > 0:
                            posiciones_reales[frente][px_key] = (
                                prev_sz * prev_px + size * avg
                            ) / new_sz
                        else:
                            posiciones_reales[frente][px_key] = avg

            async with self._lock:
                discrepancias = 0
                for frente, real in posiciones_reales.items():
                    interno = self.pesos.get(frente) or {"long": 0.0, "short": 0.0}
                    diff_l = abs(real["long"] - float(interno.get("long") or 0))
                    diff_s = abs(real["short"] - float(interno.get("short") or 0))
                    if diff_l > 0.0001 or diff_s > 0.0001 or frente not in self.pesos:
                        discrepancias += 1
                        pf = im.asegurar_peso(self.pesos, frente)
                        pf["long"] = float(real["long"])
                        pf["short"] = float(real["short"])
                        if real.get("precio_medio_long"):
                            pf["precio_medio_long"] = float(real["precio_medio_long"])
                        if real.get("precio_medio_short"):
                            pf["precio_medio_short"] = float(real["precio_medio_short"])
                        await self.bel.anotar(
                            "TUSK", "RECONCILIACIÓN",
                            f"{frente}: interno L:{float(interno.get('long') or 0):.6f}/"
                            f"S:{float(interno.get('short') or 0):.6f} → "
                            f"real L:{real['long']:.6f}/S:{real['short']:.6f}",
                        )

                for frente in list(self.pesos.keys()):
                    if frente not in posiciones_reales:
                        row = self.pesos.get(frente) or {}
                        if float(row.get("long") or 0) > 0.0001 or float(row.get("short") or 0) > 0.0001:
                            discrepancias += 1
                            await self.bel.anotar(
                                "TUSK", "RECONCILIACIÓN_FANTASMA",
                                f"{frente} existe interno pero no en exchange → reseteando",
                            )
                            self.pesos[frente] = {
                                "long": 0.0,
                                "short": 0.0,
                                "precio_medio_long": 0.0,
                                "precio_medio_short": 0.0,
                            }

                if discrepancias:
                    await self.bel.anotar(
                        "TUSK", "RECONCILIACIÓN_OK",
                        f"{discrepancias} frentes alineados con exchange",
                    )

            # Ambas queries fallidas → ciego: no mentir "OK" a Igris
            if errores >= len(queries):
                await self.bel.anotar(
                    "TUSK", "RECONCILIACIÓN_CIEGO",
                    "No se pudo leer linear ni inverse — abortar manos/semilla",
                )
                return False
            return True

        except Exception as e:
            await self.bel.anotar("TUSK", "RECONCILIACIÓN_EXCEPCIÓN", str(e))
            return False

    async def actualizar_telemetria_posiciones(self, bridge):
        """Lee posiciones abiertas en Bybit — solo telemetría para el panel."""
        from core.telemetria_igris import telemetria_desde_exchange, telemetria_desde_pesos

        equity = float(self.masa_bruta_real or self.masa_bruta or 0)

        if config.MODO_SIMULACION or not bridge or not bridge.session:
            self.telemetria_posiciones_manto = telemetria_desde_pesos(dict(self.pesos), equity)
            return

        try:
            posiciones: list[dict] = []
            # linear USDT + inverse (sin settleCoin: MNTUSD/ETHUSD aparecen aquí)
            queries = (
                {"category": "linear", "settleCoin": "USDT"},
                {"category": "inverse"},
            )
            for kwargs in queries:
                try:
                    resp = bridge.session.get_positions(**kwargs)
                except Exception:
                    continue
                if resp.get("retCode") != 0:
                    continue
                for p in resp.get("result", {}).get("list", []) or []:
                    if float(p.get("size") or 0) > 0:
                        posiciones.append(p)

            if posiciones:
                self.telemetria_posiciones_manto = telemetria_desde_exchange(posiciones, equity)
            else:
                self.telemetria_posiciones_manto = telemetria_desde_pesos(dict(self.pesos), equity)
        except Exception:
            self.telemetria_posiciones_manto = telemetria_desde_pesos(dict(self.pesos), equity)

    def snapshot_telemetria_posiciones(self) -> dict:
        from core.telemetria_igris import telemetria_desde_pesos

        if self.telemetria_posiciones_manto:
            return self.telemetria_posiciones_manto
        equity = float(self.masa_bruta_real or self.masa_bruta or 0)
        return telemetria_desde_pesos(dict(self.pesos), equity)

    async def hilo_reconciliacion(self, bridge):
        """Al arrancar + cada 60s: pesos alineados con exchange (acumulado visible a Igris)."""
        # Primera pasada pronta (no esperar 10s: Igris necesita have al despertar)
        await asyncio.sleep(1)
        while True:
            await self.actualizar_telemetria_posiciones(bridge)
            if not config.MODO_SIMULACION:
                await self.reconciliar_con_exchange(bridge)
            await asyncio.sleep(60)

    def _symbol_a_frente(self, symbol, category: str | None = None):
        """Traduce símbolo Bybit al nombre interno del frente."""
        s = str(symbol or "").upper()
        cat = (category or "").lower()
        if cat == "inverse" or (
            s.endswith("USD") and not s.endswith("USDT") and not s.endswith("USDC")
        ):
            return f"{s}_INVERSE"
        mapa = {
            "LTCUSDT": "LTCUSDT_LINEAL",
            "LTCUSDC": "LTCUSDC_SPOT",
            "BTCUSDT": "BTCUSDT_LINEAL",
            "BTCUSDC": "BTCUSDC_SPOT",
            "ETHUSDT": "ETHUSDT_LINEAL",
            "ETHUSDC": "ETHUSDC_SPOT",
        }
        if s in mapa:
            return mapa[s]
        if s.endswith("USDT") or s.endswith("USDC"):
            return f"{s}_LINEAL"
        return f"{s}_LINEAL"

    def export_for_bellion(self):
        return {
            "pesos": {f: dict(p) for f, p in self.pesos.items()},
            "margen_ocupado": self.margen_ocupado,
            "masa_autorizada": self.masa_autorizada,
            "masa_bruta": self.masa_bruta,
            "masa_bruta_real": self.masa_bruta_real,
            "total_ciclos_consumados": self.total_ciclos_consumados,
            "precio_perp": self.precio_perp,
            "precio_spot": self.precio_spot,
        }

    def restaurar_desde_bellion(self, data):
        if not data:
            return
        self.pesos = data.get("pesos", self.pesos) or {}
        self.margen_ocupado = data.get("margen_ocupado", self.margen_ocupado)
        self.masa_autorizada = data.get("masa_autorizada", self.masa_autorizada)
        self.masa_bruta = data.get("masa_bruta", self.masa_bruta)
        self.masa_bruta_real = data.get("masa_bruta_real", self.masa_bruta_real)
        self.total_ciclos_consumados = data.get("total_ciclos_consumados", self.total_ciclos_consumados)