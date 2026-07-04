import os

# === [CARGADOR DE SECRETOS .ENV] ===
def cargar_env():
    """Busca el archivo .env en la raíz del proyecto y carga las llaves en memoria."""
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

# 🔑 EXTRACCIÓN DE LLAVES (Protegidas)
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
TESTNET = os.getenv("MODO_TESTNET", "True").lower() == "true"

# 🚦 MODO SIMULACIÓN — interruptor maestro de seguridad
# True = Greed simula internamente (no toca exchange). False = órdenes van al Bridge real.
MODO_SIMULACION = os.getenv("MODO_SIMULACION", "True").lower() == "true"

# === [SUBTEMA: IDENTIDAD DEL SISTEMA] ===
FASE_ACTUAL = "HIERRO"
VERSION = "2.0.0"
SISTEMA_NOMBRE = f"LILIT DE {FASE_ACTUAL} V{VERSION}"

# === [SUBTEMA: RANGOS OPERATIVOS DE IGRIS] ===
RANGO_EXPANSION_MIN = 80.0
RANGO_LIMPIEZA_MAX = 90.0
MURO_LEY_MARCIAL = 95.0

# === [SUBTEMA: BANDA ADAPTATIVA DE DELTA] ===
# Tolerancia máxima al desbalance (±5% del 50%) cuando hay poco margen usado
DELTA_TOLERANCIA_MAX = 0.05
# Por debajo de este % de margen, la banda es máxima (45-55)
DELTA_MARGEN_RELAJADO = 70.0
# A partir de este % de margen, la banda es cero (50-50)
DELTA_MARGEN_PARANOICO = 95.0

# === [SUBTEMA: PERSONALIDAD DE SLIPPAGE POR FRENTE] ===
# Factor 1.0 = moneda tranquila (casi sin slippage, banda completa).
# Factor bajo = moneda caliente (mucho slippage histórico, banda apretada).
# Fórmula: banda_frente = banda_general × factor
# Valores pre-configurados (se reemplazarán con datos reales en M1+).
SLIPPAGE_FACTOR = {
    "LTCUSDT_LINEAL": 0.7,
    "LTCUSDC_LINEAL": 0.7,
    "LTCUSD_INVERSE": 0.5,
    "LTCUSDC_SPOT": 0.8,
    "LTCUSDT_SPOT": 0.8,
    "BTCUSDT_LINEAL": 1.0,
    "ETHUSDT_LINEAL": 0.9,
    "FILUSDT_LINEAL": 0.25,
    "WIFUSDT_LINEAL": 0.2,
}
# Frente desconocido → factor conservador
SLIPPAGE_FACTOR_DEFAULT = 0.5

# === [SUBTEMA: UMBRALES DE GREED] ===
UMBRAL_COSECHA_MIN = 0.01   
UMBRAL_REGALO_SQUAD = 0.003  
TTL_ORDEN_MS = 2000         

# === [SUBTEMA: ARITMÉTICA DE TUSK] ===
ESCALON_POTENCIA_BASE = 5.0    
FACTOR_MASA_AUTORIZADA = 10.0  

# === [SUBTEMA: AUDITORÍA TANK (VISIÓN)] ===
UMBRAL_VERDE_MS = 400.0     
UMBRAL_AMARILLO_MS = 800.0  
TOLERANCIA_GLITCH = 0.002 
TOLERANCIA_COMA_S = 15.0