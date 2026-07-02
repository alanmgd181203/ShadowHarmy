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

# === [SUBTEMA: IDENTIDAD DEL SISTEMA] ===
FASE_ACTUAL = "HIERRO"
VERSION = "2.0.0"
SISTEMA_NOMBRE = f"LILIT DE {FASE_ACTUAL} V{VERSION}"

# === [SUBTEMA: RANGOS OPERATIVOS DE IGRIS] ===
RANGO_EXPANSION_MIN = 80.0  
RANGO_LIMPIEZA_MAX = 90.0   
MURO_LEY_MARCIAL = 95.0    

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