"""Rutas por Santo — Beru rango multi-proceso sin pisarse.

Cada Santo tiene su carpeta bajo data/beru/rango/{ACTIVO}/.
Los paths legacy (rango_manos_*.json, rango_ojos_*.json) quedan
como espejo/compat para HYPE y lecturas viejas.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BERU_DIR = ROOT / "data" / "beru"
RANGO_DIR = BERU_DIR / "rango"
RANGO_VIVO_PATH = BERU_DIR / "rango_vivo.json"


def _act(activo: str) -> str:
    return str(activo or "").strip().upper()


def dir_santo(activo: str) -> Path:
    d = RANGO_DIR / _act(activo)
    d.mkdir(parents=True, exist_ok=True)
    return d


def ojos_informe(activo: str) -> Path:
    return dir_santo(activo) / "ojos_informe.json"


def ojos_eventos(activo: str) -> Path:
    return dir_santo(activo) / "ojos_eventos.jsonl"


def manos_informe(activo: str) -> Path:
    return dir_santo(activo) / "manos_informe.json"


def manos_eventos(activo: str) -> Path:
    return dir_santo(activo) / "manos_eventos.jsonl"


def flota_ojos_informe() -> Path:
    """Resumen de flota ojos (varios Santos en un proceso)."""
    RANGO_DIR.mkdir(parents=True, exist_ok=True)
    return RANGO_DIR / "ojos_flota_informe.json"


def flota_ojos_eventos() -> Path:
    RANGO_DIR.mkdir(parents=True, exist_ok=True)
    return RANGO_DIR / "ojos_flota_eventos.jsonl"


# Compat lectura/escritura espejo (no borrar hasta que el panel/UI migre)
LEGACY_MANOS_INFORME = BERU_DIR / "rango_manos_informe.json"
LEGACY_MANOS_EVENTOS = BERU_DIR / "rango_manos_eventos.jsonl"
LEGACY_OJOS_INFORME = BERU_DIR / "rango_ojos_informe.json"
LEGACY_OJOS_EVENTOS = BERU_DIR / "rango_ojos_eventos.jsonl"


def resolver_manos_informe(activo: str) -> Path:
    """Preferir sello por Santo; legacy solo si es del mismo activo."""
    p = manos_informe(activo)
    if p.is_file():
        return p
    if LEGACY_MANOS_INFORME.is_file():
        try:
            import json

            data = json.loads(LEGACY_MANOS_INFORME.read_text(encoding="utf-8"))
            if str(data.get("activo") or "").upper() == _act(activo):
                return LEGACY_MANOS_INFORME
        except Exception:
            pass
    return p
