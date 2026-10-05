"""Fantasma, después del hacha del verdugo. El cazador vivo no lee esto.

El hacha cortó. Las manos se quedan vacías. No abre el lado contrario
en el mismo golpe, ni persigue el resto de la explosión.

La punta tiene que alejarse al menos una puerta del corte. Si no,
el estornudo no es explosión y no despierta a nadie. El primer respiro
de una puerta entera, medido desde esa punta, es el nuevo cero.
Desde un alto, el respiro compra largo. Desde un bajo, vende corto.
"""
from __future__ import annotations

_EPS = 1e-12


class Fantasma:
    def __init__(self, corte: float, puerta: float) -> None:
        self.corte = float(corte or 0)
        self.puerta = float(puerta or 0)
        self.punta_alta = self.corte
        self.punta_baja = self.corte
        self.cero = 0.0
        self.lado = ""
        self.mando = ""

    def despierto(self) -> bool:
        return self.cero > 0 and self.lado in ("LONG", "SHORT")

    def ver(self, precio: float) -> bool:
        """Un latido. True solo el golpe en que nace el nuevo cero.

        Si este mismo golpe es la punta (o el desplome que se pasa de la
        otra punta), todavía no hay respiro: no despierta.
        """
        px = float(precio or 0)
        if self.despierto() or px <= 0 or self.corte <= 0 or self.puerta <= 0:
            return False
        alto = px if px > self.punta_alta else self.punta_alta
        bajo = px if px < self.punta_baja else self.punta_baja
        sube = (alto - self.corte) / self.corte
        baja = (self.corte - bajo) / self.corte
        hizo_alto = px > self.punta_alta + _EPS
        hizo_bajo = px < self.punta_baja - _EPS
        self.punta_alta = alto
        self.punta_baja = bajo
        if hizo_bajo and baja + _EPS >= self.puerta and baja + _EPS >= sube:
            self.mando = "abajo"
            return False
        if hizo_alto and sube + _EPS >= self.puerta and sube + _EPS >= baja:
            self.mando = "arriba"
            return False
        if self.mando == "arriba" and px <= alto * (1.0 - self.puerta) + _EPS:
            self._nacer("LONG", alto * (1.0 - self.puerta))
            return True
        if self.mando == "abajo" and px >= bajo * (1.0 + self.puerta) - _EPS:
            self._nacer("SHORT", bajo * (1.0 + self.puerta))
            return True
        return False

    def _nacer(self, lado: str, px: float) -> None:
        self.lado = lado
        self.cero = float(px)
