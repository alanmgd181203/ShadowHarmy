"""Quién recibe la capa y quién la suelta. Paso 3. El escudo vivo no lee esto.

Solo cuando la bolsa ya iba a engordar o a desinflar.
No hay un viaje aparte para cambiar de metal.

Al engordar, la capa entra al que tiene permiso. Si los dos
tienen, al de relación más chica. Si ninguno tiene, no entra.
Un permiso que todavía no se sabe no es un sí.

Al desinflar, sale primero el que no acompaña. Si los dos andan
mal, no se cierra el escudo por eso: solo sale lo que la bolsa
ya pidió, en el orden de las capas, la última primero.
"""
from __future__ import annotations

_EPS = 1e-9
_METALES = ("rey", "reina")


class Libro:
    def __init__(self) -> None:
        self.capas: list[tuple[str, float]] = []

    def total(self, metal: str | None = None) -> float:
        if metal is None:
            return sum(cantidad for _, cantidad in self.capas)
        return sum(cantidad for nombre, cantidad in self.capas if nombre == metal)

    def engordar(
        self,
        cantidad: float,
        *,
        permiso_rey: bool | None,
        permiso_reina: bool | None,
        relacion_rey: float | None,
        relacion_reina: float | None,
    ) -> str | None:
        """Mete una capa. Devuelve el metal, o None si no entró nadie."""
        monto = float(cantidad or 0)
        if monto <= _EPS:
            return None
        metal = _quien_recibe(
            permiso_rey,
            permiso_reina,
            relacion_rey,
            relacion_reina,
        )
        if metal is None:
            return None
        self.capas.append((metal, monto))
        return metal

    def desinflar(
        self,
        cantidad: float,
        *,
        permiso_rey: bool | None,
        permiso_reina: bool | None,
    ) -> float:
        """Suelta lo que la bolsa pidió. Nunca más de lo que hay. Nunca todo por estar mal."""
        pedido = float(cantidad or 0)
        if pedido <= _EPS or not self.capas:
            return 0.0
        orden = _orden_de_salida(permiso_rey, permiso_reina)
        suelto = 0.0
        if orden is not None:
            suelto += self._sacar(orden, pedido)
        if pedido - suelto > _EPS:
            suelto += self._sacar(None, pedido - suelto)
        return suelto

    def _sacar(self, metal: str | None, pedido: float) -> float:
        """Desde la capa más nueva. Si metal es None, cualquiera."""
        salio = 0.0
        queda: list[tuple[str, float]] = []
        for nombre, monto in reversed(self.capas):
            if pedido - salio <= _EPS:
                queda.append((nombre, monto))
                continue
            if metal is not None and nombre != metal:
                queda.append((nombre, monto))
                continue
            tomar = min(monto, pedido - salio)
            salio += tomar
            resto = monto - tomar
            if resto > _EPS:
                queda.append((nombre, resto))
        self.capas = list(reversed(queda))
        return salio


def _quien_recibe(
    permiso_rey: bool | None,
    permiso_reina: bool | None,
    relacion_rey: float | None,
    relacion_reina: float | None,
) -> str | None:
    candidatos: list[tuple[str, float]] = []
    if permiso_rey is True and relacion_rey is not None and relacion_rey > 0:
        candidatos.append(("rey", float(relacion_rey)))
    if permiso_reina is True and relacion_reina is not None and relacion_reina > 0:
        candidatos.append(("reina", float(relacion_reina)))
    if len(candidatos) == 1:
        return candidatos[0][0]
    if len(candidatos) != 2:
        return None
    if abs(candidatos[0][1] - candidatos[1][1]) <= _EPS:
        return None
    if candidatos[0][1] < candidatos[1][1]:
        return candidatos[0][0]
    return candidatos[1][0]


def _orden_de_salida(
    permiso_rey: bool | None,
    permiso_reina: bool | None,
) -> str | None:
    """El metal que no acompaña. None si no hay uno solo en falta.

    Un permiso sin saber no cuenta como malo. Los dos malos tampoco
    eligen un castigado: se sale por el orden de las capas.
    """
    rey_mal = permiso_rey is False
    reina_mal = permiso_reina is False
    if rey_mal and not reina_mal:
        return "rey"
    if reina_mal and not rey_mal:
        return "reina"
    return None
