from __future__ import annotations

import asyncio
import uuid
import time

from core.models import BeruShip
from core import mercado
from core import beru_tier
from core import beru_rail
from core import beru_cazador
from core import beru_continuo
from core import beru_altar_cazador
from core import beru_altar_nativo
from core import beru_rafaga
# Fósiles históricos se conservan en core para auditoría, pero la ruta viva
# no los importa: negociar, fusionar, residual y Mega no son Beru vigente.
from core import beru_wake
from core import beru_ley
from core import beru_fantasma
from core import beru_ensayo
import core.config as config


class BeruCazador:
    def __init__(self, tusk, bellion, tank, bridge=None, kaiser=None):
        """
        Beru: El Cazador — dueño de la casa (spot).
        Decide frente stable (USDT/USDC/…), ejecuta CAZA/COSECHA vía Bridge.
        Wake: 0 del manto · flota · cazador puro · manos solo si BERU_MANOS.
        Fantasma: BERU_MANOS_FANTASMA → bitácora. Mixto: Mariscales también.
        Ensayo nivel 3: BERU_ENSAYO_NIVEL3 → manos chiquitas + techo + consola.
        """
        self.tusk = tusk
        self.bel = bellion
        self.tank = tank
        self.bridge = bridge
        self.kaiser = kaiser
        self.legion = []
        self._flota_sembrada = False
        self._altar_tareas: dict[str, asyncio.Task] = {}
        try:
            self.tank.capitan_activo = beru_wake.adn_capitan_wake()
        except Exception:
            pass

    def _tier_efectivo(self) -> str:
        tid = getattr(self.tusk, "tier_beru_aplicado", None)
        if tid:
            return str(tid)
        return str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1"))

    def _cronica(self, beru, tipo: str, detalle: str = "", **extra):
        """Append al pergamino Sub-Santuario (data/beru/cronicas/)."""
        try:
            from core import beru_asset_detail as bad
            act = bad.activo_de_legionario(beru, self._activo_casa())
            bad.append_cronica(
                act,
                {
                    "tipo": tipo,
                    "uid": getattr(beru, "uid", ""),
                    "detalle": detalle,
                    "direccion": str(getattr(beru, "direccion", "") or "") or None,
                    "precio": float(getattr(beru, "precio_salida_real", 0) or 0)
                    or float(extra.pop("precio", 0) or 0)
                    or None,
                    **extra,
                },
            )
        except Exception:
            pass

    def _bitacora(self, evento: str, beru: BeruShip | None = None, detalle: str = "", **extra):
        """Mismo pergamino para papel y Mariscal vivo (disparos.jsonl)."""
        vivo = bool(beru is not None and self._manos_exchange(beru))
        if not (vivo or self._manos_fantasma()):
            return
        if beru is not None:
            extra.setdefault("uid", getattr(beru, "uid", None))
            extra.setdefault("activo", self._activo_de_barco(beru))
            extra.setdefault("estado", getattr(beru, "estado", None))
            extra.setdefault("direccion", getattr(beru, "direccion", None))
            extra.setdefault("grado", beru_altar_cazador.grado_de_barco(beru))
            modo = str(getattr(beru, "hoz_modo", "") or "")
            if modo:
                extra.setdefault("hoz_modo", modo)
            raf = float(getattr(beru, "masa_rafaga_usd", 0) or 0)
            if raf > 0:
                extra.setdefault("masa_rafaga_usd", raf)
            link = str(getattr(beru, "altar_link_id", "") or "")
            if link and extra.get("altar_link_id") is None:
                extra["altar_link_id"] = link
        try:
            beru_fantasma.registrar(evento, detalle=detalle, vivo=vivo, **extra)
        except Exception:
            pass

    def _llamado_ahogado(self, beru: BeruShip, motivo: str, **extra) -> None:
        """La oreja disparó y la garganta no armó — no volver a morir mudo."""
        extra.setdefault("motivo", motivo)
        self._bitacora(
            "LLAMADO_AHOGADO",
            beru,
            detalle=motivo,
            **{k: v for k, v in extra.items() if v is not None},
        )
        act = extra.get("activo") or self._activo_de_barco(beru)
        print(
            f"[BERU] Llamado ahogado {act} {getattr(beru, 'direccion', '')} · {motivo}",
            flush=True,
        )

    def _altar_en_vuelo(self, beru: BeruShip) -> bool:
        uid = str(getattr(beru, "uid", "") or "")
        t = self._altar_tareas.get(uid)
        return bool(t is not None and not t.done())

    def _lanzar_altar(self, beru: BeruShip, coro) -> None:
        """Cada Santo arma su Hoz sin congelar al resto de la legión."""
        uid = str(getattr(beru, "uid", "") or "")
        if not uid:
            try:
                coro.close()
            except Exception:
                pass
            return
        previa = self._altar_tareas.get(uid)
        if previa is not None and not previa.done():
            beru.altar_rependiente = True
            try:
                coro.close()
            except Exception:
                pass
            return
        task = asyncio.create_task(coro)
        self._altar_tareas[uid] = task

        def _limpio(done, u=uid, barco=beru):
            if self._altar_tareas.get(u) is done:
                self._altar_tareas.pop(u, None)
            resultado = None
            try:
                resultado = done.result()
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                print(f"[BERU] Altar {u} cayó: {exc}", flush=True)
                resultado = False
            if str(getattr(barco, "estado", "") or "").upper() != "CAZANDO":
                return
            if bool(getattr(barco, "altar_rependiente", False)):
                self._pedir_mover_hoz(barco)
                return
            if resultado is False:
                from core import beru_rafaga
                from core import beru_continuo as bc

                if beru_rafaga.es_radar(barco):
                    return
                if not bc.carta_hoz_viva(barco):
                    self._volver_acecho_sin_carta(barco)

        task.add_done_callback(_limpio)

    def _volver_acecho_sin_carta(self, beru: BeruShip) -> None:
        """Planta falló: acecha otra vez y Tusk suelta el oxígeno."""
        from core import beru_continuo as bc

        bc.restaurar_acecho_tras_fallo_armado(beru)
        self._bitacora(
            "CAZA_SIN_CARTA",
            beru,
            detalle="planta falló · vuelve a acechar (no caza fantasma)",
        )

        async def _oxigeno():
            try:
                await self.tusk.liberar_reserva(beru.uid)
                await self.tusk.liberar_reserva(f"E_{beru.uid}")
            except Exception:
                pass

        try:
            asyncio.get_running_loop().create_task(_oxigeno())
        except RuntimeError:
            pass

    def _activo_casa(self) -> str:
        """Casa spot: en ensayo = Santos elegidos; si no, pase / semilla."""
        # Nivel 2/3: no saltar a ETH/OP del pase — solo manto bajo ensayo
        if beru_fantasma.activo() or beru_ensayo.activo():
            ens = (
                beru_ensayo.activos_ensayo()
                if beru_ensayo.activo()
                else beru_fantasma.activos_ensayo()
            )
            for act in ens:
                if self._precio_de_activo(act) > 0:
                    return act
            if ens:
                return ens[0]
            return beru_rail.activo_semilla()
        try:
            from core import pase_director as pd
            from core import plan_crecimiento as pc
            eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
            if pd.director_activo():
                # Preferir Santo logrado que esté en flota y con precio
                logs = pd.cargar_progreso().get("pasos_logrados") or []
                for n in sorted(logs, reverse=True):
                    paso = pd.paso_por_n(int(n))
                    if not paso:
                        continue
                    act = str(paso["activo"]).upper()
                    if self._precio_de_activo(act) > 0:
                        return act
                for n in sorted(logs, reverse=True):
                    paso = pd.paso_por_n(int(n))
                    if paso:
                        return str(paso["activo"]).upper()
                return pd.activo_manto_foco(eq)
            if pc.rank_gate_activo():
                return pc.activo_manto_preferido(eq)
        except Exception:
            pass
        return beru_rail.activo_semilla()

    def _activo_de_barco(self, beru: BeruShip | None = None) -> str:
        """Santo del barco (UID SEM_BCH_…) — no forzar casa ADA en flota."""
        from core import beru_asset_detail as bad

        return bad.activo_de_legionario(beru, self._activo_casa()) if beru else self._activo_casa()

    def _precio_de_barco(self, beru: BeruShip | None = None) -> float:
        act = self._activo_de_barco(beru)
        return self._precio_de_activo(act)

    def _beru_caza_permitida(self, activo: str | None = None) -> bool:
        # Fantasma / ensayo nivel 3: Santos del ritual, sin sellos del pase Igris.
        if self._manos_fantasma() or beru_ensayo.activo():
            return True
        try:
            from core import pase_director as pd
            if not pd.director_activo():
                return True
            eq = float(self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
            act = (activo or self._activo_casa()).upper()
            return pd.beru_puede_cazar(act, eq, tusk=self.tusk)
        except Exception:
            return True

    def _manos_activas(self) -> bool:
        return beru_wake.manos_beru_activas()

    def _manos_fantasma(self) -> bool:
        return beru_wake.manos_fantasma_activas() or beru_fantasma.activo()

    def _ensayo_nivel3(self) -> bool:
        return beru_wake.ensayo_nivel3_activo() or beru_ensayo.activo()

    def _manos_exchange(self, beru: BeruShip | None = None) -> bool:
        """Hoz nativa en Bybit. Con lista mixta, solo esos Santos."""
        if config.MODO_SIMULACION or self.bridge is None:
            return False
        if not self._manos_activas():
            return False
        listed = beru_wake.activos_manos_reales()
        if listed:
            if beru is None:
                return False
            return beru_wake.manos_reales_de_activo(self._activo_de_barco(beru))
        return not self._manos_fantasma()

    def _precio_de_activo(self, activo: str) -> float:
        """Ojo Beru: solo last price spot. Sin fallback lineal/inverso."""
        from core import beru_ojos

        return beru_ojos.last_spot_desde_tank(self.tank, activo)

    def _precio_casa(self):
        """Beru acecha solo con last spot; si no hay → ciego (0)."""
        act = self._activo_casa()
        return self._precio_de_activo(act)

    def _refrescar_ceros_manto(self) -> int:
        """Igris engordó → refresca 0 absoluto; no mueve el tramo en curso."""
        n = 0
        for beru in self.legion:
            act = self._activo_de_barco(beru)
            vivo = beru_cazador.centro_manto_desde_tusk(
                self.tusk, act, fallback_global=False,
            )
            if beru_continuo.aplicar_cero_manto(beru, vivo):
                n += 1
        return n

    def _tier_barco(self, beru: BeruShip) -> beru_tier.BeruGridTier:
        tid = getattr(beru, "tier_id", None) or self._tier_efectivo()
        return beru_tier.tier_por_id(tid)

    def _modo_barco(self, beru: BeruShip) -> beru_tier.ModoCombate:
        _ = beru
        return "CAZA"

    @staticmethod
    def _es_tumor_legacy(beru: BeruShip) -> bool:
        estado = str(getattr(beru, "estado", "") or "").upper()
        modo = str(getattr(beru, "modo_combate", "") or "").upper()
        return bool(
            modo == "NEGOCIADOR"
            or getattr(beru, "neg_post_cazador", False)
            or getattr(beru, "ciclo_infinito", False)
            or getattr(beru, "es_super_beru", False)
            or float(getattr(beru, "masa_congelada", 0) or 0) > 0
            or estado in {
                "NEGOCIANDO",
                "ESPERANDO_CONDICIONAL",
                "ESPERANDO_ABISMO",
                "FUSIONADO",
            }
        )

    def _cuarentena_tumores(self) -> int:
        """Ningún estado viejo entra al pulso del cazador nuevo."""
        n = 0
        for beru in self.legion:
            if self._es_tumor_legacy(beru):
                beru.estado = "FOSIL_BLOQUEADO"
                beru.modo_combate = "CAZA"
                n += 1
        return n

    # === PULSO VITAL Y GENERACIÓN ===

    async def hilo_beru_berserker(self):
        while True:
            if not bool(getattr(config, "BERU_HILO_ENABLED", False)):
                # Cableado dormido: no pulso de combate hasta orden Monarca
                await asyncio.sleep(1.0)
                continue
            try:
                await self._pulso_berserker()
            except Exception as exc:
                print(f"[BERU] Pulso de la legión falló (reintenta): {exc}", flush=True)
                await asyncio.sleep(0.25)

    async def _pulso_berserker(self):
        precio = self._precio_casa()
        if precio <= 0.0:
            if not any(self._precio_de_barco(b) > 0 for b in self.legion):
                await asyncio.sleep(0.05)
                return

        # 0 vivo del manto (Igris engordó) → reproyectar % → precios
        self._refrescar_ceros_manto()
        # Tumor viejo = cuarentena individual. No congela a los Santos sanos.
        self._cuarentena_tumores()

        if beru_wake.siembra_flota_activa():
            if not self._flota_sembrada:
                precios_flota = {}
                for act in beru_wake.catalogo_ojos_desde_foto():
                    px_act = self._precio_de_activo(act)
                    if px_act > 0:
                        precios_flota[act] = px_act
                if precio > 0:
                    precios_flota.setdefault(self._activo_casa(), precio)
                self.despertar_flota_reset_0(precios_flota)
                self._flota_sembrada = True
        elif not any(
            b.estado in ("ACECHANDO", "CAZANDO")
            for b in self.legion
        ):
            if precio > 0:
                self.plantar_semilla_adan(precio)

        latidos = self._consumir_latidos_legion()
        await self.auditar_gatillos_adan(latidos=latidos)
        await self.sincronizar_materializacion()
        # El precio “casa” ya no manda el acordeón: cada barco oye su Santo.
        await self.ejecutar_acordeon_asimetrico(precio, latidos=latidos)
        self.limpiar_legion()
        await asyncio.sleep(0.01)

    def _centro_cazador(self, beru: BeruShip | None = None) -> float:
        """0 vivo del manto Igris; actualiza el barco si cambió."""
        act = self._activo_de_barco(beru) if beru else None
        vivo = beru_cazador.centro_manto_desde_tusk(
            self.tusk, act, fallback_global=False,
        )
        if vivo > 0 and beru is not None:
            beru_continuo.aplicar_cero_manto(beru, vivo)
            return float(beru.centro_manto or vivo)
        if beru and beru.centro_manto > 0:
            return beru.centro_manto
        return float(vivo or 0)

    def _siguiente_capa(self, direccion: str) -> int:
        numeradas = [
            b.capa for b in self.legion
            if b.direccion == direccion
            and b.estado not in ("FUSIONADO", "ACECHANDO")
        ]
        return max(numeradas, default=0) + 1

    def _aplicar_grid_cazador(self, beru: BeruShip, touch_pct: float) -> None:
        """Sangre fósil: no usa el pulso vivo. El cazador arma desde el 0 local."""
        centro = self._centro_cazador(beru)
        beru.centro_manto = centro
        beru.oz_pct, beru.red_pct = beru_cazador.niveles_desde_toque(touch_pct)
        beru.oz_adan, beru.red_adan = beru_cazador.sincronizar_precios_grid(
            centro, beru.oz_pct, beru.red_pct,
        )

    def plantar_semilla_adan(self, precio_actual, activo: str | None = None):
        """Siembra cazador continuo; metro del manto; 0 local = precio de wake."""
        act = (activo or self._activo_casa()).upper()
        if not self._beru_caza_permitida(act):
            return None
        px = float(precio_actual or 0.0)
        if px <= 0:
            return None
        centro_manto = beru_cazador.centro_manto_desde_tusk(
            self.tusk, act, fallback_global=False,
        )
        if centro_manto <= 0:
            return None
        tier_id = beru_wake.tier_siembra_activo(act, tusk=self.tusk)
        if not tier_id:
            return None
        exigido = beru_wake.tier_manos_exigido(act)
        if exigido and str(tier_id).upper() != exigido:
            return None
        semilla = beru_wake.crear_semilla_wake(
            act,
            px,
            tier_id=tier_id,
            generacion=1,
        )
        beru_wake.aplicar_centro_manto_wake(
            semilla, px, tusk_centro=centro_manto,
        )
        try:
            self.tank.capitan_activo = beru_wake.adn_capitan_wake()
            semilla.adn_capitan = beru_wake.adn_capitan_wake()
        except Exception:
            pass
        self.legion.append(semilla)
        return semilla

    def despertar_flota_reset_0(
        self,
        precios_por_activo: dict[str, float] | None = None,
        *,
        equity_usd: float | None = None,
    ) -> int:
        """Nace un Beru por Santo permitido — 0 = precio wake. Manos no disparan aquí."""
        eq = float(
            equity_usd
            if equity_usd is not None
            else (self.tusk.masa_bruta_real or self.tusk.masa_bruta or 0.0)
        )
        precios = dict(precios_por_activo or {})
        # Precio casa como fallback para el foco actual
        casa = self._activo_casa()
        px_casa = self._precio_casa()
        if casa and px_casa > 0 and casa not in precios:
            precios[casa] = px_casa

        permitidos = beru_wake.activos_siembra_permitidos(eq, tusk=self.tusk)
        if not permitidos and beru_wake.siembra_flota_activa():
            # Sin candado cumplido: aún así documenta; no planta a ciegas
            return 0

        ya = set()
        for b in self.legion:
            try:
                from core import beru_asset_detail as bad
                ya.add(bad.activo_de_legionario(b, casa))
            except Exception:
                pass

        n = 0
        for act in permitidos:
            if act in ya:
                continue
            px = float(precios.get(act) or 0.0)
            if px <= 0:
                px = self._precio_de_activo(act)
            if px <= 0:
                # Sin precio de ese Santo: no inventar; ojos rellenan después
                continue
            if self.plantar_semilla_adan(px, activo=act) is not None:
                n += 1
                ya.add(act)
        self._flota_sembrada = True
        return n

    # === ACECHO Y CAZA (EJECUCIÓN DIRECTA) ===

    def _consumir_latidos_legion(self) -> dict[str, dict]:
        """Un latido por Santo en el pulso: acecho y caza beben el mismo vaso."""
        from core import beru_ojos

        lats: dict[str, dict] = {}
        for beru in self.legion:
            act = self._activo_de_barco(beru)
            if act and act not in lats:
                lats[act] = beru_ojos.latido_spot_desde_tank(self.tank, act)
        return lats

    async def _mapear_santos(self, barcos, fn) -> None:
        """Cada Santo habla solo. Cupo compartido; cooldown no frena a los otros."""
        vivos = [b for b in barcos if not beru_rafaga.en_cooldown_api(b)]
        if not vivos:
            return
        cupo = int(getattr(config, "BERU_MANOS_PARALELAS", 8) or 8)

        async def _uno(beru: BeruShip):
            try:
                await fn(beru)
            except Exception as exc:
                act = self._activo_de_barco(beru)
                self._llamado_ahogado(
                    beru, f"pulso_excepcion:{type(exc).__name__}",
                    activo=act,
                    precio=float(self._precio_de_barco(beru) or 0),
                )
                print(f"[BERU] Pulso de un Santo falló (legión sigue): {exc}", flush=True)

        if cupo == 1 or len(vivos) == 1:
            for beru in vivos:
                await _uno(beru)
            return
        n_sem = len(vivos) if cupo <= 0 else max(1, int(cupo))
        sem = asyncio.Semaphore(n_sem)

        async def _con_cupo(beru: BeruShip):
            async with sem:
                await _uno(beru)

        await asyncio.gather(
            *[_con_cupo(b) for b in vivos],
            return_exceptions=True,
        )

    async def auditar_gatillos_adan(self, precio_actual=None, latidos=None):
        """Un gatillo por barco con el latido de SU Santo (mecha, no solo la foto)."""
        lats = dict(latidos or self._consumir_latidos_legion())
        for hijo in beru_continuo.adoptar_cosechados_sin_hijo(self.legion):
            self.legion.append(hijo)

        async def _acecho(beru: BeruShip):
            if beru.estado != "ACECHANDO":
                return
            act = self._activo_de_barco(beru)
            lat = dict(lats.get(act) or {})
            px = float(lat.get("last") or 0)
            if px <= 0 and precio_actual is not None:
                px = float(precio_actual or 0)
            if px <= 0:
                return
            await self._auditar_gatillo_cazador(beru, px, latido=lat)

        await self._mapear_santos(list(self.legion), _acecho)

    async def _auditar_gatillo_cazador(
        self, beru: BeruShip, precio_actual: float, latido: dict | None = None,
    ):
        """Vacío ±1.1 desde el wake; después silbato del relevo desde la última Red."""
        if self._centro_cazador(beru) <= 0:
            return
        lat = dict(latido or {})
        oreja = beru_continuo.decidir_oreja_acecho(beru, precio_actual, latido=lat)
        if not oreja:
            return
        px_toque = float(lat.get("toque") or precio_actual or 0)
        if px_toque <= 0:
            px_toque = float(precio_actual or 0)
        act = self._activo_de_barco(beru)
        grado = beru_altar_cazador.grado_de_barco(beru)
        touch_pct = beru_continuo.pct_desde_ancla(beru, px_toque)
        direccion = "SHORT" if touch_pct > 0 else "LONG"
        if self._ensayo_nivel3() and beru_ensayo.solo_long() and direccion != "LONG":
            beru_ensayo.registrar(
                "SKIP_SHORT",
                detalle="ensayo solo LONG (sin vender inventario)",
                uid=beru.uid,
                activo=act,
                touch_pct=round(float(touch_pct) * 100.0, 4),
            )
            return
        if self._ensayo_nivel3() and beru_ensayo.techo_alcanzado():
            beru_ensayo.registrar(
                "SKIP_TECHO",
                detalle="techo de órdenes ya alcanzado",
                uid=beru.uid,
                activo=act,
            )
            return
        if not beru_cazador.manto_vivo(self.tusk, act):
            beru.direccion = direccion
            self._llamado_ahogado(
                beru, "sin_manto",
                activo=act, oreja=oreja,
                touch_pct=round(float(touch_pct) * 100.0, 4),
                precio=float(px_toque or 0),
            )
            return

        beru.direccion = direccion
        beru.capa = 1
        beru.modo_combate = "CAZA"
        masa_fresca = beru_continuo.armar_tramo(
            beru,
            px_toque,
            activo=act,
            grado=grado,
            oreja=oreja,
            tusk=self.tusk,
        )
        if self._ensayo_nivel3():
            masa_fresca = min(masa_fresca, beru_ensayo.max_masa_usd())
            beru.masa = masa_fresca
            beru.masa_tramo_usd = masa_fresca
        if masa_fresca <= 0.0:
            self._llamado_ahogado(
                beru, "armado_masa_0",
                activo=act, oreja=oreja, grado=grado,
                touch_pct=round(float(touch_pct) * 100.0, 4),
                precio=float(px_toque or 0),
            )
            beru_continuo.restaurar_acecho_tras_fallo_armado(beru)
            beru.estado = "ACECHANDO"
            return
        arma = beru_altar_cazador.sincronizar_arma(beru)

        ok = await self.tusk.solicitar_reserva(
            beru.uid, masa_fresca, "BERU", beru.direccion,
            consumir_auth=beru_ley.consumir_auth_en_reserva(),
        )
        if not ok:
            self._llamado_ahogado(
                beru, "reserva_tusk",
                activo=act, oreja=oreja, grado=grado, arma=arma,
                masa_usd=float(masa_fresca),
                touch_pct=round(float(touch_pct) * 100.0, 4),
                precio=float(px_toque or 0),
            )
            beru_continuo.restaurar_acecho_tras_fallo_armado(beru)
            beru.estado = "ACECHANDO"
            beru.masa = 0.0
            return
        beru.masa = masa_fresca
        beru.masa_tramo_usd = masa_fresca
        # El llamado solo arma el tramo. Hoz materializa/cosecha.
        beru.estado = "CAZANDO"
        nombre = "RED" if oreja == "RED" else ("RELEVO" if bool(getattr(beru, "es_relevo_cazador", False)) else "VACIO")
        tag = "ARMAR_CONDICIONAL"
        await self.bel.anotar(
            "BERU", tag,
            f"{beru.uid} {nombre}/{grado}/{arma} tramo desde {beru.ancla_tramo:.4f} "
            f"@ {touch_pct*100:.2f}% → Hoz {beru.oz_pct*100:.2f}% "
            f"Red {beru.red_pct*100:.2f}% (${masa_fresca:.2f}) — sin fill.",
        )
        self._bitacora(
            f"LLAMADO_{nombre}",
            beru,
            detalle=(
                "detona grid — planta Hoz nativa"
                if self._manos_exchange(beru) else
                "detona grid — cero place_order"
            ),
            oz_pct=float(beru.oz_pct or 0),
            red_pct=float(beru.red_pct or 0),
            masa_usd=float(masa_fresca),
            oreja=oreja,
        )
        if self._manos_exchange(beru):
            self._lanzar_altar(beru, self._plantar_hoz_nativa(beru))

    async def _plantar_hoz_nativa(self, beru: BeruShip) -> bool:
        """Planta la Hoz. Si Bybit ahoga la gorda: mínima o radar. Cero Market feliz."""
        if not self._manos_exchange(beru):
            return False
        if beru_rafaga.es_radar(beru):
            return True
        if bool(getattr(beru, "altar_lote_bloqueado", False)):
            return False
        act = self._activo_de_barco(beru)
        oz = float(getattr(beru, "oz_adan", 0) or 0)
        masa = float(getattr(beru, "masa", 0) or 0)
        if oz <= 0 or masa <= 0:
            return False
        if self._ensayo_nivel3() and beru_ensayo.techo_alcanzado():
            return False
        masa_plan = beru_rafaga.masa_para_carta(beru) or masa
        if beru_continuo.boveda_ahogada(self.tusk):
            min_u = beru_rafaga.min_carta_usd(f"{act}USDT_SPOT", oz, beru.direccion)
            if min_u > 0 and masa_plan > min_u * 1.02:
                masa_plan = min_u
        try:
            plan = beru_altar_nativo.plan_condicional_spot(
                beru, activo=act, masa_usd=masa_plan, trigger_price=oz,
            )
        except ValueError as exc:
            await self.bel.anotar(
                "BERU", "ALTAR_PLAN_FALLIDO",
                f"{beru.uid} {act}: {exc}",
            )
            self._bitacora("ALTAR_PLAN_FALLIDO", beru, detalle=str(exc), oz_adan=oz, masa_usd=masa)
            return False
        if self._ensayo_nivel3():
            beru_ensayo.registrar(
                "CAZA_ENVIANDO",
                detalle="condicional nativa a Bybit",
                uid=beru.uid,
                activo=act,
                lado=beru.direccion,
                side=plan.side,
                symbol=plan.symbol,
                qty=float(plan.qty or 0),
                masa_usd=masa_plan,
                precio=oz,
                categoria="spot",
            )
        resultado = await beru_altar_nativo.armar_condicional(
            self.bridge, beru, plan,
        )
        if resultado.exito:
            beru.altar_lote_bloqueado = False
            if masa_plan + 1e-9 < masa * 0.98:
                beru_rafaga.marcar_hoz_minima(beru, masa_plan)
            else:
                beru_rafaga.marcar_hoz_completa(beru, masa_plan)
            await self.bel.anotar(
                "BERU", "ALTAR_ARMADO",
                f"{beru.uid} Hoz condicional @ {oz:.6f} "
                f"link={beru.altar_link_id} (${masa_plan:.2f}).",
            )
            self._bitacora(
                "ALTAR_ARMADO",
                beru,
                detalle=f"Hoz condicional @ {oz:.6f}",
                oz_adan=oz,
                masa_usd=masa_plan,
            )
            return True
        beru_rafaga.marcar_si_rate_limit(beru, resultado)
        if beru_rafaga.resultado_es_lote(resultado):
            beru.altar_lote_bloqueado = True
            await self.bel.anotar(
                "BERU", "ALTAR_LOTE_RECHAZADO",
                f"{beru.uid}: {resultado.mensaje}",
            )
            self._bitacora(
                "ALTAR_LOTE_RECHAZADO", beru,
                detalle=str(resultado.mensaje),
                oz_adan=oz, masa_usd=masa,
            )
            return False
        if not beru_rafaga.resultado_es_ahogo(resultado):
            await self.bel.anotar(
                "BERU", "ALTAR_ARMAR_FALLIDO",
                f"{beru.uid}: {resultado.mensaje}",
            )
            self._bitacora(
                "ALTAR_ARMAR_FALLIDO", beru, detalle=str(resultado.mensaje),
                oz_adan=oz, masa_usd=masa,
            )
            return False
        return await self._plantar_red_ahogo(beru, act=act, oz=oz, masa=masa)

    async def _plantar_red_ahogo(
        self, beru: BeruShip, *, act: str, oz: float, masa: float,
    ) -> bool:
        """Capa 2: Hoz mínima. Capa 3: radar interno. Nunca 4 condicionales a la vez."""
        frente = f"{act}USDT_SPOT"
        min_u = beru_rafaga.min_carta_usd(frente, oz, beru.direccion)
        if min_u <= 0 or masa + 1e-9 <= min_u * 1.02:
            beru_rafaga.activar_radar(beru)
            await self.bel.anotar(
                "BERU", "ALTAR_HOZ_RADAR",
                f"{beru.uid} bóveda ahogada · sin carta · radar @ {oz:.6f} (${masa:.2f}).",
            )
            self._bitacora(
                "ALTAR_HOZ_RADAR", beru,
                detalle=f"radar interno @ {oz:.6f}",
                oz_adan=oz, masa_usd=masa,
            )
            return True

        try:
            plan_min = beru_altar_nativo.plan_condicional_spot(
                beru, activo=act, masa_usd=min_u, trigger_price=oz,
            )
        except ValueError as exc:
            beru_rafaga.activar_radar(beru)
            self._bitacora(
                "ALTAR_HOZ_RADAR", beru,
                detalle=f"mínima no cuantizable · {exc}",
                oz_adan=oz, masa_usd=masa,
            )
            return True
        rmin = await beru_altar_nativo.armar_condicional(
            self.bridge, beru, plan_min,
        )
        beru_rafaga.marcar_si_rate_limit(beru, rmin)
        if rmin.exito:
            carta = round(float(plan_min.qty) * float(plan_min.trigger_price), 6)
            if carta <= 0:
                carta = min_u
            beru_rafaga.marcar_hoz_minima(beru, carta)
            await self.bel.anotar(
                "BERU", "ALTAR_HOZ_MINIMA",
                f"{beru.uid} Hoz mínima @ {oz:.6f} ${carta:.2f} · "
                f"acecha ${beru.masa_rafaga_usd:.2f}.",
            )
            self._bitacora(
                "ALTAR_HOZ_MINIMA", beru,
                detalle=f"carta ${carta:.2f} · ráfaga ${beru.masa_rafaga_usd:.2f}",
                oz_adan=oz, masa_usd=carta, masa_rafaga_usd=float(beru.masa_rafaga_usd),
            )
            return True

        if beru_rafaga.resultado_es_lote(rmin):
            beru.altar_lote_bloqueado = True
            await self.bel.anotar(
                "BERU", "ALTAR_LOTE_RECHAZADO",
                f"{beru.uid} mínima: {rmin.mensaje}",
            )
            self._bitacora(
                "ALTAR_LOTE_RECHAZADO", beru,
                detalle=str(rmin.mensaje),
                oz_adan=oz, masa_usd=masa,
            )
            return False

        beru_rafaga.activar_radar(beru)
        await self.bel.anotar(
            "BERU", "ALTAR_HOZ_RADAR",
            f"{beru.uid} ni el mínimo cabe · radar @ {oz:.6f} (${masa:.2f}) · "
            f"{rmin.mensaje}",
        )
        self._bitacora(
            "ALTAR_HOZ_RADAR", beru,
            detalle=str(rmin.mensaje or "minima_rechazada"),
            oz_adan=oz, masa_usd=masa,
        )
        return True

    async def _replantar_hoz_nativa(self, beru: BeruShip) -> str:
        """Cancela confirmado y planta la Hoz nueva. Si ya filló → cosecha."""
        if not self._manos_exchange(beru):
            return "sin_manos"
        if bool(getattr(beru, "altar_lote_bloqueado", False)):
            return "lote_bloqueado"
        beru_rafaga.sincronizar_masa_rafaga(beru)
        if beru_rafaga.es_radar(beru):
            return "radar"
        act = self._activo_de_barco(beru)
        if not str(getattr(beru, "altar_link_id", "") or ""):
            ok = await self._plantar_hoz_nativa(beru)
            return "armada" if ok else "armar_fallido"
        oz = float(getattr(beru, "oz_adan", 0) or 0)
        masa = beru_rafaga.masa_para_carta(beru)
        if oz <= 0 or masa <= 0:
            return "sin_hoz"
        resultado, motivo = await beru_altar_nativo.mover_condicional(
            self.bridge, beru,
            activo=act, masa_usd=masa, trigger_price=oz,
        )
        if motivo == "fill_confirmado":
            await self._cosechar_si_fill_nativo(beru, forzar_consulta=True)
            return "fill_al_mover"
        if resultado is None or not getattr(resultado, "exito", False):
            beru_rafaga.marcar_si_rate_limit(beru, resultado)
            await self.bel.anotar(
                "BERU", "ALTAR_MOVER_DIFERIDO",
                f"{beru.uid}: {motivo}",
            )
            self._bitacora("ALTAR_MOVER_DIFERIDO", beru, detalle=str(motivo or "mover_fallido"))
            return str(motivo or "mover_fallido")
        if motivo == "enmendada":
            await self.bel.anotar(
                "BERU", "ALTAR_ENMENDADO",
                f"{beru.uid} Hoz @ {oz:.6f} (${masa:.2f}).",
            )
            self._bitacora(
                "ALTAR_ENMENDADO",
                beru,
                detalle=f"Hoz @ {oz:.6f}",
                oz_adan=oz,
                masa_usd=masa,
            )
            return "enmendada"
        await self.bel.anotar(
            "BERU", "ALTAR_REPLANTADO",
            f"{beru.uid} Hoz nueva @ {oz:.6f} (${masa:.2f}).",
        )
        self._bitacora(
            "ALTAR_REPLANTADO",
            beru,
            detalle=f"Hoz nueva @ {oz:.6f}",
            oz_adan=oz,
            masa_usd=masa,
        )
        return "replantada"

    async def _cosechar_si_fill_nativo(
        self,
        beru: BeruShip,
        *,
        forzar_consulta: bool = False,
        fill_local: dict | None = None,
    ) -> bool:
        """Fill confirmado de la Hoz = cosecha. Ráfaga del resto ANTES del funeral."""
        if not self._manos_exchange(beru):
            return False
        if str(getattr(beru, "estado", "") or "") not in (
            "CAZANDO", "ESPERANDO_SUELTA", "ESPERANDO_MATERIALIZACION",
        ):
            return False
        if bool(getattr(beru, "relevo_creado", False)):
            return False
        if bool(getattr(beru, "rafaga_en_curso", False)):
            return False
        act = self._activo_de_barco(beru)
        fill = fill_local
        if fill is None:
            if beru_rafaga.es_radar(beru):
                return False
            if not str(getattr(beru, "altar_link_id", "") or "") and not forzar_consulta:
                return False
            fill = await beru_altar_nativo.consultar_fill(
                self.bridge, beru, activo=act,
            )
            if not fill:
                return False
            if beru_rafaga.debe_rafaga(beru):
                await self._ejecutar_rafaga(beru)

        if beru_rafaga.debe_rafaga(beru):
            return False

        px_fill = float(fill.get("avgPrice") or 0)
        qty = float(fill.get("cumExecQty") or 0) + float(
            getattr(beru, "qty_rafaga_acum", 0) or 0,
        )
        if px_fill <= 0:
            px_fill = float(getattr(beru, "oz_adan", 0) or 0) or self._precio_de_barco(beru)
        if px_fill <= 0:
            return False

        masa_tramo = float(beru.masa or 0)
        grado = beru_altar_cazador.grado_de_barco(beru)
        ultima_red = float(getattr(beru, "ultima_red_tocada_pct", 0) or 0)
        beru.precio_entrada_real = px_fill
        beru.precio_salida_real = px_fill
        if qty > 0:
            beru.qty_base_ejecutada = qty
        beru.frente_asignado = f"{act}USDT_SPOT"
        beru.frente_salida = beru.frente_asignado
        beru.sincronizado = True

        uid_cosecha = f"COSECHA_{str(uuid.uuid4())[:4]}"
        await self.tusk.consumar_cosecha_atomica(
            uid_cosecha, beru.frente_salida, beru,
        )
        # Libera la reserva viva del tramo (si aún colgaba del uid del barco).
        await self.tusk.liberar_reserva(beru.uid)
        await self.tusk.liberar_reserva(f"E_{beru.uid}")

        hijo = beru_altar_cazador.crear_relevo_desde_hoz(
            beru,
            px_fill,
            activo=act,
            fill_confirmado=True,
        )
        lec = beru_continuo.lecturas_cosecha(beru, px_fill)
        texto = beru_continuo.texto_lecturas_cosecha(lec)
        extra = beru_continuo.extra_bitacora_cosecha(lec)
        await self.bel.anotar(
            "BERU", "COSECHA_CONDICIONAL",
            f"{beru.uid} fill nativo @ {px_fill:.6f} "
            f"qty={qty:.8f} (${masa_tramo:.2f}) · {texto}.",
        )
        self._bitacora(
            "COSECHA_CONDICIONAL",
            beru,
            detalle=f"fill nativo · {texto}",
            precio=px_fill,
            qty=qty,
            masa_usd=masa_tramo,
            **extra,
        )
        self._cronica(
            beru, "COSECHA",
            f"{texto}",
            precio=px_fill, masa_usd=masa_tramo,
            **extra,
        )
        if self._ensayo_nivel3():
            beru_ensayo.anotar_cosecha_ok(
                uid=beru.uid,
                side="Buy" if beru.direccion == "LONG" else "Sell",
                symbol=f"{act}USDT",
                precio=px_fill,
                qty=qty,
                order_id=fill.get("order_id"),
            )
        if hijo is not None:
            self.legion.append(hijo)
            await self.bel.anotar(
                "BERU", "RELEVO_CAZADOR",
                f"{beru.uid} cosechó ${masa_tramo:.2f}; funeral confirmado · "
                f"Red tocada {ultima_red*100:.2f}% → {hijo.uid} "
                f"llamado +{hijo.llamado_tramo_pct*100:.2f}% ({grado}).",
            )
            self._bitacora(
                "RELEVO_CAZADOR",
                beru,
                detalle=f"→ {hijo.uid}",
                hijo_uid=hijo.uid,
                masa_usd=masa_tramo,
                ultima_red_pct=round(ultima_red * 100.0, 4),
            )
        else:
            await self.bel.anotar(
                "BERU", "COSECHA_CONDICIONAL_MARISCAL",
                f"{beru.uid} {grado} cosechó ${masa_tramo:.2f}; "
                "recorrido cerrado, sin plan A ni carta gorda.",
            )
            self._bitacora(
                "COSECHA_MARISCAL",
                beru,
                detalle="recorrido cerrado, sin relevo",
                masa_usd=masa_tramo,
            )
        return True

    async def _cosechar_venta_cruzada(self, beru: BeruShip, precio: float) -> bool:
        """SHORT: last ya bajo la Hoz y la Stop no filló. Cancela y cobra por ráfaga."""
        if not beru_continuo.last_bajo_hoz_venta(beru, precio):
            return False
        if bool(getattr(beru, "relevo_creado", False)):
            return False
        act = self._activo_de_barco(beru)
        if beru_continuo.carta_hoz_viva(beru):
            _ok, motivo = await beru_altar_nativo.cancelar_confirmado(
                self.bridge, beru,
                symbol=f"{act}USDT",
            )
            if motivo == "fill_confirmado":
                return await self._cosechar_si_fill_nativo(beru, forzar_consulta=True)
            if motivo == "consulta_incierta":
                return False
        beru_rafaga.activar_radar(beru)
        await self.bel.anotar(
            "BERU", "HOZ_CRUZADA_VENTA",
            f"{beru.uid} last bajo la Hoz de venta · cancela y ráfaga "
            f"(no espera el subidón).",
        )
        self._bitacora(
            "HOZ_CRUZADA_VENTA", beru,
            detalle="last bajo Hoz SHORT · Stop del lado contrario",
            precio=float(precio or 0),
            oz_adan=float(getattr(beru, "oz_adan", 0) or 0),
        )
        if beru_rafaga.debe_rafaga(beru):
            await self._ejecutar_rafaga(beru)
        if beru_rafaga.debe_rafaga(beru):
            return False
        qty = float(getattr(beru, "qty_rafaga_acum", 0) or 0)
        if bool(getattr(beru, "rafaga_hecha", False)) or qty > 0:
            fill_local = {
                "avgPrice": float(getattr(beru, "oz_adan", 0) or precio or 0),
                "cumExecQty": 0.0,
                "orderStatus": "RADAR",
                "order_id": "",
            }
            return await self._cosechar_si_fill_nativo(beru, fill_local=fill_local)
        return False

    async def _ejecutar_rafaga(self, beru: BeruShip) -> bool:
        """Bocados market de uno en uno. No corre en el camino feliz."""
        if not self._manos_exchange(beru):
            return False
        if bool(getattr(beru, "rafaga_en_curso", False)):
            return False
        if bool(getattr(beru, "rafaga_hecha", False)):
            return True
        if not beru_rafaga.debe_rafaga(beru):
            return True
        if beru_rafaga.en_cooldown(beru):
            return False
        act = self._activo_de_barco(beru)
        px = self._precio_de_barco(beru) or float(getattr(beru, "oz_adan", 0) or 0)
        usd = float(getattr(beru, "masa_rafaga_usd", 0) or 0)
        beru.rafaga_en_curso = True
        beru.rafaga_ultimo_ts = time.time()
        try:
            res = await beru_rafaga.disparar_rafaga(
                self.bridge, beru,
                activo=act, usd=usd, precio=px,
                is_leverage=1 if beru_ley.spot_margen_activo() else 0,
            )
        except Exception as exc:
            beru.rafaga_en_curso = False
            await self.bel.anotar(
                "BERU", "AHOGO_RAFAGA",
                f"{beru.uid} ráfaga excepción: {exc}",
            )
            self._bitacora("AHOGO_RAFAGA", beru, detalle=str(exc))
            return False
        beru.rafaga_en_curso = False
        beru.qty_rafaga_acum = float(getattr(beru, "qty_rafaga_acum", 0) or 0) + float(
            res.get("qty_total") or 0,
        )
        resto = float(res.get("usd_restante") or 0)
        beru.masa_rafaga_usd = resto
        polvo = float(res.get("polvo_usd") or 0)
        ok_n = int(res.get("bocados_ok") or 0)
        fail_n = int(res.get("bocados_fail") or 0)
        if polvo > 0:
            self._bitacora(
                "RAFAGA_POLVO", beru,
                detalle=f"polvo ${polvo:.4f} no plantado",
                polvo_usd=polvo,
            )
        await self.bel.anotar(
            "BERU", "RAFAGA_LISTA" if ok_n and not fail_n else "AHOGO_RAFAGA",
            f"{beru.uid} bocados {ok_n}/{res.get('n_plan')} "
            f"fail={fail_n} restante ${resto:.2f}.",
        )
        self._bitacora(
            "RAFAGA_LISTA" if ok_n else "AHOGO_RAFAGA",
            beru,
            detalle=f"ok={ok_n} fail={fail_n} resto=${resto:.2f}",
            bocados_ok=ok_n, bocados_fail=fail_n, masa_rafaga_usd=resto,
        )
        min_u = beru_rafaga.min_carta_usd(
            f"{act}USDT_SPOT", px, beru.direccion,
        )
        if resto + 1e-9 < min_u:
            beru.masa_rafaga_usd = 0.0
            beru.rafaga_hecha = True
            return ok_n > 0 or beru_rafaga.es_minima(beru)
        beru.rafaga_hecha = False
        return ok_n > 0

    async def _auditar_gatillo_negociador(self, beru: BeruShip, precio_actual: float):
        """Compatibilidad: toda entrada antigua se conduce al cazador continuo."""
        beru.modo_combate = "CAZA"
        beru.neg_post_cazador = False
        beru.ciclo_infinito = False
        await self._auditar_gatillo_cazador(beru, precio_actual)
        return

        # FÓSIL histórico, inalcanzable.
        distancia = (precio_actual - beru.centro_local) / max(beru.centro_local, 0.0001)
        if abs(distancia) < 0.0005:
            return
        if abs(distancia) < beru.adn_capitan.vacio_adan:
            return

        act = self._activo_de_barco(beru)
        masa_fresca = beru_ley.masa_unidad_intercambio_usd(act)
        if masa_fresca <= 0.0:
            return

        direccion = "SHORT" if distancia > 0 else "LONG"
        if self._ensayo_nivel3() and beru_ensayo.solo_long() and direccion != "LONG":
            beru_ensayo.registrar(
                "SKIP_SHORT",
                detalle="ensayo solo LONG (negociador)",
                uid=beru.uid,
                activo=act,
            )
            return
        if self._ensayo_nivel3() and beru_ensayo.techo_alcanzado():
            return

        beru.direccion = direccion
        beru.estado = "ESPERANDO_MATERIALIZACION"

        ok = await self.tusk.solicitar_reserva(
            beru.uid, masa_fresca, "BERU", beru.direccion,
            consumir_auth=beru_ley.consumir_auth_en_reserva(),
        )
        if ok:
            beru.masa = masa_fresca
            tier = self._tier_barco(beru)
            paso_oz, paso_red = tier.pasos("NEGOCIADOR")
            beru.red_adan, beru.oz_adan = beru_tier.precios_red_oz(
                beru.centro_local, beru.direccion,
                paso_oz=paso_oz, paso_red=paso_red,
            )
            await self._ejecutar_caza(beru)

    async def _radar_casa(self, ctx_map, masa, is_long, base: str | None = None):
        lider = self.tank._obtener_lider_verde()
        if not lider:
            nodos = list(getattr(self.tank, "nodos", None) or [])
            lider = max(nodos, key=lambda n: float(getattr(n, "ultima_actualizacion", 0) or 0)) if nodos else None
        libros = (lider.libros if lider else {}) or {}
        act = (base or self._activo_casa()).upper()
        frente, p_ef, meta = beru_rail.elegir_mejor_rail(
            ctx_map or {}, masa, is_long,
            base=act,
            libros=libros,
            kaiser=self.kaiser,
        )
        if p_ef <= 0:
            # Muleta: ticker Tank del Santo (WS caído / sin ctx rail)
            px = self._precio_de_activo(act)
            if px > 0:
                frente = f"{act}USDT_SPOT"
                fee = 0.001
                p_ef = px * (1.0 + fee) if is_long else px * (1.0 - fee)
                meta = {"ok": True, "frente": frente, "motivo": "ticker_tank", "candidatos": 1}
        if meta.get("candidatos", 0) > 1:
            await self.bel.anotar(
                "BERU", "RAIL_ELEGIDO",
                f"{frente} ({meta.get('candidatos')} stables) fee~{meta.get('fee_pct', 0):.2f}%",
            )
        return frente, p_ef

    async def _ejecutar_caza(self, beru):
        act = self._activo_de_barco(beru)
        if not self._beru_caza_permitida(act):
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ACECHANDO"
            return
        # Candado duro: la ruta vieja resolvía la Hoz con market. El Beru nuevo
        # exige condicional/trailing nativo + confirmación real de fill/cancel.
        if self._manos_exchange(beru):
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ALTAR_NATIVO_PENDIENTE"
            await self.bel.anotar(
                "BERU", "ALTAR_NATIVO_PENDIENTE",
                "Market de Hoz bloqueado; faltan condicional/trailing nativos.",
            )
            return
        ctx_map, estado = await self.tank.vision_especulativa()
        px_barco = self._precio_de_barco(beru)
        aborta, motivo = beru_ley.debe_abortar_por_vision(
            estado, ctx_map,
            precio_casa=px_barco if px_barco > 0 else self._precio_casa(),
            tank=self.tank,
        )
        if aborta:
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ACECHANDO"
            await self.bel.anotar("BERU", "CAZA_DIFERIDA", f"Ciego/visión: {motivo}")
            if self._manos_fantasma():
                beru_fantasma.registrar(
                    "ABORTO_CAZA",
                    detalle=str(motivo),
                    uid=beru.uid,
                    activo=act,
                    vision=estado,
                )
            elif self._ensayo_nivel3():
                beru_ensayo.registrar(
                    "ABORTO_CAZA",
                    detalle=str(motivo),
                    uid=beru.uid,
                    activo=act,
                    vision=estado,
                )
            return
        is_long = beru.direccion == "LONG"
        mejor_f, p_ef = await self._radar_casa(ctx_map or {}, beru.masa, is_long, base=act)
        if p_ef <= 0:
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ACECHANDO"
            if self._manos_fantasma():
                beru_fantasma.registrar(
                    "ABORTO_CAZA",
                    detalle="sin_precio_rail",
                    uid=beru.uid,
                    activo=act,
                )
            elif self._ensayo_nivel3():
                beru_ensayo.registrar(
                    "ABORTO_CAZA",
                    detalle="sin_precio_rail",
                    uid=beru.uid,
                    activo=act,
                )
            return

        # Neutro margen: no aplicar banda L/S del manto Igris al intercambio spot
        if not beru_ley.neutro_margen():
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
        side = "Buy" if is_long else "Sell"
        market_unit = None
        qty_orden = beru.masa
        is_lev = None
        if categoria == "spot":
            if beru_ley.spot_margen_activo():
                is_lev = 1
            if is_long:
                market_unit = "quoteCoin"
                qty_orden = beru.masa
            else:
                px = float(p_ef) if p_ef and p_ef > 0 else 0.0
                qty_orden = (beru.masa / px) if px > 0 else beru.masa

        manos_reales = self._manos_exchange(beru)

        if manos_reales:
            if self._ensayo_nivel3():
                if beru_ensayo.techo_alcanzado():
                    await self.tusk.liberar_reserva(beru.uid)
                    beru.estado = "ACECHANDO"
                    beru_ensayo.registrar("SKIP_TECHO", detalle="antes de place_order", uid=beru.uid)
                    return
                beru_ensayo.registrar(
                    "CAZA_ENVIANDO",
                    detalle="market REAL a Bybit",
                    uid=beru.uid,
                    activo=act,
                    lado=beru.direccion,
                    side=side,
                    symbol=symbol,
                    frente=mejor_f,
                    qty=float(qty_orden or 0),
                    masa_usd=float(beru.masa or 0),
                    precio=float(p_ef or 0),
                    market_unit=market_unit,
                    categoria=categoria,
                )
            resultado = await self.bridge.place_order(
                symbol, side, qty_orden, category=categoria,
                market_unit=market_unit, is_leverage=is_lev,
            )
            if not resultado.exito:
                await self.tusk.liberar_reserva(beru.uid)
                beru.estado = "ACECHANDO"
                await self.bel.anotar("BERU", "CAZA_ORDEN_FALLIDA", resultado.mensaje)
                if self._ensayo_nivel3():
                    beru_ensayo.anotar_orden_fallida(
                        resultado.mensaje,
                        uid=beru.uid,
                        activo=act,
                        symbol=symbol,
                        side=side,
                    )
                return
            fill = await self.bridge.esperar_fill(symbol, order_id=resultado.order_id, category=categoria)
            if not fill.exito:
                await self.tusk.liberar_reserva(beru.uid)
                beru.estado = "ACECHANDO"
                if self._ensayo_nivel3():
                    beru_ensayo.anotar_orden_fallida(
                        "fill_timeout_o_fallo",
                        uid=beru.uid,
                        activo=act,
                        symbol=symbol,
                        order_id=getattr(resultado, "order_id", None),
                    )
                return
            p_ef = fill.datos.get("avgPrice", p_ef)
            qty_base = float(fill.datos.get("cumExecQty") or 0)
            if qty_base > 0:
                beru.qty_base_ejecutada = qty_base
            await self.tusk.confirmar_reserva(
                beru.uid, mejor_f, beru.direccion, fill_confirmado=True, precio_fill=p_ef,
                qty_fill=qty_base or None,
            )
            if self._ensayo_nivel3():
                beru_ensayo.anotar_orden_ok(
                    uid=beru.uid,
                    activo=act,
                    lado=beru.direccion,
                    side=side,
                    symbol=symbol,
                    frente=mejor_f,
                    qty=float(qty_orden or 0),
                    qty_base=float(qty_base or 0),
                    masa_usd=float(beru.masa or 0),
                    precio=float(p_ef or 0),
                    order_id=getattr(resultado, "order_id", None),
                )
        elif self._manos_fantasma() or config.MODO_SIMULACION:
            if self._manos_fantasma():
                beru_fantasma.registrar(
                    "CAZA_MARKET",
                    detalle="habría market — NO enviado a Bybit",
                    uid=beru.uid,
                    activo=act,
                    lado=beru.direccion,
                    side=side,
                    symbol=symbol,
                    frente=mejor_f,
                    qty=float(qty_orden or 0),
                    masa_usd=float(beru.masa or 0),
                    precio=float(p_ef or 0),
                    market_unit=market_unit,
                    categoria=categoria,
                )
            # Fill ilusorio: avanza ciclo en memoria (sim o fantasma)
            if float(p_ef or 0) > 0 and categoria == "spot" and not is_long:
                beru.qty_base_ejecutada = float(qty_orden or 0)
            elif float(p_ef or 0) > 0 and is_long:
                beru.qty_base_ejecutada = float(beru.masa or 0) / float(p_ef)
            await self.tusk.confirmar_reserva(
                beru.uid, mejor_f, beru.direccion,
                fill_confirmado=True, precio_fill=float(p_ef or 0) or None,
                qty_fill=float(beru.qty_base_ejecutada or 0) or None,
            )
        else:
            # Live sin manos: no fingir NEGOCIANDO
            await self.tusk.liberar_reserva(beru.uid)
            beru.estado = "ACECHANDO"
            await self.bel.anotar(
                "BERU", "CAZA_SIN_MANOS",
                "Gatillo listo pero manos OFF — sin orden ni anclaje fantasma.",
            )
            return

        beru.frente_asignado = mejor_f
        beru.precio_entrada_real = p_ef
        beru.estado = "CAZANDO"
        await self.bel.anotar("BERU", "CAZA", f"Anclado en {mejor_f} @ {p_ef:.2f}")

    async def sincronizar_materializacion(self):
        for beru in self.legion:
            if beru.estado == "CAZANDO" and self._manos_exchange(beru):
                if await self._cosechar_si_fill_nativo(beru):
                    continue
                # Caza sin Stop viva (Deactivated/aire): plantar. Altar en vuelo: no duplicar.
                if (
                    float(getattr(beru, "masa", 0) or 0) > 0
                    and float(getattr(beru, "oz_adan", 0) or 0) > 0
                    and not beru_continuo.carta_hoz_viva(beru)
                    and not beru_rafaga.es_radar(beru)
                    and not bool(getattr(beru, "rafaga_en_curso", False))
                    and not bool(getattr(beru, "altar_lote_bloqueado", False))
                    and not self._altar_en_vuelo(beru)
                ):
                    self._lanzar_altar(beru, self._plantar_hoz_nativa(beru))
            if beru.estado == "CAZANDO" and not beru.sincronizado and beru.precio_entrada_real > 0:
                beru.centro_manto = self._centro_cazador(beru)
                beru.sincronizado = True
                await self.bel.anotar("BERU", "RESONANCIA", f"{beru.uid} sincronizado @ {beru.precio_entrada_real:.2f}")

    # === COMBATE ACTIVO — CAZADOR CONTINUO ===

    async def ejecutar_acordeon_asimetrico(self, precio_actual, latidos=None):
        await self._acordeon_cazador_capas(precio_actual, latidos=latidos)

    async def _pulsar_negociador_post_cazador(self, precio_actual: float):
        """FÓSIL: negociador/ping-pong extirpados. Solo existe el cazador continuo."""
        _ = precio_actual
        return
        for beru in self.legion:  # pragma: no cover
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
                # Oro ya plantado en neg_oz_pct, o se deriva del ancla
                cond = float(beru.neg_oz_pct or 0)
                if cond == 0.0:
                    cond = beru_negociador.oz_condicional_pct(beru.ancla_cosecha_pct, vacio)
                    beru.neg_oz_pct = cond
                if not beru_negociador.toca_condicional(precio_actual, centro, cond):
                    continue
                # Detona → UNA trailing (toda la masa). Sin acordeón.
                oz_n, red_n = beru_negociador.activar_trailing_unica(cond, paso_oz)
                beru.neg_oz_pct, beru.neg_red_pct = oz_n, red_n
                beru.oz_adan, _ = beru_negociador.sincronizar_grid(centro, oz_n, oz_n)
                beru.red_adan = 0.0
                beru.estado = "NEGOCIANDO"
                beru.modo_combate = "NEGOCIADOR"
                beru.neg_toques_ciclo = 0
                beru.fase_reciclaje = "TRAILING"
                beru.bracket_armado = True
                masa = float(beru.masa_congelada or beru.masa or 0)
                await self.bel.anotar(
                    "BERU", "LLAMADO_ORO",
                    f"{beru.uid} oro {cond*100:.2f}% → trailing única @ {oz_n*100:.2f}% "
                    f"(masa ${masa:.2f}) — sin acordeón.",
                )
                continue

            if beru.estado != "NEGOCIANDO" or beru.modo_combate != "NEGOCIADOR":
                continue

            # Fill de la única trailing → ping-pong: oro al otro lado (funeral holgado)
            if not beru_negociador.toca_trailing(precio_actual, centro, beru.neg_oz_pct):
                continue

            if beru_mega_reset.debe_purgar_mega(beru) or getattr(beru, "es_super_beru", False):
                # Mega: purga — NO mueve el 0 de Igris
                await self._purga_mega(beru, precio_actual)
                continue

            fill_pct = beru_cazador.pct_desde_precio(centro, precio_actual)
            await self._ping_pong_oro(beru, fill_pct, vacio, precio_actual)
            continue

    async def _purga_mega(self, beru: BeruShip, precio_actual: float):
        """Mega: suelta masa · purga · cazador nuevo con MISMO centro_manto Igris."""
        raise RuntimeError("FOSIL_BLOQUEADO: Mega no pertenece al Beru cazador")
        masa_suelta = float(beru.masa or beru.masa_congelada or 0)
        direccion = beru.direccion
        tier = getattr(beru, "tier_id", "") or self._tier_efectivo()
        generacion = beru.generacion + 1
        centro_igris = float(beru.centro_manto or 0) or beru_cazador.centro_manto_desde_tusk(self.tusk)
        pct_purga = beru_cazador.pct_desde_precio(centro_igris, precio_actual) if centro_igris > 0 else 0.0

        await self._soltar_mega_a_boveda(beru)

        nuevo_uid = f"BERU_MEGA0_{int(time.time())}"
        semilla = beru_mega_reset.crear_semilla_post_purga(
            centro_igris,
            pct_purga=pct_purga,
            direccion=direccion,
            tier_id=tier,
            adn_capitan=self.tank.capitan_activo,
            generacion=generacion,
            uid=nuevo_uid,
        )
        self.legion.append(semilla)
        piso = float(getattr(semilla, "piso_sangre_pct", 0) or 0)
        msg = (
            f"{beru.uid} purga Mega @ {precio_actual:.2f} (pct {pct_purga*100:.2f}%) → "
            f"bóveda ${masa_suelta:.0f} · 0 Igris intacto · {nuevo_uid} "
            f"sangre @{piso*100:.2f}% (masa $0)."
        )
        await self.bel.anotar("BERU", "MEGA_PURGA", msg)
        self._cronica(
            beru, "MEGA_PURGA", msg,
            precio=precio_actual, masa=masa_suelta, nuevo_uid=nuevo_uid,
        )

    async def _reset_mega_por_red(self, beru: BeruShip, precio_actual: float):
        """Alias legado → purga sin mover 0."""
        raise RuntimeError("FOSIL_BLOQUEADO: reset Mega extirpado")

    async def _soltar_mega_a_boveda(self, beru: BeruShip):
        """Capital del Mega vuelve al margen cruzado (bóveda Tusk); sin reserva exclusiva."""
        raise RuntimeError("FOSIL_BLOQUEADO: suelta Mega extirpada")
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

    async def _ping_pong_oro(
        self,
        beru: BeruShip,
        fill_pct: float,
        vacio: float,
        precio_actual: float,
    ) -> None:
        """Trailing llenó → funeral holgado → oro al otro lado del vacío (1.6%)."""
        raise RuntimeError("FOSIL_BLOQUEADO: ping-pong extirpado")
        oro = beru_negociador.oro_orilla_opuesta(fill_pct, vacio)
        beru.ancla_cosecha_pct = fill_pct
        beru.neg_oz_pct = oro
        beru.neg_red_pct = 0.0
        beru.neg_toques_ciclo = 0
        beru.estado = "ESPERANDO_CONDICIONAL"
        beru.modo_combate = "NEGOCIADOR"
        beru.fase_reciclaje = "PING_PONG"
        beru.oz_adan = 0.0
        beru.red_adan = 0.0
        masa = float(beru.masa_congelada or beru.masa or 0)
        msg = (
            f"{beru.uid} trailing fill @ {fill_pct*100:.2f}% → oro orilla "
            f"{oro*100:.2f}% (masa ${masa:.2f}) — ping-pong."
        )
        await self.bel.anotar("BERU", "PING_PONG_ORO", msg)
        self._cronica(beru, "PING_PONG_ORO", msg, precio=precio_actual)

    async def _flip_neg_a_caza(self, beru: BeruShip, precio_actual: float):
        """LEGADO: redirige a ping-pong oro (ya no vuelve a caza fantasma)."""
        raise RuntimeError("FOSIL_BLOQUEADO: negociador extirpado")
        centro = beru.centro_manto or beru_cazador.centro_manto_desde_tusk(self.tusk)
        fill_pct = beru_cazador.pct_desde_precio(centro, precio_actual) if centro > 0 else beru.ancla_cosecha_pct
        vacio = beru.adn_capitan.vacio_adan
        await self._ping_pong_oro(beru, fill_pct, vacio, precio_actual)

    async def _flip_caza_a_neg(self, beru: BeruShip, precio_actual: float):
        """Oz cazador tocada = red negociador → armar condicional al otro lado."""
        raise RuntimeError("FOSIL_BLOQUEADO: transición a negociador extirpada")
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
        msg = (
            f"{beru.uid} oz cazador {ancla*100:.2f}% → condicional {cond*100:.2f}%."
        )
        await self.bel.anotar("BERU", "VUELTA_NEG", msg)
        self._cronica(beru, "VUELTA_NEG", msg, precio=precio_actual)

    async def _pulsar_clonacion_residual(self, precio_actual: float):
        """FÓSIL: capas residuales extirpadas del cazador continuo."""
        _ = precio_actual
        return
        for rr in list(self._redes_residuales):  # pragma: no cover
            if not rr.activa:
                continue
            if not beru_residual.toca_residual(precio_actual, rr):
                continue
            rr.activa = False
            await self._parir_desde_residual(rr, precio_actual)

    async def _parir_desde_residual(self, residual: beru_residual.RedResidual, precio_actual: float):
        raise RuntimeError("FOSIL_BLOQUEADO: residual/capas extirpados")
        # FÓSIL histórico inalcanzable.
        if not beru_ley.engorde_permitido():
            residual.activa = False
            await self.bel.anotar(
                "BERU", "CLON_BLOQUEADO",
                "Ley neutro: sin engorde — residual no para capas nuevas.",
            )
            return
        direccion = residual.direccion
        capa = self._siguiente_capa(direccion)
        centro = residual.centro_manto or beru_cazador.centro_manto_desde_tusk(self.tusk)
        if centro <= 0:
            return
        touch_pct = beru_cazador.pct_desde_precio(centro, precio_actual)
        masa = beru_ley.masa_unidad_intercambio_usd(self._activo_casa())
        if masa <= 0:
            return
        nuevo_uid = f"BERU_CAPA{capa}_{self._activo_casa()}_{time.time_ns()}"
        barco = BeruShip(
            uid=nuevo_uid,
            centro_local=precio_actual,
            centro_manto=centro,
            masa=masa,
            direccion=direccion,
            estado="ESPERANDO_MATERIALIZACION",
            generacion=1,
            adn_capitan=beru_wake.adn_capitan_wake(),
            tier_id=residual.tier_id or self._tier_efectivo(),
            modo_combate="CAZA",
            capa=capa,
        )
        self._aplicar_grid_cazador(barco, touch_pct)
        if not await self.tusk.solicitar_reserva(
            nuevo_uid, masa, "BERU", direccion,
            consumir_auth=beru_ley.consumir_auth_en_reserva(),
        ):
            residual.activa = True
            return
        await self._ejecutar_caza(barco)
        if barco.estado == "NEGOCIANDO":
            self.legion.append(barco)
            await self.bel.anotar(
                "BERU", "CLON_RESIDUAL",
                f"{nuevo_uid} capa{capa} @ red_residual {residual.precio:.2f} (${masa:.0f}).",
            )

    async def _saltar_redes_latido(
        self, beru: BeruShip, px: float, lat: dict,
    ) -> bool:
        """Salta al piso más lejos que ya tocó el oído. Una reserva, una masa."""
        n = beru_continuo.n_peldaños_red(beru, px, lat)
        if n <= 0:
            return False
        arma = beru_altar_cazador.sincronizar_arma(beru)
        grado = beru_altar_cazador.grado_de_barco(beru)
        if not beru_ley.engorde_permitido():
            beru_continuo.saltar_pisos_red(beru, n, 0.0)
            await self.bel.anotar(
                "BERU", "MOVER_CONDICIONAL",
                f"{beru.uid} {grado}/{arma} Hoz/Red +{n}*0.1% (engorde OFF).",
            )
            self._bitacora(
                "MOVER_CONDICIONAL", beru,
                detalle=f"Hoz/Red +{n}*0.1% (engorde OFF)", masa_extra=0.0,
            )
            return True
        act = self._activo_de_barco(beru)
        if not beru_cazador.manto_vivo(self.tusk, act):
            beru_continuo.saltar_pisos_red(beru, n, 0.0)
            await self.bel.anotar(
                "BERU", "ENGORDE_SIN_MANTO",
                f"{beru.uid} {act} Red tocada — Hoz avanza {n} piso(s) sin masa "
                "(Santo sin manto Igris).",
            )
            self._bitacora(
                "ENGORDE_SIN_MANTO", beru,
                detalle=f"Hoz avanza {n} piso(s) sin masa (sin manto Igris)",
            )
            return True
        paso = float(beru_cazador.engorde_paso_usd(act, grado) or 0)
        n_masa = n
        if beru_continuo.boveda_ahogada(self.tusk):
            # Precio sí salta al piso; masa no se hincha (carta chica en la Oz).
            beru_continuo.saltar_pisos_red(beru, n, 0.0)
            beru_rafaga.sincronizar_masa_rafaga(beru)
            await self.bel.anotar(
                "BERU", "MOVER_CONDICIONAL",
                f"{beru.uid} {grado} Hoz/Red +{n}*0.1% "
                f"(bóveda ahogada · masa intacta ${float(beru.masa or 0):.2f}).",
            )
            self._bitacora(
                "MOVER_CONDICIONAL",
                beru,
                detalle=f"+{n} piso(s) ahogada sin masa extra tramo ${beru.masa:.2f}",
                masa_extra=0.0,
                masa_usd=float(beru.masa or 0),
            )
            return True
        if self._ensayo_nivel3() and paso > 0:
            aire = max(
                0.0,
                beru_ensayo.max_masa_usd()
                - float(getattr(beru, "masa", 0) or 0),
            )
            n_masa = min(n, int(aire // paso))
            if n_masa <= 0:
                await self.bel.anotar(
                    "BERU", "TECHO_MASA_ENSAYO",
                    f"{beru.uid} conserva Hoz: techo "
                    f"${beru_ensayo.max_masa_usd():.2f}.",
                )
                return False
        masa_extra = paso * float(n_masa)
        if await self.tusk.solicitar_reserva(
            f"E_{beru.uid}", masa_extra, "BERU", beru.direccion,
            consumir_auth=beru_ley.consumir_auth_en_reserva(),
        ):
            beru_continuo.saltar_pisos_red(beru, n_masa, masa_extra)
            beru_rafaga.sincronizar_masa_rafaga(beru)
            await self.bel.anotar(
                "BERU", "MOVER_CONDICIONAL",
                f"{beru.uid} {grado} Hoz/Red +{n_masa}*0.1% "
                f"(+${masa_extra:.2f}) tramo ${beru.masa:.2f}.",
            )
            self._bitacora(
                "MOVER_CONDICIONAL",
                beru,
                detalle=f"+{n_masa} piso(s) +${masa_extra:.2f} tramo ${beru.masa:.2f}",
                masa_extra=float(masa_extra),
                masa_usd=float(beru.masa or 0),
            )
            return True
        return False

    def _hoz_desfasada(self, beru: BeruShip) -> bool:
        """Memoria ya saltó; la carta en casa aún no está en ese piso."""
        if bool(getattr(beru, "altar_rependiente", False)):
            return True
        if beru_rafaga.es_radar(beru):
            return False
        oz = float(getattr(beru, "oz_adan", 0) or 0)
        if oz <= 0:
            return False
        status = str(getattr(beru, "altar_order_status", "") or "")
        if status in ("Cancelled", "Rejected", "Deactivated"):
            return True
        if not str(getattr(beru, "altar_link_id", "") or ""):
            return True
        trig = float(getattr(beru, "altar_trigger_price", 0) or 0)
        if trig <= 0:
            return True
        if abs(oz - trig) > 1e-8:
            return True
        return False

    def _pedir_mover_hoz(self, beru: BeruShip) -> None:
        """Un viaje por Santo. Si ya vuela, el destino queda el piso de ahora."""
        if self._altar_en_vuelo(beru):
            beru.altar_rependiente = True
            return
        self._lanzar_altar(beru, self._ciclo_mover_hoz(beru))

    async def _ciclo_mover_hoz(self, beru: BeruShip) -> str:
        """Enmendar (o plan B) hasta que la carta coincida con la memoria."""
        out = "sin_hoz"
        while True:
            oz0 = float(getattr(beru, "oz_adan", 0) or 0)
            masa0 = float(beru_rafaga.masa_para_carta(beru) or 0)
            beru.altar_rependiente = False
            out = await self._replantar_hoz_nativa(beru)
            if bool(getattr(beru, "altar_rependiente", False)):
                continue
            if abs(float(getattr(beru, "oz_adan", 0) or 0) - oz0) > 1e-9:
                continue
            if abs(float(beru_rafaga.masa_para_carta(beru) or 0) - masa0) > 1e-6:
                continue
            return out

    async def _acordeon_cazador_capas(self, precio_actual: float, latidos=None):
        """Los cuatro grados mueven la misma Hoz condicional con engorde.

        Acecho y caza oyen el mismo latido. La Hoz en vivo solo cierra con fill.
        El ``precio_actual`` de la casa es muleta si el Santo aún no tiene ojos.
        """
        lats = dict(latidos or {})

        async def _caza(beru: BeruShip):
            await self._pulso_caza_uno(beru, precio_actual, lats)

        cazando = [
            b for b in list(self.legion)
            if b.estado == "CAZANDO"
        ]
        await self._mapear_santos(cazando, _caza)

    async def _pulso_caza_uno(
        self, beru: BeruShip, precio_actual: float, lats: dict,
    ) -> None:
        if beru.estado != "CAZANDO":
            return
        if self._es_tumor_legacy(beru) or beru.estado == "FOSIL_BLOQUEADO":
            beru.estado = "FOSIL_BLOQUEADO"
            return

        act = self._activo_de_barco(beru)
        lat = dict(lats.get(act) or {})
        px = float(lat.get("last") or 0) or self._precio_de_barco(beru)
        if px <= 0:
            px = float(precio_actual or 0)
        if px <= 0:
            return

        beru_altar_cazador.sincronizar_arma(beru)

        if self._manos_exchange(beru):
            if await self._cosechar_si_fill_nativo(beru):
                return

        seq = beru_continuo.secuencia_latido_spot(beru, px, lat)
        if not seq:
            seq = [px]

        visito_oz = beru_continuo.toca_oz_en_latido(beru, px, lat) or any(
            beru_cazador.toca_oz(p, beru.direccion, beru.oz_adan) for p in seq
        )
        if visito_oz:
            if self._manos_exchange(beru):
                if await self._cosechar_si_fill_nativo(beru, forzar_consulta=True):
                    return
                if beru_rafaga.es_radar(beru):
                    if beru_rafaga.debe_rafaga(beru):
                        await self._ejecutar_rafaga(beru)
                    if beru_rafaga.debe_rafaga(beru):
                        return
                    qty = float(getattr(beru, "qty_rafaga_acum", 0) or 0)
                    if bool(getattr(beru, "rafaga_hecha", False)) or qty > 0:
                        fill_local = {
                            "avgPrice": float(beru.oz_adan or px),
                            "cumExecQty": 0.0,
                            "orderStatus": "RADAR",
                            "order_id": "",
                        }
                        await self._cosechar_si_fill_nativo(
                            beru, fill_local=fill_local,
                        )
                    return
                if await self._cosechar_venta_cruzada(beru, px):
                    return
                return
            if float(beru.masa or 0) > 0:
                fill = float(beru.oz_adan or px)
                await self._cosecha_capa_cazador(beru, fill)
            return

        if await self._saltar_redes_latido(beru, px, lat):
            if self._manos_exchange(beru):
                self._pedir_mover_hoz(beru)
        elif self._manos_exchange(beru) and self._hoz_desfasada(beru):
            self._pedir_mover_hoz(beru)

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
        """FÓSIL: reciclaje+2% era tumor. Tras cosecha manda reinicio continuo."""
        raise RuntimeError("FOSIL_BLOQUEADO: reciclaje extirpado")

    async def _crear_negociador_post_cazador(
        self,
        beru_origen: BeruShip,
        precio_actual: float,
        ancla_pct: float,
        centro_manto: float | None = None,
    ):
        """FÓSIL: no se crean negociadores. El mismo Beru sigue en CAZA."""
        _ = beru_origen, precio_actual, ancla_pct, centro_manto
        return None

    async def _cosecha_capa_cazador(self, beru: BeruShip, precio_actual: float):
        """Hoz cobra; funeral y relevo puro desde la última Red tocada."""
        if bool(getattr(beru, "relevo_creado", False)):
            return
        masa_tramo = float(beru.masa or 0)
        act = self._activo_de_barco(beru)
        grado = beru_altar_cazador.grado_de_barco(beru)
        ultima_red = float(getattr(beru, "ultima_red_tocada_pct", 0) or 0)
        uid_cosecha = f"COSECHA_{str(uuid.uuid4())[:4]}"
        beru.estado = "ESPERANDO_SUELTA"
        await self._ejecutar_cosecha(beru, uid_cosecha)
        if beru.estado == "COSECHADO":
            fill = float(beru.precio_salida_real or precio_actual)
            hijo = beru_altar_cazador.crear_relevo_desde_hoz(
                beru,
                fill,
                activo=act,
                fill_confirmado=True,
            )
            if hijo is not None:
                self.legion.append(hijo)
                await self.bel.anotar(
                    "BERU", "RELEVO_CAZADOR",
                    f"{beru.uid} cosechó ${masa_tramo:.2f}; funeral confirmado · "
                    f"Red tocada {ultima_red*100:.2f}% → {hijo.uid} "
                    f"llamado +{hijo.llamado_tramo_pct*100:.2f}% ({grado}).",
                )
                self._bitacora(
                    "RELEVO_CAZADOR",
                    beru,
                    detalle=f"→ {hijo.uid}",
                    hijo_uid=hijo.uid,
                    masa_usd=masa_tramo,
                    ultima_red_pct=round(ultima_red * 100.0, 4),
                )
            else:
                await self.bel.anotar(
                    "BERU", "COSECHA_CONDICIONAL_MARISCAL",
                    f"{beru.uid} {grado} cosechó ${masa_tramo:.2f}; "
                    "recorrido cerrado, sin plan A ni carta gorda.",
                )
                self._bitacora(
                    "COSECHA_MARISCAL",
                    beru,
                    detalle="recorrido cerrado, sin relevo",
                    masa_usd=masa_tramo,
                )

    async def _acordeon_negociador_legacy(self, beru: BeruShip, precio_actual: float):
        """FÓSIL: acordeón negociador extirpado."""
        _ = beru, precio_actual
        return

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
        """Compat pública: cosecha y relevo CAZADOR; jamás negociador."""
        _ = relevo_modo, ancla_cosecha_pct, centro_manto, masa_congelada
        uid_cosecha = f"COSECHA_{str(uuid.uuid4())[:4]}"
        beru_actual.estado = "ESPERANDO_SUELTA"
        await self._ejecutar_cosecha(beru_actual, uid_cosecha)
        if beru_actual.estado == "COSECHADO":
            fill = float(beru_actual.precio_salida_real or precio_actual)
            hijo = beru_altar_cazador.crear_relevo_desde_hoz(
                beru_actual,
                fill,
                activo=self._activo_de_barco(beru_actual),
                fill_confirmado=True,
            )
            if hijo is not None:
                self.legion.append(hijo)

    async def _ejecutar_cosecha(self, barco, uid_cosecha, forzar: bool = False):
        if self._manos_exchange(barco):
            await self.tusk.liberar_reserva(uid_cosecha)
            barco.estado = "ALTAR_NATIVO_PENDIENTE"
            await self.bel.anotar(
                "BERU", "ALTAR_NATIVO_PENDIENTE",
                "Salida market bloqueada; falta fill/cancel nativo del altar.",
            )
            return
        act = self._activo_de_barco(barco)
        px_barco = self._precio_de_barco(barco)
        ctx_map, estado = await self.tank.vision_especulativa()
        aborta, motivo = beru_ley.debe_abortar_por_vision(
            estado, ctx_map,
            precio_casa=px_barco if px_barco > 0 else self._precio_casa(),
            tank=self.tank,
        )
        if aborta and not forzar:
            barco.estado = "CAZANDO"
            await self.bel.anotar("BERU", "COSECHA_DIFERIDA", f"Ciego/visión: {motivo}")
            return
        if forzar and aborta and float(px_barco or self._precio_casa() or 0) <= 0:
            barco.estado = "ESPERANDO_SUELTA"
            return

        is_long_cosecha = barco.direccion != "LONG"
        mejor_f, p_ef = await self._radar_casa(
            ctx_map or {}, barco.masa, is_long_cosecha, base=act,
        )
        hoz = float(getattr(barco, "oz_adan", 0) or 0)
        if hoz > 0 and (
            self._manos_fantasma() or config.MODO_SIMULACION or not barco.precio_entrada_real
        ):
            p_ef = hoz
        beneficio = beru_continuo.beneficio_cosecha_pct(barco, p_ef)
        es_continuo = str(getattr(barco, "modo_combate", "") or "") == "CAZA"
        if not forzar and not es_continuo and beneficio < config.UMBRAL_COSECHA_MIN:
            barco.estado = "CAZANDO"
            await self.bel.anotar("BERU", "PACIENCIA", f"Beneficio {beneficio*100:.2f}% insuficiente.")
            return

        if not await self.tusk.solicitar_reserva(
            uid_cosecha, barco.masa, "BERU", "LONG" if is_long_cosecha else "SHORT",
            consumir_auth=beru_ley.consumir_auth_en_reserva(),
        ):
            barco.estado = "CAZANDO"
            return

        categoria = mercado.frente_a_category(mejor_f)
        symbol = mercado.frente_a_symbol(mejor_f)
        side = "Sell" if barco.direccion == "LONG" else "Buy"
        market_unit = "quoteCoin" if categoria == "spot" and barco.direccion != "LONG" else None
        qty_orden = barco.masa
        is_lev = None
        if categoria == "spot":
            if beru_ley.spot_margen_activo():
                is_lev = 1
            if barco.direccion == "LONG":
                qty_orden = float(getattr(barco, "qty_base_ejecutada", 0) or 0)
                if qty_orden <= 0 and barco.precio_entrada_real > 0:
                    qty_orden = barco.masa / barco.precio_entrada_real
                market_unit = None
            else:
                market_unit = "quoteCoin"
                qty_orden = barco.masa

        manos_reales = self._manos_exchange(barco)

        if manos_reales:
            if self._ensayo_nivel3():
                beru_ensayo.registrar(
                    "COSECHA_ENVIANDO",
                    detalle="market salida REAL",
                    uid=barco.uid,
                    activo=self._activo_de_barco(barco),
                    lado_entrada=barco.direccion,
                    side=side,
                    symbol=symbol,
                    frente=mejor_f,
                    qty=float(qty_orden or 0),
                    masa_usd=float(barco.masa or 0),
                    precio=float(p_ef or 0),
                    beneficio_pct=round(float(beneficio or 0) * 100.0, 4),
                )
            resultado = await self.bridge.place_order(
                symbol, side, qty_orden, category=categoria,
                market_unit=market_unit, is_leverage=is_lev,
            )
            if not resultado.exito:
                await self.tusk.liberar_reserva(uid_cosecha)
                barco.estado = "CAZANDO"
                if self._ensayo_nivel3():
                    beru_ensayo.anotar_orden_fallida(
                        resultado.mensaje,
                        uid=barco.uid,
                        evento_ctx="cosecha",
                    )
                return
            fill = await self.bridge.esperar_fill(symbol, order_id=resultado.order_id, category=categoria)
            if not fill.exito:
                await self.tusk.liberar_reserva(uid_cosecha)
                barco.estado = "CAZANDO"
                if self._ensayo_nivel3():
                    beru_ensayo.anotar_orden_fallida(
                        "fill_timeout_o_fallo",
                        uid=barco.uid,
                        evento_ctx="cosecha",
                    )
                return
            p_ef = fill.datos.get("avgPrice", p_ef)
            beneficio = beru_continuo.beneficio_cosecha_pct(barco, p_ef)
            if self._ensayo_nivel3():
                beru_ensayo.anotar_cosecha_ok(
                    uid=barco.uid,
                    side=side,
                    symbol=symbol,
                    precio=float(p_ef or 0),
                    qty=float(qty_orden or 0),
                    order_id=getattr(resultado, "order_id", None),
                )
        elif self._manos_fantasma() or config.MODO_SIMULACION:
            if self._manos_fantasma():
                beru_fantasma.registrar(
                    "COSECHA_CONDICIONAL",
                    detalle="fill de Hoz en papel — NO enviado a Bybit",
                    uid=barco.uid,
                    activo=act,
                    lado_entrada=barco.direccion,
                    side=side,
                    symbol=symbol,
                    frente=mejor_f,
                    qty=float(qty_orden or 0),
                    masa_usd=float(barco.masa or 0),
                    precio=float(p_ef or 0),
                    beneficio_pct=round(float(beneficio or 0) * 100.0, 4),
                    forzar=bool(forzar),
                )
        else:
            await self.tusk.liberar_reserva(uid_cosecha)
            barco.estado = "CAZANDO"
            await self.bel.anotar(
                "BERU", "COSECHA_SIN_MANOS",
                "Cosecha lista pero manos OFF — sin orden.",
            )
            return

        await self.tusk.consumar_cosecha_atomica(uid_cosecha, mejor_f, barco)
        barco.frente_salida = mejor_f
        barco.precio_salida_real = p_ef
        barco.estado = "COSECHADO"
        lec = beru_continuo.lecturas_cosecha(barco, p_ef)
        texto = beru_continuo.texto_lecturas_cosecha(lec)
        extra = beru_continuo.extra_bitacora_cosecha(lec)
        await self.bel.anotar("BERU", "COSECHA", texto)
        self._cronica(
            barco, "COSECHA", texto,
            precio=float(p_ef or 0), **extra,
        )
        if getattr(barco, "ciclo_infinito", False) or getattr(barco, "engorde_bloqueado", False):
            await self._iniciar_reciclaje_post_venta(barco, float(p_ef or 0))

    async def _fusion_negociadores_ciclo(self):
        """Fósil sellado: Beru continuo no fusiona ni crea Mega."""
        return

        # FÓSIL histórico, inalcanzable.
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
            msg = (
                f"{lider.uid} <- {len(victimas) + 1} {tag} oz~{lider.oz_adan:.2f} "
                f"${lider.masa_congelada:.0f} (reciclaje volumen sumado)."
            )
            await self.bel.anotar("BERU", "FUSION_COLISION", msg)
            self._cronica(
                lider, "FUSION", msg,
                n_fusionados=len(victimas) + 1, tag=tag,
            )

        for lider, victimas, prom in beru_fusion.grupos_mega_beru(self.legion):
            vacio = lider.adn_capitan.vacio_adan
            beru_fusion.aplicar_mega_beru(lider, victimas, prom, vacio)
            for v in victimas:
                v.estado = "FUSIONADO"
            msg_mega = (
                f"{lider.uid} prom ancla {prom * 100:.2f}% <- {len(victimas) + 1} barcos "
                f"(${lider.masa_congelada:.0f}) · cond {lider.neg_oz_pct * 100:.2f}%."
            )
            await self.bel.anotar("BERU", "MEGA_BERU", msg_mega)
            self._cronica(
                lider, "MEGA_BERU", msg_mega,
                n_fusionados=len(victimas) + 1, ancla_pct=round(prom * 100.0, 4),
            )

    # === FUSIÓN Y LIMPIEZA ===

    async def evaluar_colisiones_y_fusion(self):
        """Compatibilidad externa: fusión/Mega extirpados."""
        return

        # FÓSIL histórico, inalcanzable.
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
        # FOSIL_BLOQUEADO se conserva en cuarentena: no pelea, no detiene a nadie.
        self.legion = [
            b for b in self.legion
            if b.estado not in ("COSECHADO", "FUSIONADO", "ESPERANDO_SUELTA")
        ]

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
                legado = (
                    str(item.get("modo_combate", "") or "").upper() == "NEGOCIADOR"
                    or bool(item.get("neg_post_cazador"))
                    or bool(item.get("ciclo_infinito"))
                    or bool(item.get("es_super_beru"))
                    or float(item.get("masa_congelada", 0) or 0) > 0
                    or str(item.get("estado", "") or "").upper() in {
                        "NEGOCIANDO",
                        "ESPERANDO_CONDICIONAL",
                        "ESPERANDO_ABISMO",
                        "FUSIONADO",
                    }
                )
                self.legion.append(BeruShip(
                    uid=item["uid"],
                    centro_local=item.get("centro_local", 0.0),
                    masa=item.get("masa", 0.0),
                    direccion=item.get("direccion", "LONG"),
                    estado="FOSIL_BLOQUEADO" if legado else item.get("estado", "ACECHANDO"),
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
                    modo_combate="CAZA",
                    centro_manto=item.get("centro_manto", 0.0),
                    ancla_tramo=item.get("ancla_tramo", item.get("centro_local", 0.0)),
                    cosechas_continuas=item.get("cosechas_continuas", 0),
                    llamado_tramo_pct=item.get("llamado_tramo_pct", 0.0),
                    masa_tramo_usd=item.get("masa_tramo_usd", item.get("masa", 0.0)),
                    oz_pct=item.get("oz_pct", 0.0),
                    red_pct=item.get("red_pct", 0.0),
                    arma_cazador=item.get("arma_cazador", ""),
                    ultima_red_tocada_pct=item.get("ultima_red_tocada_pct", 0.0),
                    ultima_red_tocada_precio=item.get("ultima_red_tocada_precio", 0.0),
                    ultima_hoz_tocada_pct=item.get("ultima_hoz_tocada_pct", 0.0),
                    ultima_hoz_tocada_precio=item.get("ultima_hoz_tocada_precio", 0.0),
                    oreja_sangre_activa=item.get("oreja_sangre_activa", False),
                    oreja_red_activa=item.get("oreja_red_activa", False),
                    llamado_red_pct=item.get("llamado_red_pct", 0.0),
                    es_relevo_cazador=item.get("es_relevo_cazador", False),
                    padre_cazador_uid=item.get("padre_cazador_uid", ""),
                    relevo_cazador_uid=item.get("relevo_cazador_uid", ""),
                    relevo_creado=item.get("relevo_creado", False),
                    funeral_red_confirmado=item.get("funeral_red_confirmado", False),
                    altar_revision=item.get("altar_revision", 0),
                    altar_order_id=item.get("altar_order_id", ""),
                    altar_link_id=item.get("altar_link_id", ""),
                    altar_order_status=item.get("altar_order_status", ""),
                    altar_trigger_price=item.get("altar_trigger_price", 0.0),
                    altar_cancel_confirmado=item.get("altar_cancel_confirmado", False),
                    hoz_modo=item.get("hoz_modo", ""),
                    masa_carta_usd=item.get("masa_carta_usd", 0.0),
                    masa_rafaga_usd=item.get("masa_rafaga_usd", 0.0),
                    rafaga_en_curso=False,
                    rafaga_hecha=item.get("rafaga_hecha", False),
                    rafaga_ultimo_ts=item.get("rafaga_ultimo_ts", 0.0),
                    qty_rafaga_acum=item.get("qty_rafaga_acum", 0.0),
                    qty_base_ejecutada=item.get("qty_base_ejecutada", 0.0),
                    capa=item.get("capa", 1),
                    neg_post_cazador=item.get("neg_post_cazador", False),
                    ancla_cosecha_pct=item.get("ancla_cosecha_pct", 0.0),
                    neg_oz_pct=item.get("neg_oz_pct", 0.0),
                    neg_red_pct=item.get("neg_red_pct", 0.0),
                    neg_toques_ciclo=item.get("neg_toques_ciclo", 0),
                    ciclo_infinito=item.get("ciclo_infinito", False),
                    masa_congelada=item.get("masa_congelada", 0.0),
                    ts_wake=float(item.get("ts_wake") or 0),
                ))
            except (KeyError, TypeError):
                continue
