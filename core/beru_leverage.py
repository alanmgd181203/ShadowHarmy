"""Apalancamiento máximo Beru en OKX (un SWAP por Santo).

Pide el techo. Si la casa lo niega porque la posición no cabe en esa
palanca, baja de uno en uno. No salta a 3 ni a 2. Si ya está en el
techo, no molesta a la casa.
"""
from __future__ import annotations

import re
import asyncio
from typing import Any

from core import beru_mar
from core import okx_rest
from core import lote_okx

_TECHOS: dict[str, int] | None = None

# La posición no cabe en esa palanca, o el número pedido pasa del techo.
_BAJA_UNO = frozenset({
  "51010", "51108", "51186", "54024",
  "59102", "59107", "59108", "59110", "59111",
})
# Ruido o un stop: no se sigue bajando.
_QUIETO = frozenset({"50011", "50001", "50102", "50111", "50013", "59669"})


def _techo_vivo(inst: str, respaldo: int) -> int:
  """El máximo que la casa publica hoy. Si no contesta, el del catálogo."""
  global _TECHOS
  if _TECHOS is None:
    _TECHOS = {}
    try:
      rows = okx_rest.get_public(
        "/api/v5/public/instruments",
        params={"instType": "SWAP"},
      ) or []
    except Exception:
      rows = []
    for row in rows:
      if not isinstance(row, dict):
        continue
      nombre = str(row.get("instId") or "")
      try:
        lev = int(float(row.get("lever") or 0))
      except (TypeError, ValueError):
        lev = 0
      if nombre and lev > 0:
        _TECHOS[nombre] = lev
  return int(_TECHOS.get(inst) or respaldo or 1)


def escalones_de_uno(techo: int) -> list[int]:
  """Del techo hacia abajo, de uno en uno. Nunca un salto."""
  n = max(1, int(techo or 1))
  return list(range(n, 0, -1))


def _codigo(msg: str) -> str:
  texto = str(msg or "")
  m = re.search(r"OKX\s+(\d+)", texto)
  if m:
    return m.group(1)
  m = re.search(r"\b(\d{5})\b", texto)
  return m.group(1) if m else ""


def hay_que_bajar_uno(msg: str) -> bool:
  """True solo si esa palanca no cabe. El ahogo de la casa no es motivo."""
  codigo = _codigo(msg)
  if codigo in _QUIETO:
    return False
  if codigo in _BAJA_UNO:
    return True
  low = str(msg or "").lower()
  if "too many" in low or "timestamp" in low:
    return False
  return any(
    frase in low
    for frase in (
      "maximum position",
      "max position",
      "exceeds the maximum",
      "exceed the maximum",
      "leverage is too high",
      "leverage exceeds",
      "not within",
      "position tier",
    )
  )


def techo_dicho(msg: str) -> int | None:
  """Si la casa dice el máximo, el siguiente intento es ese número."""
  m = re.search(
    r"(?:max(?:imum)?\s*leverage|leverage[^\d]{0,24}max(?:imum)?)"
    r"[^\d]{0,16}(\d+)",
    str(msg or ""),
    flags=re.I,
  )
  if not m:
    return None
  try:
    n = int(m.group(1))
  except ValueError:
    return None
  return n if n >= 1 else None


def palanca_actual(inst: str) -> int | None:
  """La palanca que la casa tiene puesta ahora. None si no se ve."""
  try:
    rows = okx_rest.get_private(
      "/api/v5/account/leverage-info",
      params={"instId": inst, "mgnMode": "cross"},
    ) or []
  except Exception:
    return None
  for row in rows:
    if not isinstance(row, dict):
      continue
    if str(row.get("instId") or inst) not in ("", inst):
      continue
    try:
      lev = int(float(row.get("lever") or 0))
    except (TypeError, ValueError):
      continue
    if lev > 0:
      return lev
  return None


async def forzar_max_leverage_activo(bridge, bel, activo: str, *, forzar: bool = True) -> dict[str, Any]:
  act = str(activo or "").upper()
  if not act:
    return {"ok": False, "omitido": True, "avisos": ["activo_vacio"]}
  if not beru_mar.es_okx():
    from core import igris_leverage as ilev
    return await ilev.forzar_max_leverage_activo(bridge, bel, act, forzar=forzar)

  inst = beru_mar.activo_a_inst_id(act)
  pierna = lote_okx.pierna_activo(act)
  respaldo = int(float(pierna.get("maxLever") or 75))
  pedido = _techo_vivo(inst, respaldo)
  actual = await asyncio.to_thread(palanca_actual, inst)
  if actual is not None and actual >= pedido:
    return {
      "ok": True,
      "activo": act,
      "piernas": [{"symbol": inst, "aplicado": actual, "pedido": pedido, "antes": actual}],
      "avisos": [],
    }

  avisos: list[str] = []
  aplicado = None
  lev = pedido
  while lev >= 1 and (actual is None or lev >= actual):
    try:
      res = await bridge.set_leverage(inst, lev)
    except Exception as exc:
      msg = str(exc)
      avisos.append(f"{inst} {lev}x: {msg}")
      if not hay_que_bajar_uno(msg):
        break
      dicho = techo_dicho(msg)
      lev = dicho if dicho and dicho < lev else lev - 1
      continue
    if getattr(res, "exito", False):
      aplicado = lev
      break
    msg = str(getattr(res, "mensaje", "rechazado") or "rechazado")
    avisos.append(f"{inst} {lev}x: {msg}")
    if not hay_que_bajar_uno(msg):
      break
    dicho = techo_dicho(msg)
    lev = dicho if dicho and dicho < lev else lev - 1

  ok = aplicado is not None
  if bel is not None:
    try:
      await bel.anotar(
        "BERU_OKX", "LEVERAGE",
        f"{act} {aplicado or 0}x" if ok else f"{act} fallo: {'; '.join(avisos[:3])}",
      )
    except Exception:
      pass
  return {
    "ok": ok,
    "activo": act,
    "piernas": [{
      "symbol": inst,
      "aplicado": aplicado,
      "pedido": pedido,
      "antes": actual,
    }],
    "avisos": avisos,
  }
