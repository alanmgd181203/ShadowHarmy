"""Viaje y quiebre. Paso 1. El cazador vivo no lee esto.

El promedio de la casa es lo que sigue abierto. Aquí no.
La entrada la mueven solo las órdenes que engordan.
El quiebre lo mueve cada orden: lo pagado menos lo cobrado,
partido por lo que todavía queda. En el papel, ese cero también
deja pagada la comisión de abrir y la de cerrar lo que sigue.
El spread no entra: no hay un número fijo que sumarle.

Vaciar la bolsa no borra la masa. El mismo lado sigue.
La cuenta nace de cero solo cuando el lado voltea.

Una venta por debajo del promedio sube el quiebre.
Una venta por encima lo baja, porque esa ganancia ya se guardó.
Mientras el viaje es largo, una venta solo reduce. No abre corto.
La masa negociada suma las entradas y no baja cuando se reduce.
"""
from __future__ import annotations

from dataclasses import dataclass

_EPS = 1e-9
# 0,055 % por lado. El peaje lineal que el ejército ya usa. No es un spread.
PEAJE = 0.00055


def quiebre_mostrado(lado: str, base: float, peaje: float) -> float:
    """El cero, con la comisión de cerrar lo que sigue montado.

    ``base`` ya trae la comisión de lo abierto y de lo cerrado.
    """
    f = float(peaje or 0)
    if f <= 0:
        return base
    if str(lado or "").upper() == "SHORT":
        return base / (1.0 + f)
    return base / (1.0 - f)


@dataclass
class Viaje:
    lado: str
    cantidad: float = 0.0
    caja: float = 0.0
    masa_negociada: float = 0.0
    monedas_entrada: float = 0.0
    costo_entrada: float = 0.0
    peaje: float = 0.0

    def vivo(self) -> bool:
        return self.cantidad > _EPS

    def entrada(self) -> float | None:
        """Promedio de lo que engordó. Las ventas no lo mueven."""
        if self.monedas_entrada <= _EPS:
            return None
        return self.costo_entrada / self.monedas_entrada

    def quiebre(self) -> float | None:
        """Precio donde el viaje queda en tablas. None si ahora no hay monedas."""
        if not self.vivo():
            return None
        return quiebre_mostrado(self.lado, self.caja / self.cantidad, self.peaje)

    def abrir(self, cantidad: float, precio: float) -> None:
        c = float(cantidad or 0)
        p = float(precio or 0)
        if c <= _EPS or p <= _EPS:
            return
        bruto = c * p
        peaje = bruto * self.peaje
        self.cantidad += c
        if self.lado == "SHORT":
            self.caja += bruto - peaje
            self.costo_entrada += bruto - peaje
        else:
            self.caja += bruto + peaje
            self.costo_entrada += bruto + peaje
        self.masa_negociada += bruto
        self.monedas_entrada += c

    def reducir(self, cantidad: float, precio: float) -> float:
        """Baja la bolsa. Devuelve lo que de verdad redujo. El sobrante no voltea el lado."""
        c = float(cantidad or 0)
        p = float(precio or 0)
        if c <= _EPS or p <= _EPS or not self.vivo():
            return 0.0
        tomado = min(c, self.cantidad)
        bruto = tomado * p
        peaje = bruto * self.peaje
        self.cantidad -= tomado
        if self.lado == "SHORT":
            self.caja -= bruto + peaje
        else:
            self.caja -= bruto - peaje
        if self.cantidad <= _EPS:
            self._morir()
        return tomado

    def _morir(self) -> None:
        """Cero monedas. La masa y la caja siguen: el lado no cambió."""
        self.cantidad = 0.0

    def voltear(self) -> None:
        """El lado cambió. La cuenta nace de cero."""
        self.cantidad = 0.0
        self.caja = 0.0
        self.masa_negociada = 0.0
        self.monedas_entrada = 0.0
        self.costo_entrada = 0.0


class Libro:
    """Dos viajes. Uno no apaga al otro."""

    def __init__(self) -> None:
        self.largo = Viaje("LONG")
        self.corto = Viaje("SHORT")

    def abrir_largo(self, cantidad: float, precio: float) -> None:
        self.largo.abrir(cantidad, precio)

    def reducir_largo(self, cantidad: float, precio: float) -> float:
        return self.largo.reducir(cantidad, precio)

    def voltear(self) -> None:
        """La posición cambió de lado. Las dos cuentas nacen de cero."""
        self.largo.voltear()
        self.corto.voltear()

    def abrir_corto(self, cantidad: float, precio: float) -> None:
        self.corto.abrir(cantidad, precio)

    def reducir_corto(self, cantidad: float, precio: float) -> float:
        return self.corto.reducir(cantidad, precio)
