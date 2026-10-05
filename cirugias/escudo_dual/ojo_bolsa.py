"""El ojo del manto de la bolsa. No planta capa.

Mira si la casa de las acciones acompañó al índice y a la reina rápida.
La relación de esta ventana no viste el metal. Viste la misma ley lenta.
"""
from __future__ import annotations

import time

from cirugias.escudo_dual.bolsa import MAREA, REINA, REY
from cirugias.escudo_dual.ojo import _cierres
from cirugias.escudo_dual.permiso import conceder, mirar
from cirugias.escudo_dual.relaciones import las_dos

_CACHE: dict = {"ts": 0.0, "dato": None}


def ver() -> dict:
    """Quién acompañó a la bolsa. No manda orden."""
    ahora = time.time()
    if _CACHE["dato"] is not None and ahora - float(_CACHE["ts"]) < 60:
        return dict(_CACHE["dato"])
    rey = _cierres(REY)
    reina = _cierres(REINA)
    marea = _marea_de(MAREA)
    dato = {
        "permiso_rey": conceder(mirar(marea, rey)),
        "permiso_reina": conceder(mirar(marea, reina)),
        "relaciones": las_dos(marea, rey, reina),
        "marcas": len(marea),
    }
    _CACHE["ts"] = ahora
    _CACHE["dato"] = dato
    return dict(dato)


def _marea_de(nombres: tuple[str, ...]) -> list[float]:
    """El mismo índice igual-peso del ojo de las monedas, con esta casa."""
    series = []
    for inst in nombres:
        try:
            cierres = _cierres(inst)
        except Exception:
            continue
        if len(cierres) < 2:
            continue
        series.append(cierres)
    if len(series) < 3:
        return []
    # _marea arma el índice desde series ya guardadas en el ojo de las monedas.
    # Aquí se rehace igual, sin pisar esa casa.
    n = min(len(c) for c in series)
    series = [c[-n:] for c in series]
    indice = [100.0]
    for i in range(1, n):
        saltos = []
        for serie in series:
            antes = serie[i - 1]
            ahora = serie[i]
            if antes > 0 and ahora > 0:
                saltos.append((ahora / antes) - 1.0)
        if not saltos:
            indice.append(indice[-1])
        else:
            indice.append(indice[-1] * (1.0 + sum(saltos) / len(saltos)))
    return indice
