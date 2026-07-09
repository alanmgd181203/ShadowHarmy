"""Toques Greed en frentes del manto — evita rebalanceo falso en Igris."""
from __future__ import annotations

import time
from typing import Any

import core.config as config


def frente_es_manto(frente: str) -> bool:
    return str(frente) in (getattr(config, "FRENTES_MANTO_ALL", None) or [])


def registrar_toque_greed(tusk, frentes: list[str], motivo: str = "ARBITRAJE") -> None:
    """Marca frentes del manto tocados por Greed (Igris no rebalancea de inmediato)."""
    if not hasattr(tusk, "toques_greed_manto") or tusk.toques_greed_manto is None:
        tusk.toques_greed_manto = {}
    ahora = time.time()
    for f in frentes:
        if frente_es_manto(f):
            tusk.toques_greed_manto[f] = {"ts": ahora, "motivo": motivo}


def snapshot_toques(tusk) -> dict[str, Any]:
    raw = getattr(tusk, "toques_greed_manto", None) or {}
    cooldown = float(getattr(config, "GREED_MANTO_TOQUE_COOLDOWN_S", 45.0))
    ahora = time.time()
    activos = []
    for frente, meta in raw.items():
        edad = ahora - float(meta.get("ts", 0))
        if edad <= cooldown:
            activos.append({
                "frente": frente,
                "edad_s": round(edad, 1),
                "motivo": meta.get("motivo", "?"),
            })
    return {"activos": activos, "cooldown_s": cooldown}


def rebalanceo_en_pausa_por_greed(tusk) -> bool:
    """True si algún frente manto fue tocado por Greed recientemente."""
    return bool(snapshot_toques(tusk).get("activos"))


def limpiar_toques_expirados(tusk) -> None:
    raw = getattr(tusk, "toques_greed_manto", None) or {}
    if not raw:
        return
    cooldown = float(getattr(config, "GREED_MANTO_TOQUE_COOLDOWN_S", 45.0))
    ahora = time.time()
    tusk.toques_greed_manto = {
        f: m for f, m in raw.items()
        if (ahora - float(m.get("ts", 0))) <= cooldown
    }
