"""Parche espera-piso del sello Oz (evita spam ALTAR_PLAN_FALLIDO).

Se aplica en arise porque ``generales/beru_rango.py`` a veces queda bloqueado
por el IDE en Windows (sección mapeada).
"""
from __future__ import annotations

import time
from typing import Any

from core import beru_rango_altar as altar

_MOTIVOS = (
    "qty_cero_deuda",
    "qty_cero",
    "bajo_min_usd",
    "masa_o_precio_cero",
)


def parchar_espera_piso_sello(cls: Any) -> Any:
    """Envuelve ``_intentar_sello_entrada``: piso insuficiente → aviso 1/min."""
    if getattr(cls, "_altar_espera_piso_parchado", False):
        return cls
    orig = cls._intentar_sello_entrada

    async def _intentar_sello_entrada_espera(self, beru, masa, *, origen: str) -> bool:
        if not self._manos():
            return True
        if altar.sello_entrada_activo(beru) and origen == "REPARAR_SELLO":
            return True
        px_now = self._precio_lineal(self._activo)
        if not altar.stop_trigger_valido(beru, px_now):
            return await orig(self, beru, masa, origen=origen)
        try:
            plan = altar.plan_trailing_entrada(
                beru, activo=self._activo, masa_usd=masa,
            )
        except ValueError as exc:
            msg = str(exc)
            soft = any(t in msg for t in _MOTIVOS)
            if soft:
                last = float(getattr(beru, "_altar_plan_aviso_ts", 0) or 0)
                now = time.time()
                if now - last >= 60.0:
                    beru._altar_plan_aviso_ts = now
                    await self.bel.anotar(
                        "BERU_RANGO",
                        "ALTAR_ESPERA_PISO",
                        f"{beru.uid}: {exc}",
                    )
                    print(
                        f"[RANGO] ALTAR_ESPERA_PISO {self._activo}: {exc}",
                        flush=True,
                    )
                return False
            await self.bel.anotar(
                "BERU_RANGO", "ALTAR_PLAN_FALLIDO", f"{beru.uid}: {exc}",
            )
            return False
        res = await altar.armar_condicional(self.bridge, beru, plan)
        if getattr(res, "exito", False):
            return True
        msg = str(getattr(res, "mensaje", "") or "orden_rechazada")
        if "110092" in msg or "expect Rising" in msg or "expect Falling" in msg:
            return await orig(self, beru, masa, origen=origen)
        await self.bel.anotar(
            "BERU_RANGO",
            "ALTAR_ORDEN_FALLIDA",
            f"{beru.uid} {origen}: {msg} · sin sello en exchange",
        )
        print(
            f"[RANGO] ALTAR_ORDEN_FALLIDA {self._activo} {origen}: {msg}",
            flush=True,
        )
        return False

    cls._intentar_sello_entrada = _intentar_sello_entrada_espera
    cls._altar_espera_piso_parchado = True
    return cls
