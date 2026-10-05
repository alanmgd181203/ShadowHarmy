"""Reloj de la descarga. El cazador vivo no lee esto.

Beru suelta mientras el precio todavía camina hacia la masacre.
En cada paso mira la clase que el camino ya tiene. No espera a
sellarla: preguntar recién al llegar vacía los cuatrocientos de
un golpe, y el de diez y el de veinte no llegan a correr.

La clase sellada sigue siendo otra cosa. Solo se escribe al
tocar la masacre, y lo de después no la cambia. Hiron usa esa.

Si el retroceso que la vuelve difícil cae ya pasada la mitad,
esa mitad ya se caminó en silencio. Lo que queda no sale de un
golpe: se reparte en la mitad del camino que todavía falta, y
la bolsa queda vacía antes de la marca.
"""
from __future__ import annotations

from cirugias.hiron.descarga import Descarga
from cirugias.hiron.subida import Subida

_EPS = 1e-12


class Reloj:
    def __init__(self, color: str, lado: str, oz: float, meta: float) -> None:
        self.lado = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        self.oz = float(oz or 0)
        self.meta = float(meta or 0)
        self.subida = Subida(color, self.lado)
        self.subida.anclar_oz(self.oz)
        self.subida.anclar_meta(self.meta)
        self._precio = self.oz
        self._tarde_fin: float | None = None

    def ver(self, precio: float, masa: float) -> float | None:
        """Dólares de este paso. None si Beru sigue con su ritmo de siempre."""
        px = float(precio or 0)
        if px <= 0 or self.oz <= 0 or self.meta <= 0:
            return None
        desde = self._precio
        self.subida.ver(px)
        self._precio = px
        clase = self.subida.ahora()
        if clase not in ("normal", "dificil"):
            return None
        if clase == "dificil" and self._pasado_el_medio(px):
            return self._soltar_tarde(desde, px, masa)
        return Descarga(self.lado, clase, self.oz, self.meta).soltar(desde, px, masa)

    def clase_sellada(self) -> str | None:
        return self.subida.clase()

    def _pasado_el_medio(self, precio: float) -> bool:
        medio = self._adelante(self.meta) / 2.0
        return self._adelante(precio) >= medio - 1e-9

    def _abrir_tarde(self, precio: float) -> float:
        if self._tarde_fin is not None:
            return self._tarde_fin
        aqui = self._adelante(precio)
        falta = self._adelante(self.meta) - aqui
        if falta <= _EPS:
            self._tarde_fin = self._adelante(self.meta)
        else:
            self._tarde_fin = aqui + falta / 2.0
        return self._tarde_fin

    def _soltar_tarde(self, desde: float, hasta: float, masa: float) -> float | None:
        m = float(masa or 0)
        if m <= _EPS:
            return 0.0
        fin = self._abrir_tarde(hasta)
        a = self._adelante(desde)
        b = self._adelante(hasta)
        if b < -_EPS and a <= _EPS:
            return None
        if b <= a + _EPS:
            return 0.0
        a_c = min(max(a, 0.0), fin)
        b_c = min(max(b, 0.0), fin)
        cruzadas = b_c - a_c
        if cruzadas <= _EPS:
            if a >= fin - _EPS or b >= fin - _EPS:
                return m
            return 0.0
        quedan = fin - a_c
        if quedan <= _EPS:
            return m
        return min(m, m * cruzadas / quedan)

    def _adelante(self, precio: float) -> float:
        px = float(precio or 0)
        if self.lado == "LONG":
            return (px - self.oz) / self.oz
        return (self.oz - px) / self.oz
