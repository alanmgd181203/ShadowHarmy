"""Descarga de Beru. Paso 5. El cazador vivo no lee esto.

Solo dice cuánto soltar. No toca las redes ni las Oz de la caza.

- Limpia: no habla. Beru sigue como está. Un cero aquí apagaría su masa.
- Normal: lo que queda se suelta en todo el tramo, de la última Oz
  al precio quieto de la masacre. 4 % y 400 dólares son 10 dólares
  cada 0,1 %, al pie.
- Difícil: la misma masa, en la mitad del tramo. 20 dólares cada 0,1 %.

El 0,1 % es un tramo del camino, medido desde la Oz. Cuarenta de esos
caen justo en el 4 %. Un salto de precio cuenta cada décima, no una sola.

Si ya soltó, se parte lo que queda entre las décimas que faltan.
Partirlo otra vez entre las cuarenta de origen deja cola al final.
"""
from __future__ import annotations

_EPS = 1e-12
_DECIMA = 0.001


class Descarga:
    def __init__(self, lado: str, clase: str, oz: float, meta: float) -> None:
        self.lado = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        self.clase = str(clase or "").strip().lower()
        self.oz = float(oz or 0)
        self.meta = float(meta or 0)
        self.habla = self.clase in ("normal", "dificil") and self._tramo_valido()

    def al_pie(self, masa: float) -> float | None:
        """Dólares de la primera décima, parado en la Oz. None si no habla."""
        if not self.habla:
            return None
        m = _masa(masa)
        if m <= 0:
            return 0.0
        tope = self._tope()
        if tope <= _EPS:
            return None
        return m * (_DECIMA / tope)

    def soltar(self, desde: float, hasta: float, masa: float) -> float | None:
        """Dólares a soltar entre dos precios. None si este modo no habla.

        None también si el precio sigue del lado malo de la Oz: todavía
        no es terreno de descarga. Cero es otra cosa: ya está en terreno
        y este tramo no avanza, o no queda masa.
        """
        if not self.habla:
            return None
        m = _masa(masa)
        if m <= 0:
            return 0.0
        tope = self._tope()
        if tope <= _EPS:
            return None
        a = self._adelante(desde)
        b = self._adelante(hasta)
        if b < -_EPS and a <= _EPS:
            return None
        if b <= a + _EPS:
            if a >= tope - _EPS and b >= tope - _EPS and a > _EPS:
                return m
            return 0.0
        a_c = min(max(a, 0.0), tope)
        b_c = min(max(b, 0.0), tope)
        cruzadas = b_c - a_c
        if cruzadas <= _EPS:
            if a >= tope - _EPS or b_c >= tope - _EPS:
                return m
            return 0.0
        quedan = tope - a_c
        if quedan <= _EPS:
            return m
        return min(m, m * cruzadas / quedan)

    def fin(self) -> float | None:
        """Precio donde la descarga tiene que haber vaciado. None si no habla."""
        if not self.habla or self.oz <= 0:
            return None
        tope = self._tope()
        if self.lado == "LONG":
            return self.oz * (1.0 + tope)
        return self.oz * (1.0 - tope)

    def _tramo_valido(self) -> bool:
        if self.oz <= 0 or self.meta <= 0:
            return False
        if self.lado == "LONG":
            return self.meta > self.oz + self.oz * 1e-9
        return self.oz > self.meta + self.oz * 1e-9

    def _adelante(self, precio: float) -> float:
        px = float(precio or 0)
        if self.lado == "LONG":
            return (px - self.oz) / self.oz
        return (self.oz - px) / self.oz

    def _tope(self) -> float:
        span = self._adelante(self.meta)
        if self.clase == "dificil":
            return span / 2.0
        return span


def _masa(masa: float) -> float:
    m = float(masa or 0)
    if m <= _EPS:
        return 0.0
    return m
