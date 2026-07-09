"""
Trinidad + USDC spot — descubrimiento Bybit mainnet.

Trinidad (manto + casa USDT): inverse + linear USDT + spot USDT.
USDC spot: todos los pares *USDC en spot Trading (filtrados por API).
"""
from __future__ import annotations

import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(ROOT, "data", "trinidad_bybit.json")
CACHE_TTL_S = 86400
MIN_ORDER_USD_DEFAULT = 5.0


def min_order_usd_de_instrumento(x: dict, category: str) -> float:
    """Mínimo notional USD por par desde lotSizeFilter Bybit."""
    lot = x.get("lotSizeFilter") or {}
    for key in ("minNotionalValue", "minOrderAmt"):
        raw = lot.get(key)
        if raw not in (None, "", "0"):
            try:
                val = float(raw)
                if val > 0:
                    return val
            except (TypeError, ValueError):
                pass
    try:
        min_qty = float(lot.get("minOrderQty") or 0)
    except (TypeError, ValueError):
        min_qty = 0.0
    if category == "inverse" and min_qty > 0:
        return min_qty
    if min_qty > 0:
        for px_key in ("lastPrice", "markPrice", "indexPrice"):
            try:
                px = float(x.get(px_key) or 0)
            except (TypeError, ValueError):
                px = 0.0
            if px > 0:
                return round(min_qty * px, 4)
    return MIN_ORDER_USD_DEFAULT


def _par_spot(x: dict) -> dict:
    sym = x["symbol"]
    return {
        "symbol": sym,
        "category": "spot",
        "frente": f"{sym}_SPOT",
        "marginTrading": x.get("marginTrading", "none"),
        "baseCoin": x.get("baseCoin", ""),
        "quoteCoin": x.get("quoteCoin", ""),
        "min_order_usd": min_order_usd_de_instrumento(x, "spot"),
    }


def _par_derivado(x: dict, category: str, frente_suf: str) -> dict:
    sym = x["symbol"]
    return {
        "symbol": sym,
        "category": category,
        "frente": f"{sym}_{frente_suf}",
        "contractType": x.get("contractType", ""),
        "settleCoin": x.get("settleCoin", ""),
        "baseCoin": x.get("baseCoin", ""),
        "deliveryTime": x.get("deliveryTime", ""),
        "min_order_usd": min_order_usd_de_instrumento(x, category),
    }


def construir_min_order_por_frente(pares_lists: list[list[dict]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for lst in pares_lists:
        for p in lst or []:
            frente = p.get("frente")
            if not frente:
                continue
            out[str(frente)] = float(p.get("min_order_usd") or MIN_ORDER_USD_DEFAULT)
    return out

BASES_TRINIDAD_DEFAULT = [
    "AAVE", "ADA", "APT", "AVAX", "BCH", "BTC", "DOGE", "DOT", "ETC", "ETH",
    "FIL", "LINK", "LTC", "MNT", "NEAR", "OP", "SOL", "SUI", "UNI", "XLM", "XRP",
]

BASES_USDC_DEFAULT = [
    "AAVE", "ADA", "APT", "AVAX", "BCH", "BTC", "DOGE", "DOT", "ETH", "FIL",
    "LINK", "LTC", "MNT", "NEAR", "OP", "SOL", "SUI", "UNI", "XLM", "XRP",
]

# 7 pares USDE mainnet Bybit (2026-07-05): 1 linear + 6 spot
USDE_PARES_DEFAULT = [
    {"symbol": "USDEUSDT", "category": "linear", "frente": "USDEUSDT_LINEAL"},
    {"symbol": "USDEUSDT", "category": "spot", "frente": "USDEUSDT_SPOT"},
    {"symbol": "USDEUSDC", "category": "spot", "frente": "USDEUSDC_SPOT"},
    {"symbol": "BTCUSDE", "category": "spot", "frente": "BTCUSDE_SPOT"},
    {"symbol": "ETHUSDE", "category": "spot", "frente": "ETHUSDE_SPOT"},
    {"symbol": "MNTUSDE", "category": "spot", "frente": "MNTUSDE_SPOT"},
    {"symbol": "SOLUSDE", "category": "spot", "frente": "SOLUSDE_SPOT"},
]

# 6 pares USD1 mainnet Bybit (2026-07-05): 1 linear + 5 spot
USD1_PARES_DEFAULT = [
    {"symbol": "USD1USDT", "category": "linear", "frente": "USD1USDT_LINEAL"},
    {"symbol": "USD1USDT", "category": "spot", "frente": "USD1USDT_SPOT"},
    {"symbol": "USDCUSD1", "category": "spot", "frente": "USDCUSD1_SPOT"},
    {"symbol": "BTCUSD1", "category": "spot", "frente": "BTCUSD1_SPOT"},
    {"symbol": "ETHUSD1", "category": "spot", "frente": "ETHUSD1_SPOT"},
    {"symbol": "MNTUSD1", "category": "spot", "frente": "MNTUSD1_SPOT"},
]

# 23 pares spot MNT mainnet Bybit (2026-07-05): quote=MNT (17) + base=MNT (6)
MNT_SPOT_PARES_DEFAULT = [
    {"symbol": s, "category": "spot", "frente": f"{s}_SPOT"}
    for s in (
        "LTCMNT", "ETHMNT", "SOLMNT", "XRPMNT", "DOGEMNT", "SUIMNT",
        "ADAMNT", "APEXMNT", "BBSOLMNT", "ENAMNT", "HBARMNT", "NXPCMNT",
        "ONDOMNT", "PEPEMNT", "PUMPMNT", "TRUMPMNT", "VIRTUALMNT",
        "MNTUSDT", "MNTUSDC", "MNTUSDE", "MNTUSD1", "MNTBTC", "MNTRLUSD",
    )
]


def frentes_trinidad_de_activo(base: str) -> list[str]:
    b = base.upper()
    return [f"{b}USDT_LINEAL", f"{b}USD_INVERSE", f"{b}USDT_SPOT"]


def frente_usdc_spot(base: str) -> str:
    return f"{base.upper()}USDC_SPOT"


def frentes_trinidad_para_bases(bases: list[str]) -> list[str]:
    out = []
    for base in bases:
        out.extend(frentes_trinidad_de_activo(base))
    return list(dict.fromkeys(out))


def frentes_usdc_para_bases(bases: list[str]) -> list[str]:
    return list(dict.fromkeys(frente_usdc_spot(b) for b in bases))


def frentes_rail_de_pares(pares: list[dict]) -> list[str]:
    return list(dict.fromkeys(p["frente"] for p in pares))


def calcular_bases_huerfanas(spot_all_pares: list[dict], linear_perp_pares: list[dict]) -> list[str]:
    """Perps USDT lineales sin par spot {BASE}USDT en Bybit."""
    spot_bases: set[str] = set()
    for p in spot_all_pares:
        sym = p.get("symbol", "")
        if sym.endswith("USDT"):
            spot_bases.add(sym[:-4])
    huerfanas: list[str] = []
    for p in linear_perp_pares:
        sym = p.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        base = sym[:-4]
        if base not in spot_bases:
            huerfanas.append(base)
    return sorted(set(huerfanas))


frentes_usde_de_pares = frentes_rail_de_pares


def descubrir_rail_desde_bybit(token: str, orden: dict | None = None) -> list[dict]:
    """Pares spot + linear cuyo símbolo contiene token (ej. USDE, USD1)."""
    from pybit.unified_trading import HTTP

    session = HTTP(testnet=False)
    pares = []
    for cat in ("spot", "linear"):
        r = session.get_instruments_info(category=cat, limit=1000)
        for x in r["result"]["list"]:
            if x.get("status") != "Trading":
                continue
            sym = x["symbol"]
            if token not in sym:
                continue
            suf = "LINEAL" if cat == "linear" else "SPOT"
            pares.append({
                "symbol": sym,
                "category": cat,
                "frente": f"{sym}_{suf}",
                "min_order_usd": min_order_usd_de_instrumento(x, cat),
            })
    if orden:
        pares.sort(key=lambda p: (0 if p["category"] == "linear" else 1, orden.get(p["symbol"], 99), p["symbol"]))
    return pares


def descubrir_usde_desde_listas(lin_list: list, spot_list: list) -> list[dict]:
    orden = {"USDEUSDT": 0, "USDEUSDC": 1, "BTCUSDE": 2, "ETHUSDE": 3, "MNTUSDE": 4, "SOLUSDE": 5}
    pares = []
    for cat, lst in (("linear", lin_list), ("spot", spot_list)):
        for x in lst:
            if x.get("status") != "Trading" or "USDE" not in x["symbol"]:
                continue
            sym = x["symbol"]
            suf = "LINEAL" if cat == "linear" else "SPOT"
            pares.append({
                "symbol": sym,
                "category": cat,
                "frente": f"{sym}_{suf}",
                "min_order_usd": min_order_usd_de_instrumento(x, cat),
            })
    pares.sort(key=lambda p: (0 if p["category"] == "linear" else 1, orden.get(p["symbol"], 99), p["symbol"]))
    return pares


def descubrir_usd1_desde_listas(lin_list: list, spot_list: list) -> list[dict]:
    orden = {"USD1USDT": 0, "USDCUSD1": 1, "BTCUSD1": 2, "ETHUSD1": 3, "MNTUSD1": 4}
    pares = []
    for cat, lst in (("linear", lin_list), ("spot", spot_list)):
        for x in lst:
            if x.get("status") != "Trading" or "USD1" not in x["symbol"]:
                continue
            sym = x["symbol"]
            suf = "LINEAL" if cat == "linear" else "SPOT"
            pares.append({
                "symbol": sym,
                "category": cat,
                "frente": f"{sym}_{suf}",
                "min_order_usd": min_order_usd_de_instrumento(x, cat),
            })
    pares.sort(key=lambda p: (0 if p["category"] == "linear" else 1, orden.get(p["symbol"], 99), p["symbol"]))
    return pares


def descubrir_usde_desde_bybit() -> list[dict]:
    orden = {"USDEUSDT": 0, "USDEUSDC": 1, "BTCUSDE": 2, "ETHUSDE": 3, "MNTUSDE": 4, "SOLUSDE": 5}
    return descubrir_rail_desde_bybit("USDE", orden)


def descubrir_usd1_desde_bybit() -> list[dict]:
    orden = {"USD1USDT": 0, "USDCUSD1": 1, "BTCUSD1": 2, "ETHUSD1": 3, "MNTUSD1": 4}
    return descubrir_rail_desde_bybit("USD1", orden)


def descubrir_todo_spot_desde_bybit() -> list[dict]:
    """Todos los pares spot Trading en Bybit mainnet (mapa completo Tank)."""
    from pybit.unified_trading import HTTP

    session = HTTP(testnet=False)
    pares = []
    for x in session.get_instruments_info(category="spot", limit=1000)["result"]["list"]:
        if x.get("status") != "Trading":
            continue
        sym = x["symbol"]
        if "SPOTTEST" in sym:
            continue
        pares.append(_par_spot(x))
    pares.sort(key=lambda p: p["symbol"])
    return pares


def _entry_derivado(x: dict, category: str, frente_suf: str) -> dict:
    return _par_derivado(x, category, frente_suf)


def parse_derivados_desde_listas(lin_list: list, inv_list: list) -> dict:
    """Perpetuos + futuros dated desde respuestas instruments-info (sin API extra)."""
    linear_perp, linear_futures = [], []
    inverse_perp, inverse_futures = [], []
    for x in lin_list:
        if x.get("status") != "Trading":
            continue
        ct = x.get("contractType", "")
        if ct == "LinearPerpetual":
            linear_perp.append(_entry_derivado(x, "linear", "LINEAL"))
        elif ct == "LinearFutures":
            linear_futures.append(_entry_derivado(x, "linear", "FUTURO"))
    for x in inv_list:
        if x.get("status") != "Trading":
            continue
        ct = x.get("contractType", "")
        if ct == "InversePerpetual":
            inverse_perp.append(_entry_derivado(x, "inverse", "INVERSE"))
        elif ct == "InverseFutures":
            inverse_futures.append(_entry_derivado(x, "inverse", "FUTURO"))
    for lst in (linear_perp, linear_futures, inverse_perp, inverse_futures):
        lst.sort(key=lambda p: p["symbol"])
    return {
        "linear": linear_perp,
        "inverse": inverse_perp,
        "linear_futures": linear_futures,
        "inverse_futures": inverse_futures,
    }


def descubrir_todo_perp_desde_bybit() -> dict:
    """Todos los perpetuos Trading: linear + inverse."""
    from pybit.unified_trading import HTTP

    session = HTTP(testnet=False)
    lin = session.get_instruments_info(category="linear", limit=1000)["result"]["list"]
    inv = session.get_instruments_info(category="inverse", limit=1000)["result"]["list"]
    d = parse_derivados_desde_listas(lin, inv)
    return {"linear": d["linear"], "inverse": d["inverse"]}


def descubrir_todo_futures_desde_bybit() -> dict:
    """Futuros con vencimiento (trimestrales / dated)."""
    from pybit.unified_trading import HTTP

    session = HTTP(testnet=False)
    lin = session.get_instruments_info(category="linear", limit=1000)["result"]["list"]
    inv = session.get_instruments_info(category="inverse", limit=1000)["result"]["list"]
    d = parse_derivados_desde_listas(lin, inv)
    return {"linear": d["linear_futures"], "inverse": d["inverse_futures"]}


def descubrir_mnt_spot_desde_bybit() -> list[dict]:
    """Todos los pares spot con base o quote MNT (ventanilla + token)."""
    from pybit.unified_trading import HTTP

    session = HTTP(testnet=False)
    quote_prio = {"LTCMNT": 0, "ETHMNT": 1, "SOLMNT": 2, "XRPMNT": 3, "DOGEMNT": 4, "SUIMNT": 5}
    base_prio = {"MNTUSDT": 0, "MNTUSDC": 1, "MNTUSDE": 2, "MNTUSD1": 3, "MNTBTC": 4, "MNTRLUSD": 5}
    pares = []
    for x in session.get_instruments_info(category="spot", limit=1000)["result"]["list"]:
        if x.get("status") != "Trading":
            continue
        base = x.get("baseCoin", "")
        quote = x.get("quoteCoin", "")
        if base != "MNT" and quote != "MNT":
            continue
        sym = x["symbol"]
        pares.append(_par_spot(x))
    pares.sort(
        key=lambda p: (
            0 if p["symbol"] in quote_prio else 1,
            quote_prio.get(p["symbol"], base_prio.get(p["symbol"], 50)),
            p["symbol"],
        )
    )
    return pares


def frentes_tank_completos(
    spot_pares: list[dict],
    linear_perp: list[dict],
    inverse_perp: list[dict],
    linear_futures: list[dict],
    inverse_futures: list[dict],
    mares_extra: list[str],
) -> list[str]:
    return list(dict.fromkeys(
        frentes_rail_de_pares(spot_pares)
        + frentes_rail_de_pares(linear_perp)
        + frentes_rail_de_pares(inverse_perp)
        + frentes_rail_de_pares(linear_futures)
        + frentes_rail_de_pares(inverse_futures)
        + list(mares_extra)
    ))


# Compat aliases
frentes_de_activo = frentes_trinidad_de_activo
frentes_para_bases = frentes_trinidad_para_bases


def _leer_cache() -> dict | None:
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _guardar_cache(payload: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def descubrir_desde_bybit() -> dict:
    """Retorna bases trinidad + bases USDC spot permitidos."""
    from pybit.unified_trading import HTTP

    session = HTTP(testnet=False)
    inv = session.get_instruments_info(category="inverse", limit=1000)
    lin = session.get_instruments_info(category="linear", limit=1000)
    spot = session.get_instruments_info(category="spot", limit=1000)

    inv_syms = {
        x["symbol"]
        for x in inv["result"]["list"]
        if x.get("status") == "Trading" and x["symbol"].endswith("USD") and "USDT" not in x["symbol"]
    }
    lin_usdt = {
        x["symbol"]
        for x in lin["result"]["list"]
        if x.get("status") == "Trading" and x["symbol"].endswith("USDT")
    }
    spot_usdt = {
        x["symbol"]
        for x in spot["result"]["list"]
        if x.get("status") == "Trading" and x["symbol"].endswith("USDT")
    }
    spot_usdc = sorted(
        x["symbol"]
        for x in spot["result"]["list"]
        if x.get("status") == "Trading" and x["symbol"].endswith("USDC")
    )

    bases_trinidad = []
    for sym in sorted(inv_syms):
        base = sym.replace("USD", "")
        if f"{base}USDT" in lin_usdt and f"{base}USDT" in spot_usdt:
            bases_trinidad.append(base)

    bases_usdc = [sym.replace("USDC", "") for sym in spot_usdc]
    spot_list = spot["result"]["list"]
    lin_list = lin["result"]["list"]
    inv_list = inv["result"]["list"]

    spot_all_pares = []
    mnt_spot_pares = []
    for x in spot_list:
        if x.get("status") != "Trading":
            continue
        sym = x["symbol"]
        if "SPOTTEST" in sym:
            continue
        entry = _par_spot(x)
        spot_all_pares.append(entry)
        base, quote = x.get("baseCoin", ""), x.get("quoteCoin", "")
        if base == "MNT" or quote == "MNT":
            mnt_spot_pares.append(dict(entry))
    spot_all_pares.sort(key=lambda p: p["symbol"])
    mnt_spot_pares.sort(key=lambda p: p["symbol"])

    usde_pares = descubrir_usde_desde_listas(lin_list, spot_list)
    usd1_pares = descubrir_usd1_desde_listas(lin_list, spot_list)
    deriv = parse_derivados_desde_listas(lin_list, inv_list)

    return {
        "bases_trinidad": bases_trinidad,
        "bases_usdc_spot": bases_usdc,
        "symbols_usdc_spot": spot_usdc,
        "usde_pares": usde_pares,
        "usd1_pares": usd1_pares,
        "mnt_spot_pares": mnt_spot_pares,
        "spot_all_pares": spot_all_pares,
        "linear_perp_pares": deriv["linear"],
        "inverse_perp_pares": deriv["inverse"],
        "linear_futures_pares": deriv["linear_futures"],
        "inverse_futures_pares": deriv["inverse_futures"],
    }


def _payload_desde_descubrimiento(data: dict, fuente: str = "api") -> dict:
    bt = data["bases_trinidad"]
    bu = data["bases_usdc_spot"]
    usde = data.get("usde_pares") or USDE_PARES_DEFAULT
    usd1 = data.get("usd1_pares") or USD1_PARES_DEFAULT
    mnt_spot = data.get("mnt_spot_pares") or MNT_SPOT_PARES_DEFAULT
    spot_all = data.get("spot_all_pares") or []
    linear_perp = data.get("linear_perp_pares") or []
    inverse_perp = data.get("inverse_perp_pares") or []
    linear_futures = data.get("linear_futures_pares") or []
    inverse_futures = data.get("inverse_futures_pares") or []
    huerfanas = calcular_bases_huerfanas(spot_all, linear_perp)
    return {
        "ts": time.time(),
        "fuente": fuente,
        "bases_trinidad": bt,
        "bases_usdc_spot": bu,
        "bases_huerfanas": huerfanas,
        "count_huerfanas": len(huerfanas),
        "count_trinidad": len(bt),
        "count_usdc_spot": len(bu),
        "count_usde": len(usde),
        "count_usd1": len(usd1),
        "count_mnt_spot": len(mnt_spot),
        "count_spot_all": len(spot_all),
        "count_linear_perp": len(linear_perp),
        "count_inverse_perp": len(inverse_perp),
        "count_linear_futures": len(linear_futures),
        "count_inverse_futures": len(inverse_futures),
        "count_spot_margin": sum(
            1 for p in spot_all if str(p.get("marginTrading", "none")).lower() not in ("none", "")
        ),
        "frentes_trinidad": frentes_trinidad_para_bases(bt),
        "frentes_usdc_spot": frentes_usdc_para_bases(bu),
        "usde_pares": usde,
        "usd1_pares": usd1,
        "mnt_spot_pares": mnt_spot,
        "spot_all_pares": spot_all,
        "linear_perp_pares": linear_perp,
        "inverse_perp_pares": inverse_perp,
        "linear_futures_pares": linear_futures,
        "inverse_futures_pares": inverse_futures,
        "frentes_usde": frentes_rail_de_pares(usde),
        "frentes_usd1": frentes_rail_de_pares(usd1),
        "frentes_mnt_spot": frentes_rail_de_pares(mnt_spot),
        "frentes_spot_all": frentes_rail_de_pares(spot_all),
        "frentes_linear_perp": frentes_rail_de_pares(linear_perp),
        "frentes_inverse_perp": frentes_rail_de_pares(inverse_perp),
        "frentes_linear_futures": frentes_rail_de_pares(linear_futures),
        "frentes_inverse_futures": frentes_rail_de_pares(inverse_futures),
        "symbols_usdc_spot": data.get("symbols_usdc_spot", []),
    }


def cargar_desde_cache_o_default() -> dict:
    cached = _leer_cache()
    if cached and cached.get("bases_trinidad"):
        return cached
    return _payload_desde_descubrimiento(
        {
            "bases_trinidad": BASES_TRINIDAD_DEFAULT,
            "bases_usdc_spot": BASES_USDC_DEFAULT,
            "usde_pares": USDE_PARES_DEFAULT,
            "usd1_pares": USD1_PARES_DEFAULT,
            "mnt_spot_pares": MNT_SPOT_PARES_DEFAULT,
        },
        fuente="default",
    )


def cargar_bases(sync_refresh: bool = False) -> list[str]:
    """Compat: solo bases trinidad."""
    data = cargar_desde_cache_o_default()
    if sync_refresh:
        try:
            fresh = descubrir_desde_bybit()
            _guardar_cache(_payload_desde_descubrimiento(fresh))
            return fresh["bases_trinidad"]
        except Exception:
            pass
    return list(data.get("bases_trinidad", BASES_TRINIDAD_DEFAULT))


def cargar_bases_usdc() -> list[str]:
    data = cargar_desde_cache_o_default()
    return list(data.get("bases_usdc_spot", BASES_USDC_DEFAULT))


def aplicar_a_config(config_module) -> None:
    data = cargar_desde_cache_o_default()
    config_module.ACTIVOS_TRINIDAD = list(data.get("bases_trinidad", BASES_TRINIDAD_DEFAULT))
    config_module.ACTIVOS_USDC_SPOT = list(data.get("bases_usdc_spot", BASES_USDC_DEFAULT))
    config_module.USDE_PARES = list(data.get("usde_pares", USDE_PARES_DEFAULT))
    config_module.USD1_PARES = list(data.get("usd1_pares", USD1_PARES_DEFAULT))
    config_module.MNT_SPOT_PARES = list(data.get("mnt_spot_pares", MNT_SPOT_PARES_DEFAULT))
    config_module.SPOT_ALL_PARES = list(data.get("spot_all_pares", []))
    config_module.LINEAR_PERP_PARES = list(data.get("linear_perp_pares", []))
    config_module.INVERSE_PERP_PARES = list(data.get("inverse_perp_pares", []))
    config_module.LINEAR_FUTURES_PARES = list(data.get("linear_futures_pares", []))
    config_module.INVERSE_FUTURES_PARES = list(data.get("inverse_futures_pares", []))
    config_module.ACTIVOS_HUERFANOS = list(
        data.get("bases_huerfanas")
        or calcular_bases_huerfanas(
            config_module.SPOT_ALL_PARES,
            config_module.LINEAR_PERP_PARES,
        )
    )
    from core.activo import bases_vigilancia_binance
    config_module.BASES_PANORAMA = bases_vigilancia_binance()
    config_module.FRENTES_TRINIDAD = frentes_trinidad_para_bases(config_module.ACTIVOS_TRINIDAD)
    config_module.FRENTES_USDC_SPOT = frentes_usdc_para_bases(config_module.ACTIVOS_USDC_SPOT)
    config_module.FRENTES_USDE = frentes_rail_de_pares(config_module.USDE_PARES)
    config_module.FRENTES_USD1 = frentes_rail_de_pares(config_module.USD1_PARES)
    config_module.FRENTES_MNT_SPOT = frentes_rail_de_pares(config_module.MNT_SPOT_PARES)
    config_module.FRENTES_SPOT_ALL = frentes_rail_de_pares(config_module.SPOT_ALL_PARES)
    config_module.FRENTES_LINEAR_PERP = frentes_rail_de_pares(config_module.LINEAR_PERP_PARES)
    config_module.FRENTES_INVERSE_PERP = frentes_rail_de_pares(config_module.INVERSE_PERP_PARES)
    config_module.FRENTES_LINEAR_FUTURES = frentes_rail_de_pares(config_module.LINEAR_FUTURES_PARES)
    config_module.FRENTES_INVERSE_FUTURES = frentes_rail_de_pares(config_module.INVERSE_FUTURES_PARES)
    config_module.FRENTES_TANK = frentes_tank_completos(
        config_module.SPOT_ALL_PARES,
        config_module.LINEAR_PERP_PARES,
        config_module.INVERSE_PERP_PARES,
        config_module.LINEAR_FUTURES_PARES,
        config_module.INVERSE_FUTURES_PARES,
        config_module.MARES_PENTIVERSO_ALL,
    )
    config_module.MIN_ORDER_USD_DEFAULT = MIN_ORDER_USD_DEFAULT
    config_module.MIN_ORDER_USD_BY_FRENTE = construir_min_order_por_frente([
        config_module.SPOT_ALL_PARES,
        config_module.LINEAR_PERP_PARES,
        config_module.INVERSE_PERP_PARES,
        config_module.LINEAR_FUTURES_PARES,
        config_module.INVERSE_FUTURES_PARES,
        config_module.USDE_PARES,
        config_module.USD1_PARES,
        config_module.MNT_SPOT_PARES,
    ])


def refrescar_config() -> dict:
    import core.config as cfg
    fresh = descubrir_desde_bybit()
    payload = _payload_desde_descubrimiento(fresh)
    _guardar_cache(payload)
    aplicar_a_config(cfg)
    return payload


def inicializar_config(config_module) -> None:
    aplicar_a_config(config_module)


async def refrescar_si_stale() -> dict:
    cached = _leer_cache()
    if cached and (time.time() - cached.get("ts", 0)) < CACHE_TTL_S:
        return cached
    import asyncio
    try:
        fresh = await asyncio.to_thread(descubrir_desde_bybit)
        payload = _payload_desde_descubrimiento(fresh)
        _guardar_cache(payload)
        import core.config as cfg
        aplicar_a_config(cfg)
        return payload
    except Exception:
        pass
    return cargar_desde_cache_o_default()
