"""Clase de la subida. Paso 4. El cazador vivo no lee esto.

El cero está en la última Oz. El otro extremo es el precio de la
masacre, y ese precio no se corre.

No se cuentan las órdenes. Una mecha más chica que el peldaño
no es un retroceso. El retroceso es un peldaño entero en contra.

La subida limpia es la que, desde su último retroceso, llega a
la masacre sin otro peldaño en contra.

- Si ese tramo empieza en el primer 25 % del camino, es limpia.
- Si empieza entre el 25 % y el 75 %, es normal.
- Si empieza pasada el 75 %, es difícil.

Se sella al tocar la masacre. Lo que pase después no la cambia.
"""
from __future__ import annotations

from cirugias.hiron.papel import paso_del_tonto

_EPS = 1e-9


class Subida:
    def __init__(self, color: str, lado: str) -> None:
        self.lado = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        self.paso = paso_del_tonto(color, self.lado)
        self.oz: float | None = None
        self.meta: float | None = None
        self._precios: list[float] = []
        self._clase: str | None = None
        self.arranque: float | None = None

    def anclar_oz(self, precio: float) -> None:
        if self._clase is not None:
            return
        px = float(precio or 0)
        if px <= 0:
            return
        self.oz = px
        self._precios = [px]

    def anclar_meta(self, precio: float) -> None:
        if self._clase is not None or self.meta is not None:
            return
        px = float(precio or 0)
        if px <= 0:
            return
        self.meta = px
        self._intentar()

    def ver(self, precio: float) -> str | None:
        if self._clase is not None:
            return self._clase
        px = float(precio or 0)
        if px <= 0 or self.oz is None:
            return None
        self._precios.append(px)
        return self._intentar()

    def clase(self) -> str | None:
        return self._clase

    def ahora(self) -> str | None:
        """La clase del camino ya visto. No sella.

        Beru la necesita mientras todavía camina. La sellada, la de
        Hiron, sigue saliendo solo al tocar la masacre.
        """
        if self._clase is not None:
            return self._clase
        if self.oz is None or self.meta is None or not self._precios:
            return None
        if not self._tramo_valido():
            return None
        nombre, _arranque = self._leer(self._precios)
        return nombre

    def _intentar(self) -> str | None:
        if self._clase is not None:
            return self._clase
        if self.oz is None or self.meta is None or not self._precios:
            return None
        if not self._tramo_valido():
            return None
        if not self._ya_toco():
            return None
        nombre, arranque = self._leer(self._hasta_la_meta())
        if nombre is None:
            return None
        self._clase = nombre
        self.arranque = arranque
        return nombre

    def _tramo_valido(self) -> bool:
        assert self.oz is not None and self.meta is not None
        if self.lado == "LONG":
            return self.meta > self.oz + _EPS
        return self.oz > self.meta + _EPS

    def _ya_toco(self) -> bool:
        assert self.meta is not None
        tol = self.meta * 1e-9
        for px in self._precios:
            if self.lado == "LONG" and px >= self.meta - tol:
                return True
            if self.lado == "SHORT" and px <= self.meta + tol:
                return True
        return False

    def _hasta_la_meta(self) -> list[float]:
        assert self.meta is not None
        tol = self.meta * 1e-9
        out: list[float] = []
        for px in self._precios:
            out.append(px)
            if self.lado == "LONG" and px >= self.meta - tol:
                break
            if self.lado == "SHORT" and px <= self.meta + tol:
                break
        return out

    def _leer(self, tramo: list[float]) -> tuple[str | None, float | None]:
        if len(tramo) < 1:
            return None, None
        inicio = tramo[0]
        pico = tramo[0]
        for px in tramo[1:]:
            if self.lado == "LONG":
                if px > pico:
                    pico = px
                if px <= pico * (1.0 - self.paso) + pico * 1e-12:
                    inicio = px
                    pico = px
            else:
                if px < pico:
                    pico = px
                if px >= pico * (1.0 + self.paso) - pico * 1e-12:
                    inicio = px
                    pico = px
        frac = self._fraccion(inicio)
        if frac is None:
            return None, None
        if frac <= 0.25 + 1e-12:
            return "limpia", frac
        if frac <= 0.75 + 1e-12:
            return "normal", frac
        return "dificil", frac

    def _fraccion(self, inicio: float) -> float | None:
        assert self.oz is not None and self.meta is not None
        if self.lado == "LONG":
            span = self.meta - self.oz
            if span <= _EPS:
                return None
            frac = (inicio - self.oz) / span
        else:
            span = self.oz - self.meta
            if span <= _EPS:
                return None
            frac = (self.oz - inicio) / span
        if frac < 0:
            return 0.0
        if frac > 1:
            return 1.0
        return frac
