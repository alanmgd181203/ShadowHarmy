"""Ley Beru — visión original (mega-cirugía 2026-08-12).

Beru es el molino: spot margen al máximo, transmuta USDT ↔ Santo.
No pregunta si hay USDT. No descansa mientras haya manto.
No planta futuros (eso es Igris). No engorda el escudo.

Spot margen ON = permiso de Bybit cuando el mantenimiento ya está feo.
La caja USDT la pone Tusk/Monarca — Beru no la chequea.
Manos/hilo: OFF hasta orden (cirugía ≠ despertar).
"""
from __future__ import annotations

from typing import Any

import core.config as config


def engorde_permitido() -> bool:
    """No sumar capas / +G_min al manto. El molino recicla, no engorda escudo."""
    return bool(getattr(config, "BERU_ENGORDE_PERMITIDO", False))


def neutro_margen() -> bool:
    """No restar oxígeno de Igris al registrar el intercambio."""
    return bool(getattr(config, "BERU_NEUTRO_MARGEN", True))


def abortar_solo_ceguera() -> bool:
    return bool(getattr(config, "BERU_ABORTAR_SOLO_CEGUERA", True))


def ceguera_coma_s() -> float:
    d = float(getattr(config, "TOLERANCIA_COMA_S", 15.0) or 15.0)
    return float(getattr(config, "BERU_CEGUERA_COMA_S", d) or d)


def spot_margen_activo() -> bool:
    """Permiso Bybit para transmutar con ocupación/mantenimiento altos."""
    return bool(getattr(config, "BERU_SPOT_MARGEN_ENABLED", True))


def spot_margen_leverage() -> int:
    return int(getattr(config, "BERU_SPOT_MARGEN_LEVERAGE", 10) or 10)


def nunca_descansa() -> bool:
    """Hay manto → Beru patrulla. No hiberna por oxígeno del escudo."""
    return True


def consumir_auth_en_reserva() -> bool:
    """Neutro: no restar masa_autorizada de Igris."""
    if neutro_margen():
        return False
    return True


def debe_abortar_por_vision(
    estado_vision: str | None,
    ctx_map: dict | None,
    *,
    precio_casa: float = 0.0,
    tank=None,
) -> tuple[bool, str]:
    """True = abortar caza.

    Solo ciego de verdad (sin precio / coma). ROJO con precio vivo → sigue.
    No abortar por 'no hay margen de Igris'.
    """
    if precio_casa is not None and float(precio_casa or 0) <= 0:
        return True, "sin_precio_casa"
    if not ctx_map:
        if abortar_solo_ceguera() and float(precio_casa or 0) > 0:
            pass
        else:
            return True, "sin_vision"
    if tank is not None and _tank_en_coma(tank):
        return True, "tank_coma"

    est = str(estado_vision or "")
    if abortar_solo_ceguera():
        if est in ("GLITCH_DETECTADO",) and float(precio_casa or 0) <= 0:
            return True, "glitch_sin_precio"
        return False, "ok"
    if est in ("GLITCH_DETECTADO", "ROJO"):
        return True, f"vision_{est.lower()}"
    return False, "ok"


def _tank_en_coma(tank) -> bool:
    import time

    nodos = list(getattr(tank, "nodos", None) or [])
    if not nodos:
        return False
    ahora = time.time()
    lim = ceguera_coma_s()
    vivos = 0
    for n in nodos:
        edad = ahora - float(getattr(n, "ultima_actualizacion", 0) or 0)
        if edad > lim:
            continue
        vivos += 1
    return vivos == 0


def masa_unidad_intercambio_usd(asset: str | None = None) -> float:
    """Bocado del molino (G_min) — no es engorde de margen."""
    from core import beru_cazador as bc

    return float(bc.mordida_usd(asset))


def resumen_ley() -> dict[str, Any]:
    return {
        "engorde_permitido": engorde_permitido(),
        "neutro_margen": neutro_margen(),
        "abortar_solo_ceguera": abortar_solo_ceguera(),
        "ceguera_coma_s": ceguera_coma_s(),
        "consumir_auth": consumir_auth_en_reserva(),
        "spot_margen": spot_margen_activo(),
        "spot_margen_lev": spot_margen_leverage(),
        "nunca_descansa": nunca_descansa(),
        "manos": bool(getattr(config, "BERU_MANOS", False)),
        "hilo": bool(getattr(config, "BERU_HILO_ENABLED", False)),
        "ley": (
            "Beru: molino spot-margen · no descansa si hay manto · "
            "no pregunta USDT · no engorda Igris · aborta solo si ciego · "
            "manos OFF hasta orden"
        ),
    }
