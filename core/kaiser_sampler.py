"""Muestreo Tank → Kaiser samples (perp vs index + aristas metaverso)."""
from __future__ import annotations

import time

import core.config as config
from core.kaiser_samples import append_sample


def _flota_manto() -> list[str]:
    """Activos Inverse∩Linear del diccionario Beru (ranking manto)."""
    from pathlib import Path
    import json

    path = Path(__file__).resolve().parents[1] / "config" / "diccionario_beru_flota_manto.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [str(x).upper() for x in ((data.get("meta") or {}).get("activos") or [])]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def _bases_prioritarias(tank) -> list[str]:
    penta = list(config.ACTIVOS_PENTIVERSO)
    trinidad = list(getattr(config, "ACTIVOS_TRINIDAD", []) or [])
    flota = _flota_manto()
    huerfanas = list(getattr(config, "ACTIVOS_HUERFANOS", []) or [])
    cap_h = getattr(config, "KAISER_SAMPLE_HUERFANAS_CAP", 60)
    top_desv = [r.get("base") for r in (tank.desvios_indice or [])[:20]]
    out: list[str] = []
    seen: set[str] = set()
    for b in flota + penta + trinidad + top_desv + huerfanas[:cap_h]:
        if not b:
            continue
        bu = str(b).upper()
        if bu not in seen:
            seen.add(bu)
            out.append(bu)
    return out


def muestrear_desde_tank(tank) -> int:
    lider = tank._obtener_lider_verde()
    if not lider:
        return 0
    px = lider.precios_con_reflejo()
    idx_map = lider.index_prices
    huerfanas = set(getattr(config, "ACTIVOS_HUERFANOS", []) or [])
    n = 0

    for base in _bases_prioritarias(tank):
        frente = f"{base}USDT_LINEAL"
        local = px.get(frente, 0.0)
        idx = idx_map.get(frente, 0.0)
        if local <= 0 or idx <= 0:
            continue
        signed = (local - idx) / idx * 100
        append_sample(
            base, "perp_vs_index",
            signed_pct=signed,
            huerfana=base in huerfanas,
            ref_tipo="index",
            extra={"precio_perp": local, "ref_global": idx},
        )
        n += 1

    flota_set = set(_flota_manto())
    penta_set = set(config.ACTIVOS_PENTIVERSO) | set(
        getattr(config, "ACTIVOS_TRINIDAD", []) or []
    )
    for row in tank.matriz_spreads or []:
        base = str(row.get("base", "")).upper()
        tipo = row.get("tipo", "")
        if not base or tipo not in (
            "spot_vs_perp", "lineal_vs_inverse", "usdt_vs_usdc",
            "perp_vs_index", "spot_vs_index",
        ):
            continue
        # lineal_vs_inverse: flota manto completa (frecuencia 4 umbrales)
        if tipo == "lineal_vs_inverse":
            if base not in flota_set and base not in penta_set:
                continue
        elif base not in penta_set:
            continue
        signed = float(row.get("desvio_signed_pct") or row.get("spread_pct") or 0)
        append_sample(
            base, tipo,
            signed_pct=signed,
            huerfana=base in huerfanas,
            ref_tipo="matriz",
        )
        n += 1

    return n


def muestrear_si_toca(tank, ultimo_muestra: float) -> tuple[int, float]:
    intervalo = getattr(config, "KAISER_SAMPLE_INTERVAL_S", 60.0)
    ahora = time.time()
    if ahora - ultimo_muestra < intervalo:
        return 0, ultimo_muestra
    return muestrear_desde_tank(tank), ahora
