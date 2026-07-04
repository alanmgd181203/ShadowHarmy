from dataclasses import dataclass, field
import time
import uuid

# === [SUBTEMA: IMPORTACIONES Y ADN] ===
from generales.capitanes import ADN_Capitan 
import core.config as config



# === [SUBTEMA: EL BARCO DE COMBATE (BeruShip)] ===

@dataclass
class BeruShip:
    """Representación física de un barco en el Pentiverso."""
    uid: str
    centro_local: float
    masa: float
    direccion: str
    estado: str = "ACECHANDO"
    red_adan: float = 0.0
    oz_adan: float = 0.0
    max_favor: float = 0.0
    distancia_gatillo: float = 0.005
    es_super_beru: bool = False
    generacion: int = 1
    is_veterano: bool = False

    # Pasaporte inmutable tras la materialización
    adn_capitan: ADN_Capitan = None

    # Trazabilidad Multipolar (Entrada)
    frente_asignado: str = "INDEFINIDO"
    precio_entrada_real: float = 0.0

    # Trazabilidad de Cuarzo (Cosecha/Salida)
    frente_salida: str = "INDEFINIDO"
    precio_salida_real: float = 0.0

    # Flag de sincronización con Greed
    sincronizado: bool = False



# === [SUBTEMA: CONTEXTO DE MERCADO (MarketContext)] ===

@dataclass
class MarketContext:
    """La fotografía de uno de los 5 mares de LTC."""
    symbol: str
    market_type: str        
    last_price: float
    spread: float
    depth_ask: float
    depth_bid: float
    volatilidad: float
    timestamp: float
    local_arrival: float
    
    # Muros de liquidez para el escaneo de Greed
    muro_ask_volumen: float = 0.0 
    muro_bid_volumen: float = 0.0

# === [SUBTEMA: VITALIDAD DEL SISTEMA (HealthState)] ===

@dataclass
class HealthState:
    """Monitoreo del latido de los nodos de la Hidra."""
    status: str             
    last_heartbeat: float
    jitter_ms: float
    sync_drift_ms: float
    reconnect_count: int = 0

# === [SUBTEMA: CONTRATOS DE ACCIÓN (IntencionAccion)] ===

@dataclass(order=True)
class IntencionAccion:
    """El mensaje contractual enviado al Altar de Greed."""
    prioridad: int
    timestamp: float = field(default_factory=time.time)
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8], compare=False)
    general: str = field(default="ANÓNIMO", compare=False)
    
    # Tipos: CAZA, COSECHA, PODAR_MANTO, LIMPIAR_ESPEJOS, etc.
    tipo: str = field(default="CAZA", compare=False)
    masa: float = field(default=0.0, compare=False)
    direccion: str = field(default="LONG", compare=False)
    dedupe_key: str = field(default="", compare=False)
    
    # SOLDADURA: Se lee exclusivamente desde config.py
    expira_en_ms: int = field(default=config.TTL_ORDEN_MS, compare=False)
    es_negociacion: bool = field(default=False, compare=False)
    
    # Referencia para inyección de liquidez y precio
    barco_ref: BeruShip = field(default=None, compare=False)
    precio_oz_objetivo: float = field(default=0.0, compare=False)

    def __post_init__(self):
        """🛡️ MAGIA DE MERLÍN: Escudo contra el fuego amigo."""
        if not self.dedupe_key:
            referencia_obj = self.barco_ref.uid if self.barco_ref else "MANTO"
            self.dedupe_key = f"{self.tipo}_{referencia_obj}"

    def es_valida(self) -> bool:
        """Verifica si la intención aún es aire fresco o ya es humo."""
        # Se asegura que la validación coincida con la purga de Tusk
        return (time.time() - self.timestamp) * 1000 < self.expira_en_ms