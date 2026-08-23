#!/usr/bin/env python3
"""Fichas teatro: descripción LARGA en español (2–4 párrafos).

Bybit no publica esos párrafos en su API de instrumentos.
Fuentes: fichas propias + Wikipedia ES (+ CoinGecko ES si deja).

  python -u scripts/armar_santos_ficha_teatro.py
  python -u scripts/armar_santos_ficha_teatro.py --enrich

No toca juicios.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data" / "coliseo" / "rango_juicio" / "santos_ficha.json"
UA = "ShadowHarmyTeatro/1.2 (local lab; es)"

FICHAS_ES: dict[str, list[str]] = {
    "BTC": [
        "Bitcoin (BTC) es la primera criptomoneda: un sistema de dinero digital sin banco central, asegurado por minería y una cadena de bloques pública.",
        "Se usa como reserva de valor y referencia del mercado cripto; casi todo lo demás se compara contra BTC o contra el dólar.",
        "En Bybit se negocia el perpetuo lineal BTCUSDT (contrato sobre el precio de Bitcoin, liquidado en USDT).",
    ],
    "ETH": [
        "Ethereum (ETH) es una blockchain de código abierto pensada para contratos inteligentes y aplicaciones descentralizadas (DeFi, NFTs, DAOs).",
        "Ether es la moneda nativa: sirve para pagar gas (comisiones) y asegurar la red bajo proof-of-stake.",
        "En Bybit cotiza el perpetuo ETHUSDT, que sigue el precio de Ether sin entregar el activo on-chain.",
    ],
    "SOL": [
        "Solana (SOL) es una capa 1 rápida y de bajo costo, muy usada para DeFi, memes, NFTs y apps de consumo.",
        "Su token SOL paga comisiones y staking dentro del ecosistema.",
        "En Bybit se opera el perpetuo SOLUSDT.",
    ],
    "HYPE": [
        "Hyperliquid es un exchange descentralizado de futuros perpetuos, orientado a alta velocidad y libro de órdenes on-chain.",
        "HYPE es el token del ecosistema de ese protocolo; su precio refleja la narrativa y el uso de esa venue.",
        "En Bybit se negocia HYPEUSDT como perpetuo USDT lineal.",
    ],
    "BEAT": [
        "BEAT es un perpetuo cripto listado en Bybit (BEATUSDT). En el teatro de sombras reciente lideró métricas de zigzag/rango a plazos cortos.",
        "Como muchos listings nuevos, la narrativa del proyecto puede cambiar; conviene contrastar con el sitio oficial y el anuncio de Bybit.",
        "Aquí se trata como activo de alto rotación para el oficio Beru rango, no como blue-chip.",
    ],
    "ZRX": [
        "0x (ZRX) es un protocolo abierto para intercambiar tokens en Ethereum de persona a persona, usado por wallets y dApps.",
        "ZRX fue el token de utilidad/gobernanza de ese ecosistema de liquidez DEX.",
        "En Bybit aparece como perpetuo ZRXUSDT.",
    ],
    "WLD": [
        "Worldcoin (WLD) es el token ligado al proyecto World: identidad digital (World ID) y distribución asociada a verificación biométrica.",
        "Es controvertido por privacidad e inclusión; el mercado lo negocia como cripto de narrativa de identidad.",
        "En Bybit: perpetuo WLDUSDT.",
    ],
    "ONDO": [
        "Ondo Finance tokeniza activos del mundo real (RWA), acercando treasuries y productos financieros tradicionales a on-chain.",
        "ONDO es el token de gobernanza/ecosistema de ese protocolo.",
        "En Bybit se negocia ONDOUSDT.",
    ],
    "UNI": [
        "Uniswap es el exchange descentralizado más grande de Ethereum; UNI es su token de gobernanza.",
        "No es un pago del swap en sí: sirve para votar cambios del protocolo y la tesorería.",
        "En Bybit: perpetuo UNIUSDT.",
    ],
    "AAVE": [
        "Aave es un protocolo DeFi de préstamos y depósitos sin intermediario bancario.",
        "AAVE gobierna parámetros de riesgo y el futuro del protocolo.",
        "En Bybit: perpetuo AAVEUSDT.",
    ],
    "LIT": [
        "LIT es el listing que el ejército usó como laboratorio de Beru rango (ojos) para validar la doctrina de nacimiento $5 y Red.",
        "Verifica siempre el proyecto detrás del ticker en el anuncio de Bybit; varios tokens comparten nombres cortos.",
        "En Bybit se negocia el perpetuo LITUSDT.",
    ],
    "AAPL": [
        "Apple Inc. es la compañía de iPhone, Mac, servicios y ecosistema de hardware/software.",
        "En Bybit no compras la acción en un broker clásico: operas un perpetuo TradeFi AAPLUSDT que sigue el precio de la acción.",
    ],
    "TSLA": [
        "Tesla es el fabricante de autos eléctricos y sistemas de energía; su acción es muy seguida por traders de crecimiento.",
        "En Bybit se negocia como perpetuo TradeFi TSLAUSDT.",
    ],
    "XAU": [
        "XAU representa el precio del oro (commodity de refugio y reserva).",
        "En Bybit es un perpetuo TradeFi XAUUSDT: exposición al precio del oro liquidada en USDT.",
    ],
    "XAG": [
        "XAG representa el precio de la plata.",
        "En Bybit se opera como perpetuo TradeFi XAGUSDT.",
    ],
    "NVDA": [
        "NVIDIA diseña GPUs usadas en gaming, centros de datos e inteligencia artificial.",
        "En Bybit cotiza el perpetuo TradeFi NVDAUSDT sobre la acción.",
    ],
    "MSTR": [
        "MicroStrategy es una empresa de software conocida por acumular grandes tenencias de Bitcoin en balance.",
        "Muchos la usan como proxy de BTC; en Bybit es el perpetuo TradeFi MSTRUSDT.",
    ],
    "LINK": [
        "Chainlink (LINK) es una red de oráculos: lleva datos del mundo real a contratos inteligentes on-chain.",
        "LINK es el token que incentiva a los nodos que alimentan esos feeds de precios y datos.",
        "En Bybit se negocia el perpetuo LINKUSDT.",
    ],
    "XRP": [
        "XRP es el token nativo de la red XRPL, orientada a pagos y liquidación rápida entre instituciones.",
        "A diferencia de muchas L1 de smart contracts, su narrativa gira en torno a remesas y rails de pago.",
        "En Bybit cotiza el perpetuo XRPUSDT.",
    ],
    "DOGE": [
        "Dogecoin (DOGE) nació como moneda meme con el perro Shiba; la comunidad la convirtió en medio de propinas y especulación.",
        "Sigue siendo uno de los activos más líquidos y reconocidos del mercado cripto.",
        "En Bybit: perpetuo DOGEUSDT.",
    ],
    "ADA": [
        "Cardano (ADA) es una blockchain de capa 1 orientada a investigación académica y contratos inteligentes.",
        "ADA paga comisiones y staking dentro de esa red.",
        "En Bybit se opera ADAUSDT.",
    ],
    "AVAX": [
        "Avalanche (AVAX) es una plataforma de blockchains rápidas (subnets) para DeFi y apps empresariales.",
        "AVAX es el token de gas y seguridad del ecosistema.",
        "En Bybit: perpetuo AVAXUSDT.",
    ],
    "DOT": [
        "Polkadot (DOT) conecta blockchains especializadas (parachains) bajo un relay chain compartido.",
        "DOT se usa para staking, gobernanza y unir ranuras de parachain.",
        "En Bybit: perpetuo DOTUSDT.",
    ],
    "ARB": [
        "Arbitrum (ARB) es una red de capa 2 sobre Ethereum: más barata y rápida, con herencia de seguridad de L1.",
        "ARB es el token de gobernanza del ecosistema Arbitrum.",
        "En Bybit: perpetuo ARBUSDT.",
    ],
    "OP": [
        "Optimism (OP) es otra capa 2 de Ethereum basada en rollups optimistas.",
        "OP gobierna el ecosistema Superchain / Optimism Collective.",
        "En Bybit: perpetuo OPUSDT.",
    ],
    "PEPE": [
        "PEPE es un token meme inspirado en la rana Pepe; su precio se mueve sobre todo por narrativa y liquidez.",
        "No pretende ser infraestructura DeFi: es especulación de comunidad.",
        "En Bybit: perpetuo PEPEUSDT.",
    ],
    "LTC": [
        "Litecoin (LTC) es una de las criptomonedas más antiguas, derivada del código de Bitcoin con bloques más rápidos.",
        "Se usa como medio de pago y como activo ‘hermano’ histórico de BTC.",
        "En Bybit: perpetuo LTCUSDT.",
    ],
    "BCH": [
        "Bitcoin Cash (BCH) es un fork de Bitcoin orientado a bloques más grandes y pagos cotidianos.",
        "Comparte historia con BTC pero diverge en reglas de consenso y tamaño de bloque.",
        "En Bybit: perpetuo BCHUSDT.",
    ],
    "NEAR": [
        "NEAR Protocol es una capa 1 pensada para usabilidad (cuentas legibles) y shards de escalado.",
        "NEAR es el token de gas y staking de esa red.",
        "En Bybit: perpetuo NEARUSDT.",
    ],
    "SUI": [
        "Sui es una blockchain de alto rendimiento basada en el lenguaje Move, orientada a apps y juegos.",
        "SUI paga gas y participa en el staking del protocolo.",
        "En Bybit: perpetuo SUIUSDT.",
    ],
    "APT": [
        "Aptos es otra L1 en Move, nacida del ecosistema Diem/Libra, enfocada en throughput y seguridad.",
        "APT es su token nativo de gas y gobernanza.",
        "En Bybit: perpetuo APTUSDT.",
    ],
    "FIL": [
        "Filecoin (FIL) es una red de almacenamiento descentralizado: pagas por guardar datos en nodos de la red.",
        "FIL incentiva a proveedores de espacio y recupera archivos on-chain.",
        "En Bybit: perpetuo FILUSDT.",
    ],
    "ATOM": [
        "Cosmos (ATOM) es el ecosistema de blockchains interoperables vía IBC (Inter-Blockchain Communication).",
        "ATOM es el token del Hub Cosmos y de su seguridad compartida.",
        "En Bybit: perpetuo ATOMUSDT.",
    ],
    "TRX": [
        "TRON (TRX) es una blockchain popular para stablecoins y transferencia de valor a bajo costo.",
        "TRX paga energía/ancho de banda en esa red.",
        "En Bybit: perpetuo TRXUSDT.",
    ],
    "SHIB": [
        "Shiba Inu (SHIB) es un token meme del ecosistema Ethereum, con comunidad amplia y proyectos satélite.",
        "Como otros memes, el precio depende más de atención que de flujos fundamentales.",
        "En Bybit: perpetuo SHIBUSDT.",
    ],
    "CRV": [
        "Curve (CRV) es un DEX DeFi especializado en pools de stablecoins y activos correlacionados.",
        "CRV gobierna emisiones y parámetros del protocolo.",
        "En Bybit: perpetuo CRVUSDT.",
    ],
    "LDO": [
        "Lido (LDO) es el mayor protocolo de staking líquido de Ethereum (stETH).",
        "LDO gobierna el DAO que administra nodos y fees.",
        "En Bybit: perpetuo LDOUSDT.",
    ],
    "MNT": [
        "Mantle (MNT) es el token del ecosistema Mantle, una capa 2 / modular ligada a Bybit históricamente.",
        "Se usa en gobernanza y gas dentro de esa red.",
        "En Bybit: perpetuo MNTUSDT.",
    ],
}


def _http_json(url: str, timeout: float = 45.0) -> Any:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _clean(text: str) -> str:
    t = re.sub(r"<[^>]+>", " ", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _parece_ingles(text: str) -> bool:
    t = (text or "").lower()
    if not t:
        return False
    eng = sum(
        1
        for w in (" the ", " and ", " is ", " of ", " with ", " for ", " on ", " that ")
        if w in f" {t} "
    )
    esp = sum(
        1
        for w in (" de ", " la ", " el ", " en ", " que ", " para ", " con ", " una ", " los ")
        if w in f" {t} "
    )
    return eng >= 2 and eng > esp


def _paras_from_text(text: str, max_paras: int = 4) -> list[str]:
    t = _clean(text)
    if not t:
        return []
    parts = [p.strip() for p in re.split(r"\n{2,}", t) if p.strip()]
    if len(parts) == 1:
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", parts[0]) if s.strip()]
        if len(sents) <= 2:
            parts = [" ".join(sents)] if sents else []
        else:
            mid = max(1, len(sents) // 2)
            parts = [" ".join(sents[:mid]), " ".join(sents[mid:])]
    out: list[str] = []
    for p in parts:
        if len(p) > 560:
            p = p[:557].rsplit(" ", 1)[0] + "…"
        out.append(p)
        if len(out) >= max_paras:
            break
    return out


def _bybit_rows() -> list[dict[str, Any]]:
    from pybit.unified_trading import HTTP

    session = HTTP(testnet=False)
    out: list[dict[str, Any]] = []
    cursor = ""
    seen: set[str] = set()
    for _ in range(20):
        kwargs: dict[str, Any] = {"category": "linear", "limit": 1000}
        if cursor:
            kwargs["cursor"] = cursor
        resp = session.get_instruments_info(**kwargs)
        lst = (resp.get("result") or {}).get("list") or []
        cursor = str((resp.get("result") or {}).get("nextPageCursor") or "")
        for row in lst:
            if row.get("status") != "Trading":
                continue
            if row.get("contractType") not in ("LinearPerpetual",):
                continue
            if str(row.get("quoteCoin") or "").upper() != "USDT":
                continue
            base = str(row.get("baseCoin") or "").upper()
            if not base or base in seen:
                continue
            seen.add(base)
            sym_type = str(row.get("symbolType") or "crypto").lower() or "crypto"
            out.append(
                {
                    "base": base,
                    "symbol": str(row.get("symbol") or f"{base}USDT"),
                    "display_name": str(row.get("displayName") or base),
                    "symbol_type": sym_type,
                    "tradefi": sym_type in ("stock", "commodity", "fx", "forex"),
                    "max_leverage": str(
                        (row.get("leverageFilter") or {}).get("maxLeverage") or ""
                    ),
                }
            )
        if not cursor or not lst:
            break
        time.sleep(0.08)
    return out


def _wiki_es_summary(title: str) -> str:
    if not title:
        return ""
    url = (
        "https://es.wikipedia.org/api/rest_v1/page/summary/"
        + urllib.parse.quote(title.replace(" ", "_"))
    )
    try:
        data = _http_json(url, timeout=20)
    except Exception:
        return ""
    if data.get("type") == "disambiguation":
        return ""
    extract = _clean(str(data.get("extract") or ""))
    if not extract or _parece_ingles(extract):
        return ""
    return extract


def _wiki_es_search(query: str) -> str:
    """Busca título en Wikipedia ES y devuelve el summary del mejor hit."""
    q = (query or "").strip()
    if not q:
        return ""
    url = (
        "https://es.wikipedia.org/w/api.php?action=query&list=search"
        f"&srsearch={urllib.parse.quote(q)}&srlimit=5&format=json"
    )
    try:
        data = _http_json(url, timeout=20)
    except Exception:
        return ""
    hits = ((data.get("query") or {}).get("search")) or []
    for hit in hits:
        title = str(hit.get("title") or "")
        extract = _wiki_es_summary(title)
        if extract:
            return extract
    return ""


def _wiki_es(title: str, *, strict: bool = True, fallback_query: str = "") -> str:
    extract = _wiki_es_summary(title)
    if not extract and fallback_query:
        extract = _wiki_es_search(fallback_query)
    if not extract:
        return ""
    if strict:
        low = extract.lower()
        hints = (
            "cripto",
            "bitcoin",
            "ethereum",
            "blockchain",
            "token",
            "empresa",
            "compañía",
            "protocolo",
            "red ",
            "moneda",
            "oro",
            "plata",
            "acción",
            "software",
            "exchange",
            "finanzas",
            "plataforma",
            "caden",
            "criptomoneda",
            "bolsa",
            "financ",
        )
        if not any(h in low for h in hints):
            return ""
    return extract


def _parrafo_bybit(nombre: str, base: str, symbol: str, sym_type: str, tradefi: bool) -> str:
    if tradefi or sym_type in ("stock", "commodity", "fx", "forex", "etf"):
        return (
            f"En Bybit, {nombre} ({base}) se negocia como perpetuo TradeFi {symbol} "
            f"(tipo {sym_type}). No es un token on-chain típico: el precio sigue el "
            "activo tradicional bajo las reglas del exchange, liquidado en USDT."
        )
    return (
        f"En Bybit, {nombre} ({base}) cotiza como perpetuo lineal {symbol}. "
        "La API de instrumentos solo da datos técnicos; esta descripción del "
        "proyecto está en español a partir de fichas públicas."
    )


def _build_es(
    *,
    base: str,
    nombre: str,
    symbol: str,
    sym_type: str,
    tradefi: bool,
    wiki: str,
    tags_es_hint: str = "",
) -> list[str]:
    if base in FICHAS_ES:
        paras = list(FICHAS_ES[base])
        if not any("Bybit" in p for p in paras):
            paras.append(_parrafo_bybit(nombre, base, symbol, sym_type, tradefi))
        return paras[:4]

    paras: list[str] = []
    for p in _paras_from_text(wiki, 3):
        if p and not _parece_ingles(p):
            paras.append(p)

    if not paras:
        if tradefi or sym_type in ("stock", "commodity", "etf"):
            paras.append(
                f"{nombre} ({base}) es un activo tradicional (TradeFi) listado en Bybit "
                f"como perpetuo {symbol}."
            )
        else:
            paras.append(
                f"{nombre} ({base}) es un proyecto cripto/token con ticker {base}. "
                f"En Bybit el contrato perpetuo es {symbol}."
            )

    if tags_es_hint and len(paras) < 3:
        paras.append(tags_es_hint)

    bybit_p = _parrafo_bybit(nombre, base, symbol, sym_type, tradefi)
    if bybit_p not in paras:
        paras.append(bybit_p)
    return paras[:4]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enrich", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--limit-enrich", type=int, default=0)
    args = ap.parse_args()

    print("Armando fichas en ESPAÑOL…", flush=True)
    bybit = _bybit_rows()

    prev: dict[str, Any] = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8")).get("por_base") or {}
        except Exception:
            prev = {}

    por_base: dict[str, Any] = {}
    for row in bybit:
        base = row["base"]
        old = prev.get(base) or {}
        nombre = str(old.get("nombre") or row["display_name"] or base)

        if base in FICHAS_ES:
            paras = _build_es(
                base=base,
                nombre=nombre,
                symbol=row["symbol"],
                sym_type=row["symbol_type"],
                tradefi=row["tradefi"],
                wiki="",
            )
            fuente = "ejercito_es"
        else:
            paras = old.get("parrafos") if isinstance(old.get("parrafos"), list) else []
            if paras and _parece_ingles(" ".join(map(str, paras))):
                paras = []
            if not paras:
                paras = _build_es(
                    base=base,
                    nombre=nombre,
                    symbol=row["symbol"],
                    sym_type=row["symbol_type"],
                    tradefi=row["tradefi"],
                    wiki="",
                )
            fuente = str(old.get("fuente") or "base_es")
            if not str(fuente).endswith("_es") and not str(fuente).startswith("wiki"):
                fuente = "base_es"

        por_base[base] = {
            **row,
            "nombre": nombre,
            "idioma": "es",
            "parrafos": paras,
            "descripcion": "\n\n".join(paras),
            "blurb": "\n\n".join(paras),
            "paprika_id": old.get("paprika_id") or "",
            "coingecko_id": old.get("coingecko_id") or "",
            "fuente": fuente,
        }

    def _save(extra: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "idioma": "es",
            "n": len(por_base),
            "nota": "Descripciones en español · 2–4 párrafos · campo parrafos[].",
            "por_base": por_base,
        }
        if extra:
            payload.update(extra)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _save()
    print(f"OK base ES {len(por_base)} → {OUT}", flush=True)
    if not args.enrich:
        return 0

    wiki_map = {
        "AAPL": "Apple",
        "TSLA": "Tesla_(empresa)",
        "NVDA": "Nvidia",
        "AMZN": "Amazon",
        "META": "Meta_Platforms",
        "GOOGL": "Alphabet_Inc.",
        "MSFT": "Microsoft",
        "COIN": "Coinbase",
        "MSTR": "MicroStrategy",
        "XAU": "Oro",
        "XAG": "Plata",
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "SOL": "Solana",
        "ADA": "Cardano",
        "DOT": "Polkadot",
        "AVAX": "Avalanche",
        "LINK": "Chainlink",
        "UNI": "Uniswap",
        "AAVE": "Aave",
        "XRP": "XRP",
        "DOGE": "Dogecoin",
        "LTC": "Litecoin",
        "BCH": "Bitcoin Cash",
        "ETC": "Ethereum Classic",
        "FIL": "Filecoin",
        "ATOM": "Cosmos",
        "NEAR": "NEAR Protocol",
        "APT": "Aptos",
        "SUI": "Sui",
        "ARB": "Arbitrum",
        "OP": "Optimism",
        "PEPE": "Pepe",
        "SHIB": "Shiba Inu",
        "TRX": "TRON",
        "SAND": "The Sandbox",
        "MANA": "Decentraland",
        "AXS": "Axie Infinity",
        "CRV": "Curve Finance",
        "LDO": "Lido",
        "STX": "Stacks",
        "STRK": "Starknet",
        "TIA": "Celestia",
        "INJ": "Injective",
        "SEI": "Sei",
        "RENDER": "Render Network",
        "TAO": "Bittensor",
        "JUP": "Jupiter",
        "PYTH": "Pyth Network",
        "ENA": "Ethena",
        "W": "Wormhole",
        "ZRO": "LayerZero",
        "HYPE": "Hyperliquid",
        "ONDO": "Ondo Finance",
        "WLD": "Worldcoin",
        "ZRX": "0x",
    }

    pendientes = list(por_base.keys())
    prioridad: list[str] = []
    # Primero títulos con mapa Wikipedia (para no gastar el cupo en memes sin ficha).
    prioridad.extend(list(wiki_map.keys()))
    prioridad.extend(list(FICHAS_ES))
    top_path = ROOT / "data/coliseo/rango_juicio/matriz/normal_reciente/checkpoint_parcial.json"
    if top_path.exists():
        try:
            ranking = json.loads(top_path.read_text(encoding="utf-8")).get("ranking") or []
            prioridad.extend([str(r.get("activo") or "").upper() for r in ranking[:200]])
        except Exception:
            pass
    seen: set[str] = set()
    orden: list[str] = []
    for b in prioridad + pendientes:
        if b in por_base and b not in seen:
            orden.append(b)
            seen.add(b)
    pendientes = orden
    if args.limit_enrich > 0:
        pendientes = pendientes[: int(args.limit_enrich)]

    print(f"Enrich ES: {len(pendientes)}…", flush=True)
    ok = 0
    for i, base in enumerate(pendientes, 1):
        row = por_base[base]
        if base in FICHAS_ES:
            if i % 25 == 0:
                _save({"enrich_progress": {"hecho": i, "total": len(pendientes), "con_texto": ok}})
            continue

        ya = row.get("parrafos") or []
        if (
            len(ya) >= 2
            and not _parece_ingles(" ".join(map(str, ya)))
            and len(str(row.get("descripcion") or "")) >= 260
            and "wiki_es" in str(row.get("fuente") or "")
        ):
            continue

        title = wiki_map.get(base) or str(row.get("nombre") or base)
        query = f"{title} criptomoneda" if not row.get("tradefi") else title
        wiki = _wiki_es(
            title,
            strict=not bool(row.get("tradefi")),
            fallback_query=query if base not in wiki_map else "",
        )
        # Si el mapa falló, intentar búsqueda libre en español.
        if not wiki and base in wiki_map:
            wiki = _wiki_es_search(f"{wiki_map[base]} criptomoneda") or _wiki_es_search(
                wiki_map[base]
            )
            if wiki and _parece_ingles(wiki):
                wiki = ""
        tags_hint = ""
        if row.get("symbol_type") == "innovation":
            tags_hint = (
                "Bybit lo clasifica en zona innovation: listings más nuevos, "
                "suele haber más volatilidad y menos profundidad de libro."
            )
        # No pisar fichas del ejército; para el resto preferir wiki si llegó.
        if base in FICHAS_ES:
            paras = _build_es(
                base=base,
                nombre=str(row.get("nombre") or base),
                symbol=str(row.get("symbol") or f"{base}USDT"),
                sym_type=str(row.get("symbol_type") or "crypto"),
                tradefi=bool(row.get("tradefi")),
                wiki="",
            )
            fuente = "ejercito_es"
        else:
            paras = _build_es(
                base=base,
                nombre=str(row.get("nombre") or base),
                symbol=str(row.get("symbol") or f"{base}USDT"),
                sym_type=str(row.get("symbol_type") or "crypto"),
                tradefi=bool(row.get("tradefi")),
                wiki=wiki,
                tags_es_hint=tags_hint,
            )
            fuente = "wiki_es" if wiki else "plantilla_es"
        row["parrafos"] = paras
        row["descripcion"] = "\n\n".join(paras)
        row["blurb"] = row["descripcion"]
        row["idioma"] = "es"
        row["fuente"] = fuente
        if wiki and base not in FICHAS_ES:
            ok += 1
        por_base[base] = row

        if i % 15 == 0 or i == len(pendientes):
            _save({"enrich_progress": {"hecho": i, "total": len(pendientes), "con_texto": ok}})
            print(f"  [{i}/{len(pendientes)}] es_ok={ok}", flush=True)
        time.sleep(max(0.2, float(args.sleep)))

    print(f"OK enrich ES · {ok}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
