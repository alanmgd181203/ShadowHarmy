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


def ojos_inverso_informe(activo: str) -> Path:
    return dir_santo(activo) / "ojos_inverso_informe.json"


def ojos_inverso_eventos(activo: str) -> Path:
    return dir_santo(activo) / "ojos_inverso_eventos.jsonl"


def informe_ojo(
    activo: str,
    mercado: str = "linear",
    perfil: str = "normal",
) -> Path:
    from core import beru_rango_ojos

    m = beru_rango_ojos.mercado_norm(mercado)
    p = beru_rango_ojos.perfil_norm(perfil)
    if m == "inverse":
        return ojos_inverso_informe(activo)
    if p == "feria":
        return ojos_feria_informe(activo)
    return ojos_informe(activo)


def eventos_ojo(
    activo: str,
    mercado: str = "linear",
    perfil: str = "normal",
) -> Path:
    from core import beru_rango_ojos

    m = beru_rango_ojos.mercado_norm(mercado)
    p = beru_rango_ojos.perfil_norm(perfil)
    if m == "inverse":
        return ojos_inverso_eventos(activo)
    if p == "feria":
        return ojos_feria_eventos(activo)
    return ojos_eventos(activo)


def manos_informe(activo: str) -> Path:
    return dir_santo(activo) / "manos_informe.json"


def manos_eventos(activo: str) -> Path:
    return dir_santo(activo) / "manos_eventos.jsonl"


def manos_inverso_informe(activo: str) -> Path:
    return dir_santo(activo) / "manos_inverso_informe.json"


def manos_inverso_eventos(activo: str) -> Path:
    return dir_santo(activo) / "manos_inverso_eventos.jsonl"


def manos_feria_informe(activo: str) -> Path:
    return dir_santo(activo) / "manos_feria_informe.json"


def manos_feria_eventos(activo: str) -> Path:
    return dir_santo(activo) / "manos_feria_eventos.jsonl"


def ojos_feria_informe(activo: str) -> Path:
    return dir_santo(activo) / "ojos_feria_informe.json"


def ojos_feria_eventos(activo: str) -> Path:
    return dir_santo(activo) / "ojos_feria_eventos.jsonl"


def manos_piedra_informe(activo: str) -> Path:
    return dir_santo(activo) / "manos_piedra_informe.json"


def manos_piedra_eventos(activo: str) -> Path:
    return dir_santo(activo) / "manos_piedra_eventos.jsonl"


def informe_manos(
    activo: str,
    mercado: str = "linear",
    perfil: str = "normal",
) -> Path:
    from core import beru_rango_ojos

    m = beru_rango_ojos.mercado_norm(mercado)
    p = beru_rango_ojos.perfil_norm(perfil)
    if m == "inverse":
        return manos_inverso_informe(activo)
    if p == "feria":
        return manos_feria_informe(activo)
    if p == "piedra":
        return manos_piedra_informe(activo)
    return manos_informe(activo)


def eventos_manos(
    activo: str,
    mercado: str = "linear",
    perfil: str = "normal",
) -> Path:
    from core import beru_rango_ojos

    m = beru_rango_ojos.mercado_norm(mercado)
    p = beru_rango_ojos.perfil_norm(perfil)
    if m == "inverse":
        return manos_inverso_eventos(activo)
    if p == "feria":
        return manos_feria_eventos(activo)
    if p == "piedra":
        return manos_piedra_eventos(activo)
    return manos_eventos(activo)


def flota_ojos_informe() -> Path:
    """Resumen de flota ojos (varios Santos en un proceso)."""
    RANGO_DIR.mkdir(parents=True, exist_ok=True)
    return RANGO_DIR / "ojos_flota_informe.json"


def flota_ojos_eventos() -> Path:
    RANGO_DIR.mkdir(parents=True, exist_ok=True)
    return RANGO_DIR / "ojos_flota_eventos.jsonl"


def flota_ojos_inverso_informe() -> Path:
    RANGO_DIR.mkdir(parents=True, exist_ok=True)
    return RANGO_DIR / "ojos_inverso_flota_informe.json"


def flota_ojos_inverso_eventos() -> Path:
    RANGO_DIR.mkdir(parents=True, exist_ok=True)
    return RANGO_DIR / "ojos_inverso_flota_eventos.jsonl"


# Compat lectura/escritura espejo (no borrar hasta que el panel/UI migre)
LEGACY_MANOS_INFORME = BERU_DIR / "rango_manos_informe.json"
LEGACY_MANOS_EVENTOS = BERU_DIR / "rango_manos_eventos.jsonl"
LEGACY_OJOS_INFORME = BERU_DIR / "rango_ojos_informe.json"
LEGACY_OJOS_EVENTOS = BERU_DIR / "rango_ojos_eventos.jsonl"


def resolver_manos_informe(
    activo: str,
    mercado: str = "linear",
    perfil: str = "normal",
) -> Path:
    """Preferir sello por Santo, mercado y perfil; legacy solo lineal normal."""
    from core import beru_rango_ojos

    m = beru_rango_ojos.mercado_norm(mercado)
    p = beru_rango_ojos.perfil_norm(perfil)
    path = informe_manos(activo, m, p)
    if path.is_file():
        return path
    if m != "inverse" and p == "normal" and LEGACY_MANOS_INFORME.is_file():
        try:
            import json

            data = json.loads(LEGACY_MANOS_INFORME.read_text(encoding="utf-8"))
            if str(data.get("activo") or "").upper() == _act(activo):
                return LEGACY_MANOS_INFORME
        except Exception:
            pass
    return path
