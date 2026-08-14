"""Beru manos fantasma — nivel 2 ensayo (Monarca 2026-08-12).

Ojos reales Bybit · cerebro Beru late · CERO órdenes al exchange.
Cada disparo que habría sido market se imprime y se anexa a bitácora.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import core.config as config

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs" / "beru_fantasma" / "disparos.jsonl"


def activo() -> bool:
    """Manos de mentira: registra disparos, no place_order."""
    return bool(getattr(config, "BERU_MANOS_FANTASMA", False))


def activos_ensayo() -> list[str]:
    """Santos del manto a vigilar en el ritual (default ADA,BCH,MNT)."""
    raw = str(getattr(config, "BERU_FANTASMA_ACTIVOS", "") or "").strip()
    if not raw:
        raw = "ADA,BCH,MNT"
    out: list[str] = []
    for part in raw.split(","):
        u = part.strip().upper()
        if u and u not in out:
            out.append(u)
    return out


def ampliar_ojos_spot(activos: list[str] | None = None) -> list[str]:
    """Añade solo frentes spot a vigilancia Beru (ciego a lineal/inverso)."""
    acts = list(activos or activos_ensayo())
    frentes: list[str] = []
    for a in acts:
        for f in (f"{a}USDT_SPOT", f"{a}USDC_SPOT"):
            if f not in frentes:
                frentes.append(f)
    sem = str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH") or "ETH").upper()
    for f in (f"{sem}USDT_SPOT", f"{sem}USDC_SPOT"):
        if f not in frentes:
            frentes.insert(0, f)

    actuales = list(getattr(config, "FRENTES_BERU_VIGILANCIA", []) or [])
    for f in frentes:
        if f not in actuales:
            actuales.append(f)
    config.FRENTES_BERU_VIGILANCIA = actuales

    reso = list(getattr(config, "FRENTES_RESONANCIA_TANK", []) or [])
    for f in frentes:
        if f not in reso:
            reso.append(f)
    config.FRENTES_RESONANCIA_TANK = reso
    return frentes


def estrechar_ojos_bridge(activos: list[str] | None = None) -> list[str]:
    """Solo bases del ensayo en Bridge WS — sin trinidad completa ni libros.

    Sin esto el ritual abre ~11 shards / ~1390 tickers y el handshake muere
    (Tank ROJO, px=0, Beru ciego). Mismo patrón que arise_igris_sim.
    """
    acts = list(activos or activos_ensayo())
    seen: set[str] = set()
    bases: list[str] = []
    for a in acts:
        u = str(a or "").strip().upper()
        if u and u not in seen:
            seen.add(u)
            bases.append(u)
    # Semilla / ticker si no están ya (respaldo precio)
    for extra in (
        getattr(config, "BERU_ACTIVO_SEMILLA", None),
        getattr(config, "TICKER_BASE", None),
    ):
        u = str(extra or "").strip().upper()
        if u and u not in seen:
            seen.add(u)
            bases.append(u)
    config.BRIDGE_WS_BASES = bases
    config.BRIDGE_WS_SUBSCRIBE_BOOKS = False
    if hasattr(config, "BRIDGE_WS_BOOKS_BASES"):
        config.BRIDGE_WS_BOOKS_BASES = []
    return bases


def registrar(
    evento: str,
    *,
    detalle: str = "",
    **extra: Any,
) -> dict[str, Any]:
    """Imprime en consola + append jsonl. Nunca lanza (ensayo no debe morir por log)."""
    fila: dict[str, Any] = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "evento": str(evento),
        "detalle": str(detalle or ""),
        "fantasma": True,
    }
    for k, v in extra.items():
        if v is None:
            continue
        try:
            json.dumps(v)
            fila[k] = v
        except TypeError:
            fila[k] = str(v)

    linea = (
        f"[BERU_FANTASMA] {fila['iso']} · {evento}"
        + (f" · {detalle}" if detalle else "")
    )
    extras = {
        k: v
        for k, v in fila.items()
        if k not in ("ts", "iso", "evento", "detalle", "fantasma")
    }
    if extras:
        bits = []
        for k, v in extras.items():
            if isinstance(v, float):
                bits.append(f"{k}={v:.6g}" if abs(v) < 1e6 else f"{k}={v:.2f}")
            else:
                bits.append(f"{k}={v}")
        linea += " | " + " ".join(bits)
    print(linea, flush=True)

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return fila


def resumen_modo() -> dict[str, Any]:
    return {
        "manos_fantasma": activo(),
        "manos_reales": bool(getattr(config, "BERU_MANOS", False)),
        "hilo": bool(getattr(config, "BERU_HILO_ENABLED", False)),
        "sim": bool(getattr(config, "MODO_SIMULACION", True)),
        "activos_ensayo": activos_ensayo(),
        "log": str(LOG_PATH),
        "ley": "ojos reales · disparos solo bitácora · Igris no engorda",
    }
