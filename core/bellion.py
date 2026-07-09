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
        self._lock = asyncio.Lock() 

        if not os.path.exists("data"):
            os.makedirs("data")

# === [SUBTEMA: CRÓNICAS (REGISTRO HISTÓRICO)] ===

    async def anotar(self, general: str, accion: str, detalle: str):
        """Registra el evento en el cristal histórico y lo proyecta al Monarca."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        registro = f"[{timestamp}] [{general}] {accion}: {detalle}\n"
        
        async with self._lock:
            with open(self.ruta_historial, "a", encoding="utf-8") as f:
                f.write(registro)
        
        # Reflejo instantáneo en consola
        print(registro.strip())

# === [SUBTEMA: PERSISTENCIA (EL CRISTAL DE MEMORIA)] ===

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

    # === [SUBTEMA: LEY DE SUCESIÓN (FOTOGRAFÍA MULTIVERSAL)] ===

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

        banda_min, banda_max = igris.calcular_banda_delta()
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
        eq = float(tusk.masa_bruta_real or tusk.masa_bruta or 0)
        igris_resumen["plan_crecimiento"] = pc.resumen_plan(eq)

        legion_resumen = []
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
            "masa_autorizada": tusk.masa_autorizada,
            "masa_bruta": masa_bruta,
            "peso_long": peso_l,
            "peso_short": peso_s,
            "delta_ratio": (peso_l / masa_bruta) if masa_bruta > 0 else 0.5,
            "banda_min": banda_min,
            "banda_max": banda_max,
            "igris": igris_resumen,
            "greed_basis_abiertos": list(getattr(tusk, "greed_basis_abiertos", None) or []),
            "beru_capital": resumen_capital(),
            "pesos_por_frente": {f: dict(p) for f, p in tusk.pesos.items()},
            "pentiverso": tank.snapshot_pentiverso() if tank else {},
            "legion": legion_resumen,
            "ciclos_consumados": tusk.total_ciclos_consumados,
        }

        try:
            with open("data/estado_vivo.json", "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
        except Exception:
            pass