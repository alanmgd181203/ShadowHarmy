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

    # Tier Proto/Pleno + oficio (desde 2026-08-15: CAZA continuo únicamente)
    tier_id: str = ""
    modo_combate: str = ""

    # Cazador continuo: 0 absoluto Igris + 0 local del tramo
    centro_manto: float = 0.0
    ancla_tramo: float = 0.0
    cosechas_continuas: int = 0
    llamado_tramo_pct: float = 0.0
    masa_tramo_usd: float = 0.0
    oz_pct: float = 0.0
    red_pct: float = 0.0
    # Arma del cazador: CONDICIONAL en los cuatro grados. Mariscal cierra sin hijo.
    arma_cazador: str = ""
    # Relevo puro: la frontera que desplegó la Hoz y el hijo que dejó.
    # Son datos del oficio CAZA; nunca crean negociador/residual/Mega.
    ultima_red_tocada_pct: float = 0.0
    ultima_red_tocada_precio: float = 0.0
    ultima_hoz_tocada_pct: float = 0.0
    ultima_hoz_tocada_precio: float = 0.0
    # Tras cosecha: sangre 1.1 desde la última Hoz; Red 0.9/0.5/0.3 despierta hijo
    # y APAGA la sangre vieja. Nunca dos llamados vivos.
    oreja_sangre_activa: bool = False
    oreja_red_activa: bool = False
    llamado_red_pct: float = 0.0
    es_relevo_cazador: bool = False
    padre_cazador_uid: str = ""
    relevo_cazador_uid: str = ""
    relevo_creado: bool = False
    funeral_red_confirmado: bool = False
    # Primera caza: nace dentro de su Vacío (0 local = wake).
    sangre_vista_dentro: bool = False
    # Recibo del altar nativo. Persistirlo impide duplicar cartas al reiniciar.
    altar_revision: int = 0
    altar_order_id: str = ""
    altar_link_id: str = ""
    altar_order_status: str = ""
    altar_trigger_price: float = 0.0
    altar_cancel_confirmado: bool = False
    capa: int = 1
    # Post-Mega: sangre absoluta sobre 0 de Igris (ej. +0.309 si purga en +30%)
    piso_sangre_pct: float = 0.0

    # Negociador post-cazador (abismo, condicional, ciclo 5+resorte)
    neg_post_cazador: bool = False
    ancla_cosecha_pct: float = 0.0
    neg_oz_pct: float = 0.0
    neg_red_pct: float = 0.0
    neg_toques_ciclo: int = 0

    # Ciclo infinito Cazador ↔ Negociador (masa congelada, sin engorde)
    ciclo_infinito: bool = False
    masa_congelada: float = 0.0

    # Reciclaje doctrina Monarca 2026-07-11
    engorde_bloqueado: bool = False
    volumen_reciclaje: float = 0.0
    trigger_salida: float = 0.0
    trigger_recompra: float = 0.0
    bracket_armado: bool = False
    red_extrema: float = 0.0
    precio_fusion_ref: float = 0.0
    fase_reciclaje: str = ""  # "" | ESPERANDO_SALIDA | ARMADO_ADAN | ESPERANDO_RECOMPRA

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
    """Contrato legacy hacia altar Greed. Runtime: Beru spot; manto = Igris→Bridge directo."""
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