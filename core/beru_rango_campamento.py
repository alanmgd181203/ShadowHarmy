"""Campamentos Beru piedra — escuadrones de N Santos en un cuartel.

Ley dura: cada campamento se completa a N (default 8).
La mezcla 2V+3A+3R es solo preferencia; si falta un color, se rellena
con lo que haya (pueden salir campamentos distintos).
Sobras que no lleguen a N quedan fuera (no se parte a medias).

Prioridad de latido: el que CAZA pasa antes que el que solo acecha
(comparte el río WS/altar del cuartel).
"""
from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from core import beru_rango_semaforo as sem

ROOT = Path(__file__).resolve().parents[1]
ASIG_PATH = ROOT / "data" / "beru" / "rango" / "piedra_asignacion.json"
CAMP_MANIFEST = ROOT / "data" / "beru" / "rango" / "vigilante_flota" / "campamentos.json"


def tamano_campamento() -> int:
    return max(2, int(float(os.getenv("BERU_FLOTA_CAMPAMENTO_N", "8") or 8)))


def max_pulsos_concurrentes() -> int:
    """Cuántos latidos del campamento pueden golpear el altar a la vez."""
    return max(1, int(float(os.getenv("BERU_FLOTA_CAMP_PULSOS", "2") or 2)))


def factor_cesion_acecho() -> float:
    """Si hay cazador en el cuartel, el acecho duerme × este factor."""
    return max(1.0, float(os.getenv("BERU_FLOTA_CESION_ACECHO", "2.5") or 2.5))


def beru_esta_cazando(beru: Any) -> bool:
    """True si el vivo (o el ship) está en CAZANDO."""
    if beru is None:
        return False
    vivo = getattr(beru, "vivo", None)
    ship = vivo if vivo is not None else beru
    return str(getattr(ship, "estado", "") or "").upper() == "CAZANDO"


def campamento_tiene_cazador(stacks: dict[str, Any] | None) -> bool:
    if not stacks:
        return False
    for st in stacks.values():
        if not isinstance(st, dict):
            continue
        if beru_esta_cazando(st.get("beru")):
            return True
    return False


def wait_con_prioridad_caza(
    wait_s: float,
    beru: Any,
    stacks: dict[str, Any] | None,
    *,
    lento_s: float = 1.5,
) -> float:
    """Cazador: latido fino. Acecho con cazador hermano: cede el río (duerme más)."""
    w = max(0.05, float(wait_s or 0))
    if beru_esta_cazando(beru):
        return w
    if campamento_tiene_cazador(stacks):
        lento = max(0.2, float(lento_s or 1.5))
        return max(w * factor_cesion_acecho(), lento * 2.0)
    return w


class CampPrioridadCaza:
    """Candado del cuartel: fila CAZANDO antes que ACECHANDO.

    Limita pulsos concurrentes al altar/WS compartido y, si hay cola,
    deja pasar primero a los que están cazando.
    """

    def __init__(self, max_concurrent: int | None = None):
        self._max = max(1, int(max_concurrent or max_pulsos_concurrentes()))
        self._active = 0
        self._fila_caza = 0
        self._fila_acecho = 0
        self._cond = asyncio.Condition()

    @asynccontextmanager
    async def turno(self, beru: Any) -> AsyncIterator[None]:
        caza = beru_esta_cazando(beru)
        async with self._cond:
            if caza:
                self._fila_caza += 1
            else:
                self._fila_acecho += 1
            try:
                while True:
                    hay_cupo = self._active < self._max
                    # Acecho espera si hay cazador en fila o activo preferente.
                    if hay_cupo and (caza or self._fila_caza == 0):
                        break
                    await self._cond.wait()
                self._active += 1
            finally:
                if caza:
                    self._fila_caza = max(0, self._fila_caza - 1)
                else:
                    self._fila_acecho = max(0, self._fila_acecho - 1)
        try:
            yield
        finally:
            async with self._cond:
                self._active = max(0, self._active - 1)
                self._cond.notify_all()


def receta_campamento() -> dict[str, int]:
    """Preferencia de mezcla (no obligacion). Se usa solo si hay stock."""
    n = tamano_campamento()
    v = max(0, int(os.getenv("BERU_FLOTA_CAMPAMENTO_VERDE", "2") or 2))
    a = max(0, int(os.getenv("BERU_FLOTA_CAMPAMENTO_AMARILLO", "3") or 3))
    r = max(0, int(os.getenv("BERU_FLOTA_CAMPAMENTO_ROJO", "3") or 3))
    total = v + a + r
    if total <= 0:
        return {"verde": 2, "amarillo": 3, "rojo": max(0, n - 5)}
    if total != n and total > 0:
        scale = n / float(total)
        v = max(0, int(round(v * scale)))
        a = max(0, int(round(a * scale)))
        r = max(0, n - v - a)
    return {"verde": v, "amarillo": a, "rojo": r}


def _asignacion(path: Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else ASIG_PATH
    if not p.is_file():
        return {"activos": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"activos": {}}


def color_santo(activo: str, asig: dict[str, Any] | None = None) -> str:
    data = asig if asig is not None else _asignacion()
    row = (data.get("activos") or {}).get(str(activo).upper())
    if isinstance(row, dict):
        raw = row.get("semaforo") or row.get("color") or row.get("tier")
        if raw:
            return sem.semaforo_normalizado(str(raw))
    return sem.semaforo_normalizado(None)


def pools_por_color(
    activos: list[str] | None = None,
    *,
    asig_path: Path | None = None,
) -> dict[str, list[str]]:
    data = _asignacion(asig_path)
    keys = list(activos) if activos is not None else sorted(
        str(k).upper() for k in (data.get("activos") or {}).keys() if str(k).strip()
    )
    pools: dict[str, list[str]] = {"verde": [], "amarillo": [], "rojo": []}
    for act in keys:
        a = str(act).strip().upper()
        if not a:
            continue
        col = color_santo(a, data)
        pools.setdefault(col, []).append(a)
    for col in pools:
        pools[col] = sorted(set(pools[col]))
    return pools


def _tomar(pool: list[str], n: int, usados: set[str]) -> list[str]:
    out: list[str] = []
    for a in pool:
        if a in usados:
            continue
        out.append(a)
        usados.add(a)
        if len(out) >= n:
            break
    return out


def _rellenar(
    falta: int,
    pools: dict[str, list[str]],
    usados: set[str],
    prefer: tuple[str, ...] = ("amarillo", "rojo", "verde"),
) -> list[str]:
    """Completa plazas con cualquier color disponible."""
    out: list[str] = []
    if falta <= 0:
        return out
    for col in prefer:
        if falta <= 0:
            break
        got = _tomar(pools.get(col) or [], falta, usados)
        out.extend(got)
        falta -= len(got)
    return out


def _clasificar(
    miembros: list[str],
    asig: dict[str, Any],
) -> dict[str, list[str]]:
    por: dict[str, list[str]] = {"verde": [], "amarillo": [], "rojo": []}
    for a in miembros:
        por.setdefault(color_santo(a, asig), []).append(a)
    return {k: v for k, v in por.items() if v}


def empaquetar_campamentos(
    activos: list[str] | None = None,
    *,
    asig_path: Path | None = None,
    tamano: int | None = None,
    receta: dict[str, int] | None = None,
    solo_completos: bool = True,
) -> list[dict[str, Any]]:
    """Arma escuadrones de N. Mezcla preferida; completar a N es la ley.

    Si solo_completos (default), no emite campamentos a medias.
    """
    n = max(2, int(tamano if tamano is not None else tamano_campamento()))
    rec = dict(receta or receta_campamento())
    asig = _asignacion(asig_path)
    pools = pools_por_color(activos, asig_path=asig_path)
    usados: set[str] = set()
    camps: list[dict[str, Any]] = []
    idx = 0

    def _queda() -> int:
        return sum(1 for c in pools for a in pools[c] if a not in usados)

    while _queda() > 0:
        if solo_completos and _queda() < n:
            break
        idx += 1
        miembros: list[str] = []
        for col in ("verde", "amarillo", "rojo"):
            want = int(rec.get(col, 0) or 0)
            if want <= 0:
                continue
            got = _tomar(pools.get(col) or [], want, usados)
            miembros.extend(got)
        if len(miembros) < n:
            miembros.extend(_rellenar(n - len(miembros), pools, usados))
        if not miembros:
            break
        if solo_completos and len(miembros) < n:
            for a in miembros:
                usados.discard(a)
            break
        camp_id = f"CAMP_{idx:03d}"
        camps.append(
            {
                "id": camp_id,
                "santos": list(miembros),
                "n": len(miembros),
                "por_color": _clasificar(miembros, asig),
                "receta_preferida": dict(rec),
                "completo": len(miembros) >= n,
            }
        )
    return camps


def campamentos_hasta_cupo(
    cupo_santos: int,
    *,
    activos: list[str] | None = None,
    asig_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Primeros campamentos completos que caben en el cupo de Santos."""
    todos = empaquetar_campamentos(activos, asig_path=asig_path, solo_completos=True)
    if cupo_santos <= 0:
        return todos
    out: list[dict[str, Any]] = []
    plazas = 0
    for c in todos:
        cn = int(c.get("n") or len(c.get("santos") or []))
        if plazas + cn > cupo_santos:
            break
        out.append(c)
        plazas += cn
    return out


def sellar_manifest(camps: list[dict[str, Any]], *, path: Path | None = None) -> Path:
    dest = Path(path) if path else CAMP_MANIFEST
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tamano": tamano_campamento(),
        "receta_preferida": receta_campamento(),
        "nota": "Completar a N es ley; la mezcla por color es preferencia.",
        "n_campamentos": len(camps),
        "n_santos": sum(int(c.get("n") or 0) for c in camps),
        "campamentos": camps,
    }
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest


def santos_csv(camp: dict[str, Any]) -> str:
    return ",".join(str(a).upper() for a in (camp.get("santos") or []) if str(a).strip())
