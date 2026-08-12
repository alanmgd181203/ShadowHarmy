"""Beru ensayo nivel 3 — manos chiquitas reales (Monarca 2026-08-12).

Ojos reales · Beru late · place_order real con techos · todo en consola.
Igris/Greed fuera. No es ejército libre: es un disparo acotado.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import core.config as config

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs" / "beru_ensayo" / "disparos.jsonl"

_ordenes_ok = 0
_ordenes_fallidas = 0
_techo_avisado = False


def activo() -> bool:
    """Ritual nivel 3 armado (candados del arise)."""
    return bool(getattr(config, "BERU_ENSAYO_NIVEL3", False))


def activos_ensayo() -> list[str]:
    """Santos del ensayo nivel 3 (default MNT)."""
    raw = str(getattr(config, "BERU_ENSAYO_ACTIVOS", "") or "").strip()
    if not raw:
        raw = "MNT"
    out: list[str] = []
    for part in raw.split(","):
        u = part.strip().upper()
        if u and u not in out:
            out.append(u)
    return out


def solo_long() -> bool:
    """Default ON: evita SHORT spot sin inventario del Santo."""
    return bool(getattr(config, "BERU_ENSAYO_SOLO_LONG", True))


def max_ordenes() -> int:
    n = int(float(getattr(config, "BERU_ENSAYO_MAX_ORDENES", 1) or 1))
    return max(1, n)


def ordenes_ok() -> int:
    return int(_ordenes_ok)


def techo_alcanzado() -> bool:
    return activo() and ordenes_ok() >= max_ordenes()


def reset_contadores() -> None:
    global _ordenes_ok, _ordenes_fallidas, _techo_avisado
    _ordenes_ok = 0
    _ordenes_fallidas = 0
    _techo_avisado = False


def registrar(
    evento: str,
    *,
    detalle: str = "",
    **extra: Any,
) -> dict[str, Any]:
    """Imprime en consola + append jsonl. Nunca tumba el ritual."""
    fila: dict[str, Any] = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "evento": str(evento),
        "detalle": str(detalle or ""),
        "nivel": 3,
        "fantasma": False,
        "manos_reales": True,
    }
    for k, v in extra.items():
        if v is None:
            continue
        try:
            json.dumps(v)
            fila[k] = v
        except TypeError:
            fila[k] = str(v)

    linea = (
        f"[BERU_LIVE] {fila['iso']} · {evento}"
        + (f" · {detalle}" if detalle else "")
    )
    extras = {
        k: v
        for k, v in fila.items()
        if k not in ("ts", "iso", "evento", "detalle", "nivel", "fantasma", "manos_reales")
    }
    if extras:
        bits = []
        for k, v in extras.items():
            if isinstance(v, float):
                bits.append(f"{k}={v:.6g}" if abs(v) < 1e6 else f"{k}={v:.2f}")
            else:
                bits.append(f"{k}={v}")
        linea += " | " + " ".join(bits)
    print(linea, flush=True)

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return fila


def anotar_orden_ok(**extra: Any) -> int:
    """Cuenta fill de caza real; al techo ya no abre más cazas (cosecha sigue OK)."""
    global _ordenes_ok, _techo_avisado
    _ordenes_ok += 1
    n = _ordenes_ok
    registrar(
        "ORDEN_OK",
        detalle=f"fill real #{n}/{max_ordenes()}",
        n_ok=n,
        max_ordenes=max_ordenes(),
        **extra,
    )
    if techo_alcanzado() and not _techo_avisado:
        _techo_avisado = True
        registrar(
            "TECHO_CAZAS",
            detalle="no más cazas nuevas — cosecha de lo abierto sigue permitida",
            n_ok=n,
            max_ordenes=max_ordenes(),
        )
        print(
            f"[BERU_LIVE] Techo {max_ordenes()} caza(s) OK — "
            f"no abre más; puede cosechar lo abierto.",
            flush=True,
        )
    return n


def anotar_orden_fallida(motivo: str = "", **extra: Any) -> int:
    global _ordenes_fallidas
    _ordenes_fallidas += 1
    registrar(
        "ORDEN_FALLIDA",
        detalle=str(motivo or "fallo"),
        n_fallidas=_ordenes_fallidas,
        **extra,
    )
    return _ordenes_fallidas


def anotar_cosecha_ok(**extra: Any) -> None:
    """Fill de salida: consola, sin sumar al techo de cazas."""
    registrar(
        "COSECHA_OK",
        detalle="fill salida real",
        **extra,
    )


def resumen_modo() -> dict[str, Any]:
    return {
        "ensayo_nivel3": activo(),
        "manos_reales": bool(getattr(config, "BERU_MANOS", False)),
        "manos_fantasma": bool(getattr(config, "BERU_MANOS_FANTASMA", False)),
        "sim": bool(getattr(config, "MODO_SIMULACION", True)),
        "solo_long": solo_long(),
        "max_ordenes": max_ordenes(),
        "ordenes_ok": ordenes_ok(),
        "ordenes_fallidas": int(_ordenes_fallidas),
        "log": str(LOG_PATH),
        "ley": "ojos reales · manos chiquitas · techo · Igris OFF · consola",
    }
