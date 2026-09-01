"""Semáforo rojo/amarillo/verde + bando de pierna (paz/medio/pesado) — Beru piedra."""
from __future__ import annotations

import os
from typing import Any

import core.config as config


def semaforo_normalizado(color: str | None) -> str:
    c = str(color or os.getenv("BERU_RANGO_SEMAFORO", "amarillo") or "amarillo").strip().lower()
    if c in ("rojo", "r", "red", "cenido", "ceñido"):
        return "rojo"
    if c in ("verde", "v", "green", "ancho", "wide"):
        return "verde"
    if c in ("amarillo", "a", "yellow", "medio", "medium", "default"):
        return "amarillo"
    return "amarillo"


def _mapa_semaforo() -> dict[str, dict[str, float]]:
    return getattr(config, "BERU_RANGO_SEMAFORO_MAPA", {}) or {}


def semaforo_resuelto(activo: str | None, beru: Any | None = None) -> str:
    """Color del Santo: JSON asignación > env BERU_RANGO_SEMAFORO > amarillo."""
    from core import beru_rango as br

    base = str(activo or br.activo_desde_beru(beru) or "").upper()
    if base:
        row = (br._piedra_asignacion().get("activos") or {}).get(base)
        if row:
            if isinstance(row, dict):
                raw = row.get("semaforo") or row.get("color") or row.get("tier") or row.get("piedra_tier")
            else:
                raw = row
            if raw:
                return semaforo_normalizado(str(raw))
    return semaforo_normalizado(os.getenv("BERU_RANGO_SEMAFORO"))


def masa_nacimiento_por_bando(color: str, bando: str) -> float:
    m = _mapa_semaforo()
    col = semaforo_normalizado(color)
    b = str(bando or "paz").strip().lower()
    if b not in ("paz", "medio", "pesado"):
        b = "paz"
    row = m.get(col) or {}
    return float(row.get(b, row.get("paz", 0.20)) or 0.20)


def tope_serie_por_color(color: str) -> float:
    m = _mapa_semaforo()
    col = semaforo_normalizado(color)
    return float((m.get(col) or {}).get("tope", 0.80) or 0.80)


def umbral_pierna_medio() -> float:
    return float(getattr(config, "BERU_RANGO_PIERNA_UMBRAL_MEDIO", 100.0) or 100.0)


def umbral_pierna_pesado() -> float:
    return float(getattr(config, "BERU_RANGO_PIERNA_UMBRAL_PESADO", 300.0) or 300.0)


def histéresis_pierna_pct() -> float:
    return float(getattr(config, "BERU_RANGO_PIERNA_HIST_PCT", 0.20) or 0.20)


def pierna_usd(beru: Any | None) -> float:
    """Pierna viva = max(LONG, SHORT) saco + masa del tramo cazando."""
    if beru is None:
        return 0.0
    from core import beru_rango as br

    sl = br.saco_lado_usd(beru, "LONG")
    ss = br.saco_lado_usd(beru, "SHORT")
    if str(getattr(beru, "estado", "") or "").upper() == "CAZANDO":
        m = max(0.0, float(getattr(beru, "masa", 0) or 0))
        d = str(getattr(beru, "direccion", "") or "").upper()
        if d == "LONG":
            sl += m
        elif d == "SHORT":
            ss += m
    return max(sl, ss)


def actualizar_bando_pierna(beru: Any, pierna: float, precio: float) -> str:
    """Involución al subir pierna; evolución al 80 % del umbral."""
    if beru is None:
        return "paz"
    p = max(0.0, float(pierna or 0))
    px = float(precio or 0)
    u_med = umbral_pierna_medio()
    u_pes = umbral_pierna_pesado()
    h = histéresis_pierna_pct()
    bando = str(getattr(beru, "pierna_bando", "") or "paz").lower()
    if bando not in ("paz", "medio", "pesado"):
        bando = "paz"

    if bando == "pesado":
        if p <= u_pes * (1.0 - h):
            bando = "medio"
    elif bando == "medio":
        if p > u_pes:
            bando = "pesado"
            beru.pierna_umbral_involucion = u_pes
            beru.pierna_px_involucion = px
        elif p <= u_med * (1.0 - h):
            bando = "paz"
    else:
        if p > u_pes:
            bando = "pesado"
            beru.pierna_umbral_involucion = u_pes
            beru.pierna_px_involucion = px
        elif p >= u_med:
            bando = "medio"
            beru.pierna_umbral_involucion = u_med
            beru.pierna_px_involucion = px

    beru.pierna_bando = bando
    return bando


def preparar_nacimiento_tramo(
    beru: Any,
    *,
    precio: float,
    activo: str = "",
) -> float:
    """Actualiza bando pierna + serie base según semáforo. Devuelve masa nacimiento."""
    from core import beru_rango as br

    if not br.engorde_modo_peldaños_sumados():
        return br.masa_tramo_usd()
    act = str(activo or br.activo_desde_beru(beru) or "").upper()
    pierna = pierna_usd(beru)
    bando = actualizar_bando_pierna(beru, pierna, precio)
    color = semaforo_resuelto(act, beru)
    base = masa_nacimiento_por_bando(color, bando)
    beru.semaforo_color = color
    beru.serie_masa_base_usd = base
    return base


def serie_base_usd(beru: Any | None) -> float | None:
    if beru is None:
        return None
    b = float(getattr(beru, "serie_masa_base_usd", 0) or 0)
    return b if b > 0 else None


def tope_masa_viva(beru: Any | None, activo: str | None = None) -> float:
    from core import beru_rango as br

    if str(os.getenv("BERU_RANGO_PIEDRA_SIN_TOPE", "") or "").strip().lower() in (
        "1",
        "true",
        "si",
        "yes",
    ):
        return 0.0
    if not br.engorde_modo_peldaños_sumados():
        return br.engorde_tope_usd(beru, activo=activo)
    act = str(activo or br.activo_desde_beru(beru) or "").upper()
    color = semaforo_resuelto(act, beru)
    if beru is not None and getattr(beru, "semaforo_color", ""):
        color = semaforo_normalizado(str(getattr(beru, "semaforo_color")))
    return tope_serie_por_color(color)


def resumen_semaforo(beru: Any | None = None, *, activo: str = "") -> dict[str, Any]:
    from core import beru_rango as br

    act = str(activo or br.activo_desde_beru(beru) or "").upper()
    color = semaforo_resuelto(act, beru)
    bando = str(getattr(beru, "pierna_bando", "paz") or "paz") if beru else "paz"
    return {
        "semaforo": color,
        "pierna_bando": bando,
        "pierna_usd": round(pierna_usd(beru), 4) if beru else 0.0,
        "masa_nacimiento": masa_nacimiento_por_bando(color, bando),
        "tope_serie": tope_serie_por_color(color),
        "umbral_medio": umbral_pierna_medio(),
        "umbral_pesado": umbral_pierna_pesado(),
        "hist_pct": histéresis_pierna_pct(),
    }
