from dataclasses import dataclass

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
import core.config as config

# === [SUBTEMA: GENÉTICA BASE (ADN)] ===

@dataclass
class ADN_Capitan:
    """Plantilla genética que define el comportamiento de combate en el Pentiverso."""
    nombre: str
    vacio_adan: float        # Umbral para activar la orden condicional
    margen_apertura: float   # Distancia de la Oz y la Red al nacer el barco
    latigazo_snap: float     # El tamaño del salto defensivo (seguro de botín)
    distancia_pendulo: float # Distancia para fusiones o descarte de barcos

# === [SUBTEMA: ALTAR DE CAPITANES (INSTANCIAS)] ===

# --- 🟢 CAPITÁN FRICCIÓN (MODO ANSIEDAD) ---
# Objetivo: Alta frecuencia. Robar centavos en mercados laterales.
CapitanAnsiedad = ADN_Capitan(
    nombre=f"FRICCIÓN_{config.FASE_ACTUAL}", 
    vacio_adan=0.006,        # 0.6%
    margen_apertura=0.001,   # +- 0.1%
    latigazo_snap=0.002,     # 0.2%
    distancia_pendulo=0.01   # 1.0%
)

# --- 🟡 CAPITÁN CAZADOR (MODO EQUILIBRIO) ---
# Objetivo: Calidad y seguimiento de tendencia. El motor de la Legión.
# 🔴 SOLDADURA: Snap mantenido al 0.2% para protección estricta.
CapitanCazador = ADN_Capitan(
    nombre=f"CAZADOR_{config.FASE_ACTUAL}",  
    vacio_adan=0.015,        # 1.5%
    margen_apertura=0.001,   # +- 0.1%
    latigazo_snap=0.002,     # 0.2%
    distancia_pendulo=0.015  # 1.5%
)

# --- 🔴 CAPITÁN BERSERKER (MODO TSUNAMI) ---
# Objetivo: Sobrevivir y surfear volatilidad extrema.
CapitanBerserker = ADN_Capitan(
    nombre=f"TSUNAMI_{config.FASE_ACTUAL}",   
    vacio_adan=0.020,        # 2.0%
    margen_apertura=0.003,   # +- 0.3%
    latigazo_snap=0.006,     # 0.6% (Respiración en el caos)
    distancia_pendulo=0.02   # 2.0%
)