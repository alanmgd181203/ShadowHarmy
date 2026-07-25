"""Bellion oído — tabla evento → nivel (4.1.2).

Niveles (doctrina 06):
  critico   — el Monarca debe mirar ya
  ejecucion — fill / cosecha / disparo completo (sin ruido de amend)
  salud     — arranque, sync, estado del cuartel
  ruido     — no sale al Pergamino (paciencia, loops, skips)

Sin LLM. Sin Telegram. Solo reglas.
"""
from __future__ import annotations

import json
import os
import time
from collections import deque
from typing import Any, Literal

Nivel = Literal["critico", "ejecucion", "salud", "ruido"]

NIVELES_OIDO: tuple[Nivel, ...] = ("critico", "ejecucion", "salud")

# Prefijos / tokens en accion (mayúsculas). Orden: primero match gana.
_TABLA: list[tuple[Nivel, tuple[str, ...]]] = [
    (
        "critico",
        (
            "ERROR", "FALLIDO", "FALLIDA", "CRASH", "GLITCH", "DESCONEX",
            "RECONEXIÓN", "RECONEXION", "SAFE_MODE", "SAFE MODE",
            "NAV_ERROR", "NAV_EXCEPCI", "ORDEN_RECHAZADA", "CANCEL_RECHAZADA",
            "CANCEL_ERROR", "ORDEN_ERROR", "SPOT_MARGEN_ERROR",
            "LEVERAGE_RECHAZADO", "LEVERAGE_ERROR", "FILL_TIMEOUT",
            "FILL_POLL_ERROR", "SALDO", "SIN_RESERVA", "ARBITRAJE_FALLIDO",
            "MULTICRUCE_ABORT", "ALERTA", "APAGADO", "MUERTE",
        ),
    ),
    (
        "ejecucion",
        (
            "COSECHA", "FILL", "ORDEN_LLENADA", "ORDEN_COMPLETA", "MATERIALIZ",
            "DISPARO", "MEGA_RESET", "MEGA_BERU", "FUSION", "PODA",
            "REBALANCEO", "ENGORDE", "CAZA_OK", "BOTIN", "VIP_",
            "ARBITRAJE_OK", "MULTICRUCE_OK", "SALVAVIDAS",
            "ORDEN_CANCELADA", "ORDEN_MODIFICADA",
        ),
    ),
    (
        "salud",
        (
            "ARRANQUE", "ARISE", "INICIO", "FIN_CICLO", "INICIO_CICLO",
            "BACKFILL", "NAV_OK", "NAV_SYNC", "SENTIDOS", "WS_OK",
            "CONECTADO", "DESPERTAR", "LEY_SUCESION", "HEARTBEAT",
            "RESUMEN", "SALUD",
        ),
    ),
]

# Si la accion es exactamente esto → ruido (aunque contenga otra palabra)
_RUIDO_EXACTO = frozenset({
    "PACIENCIA", "ESCALERA_SKIP", "LOOP", "TICK", "DEBUG",
})


def clasificar(general: str, accion: str, detalle: str = "") -> Nivel:
    """Devuelve nivel del oído para un evento Bellion."""
    act = str(accion or "").strip().upper()
    if not act:
        return "ruido"
    if act in _RUIDO_EXACTO:
        return "ruido"
    blob = f"{act} {str(detalle or '').upper()}"
    for nivel, tokens in _TABLA:
        for tok in tokens:
            if tok in act or tok in blob:
                return nivel
    # Kaiser ALERTA ya cubierto; resto de anotar genérico = ruido
    return "ruido"


def etiqueta_nivel(nivel: str) -> str:
    return {
        "critico": "Crítico",
        "ejecucion": "Ejecución",
        "salud": "Salud",
        "ruido": "Ruido",
    }.get(str(nivel), str(nivel))


class OidoRing:
    """Memoria corta de eventos clasificados (para estado_vivo.bellion_oido)."""

    def __init__(self, max_n: int = 80):
        self._max = max(10, int(max_n))
        self._buf: deque[dict[str, Any]] = deque(maxlen=self._max)

    def push(
        self,
        *,
        general: str,
        accion: str,
        detalle: str,
        nivel: Nivel | None = None,
        ts: float | None = None,
    ) -> dict[str, Any]:
        niv: Nivel = nivel or clasificar(general, accion, detalle)
        row = {
            "ts": float(ts if ts is not None else time.time()),
            "general": str(general or "").upper(),
            "accion": str(accion or ""),
            "detalle": str(detalle or "")[:240],
            "nivel": niv,
            "nivel_label": etiqueta_nivel(niv),
        }
        self._buf.append(row)
        return row

    def snapshot(self, *, limit: int = 40, incluir_ruido: bool = False) -> dict[str, Any]:
        rows = list(self._buf)
        if not incluir_ruido:
            rows = [r for r in rows if r.get("nivel") in NIVELES_OIDO]
        recent = rows[-limit:]
        counts = {n: 0 for n in ("critico", "ejecucion", "salud", "ruido")}
        for r in self._buf:
            k = str(r.get("nivel") or "ruido")
            if k in counts:
                counts[k] += 1
        por_nivel: dict[str, list] = {n: [] for n in NIVELES_OIDO}
        for r in reversed(recent):
            n = r.get("nivel")
            if n in por_nivel and len(por_nivel[n]) < 12:
                por_nivel[n].append(r)
        return {
            "ts": time.time(),
            "fuente": "anillo",
            "n_anillo": len(self._buf),
            "counts": counts,
            "recientes": list(reversed(recent[-limit:])),
            "por_nivel": por_nivel,
            "nota": (
                "Oído 4.1.2 — solo crítico / ejecución / salud al Pergamino. "
                "Ruido queda en historial crudo."
            ),
        }


def cargar_tabla_override(path: str | None = None) -> dict[str, Any] | None:
    """Opcional: data/bellion_oido_tabla.json para ampliar tokens sin tocar código."""
    ruta = path or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "bellion_oido_tabla.json",
    )
    if not os.path.isfile(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
