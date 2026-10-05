"""Un solo escudo, dos inversos. Paso 4. El escudo vivo no lee esto.

Beru caza en el lineal. Aquí eso solo dice el lado:
más corto en la bolsa → el escudo va largo.
Más largo en la bolsa → el escudo va corto.
Dentro del polvo, no hay lado.

Las capas son del inverso, rey o reina, y las dos van
del mismo lado. El lineal no se anota como capa.
Al girar la bolsa, lo ya puesto no cambia de nombre
y no se borra solo: deja de ser la cubierta de ahora.
"""
from __future__ import annotations

from cirugias.escudo_dual.capas import Libro

_EPS = 1e-9


class Escudo:
    def __init__(self) -> None:
        self._libros = {"LONG": Libro(), "SHORT": Libro()}
        self.lado: str | None = None

    def ver_bolsa(
        self,
        largo_usd: float,
        corto_usd: float,
        *,
        polvo: float = 0.0,
    ) -> str | None:
        """El lado que pide la bolsa. No mueve las capas de sitio."""
        neto = _neto(largo_usd, corto_usd)
        umbral = max(0.0, float(polvo or 0))
        if abs(neto) <= umbral + _EPS:
            self.lado = None
            return None
        self.lado = "LONG" if neto > 0 else "SHORT"
        return self.lado

    def cubierta(self) -> float:
        """Lo que cuenta como escudo de ahora. El otro lado no se suma."""
        libro = self._activo()
        if libro is None:
            return 0.0
        return libro.total()

    def guardado(self, lado: str) -> float:
        """Lo que quedó en un lado, aunque ya no sea el de ahora."""
        libro = self._libros.get(lado)
        if libro is None:
            return 0.0
        return libro.total()

    def engordar(self, cantidad: float, **datos: bool | float | None) -> str | None:
        libro = self._activo()
        if libro is None:
            return None
        return libro.engordar(cantidad, **datos)  # type: ignore[arg-type]

    def desinflar(self, cantidad: float, **datos: bool | None) -> float:
        """Suelta del lado que manda. Si la bolsa quedó neutra y solo
        un lado tiene capas, suelta de ese. Si los dos tienen, no elige.
        """
        libro = self._a_soltar()
        if libro is None:
            return 0.0
        return libro.desinflar(cantidad, **datos)  # type: ignore[arg-type]

    def _activo(self) -> Libro | None:
        if self.lado not in self._libros:
            return None
        return self._libros[self.lado]

    def _a_soltar(self) -> Libro | None:
        activo = self._activo()
        if activo is not None:
            return activo
        con_capas = [
            libro for libro in self._libros.values() if libro.total() > _EPS
        ]
        if len(con_capas) == 1:
            return con_capas[0]
        return None


def _neto(largo_usd: float, corto_usd: float) -> float:
    """Igual que el escudo de hoy: corto menos largo. Un número negativo no cuenta."""
    largo = max(0.0, float(largo_usd or 0))
    corto = max(0.0, float(corto_usd or 0))
    return corto - largo
