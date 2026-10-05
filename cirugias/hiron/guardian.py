"""Hiron, guardián de la ganancia. Paso 6. El cazador vivo no lee esto.

No abre redes y no suelta por tramos. Solo la Oz de la masacre.

No nace al tocar el precio quieto, ni porque una red se haya armado
más arriba. Nace cuando el precio ya se alejó de ese precio:

- limpia: 1 %
- normal: 0,7 %
- difícil: 0,5 %

A partir de ahí caza como Beru. El extremo solo avanza a favor.
La Oz queda detrás, a esa distancia. Si el precio se regresa y la
toca, cierra lo condenado en el activador. Si ahora queda menos,
cierra ese menos. La grasa de después no sale. Beru no se apaga.
"""
from __future__ import annotations

from cirugias.hiron.masacre_precio import distancia_activador


class Hiron:
    def __init__(self, lado: str, clase: str, meta: float) -> None:
        self.lado = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        self.clase = str(clase or "").strip().lower()
        self.meta = float(meta or 0)
        self.gap = distancia_activador(self.clase)
        self.extremo: float | None = None
        self.oz: float | None = None
        self.nacido = False
        self.tocada = False
        self.beru_sigue = True
        self.condenadas: float | None = None

    def ver(self, precio: float, monedas: float | None = None) -> bool:
        """True solo en la impresión que toca la Oz. Nacer no es tocarla.

        Las monedas del activador quedan condenadas en ese mismo latido.
        Las de después no suben ese techo.
        """
        if self.gap is None or self.meta <= 0 or self.tocada:
            return False
        px = float(precio or 0)
        if px <= 0:
            return False
        if not self.nacido:
            if self._distancia(px) + 1e-12 < self.gap:
                return False
            self._sentar(px)
            self._mirar_condena(monedas)
            return False
        if self._extremo_nuevo(px):
            self._sentar(px)
            return False
        if self.oz is not None and self._toca(px):
            self.tocada = True
            return True
        return False

    def a_cerrar(self, cantidad: float) -> float | None:
        """Lo condenado en el activador, si la Oz ya se tocó.

        None si todavía no se tocó. Si ahora queda menos, cierra ese
        menos. La grasa de después no sale. Sin condena anotada, cierra
        lo que haya: no inventa un techo.
        """
        if not self.tocada:
            return None
        c = float(cantidad or 0)
        if c <= 1e-12:
            return 0.0
        if self.condenadas is None:
            return c
        return min(c, self.condenadas)

    def _mirar_condena(self, monedas: float | None) -> None:
        """Solo en el latido en que nace. Después, la grasa no entra."""
        if monedas is None or self.condenadas is not None:
            return
        monto = float(monedas)
        if monto < -1e-12:
            return
        self.condenadas = max(0.0, monto)

    def _distancia(self, px: float) -> float:
        if self.lado == "LONG":
            return (px - self.meta) / self.meta
        return (self.meta - px) / self.meta

    def _sentar(self, px: float) -> None:
        self.nacido = True
        self.extremo = px
        if self.lado == "LONG":
            self.oz = px * (1.0 - self.gap)
        else:
            self.oz = px * (1.0 + self.gap)

    def _extremo_nuevo(self, px: float) -> bool:
        assert self.extremo is not None
        paso = self.extremo * 1e-15
        if self.lado == "LONG":
            return px > self.extremo + paso
        return px < self.extremo - paso

    def _toca(self, px: float) -> bool:
        assert self.oz is not None
        if self.lado == "LONG":
            return px <= self.oz * (1.0 + 1e-12)
        return px >= self.oz * (1.0 - 1e-12)
