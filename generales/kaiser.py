"""
Kaiser — vocero interno; guardián de indicadores.
Lee snapshots Tank, interpreta, perfiles multietiqueta, rutas metaverso (sin disparar).
"""
from __future__ import annotations

import asyncio
import time

import core.config as config
from core import kaiser_indicators as indic
from core import kaiser_perfil as perfil
from core import kaiser_sampler as sampler
from core import metaverso_grafo as metaverso


class KaiserVocero:
    def __init__(self, tank, bellion):
        self.tank = tank
        self.bel = bellion
        self.ultimo_digest: dict = {}
        self.perfiles: dict = {}
        self._ultimo_refresh = 0.0
        self._ultimo_muestra = 0.0
        self._ultimo_perfil = 0.0
        self._alertas_logeadas: dict[str, float] = {}
        self._backfill_hecho = False
        from core.kaiser_pipeline import ColaOportunidadesGreed, RastreadorSpread
        self._rastreador_spread = RastreadorSpread()
        self._cola_greed = ColaOportunidadesGreed()
        self._ultimo_calc_ms = 0.0

    def _bases_perfil(self) -> list[str]:
        penta = list(config.ACTIVOS_PENTIVERSO)
        trinidad = list(getattr(config, "ACTIVOS_TRINIDAD", []) or [])
        top = [r.get("base") for r in (self.tank.desvios_indice or [])[:25]]
        huerf = list(getattr(config, "ACTIVOS_HUERFANOS", []) or [])[
            : getattr(config, "KAISER_PERFIL_HUERFANAS_CAP", 30)
        ]
        spot_extra: list[str] = []
        cap = int(getattr(config, "KAISER_SPOT_ALL_CAP", 60))
        for p in getattr(config, "SPOT_ALL_PARES", []) or []:
            if len(spot_extra) >= cap:
                break
            bc = str(p.get("baseCoin") or "").upper()
            qc = str(p.get("quoteCoin") or "").upper()
            sym = str(p.get("symbol") or "")
            if bc and (qc == "USDT" or sym.endswith("USDT")):
                spot_extra.append(bc)
        out: list[str] = []
        seen: set[str] = set()
        for b in penta + trinidad + top + huerf + spot_extra:
            if not b:
                continue
            bu = str(b).upper()
            if bu not in seen:
                seen.add(bu)
                out.append(bu)
        return out[: getattr(config, "KAISER_PERFIL_MAX_BASES", 40)]

    def _recalcular_perfiles(self) -> None:
        edges = ["perp_vs_index", "spot_vs_perp", "usdt_vs_usdc", "lineal_vs_inverse"]
        nuevos: dict = {}
        for base in self._bases_perfil():
            nuevos[base] = {}
            for edge in edges:
                nuevos[base][edge] = perfil.perfil_par(base, edge)
        self.perfiles = nuevos
        self._ultimo_perfil = time.time()

    def _metaverso_vivo(self) -> dict:
        from core import ancla

        matriz = self.tank.snapshot_matriz_spreads()
        filas = matriz.get("filas") or list(self.tank.matriz_spreads or [])
        bases = self._bases_perfil()
        libros = ancla.libros_desde_lider(self.tank)
        return metaverso.oportunidades_metaverso(filas, bases, self.perfiles, libros)

    def refrescar(self) -> dict:
        import time as _time
        from core.kaiser_pipeline import estimar_pipeline_ms

        t0 = _time.time()
        _, self._ultimo_muestra = sampler.muestrear_si_toca(self.tank, self._ultimo_muestra)

        if _time.time() - self._ultimo_perfil >= getattr(config, "KAISER_PROFILE_RECALC_S", 120):
            self._recalcular_perfiles()

        lider = self.tank._obtener_lider_verde()
        latencia = lider.latencia_ms if lider else 999.0
        pipeline = estimar_pipeline_ms(latencia, self._ultimo_calc_ms)

        mv = self._metaverso_vivo()
        self.ultimo_digest = indic.interpretar_tank(
            self.tank,
            perfiles=self.perfiles,
            metaverso=mv,
            pipeline=pipeline,
            rastreador=self._rastreador_spread,
            cola_greed=self._cola_greed,
        )
        self._ultimo_calc_ms = (_time.time() - t0) * 1000.0
        self._ultimo_refresh = _time.time()
        return self.ultimo_digest

    def cola_greed_viva(self) -> list[dict]:
        return self._cola_greed.cola_vivas()

    def oportunidades_abortadas(self) -> list[dict]:
        return self._cola_greed.abortadas_recientes()

    def snapshot(self) -> dict:
        if not self.ultimo_digest:
            return self.refrescar()
        return dict(self.ultimo_digest)

    def consumir(self, destinatario: str) -> list[dict]:
        snap = self.snapshot()
        if destinatario == "GREED":
            return self.cola_greed_viva() + indic.filtrar_por_destinatario(snap, destinatario)
        return indic.filtrar_por_destinatario(snap, destinatario)

    def consumir_greed(self) -> dict:
        """Slice Greed: cola viva + abortadas recientes."""
        return {
            "oportunidades_vivas": self.cola_greed_viva(),
            "abortadas": self.oportunidades_abortadas(),
            "pipeline_ms": (self.ultimo_digest.get("pipeline") or {}).get("total_ms"),
        }

    def consultar_liquidez(self, intencion: dict) -> dict:
        """Respuesta Ancla a intención de general (masa USD, frente(s))."""
        from core import ancla

        lider = self.tank._obtener_lider_verde()
        semaforo = lider.estado_foco if lider else "ROJO"
        latencia = lider.latencia_ms if lider else 999.0
        libros = ancla.libros_desde_lider(self.tank)
        precios = lider.precios_con_reflejo() if lider else {}
        return ancla.consultar_liquidez_intencion(
            intencion,
            libros,
            tank_semaforo=semaforo,
            latencia_ms=latencia,
            precios=precios,
        )

    def perfil_base(self, base: str, edge: str = "perp_vs_index") -> dict:
        return (self.perfiles.get(base.upper()) or {}).get(edge) or perfil.perfil_par(base, edge)

    def _debe_logear(self, alerta_id: str) -> bool:
        cooldown = getattr(config, "KAISER_ALERTA_COOLDOWN_S", 120)
        ahora = time.time()
        ultimo = self._alertas_logeadas.get(alerta_id, 0)
        if ahora - ultimo < cooldown:
            return False
        self._alertas_logeadas[alerta_id] = ahora
        return True

    async def _emitir_alertas_criticas(self, digest: dict):
        for a in digest.get("alertas", []):
            if a.get("severidad") != "ALERTA":
                continue
            aid = a.get("id", "")
            if not self._debe_logear(aid):
                continue
            await self.bel.anotar("KAISER", a.get("tipo", "ALERTA"), a.get("mensaje", ""))

    async def _backfill_inicial(self):
        if self._backfill_hecho or not getattr(config, "KAISER_BACKFILL_ON_START", True):
            return
        self._backfill_hecho = True
        try:
            from core.kaiser_backfill import backfill_bases
            loop = asyncio.get_running_loop()
            resultados = await loop.run_in_executor(None, backfill_bases)
            ok = sum(1 for r in resultados if r.get("ok"))
            await self.bel.anotar(
                "KAISER", "BACKFILL",
                f"Histórico kline: {ok}/{len(resultados)} bases.",
            )
        except Exception as exc:
            await self.bel.anotar("KAISER", "BACKFILL", f"Omitido: {repr(exc)[:120]}")

    async def vigilar_indicadores(self):
        await self.bel.anotar(
            "KAISER", "DESPERTAR",
            "Vocero activo — Ancla (orderbook) + perfiles + metaverso; no disparo.",
        )
        asyncio.create_task(self._backfill_inicial())
        intervalo = getattr(config, "KAISER_INTERVAL_S", 3.0)
        while True:
            try:
                digest = self.refrescar()
                await self._emitir_alertas_criticas(digest)
            except Exception as exc:
                await self.bel.anotar("KAISER", "ERROR", repr(exc)[:200])
            await asyncio.sleep(intervalo)
