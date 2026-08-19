import os

# === [CARGADOR DE SECRETOS .ENV] ===
def cargar_env():
    ruta_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(ruta_env):
        with open(ruta_env, mode="r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    try:
                        clave, valor = linea.split("=", 1)
                        os.environ[clave.strip()] = valor.strip().replace('"', '').replace("'", "")
                    except ValueError:
                        continue

cargar_env()

# Llaves duales: mainnet (batalla) vs testnet (entrenamiento). El puente usa un solo par.
API_KEY_MAINNET = os.getenv("BYBIT_API_KEY")
API_SECRET_MAINNET = os.getenv("BYBIT_API_SECRET")
API_KEY_TESTNET = os.getenv("BYBIT_TESTNET_API_KEY") or os.getenv("BYBIT_API_KEY_TESTNET")
API_SECRET_TESTNET = os.getenv("BYBIT_TESTNET_API_SECRET") or os.getenv("BYBIT_API_SECRET_TESTNET")

TESTNET = os.getenv("MODO_TESTNET", "True").lower() == "true"
# Con testnet: SOLO llaves de entrenamiento (nunca caer a mainnet por error).
# Con mainnet oficial: SOLO BYBIT_API_KEY / BYBIT_API_SECRET.
API_KEY = API_KEY_TESTNET if TESTNET else API_KEY_MAINNET
API_SECRET = API_SECRET_TESTNET if TESTNET else API_SECRET_MAINNET

MODO_SIMULACION = os.getenv("MODO_SIMULACION", "True").lower() == "true"
SAFE_MODE = os.getenv("SAFE_MODE", "False").lower() == "true"

# Testeo Igris — Beru y Greed hibernados; solo Igris + Tank + Tusk en arise.py
MODO_ENFOQUE_IGRIS = os.getenv("MODO_ENFOQUE_IGRIS", "True").lower() in ("1", "true", "yes")

# Fase 4 — ops Monarca (opcional en .env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# Oído Bellion 4.1.2 — susurro Pergamino (sin LLM / sin Telegram)
BELLION_OIDO_ANILLO = int(os.getenv("BELLION_OIDO_ANILLO", "80"))
BELLION_OIDO_LIMIT = int(os.getenv("BELLION_OIDO_LIMIT", "40"))
BELLION_OIDO_INCLUIR_RUIDO = os.getenv("BELLION_OIDO_INCLUIR_RUIDO", "false").lower() == "true"

# Activo principal: Beru acecho + manos testnet (referencia operativa)
TICKER_BASE = os.getenv("TICKER_BASE", "BTC").upper()
SIMBOLO_LINEAR = f"{TICKER_BASE}USDT"
FRENTE_PRINCIPAL = f"{TICKER_BASE}USDT_LINEAL"

# Pentiverso dual — ojos mainnet LTC + BTC (USDC fase 2)
ACTIVOS_PENTIVERSO = ["LTC", "BTC"]

# Beru — semilla y flota (doctrina capital manto)
BERU_ACTIVO_SEMILLA = os.getenv("BERU_ACTIVO_SEMILLA", "ETH").upper()

# Casa Beru en Tank (WS + resonancia) — además del pentiverso LTC/BTC
FRENTES_BERU_VIGILANCIA = [f"{BERU_ACTIVO_SEMILLA}USDT_SPOT"]
# Activos con precio vivo en Tank: pentiverso + semilla Beru
ACTIVOS_VIGILANCIA = list(dict.fromkeys(ACTIVOS_PENTIVERSO + [BERU_ACTIVO_SEMILLA]))
BERU_TIER_DEFAULT = os.getenv("BERU_TIER_DEFAULT", "PROTO1").upper()  # arranque: ProtoBeru ETH
BERU_MODO_COMBATE_DEFAULT = "CAZA"  # oficio único desde cirugía continua 2026-08-15
# Legacy — PnL/1% PLENO se expresa como 10×G_min del Santo (antes $50 con G_min=$5)
BERU_PNL_OBJETIVO_POR_1PCT_USD = float(os.getenv("BERU_PNL_OBJETIVO_POR_1PCT_USD", "50"))
BERU_SPOT_COLCHON_USD = float(os.getenv("BERU_SPOT_COLCHON_USD", "0"))  # spot margen: mismo equity, sin extra
BERU_VACIO_ANSIEDAD = float(os.getenv("BERU_VACIO_ANSIEDAD", "0.012"))   # 1.2% legado capitán
# Vacío de Adán vivo: ±1.1% — primer silbato de todos los grados (Hoz un peldaño atrás)
BERU_VACIO_NORMAL = float(os.getenv("BERU_VACIO_NORMAL", "0.011"))         # 1.1%
# Motor 5 Reglas — G_min Bybit POR SANTO (archivo sync) + piso + default
# Default 1.0: pensamiento en mínimo real; override por activo en data/bybit_minimos_orden.json
# Legado 5.0: documentado en CHECKPOINT_PRE_GMIN_VARIABLE — ya no es el peaje único
G_MIN_USD_DEFAULT = float(os.getenv("G_MIN_USD_DEFAULT", "1"))
G_MIN_USD_PISO = float(os.getenv("G_MIN_USD_PISO", "1"))  # nunca por debajo (salvo override explícito archivo)
# Legado estático — solo si el Santo no está en archivo de mínimos
G_MIN_USD_BY_ASSET: dict[str, float] = {}
BERU_FRICCION_SOLDADO_PCT = float(os.getenv("BERU_FRICCION_SOLDADO_PCT", "0.008"))  # 0.8%
# Abismo histórico 1.6% (teatro/fósil) — no gobierna al cazador vivo
BERU_ABISMO_SALIDA_PCT = float(os.getenv("BERU_ABISMO_SALIDA_PCT", "0.016"))
BERU_ADAN_ARMADO_PCT = float(os.getenv("BERU_ADAN_ARMADO_PCT", "0.005"))  # legado
# Cazador vivo: Vacío ±1.1 → Hoz ±1.0 (un peldaño detrás). Relevo 0.9/0.5/0.3 no cambia.
BERU_HOZ_PRODUCTIVA_PCT = float(os.getenv("BERU_HOZ_PRODUCTIVA_PCT", "0.010"))
BERU_LLAMADO_SANGRE_PCT = float(os.getenv("BERU_LLAMADO_SANGRE_PCT", "0.011"))
BERU_CAZADOR_MORDIDA_USD = float(os.getenv("BERU_CAZADOR_MORDIDA_USD", "0"))
BERU_CAZADOR_PASO_PCT = float(os.getenv("BERU_CAZADOR_PASO_PCT", "0.001"))
BERU_CAZADOR_SPAWN_CADA_PCT = float(os.getenv("BERU_CAZADOR_SPAWN_CADA_PCT", "0.003"))  # legado
BERU_CAZADOR_GATILLO_FRACCION = float(os.getenv("BERU_CAZADOR_GATILLO_FRACCION", "0.5"))  # legado
BERU_CAZA_CAPA1_USD = float(os.getenv("BERU_CAZA_CAPA1_USD", "0"))
BERU_CAZA_CAPA1_MAX_USD = float(os.getenv("BERU_CAZA_CAPA1_MAX_USD", "0"))
BERU_NEG_PASO_OZ_PCT = float(os.getenv("BERU_NEG_PASO_OZ_PCT", "0.001"))
BERU_NEG_PASO_RED_PCT = float(os.getenv("BERU_NEG_PASO_RED_PCT", "0.0005"))
BERU_COSECHA_PASO_PCT = float(os.getenv("BERU_COSECHA_PASO_PCT", "0.001"))
# Cirugía Beru 2026-08-12 (Jess → USA): ley · wake · ojos · fantasma. Manos reales OFF.
BERU_WAKE_RESET_0 = False  # fósil: el 0 solo viene del manto Igris
BERU_SIEMBRA_FLOTA = os.getenv("BERU_SIEMBRA_FLOTA", "true").lower() == "true"
BERU_CAPITAN_WAKE = os.getenv("BERU_CAPITAN_WAKE", "NORMAL").upper()  # NORMAL=1.1 · ANSIEDAD=1.2
BERU_MANOS = os.getenv("BERU_MANOS", "false").lower() == "true"  # órdenes spot reales
BERU_HILO_ENABLED = os.getenv("BERU_HILO_ENABLED", "false").lower() == "true"  # hilo en arise; default OFF
# Nivel 2: ojos reales · bitácora · cero place_order. Ritual arise_beru_fantasma.
BERU_MANOS_FANTASMA = os.getenv("BERU_MANOS_FANTASMA", "false").lower() == "true"
BERU_FANTASMA_ACTIVOS = os.getenv("BERU_FANTASMA_ACTIVOS", "ADA,BCH,MNT")
# Flota mixta: estos Santos plantan Hoz real; el resto queda en fantasma.
# Vacío = todos según BERU_MANOS / FANTASMA (ley antigua).
BERU_MANOS_ACTIVOS = os.getenv("BERU_MANOS_ACTIVOS", "")
BERU_MANOS_EXIGIR_TIER = os.getenv("BERU_MANOS_EXIGIR_TIER", "PLENO").upper()
# Nivel 3: manos chiquitas (dormido hasta mandato). Ritual arise_beru_manos_chiquitas.
BERU_ENSAYO_NIVEL3 = os.getenv("BERU_ENSAYO_NIVEL3", "false").lower() == "true"
BERU_ENSAYO_ACTIVOS = os.getenv("BERU_ENSAYO_ACTIVOS", "MNT")
BERU_ENSAYO_MAX_ORDENES = int(float(os.getenv("BERU_ENSAYO_MAX_ORDENES", "1") or 1))
BERU_ENSAYO_MAX_MASA_USD = float(os.getenv("BERU_ENSAYO_MAX_MASA_USD", "60") or 60)
BERU_ENSAYO_SOLO_LONG = os.getenv("BERU_ENSAYO_SOLO_LONG", "true").lower() == "true"
BERU_OJOS_REST_FALLBACK = os.getenv("BERU_OJOS_REST_FALLBACK", "true").lower() == "true"
BERU_OJOS_REST_S = float(os.getenv("BERU_OJOS_REST_S", "10") or 10)
# Si el last spot WS llegó hace menos de esto, la muleta REST calla.
BERU_OJOS_WS_MAX_AGE_S = float(os.getenv("BERU_OJOS_WS_MAX_AGE_S", "5") or 5)
BERU_NEUTRO_MARGEN = os.getenv("BERU_NEUTRO_MARGEN", "true").lower() == "true"
# Ráfaga de seguridad (solo si Bybit escupe la Hoz gorda por ahogo de bóveda)
BERU_RAFAGA_LATENCIA_S = float(os.getenv("BERU_RAFAGA_LATENCIA_S", "0.25") or 0.25)
BERU_RAFAGA_MAX_BOCADOS = int(float(os.getenv("BERU_RAFAGA_MAX_BOCADOS", "24") or 24))
BERU_RAFAGA_FILL_TIMEOUT_S = float(os.getenv("BERU_RAFAGA_FILL_TIMEOUT_S", "2") or 2)
BERU_RAFAGA_COOLDOWN_S = float(os.getenv("BERU_RAFAGA_COOLDOWN_S", "3") or 3)
# Pulso: cuántos Santos hablan a Bybit a la vez. 1 = fila legado. 0 = todos.
BERU_MANOS_PARALELAS = int(float(os.getenv("BERU_MANOS_PARALELAS", "8") or 8))
# Si Bybit escupe 10006, ese Santo espera; los otros no se congelan.
BERU_API_COOLDOWN_S = float(os.getenv("BERU_API_COOLDOWN_S", "0.5") or 0.5)
# Engorde de Hoz en CAZA (por grado). No engorda escudo Igris. Manos siguen OFF.
BERU_ENGORDE_PERMITIDO = os.getenv("BERU_ENGORDE_PERMITIDO", "true").lower() == "true"
BERU_ABORTAR_SOLO_CEGUERA = os.getenv("BERU_ABORTAR_SOLO_CEGUERA", "true").lower() == "true"
BERU_CEGUERA_COMA_S = float(os.getenv("BERU_CEGUERA_COMA_S", "15"))
# Peces / barcos — apalancamiento máx Bybit (promedio inverse+lineal en beru_capital)
# Flota manto viva (Jess sync 2026-07-18): Inverse ∩ Linear USDT — ver diccionario_beru_flota_manto.json
ACTIVOS_BERU_FLOTA = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "LTC", "AAVE", "HYPE",
    "MNT", "APT", "AVAX", "BCH", "ETC", "LINK", "NEAR", "OP", "SUI", "UNI",
    "XLM", "FIL",
]
MANTO_LEVERAGE_DEFAULT = float(os.getenv("MANTO_LEVERAGE_DEFAULT", "25"))
MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET: dict[str, float] = {
    "AAVE": 75, "ADA": 75, "APT": 50, "ARB": 50, "ATOM": 75,
    "AVAX": 50, "BCH": 50, "BTC": 100, "DOGE": 75, "DOT": 50,
    "ETC": 50, "ETH": 100, "FIL": 25, "HYPE": 75, "LINK": 50,
    "LTC": 50, "MATIC": 75, "MNT": 25, "NEAR": 50, "OP": 50,
    "SOL": 100, "SUI": 50, "UNI": 50, "WIF": 50, "XLM": 50,
    "XRP": 100,
}
MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET: dict[str, float] = {
    "AAVE": 20, "ADA": 50, "APT": 20, "AVAX": 20, "BCH": 20,
    "BTC": 100, "DOGE": 25, "DOT": 50, "ETC": 20, "ETH": 100,
    "FIL": 20, "HYPE": 20, "LINK": 20, "LTC": 50, "MNT": 50,
    "NEAR": 20, "OP": 20, "SOL": 50, "SUI": 20, "UNI": 20,
    "WIF": 20, "XLM": 20, "XRP": 50,
}
# Densidad útil: mayor leverage cuyo tier de riesgo soporta una pierna
# Mariscal de $5k con 20% de holgura. Inverso convierte límite base×last.
# Snapshot Bybit vivo 2026-08-15.
# El techo de catálogo se conserva arriba; Igris y el pase usan este mapa.
MANTO_RISK_HEADROOM_PCT = float(os.getenv("MANTO_RISK_HEADROOM_PCT", "0.80"))
MANTO_LEVERAGE_LINEAR_UTIL_BY_ASSET: dict[str, float] = {
    "AAVE": 75, "ADA": 75, "APT": 50, "AVAX": 50, "BCH": 50,
    "BTC": 100, "DOGE": 75, "DOT": 50, "ETC": 50, "ETH": 100,
    "FIL": 25, "HYPE": 50, "LINK": 50,
    "LTC": 50, "MNT": 25, "NEAR": 50, "OP": 50, "SOL": 100,
    "SUI": 50, "UNI": 50, "XLM": 50, "XRP": 100,
}
MANTO_LEVERAGE_INVERSE_UTIL_BY_ASSET: dict[str, float] = {
    "AAVE": 20, "ADA": 50, "APT": 4, "AVAX": 20, "BCH": 20,
    "BTC": 100, "DOGE": 25, "DOT": 50, "ETC": 20, "ETH": 100,
    "FIL": 20, "HYPE": 20, "LINK": 20,
    "LTC": 50, "MNT": 40, "NEAR": 20, "OP": 20, "SOL": 50,
    "SUI": 20, "UNI": 20, "XLM": 20, "XRP": 50,
}

# Trinidad + USDC spot + USDE (core/trinidad.py)
ACTIVOS_TRINIDAD: list[str] = []
ACTIVOS_USDC_SPOT: list[str] = []
USDE_PARES: list[dict] = []
USD1_PARES: list[dict] = []
MNT_SPOT_PARES: list[dict] = []
SPOT_ALL_PARES: list[dict] = []
FRENTES_TRINIDAD: list[str] = []
FRENTES_USDC_SPOT: list[str] = []
FRENTES_USDE: list[str] = []
FRENTES_USD1: list[str] = []
FRENTES_MNT_SPOT: list[str] = []
FRENTES_SPOT_ALL: list[str] = []
LINEAR_PERP_PARES: list[dict] = []
INVERSE_PERP_PARES: list[dict] = []
LINEAR_FUTURES_PARES: list[dict] = []
INVERSE_FUTURES_PARES: list[dict] = []
FRENTES_LINEAR_PERP: list[str] = []
FRENTES_INVERSE_PERP: list[str] = []
FRENTES_LINEAR_FUTURES: list[str] = []
FRENTES_INVERSE_FUTURES: list[str] = []
FRENTES_TANK: list[str] = []

# Bridge: pares por conexión WS (evitar saturar un solo socket)
SPOT_WS_SHARD_SIZE = 150
DERIV_WS_SHARD_SIZE = 150

# Sentidos extra Tank (REST complementario — spread producto, alpha, convert)
SENTIDOS_SPREAD_POLL_S = 60
SENTIDOS_ALPHA_POLL_S = 120
SENTIDOS_CONVERT_POLL_S = 90
MATRIZ_SPREADS_TOP_N = int(os.getenv("MATRIZ_SPREADS_TOP_N", "50"))
MATRIZ_SPREADS_CALC_S = 2

# Fase 1 — desvío perp vs index Bybit
DESVIO_INDICE_TOP_N = 40
DESVIO_ALERTA_PCT = 0.5

# Fase 2 — Binance referencia (segundo mar)
BINANCE_REF_ENABLED = os.getenv("BINANCE_REF_ENABLED", "True").lower() == "true"
BINANCE_REF_MAX_SYMBOLS = int(os.getenv("BINANCE_REF_MAX_SYMBOLS", "80"))
REF_STALE_S = float(os.getenv("REF_STALE_S", "30"))
PANORAMA_TOP_N = 30
ACTIVOS_HUERFANOS: list[str] = []
BASES_PANORAMA: list[str] = []

# Kaiser — vocero interno (interpreta Tank → alertas / cola)
KAISER_INTERVAL_S = float(os.getenv("KAISER_INTERVAL_S", "3"))
KAISER_ALERTA_COOLDOWN_S = float(os.getenv("KAISER_ALERTA_COOLDOWN_S", "120"))
KAISER_MATRIZ_UMBRAL_PCT = float(os.getenv("KAISER_MATRIZ_UMBRAL_PCT", "0.25"))
KAISER_FUNDING_UMBRAL = float(os.getenv("KAISER_FUNDING_UMBRAL", "0.0005"))
KAISER_DESVIO_CRIT_PCT = float(os.getenv("KAISER_DESVIO_CRIT_PCT", "1.0"))
KAISER_MAX_ALERTAS = int(os.getenv("KAISER_MAX_ALERTAS", "50"))
KAISER_COLA_TOP_N = int(os.getenv("KAISER_COLA_TOP_N", "20"))

# Perfiles multietiqueta + metaverso
KAISER_SAMPLE_INTERVAL_S = float(os.getenv("KAISER_SAMPLE_INTERVAL_S", "60"))
KAISER_PROFILE_RECALC_S = float(os.getenv("KAISER_PROFILE_RECALC_S", "120"))
KAISER_SAMPLE_MAX_DAYS = int(os.getenv("KAISER_SAMPLE_MAX_DAYS", "400"))
KAISER_SAMPLE_MAX_LINES = int(os.getenv("KAISER_SAMPLE_MAX_LINES", "25000"))
KAISER_SAMPLE_HUERFANAS_CAP = int(os.getenv("KAISER_SAMPLE_HUERFANAS_CAP", "60"))
KAISER_EVENT_UMBRAL_PCT = float(os.getenv("KAISER_EVENT_UMBRAL_PCT", "0.5"))
KAISER_REVERSION_WINDOW_S = float(os.getenv("KAISER_REVERSION_WINDOW_S", "900"))
KAISER_PERFIL_MIN_MUESTRAS = int(os.getenv("KAISER_PERFIL_MIN_MUESTRAS", "20"))
KAISER_PERFIL_MAX_BASES = int(os.getenv("KAISER_PERFIL_MAX_BASES", "40"))
KAISER_SPOT_ALL_CAP = int(os.getenv("KAISER_SPOT_ALL_CAP", "60"))
KAISER_PERFIL_HUERFANAS_CAP = int(os.getenv("KAISER_PERFIL_HUERFANAS_CAP", "30"))
KAISER_SLIPPAGE_PERP_PCT = float(os.getenv("KAISER_SLIPPAGE_PERP_PCT", "0.04"))
KAISER_SLIPPAGE_SPOT_PERP_PCT = float(os.getenv("KAISER_SLIPPAGE_SPOT_PERP_PCT", "0.08"))
KAISER_SLIPPAGE_STABLE_PCT = float(os.getenv("KAISER_SLIPPAGE_STABLE_PCT", "0.03"))
KAISER_SLIPPAGE_SPOT_PCT = float(os.getenv("KAISER_SLIPPAGE_SPOT_PCT", "0.05"))
KAISER_RUTAS_TOP_N = int(os.getenv("KAISER_RUTAS_TOP_N", "5"))
KAISER_BACKFILL_ON_START = os.getenv("KAISER_BACKFILL_ON_START", "True").lower() == "true"
KAISER_BACKFILL_DIAS = int(os.getenv("KAISER_BACKFILL_DIAS", "365"))
KAISER_BACKFILL_MAX_BASES = int(os.getenv("KAISER_BACKFILL_MAX_BASES", "12"))
# Sesgo estructural vs índice (3.8.P5) — digest sesgo_estructural; sin manos
KAISER_SESGO_INDEX_ACTIVO = os.getenv("KAISER_SESGO_INDEX_ACTIVO", "true").lower() == "true"
KAISER_SESGO_MIN_MUESTRAS = int(os.getenv("KAISER_SESGO_MIN_MUESTRAS", "15"))
KAISER_SESGO_CLIMA_EPS_PCT = float(os.getenv("KAISER_SESGO_CLIMA_EPS_PCT", "0.05"))

# Memoria de barcos — diario horario Tank → data/kaiser/memoria/{BASE}.jsonl
KAISER_MEMORIA_INTERVAL_S = float(os.getenv("KAISER_MEMORIA_INTERVAL_S", "3600"))
KAISER_MEMORIA_MAX_LINES = int(os.getenv("KAISER_MEMORIA_MAX_LINES", "2160"))
KAISER_MEMORIA_MAX_DAYS = int(os.getenv("KAISER_MEMORIA_MAX_DAYS", "120"))
KAISER_MEMORIA_MAX_BASES = int(os.getenv("KAISER_MEMORIA_MAX_BASES", "40"))
KAISER_MEMORIA_DELTA_UMBRAL_PCT = float(os.getenv("KAISER_MEMORIA_DELTA_UMBRAL_PCT", "0.35"))

# Ancla de Realidad — slippage desde orderbook (Capa 1 liquidez)
ANCLA_MIN_NOTIONAL_USD = float(os.getenv("ANCLA_MIN_NOTIONAL_USD", "10"))
ANCLA_PASO_BUSQUEDA_USD = float(os.getenv("ANCLA_PASO_BUSQUEDA_USD", "25"))
ANCLA_LIBRO_MAX_NIVELES = int(os.getenv("ANCLA_LIBRO_MAX_NIVELES", "50"))
ANCLA_SEGURA_FRACCION_MAX = float(os.getenv("ANCLA_SEGURA_FRACCION_MAX", "0.30"))
ANCLA_SEGURA_SLIPPAGE_PCT = float(os.getenv("ANCLA_SEGURA_SLIPPAGE_PCT", "0.05"))
ANCLA_FEE_SPOT_PCT = float(os.getenv("ANCLA_FEE_SPOT_PCT", "0.10"))
ANCLA_FEE_LINEAR_TAKER_PCT = float(os.getenv("ANCLA_FEE_LINEAR_TAKER_PCT", "0.055"))
ANCLA_FEE_INVERSE_TAKER_PCT = float(os.getenv("ANCLA_FEE_INVERSE_TAKER_PCT", "0.055"))
ANCLA_TOP_N = int(os.getenv("ANCLA_TOP_N", "15"))
# Regalo neto mínimo vs fees: 1.0 = ganamos al menos lo que pagamos en fees
ANCLA_NETO_MIN_VS_FEES = float(os.getenv("ANCLA_NETO_MIN_VS_FEES", "1.0"))
# Umbral spread para escanear (0 = cualquier spread positivo con libro)
ANCLA_UMBRAL_SPREAD_PCT = float(os.getenv("ANCLA_UMBRAL_SPREAD_PCT", "0"))

# Pipeline Kaiser → Greed (Tokio: ~100–500 ms total)
PIPELINE_KAISER_ALERT_MS = float(os.getenv("PIPELINE_KAISER_ALERT_MS", "5"))
PIPELINE_GREED_DECIDE_MS = float(os.getenv("PIPELINE_GREED_DECIDE_MS", "15"))
PIPELINE_EXECUTE_MS = float(os.getenv("PIPELINE_EXECUTE_MS", "50"))
PIPELINE_SPREAD_HIST_LEN = int(os.getenv("PIPELINE_SPREAD_HIST_LEN", "12"))
PIPELINE_SPREAD_MIN_RATIO = float(os.getenv("PIPELINE_SPREAD_MIN_RATIO", "0.65"))
PIPELINE_TTL_FACTOR = float(os.getenv("PIPELINE_TTL_FACTOR", "3.0"))
PIPELINE_TTL_MIN_S = float(os.getenv("PIPELINE_TTL_MIN_S", "0.5"))
PIPELINE_MAX_MS = float(os.getenv("PIPELINE_MAX_MS", "500"))

# Mínimo orden Bybit por frente (Trinidad → MIN_ORDER_USD_BY_FRENTE)
MIN_ORDER_USD_DEFAULT = float(os.getenv("MIN_ORDER_USD_DEFAULT", "5"))
MIN_ORDER_USD_BY_FRENTE: dict[str, float] = {}

# Convert quotes (muestra trinidad + pentiverso)
CONVERT_QUOTE_POLL_S = 120
CONVERT_QUOTE_USDT_MONTO = "100"


def _mares_de_activo(asset: str):
    return [
        f"{asset}USDT_LINEAL",
        f"{asset}USDC_LINEAL",
        f"{asset}USD_INVERSE",
        f"{asset}USDT_SPOT",
        f"{asset}USDC_SPOT",
    ]


MARES_PENTIVERSO_LTC = _mares_de_activo("LTC")
MARES_PENTIVERSO_BTC = _mares_de_activo("BTC")
MARES_PENTIVERSO_ALL = MARES_PENTIVERSO_LTC + MARES_PENTIVERSO_BTC
# Pentiverso (10 mares) + frentes casa Beru para ctx_map / resonancia
FRENTES_RESONANCIA_TANK = list(dict.fromkeys(MARES_PENTIVERSO_ALL + FRENTES_BERU_VIGILANCIA))

FRENTES_CASA = [f"{TICKER_BASE}USDT_SPOT", f"{TICKER_BASE}USDC_SPOT"]
FRENTES_MANTO = [f"{TICKER_BASE}USDT_LINEAL", f"{TICKER_BASE}USD_INVERSE"]
FRENTES_MANTO_ALL = [
    f"{a}USDT_LINEAL" for a in ACTIVOS_PENTIVERSO
] + [f"{a}USD_INVERSE" for a in ACTIVOS_PENTIVERSO]
FRENTES_CASA_ALL = [
    f"{a}USDT_SPOT" for a in ACTIVOS_PENTIVERSO
] + [f"{a}USDC_SPOT" for a in ACTIVOS_PENTIVERSO]
FRENTES_ACTIVOS = list(dict.fromkeys(MARES_PENTIVERSO_ALL))

GREED_SQUAD_MASA_FRACCION = 0.5
GREED_SQUAD_COOLDOWN_S = 10.0

# Greed ← Kaiser (doctrina §6–§8)
GREED_KAISER_ENABLED = os.getenv("GREED_KAISER_ENABLED", "true").lower() == "true"
GREED_MULTICRUCE_ENABLED = os.getenv("GREED_MULTICRUCE_ENABLED", "true").lower() == "true"
GREED_MULTICRUCE_UMBRAL_PCT = float(os.getenv("GREED_MULTICRUCE_UMBRAL_PCT", "0.15"))
GREED_MULTICRUCE_TOP_N = int(os.getenv("GREED_MULTICRUCE_TOP_N", "20"))
GREED_MULTICRUCE_VIA_QUOTES = tuple(
    q.strip().upper()
    for q in os.getenv("GREED_MULTICRUCE_VIA_QUOTES", "USDC,MNT,EUR").split(",")
    if q.strip()
)
GREED_LEGACY_SQUAD_ENABLED = os.getenv("GREED_LEGACY_SQUAD_ENABLED", "false").lower() == "true"
# 0 = yield inmediato (doctrina: sin sleeps pasivos; solo cede el event loop)
GREED_LOOP_INTERVAL_S = float(os.getenv("GREED_LOOP_INTERVAL_S", "0"))
GREED_DISPARO_COOLDOWN_S = float(os.getenv("GREED_DISPARO_COOLDOWN_S", "1.0"))
GREED_REINTENTO_COOLDOWN_S = float(os.getenv("GREED_REINTENTO_COOLDOWN_S", "2.0"))
GREED_MAX_INTENTOS_POR_CICLO = int(os.getenv("GREED_MAX_INTENTOS_POR_CICLO", "1"))
GREED_PLANES_TOP_N = int(os.getenv("GREED_PLANES_TOP_N", "3"))
GREED_RIESGO_MAX_PCT_CUENTA = float(os.getenv("GREED_RIESGO_MAX_PCT_CUENTA", "0.01"))
GREED_FRACCION_MIN = float(os.getenv("GREED_FRACCION_MIN", "0.05"))
GREED_FRACCION_MAX = float(os.getenv("GREED_FRACCION_MAX", "0.85"))
GREED_HUERFANA_SIN_PERFIL_FRACCION_MAX = float(os.getenv("GREED_HUERFANA_SIN_PERFIL_FRACCION_MAX", "0.30"))
GREED_CALOR_MODULO = float(os.getenv("GREED_CALOR_MODULO", "0.5"))
GREED_LEVERAGE_DEFAULT = float(os.getenv("GREED_LEVERAGE_DEFAULT", "10"))
GREED_LEVERAGE_SPOT = float(os.getenv("GREED_LEVERAGE_SPOT", "1"))


def _build_greed_leverage_by_frente() -> dict[str, float]:
    out: dict[str, float] = {}
    for a, lev in MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET.items():
        out[f"{a}USDT_LINEAL"] = float(lev)
        out[f"{a}USDC_LINEAL"] = float(lev)
    for a, lev in MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET.items():
        out[f"{a}USD_INVERSE"] = float(lev)
    return out


GREED_LEVERAGE_BY_FRENTE: dict[str, float] = _build_greed_leverage_by_frente()
GREED_PESOS_INDICADORES = {
    "calor": float(os.getenv("GREED_PESO_CALOR", "0.25")),
    "tags": float(os.getenv("GREED_PESO_TAGS", "0.25")),
    "plazos": float(os.getenv("GREED_PESO_PLAZOS", "0.20")),
    "ruta": float(os.getenv("GREED_PESO_RUTA", "0.15")),
    "clima": float(os.getenv("GREED_PESO_CLIMA", "0.10")),
    "manto": float(os.getenv("GREED_PESO_MANTO", "0.05")),
}

# VIP / Mega VIP — micro-órdenes al min_order, escalado por neto metaverso
GREED_VIP_ENABLED = os.getenv("GREED_VIP_ENABLED", "true").lower() == "true"
GREED_VIP_NETO_MIN_PCT = float(os.getenv("GREED_VIP_NETO_MIN_PCT", "0.5"))
GREED_MEGA_VIP_NETO_MIN_PCT = float(os.getenv("GREED_MEGA_VIP_NETO_MIN_PCT", "1.0"))
GREED_VIP_NETO_CONTINUAR_PCT = float(os.getenv("GREED_VIP_NETO_CONTINUAR_PCT", "0.5"))
GREED_MEGA_VIP_RIESGO_MAX_PCT = float(os.getenv("GREED_MEGA_VIP_RIESGO_MAX_PCT", "0.05"))
GREED_VIP_SONDAS_MIN = int(os.getenv("GREED_VIP_SONDAS_MIN", "3"))
GREED_VIP_MICROS_POR_CICLO = int(os.getenv("GREED_VIP_MICROS_POR_CICLO", "1"))

BOOTSTRAP_MANTO_FRACCION = float(os.getenv("BOOTSTRAP_MANTO_FRACCION", "0"))  # 0 = sin tope 25%; sizing vía beru_capital
# Engorde: pasos duales L/S (no tragar toda masa_autorizada de un lado)
ENGORDE_PASO_FRACCION = float(os.getenv("ENGORDE_PASO_FRACCION", "0.05"))
ENGORDE_PASO_MIN = float(os.getenv("ENGORDE_PASO_MIN", "0.1"))
ENGORDE_BLOQUEADO_LOG_S = float(os.getenv("ENGORDE_BLOQUEADO_LOG_S", "60"))
ENGORDE_FAIL_COOLDOWN_S = float(os.getenv("ENGORDE_FAIL_COOLDOWN_S", "30"))

# Igris — despliegue paciente §E (Ask/Bid, fees, urgencia invertida, mordida inteligente)
IGRIS_URGENCIA_TAU_HORAS = float(os.getenv("IGRIS_URGENCIA_TAU_HORAS", "8"))  # fallback sin Kaiser
IGRIS_URGENCIA_TAU_MIN_HORAS = float(os.getenv("IGRIS_URGENCIA_TAU_MIN_HORAS", "1"))  # baja frecuencia
IGRIS_URGENCIA_TAU_MAX_HORAS = float(os.getenv("IGRIS_URGENCIA_TAU_MAX_HORAS", "24"))  # alta frecuencia
IGRIS_URGENCIA_HOLGURA_MAX_PCT = float(os.getenv("IGRIS_URGENCIA_HOLGURA_MAX_PCT", "0.05"))
# Frecuencia manto: 4 umbrales × plazos (corto 50% · mediano 40% · anual 10%)
MANTO_FREQ_ACTIVA = os.getenv("MANTO_FREQ_ACTIVA", "true").lower() in ("1", "true", "yes", "on")
MANTO_FREQ_PESO_CORTO = float(os.getenv("MANTO_FREQ_PESO_CORTO", "0.50"))
MANTO_FREQ_PESO_MEDIANO = float(os.getenv("MANTO_FREQ_PESO_MEDIANO", "0.40"))
MANTO_FREQ_PESO_LARGO = float(os.getenv("MANTO_FREQ_PESO_LARGO", "0.10"))
MANTO_FREQ_TABLAS_EPS_PCT = float(os.getenv("MANTO_FREQ_TABLAS_EPS_PCT", "0.01"))
MANTO_FREQ_MIN_MUESTRAS = int(os.getenv("MANTO_FREQ_MIN_MUESTRAS", "20"))
MANTO_FREQ_SCORE_TACTICO = float(os.getenv("MANTO_FREQ_SCORE_TACTICO", "0.25"))
MANTO_FREQ_SCORE_FORZADA = float(os.getenv("MANTO_FREQ_SCORE_FORZADA", "0.08"))
MANTO_FREQ_MORDIDA_USD = float(os.getenv("MANTO_FREQ_MORDIDA_USD", "5"))
MANTO_FREQ_META_DEFAULT_USD = float(os.getenv("MANTO_FREQ_META_DEFAULT_USD", "100"))
# Contar oportunidad / puerta manto vs cero estructural (no gap eterno)
MANTO_CERO_ESTRUCTURAL = os.getenv("MANTO_CERO_ESTRUCTURAL", "true").lower() in ("1", "true", "yes", "on")
IGRIS_ESPERA_LOG_S = float(os.getenv("IGRIS_ESPERA_LOG_S", "60"))
IGRIS_ESPERA_COOLDOWN_S = float(os.getenv("IGRIS_ESPERA_COOLDOWN_S", "5"))
# Ritmo entre duales OK de engorde/bootstrap (mismo Santo): default 15s.
# No mandar otro par Market hasta confirmar fills L+S del dual anterior.
IGRIS_ENGORDE_RITMO_S = float(os.getenv("IGRIS_ENGORDE_RITMO_S", "15"))
# Una reconciliación global L/S al inicio de la ronda alimenta todas las manos.
# Evita 2 consultas REST por Santo y mantiene el medidor fresco durante el lote.
IGRIS_MEDIDOR_LOTE_FRESCO_S = float(
    os.getenv("IGRIS_MEDIDOR_LOTE_FRESCO_S", "3")
)
# Disparo dual §E: timeout fill inicial + salvavidas
IGRIS_DUAL_FILL_TIMEOUT_S = float(os.getenv("IGRIS_DUAL_FILL_TIMEOUT_S", "20"))
# Legado: si true, empata USD al toque (cirugía: OFF — usar siguiente bocado)
IGRIS_DUAL_SALVAVIDAS_EMPATE = os.getenv(
    "IGRIS_DUAL_SALVAVIDAS_EMPATE", "false"
).lower() == "true"
# Solo si falta una pierna tras el dual
IGRIS_DUAL_SALVAVIDAS_EMERGENCIA = os.getenv(
    "IGRIS_DUAL_SALVAVIDAS_EMERGENCIA", "true"
).lower() == "true"
# Compat: OR de emergencia (empate ya no entra por defecto)
IGRIS_DUAL_SALVAVIDAS_MARKET = os.getenv(
    "IGRIS_DUAL_SALVAVIDAS_MARKET",
    "true" if IGRIS_DUAL_SALVAVIDAS_EMERGENCIA else "false",
).lower() == "true"
# Freno de mano de prueba: 0 = sin tope; N = Igris para tras N duales L+S llenos
IGRIS_MAX_DUALES_SESION = int(float(os.getenv("IGRIS_MAX_DUALES_SESION", "0") or 0))
# Escalera permanente: 0=ojos, 1=1 dual, 2=3, 3=10, 4=autónomo.
IGRIS_DESPLIEGUE_NIVEL = int(float(os.getenv("IGRIS_DESPLIEGUE_NIVEL", "0") or 0))
IGRIS_BOCADO_ASIMETRICO = os.getenv("IGRIS_BOCADO_ASIMETRICO", "true").lower() == "true"
IGRIS_BOCADO_CORR_MIN_USD = float(os.getenv("IGRIS_BOCADO_CORR_MIN_USD", "1.0") or 1.0)
# Máxima diferencia intencional L-S como fracción del bocado L+S.
IGRIS_BOCADO_CORR_MAX_TOTAL_PCT = float(
    os.getenv("IGRIS_BOCADO_CORR_MAX_TOTAL_PCT", "0.50") or 0.50
)
# Tusk: vigilia lenta; durante misión Igris mide el manto con mayor frecuencia.
TUSK_RECONCILIACION_DORMIDO_S = float(
    os.getenv("TUSK_RECONCILIACION_DORMIDO_S", "60") or 60
)
TUSK_RECONCILIACION_ASALTO_S = float(
    os.getenv("TUSK_RECONCILIACION_ASALTO_S", "20") or 20
)
# Sueño + misiones (mega-cirugía 2026-08-12)
IGRIS_SUENO_MISION = os.getenv("IGRIS_SUENO_MISION", "true").lower() == "true"
IGRIS_SARGENTO_AUTO = os.getenv("IGRIS_SARGENTO_AUTO", "true").lower() == "true"
IGRIS_SUENO_POLL_S = float(os.getenv("IGRIS_SUENO_POLL_S", "2") or 2)
# Marcha principal: una ronda recorre todos los Santos abiertos antes de repetir.
IGRIS_LATIDO_LOTE = os.getenv("IGRIS_LATIDO_LOTE", "true").lower() == "true"
# Manos paralelas: cuántos duales (Santos distintos) pueden volar a la vez.
# 1 = secuencial (legado). 0 = todos los elegibles del latido.
IGRIS_MANOS_PARALELAS = int(float(os.getenv("IGRIS_MANOS_PARALELAS", "8") or 8))
# Concentrar las manos en Santos cercanos a cerrar, en vez de repartir masa
# entre todo el lote incompleto. Los huérfanos sin espejo conservan prioridad.
IGRIS_PRIORIZAR_CIERRE = os.getenv("IGRIS_PRIORIZAR_CIERRE", "true").lower() == "true"
IGRIS_FOCO_CIERRE_SANTOS = int(
    float(os.getenv("IGRIS_FOCO_CIERRE_SANTOS", "3") or 3)
)
IGRIS_SOLO_ASALTO = os.getenv("IGRIS_SOLO_ASALTO", "true").lower() == "true"
IGRIS_REDUCIR_REQUIERE_CONFIRMA = os.getenv(
    "IGRIS_REDUCIR_REQUIERE_CONFIRMA", "true"
).lower() == "true"
IGRIS_REDUCIR_CONFIRMADO = os.getenv("IGRIS_REDUCIR_CONFIRMADO", "false").lower() == "true"
# Visión reducida (duda V1 — no castrar; sin precio usable no dispara)
IGRIS_VISION_MODO = os.getenv("IGRIS_VISION_MODO", "last_price").strip().lower()
IGRIS_VISION_LIBRO_NIVELES = int(os.getenv("IGRIS_VISION_LIBRO_NIVELES", "5") or 5)
# §A no pilotéa engorde (congelado)
IGRIS_OXIGENO_PILOTO = os.getenv("IGRIS_OXIGENO_PILOTO", "false").lower() == "true"
# Bóveda MNT: quote preferido documentado (migración campo = duda V6)
IGRIS_BOVEDA_SHORT_QUOTE = os.getenv("IGRIS_BOVEDA_SHORT_QUOTE", "USDC").strip().upper()
# Ley de la Masa: |USD_L − USD_S| / ref > este techo → disparo dual prohibido
IGRIS_MASA_ASIMETRIA_MAX_PCT = float(os.getenv("IGRIS_MASA_ASIMETRIA_MAX_PCT", "0.05"))
# Asalto (no cacería): asimetría más holgada — peaje de espejo aceptado
IGRIS_MASA_ASIMETRIA_ASALTO_PCT = float(
    os.getenv("IGRIS_MASA_ASIMETRIA_ASALTO_PCT", "0.12") or 0.12
)
# Asalto: si el polvo de meta < mínimo del Santo, igual planta 1× mínimo (puede pasarse)
IGRIS_ASALTO_OVERSHOOT_META = os.getenv("IGRIS_ASALTO_OVERSHOOT_META", "true").lower() == "true"
# Monarca 2026-08-09 noche: engorde no espera ojos perfectos / ventana perfecta
IGRIS_VENTANA_NO_BLOQUEA_ENGORDE = os.getenv(
    "IGRIS_VENTANA_NO_BLOQUEA_ENGORDE", "true"
).lower() == "true"
IGRIS_ASALTO_SIN_TANK_ROJO = os.getenv(
    "IGRIS_ASALTO_SIN_TANK_ROJO", "true"
).lower() == "true"
IGRIS_ASALTO_PUERTA_SIN_OJOS = os.getenv(
    "IGRIS_ASALTO_PUERTA_SIN_OJOS", "true"
).lower() == "true"
# Si la mordida pide más O₂ del libre, encoger al techo auth (reponer Santos chicos)
IGRIS_RESERVA_AJUSTAR_A_AUTH = os.getenv(
    "IGRIS_RESERVA_AJUSTAR_A_AUTH", "true"
).lower() == "true"
IGRIS_RESERVA_AUTH_FRAC = float(os.getenv("IGRIS_RESERVA_AUTH_FRAC", "0.92") or 0.92)
# Densidad máxima siempre (inv+lin). Avisar si Bybit no deja el techo de catálogo.
IGRIS_FORCE_MAX_LEVERAGE = os.getenv("IGRIS_FORCE_MAX_LEVERAGE", "true").lower() == "true"
IGRIS_LEVERAGE_FORCE_COOLDOWN_S = float(os.getenv("IGRIS_LEVERAGE_FORCE_COOLDOWN_S", "300") or 300)
IGRIS_LEVERAGE_FORCE_GAP_S = float(os.getenv("IGRIS_LEVERAGE_FORCE_GAP_S", "0.15") or 0.15)
# Escalera de precios — micro-bocados Limit a distintos niveles (Igris/Greed)
ESCALERA_PRECIOS_ACTIVA = os.getenv("ESCALERA_PRECIOS_ACTIVA", "true").lower() == "true"
ESCALERA_IGRIS_ACTIVA = os.getenv("ESCALERA_IGRIS_ACTIVA", "true").lower() == "true"
ESCALERA_GREED_ACTIVA = os.getenv("ESCALERA_GREED_ACTIVA", "true").lower() == "true"
ESCALERA_MAX_PELDANOS = int(os.getenv("ESCALERA_MAX_PELDANOS", "8"))
ESCALERA_TICK_PCT = float(os.getenv("ESCALERA_TICK_PCT", "0.00015"))
ESCALERA_FILL_TIMEOUT_S = float(os.getenv("ESCALERA_FILL_TIMEOUT_S", "12"))
# Horizonte 95% = colchón de cálculo; rebase táctico permitido (poda posterior)
IGRIS_COLCHON_OXIGENO_PCT = float(os.getenv("IGRIS_COLCHON_OXIGENO_PCT", "5"))

FASE_ACTUAL = "HIERRO"
VERSION = "2.0.0"
SISTEMA_NOMBRE = f"LILIT DE {FASE_ACTUAL} V{VERSION}"

# Igris — gobernador absoluto del manto (doctrina Monarca 2026-07-12)
# Empuja margen hasta el muro 95%; reserva oxígeno 5% (MONARCA_RESERVA_PCT).
RANGO_EXPANSION_MIN = 80.0
RANGO_PISO_IDEAL = 95.0          # bajo esto → Igris sigue engordando
RANGO_OBJETIVO_MARGEN = 95.0     # horizonte operativo = muro (ya no 85–90)
RANGO_LIMPIEZA_MAX = 95.0
MURO_LEY_MARCIAL = 95.0          # ≥95%: fase oxígeno bajo (aviso); poda OFF por default
# Monarca 2026-08-09: sin poda/espejos automáticos (rompió dual SOL). Solo con true explícito.
IGRIS_PODA_AUTO = os.getenv("IGRIS_PODA_AUTO", "false").lower() == "true"
IGRIS_YIELD_EN_ZONA_IDEAL = os.getenv("IGRIS_YIELD_EN_ZONA_IDEAL", "false").lower() == "true"
# Igris event-driven: Kaiser despierta al escudo (no escaneo agresivo cada tick)
IGRIS_EVENT_DRIVEN = os.getenv("IGRIS_EVENT_DRIVEN", "false").lower() == "true"
IGRIS_BOOTSTRAP_ON_START = os.getenv("IGRIS_BOOTSTRAP_ON_START", "true").lower() == "true"
IGRIS_EVENT_HEARTBEAT_S = float(os.getenv("IGRIS_EVENT_HEARTBEAT_S", "300"))

# Arena Igris aislado — scripts/arena_igris_aislado.py
ARENA_IGRIS_ACTIVA = os.getenv("ARENA_IGRIS_ACTIVA", "false").lower() == "true"
ARENA_IGRIS_EQUITY_USD = float(os.getenv("ARENA_IGRIS_EQUITY_USD", "500"))
ARENA_IGRIS_UMBRAL_PCT = float(os.getenv("ARENA_IGRIS_UMBRAL_PCT", "0.01"))
ARENA_IGRIS_MORDIDA_USD = float(os.getenv("ARENA_IGRIS_MORDIDA_USD", "5"))
ARENA_IGRIS_FILLS_VIRTUALES = os.getenv("ARENA_IGRIS_FILLS_VIRTUALES", "true").lower() == "true"
ARENA_IGRIS_SIN_RANGOS = os.getenv("ARENA_IGRIS_SIN_RANGOS", "true").lower() == "true"
ARENA_IGRIS_SIN_PACIENCIA = os.getenv("ARENA_IGRIS_SIN_PACIENCIA", "true").lower() == "true"
ARENA_IGRIS_ACTIVOS = os.getenv("ARENA_IGRIS_ACTIVOS", "flota")
ARENA_IGRIS_SEGUNDOS_OJOS = float(os.getenv("ARENA_IGRIS_SEGUNDOS_OJOS", "120"))
ARENA_IGRIS_SIN_BANDA_DELTA = os.getenv("ARENA_IGRIS_SIN_BANDA_DELTA", "true").lower() == "true"
ARENA_IGRIS_TUSK_LIMPIO_POR_ACTIVO = os.getenv("ARENA_IGRIS_TUSK_LIMPIO_POR_ACTIVO", "true").lower() == "true"
ARENA_IGRIS_REQUIRE_KAISER = os.getenv("ARENA_IGRIS_REQUIRE_KAISER", "false").lower() == "true"
KAISER_OPORTUNIDAD_MANTO_UMBRAL_PCT = float(
    os.getenv("KAISER_OPORTUNIDAD_MANTO_UMBRAL_PCT", "0")
)  # prod: piso extra; 0 = solo fees break-even Ask/Bid

# Live Igris testnet — scripts/igris_live_testnet.py (checklist 3.10.7b)
LIVE_IGRIS_TESTNET = os.getenv("LIVE_IGRIS_TESTNET", "false").lower() == "true"
LIVE_IGRIS_SEGUNDOS_OJOS = float(os.getenv("LIVE_IGRIS_SEGUNDOS_OJOS", "90"))
LIVE_IGRIS_ACTIVOS = os.getenv("LIVE_IGRIS_ACTIVOS", "ETH,BTC,LTC,SOL,OP")
LIVE_IGRIS_MORDIDA_MAX_USD = float(os.getenv("LIVE_IGRIS_MORDIDA_MAX_USD", "12"))
LIVE_IGRIS_REQUIRE_KAISER = os.getenv("LIVE_IGRIS_REQUIRE_KAISER", "false").lower() == "true"
LIVE_IGRIS_SIN_PACIENCIA = os.getenv("LIVE_IGRIS_SIN_PACIENCIA", "false").lower() == "true"

# Live Beru testnet — scripts/beru_live_testnet.py (checklist 3.9.9)
# Ansiedad 1.2% → gatillo ±0.6% · Mariscal PLENO clon 0.1% · CAZA · ~$10
LIVE_BERU_TESTNET = os.getenv("LIVE_BERU_TESTNET", "false").lower() == "true"
LIVE_BERU_SEGUNDOS = float(os.getenv("LIVE_BERU_SEGUNDOS", "3600"))  # 1 h; 0 = Ctrl+C
LIVE_BERU_ACTIVOS = os.getenv("LIVE_BERU_ACTIVOS", "flota")  # flota = 22 barcos USDT
LIVE_BERU_MORDIDA_USD = float(os.getenv("LIVE_BERU_MORDIDA_USD", "20"))
# Ley Monarca: Beru es molino spot-margen (compra y venta). Default ON.
BERU_SPOT_MARGEN_ENABLED = os.getenv("BERU_SPOT_MARGEN_ENABLED", "true").lower() == "true"
BERU_SPOT_MARGEN_LEVERAGE = int(float(os.getenv("BERU_SPOT_MARGEN_LEVERAGE", "10")))
BERU_RAIL_USDT_ONLY = os.getenv("BERU_RAIL_USDT_ONLY", "false").lower() == "true"

GREED_MANTO_EJECUTOR = os.getenv("GREED_MANTO_EJECUTOR", "false").lower() == "true"
GREED_VIP_PERMITIR_EN_LEY_MARCIAL = os.getenv("GREED_VIP_PERMITIR_EN_LEY_MARCIAL", "true").lower() == "true"
GREED_MANTO_TOQUE_COOLDOWN_S = float(os.getenv("GREED_MANTO_TOQUE_COOLDOWN_S", "45"))

# Greed — basis / manto temporal (spot↔perp, lineal↔inverse)
GREED_BASIS_HOLD_ENABLED = os.getenv("GREED_BASIS_HOLD_ENABLED", "true").lower() == "true"
GREED_BASIS_ENTRADA_SPREAD_MIN_PCT = float(os.getenv("GREED_BASIS_ENTRADA_SPREAD_MIN_PCT", "0.20"))
GREED_BASIS_SALIDA_SPREAD_MAX_PCT = float(os.getenv("GREED_BASIS_SALIDA_SPREAD_MAX_PCT", "0.05"))
GREED_BASIS_SALIDA_NETO_MIN_PCT = float(os.getenv("GREED_BASIS_SALIDA_NETO_MIN_PCT", "0.08"))
GREED_BASIS_ABORT_NETO_PCT = float(os.getenv("GREED_BASIS_ABORT_NETO_PCT", "0.02"))
GREED_BASIS_HOLD_MAX_S = float(os.getenv("GREED_BASIS_HOLD_MAX_S", "3600"))
GREED_BASIS_MAX_ABIERTOS = int(os.getenv("GREED_BASIS_MAX_ABIERTOS", "3"))

# Beru — rail stable
BERU_RAIL_FEE_USDT_PCT = float(os.getenv("BERU_RAIL_FEE_USDT_PCT", "0.10"))
BERU_RAIL_FEE_USDC_PCT = float(os.getenv("BERU_RAIL_FEE_USDC_PCT", "0.10"))

# Plan crecimiento Monarca (doctrina 23)
# Plan crecimiento Monarca — doctrina 23 v1 (2026-07-06)
# Colchón doctrinal 5% + extra Monarca (apertura / paranoia) sobre disponible UTA
MONARCA_RESERVA_PCT = float(os.getenv("MONARCA_RESERVA_PCT", "0.05"))
TUSK_RESERVA_MONARCA_EXTRA_PCT = float(os.getenv("TUSK_RESERVA_MONARCA_EXTRA_PCT", "0.0"))
# Tesorería UTA: oxígeno de guerra desde disponible real (MNT hedge visible)
TUSK_TESORERIA_ACTIVA = os.getenv("TUSK_TESORERIA_ACTIVA", "true").lower() == "true"
TUSK_TESORERIA_FETCH_POS = os.getenv("TUSK_TESORERIA_FETCH_POS", "true").lower() == "true"
# Recitar linear+inverse en cada pulso. Ritual Beru lo apaga: Igris hiberna.
TUSK_RECONCILE_LIVE = os.getenv("TUSK_RECONCILE_LIVE", "true").lower() == "true"
# Tesorería: publica caja USDT + lectura legado MNT; MANOS default false
TUSK_BOVEDA_MNT_DOCTRINA = os.getenv("TUSK_BOVEDA_MNT_DOCTRINA", "true").lower() == "true"
TUSK_BOVEDA_MANOS = os.getenv("TUSK_BOVEDA_MANOS", "false").lower() == "true"
TUSK_CAJA_USDT_ACTIVO = os.getenv("TUSK_CAJA_USDT_ACTIVO", "LTC").upper()
TUSK_CAJA_USDT_MAX_PEAJE_PCT = float(
    os.getenv("TUSK_CAJA_USDT_MAX_PEAJE_PCT", "0.75") or 0.75
)
TUSK_BOVEDA_EQUILIBRIO_TOL_PCT = float(os.getenv("TUSK_BOVEDA_EQUILIBRIO_TOL_PCT", "0.03") or 0.03)
# Ritual ojos: scripts/arise_ojos_tusk.py (Tusk+Tank+Kaiser; sin Igris/Greed/Beru)
ARISE_OJOS_TUSK = os.getenv("ARISE_OJOS_TUSK", "false").lower() == "true"
ARISE_OJOS_SEGUNDOS = float(os.getenv("ARISE_OJOS_SEGUNDOS", "0") or 0)
# Ritual 4.0.2: Igris sim — manos reales OFF, fills ilusorios ON
ARISE_IGRIS_SIM = os.getenv("ARISE_IGRIS_SIM", "false").lower() == "true"
ARISE_IGRIS_SIM_SEGUNDOS = float(os.getenv("ARISE_IGRIS_SIM_SEGUNDOS", "0") or 0)
MONARCA_CONCENTRACION_MAX_PCT = float(os.getenv("MONARCA_CONCENTRACION_MAX_PCT", "0.20"))
MONARCA_MARGEN_OBJETIVO_PCT = float(os.getenv("MONARCA_MARGEN_OBJETIVO_PCT", "93.0"))
MONARCA_TIER_AUTO_DIAS = int(os.getenv("MONARCA_TIER_AUTO_DIAS", "3"))
MONARCA_MEGA_VIP_EQUITY_MIN = float(os.getenv("MONARCA_MEGA_VIP_EQUITY_MIN", "100"))
MONARCA_NIVEL_AUTO = os.getenv("MONARCA_NIVEL_AUTO", "true").lower() == "true"
# Canal paralelo Igris: CSV de activos exclusivos (ej. ETH). Vacío = lote del pase.
_IGRIS_EXCL_RAW = os.getenv("IGRIS_ACTIVOS_EXCLUSIVOS", "").strip()
IGRIS_ACTIVOS_EXCLUSIVOS: list[str] = (
    [a.strip().upper() for a in _IGRIS_EXCL_RAW.split(",") if a.strip()]
    if _IGRIS_EXCL_RAW
    else []
)
# Lectura legado: short inverso MNT = sucio (no saco). MNT sí es Santo del ranking.
# No banear del lote. No reconstruir hedge. No contar short inverso como manto.
_IGRIS_BOVEDA = os.getenv(
    "IGRIS_BOVEDA_BASES",
    os.getenv("IGRIS_PROTEGER_BASES", "MNT"),
).strip()
IGRIS_BOVEDA_BASES: list[str] = (
    [a.strip().upper() for a in _IGRIS_BOVEDA.split(",") if a.strip()]
    if _IGRIS_BOVEDA
    else ["MNT"]
)
# Alias legado cleanup / símbolos
IGRIS_PROTEGER_BASES: list[str] = list(IGRIS_BOVEDA_BASES)
_IGRIS_PROT_SYMS = os.getenv("IGRIS_PROTEGER_SYMBOLS", "MNTPERP,MNTUSDC").strip()
IGRIS_PROTEGER_SYMBOLS: list[str] = (
    [a.strip().upper() for a in _IGRIS_PROT_SYMS.split(",") if a.strip()]
    if _IGRIS_PROT_SYMS
    else ["MNTUSD"]
)
# Abrir manto MNT inverso: switch hedge + positionIdx (default ON)
# Mega-cirugía: no reconstruir short bóveda. MNT = Santo del manto.
IGRIS_MNT_HEDGE_OBLIGATORIO = os.getenv("IGRIS_MNT_HEDGE_OBLIGATORIO", "false").lower() == "true"
# True = MNT Santo entra al lote. False = pausa explícita (no es el default).
IGRIS_BOVEDA_EN_LOTE = os.getenv("IGRIS_BOVEDA_EN_LOTE", "true").lower() == "true"
# CSV extra a saltar del lote (además de bóveda si BOVEDA_EN_LOTE=false)
_IGRIS_EXCLUIR = os.getenv("IGRIS_EXCLUIR_BASES", "").strip()
IGRIS_EXCLUIR_BASES: list[str] = (
    [a.strip().upper() for a in _IGRIS_EXCLUIR.split(",") if a.strip()]
    if _IGRIS_EXCLUIR
    else []
)

# Candado pase → Igris (activos por rango). Lives saltan con LIVE_IGRIS_TESTNET / ARENA SIN_RANGOS.
MONARCA_RANK_GATE = os.getenv("MONARCA_RANK_GATE", "true").lower() == "true"
# Director pase: lote/reserva + marcha operativa (asalto | personalizado)
# Legado env tactico/marcha_forzada → normalizar_marcha las mapea a asalto
PASE_DIRECTOR_ACTIVO = os.getenv("PASE_DIRECTOR_ACTIVO", "true").lower() == "true"
MARCHA_DESPLIEGUE = os.getenv("MARCHA_DESPLIEGUE", "asalto").strip().lower()
# Legacy — botín 50/50 retirado; Greed usa colchón 5%
MONARCA_BOTIN_CIMIENTOS_PCT = float(os.getenv("MONARCA_BOTIN_CIMIENTOS_PCT", "1.0"))

DELTA_TOLERANCIA_MAX = 0.05
DELTA_MARGEN_RELAJADO = 70.0
DELTA_MARGEN_PARANOICO = 95.0

# Ventana 48–52 / long-primero (doctrina 21 checkpoint 3.5.8c) — sustituye banda-por-margen como ley L/S
MANTO_VENTANA_4852_ACTIVA = os.getenv("MANTO_VENTANA_4852_ACTIVA", "true").lower() == "true"
MANTO_VENTANA_LONG_MAX = float(os.getenv("MANTO_VENTANA_LONG_MAX", "0.52"))
MANTO_VENTANA_LONG_MIN = float(os.getenv("MANTO_VENTANA_LONG_MIN", "0.48"))
MANTO_VENTANA_LONG_MIN_CORRECCION = float(os.getenv("MANTO_VENTANA_LONG_MIN_CORRECCION", "0.49"))

SLIPPAGE_FACTOR = {
    "LTCUSDT_LINEAL": 0.7,
    "LTCUSDC_LINEAL": 0.7,
    "LTCUSD_INVERSE": 0.5,
    "LTCUSDC_SPOT": 0.8,
    "LTCUSDT_SPOT": 0.8,
    "BTCUSDT_LINEAL": 1.0,
    "BTCUSDC_LINEAL": 1.0,
    "BTCUSD_INVERSE": 0.9,
    "BTCUSDC_SPOT": 0.9,
    "BTCUSDT_SPOT": 1.0,
    "ETHUSDT_LINEAL": 0.9,
    "FILUSDT_LINEAL": 0.25,
    "WIFUSDT_LINEAL": 0.2,
}
SLIPPAGE_FACTOR_DEFAULT = 0.5

UMBRAL_COSECHA_MIN = 0.01
UMBRAL_REGALO_SQUAD = 0.003
TTL_ORDEN_MS = 2000

ESCALON_POTENCIA_BASE = 5.0
FACTOR_MASA_AUTORIZADA = 10.0

# Bridge WS vía VIP/túnel: timeout de handshake y stagger entre shards
BRIDGE_WS_OPEN_TIMEOUT_S = float(os.getenv("BRIDGE_WS_OPEN_TIMEOUT_S", "45") or 45)
# Tras caída WS: no borrar libros si el fallo fue solo handshake (ver core/bridge.py).
BRIDGE_WS_INVALIDAR_ON_DROP = os.getenv("BRIDGE_WS_INVALIDAR_ON_DROP", "true").lower() == "true"
BRIDGE_WS_RECONNECT_S = float(os.getenv("BRIDGE_WS_RECONNECT_S", "5") or 5)
BRIDGE_WS_RECONNECT_MAX_S = float(os.getenv("BRIDGE_WS_RECONNECT_MAX_S", "30") or 30)
BRIDGE_WS_STAGGER_S = float(os.getenv("BRIDGE_WS_STAGGER_S", "0.45") or 0.45)
# Preferir IPv4 en WS (evita handshakes muertos por IPv6 flaky en laps/hogar).
BRIDGE_WS_FORCE_IPV4 = os.getenv("BRIDGE_WS_FORCE_IPV4", "true").lower() == "true"
# env = confiar en HTTP(S)_PROXY / ALL_PROXY. direct = sin proxy (ojos estables en cuartel).
BRIDGE_WS_PROXY = (os.getenv("BRIDGE_WS_PROXY", "direct") or "direct").strip()
# orderbook.50 = muros (RAM/CPU altos). False = solo tickers (ojos estrechos / lap débil).
BRIDGE_WS_SUBSCRIBE_BOOKS = os.getenv("BRIDGE_WS_SUBSCRIBE_BOOKS", "true").lower() == "true"
# Si no vacío: solo esas bases (ETH,LTC,…) — CSV o lista mutada en runtime.
_BRIDGE_WS_BASES_RAW = os.getenv("BRIDGE_WS_BASES", "").strip()
BRIDGE_WS_BASES: list[str] = (
    [b.strip().upper() for b in _BRIDGE_WS_BASES_RAW.split(",") if b.strip()]
    if _BRIDGE_WS_BASES_RAW
    else []
)
# Ritual Beru: Tank/puente ciegos a lineal, inverso y futuros — solo last spot.
BRIDGE_WS_SOLO_SPOT = os.getenv("BRIDGE_WS_SOLO_SPOT", "false").lower() == "true"
# Tratos públicos spot (mecha). En ritual Beru (solo spot) se abre solo.
# Igris no lo usa: el libro se mueve sin trato; Vacío oye last/trato, no mark.
BRIDGE_WS_PUBLIC_TRADES_SPOT = os.getenv(
    "BRIDGE_WS_PUBLIC_TRADES_SPOT", "false"
).lower() == "true"

# Bybit HTTP: recv_window (ms). Skew ~5s del Mac→10002; 60s da colchón.
BYBIT_RECV_WINDOW_MS = int(float(os.getenv("BYBIT_RECV_WINDOW_MS", "60000") or 60000))
# Timeout del client HTTP (pybit default 10). Foto de posiciones de la flota
# cabe; no cortar el hilo a los 8s y dejar la sesión colgada.
BYBIT_HTTP_TIMEOUT_S = int(float(os.getenv("BYBIT_HTTP_TIMEOUT_S", "20") or 20))

# Igris sim / ojos sin muros: puerta §E puede usar ticker si no hay libro.
# true|false|auto — auto = ON si MODO_SIMULACION o ARISE_IGRIS_SIM o books OFF.
_IGRIS_TICKER_PUERTA_RAW = os.getenv("IGRIS_TICKER_PUERTA_SI_SIN_LIBRO", "auto").strip().lower()
IGRIS_TICKER_PUERTA_SI_SIN_LIBRO = _IGRIS_TICKER_PUERTA_RAW  # "auto"|"true"|"false"

# Ojos frescos: libro WS más viejo que esto = ciego (no manos).
IGRIS_LIBRO_STALE_S = float(os.getenv("IGRIS_LIBRO_STALE_S", "12") or 12)
# Muleta REST orderbook si WS stale / divergente.
IGRIS_LIBRO_REST_FALLBACK = os.getenv("IGRIS_LIBRO_REST_FALLBACK", "true").lower() == "true"
IGRIS_LIBRO_REST_COOLDOWN_S = float(os.getenv("IGRIS_LIBRO_REST_COOLDOWN_S", "15") or 15)
# Si mid libro vs ticker divergen más que esto (%) → sospechoso.
# 0.35 era demasiado fino en live Asalto (ruido 0.4–0.7% → sin fill eterno).
IGRIS_LIBRO_DIVERGENCIA_PCT = float(os.getenv("IGRIS_LIBRO_DIVERGENCIA_PCT", "1.0") or 1.0)
# Asalto (peaje aceptado): techo un poco más holgado; personalizado usa el general.
IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT = float(
    os.getenv("IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT", "2.5") or 2.5
)

UMBRAL_VERDE_MS = 400.0
UMBRAL_AMARILLO_MS = 800.0
TOLERANCIA_GLITCH = 0.002
TOLERANCIA_COMA_S = 15.0

import sys
from core import trinidad as _trinidad  # noqa: E402

_trinidad.aplicar_a_config(sys.modules[__name__])
