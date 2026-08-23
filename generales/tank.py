import asyncio
import time
from collections import deque

from core.models import MarketContext
from core import mercado
from core import spreads as spread_calc
from generales.capitanes import CapitanAnsiedad, CapitanCazador, CapitanNormal
import core.config as config


def _frentes_iniciales():
    frentes = getattr(config, "FRENTES_TANK", None) or getattr(
        config, "FRENTES_RESONANCIA_TANK", config.MARES_PENTIVERSO_ALL,
    )
    return list(frentes)


def _frentes_resonancia():
    return getattr(config, "FRENTES_RESONANCIA_TANK", config.MARES_PENTIVERSO_ALL)


class TankNode:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.estado_foco = "ROJO"
        self.latencia_ms = 999.0
        self.jitter_ms = 0.0
        self.ultima_actualizacion = time.time()
        frentes = _frentes_iniciales()
        self.precios = {f: 0.0 for f in frentes}
        self.muros = {f: {"ask": 0.0, "bid": 0.0} for f in frentes}
        self.libros: dict[str, dict] = {}
        self.funding = {}
        self.index_prices = {}

    def asegurar_frente(self, f_key: str):
        if f_key not in self.precios:
            self.precios[f_key] = 0.0
        if f_key not in self.muros:
            self.muros[f_key] = {"ask": 0.0, "bid": 0.0}

    def inyectar_verdad_real(self, f_key: str, price: float, latency: float):
        self.asegurar_frente(f_key)
        delta = abs(latency - self.latencia_ms)
        self.jitter_ms = (self.jitter_ms * 0.8) + (delta * 0.2)
        self.latencia_ms, self.ultima_actualizacion = latency, time.time()
        self.precios[f_key] = price

    def inyectar_muro(self, f_key: str, bid_vol: float, ask_vol: float):
        self.asegurar_frente(f_key)
        if bid_vol > 0:
            self.muros[f_key]["bid"] = bid_vol
        if ask_vol > 0:
            self.muros[f_key]["ask"] = ask_vol

    def asegurar_libro(self, f_key: str):
        self.asegurar_frente(f_key)
        if f_key not in self.libros:
            self.libros[f_key] = {"bids": [], "asks": [], "ts": 0.0}

    @staticmethod
    def _parse_niveles(niveles: list) -> list[list[float]]:
        out: list[list[float]] = []
        for row in niveles or []:
            try:
                p, q = float(row[0]), float(row[1])
                out.append([p, q])
            except (IndexError, TypeError, ValueError):
                continue
        return out

    @staticmethod
    def _merge_niveles(existing: list, updates: list, *, reverse: bool) -> list[list[float]]:
        book: dict[float, float] = {}
        for row in existing or []:
            try:
                book[float(row[0])] = float(row[1])
            except (IndexError, TypeError, ValueError):
                continue
        for row in updates or []:
            try:
                price, size = float(row[0]), float(row[1])
            except (IndexError, TypeError, ValueError):
                continue
            if size <= 0:
                book.pop(price, None)
            else:
                book[price] = size
        ordered = sorted(book.items(), key=lambda x: x[0], reverse=reverse)
        max_n = getattr(config, "ANCLA_LIBRO_MAX_NIVELES", 50)
        return [[p, s] for p, s in ordered[:max_n]]

    def _actualizar_muro_desde_libro(self, f_key: str):
        libro = self.libros.get(f_key) or {}
        bid_vol = sum(float(r[1]) for r in (libro.get("bids") or [])[:5])
        ask_vol = sum(float(r[1]) for r in (libro.get("asks") or [])[:5])
        self.inyectar_muro(f_key, bid_vol, ask_vol)

    def inyectar_libro_snapshot(self, f_key: str, bids: list, asks: list):
        self.asegurar_libro(f_key)
        self.libros[f_key]["bids"] = self._merge_niveles([], bids, reverse=True)
        self.libros[f_key]["asks"] = self._merge_niveles([], asks, reverse=False)
        self.libros[f_key]["ts"] = time.time()
        self._actualizar_muro_desde_libro(f_key)

    def aplicar_delta_libro(self, f_key: str, bid_updates: list, ask_updates: list):
        self.asegurar_libro(f_key)
        # Sin snapshot fresco (post-reconexión): ignorar deltas — evitan libro zombi
        if float(self.libros[f_key].get("ts") or 0) <= 0:
            return
        if bid_updates:
            self.libros[f_key]["bids"] = self._merge_niveles(
                self.libros[f_key]["bids"], bid_updates, reverse=True,
            )
        if ask_updates:
            self.libros[f_key]["asks"] = self._merge_niveles(
                self.libros[f_key]["asks"], ask_updates, reverse=False,
            )
        self.libros[f_key]["ts"] = time.time()
        self._actualizar_muro_desde_libro(f_key)

    def invalidar_libros(self, bases: list[str] | None = None) -> int:
        """Vacía libros (WS caído). bases=None → todos."""
        from core import igris_ojos as ojos

        return ojos.invalidar_libros_tank(self, bases)

    def inyectar_funding(self, f_key: str, rate: float):
        self.asegurar_frente(f_key)
        self.funding[f_key] = rate

    def inyectar_index(self, f_key: str, index_px: float):
        self.asegurar_frente(f_key)
        self.index_prices[f_key] = index_px

    def precios_con_reflejo(self):
        return mercado.aplicar_reflejos_usdc_lineal(self.precios)


class TankCluster:
    def __init__(self, tusk, bellion, ticker_base=None):
        self.tusk, self.bel = tusk, bellion
        self.ticker_base = ticker_base or config.TICKER_BASE
        self.nodos = [TankNode(i) for i in range(1, 5)]
        self.historial_precios = deque(maxlen=30)
        self.capitan_activo = CapitanNormal
        self.tsunami_activado = False
        self.sentidos_extra = {
            "spread_producto": [],
            "alpha": {},
            "convert": [],
            "convert_quotes": [],
            "errores": {},
            "ts_spread": 0.0,
            "ts_alpha": 0.0,
            "ts_convert": 0.0,
            "ts_convert_quotes": 0.0,
        }
        self.matriz_spreads: list[dict] = []
        self.desvios_indice: list[dict] = []
        self.panorama_global: list[dict] = []
        self.ref_binance: dict = {}
        self._ultimo_calc_spreads = 0.0
        # Latido lineal (mecha): tratos/ticks entre pulsos de Beru rango.
        self._latidos_lineal: dict[str, dict] = {}
        self.ts_rio_lineal_ws = 0.0
        self._latido_prints_max = int(
            getattr(config, "BERU_RANGO_LATIDO_PRINTS_MAX", 500) or 500
        )

    def inyectar_ref_binance(self, base: str, mid: float, ts: float):
        self.ref_binance[base.upper()] = {"mid": mid, "ts": ts}

    def registrar_print_lineal(self, f_key: str, price: float, *, fuente_ws: bool = True) -> None:
        """Acumula un trato/tick en el vaso del latido lineal (no limpia)."""
        frente = str(f_key or "").upper()
        px = float(price or 0)
        if not frente.endswith("USDT_LINEAL") or px <= 0:
            return
        bucket = self._latidos_lineal.get(frente)
        if not bucket:
            bucket = {"last": 0.0, "high": 0.0, "low": 0.0, "prints": []}
            self._latidos_lineal[frente] = bucket
        bucket["last"] = px
        hi = float(bucket.get("high") or 0)
        lo = float(bucket.get("low") or 0)
        bucket["high"] = px if hi <= 0 else max(hi, px)
        bucket["low"] = px if lo <= 0 else min(lo, px)
        prints = bucket.setdefault("prints", [])
        prints.append(px)
        max_n = max(20, int(self._latido_prints_max or 200))
        if len(prints) > max_n:
            del prints[: len(prints) - max_n]
        if fuente_ws:
            self.ts_rio_lineal_ws = time.time()

    def consumir_latido_lineal(self, f_key: str) -> dict:
        """Devuelve y vacía el latido lineal de ese frente."""
        frente = str(f_key or "").upper()
        bucket = self._latidos_lineal.pop(frente, None) or {}
        last = float(bucket.get("last") or 0)
        hi = float(bucket.get("high") or 0)
        lo = float(bucket.get("low") or 0)
        prints = [float(p) for p in (bucket.get("prints") or []) if float(p or 0) > 0]
        if last <= 0 and prints:
            last = float(prints[-1])
        if hi <= 0 and last > 0:
            hi = last
        if lo <= 0 and last > 0:
            lo = last
        return {"last": last, "high": hi, "low": lo, "prints": prints}

    def expandir_frentes(self, frentes):
        for nodo in self.nodos:
            for f in frentes:
                nodo.asegurar_frente(f)

    def _precio_referencia(self, nodo):
        p = nodo.precios_con_reflejo()
        prim = f"{self.ticker_base}USDT_LINEAL"
        spot = f"{self.ticker_base}USDT_SPOT"
        return p.get(prim) or p.get(spot) or 0.0

    async def vigilar_aguas(self):
        n_tri = len(getattr(config, "ACTIVOS_TRINIDAD", []))
        print(
            f"[TANK] Trinidad {n_tri} activos | pentiverso {config.ACTIVOS_PENTIVERSO} | "
            f"beru {getattr(config, 'FRENTES_BERU_VIGILANCIA', [])} | "
            f"ref: {self.ticker_base} ({config.FASE_ACTUAL})."
        )
        while True:
            self._auditar_semaforos()
            lider = self._obtener_lider_verde()
            if not lider:
                # Arena / arranque: aún sin VERDE, calcular matriz desde el nodo más fresco
                candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
                lider_calc = candidatos[0] if candidatos else None
                if lider_calc and (time.time() - lider_calc.ultima_actualizacion) < 30:
                    self._actualizar_matriz_spreads(lider_calc)
            if lider:
                self._actualizar_matriz_spreads(lider)
            if lider and self._precio_referencia(lider) > 0:
                px = lider.precios_con_reflejo()
                p_perp = px.get(f"{self.ticker_base}USDT_LINEAL", 0.0)
                p_spot = px.get(f"{self.ticker_base}USDT_SPOT", 0.0)
                p_inv = px.get(f"{self.ticker_base}USD_INVERSE", 0.0)
                await self.tusk.actualizar_precios(p_perp, p_spot, p_inv)
                ref = self._precio_referencia(lider)
                ahora = time.time()
                self.historial_precios.append((ahora, ref))
                while self.historial_precios and (ahora - self.historial_precios[0][0]) > 30:
                    self.historial_precios.popleft()
                await self.evaluar_clima()
            await asyncio.sleep(0.5)

    def _actualizar_matriz_spreads(self, lider):
        ahora = time.time()
        if ahora - self._ultimo_calc_spreads < getattr(config, "MATRIZ_SPREADS_CALC_S", 2):
            return
        self._ultimo_calc_spreads = ahora
        px = lider.precios_con_reflejo()
        self.matriz_spreads = spread_calc.calcular_matriz_spreads(
            px,
            funding=lider.funding,
            index_prices=lider.index_prices,
        )
        self.desvios_indice = spread_calc.calcular_desvios_indice(
            px,
            index_prices=lider.index_prices,
        )
        self.panorama_global = spread_calc.calcular_panorama_global(
            px,
            lider.index_prices,
            self.ref_binance,
        )

    async def evaluar_clima(self):
        if len(self.historial_precios) < 10:
            return
        p_ini, p_fin = self.historial_precios[0][1], self.historial_precios[-1][1]
        inercia = abs(p_fin - p_ini) / max(p_ini, 1.0)
        if inercia >= 0.02:
            if not self.tsunami_activado:
                self.capitan_activo, self.tsunami_activado = CapitanAnsiedad, True
                await self.bel.anotar("TANK", "ALERTA", f"¡TSUNAMI! {inercia*100:.2f}% → Ansiedad.")
        elif inercia <= 0.001:
            if self.capitan_activo != CapitanAnsiedad:
                self.capitan_activo, self.tsunami_activado = CapitanAnsiedad, False
                await self.bel.anotar("TANK", "CLIMA", "Aguas estancadas.")
        else:
            if self.tsunami_activado and inercia > 0.005:
                return
            if self.capitan_activo != CapitanNormal:
                self.capitan_activo, self.tsunami_activado = CapitanNormal, False
                await self.bel.anotar("TANK", "CLIMA", "Aguas normales.")

    def _auditar_semaforos(self):
        ahora = time.time()
        for nodo in self.nodos:
            if (ahora - nodo.ultima_actualizacion) > config.TOLERANCIA_COMA_S:
                nodo.estado_foco, nodo.latencia_ms = "CONGELADO", 999.0
                continue
            if nodo.latencia_ms <= config.UMBRAL_VERDE_MS:
                nodo.estado_foco = "VERDE"
            elif nodo.latencia_ms <= config.UMBRAL_AMARILLO_MS:
                nodo.estado_foco = "AMARILLO"
            else:
                nodo.estado_foco = "ROJO"

    def _obtener_lider_verde(self):
        verdes = [n for n in self.nodos if n.estado_foco == "VERDE"]
        if verdes:
            return min(verdes, key=lambda n: n.latencia_ms)
        amarillos = [n for n in self.nodos if n.estado_foco == "AMARILLO"]
        return min(amarillos, key=lambda n: n.latencia_ms) if amarillos else None

    def invalidar_libros(self, bases: list[str] | None = None) -> int:
        """Tirar fotos de libros en todos los nodos (ojos rotos / reconexión)."""
        from core import igris_ojos as ojos

        return ojos.invalidar_libros_tank(self, bases)

    async def vision_especulativa(self):
        lider = self._obtener_lider_verde()
        if not lider:
            candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
            lider = candidatos[0] if candidatos else None
        if not lider:
            return None, "ROJO"
        ahora_ms = time.time() * 1000
        frentes = lider.precios_con_reflejo()
        vigia = set(_frentes_resonancia())
        ctx_map = {}
        for f, p in frentes.items():
            if f not in vigia:
                continue
            muro = lider.muros.get(f, {"ask": 0.0, "bid": 0.0})
            ctx_map[f] = MarketContext(
                symbol=f.split("_")[0], market_type=f.split("_")[1],
                last_price=p, spread=0.01,
                depth_ask=muro["ask"], depth_bid=muro["bid"],
                volatilidad=0.005, timestamp=ahora_ms, local_arrival=ahora_ms,
                muro_ask_volumen=muro["ask"], muro_bid_volumen=muro["bid"],
            )

        auditores = [n for n in self.nodos if n.estado_foco in ["VERDE", "AMARILLO"] and n.node_id != lider.node_id]
        estado_consenso = "VERDE_SEGURO"
        ref_key = f"{self.ticker_base}USDT_LINEAL"
        ref_p = frentes.get(ref_key, 0.0)
        for auditor in auditores:
            aud_p = auditor.precios_con_reflejo().get(ref_key, 0.0)
            if ref_p > 0 and abs(ref_p - aud_p) / ref_p > config.TOLERANCIA_GLITCH:
                estado_consenso = "GLITCH_DETECTADO"
                lider.latencia_ms += 500.0
                break
        return ctx_map, estado_consenso

    def snapshot_pentiverso(self):
        lider = self._obtener_lider_verde()
        if not lider:
            candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
            lider = candidatos[0] if candidatos else None
        if not lider:
            return {}

        frentes = lider.precios_con_reflejo()
        out = {}
        for f in config.MARES_PENTIVERSO_ALL:
            p = frentes.get(f, 0.0)
            m = lider.muros.get(f, {"bid": 0.0, "ask": 0.0})
            reflejo = (
                f.endswith("USDC_LINEAL")
                and lider.precios.get(f, 0) <= 0
                and lider.precios.get(f.replace("LINEAL", "SPOT"), 0) > 0
            )
            if reflejo and m["bid"] == 0 and m["ask"] == 0:
                sm = lider.muros.get(f.replace("LINEAL", "SPOT"), {"bid": 0.0, "ask": 0.0})
                m = {"bid": sm["bid"], "ask": sm["ask"]}
            asset = mercado.activo_de_frente(f)
            out[f] = {
                "precio": p,
                "muro_bid": m["bid"],
                "muro_ask": m["ask"],
                "reflejo_spot": reflejo,
                "activo": asset,
            }
        return out

    def snapshot_trinidad(self):
        """Resumen de sentidos trinidad (precio + muro) por activo."""
        lider = self._obtener_lider_verde()
        if not lider:
            candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
            lider = candidatos[0] if candidatos else None
        if not lider:
            return {"activos": 0, "frentes_vivos": 0, "muros_vivos": 0, "detalle": {}}

        detalle = {}
        frentes_vivos = muros_vivos = 0
        for base in getattr(config, "ACTIVOS_TRINIDAD", []):
            fila = {}
            for suf, tag in [("USDT_LINEAL", "lineal"), ("USD_INVERSE", "inverse"), ("USDT_SPOT", "spot")]:
                f = f"{base}{suf}"
                p = lider.precios.get(f, 0.0)
                m = lider.muros.get(f, {"bid": 0.0, "ask": 0.0})
                if p > 0:
                    frentes_vivos += 1
                if m["bid"] > 0 or m["ask"] > 0:
                    muros_vivos += 1
                fila[tag] = {"precio": p, "muro_bid": m["bid"], "muro_ask": m["ask"]}
            detalle[base] = fila

        esperados = len(getattr(config, "FRENTES_TRINIDAD", []))
        return {
            "activos": len(detalle),
            "frentes_esperados": esperados,
            "frentes_vivos": frentes_vivos,
            "muros_vivos": muros_vivos,
            "detalle": detalle,
        }

    def snapshot_usdc_spot(self):
        """Resumen spot USDC — precio + muros por activo permitido."""
        lider = self._obtener_lider_verde()
        if not lider:
            candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
            lider = candidatos[0] if candidatos else None
        if not lider:
            return {"activos": 0, "frentes_vivos": 0, "muros_vivos": 0}

        frentes_vivos = muros_vivos = 0
        for base in getattr(config, "ACTIVOS_USDC_SPOT", []):
            f = f"{base}USDC_SPOT"
            p = lider.precios.get(f, 0.0)
            m = lider.muros.get(f, {"bid": 0.0, "ask": 0.0})
            if p > 0:
                frentes_vivos += 1
            if m["bid"] > 0 or m["ask"] > 0:
                muros_vivos += 1

        esperados = len(getattr(config, "FRENTES_USDC_SPOT", []))
        return {
            "activos": len(getattr(config, "ACTIVOS_USDC_SPOT", [])),
            "frentes_esperados": esperados,
            "frentes_vivos": frentes_vivos,
            "muros_vivos": muros_vivos,
        }

    def _snapshot_rail(self, pares: list[dict]) -> dict:
        lider = self._obtener_lider_verde()
        if not lider:
            candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
            lider = candidatos[0] if candidatos else None
        if not lider:
            return {"pares": 0, "frentes_vivos": 0, "muros_vivos": 0, "detalle": {}}

        detalle = {}
        frentes_vivos = muros_vivos = 0
        for p in pares:
            f = p["frente"]
            precio = lider.precios.get(f, 0.0)
            m = lider.muros.get(f, {"bid": 0.0, "ask": 0.0})
            if precio > 0:
                frentes_vivos += 1
            if m["bid"] > 0 or m["ask"] > 0:
                muros_vivos += 1
            detalle[f] = {
                "symbol": p["symbol"],
                "category": p["category"],
                "precio": precio,
                "muro_bid": m["bid"],
                "muro_ask": m["ask"],
            }

        return {
            "pares": len(detalle),
            "frentes_esperados": len(pares),
            "frentes_vivos": frentes_vivos,
            "muros_vivos": muros_vivos,
            "detalle": detalle,
        }

    def snapshot_usde(self):
        """7 pares USDE — spot + 1 linear (sentidos Tank)."""
        return self._snapshot_rail(getattr(config, "USDE_PARES", []))

    def snapshot_usd1(self):
        """6 pares USD1 — spot + 1 linear (sentidos Tank)."""
        return self._snapshot_rail(getattr(config, "USD1_PARES", []))

    def snapshot_mnt_spot(self):
        """Pares spot MNT — ventanilla *MNT + token MNT/* (sentidos Tank)."""
        return self._snapshot_rail(getattr(config, "MNT_SPOT_PARES", []))

    def snapshot_spot_all(self):
        """Mapa spot completo Bybit — precio + muros (sentidos Tank)."""
        return self._snapshot_rail(getattr(config, "SPOT_ALL_PARES", []))

    def snapshot_linear_perp(self):
        """Todos los perpetuos lineales (USDT + USDC settle)."""
        return self._snapshot_rail(getattr(config, "LINEAR_PERP_PARES", []))

    def snapshot_inverse_perp(self):
        """Todos los perpetuos inverse."""
        return self._snapshot_rail(getattr(config, "INVERSE_PERP_PARES", []))

    def snapshot_linear_futures(self):
        """Futuros lineales con vencimiento (trimestrales / dated)."""
        return self._snapshot_rail(getattr(config, "LINEAR_FUTURES_PARES", []))

    def snapshot_inverse_futures(self):
        """Futuros inverse con vencimiento."""
        return self._snapshot_rail(getattr(config, "INVERSE_FUTURES_PARES", []))

    def forzar_matriz_spreads(self) -> dict:
        """Recalcula matriz sin exigir semáforo VERDE (arena / diagnóstico)."""
        lider = self._obtener_lider_verde()
        if not lider:
            candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
            lider = candidatos[0] if candidatos else None
        if lider:
            # Bypass throttle para forzar snapshot fresco
            self._ultimo_calc_spreads = 0.0
            self._actualizar_matriz_spreads(lider)
        return self.snapshot_matriz_spreads()

    def snapshot_matriz_spreads(self):
        """Top spreads calculados desde precios Tank (arbitraje presente)."""
        lider = self._obtener_lider_verde()
        if not lider:
            candidatos = sorted(self.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
            lider = candidatos[0] if candidatos else None
        funding_vivos = len(lider.funding) if lider else 0
        index_vivos = sum(1 for v in (lider.index_prices.values() if lider else []) if v and float(v) > 0)
        return {
            "filas": list(self.matriz_spreads),
            "top_n": len(self.matriz_spreads),
            "funding_vivos": funding_vivos,
            "index_vivos": index_vivos,
            "ts_calc": self._ultimo_calc_spreads,
        }

    def snapshot_funding(self):
        """Funding rate presente (desde ticker WS derivados)."""
        lider = self._obtener_lider_verde()
        if not lider:
            return {"vivos": 0, "detalle": {}}
        detalle = {}
        for f, rate in lider.funding.items():
            try:
                rv = float(rate)
            except (TypeError, ValueError):
                continue
            base = mercado.activo_de_frente(f)
            detalle[f] = {
                "base": base,
                "funding_rate": rv,
                "funding_pct": round(rv * 100, 6),
            }
        # Top |funding| para panel
        top = sorted(detalle.values(), key=lambda x: abs(x["funding_rate"]), reverse=True)[:15]
        return {"vivos": len(detalle), "top": top, "detalle": detalle}

    def snapshot_sentidos_extra(self):
        """Spread producto Bybit, Alpha, Convert — REST complementario."""
        sp = self.sentidos_extra.get("spread_producto", [])
        alpha = self.sentidos_extra.get("alpha", {})
        conv = self.sentidos_extra.get("convert", [])
        return {
            "spread_producto": {
                "instrumentos": len(sp),
                "vivos": sum(1 for x in sp if x.get("lastPrice", 0) > 0),
                "ts": self.sentidos_extra.get("ts_spread", 0),
                "top": sorted(sp, key=lambda x: abs(x.get("lastPrice", 0)), reverse=True)[:10],
            },
            "alpha": {
                "tokens": alpha.get("total", len(alpha.get("tokens", []))),
                "ts": self.sentidos_extra.get("ts_alpha", 0),
                "muestra": (alpha.get("tokens") or [])[:10],
            },
            "convert": {
                "pares": len(conv),
                "ts": self.sentidos_extra.get("ts_convert", 0),
                "muestra": conv[:15],
            },
            "convert_quotes": {
                "filas": len(self.sentidos_extra.get("convert_quotes", [])),
                "ts": self.sentidos_extra.get("ts_convert_quotes", 0),
                "muestra": (self.sentidos_extra.get("convert_quotes") or [])[:10],
            },
            "errores": dict(self.sentidos_extra.get("errores", {})),
        }

    def snapshot_desvios_indice(self):
        huerfanas = sum(1 for r in self.desvios_indice if r.get("huerfana"))
        perps_con_indice = sum(1 for r in self.desvios_indice if (r.get("index_price") or 0) > 0)
        return {
            "filas": list(self.desvios_indice),
            "top_n": len(self.desvios_indice),
            "perps_con_indice": perps_con_indice,
            "huerfanas_en_top": huerfanas,
            "umbral_alerta_pct": getattr(config, "DESVIO_ALERTA_PCT", 0.5),
            "ts_calc": self._ultimo_calc_spreads,
        }

    def snapshot_panorama_global(self):
        ref_vivos = sum(
            1 for v in self.ref_binance.values()
            if (time.time() - float(v.get("ts", 0))) <= getattr(config, "REF_STALE_S", 30)
        )
        alertas = sum(1 for r in self.panorama_global if r.get("estado") == "DESALINEADO")
        return {
            "filas": list(self.panorama_global),
            "bases_huerfanas": len(getattr(config, "ACTIVOS_HUERFANOS", []) or []),
            "refs_binance": ref_vivos,
            "ref_binance_vivos": ref_vivos,
            "ref_binance_total": len(self.ref_binance),
            "alertas_desalineado": alertas,
            "ts_calc": self._ultimo_calc_spreads,
        }
