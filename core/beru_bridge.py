"""Fábrica del puente Beru — OKX por defecto."""
from __future__ import annotations

import core.config as config
from core import beru_mar


def credenciales_ok() -> bool:
  if beru_mar.es_okx():
    from core import okx_rest
    return okx_rest.credenciales_ok()
  return bool(getattr(config, "API_KEY", None) and getattr(config, "API_SECRET", None))


def crear_beru_bridge(tank, tusk, bellion, *, ws_bases=None):
  """Puente de ojos/manos para Beru rango."""
  if beru_mar.es_okx():
    from core.okx_bridge import OkxBridge
    return OkxBridge(tank, tusk, bellion, ws_bases=ws_bases)
  from core.bridge import BybitBridge
  return BybitBridge(
    tank, tusk, bellion,
    config.API_KEY, config.API_SECRET,
    ws_bases=ws_bases,
  )


def nombre_mar() -> str:
  return beru_mar.mar_activo().upper()
