"""Sentidos REST — Spread producto Bybit, Alpha, Convert (ojos complementarios a Tank WS)."""
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request

import core.config as config

# Ojos públicos: mainnet (igual que WS Bridge), aunque manos sean testnet
API_BASE = "https://api.bybit.com"


def _http_get(path: str, params: dict | None = None) -> dict:
    qs = ""
    if params:
        qs = "?" + "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{API_BASE}{path}{qs}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def _http_post(path: str, body: dict) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def _safe_call(fn, *args, **kwargs) -> tuple[dict | list | None, str | None]:
    try:
        return fn(*args, **kwargs), None
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
        except Exception:
            body = str(e)
        return None, f"HTTP {e.code}: {body[:200]}"
    except Exception as e:
        return None, str(e)[:200]


def fetch_spread_producto_sync(session=None) -> tuple[list[dict], str | None]:
    """Instrumentos + tickers del producto Spread Trading Bybit."""
    from pybit.unified_trading import HTTP

    sess = HTTP(testnet=False)
    instrumentos: list[dict] = []
    cursor = ""
    err = None
    while True:
        kwargs = {"limit": 500}
        if cursor:
            kwargs["cursor"] = cursor
        data, e = _safe_call(sess.spread_get_instruments_info, **kwargs)
        if e:
            err = e
            break
        if not data or data.get("retCode") != 0:
            err = (data or {}).get("retMsg", "spread/instrument error")
            break
        batch = data.get("result", {}).get("list", [])
        instrumentos.extend(batch)
        cursor = data.get("result", {}).get("nextPageCursor", "")
        if not cursor or not batch:
            break

    tickers_map: dict[str, dict] = {}
    for inst in instrumentos:
        sym = inst.get("symbol", "")
        if not sym or inst.get("status") != "Trading":
            continue
        td, e = _safe_call(sess.spread_get_tickers, symbol=sym)
        if e and not err:
            err = e
            continue
        if td and td.get("retCode") == 0:
            lst = td.get("result", {}).get("list", [])
            if lst:
                tickers_map[sym] = lst[0]

    out = []
    for inst in instrumentos:
        sym = inst.get("symbol", "")
        tk = tickers_map.get(sym, {})
        last = float(tk.get("lastPrice") or 0)
        out.append({
            "symbol": sym,
            "contractType": inst.get("contractType", ""),
            "baseCoin": inst.get("baseCoin", ""),
            "lastPrice": last,
            "bidPrice": float(tk.get("bidPrice") or 0),
            "askPrice": float(tk.get("askPrice") or 0),
            "legs": inst.get("legs", []),
        })
    return out, err


def fetch_alpha_sync() -> tuple[dict, str | None]:
    """Tokens Alpha on-chain (lista + precios). API pública REST."""
    tokens_body = {"page": 1, "limit": 50}
    data, err = _safe_call(_http_post, "/v5/alpha/trade/biz-token-list", tokens_body)
    if err or not data or data.get("retCode") != 0:
        return {}, err or (data or {}).get("retMsg", "alpha token list error")

    tokens = data.get("result", {}).get("list", []) or data.get("result", {}).get("tokenList", []) or []
    if not tokens and isinstance(data.get("result"), dict):
        tokens = data["result"].get("data", []) or []

    precios: dict = {}
    if tokens:
        codes = []
        for t in tokens[:30]:
            code = t.get("tokenCode") or t.get("bizTokenId") or t.get("id")
            if code:
                codes.append(str(code))
        if codes:
            price_body = {"tokenCodeList": codes}
            pd, pe = _safe_call(_http_post, "/v5/alpha/trade/biz-token-price-list", price_body)
            if not pe and pd and pd.get("retCode") == 0:
                plst = pd.get("result", {}).get("list", []) or pd.get("result", {}).get("priceList", [])
                for p in plst:
                    key = p.get("tokenCode") or p.get("bizTokenId", "")
                    if key:
                        precios[key] = {
                            "price": p.get("price") or p.get("lastPrice"),
                            "change24h": p.get("change24h") or p.get("priceChange24h"),
                        }

    resumen = []
    for t in tokens[:50]:
        code = t.get("tokenCode") or t.get("bizTokenId") or t.get("id", "")
        resumen.append({
            "tokenCode": code,
            "symbol": t.get("symbol") or t.get("tokenName", ""),
            "chain": t.get("chain") or t.get("chainName", ""),
            "precio": (precios.get(str(code)) or {}).get("price"),
        })

    return {"tokens": resumen, "precios": precios, "total": len(tokens)}, err


def fetch_convert_sync(session=None) -> tuple[list[dict], str | None]:
    """Pares Convert disponibles (requiere API key en cuenta unificada)."""
    from pybit.unified_trading import HTTP

    if not session and not (config.API_KEY and config.API_SECRET):
        return [], "Sin sesión API — Convert ojos omitidos"

    sess = session or HTTP(
        testnet=False,
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
    )
    data, err = _safe_call(sess.get_convert_coin_list, accountType="eb_convert_uta")
    if err or not data or data.get("retCode") != 0:
        return [], err or (data or {}).get("retMsg", "convert coin list error")

    coins = data.get("result", {}).get("coins", []) or data.get("result", {}).get("list", []) or []
    out = []
    for c in coins[:100]:
        out.append({
            "coin": c.get("coin", c.get("fromCoin", "")),
            "toCoin": c.get("toCoin", ""),
            "support": c.get("supportConvert") or c.get("support", 1),
        })
    return out, err


def fetch_convert_quotes_sync(session=None, precios_spot: dict | None = None) -> tuple[list[dict], str | None]:
    """Cotización Convert vs spot Bybit (muestra trinidad + pentiverso)."""
    from pybit.unified_trading import HTTP

    if not session and not (config.API_KEY and config.API_SECRET):
        return [], "Sin sesión API — Convert quotes omitidos"

    sess = session or HTTP(
        testnet=False,
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
    )
    precios_spot = precios_spot or {}
    bases = list(dict.fromkeys(
        list(getattr(config, "ACTIVOS_TRINIDAD", [])[:8])
        + list(config.ACTIVOS_PENTIVERSO)
    ))
    monto = getattr(config, "CONVERT_QUOTE_USDT_MONTO", "100")
    out: list[dict] = []
    err = None

    for base in bases:
        spot_f = f"{base}USDT_SPOT"
        spot_px = precios_spot.get(spot_f, 0.0)
        q, e = _safe_call(
            sess.request_a_quote,
            fromCoin="USDT",
            toCoin=base,
            requestCoin="USDT",
            requestAmount=monto,
            accountType="eb_convert_uta",
        )
        if e and not err:
            err = e
            continue
        if not q or q.get("retCode") != 0:
            continue
        res = q.get("result", {})
        to_amt = float(res.get("toAmount") or res.get("receiveAmount") or 0)
        if to_amt <= 0:
            continue
        convert_px = float(monto) / to_amt
        lag_pct = None
        if spot_px > 0:
            lag_pct = round((convert_px - spot_px) / spot_px * 100, 4)
        out.append({
            "base": base,
            "convert_px_implied": round(convert_px, 8),
            "spot_bybit": spot_px if spot_px > 0 else None,
            "lag_vs_spot_pct": lag_pct,
            "from_usdt": monto,
        })
    return out, err


class SentidosExtraPoller:
    """Hilo asyncio: inyecta sentidos REST en Tank.sentidos_extra."""

    def __init__(self, tank, bellion, session=None):
        self.tank = tank
        self.bel = bellion
        self.session = session

    async def run(self):
        await self.bel.anotar("TANK", "SENTIDOS_EXTRA", "Ojos REST: spread producto, alpha, convert.")
        while True:
            await self._poll_spread()
            await asyncio.sleep(getattr(config, "SENTIDOS_SPREAD_POLL_S", 60))

    async def run_alpha(self):
        while True:
            await self._poll_alpha()
            await asyncio.sleep(getattr(config, "SENTIDOS_ALPHA_POLL_S", 120))

    async def run_convert(self):
        while True:
            await self._poll_convert()
            await asyncio.sleep(getattr(config, "SENTIDOS_CONVERT_POLL_S", 90))

    async def run_convert_quotes(self):
        while True:
            await self._poll_convert_quotes()
            await asyncio.sleep(getattr(config, "CONVERT_QUOTE_POLL_S", 120))

    async def _poll_spread(self):
        loop = asyncio.get_running_loop()
        items, err = await loop.run_in_executor(None, fetch_spread_producto_sync, self.session)
        self.tank.sentidos_extra["spread_producto"] = items
        self.tank.sentidos_extra["ts_spread"] = time.time()
        if err:
            self.tank.sentidos_extra["errores"]["spread"] = err
        elif "spread" in self.tank.sentidos_extra.get("errores", {}):
            self.tank.sentidos_extra["errores"].pop("spread", None)

    async def _poll_alpha(self):
        loop = asyncio.get_running_loop()
        data, err = await loop.run_in_executor(None, fetch_alpha_sync)
        self.tank.sentidos_extra["alpha"] = data
        self.tank.sentidos_extra["ts_alpha"] = time.time()
        if err:
            self.tank.sentidos_extra["errores"]["alpha"] = err
        elif "alpha" in self.tank.sentidos_extra.get("errores", {}):
            self.tank.sentidos_extra["errores"].pop("alpha", None)

    async def _poll_convert(self):
        loop = asyncio.get_running_loop()
        items, err = await loop.run_in_executor(None, fetch_convert_sync, self.session)
        self.tank.sentidos_extra["convert"] = items
        self.tank.sentidos_extra["ts_convert"] = time.time()
        if err:
            self.tank.sentidos_extra["errores"]["convert"] = err
        elif "convert" in self.tank.sentidos_extra.get("errores", {}):
            self.tank.sentidos_extra["errores"].pop("convert", None)

    async def _poll_convert_quotes(self):
        loop = asyncio.get_running_loop()
        lider = self.tank._obtener_lider_verde()
        precios = lider.precios_con_reflejo() if lider else {}
        items, err = await loop.run_in_executor(
            None, fetch_convert_quotes_sync, self.session, precios,
        )
        self.tank.sentidos_extra["convert_quotes"] = items
        self.tank.sentidos_extra["ts_convert_quotes"] = time.time()
        if err:
            self.tank.sentidos_extra["errores"]["convert_quotes"] = err
        elif "convert_quotes" in self.tank.sentidos_extra.get("errores", {}):
            self.tank.sentidos_extra["errores"].pop("convert_quotes", None)
