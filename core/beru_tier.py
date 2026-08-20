"""Beru — tiers Proto/Pleno/Berubby, trailing 0.1% y resolución dinámica de clonación."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import core.config as config

ModoCombate = Literal["CAZA"]

# Trailing simétrico caza: siempre 0.1% (doctrina Monarca 2026-07)
PASO_TRAILING_CAZA = 0.001
# Alias del peldaño de Hoz/Red (0.1%). Sin esto el armado del llamado explota.
PASO_HOZ_CAZA = PASO_TRAILING_CAZA

# Relevo (silbato del siguiente cazador) — NO distancia de Red en caza
# Soldado +0.9 · Capitán +0.5 · General +0.3 · Mariscal +0.1 (desde última Red tocada)
RANGO_MARISCAL = 0.001   # PLENO
RANGO_GENERAL = 0.003    # PROTO1
RANGO_CABALLERO = 0.005  # PROTO2 = Capitán
RANGO_SOLDADO = 0.009    # BERUBBY


@dataclass(frozen=True)
class BeruGridTier:
    id: str
    nombre: str
    rango: str
    paso_oz_caza: float
    paso_red_caza: float
    paso_oz_negociador: float
    paso_red_negociador: float
    distancia_clon_pct: float
    escala_manto: float
    oz_tras_toque_red: float | None = None

    def pasos(self, modo: ModoCombate) -> tuple[float, float]:
        if str(modo or "").upper() != "CAZA":
            raise RuntimeError("FOSIL_BLOQUEADO: negociador extirpado del grid")
        return self.paso_oz_caza, self.paso_red_caza


BERU_TIERS: dict[str, BeruGridTier] = {
    "PLENO": BeruGridTier(
        id="PLENO",
        nombre="Comandante",
        rango="Mariscal",
        paso_oz_caza=PASO_TRAILING_CAZA,
        paso_red_caza=PASO_TRAILING_CAZA,
        paso_oz_negociador=0.001,
        paso_red_negociador=0.0005,
        distancia_clon_pct=RANGO_MARISCAL,
        escala_manto=1.0,
    ),
    "PROTO1": BeruGridTier(
        id="PROTO1",
        nombre="Guerrero",
        rango="General",
        paso_oz_caza=PASO_TRAILING_CAZA,
        paso_red_caza=PASO_TRAILING_CAZA,
        paso_oz_negociador=0.002,
        paso_red_negociador=0.001,
        distancia_clon_pct=RANGO_GENERAL,
        escala_manto=2.0,
    ),
    "PROTO2": BeruGridTier(
        id="PROTO2",
        nombre="Aprendiz",
        rango="Caballero",
        paso_oz_caza=PASO_TRAILING_CAZA,
        paso_red_caza=PASO_TRAILING_CAZA,
        paso_oz_negociador=0.004,
        paso_red_negociador=0.002,
        distancia_clon_pct=RANGO_CABALLERO,
        escala_manto=4.0,
    ),
    "BERUBBY": BeruGridTier(
        id="BERUBBY",
        nombre="Beru Aspirante",
        rango="Soldado",
        paso_oz_caza=PASO_TRAILING_CAZA,
        paso_red_caza=PASO_TRAILING_CAZA,
        paso_oz_negociador=0.02,
        paso_red_negociador=0.01,
        distancia_clon_pct=RANGO_SOLDADO,
        escala_manto=8.0,
        oz_tras_toque_red=0.02,
    ),
}


def tier_por_id(tier_id: str | None = None) -> BeruGridTier:
    tid = (tier_id or getattr(config, "BERU_TIER_DEFAULT", "PROTO1")).upper()
    return BERU_TIERS.get(tid, BERU_TIERS["PROTO1"])


def modo_combate_default() -> ModoCombate:
    return "CAZA"


def precios_red_oz(
    centro: float,
    direccion: str,
    *,
    paso_oz: float,
    paso_red: float,
) -> tuple[float, float]:
    """Red y oz iniciales desde centro y pasos (% fracción)."""
    if direccion == "SHORT":
        red = centro * (1.0 + paso_red)
        oz = centro * (1.0 - paso_oz)
    else:
        red = centro * (1.0 - paso_red)
        oz = centro * (1.0 + paso_oz)
    return red, oz


def oz_berubby_tras_toque_red(centro: float, direccion: str, paso_oz: float = 0.02) -> float:
    if direccion == "SHORT":
        return centro * (1.0 - paso_oz)
    return centro * (1.0 + paso_oz)


def mover_red(precio_red: float, direccion: str, paso_red: float) -> float:
    if direccion == "SHORT":
        return precio_red * (1.0 + paso_red)
    return precio_red * (1.0 - paso_red)


def resumen_tiers() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in BERU_TIERS.values():
        oz_c, red_c = t.pasos("CAZA")
        row: dict[str, Any] = {
            "id": t.id,
            "nombre": t.nombre,
            "rango": t.rango,
            "escala_manto": t.escala_manto,
            "caza_oz_pct": round(oz_c * 100, 2),
            "caza_red_pct": round(red_c * 100, 2),
            "clon_red_pct": round(t.distancia_clon_pct * 100, 2),
        }
        if t.oz_tras_toque_red is not None:
            row["oz_tras_toque_red_pct"] = round(t.oz_tras_toque_red * 100, 2)
        out.append(row)
    return out
