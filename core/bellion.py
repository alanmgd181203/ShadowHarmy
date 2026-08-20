import os
import json
import time
import asyncio
from dataclasses import asdict

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
import core.config as config
from core.igris_estado import funding_vigilancia, resumen_manto
from core.manto_touch import snapshot_toques
from core.beru_capital import resumen_capital

class BellionAuditor:
    def __init__(self):
        """
        Bellion: El Escribano del Multiverso.
        Custodia la memoria del sistema. La transparencia y la 
        velocidad de recuperación son las leyes fundamentales.
        """
        # Rutas dinámicas basadas en el cerebro central
        self.ruta_estado = f"data/estado_{config.FASE_ACTUAL.lower()}.json"
        self.ruta_historial = f"data/historial_{config.FASE_ACTUAL.lower()}.jsonl"
        self.ruta_historial_cola = "data/historial_cola.jsonl"
        self._cola_max_lineas = 150
        self._lock = asyncio.Lock()
        from core.bellion_oido import OidoRing
        self._oido = OidoRing(
            max_n=int(getattr(config, "BELLION_OIDO_ANILLO", 80) or 80),
        )

        if not os.path.exists("data"):
            os.makedirs("data")
        self._sembrar_cola_desde_historial()

    def _sembrar_cola_desde_historial(self):
        """Cola corta para el panel (evita servir 4MB de jsonl por poll)."""
        try:
            if not os.path.exists(self.ruta_historial):
                return
            with open(self.ruta_historial, "r", encoding="utf-8", errors="replace") as f:
                lineas = f.readlines()
            cola = lineas[-self._cola_max_lineas:]
            with open(self.ruta_historial_cola, "w", encoding="utf-8") as f:
                f.writelines(cola)
        except Exception as e:
            print(f"[BELLION] No se pudo sembrar cola panel: {e}")

    def _actualizar_cola(self, registro: str):
        try:
            prev: list[str] = []
            if os.path.exists(self.ruta_historial_cola):
                with open(self.ruta_historial_cola, "r", encoding="utf-8", errors="replace") as f:
                    prev = f.readlines()
            prev.append(registro if registro.endswith("\n") else registro + "\n")
            prev = prev[-self._cola_max_lineas:]
            with open(self.ruta_historial_cola, "w", encoding="utf-8") as f:
                f.writelines(prev)
        except Exception:
            pass

    async def anotar(self, general: str, accion: str, detalle: str):
        """Registra el evento en el cristal histórico y lo proyecta al Monarca."""
        from core.bellion_oido import clasificar
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        registro = f"[{timestamp}] [{general}] {accion}: {detalle}\n"
        nivel = clasificar(general, accion, detalle)

        async with self._lock:
            with open(self.ruta_historial, "a", encoding="utf-8") as f:
                f.write(registro)
            self._actualizar_cola(registro)
            self._oido.push(
                general=general, accion=accion, detalle=detalle, nivel=nivel,
            )

        print(registro.strip())
        if nivel == "critico":
            print(f"[BELLION OIDO · CRITICO] {general} {accion}")

    def snapshot_oido(self) -> dict:
        """Susurro para Pergamino / estado_vivo (sin ruido)."""
        return self._oido.snapshot(
            limit=int(getattr(config, "BELLION_OIDO_LIMIT", 40) or 40),
            incluir_ruido=bool(getattr(config, "BELLION_OIDO_INCLUIR_RUIDO", False)),
        )

    async def guardar_estado(self, datos: dict):
        """Sella la fotografía del Multiverso con seguridad piezoeléctrica."""
        async with self._lock:
            try:
                with open(self.ruta_estado, "w", encoding="utf-8") as f:
                    json.dump(datos, f, indent=4)
            except Exception as e:
                print(f"[BELLION] ERROR DE SELLADO: {e}")

    def cargar_estado(self):
        """Recupera la memoria tras un reinicio del sistema."""
        if os.path.exists(self.ruta_estado):
            try:
                with open(self.ruta_estado, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[BELLION] Error al leer cristal: {e}")
        return None

    async def ley_de_sucesion(self, tusk_data, legion):
        """Captura el estado total de la flota y la bóveda para el sellado."""
        legion_serializada = []
        for barco in (legion or []):
            legion_serializada.append(asdict(barco))

        estado_total = {
            "timestamp": time.time(),
            "fase": config.SISTEMA_NOMBRE,
            "boveda": tusk_data,
            "legion": legion_serializada,
            "metria_margen": tusk_data.get("margen_ocupado", 0.0)
        }

        await self.guardar_estado(estado_total)

    # === ESTADO VIVO (PARA PANEL STREAMLIT) ===

    async def publicar_estado_vivo(self, tusk, beru_legion, igris, tank=None, kaiser=None):
        """Escribe un snapshot ligero cada segundo para que el panel lo lea."""
        peso_l = sum(f["long"] for f in tusk.pesos.values())
        peso_s = sum(f["short"] for f in tusk.pesos.values())
        masa_bruta = peso_l + peso_s

        if igris is not None and hasattr(igris, "calcular_banda_delta"):
            banda_min, banda_max = igris.calcular_banda_delta()
        else:
            banda_min, banda_max = 0.0, 0.0
        funding_snap = tank.snapshot_funding() if tank else {}
        igris_resumen = resumen_manto(
            margen_ocupado_pct=tusk.margen_ocupado,
            peso_long=peso_l,
            peso_short=peso_s,
            banda_min=banda_min,
            banda_max=banda_max,
        )
        igris_resumen["funding_extremo"] = funding_vigilancia(funding_snap)
        igris_resumen["toques_greed_manto"] = snapshot_toques(tusk)
        from core import igris_manto as im
        igris_resumen["promedios_pierna"] = im.resumen_promedios(tusk.pesos)
        from core import plan_crecimiento as pc
        from core import beru_capital as bc
        from core import manto_ventana as mv
        from core import tusk_libros as tl
        eq = float(tusk.masa_bruta_real or tusk.masa_bruta or 0)
        igris_resumen["plan_crecimiento"] = pc.resumen_plan(eq)
        pesos_vw = tusk.pesos or {}
        usd_l, usd_s = mv.usd_piernas_desde_pesos(pesos_vw)
        if usd_l + usd_s <= 0:
            usd_l, usd_s = float(peso_l), float(peso_s)
        igris_resumen["ventana_manto"] = mv.resumen_barco(usd_l, usd_s)
        igris_resumen["marcha"] = {
            "id": None,
            "titulo": "Igris de baja",
            "preferencia_asalto": False,
        }
        igris_resumen["meta_engorde"] = {"ok": False, "motivo": "igris_de_baja"}
        igris_resumen["ley_masa"] = {"ok": None, "motivo": "igris_de_baja", "bloqueado": None}
        igris_resumen["mision"] = {"ok": False, "motivo": "igris_de_baja"}
        igris_resumen["frecuencia_manto"] = {"de_baja": True}
        igris_resumen["libros_foco"] = {}
        igris_resumen["libros_eth"] = {}

        tusk_libros_snap = tl.snapshot_libros(tusk)
        progresion = bc.telemetria_progresion(eq)

        beru_flota: dict = {"activos": []}
        beru_details: dict = {}
        legion_resumen: list = []
        try:
            from core import beru_asset_detail as bad
            from core import beru_rail as br

            sem = br.activo_semilla()
            legion_resumen = bad.enriquecer_legion_resumen(beru_legion or [], sem)
            beru_flota = bad.flota_resumen(beru_legion or [], semilla=sem)
            precios_mark: dict[str, float] = {}
            if tank and hasattr(tank, "_obtener_lider_verde"):
                lider = tank._obtener_lider_verde()
                if lider and hasattr(lider, "precios_con_reflejo"):
                    px = lider.precios_con_reflejo() or {}
                    for row in beru_flota.get("activos") or []:
                        a = str(row.get("activo") or "")
                        for q in ("USDT", "USDC"):
                            p = float(px.get(f"{a}{q}_SPOT") or 0)
                            if p > 0:
                                precios_mark[a] = p
                                break
            beru_details = bad.mapa_asset_details(
                beru_legion or [], precios=precios_mark, semilla=sem,
            )
        except Exception as e:
            beru_flota = {"error": str(e), "activos": []}
            beru_details = {}
            for b in (beru_legion or []):
                legion_resumen.append({
                    "uid": b.uid, "estado": b.estado, "direccion": b.direccion,
                    "centro": b.centro_local, "masa": b.masa,
                    "max_favor": getattr(b, "max_favor", 0.0),
                    "es_super": getattr(b, "es_super_beru", False),
                    "generacion": b.generacion,
                })

        snapshot = {
            "ts": time.time(),
            "sistema": config.SISTEMA_NOMBRE,
            "ticker_base": config.TICKER_BASE,
            "activos_pentiverso": config.ACTIVOS_PENTIVERSO,
            "trinidad": tank.snapshot_trinidad() if tank else {},
            "usdc_spot": tank.snapshot_usdc_spot() if tank else {},
            "usde": tank.snapshot_usde() if tank else {},
            "usd1": tank.snapshot_usd1() if tank else {},
            "mnt_spot": tank.snapshot_mnt_spot() if tank else {},
            "spot_all": tank.snapshot_spot_all() if tank else {},
            "linear_perp": tank.snapshot_linear_perp() if tank else {},
            "inverse_perp": tank.snapshot_inverse_perp() if tank else {},
            "linear_futures": tank.snapshot_linear_futures() if tank else {},
            "inverse_futures": tank.snapshot_inverse_futures() if tank else {},
            "matriz_spreads": tank.snapshot_matriz_spreads() if tank else {},
            "desvios_indice": tank.snapshot_desvios_indice() if tank else {},
            "panorama_global": tank.snapshot_panorama_global() if tank else {},
            "funding": tank.snapshot_funding() if tank else {},
            "sentidos_extra": tank.snapshot_sentidos_extra() if tank else {},
            "kaiser": kaiser.snapshot() if kaiser else {},
            "margen_ocupado": tusk.margen_ocupado,
            "total_maintenance_margin_usd": getattr(tusk, "total_maintenance_margin_usd", None),
            "account_mm_rate": getattr(tusk, "account_mm_rate", None),
            "igris_posiciones": tusk.snapshot_telemetria_posiciones(),
            "masa_autorizada": tusk.masa_autorizada,
            "masa_bruta": masa_bruta,
            "masa_bruta_real": float(getattr(tusk, "masa_bruta_real", 0) or 0),
            "tusk_tesoreria": tusk.snapshot_tesoreria() if hasattr(tusk, "snapshot_tesoreria") else {},
            "peso_long": peso_l,
            "peso_short": peso_s,
            "delta_ratio": (usd_l / (usd_l + usd_s)) if (usd_l + usd_s) > 0 else 0.5,
            "banda_min": banda_min,
            "banda_max": banda_max,
            "igris": igris_resumen,
            "tusk_libros": tusk_libros_snap,
            "greed_basis_abiertos": list(getattr(tusk, "greed_basis_abiertos", None) or []),
            "beru_capital": resumen_capital(),
            # Motor dinámico — Árbol de Evolución / panel
            "grado_beru": progresion["grado_beru"],
            "costo_base_X": progresion["costo_base_X"],
            "rango_ejercito": progresion["rango_ejercito"],
            "rango_ejercito_id": progresion["rango_ejercito_id"],
            "progresion": progresion,
            "pesos_por_frente": {f: dict(p) for f, p in tusk.pesos.items()},
            "pentiverso": tank.snapshot_pentiverso() if tank else {},
            "legion": legion_resumen,
            "beru_flota": beru_flota,
            "ciclos_consumados": tusk.total_ciclos_consumados,
        }

        snapshot["igris_asset_details"] = {}

        snapshot["beru_asset_details"] = beru_details
        try:
            snapshot["bellion_oido"] = self.snapshot_oido()
        except Exception as e:
            snapshot["bellion_oido"] = {"error": str(e), "recientes": [], "por_nivel": {}}

        try:
            with open("data/estado_vivo.json", "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
        except Exception:
            pass