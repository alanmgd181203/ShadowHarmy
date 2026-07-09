"""Utilidades neutras de mercado — radar compartido, no pertenecen a ningún General."""
import core.config as config

SYMBOL_MAP = {
    "LTCUSDT_LINEAL": "LTCUSDT",
    "LTCUSDC_LINEAL": "LTCUSDC",
    "LTCUSD_INVERSE": "LTCUSD",
    "LTCUSDT_SPOT": "LTCUSDT",
    "LTCUSDC_SPOT": "LTCUSDC",
    "BTCUSDT_LINEAL": "BTCUSDT",
    "BTCUSDC_LINEAL": "BTCUSDC",
    "BTCUSD_INVERSE": "BTCUSD",
    "BTCUSDT_SPOT": "BTCUSDT",
    "BTCUSDC_SPOT": "BTCUSDC",
    "ETHUSDT_LINEAL": "ETHUSDT",
}

CATEGORY_MAP = {
    "LTCUSDT_LINEAL": "linear",
    "LTCUSDC_LINEAL": "linear",
    "LTCUSD_INVERSE": "inverse",
    "LTCUSDT_SPOT": "spot",
    "LTCUSDC_SPOT": "spot",
    "BTCUSDT_LINEAL": "linear",
    "BTCUSDC_LINEAL": "linear",
    "BTCUSD_INVERSE": "inverse",
    "BTCUSDT_SPOT": "spot",
    "BTCUSDC_SPOT": "spot",
    "ETHUSDT_LINEAL": "linear",
}


def frente_a_symbol(frente: str) -> str:
    if frente in SYMBOL_MAP:
        return SYMBOL_MAP[frente]
    if "_" in frente:
        return frente.rsplit("_", 1)[0]
    return config.SIMBOLO_LINEAR


def frente_a_category(frente: str) -> str:
    if frente in CATEGORY_MAP:
        return CATEGORY_MAP[frente]
    if frente.endswith("_LINEAL"):
        return "linear"
    if frente.endswith("_INVERSE"):
        return "inverse"
    if frente.endswith("_SPOT"):
        return "spot"
    return "linear"


def activo_de_frente(frente: str) -> str:
    candidatos = (
        list(getattr(config, "ACTIVOS_TRINIDAD", []))
        + list(getattr(config, "ACTIVOS_USDC_SPOT", []))
        + list(config.ACTIVOS_PENTIVERSO)
    )
    candidatos = list(dict.fromkeys(candidatos))
    candidatos.sort(key=len, reverse=True)
    for a in candidatos:
        if frente.startswith(a):
            return a
    return config.TICKER_BASE


def es_frente_usdt(frente: str) -> bool:
    return "USDT" in frente.split("_")[0]


def es_frente_usdc(frente: str) -> bool:
    return "USDC" in frente.split("_")[0]


def aplicar_reflejos_usdc_lineal(precios: dict) -> dict:
    """Bybit no tiene *USDC perp — slot lineal refleja spot USDC."""
    out = dict(precios)
    for asset in config.ACTIVOS_PENTIVERSO:
        fl = f"{asset}USDC_LINEAL"
        fs = f"{asset}USDC_SPOT"
        if out.get(fl, 0) <= 0 and out.get(fs, 0) > 0:
            out[fl] = out[fs]
    return out


def escanear_mejor_precio(frentes, ctx_map, masa, is_long):
    analisis = {}
    for f in frentes:
        ctx = ctx_map.get(f)
        if not ctx or ctx.last_price <= 0:
            continue
        muro = ctx.muro_ask_volumen if is_long else ctx.muro_bid_volumen
        penalidad = 0.0001 if muro > (masa * 10) else 0.0015
        p_ef = ctx.last_price * (1 + penalidad) if is_long else ctx.last_price * (1 - penalidad)
        analisis[f] = p_ef
    if not analisis:
        return config.FRENTE_PRINCIPAL, 0.0
    ganador = min(analisis, key=analisis.get) if is_long else max(analisis, key=analisis.get)
    return ganador, analisis[ganador]


def escanear_mejor_regalo_usdt_usdc(ctx_map):
    """
    Greed: mezcla USDT con USDC (mismo activo LTC/BTC).
    Retorna (desviacion, frente_usdt, frente_usdc, p_usdt, p_usdc) o None.
    """
    mejor = None
    for fu, ctx_u in ctx_map.items():
        if not es_frente_usdt(fu) or ctx_u.last_price <= 0:
            continue
        asset = activo_de_frente(fu)
        for fc, ctx_c in ctx_map.items():
            if not es_frente_usdc(fc) or ctx_c.last_price <= 0:
                continue
            if activo_de_frente(fc) != asset:
                continue
            pu, pc = ctx_u.last_price, ctx_c.last_price
            desv = abs(pu - pc) / min(pu, pc)
            if mejor is None or desv > mejor[0]:
                mejor = (desv, fu, fc, pu, pc)
    return mejor


def calcular_banda_delta(margen: float):
    if margen <= config.DELTA_MARGEN_RELAJADO:
        tolerancia = config.DELTA_TOLERANCIA_MAX
    elif margen >= config.DELTA_MARGEN_PARANOICO:
        tolerancia = 0.0
    else:
        progreso = (margen - config.DELTA_MARGEN_RELAJADO) / (
            config.DELTA_MARGEN_PARANOICO - config.DELTA_MARGEN_RELAJADO
        )
        tolerancia = config.DELTA_TOLERANCIA_MAX * (1.0 - progreso)
    return (0.50 - tolerancia, 0.50 + tolerancia)


def calcular_banda_frente(margen: float, frente: str):
    if margen <= config.DELTA_MARGEN_RELAJADO:
        tolerancia_base = config.DELTA_TOLERANCIA_MAX
    elif margen >= config.DELTA_MARGEN_PARANOICO:
        tolerancia_base = 0.0
    else:
        progreso = (margen - config.DELTA_MARGEN_RELAJADO) / (
            config.DELTA_MARGEN_PARANOICO - config.DELTA_MARGEN_RELAJADO
        )
        tolerancia_base = config.DELTA_TOLERANCIA_MAX * (1.0 - progreso)
    factor = config.SLIPPAGE_FACTOR.get(frente, config.SLIPPAGE_FACTOR_DEFAULT)
    tolerancia = tolerancia_base * factor
    return (0.50 - tolerancia, 0.50 + tolerancia)


def verificar_delta_post_maniobra(margen, masa_long_nueva, masa_short_nueva):
    total = masa_long_nueva + masa_short_nueva
    if total <= 0:
        return True
    ratio = masa_long_nueva / total
    banda_min, banda_max = calcular_banda_delta(margen)
    return banda_min <= ratio <= banda_max


def verificar_delta_frente(margen, frente, masa_long_frente, masa_short_frente):
    total = masa_long_frente + masa_short_frente
    if total <= 0:
        return True
    ratio = masa_long_frente / total
    banda_min, banda_max = calcular_banda_frente(margen, frente)
    return banda_min <= ratio <= banda_max
