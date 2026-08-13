"""Libros Tusk — caja / guerra / testigo (sello mega-pre-Igris).

MtM de MNT legado (sucio) ≠ riqueza Beru. Caja = USDT.
Equity UTA = testigo (no veredicto de riqueza).
Guerra = reportes (stub hasta sim).
Aporte guerra→bóveda = transferencia explícita entre libros (asiento futuro).
"""
from __future__ import annotations

import json
import os
import time
from typing import Any


def _ruta_estado() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "estado_vivo.json")


def _leer_estado(estado: dict | None = None) -> dict[str, Any]:
    if isinstance(estado, dict):
        return estado
    ruta = _ruta_estado()
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError, TypeError):
        return {}


def snapshot_libros(
    tusk=None,
    *,
    estado: dict | None = None,
) -> dict[str, Any]:
    """Snapshot de los tres libros + reglas doctrinales."""
    live = _leer_estado(estado)
    boveda_live = live.get("boveda") if isinstance(live.get("boveda"), dict) else {}

    # Equity / testigo UTA
    equity = 0.0
    if tusk is not None:
        try:
            equity = float(
                getattr(tusk, "masa_bruta_real", None)
                or getattr(tusk, "masa_bruta", None)
                or 0
            )
        except (TypeError, ValueError):
            equity = 0.0
    if equity <= 0:
        for k in ("masa_bruta_real", "masa_bruta", "equity_usd", "equity"):
            try:
                v = float(boveda_live.get(k) or 0)
            except (TypeError, ValueError):
                v = 0.0
            if v > 0:
                equity = v
                break

    # MtM MNT legado (si existe en snapshot) — NO es riqueza Beru
    mtm_mnt = None
    for k in ("boveda_mnt_mtm_usd", "mnt_mtm_usd", "mtm_boveda_usd"):
        if boveda_live.get(k) is not None:
            try:
                mtm_mnt = float(boveda_live[k])
            except (TypeError, ValueError):
                mtm_mnt = None
            break

    return {
        "ts": time.time(),
        "boveda": {
            "mtm_mnt_usd": mtm_mnt,
            "mtm_no_es_riqueza_beru": True,
            "nota": "MtM MNT legado ≠ riqueza Beru",
        },
        "guerra": {
            "reportes_vivos": False,
            "stub": True,
            "nota": "Libro de guerra hasta sim/reportes",
        },
        "testigo": {
            "equity_uta_usd": round(equity, 4),
            "no_es_veredicto_riqueza": True,
            "nota": "Equity UTA = testigo, no veredicto",
        },
        "reglas": {
            "aporte_guerra_a_boveda": "transferencia_explicita_futura",
            "no_mezclar_contabilidades": True,
        },
        "ley": "tusk_libros_mega_pre_igris",
    }
