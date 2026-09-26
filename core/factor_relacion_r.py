"""Factor dinámico R — volatilidad relativa TOTAL3 / BTC (escudo Igris).

Módulo aislado para cablear a testnet/live **sin** tocar el teatro viejo.

Pipeline (Monarca 2026-09-23 — under-hedging con sesgo largo)::

  1. R_crudo   = std(TOTAL3) / std(BTC)
  2. R_vol     = clamp(R_crudo, 1.0, 1.8)          # cinturón de seguridad
  3. R_redondeado = round(R_vol, 1)               # décima (mata fricción)
  4. R_final   = max(1.0, R_redondeado - 0.2)     # descuento estratégico −0.2

Ejemplo: 1.63 → 1.6 → **1.4**. Nunca bajo 1:1. Fallo API → R = 1.0.

TOTAL3 (TradingView CRYPTOCAP:TOTAL3) = cap. cripto excluyendo BTC y ETH.
Fuente ligera por defecto: **Bybit public klines** — índice equal-weight de
alts líquidas (ex-BTC, ex-ETH). Opcional: CoinGecko market_caps
(total − BTC − ETH) si hay ``COINGECKO_API_KEY`` / ``CG_API_KEY``.

Uso::

    from core.factor_relacion_r import calcular_r, RelacionR

    r = calcular_r()                 # R_final listo para Igris
    info = calcular_r_detalle()      # auditoría (crudo / redondeado / final)
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Sequence

# --- Constantes doctrinales -------------------------------------------------

R_MIN: float = 1.0
R_MAX: float = 1.8
R_FALLBACK: float = 1.0
# Under-hedging: holgura direccional (Monarca) — no cubrir el 100% del R de vol
R_DESCUENTO_ESTRATEGICO: float = float(
    os.getenv("IGRIS_ESCUDO_BTC_R_DESCUENTO", "0.2") or 0.2
)

BYBIT_BASE: str = os.getenv("BYBIT_PUBLIC_BASE", "https://api.bybit.com").rstrip("/")
COINGECKO_BASE: str = os.getenv(
    "COINGECKO_API_BASE", "https://api.coingecko.com/api/v3"
).rstrip("/")

# Cesta TOTAL3-proxy (ex BTC, ex ETH) — linear USDT Bybit, líquidas
TOTAL3_BYBIT_SYMBOLS: tuple[str, ...] = (
    "SOLUSDT",
    "XRPUSDT",
    "BNBUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "ATOMUSDT",
    "NEARUSDT",
    "UNIUSDT",
    "APTUSDT",
    "SUIUSDT",
    "AAVEUSDT",
)


@dataclass(frozen=True)
class RelacionR:
    """Resultado del cálculo de R con auditoría mínima.

    ``r`` = R_final operativo (lo que Igris debe usar).
    """

    r: float
    r_raw: float
    r_vol: float
    r_redondeado: float
    std_total3: float
    std_btc: float
    n_obs: int
    ventana_dias: int
    intervalo: str
    fuente_btc: str
    fuente_total3: str
    ok: bool
    detalle: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# --- HTTP mínimo ------------------------------------------------------------


def _http_get_json(url: str, *, timeout: float = 25.0, headers: dict[str, str] | None = None) -> Any:
    hdrs = {
        "User-Agent": "ShadowHarmy-factor-relacion-r/1.0",
        "Accept": "application/json",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _coingecko_headers() -> dict[str, str]:
    key = (
        os.getenv("COINGECKO_API_KEY")
        or os.getenv("CG_API_KEY")
        or os.getenv("X_CG_DEMO_API_KEY")
        or ""
    ).strip()
    if not key:
        return {}
    # Demo y Pro usan headers distintos; enviamos ambos inofensivos
    return {"x-cg-demo-api-key": key, "x-cg-api-key": key}


# --- Series de precio -------------------------------------------------------


def fetch_btc_closes_bybit(
    *,
    intervalo: str = "D",
    limit: int = 35,
) -> list[float]:
    """Cierres BTCUSDT (linear) vía Bybit v5 público."""
    q = urllib.parse.urlencode(
        {
            "category": "linear",
            "symbol": "BTCUSDT",
            "interval": intervalo,
            "limit": int(limit),
        }
    )
    url = f"{BYBIT_BASE}/v5/market/kline?{q}"
    data = _http_get_json(url)
    if int(data.get("retCode") or 0) != 0:
        raise RuntimeError(f"Bybit BTC kline: {data.get('retMsg')}")
    rows = list(data.get("result", {}).get("list") or [])
    # Bybit devuelve newest-first: [start, open, high, low, close, ...]
    rows.sort(key=lambda r: int(r[0]))
    closes = [float(r[4]) for r in rows if float(r[4]) > 0]
    if len(closes) < 5:
        raise RuntimeError("Bybit BTC: series demasiado corta")
    return closes


def fetch_alt_closes_bybit(
    symbol: str,
    *,
    intervalo: str = "D",
    limit: int = 35,
) -> list[float]:
    q = urllib.parse.urlencode(
        {
            "category": "linear",
            "symbol": symbol,
            "interval": intervalo,
            "limit": int(limit),
        }
    )
    url = f"{BYBIT_BASE}/v5/market/kline?{q}"
    data = _http_get_json(url)
    if int(data.get("retCode") or 0) != 0:
        raise RuntimeError(f"Bybit {symbol}: {data.get('retMsg')}")
    rows = list(data.get("result", {}).get("list") or [])
    rows.sort(key=lambda r: int(r[0]))
    return [float(r[4]) for r in rows if float(r[4]) > 0]


def build_total3_proxy_bybit(
    *,
    intervalo: str = "D",
    limit: int = 35,
    symbols: Sequence[str] | None = None,
) -> tuple[list[float], str]:
    """Índice equal-weight de alts (ex-BTC, ex-ETH) normalizado a 100 en t0.

    Proxy operativo de TOTAL3 cuando no hay serie CRYPTOCAP oficial gratis.
    """
    syms = list(symbols or TOTAL3_BYBIT_SYMBOLS)
    series: list[list[float]] = []
    used: list[str] = []
    errors: list[str] = []
    for sym in syms:
        try:
            closes = fetch_alt_closes_bybit(sym, intervalo=intervalo, limit=limit)
            if len(closes) >= 5:
                series.append(closes)
                used.append(sym)
            time.sleep(0.05)  # cortesía rate-limit
        except Exception as exc:  # noqa: BLE001 — acumular y seguir
            errors.append(f"{sym}:{exc}")
    if len(series) < 3:
        raise RuntimeError(
            "Bybit TOTAL3-proxy: menos de 3 alts útiles (" + "; ".join(errors[:5]) + ")"
        )
    n = min(len(s) for s in series)
    series = [s[-n:] for s in series]
    # equal-weight: media de precios rebased a 1.0 en la primera vela
    index: list[float] = []
    for i in range(n):
        acc = 0.0
        for s in series:
            base = s[0]
            acc += (s[i] / base) if base > 0 else 1.0
        index.append(100.0 * acc / len(series))
    detalle = f"bybit_ew_{len(used)}alts"
    return index, detalle


def fetch_total3_coingecko(
    *,
    days: int = 30,
) -> tuple[list[float], list[float], str]:
    """TOTAL3 = total_mcap − BTC_mcap − ETH_mcap (definición CRYPTOCAP).

    Requiere endpoint global chart (suele pedir API key). Devuelve
    (total3_levels, btc_prices, fuente).
    """
    hdrs = _coingecko_headers()
    days_s = str(max(7, int(days)))

    def _chart(coin_id: str) -> dict[str, Any]:
        url = (
            f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
            f"?vs_currency=usd&days={days_s}&interval=daily"
        )
        return _http_get_json(url, headers=hdrs)

    btc = _chart("bitcoin")
    eth = _chart("ethereum")
    btc_mc = {int(t): float(v) for t, v in (btc.get("market_caps") or []) if v}
    eth_mc = {int(t): float(v) for t, v in (eth.get("market_caps") or []) if v}
    btc_px = {int(t): float(v) for t, v in (btc.get("prices") or []) if v}

    url_g = f"{COINGECKO_BASE}/global/market_cap_chart?days={days_s}"
    global_chart = _http_get_json(url_g, headers=hdrs)
    # formas posibles: {"market_cap_chart":{"market_cap":[...]}} o lista directa
    raw = (
        (global_chart.get("market_cap_chart") or {}).get("market_cap")
        or global_chart.get("market_caps")
        or global_chart.get("market_cap")
        or []
    )
    if not raw:
        raise RuntimeError("CoinGecko global/market_cap_chart vacío o no autorizado")

    total3: list[float] = []
    btc_prices: list[float] = []
    for t, total in raw:
        ts = int(t)
        bm = btc_mc.get(ts)
        em = eth_mc.get(ts)
        # alinear por día si timestamps no coinciden exactos
        if bm is None or em is None:
            # buscar closest dentro de 36h
            bm = bm or _closest(btc_mc, ts)
            em = em or _closest(eth_mc, ts)
        if bm is None or em is None:
            continue
        level = float(total) - float(bm) - float(em)
        if level <= 0:
            continue
        px = btc_px.get(ts) or _closest(btc_px, ts)
        if px is None or px <= 0:
            continue
        total3.append(level)
        btc_prices.append(float(px))

    if len(total3) < 5:
        raise RuntimeError("CoinGecko TOTAL3: series demasiado corta tras alinear")
    return total3, btc_prices, "coingecko_total_minus_btc_eth"


def _closest(mp: dict[int, float], ts: int, max_delta_ms: int = 36 * 3600 * 1000) -> float | None:
    if not mp:
        return None
    best_k = min(mp.keys(), key=lambda k: abs(k - ts))
    if abs(best_k - ts) > max_delta_ms:
        return None
    return mp[best_k]


# --- Matemáticas ------------------------------------------------------------


def retornos_pct(levels: Sequence[float]) -> list[float]:
    """Retornos simples porcentuales r_t = (p_t / p_{t-1}) - 1."""
    out: list[float] = []
    for i in range(1, len(levels)):
        a, b = float(levels[i - 1]), float(levels[i])
        if a <= 0 or b <= 0:
            continue
        out.append((b / a) - 1.0)
    return out


def desviacion_estandar(xs: Sequence[float]) -> float:
    """Desviación estándar muestral (n-1)."""
    n = len(xs)
    if n < 2:
        return 0.0
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1)
    return math.sqrt(max(0.0, var))


def clamp_r(r_raw: float, *, lo: float = R_MIN, hi: float = R_MAX) -> float:
    return max(float(lo), min(float(hi), float(r_raw)))


def redondear_decima(x: float) -> float:
    """Redondeo a décima inmediata (mata fricción de ajuste)."""
    return round(float(x) + 1e-12, 1)


def aplicar_descuento_estrategico(
    r_crudo: float,
    *,
    descuento: float | None = None,
) -> tuple[float, float, float, float]:
    """Under-hedging con sesgo largo (Monarca).

    Returns:
        (r_vol, r_redondeado, r_final, r_crudo_usado)
    """
    desc = float(R_DESCUENTO_ESTRATEGICO if descuento is None else descuento)
    desc = max(0.0, min(1.0, desc))
    r_vol = clamp_r(float(r_crudo))
    r_red = redondear_decima(r_vol)
    r_final = max(R_MIN, r_red - desc)
    return r_vol, r_red, r_final, float(r_crudo)


def _align_tail(a: Sequence[float], b: Sequence[float]) -> tuple[list[float], list[float]]:
    n = min(len(a), len(b))
    if n < 5:
        raise RuntimeError("Series demasiado cortas para alinear")
    return list(a)[-n:], list(b)[-n:]


# --- API pública ------------------------------------------------------------


def calcular_r_detalle(
    *,
    ventana_dias: int = 30,
    intervalo: str = "D",
    preferir_coingecko: bool = False,
) -> RelacionR:
    """Calcula R_final con metadatos. Nunca lanza: ante error → R=1.0."""
    try:
        limit = max(10, int(ventana_dias) + 5)
        fuente_btc = "bybit_BTCUSDT"
        fuente_total3 = ""
        btc: list[float]
        total3: list[float]

        use_cg = preferir_coingecko or bool(
            os.getenv("COINGECKO_API_KEY")
            or os.getenv("CG_API_KEY")
            or os.getenv("X_CG_DEMO_API_KEY")
        )
        if use_cg:
            try:
                total3, btc, fuente_total3 = fetch_total3_coingecko(days=ventana_dias)
                fuente_btc = "coingecko_bitcoin"
            except Exception:
                use_cg = False

        if not use_cg:
            btc = fetch_btc_closes_bybit(intervalo=intervalo, limit=limit)
            total3, fuente_total3 = build_total3_proxy_bybit(
                intervalo=intervalo, limit=limit
            )
            btc, total3 = _align_tail(btc, total3)

        r_btc = retornos_pct(btc)
        r_t3 = retornos_pct(total3)
        r_btc, r_t3 = _align_tail(r_btc, r_t3)

        std_btc = desviacion_estandar(r_btc)
        std_t3 = desviacion_estandar(r_t3)
        if std_btc <= 1e-12:
            raise RuntimeError("std(BTC) ≈ 0 — no se puede dividir")

        r_crudo = std_t3 / std_btc
        r_vol, r_red, r_final, _ = aplicar_descuento_estrategico(r_crudo)
        return RelacionR(
            r=round(r_final, 6),
            r_raw=round(r_crudo, 6),
            r_vol=round(r_vol, 6),
            r_redondeado=round(r_red, 6),
            std_total3=round(std_t3, 8),
            std_btc=round(std_btc, 8),
            n_obs=len(r_btc),
            ventana_dias=int(ventana_dias),
            intervalo=str(intervalo),
            fuente_btc=fuente_btc,
            fuente_total3=fuente_total3,
            ok=True,
            detalle=(
                f"vol_clamp[{R_MIN},{R_MAX}] → décima → "
                f"max({R_MIN}, redondeado−{R_DESCUENTO_ESTRATEGICO})"
            ),
        )
    except Exception as exc:  # noqa: BLE001 — salvavidas producción
        return RelacionR(
            r=R_FALLBACK,
            r_raw=R_FALLBACK,
            r_vol=R_FALLBACK,
            r_redondeado=R_FALLBACK,
            std_total3=0.0,
            std_btc=0.0,
            n_obs=0,
            ventana_dias=int(ventana_dias),
            intervalo=str(intervalo),
            fuente_btc="",
            fuente_total3="",
            ok=False,
            detalle=f"fallback R={R_FALLBACK}: {type(exc).__name__}: {exc}",
        )


def calcular_r(
    *,
    ventana_dias: int = 30,
    intervalo: str = "D",
    preferir_coingecko: bool = False,
) -> float:
    """Atajo: R_final para Igris (1.0 si falla)."""
    return float(
        calcular_r_detalle(
            ventana_dias=ventana_dias,
            intervalo=intervalo,
            preferir_coingecko=preferir_coingecko,
        ).r
    )


if __name__ == "__main__":
    info = calcular_r_detalle(ventana_dias=30, intervalo="D")
    print(json.dumps(info.as_dict(), indent=2, ensure_ascii=False))
    print(f"\nR actual (clamp) = {info.r}")
