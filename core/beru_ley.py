"""Ley Beru — mega-cirugía 2026-08-13 (visión Monarca).

Beru = molino spot-margen: tres vidas (cazar / negociar / cosechar) + Mega.
No pregunta USDT. No descansa si hay manto. No planta futuros (Igris).
Engorde = engorde de Hoz en CAZA (por grado). No engorda el escudo Igris.
Manos/hilo OFF hasta orden (cirugía ≠ despertar).
"""
from __future__ import annotations

from typing import Any

import core.config as config


def engorde_permitido() -> bool:
    """Engorde de Hoz en caza (por peldaño de grado). Default ON tras cirugía 2026-08-13."""
    return bool(getattr(config, "BERU_ENGORDE_PERMITIDO", True))


def engorde_escudo_prohibido() -> bool:
    """Nunca engordar el manto/pase de Igris desde Beru."""
    return True


def neutro_margen() -> bool:
    """No restar oxígeno de Igris al registrar el intercambio."""
    return bool(getattr(config, "BERU_NEUTRO_MARGEN", True))


def abortar_solo_ceguera() -> bool:
    return bool(getattr(config, "BERU_ABORTAR_SOLO_CEGUERA", True))


def ceguera_coma_s() -> float:
    d = float(getattr(config, "TOLERANCIA_COMA_S", 15.0) or 15.0)
    return float(getattr(config, "BERU_CEGUERA_COMA_S", d) or d)


def spot_margen_activo() -> bool:
    return bool(getattr(config, "BERU_SPOT_MARGEN_ENABLED", True))


def spot_margen_leverage() -> int:
    return int(getattr(config, "BERU_SPOT_MARGEN_LEVERAGE", 10) or 10)


def nunca_descansa() -> bool:
    return True


def llamados_solo_detonan() -> bool:
    """Sangre / oro / tiempo: cero fill. Solo detonan la condicional ya armada."""
    return True


def consumir_auth_en_reserva() -> bool:
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


def masa_unidad_intercambio_usd(asset: str | None = None, grado: str | None = None) -> float:
    """Bocado inicial de caza = peldaños hasta Hoz × engorde del grado."""
    from core import beru_cazador as bc

    return float(bc.capa1_masa_usd(0.0, asset, grado))


def resumen_ley() -> dict[str, Any]:
    return {
        "engorde_permitido": engorde_permitido(),
        "engorde_escudo_prohibido": engorde_escudo_prohibido(),
        "neutro_margen": neutro_margen(),
        "abortar_solo_ceguera": abortar_solo_ceguera(),
        "ceguera_coma_s": ceguera_coma_s(),
        "consumir_auth": consumir_auth_en_reserva(),
        "spot_margen": spot_margen_activo(),
        "nunca_descansa": nunca_descansa(),
        "llamados_solo_detonan": llamados_solo_detonan(),
        "manos": bool(getattr(config, "BERU_MANOS", False)),
        "hilo": bool(getattr(config, "BERU_HILO_ENABLED", False)),
    }
