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

        # El estado se marca con la identidad de config.py
        estado_total = {
            "timestamp": time.time(),
            "fase": config.SISTEMA_NOMBRE, 
            "boveda": tusk_data,
            "legion": legion_serializada,
            "metria_margen": tusk_data.get("margen_ocupado", 0.0)
        }
        
        await self.guardar_estado(estado_total)