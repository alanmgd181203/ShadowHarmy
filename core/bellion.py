import os
import json
import time
import asyncio
from dataclasses import asdict

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
import core.config as config

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

    async def publicar_estado_vivo(self, tusk, beru_legion, igris):
        """Escribe un snapshot ligero cada segundo para que el panel lo lea."""
        peso_l = sum(f["long"] for f in tusk.pesos.values())
        peso_s = sum(f["short"] for f in tusk.pesos.values())
        masa_bruta = peso_l + peso_s

        banda_min, banda_max = igris.calcular_banda_delta()

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
            "margen_ocupado": tusk.margen_ocupado,
            "masa_autorizada": tusk.masa_autorizada,
            "masa_bruta": masa_bruta,
            "peso_long": peso_l,
            "peso_short": peso_s,
            "delta_ratio": (peso_l / masa_bruta) if masa_bruta > 0 else 0.5,
            "banda_min": banda_min,
            "banda_max": banda_max,
            "pesos_por_frente": {f: dict(p) for f, p in tusk.pesos.items()},
            "legion": legion_resumen,
            "ciclos_consumados": tusk.total_ciclos_consumados,
        }

        try:
            with open("data/estado_vivo.json", "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
        except Exception:
            pass