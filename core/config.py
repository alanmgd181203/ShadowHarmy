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

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
TESTNET = os.getenv("MODO_TESTNET", "True").lower() == "true"
MODO_SIMULACION = os.getenv("MODO_SIMULACION", "True").lower() == "true"
SAFE_MODE = os.getenv("SAFE_MODE", "False").lower() == "true"

# Testeo Igris — Beru y Greed hibernados; solo Igris + Tank + Tusk en arise.py
MODO_ENFOQUE_IGRIS = os.getenv("MODO_ENFOQUE_IGRIS", "True").lower() in ("1", "true", "yes")

# Fase 4 — ops Monarca (opcional en .env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

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
BERU_MODO_COMBATE_DEFAULT = os.getenv("BERU_MODO_COMBATE_DEFAULT", "NEGOCIADOR").upper()
# Legacy — el motor dinámico usa G_min + fricción 0.8% (beru_capital)
BERU_PNL_OBJETIVO_POR_1PCT_USD = float(os.getenv("BERU_PNL_OBJETIVO_POR_1PCT_USD", "50"))
BERU_SPOT_COLCHON_USD = float(os.getenv("BERU_SPOT_COLCHON_USD", "0"))  # spot margen: mismo equity, sin extra
BERU_VACIO_ANSIEDAD = float(os.getenv("BERU_VACIO_ANSIEDAD", "0.012"))   # 1.2%
BERU_VACIO_NORMAL = float(os.getenv("BERU_VACIO_NORMAL", "0.016"))         # 1.6%
# Motor 5 Reglas — G_min Bybit (arranque estático) + fricción Soldado
G_MIN_USD_DEFAULT = float(os.getenv("G_MIN_USD_DEFAULT", "5"))
G_MIN_USD_BY_ASSET: dict[str, float] = {
    "ETH": 5.0, "BTC": 5.0, "LTC": 5.0, "SOL": 5.0, "XRP": 5.0,
    "DOGE": 5.0, "ADA": 5.0, "LINK": 5.0, "AVAX": 5.0, "FIL": 5.0,
    "WIF": 5.0, "PEPE": 5.0,
}
BERU_FRICCION_SOLDADO_PCT = float(os.getenv("BERU_FRICCION_SOLDADO_PCT", "0.008"))  # 0.8%
BERU_ABISMO_SALIDA_PCT = float(os.getenv("BERU_ABISMO_SALIDA_PCT", "0.02"))         # -2% salida
BERU_ADAN_ARMADO_PCT = float(os.getenv("BERU_ADAN_ARMADO_PCT", "0.005"))           # 0.5% vacío Adán
# Beru Cazador — capas, red/oz reactivas (doctrina Monarca 2026-07)
BERU_CAZADOR_MORDIDA_USD = float(os.getenv("BERU_CAZADOR_MORDIDA_USD", "5"))
BERU_CAZADOR_PASO_PCT = float(os.getenv("BERU_CAZADOR_PASO_PCT", "0.001"))
BERU_CAZADOR_SPAWN_CADA_PCT = float(os.getenv("BERU_CAZADOR_SPAWN_CADA_PCT", "0.003"))
BERU_CAZADOR_GATILLO_FRACCION = float(os.getenv("BERU_CAZADOR_GATILLO_FRACCION", "0.5"))
BERU_CAZA_CAPA1_USD = float(os.getenv("BERU_CAZA_CAPA1_USD", "0"))
BERU_CAZA_CAPA1_MAX_USD = float(os.getenv("BERU_CAZA_CAPA1_MAX_USD", "50"))
# Peces / barcos — apalancamiento máx Bybit (promedio inverse+lineal en beru_capital)
ACTIVOS_BERU_FLOTA = [
    "ETH", "BTC", "LTC", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "MATIC",
    "DOT", "UNI", "ATOM", "FIL", "APT", "ARB", "OP", "SUI", "WIF", "PEPE",
]
MANTO_LEVERAGE_DEFAULT = float(os.getenv("MANTO_LEVERAGE_DEFAULT", "25"))
MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET: dict[str, float] = {
    "ETH": 100, "BTC": 100, "LTC": 75, "SOL": 50, "XRP": 75, "DOGE": 50,
    "ADA": 50, "LINK": 50, "AVAX": 50, "MATIC": 50, "DOT": 50, "UNI": 50,
    "ATOM": 50, "FIL": 25, "APT": 50, "ARB": 50, "OP": 50, "SUI": 50,
    "WIF": 20, "PEPE": 20,
}
MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET: dict[str, float] = {
    "ETH": 100, "BTC": 100, "LTC": 50, "SOL": 50, "XRP": 50, "DOGE": 50,
    "ADA": 50, "LINK": 50, "AVAX": 50, "MATIC": 50, "DOT": 50, "UNI": 50,
    "ATOM": 50, "FIL": 25, "APT": 50, "ARB": 50, "OP": 50, "SUI": 50,
    "WIF": 20, "PEPE": 20,
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

BOOTSTRAP_MANTO_FRACCION = 0.25

FASE_ACTUAL = "HIERRO"
VERSION = "2.0.0"
SISTEMA_NOMBRE = f"LILIT DE {FASE_ACTUAL} V{VERSION}"

# Igris / Greed — jurisdicción del manto (doctrina Monarca 2026-07-11)
RANGO_EXPANSION_MIN = 80.0       # legacy: umbral bajo absoluto
RANGO_PISO_IDEAL = 85.0          # piso zona ideal — bajo esto → Greed restaura
RANGO_OBJETIVO_MARGEN = 90.0     # techo zona ideal — Igris YIELD al entrar 85–90
RANGO_LIMPIEZA_MAX = 93.0        # zona alta (Greed puede limpiar)
MURO_LEY_MARCIAL = 95.0          # ≥95%: Greed poda fuerte de emergencia
IGRIS_YIELD_EN_ZONA_IDEAL = os.getenv("IGRIS_YIELD_EN_ZONA_IDEAL", "true").lower() == "true"
GREED_MANTO_EJECUTOR = os.getenv("GREED_MANTO_EJECUTOR", "true").lower() == "true"
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
MONARCA_RESERVA_PCT = float(os.getenv("MONARCA_RESERVA_PCT", "0.05"))
MONARCA_CONCENTRACION_MAX_PCT = float(os.getenv("MONARCA_CONCENTRACION_MAX_PCT", "0.20"))
MONARCA_MARGEN_OBJETIVO_PCT = float(os.getenv("MONARCA_MARGEN_OBJETIVO_PCT", "93.0"))
MONARCA_TIER_AUTO_DIAS = int(os.getenv("MONARCA_TIER_AUTO_DIAS", "3"))
MONARCA_MEGA_VIP_EQUITY_MIN = float(os.getenv("MONARCA_MEGA_VIP_EQUITY_MIN", "100"))
MONARCA_NIVEL_AUTO = os.getenv("MONARCA_NIVEL_AUTO", "true").lower() == "true"
# Legacy — botín 50/50 retirado; Greed usa colchón 5%
MONARCA_BOTIN_CIMIENTOS_PCT = float(os.getenv("MONARCA_BOTIN_CIMIENTOS_PCT", "1.0"))

DELTA_TOLERANCIA_MAX = 0.05
DELTA_MARGEN_RELAJADO = 70.0
DELTA_MARGEN_PARANOICO = 95.0

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

UMBRAL_VERDE_MS = 400.0
UMBRAL_AMARILLO_MS = 800.0
TOLERANCIA_GLITCH = 0.002
TOLERANCIA_COMA_S = 15.0

import sys
from core import trinidad as _trinidad  # noqa: E402

_trinidad.aplicar_a_config(sys.modules[__name__])
