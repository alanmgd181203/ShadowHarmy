"""Ley Beru — Monarca 2026-08-11 (códice).

Beru NO toca margen / NO engorda el manto.
Solo intercambia en spot lo que una pierna gana por lo que la otra pierde.
Abortar caza solo si está ciego (sin precio / coma larga), no por ROJO ligero de Tank.
"""
from __future__ import annotations

from typing import Any

import core.config as config


def engorde_permitido() -> bool:
    """Default OFF — frontera/+G_min/clon de masa = prohibido en vivo doctrinal."""
    return bool(getattr(config, "BERU_ENGORDE_PERMITIDO", False))


def neutro_margen() -> bool:
    """0% margen extra: no consumir masa_autorizada (oxígeno Igris) ni sumar IM."""
    return bool(getattr(config, "BERU_NEUTRO_MARGEN", True))


def abortar_solo_ceguera() -> bool:
    return bool(getattr(config, "BERU_ABORTAR_SOLO_CEGUERA", True))


def ceguera_coma_s() -> float:
    """Segundos sin update = red caída / coma (default = TOLERANCIA_COMA Tank)."""
    d = float(getattr(config, "TOLERANCIA_COMA_S", 15.0) or 15.0)
    return float(getattr(config, "BERU_CEGUERA_COMA_S", d) or d)


def consumir_auth_en_reserva() -> bool:
    """Si neutro margen → no restar oxígeno Tusk al registrar intercambio spot."""
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

    Con abortar_solo_ceguera: solo sin precio usable / coma / sin ctx.
    Sin flag: legado ROJO/GLITCH aborta.
    """
    if precio_casa is not None and float(precio_casa or 0) <= 0:
        return True, "sin_precio_casa"
    if not ctx_map:
        # Aún puede haber precio_casa; sin mapa rail falla → ciego operativo
        if abortar_solo_ceguera() and float(precio_casa or 0) > 0:
            # Permitir si hay ticker; rail usará lo que pueda
            pass
        else:
            return True, "sin_vision"
    if tank is not None and _tank_en_coma(tank):
        return True, "tank_coma"

    est = str(estado_vision or "")
    if abortar_solo_ceguera():
        if est in ("GLITCH_DETECTADO",) and float(precio_casa or 0) <= 0:
            return True, "glitch_sin_precio"
        # ROJO / AMARILLO / GLITCH con precio vivo → NO abortar
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
    # Solo edad: CONGELADO con update fresco (muleta REST) no es ceguera.
    vivos = 0
    for n in nodos:
        edad = ahora - float(getattr(n, "ultima_actualizacion", 0) or 0)
        if edad > lim:
            continue
        vivos += 1
    return vivos == 0


def masa_unidad_intercambio_usd(asset: str | None = None) -> float:
    """Tamaño mínimo del intercambio spot (G_min) — NO es engorde de margen."""
    from core import beru_cazador as bc

    return float(bc.mordida_usd(asset))


def resumen_ley() -> dict[str, Any]:
    return {
        "engorde_permitido": engorde_permitido(),
        "neutro_margen": neutro_margen(),
        "abortar_solo_ceguera": abortar_solo_ceguera(),
        "ceguera_coma_s": ceguera_coma_s(),
        "consumir_auth": consumir_auth_en_reserva(),
        "manos": bool(getattr(config, "BERU_MANOS", False)),
        "hilo": bool(getattr(config, "BERU_HILO_ENABLED", False)),
        "ley": (
            "Beru: 0% margen extra · solo intercambio spot pierna↔pierna · "
            "sin engorde · aborta solo si ciego (coma/sin precio)"
        ),
    }
