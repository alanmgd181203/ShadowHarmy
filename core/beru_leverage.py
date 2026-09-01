"""Apalancamiento máximo Beru en OKX (un SWAP por Santo)."""
from __future__ import annotations

from typing import Any

from core import beru_mar
from core import okx_rest
from core import lote_okx


async def forzar_max_leverage_activo(bridge, bel, activo: str, *, forzar: bool = True) -> dict[str, Any]:
  act = str(activo or "").upper()
  if not act:
    return {"ok": False, "omitido": True, "avisos": ["activo_vacio"]}
  if not beru_mar.es_okx():
    from core import igris_leverage as ilev
    return await ilev.forzar_max_leverage_activo(bridge, bel, act, forzar=forzar)

  inst = beru_mar.activo_a_inst_id(act)
  pierna = lote_okx.pierna_activo(act)
  pedido = int(float(pierna.get("maxLever") or 75))
  candidatos = [pedido]
  for x in (100, 75, 50, 25, 20, 15, 10, 5, 3, 2, 1):
    if x < pedido and x not in candidatos:
      candidatos.append(x)

  avisos: list[str] = []
  aplicado = None
  for lev in candidatos:
    try:
      res = await bridge.set_leverage(inst, lev)
    except Exception as exc:
      avisos.append(f"{inst} {lev}x: {exc}")
      continue
    if getattr(res, "exito", False):
      aplicado = lev
      break
    avisos.append(f"{inst} {lev}x: {getattr(res, 'mensaje', 'rechazado')}")

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
    "piernas": [{"symbol": inst, "aplicado": aplicado, "pedido": pedido}],
    "avisos": avisos,
  }
