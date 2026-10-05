"""La mente que Igris suma. El escudo vivo no lee esto.

Cada Beru declara la masa ya sentada que saldrá al tocar su Oz.
Igris no adivina y no pondera: suma. El deber es la bolsa cruda
menos esa suma.

El hacha guarda monedas, no dólares de aquel instante. Se valúan
con la marca de hoy. Sustituye a la Oz de ese mismo cazador.
Al cobrar se calla: la grasa de después no queda desnuda.
"""
from __future__ import annotations

_EPS = 1e-9


class Mente:
    """Lo que un Beru ya firmó, y el hacha si ya está esperando."""

    def __init__(self) -> None:
        self.masa_oz = 0.0
        self.hacha = False
        self.monedas_hacha = 0.0

    def declarar(self, masa: float) -> float:
        """La masa sentada que saldrá en la Oz. Negativa no existe.

        Mientras el hacha espera, esa voz no se oye. Al cobrarse,
        puede volver a hablar.
        """
        if self.hacha:
            return self.masa_oz
        monto = float(masa or 0)
        if monto < -_EPS:
            raise ValueError("radar: la mente no declara masa negativa")
        self.masa_oz = monto
        return self.masa_oz

    def sentar_hacha(self, monedas: float) -> float:
        """El activador prendió. Esas monedas quedan condenadas.

        Una segunda vez no las mueve. La grasa de después no entra.
        """
        if self.hacha:
            return self.monedas_hacha
        monto = float(monedas or 0)
        if monto < -_EPS:
            raise ValueError("radar: el hacha no agarra monedas negativas")
        self.hacha = True
        self.monedas_hacha = max(0.0, monto)
        return self.monedas_hacha

    def cobrar(self) -> None:
        """El hacha ya cobró. La mente se calla.

        Lo que sigue abierto puede volver a declararse. El número
        viejo no se queda descontando.
        """
        if not self.hacha:
            return
        self.hacha = False
        self.monedas_hacha = 0.0
        self.masa_oz = 0.0

    def firmada(self, precio: float | None = None) -> float:
        """Lo que Igris puede dar por ya salido. El hacha no se suma a la Oz.

        Sin la marca de hoy, las monedas condenadas no se inventan
        en dólares.
        """
        if self.hacha:
            marca = float(precio or 0)
            if marca <= _EPS:
                raise ValueError("radar: el hacha no se valua sin la marca de hoy")
            return self.monedas_hacha * marca
        return self.masa_oz


def firmada(mentes: list[Mente], precio: float | None = None) -> float:
    """La suma. Una mente callada aporta cero."""
    return sum(mente.firmada(precio) for mente in mentes)


def deber(
    bolsa: float,
    mentes: list[Mente],
    precio: float | None = None,
) -> float:
    """Lo que el escudo todavía tiene que cubrir. Nunca al revés."""
    cruda = max(0.0, float(bolsa or 0))
    return max(0.0, cruda - firmada(mentes, precio))
