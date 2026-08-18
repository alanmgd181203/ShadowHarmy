from dataclasses import dataclass

# === [SUBTEMA: IMPORTACIONES Y CONFIGURACIÓN] ===
import core.config as config

# === [SUBTEMA: GENÉTICA BASE (ADN)] ===

@dataclass
class ADN_Capitan:
    """Plantilla genética — comportamiento Beru (oz/red cada 0.1%)."""
    nombre: str
    vacio_adan: float        # Umbral gatillo semilla (%)
    margen_apertura: float   # Distancia Oz/Red al nacer (0.1% = 0.001)
    latigazo_snap: float
    distancia_pendulo: float


# --- Ansiedad (1.2%) — más ciclos, mercados laterales ---
CapitanAnsiedad = ADN_Capitan(
    nombre=f"ANSIEDAD_{config.FASE_ACTUAL}",
    vacio_adan=float(getattr(config, "BERU_VACIO_ANSIEDAD", 0.012)),
    margen_apertura=0.001,
    latigazo_snap=0.002,
    distancia_pendulo=0.01,
)

# --- Normal (1.1%) — Vacío de Adán vivo; primer silbato de todos los grados ---
CapitanNormal = ADN_Capitan(
    nombre=f"NORMAL_{config.FASE_ACTUAL}",
    vacio_adan=float(getattr(config, "BERU_VACIO_NORMAL", 0.011)),
    margen_apertura=0.001,
    latigazo_snap=0.002,
    distancia_pendulo=0.015,
)

# Aliases legacy
CapitanCazador = CapitanNormal
CapitanBerserker = CapitanAnsiedad  # clima volátil → ansiedad, no tercer perfil

CAPITANES_BERU = (CapitanAnsiedad, CapitanNormal)
