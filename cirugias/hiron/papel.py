"""La ganancia de la pierna. Paso 2. El cazador vivo no lee esto.

La promesa no camina el precio ni mira el promedio. Es la pierna
completa de ahora: lo negociado en ese lado, al uno por ciento
redondo. El peaje y el spread no la recortan. A medio camino se
cuenta igual: la recta se supone y vacía lo que falta.
"""
from __future__ import annotations

from cirugias.hiron.viaje import PEAJE, Viaje
from cirugias.sala_por_color.sala import oz_pct, red_pct

_TOPE = 8000
# Umbral fijo. Cien de pierna prometen un dólar. No se le resta peaje.
_UMBRAL = 0.01


def ganancia_de_la_pierna(masa: float) -> float | None:
    """Lo que rinde vaciar la pierna completa, aunque la recta no haya acabado.

    Cien de corto, o cien de largo, prometen uno. No es la masa que
    todavía falta ni la que ya se recompró sola.
    """
    monto = max(0.0, float(masa or 0))
    if monto <= 0:
        return None
    return monto * _UMBRAL


def cuenta_de_la_pierna(
    toques: list[tuple[float, float]],
    lado: str,
) -> dict[str, float]:
    """La pierna es lo que se abrió en este lado. Un cierre no la recorta.

    Cada toque es (cambio de monedas, dólares de esa orden). Comprar
    suma monedas. Si una orden voltea, solo cuenta el trozo del lado
    que se pregunta. ``cerrada`` es lo ya soltado: entra en la historia
    y no baja la promesa.
    """
    casa = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
    monedas = 0.0
    pierna = 0.0
    cerrada = 0.0
    for delta, dolares in toques:
        cambio = float(delta or 0)
        monto = max(0.0, float(dolares or 0))
        if abs(cambio) <= 1e-12 or monto <= 0:
            monedas += cambio
            continue
        antes = monedas
        despues = monedas + cambio
        if casa == "LONG":
            nuevos = max(despues, 0.0) - max(antes, 0.0)
            pierde = max(antes, 0.0) - max(despues, 0.0)
        else:
            nuevos = max(-despues, 0.0) - max(-antes, 0.0)
            pierde = max(-antes, 0.0) - max(-despues, 0.0)
        parte = monto / abs(cambio)
        if nuevos > 0:
            pierna += parte * nuevos
        if pierde > 0:
            cerrada += parte * pierde
        monedas = despues
    return {"pierna": pierna, "cerrada": cerrada, "monedas": monedas}


def paso_del_tonto(color: str, lado: str) -> float:
    """Distancia entre toques: la red de esa sala menos la Oz de 0,2."""
    d = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
    paso = float(red_pct(color, d) - oz_pct(color))
    if paso <= 1e-12 or paso >= 1:
        raise ValueError(f"paso inutil {paso}")
    return paso


class Papel:
    def __init__(self, color: str, lado: str) -> None:
        self.color = str(color or "amarillo")
        self.lado = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        self.paso = paso_del_tonto(self.color, self.lado)
        self.peaje = PEAJE
        self.ancla: float | None = None
        self.toques: list[tuple[str, float]] = []
        self._sombra = Viaje(self.lado)
        self._sombra.peaje = self.peaje

    def reiniciar(self) -> None:
        """Borra la cuenta y se queda en el mismo lado."""
        self.ancla = None
        self.toques.clear()
        self._sombra = Viaje(self.lado)
        self._sombra.peaje = self.peaje

    def voltear(self) -> None:
        """De largo a corto, o al revés. La cuenta anterior nace de cero."""
        self.lado = "SHORT" if self.lado == "LONG" else "LONG"
        self.paso = paso_del_tonto(self.color, self.lado)
        self.reiniciar()

    def enganchar(self, precios: list[float]) -> None:
        """El camino de los que ya están despiertos. Una sola vez.

        La masa no entra aquí. Se pregunta después, con lo que Beru
        haya negociado en ese momento. Volver a recorrer el archivo
        desde el origen inventaría toques que no hubo.
        """
        if self.ancla is not None or self.toques:
            raise RuntimeError("papel: el recorrido ya está andado")
        for px in precios:
            self.ver_precio(px)

    def ver_precio(self, precio: float) -> None:
        px = float(precio or 0)
        if px <= 0:
            return
        if self.ancla is None:
            self._anotar("abrir", px)
            return
        self._alcanzar(px)

    def _alcanzar(self, px: float) -> None:
        """Llega al precio por peldaños. La bolsa muerta, si sigue de largo, voltea."""
        vueltas = 0
        while True:
            avanzo = False
            while self._en_apertura(px):
                self._anotar("abrir", self._precio_abre())
                avanzo = True
                vueltas += 1
                if vueltas > _TOPE:
                    raise RuntimeError("papel: demasiados toques en un precio")
            while self._en_descarga(px):
                vueltas += 1
                if vueltas > _TOPE:
                    raise RuntimeError("papel: demasiados toques en un precio")
                if not self._sombra.vivo():
                    nacimiento = self._precio_descarga()
                    self.voltear()
                    self._anotar("abrir", nacimiento)
                    avanzo = True
                    break
                self._anotar("reducir", self._precio_descarga())
                avanzo = True
            if not avanzo:
                return

    def cuentas(
        self,
        masa_negociada: float,
        marca: float | None = None,
        toques: int | None = None,
    ) -> dict:
        """La masa absoluta se parte entre todos los toques.

        Diez largos y cinco cortos no es mitad y mitad: el largo se queda
        diez partes y el corto cinco. Si ``toques`` viene, es el total de
        los dos lados, y esta cuenta usa esa misma parte.
        """
        masa = max(0.0, float(masa_negociada or 0))
        n = len(self.toques)
        divisor = n if toques is None else int(toques)
        vacio = {
            "n": 0,
            "trozo": 0.0,
            "montado": 0.0,
            "quiebre": None,
            "entrada": None,
            "cantidad": 0.0,
            "dolares": 0.0,
            "salida": None,
            "vivo": False,
        }
        promesa = ganancia_de_la_pierna(masa)
        if n == 0 or divisor <= 0 or masa <= 0:
            vacio["salida"] = promesa
            return vacio
        trozo = masa / divisor
        viaje = Viaje(self.lado)
        viaje.peaje = self.peaje
        puerta = None
        for accion, px in self.toques:
            coins = trozo / px
            if accion == "abrir":
                viaje.abrir(coins, px)
            elif puerta is not None and self._en_tablas(px, puerta):
                # Esta suelta ya estaba en la recta. No reescribe el cero.
                viaje.reducir(coins, px)
                if not viaje.vivo():
                    puerta = None
                continue
            else:
                viaje.reducir(coins, px)
            if not viaje.vivo():
                puerta = None
                continue
            nueva, _ganancia = self._camino(viaje, trozo, px, viaje.quiebre())
            if nueva is not None:
                puerta = nueva
        vivo = viaje.vivo()
        golpe = viaje.quiebre()
        marca_px = float(marca if marca is not None else (self.ancla or 0))
        if vivo and golpe is not None and marca_px > 0:
            if self.lado == "LONG":
                dolares = (marca_px - golpe) * viaje.cantidad
            else:
                dolares = (golpe - marca_px) * viaje.cantidad
        else:
            # Bolsa muerta: lo que quedó en la caja, neto de comisión.
            # Cobrado menos pagado infla esa cifra y no es la ganancia prometida.
            dolares = -viaje.caja if self.lado == "LONG" else viaje.caja
        _resto, _subida = self._camino(viaje, trozo, marca_px, golpe)
        cero = puerta if vivo else None
        salida = promesa
        abiertos = sum(1 for accion, _px in self.toques if accion == "abrir")
        montado = max(0.0, trozo * (abiertos - (n - abiertos)))
        if vivo and montado <= 0 and viaje.cantidad > 0 and marca_px > 0:
            montado = viaje.cantidad * marca_px
        return {
            "n": n,
            "trozo": trozo,
            "montado": montado,
            "quiebre": cero,
            "entrada": viaje.entrada(),
            "cantidad": viaje.cantidad if vivo else 0.0,
            "dolares": dolares,
            "salida": salida,
            "vivo": vivo,
        }

    def _camino(
        self,
        viaje: Viaje,
        trozo: float,
        marca: float,
        golpe: float | None,
    ) -> tuple[float | None, float | None]:
        """Cero del camino, y dólares desde ahí hasta vaciar.

        El cero es el precio de la bolsa. Si antes de llegar a él hay
        peldaños enteros, se suelta en esos y la comisión empuja el cero.
        Si el peldaño siguiente ya lo pasaría, el cero no salta hasta ese
        peldaño: un engorde más barato lo baja. La ganancia es lo que se
        cobra de ahí hasta vaciar.
        """
        if not viaje.vivo() or golpe is None or marca <= 0 or trozo <= 0:
            return None, None
        sombra = self._copia(viaje)
        px = self._arranque(marca)
        for _ in range(_TOPE):
            if not sombra.vivo():
                return None, None
            q = sombra.quiebre()
            if q is None:
                return None, None
            siguiente = self._adelante(px)
            if self._en_tablas(px, q) or (siguiente > 0 and self._en_tablas(siguiente, q)):
                ganancia = self._cobro(sombra, trozo, px)
                if ganancia is None or ganancia <= 1e-9:
                    return float(q), None
                return float(q), ganancia
            if siguiente <= 0:
                return None, None
            tomado = sombra.reducir(trozo / siguiente, siguiente)
            if tomado <= 0:
                return None, None
            px = siguiente
            if not sombra.vivo():
                return self._vacio_en_tablas(px, sombra)
        return None, None

    def _cobro(self, viaje: Viaje, trozo: float, desde: float) -> float | None:
        """Dólares de soltar lo montado, peldaño a peldaño, desde aquí."""
        if not viaje.vivo() or desde <= 0 or trozo <= 0:
            return None
        sombra = self._copia(viaje)
        caja = viaje.caja
        px = desde
        cobrado = 0.0
        for _ in range(_TOPE):
            if not sombra.vivo():
                break
            px = self._adelante(px)
            if px <= 0:
                return None
            tomado = sombra.reducir(trozo / px, px)
            if tomado <= 0:
                return None
            neto = tomado * px
            if self.lado == "LONG":
                cobrado += neto * (1.0 - self.peaje)
            else:
                cobrado += neto * (1.0 + self.peaje)
        if sombra.vivo():
            return None
        if self.lado == "LONG":
            return cobrado - caja
        return caja - cobrado

    def _vacio_en_tablas(self, px: float, sombra: Viaje) -> tuple[float | None, float | None]:
        """La bolsa se acabó en este peldaño. La caja que sobra es la ganancia."""
        if self.lado == "LONG":
            ganancia = -sombra.caja
        else:
            ganancia = sombra.caja
        if ganancia <= 1e-9:
            return None, None
        return px, ganancia

    def _copia(self, viaje: Viaje) -> Viaje:
        sombra = Viaje(viaje.lado)
        sombra.peaje = viaje.peaje
        sombra.cantidad = viaje.cantidad
        sombra.caja = viaje.caja
        return sombra

    def _adelante(self, px: float) -> float:
        if self.lado == "LONG":
            return px * (1.0 + self.paso)
        return px * (1.0 - self.paso)

    def _arranque(self, marca: float) -> float:
        """Si el precio aún no llega al siguiente peldaño, el camino sale del último toque.

        Un ruido dentro del peldaño no inventa otra escalera.
        """
        if self.ancla is None:
            return marca
        ancla = float(self.ancla)
        bajo = ancla * (1.0 - self.paso)
        alto = ancla * (1.0 + self.paso)
        if bajo < marca < alto:
            return ancla
        return marca

    def _en_tablas(self, px: float, cero: float) -> bool:
        if self.lado == "LONG":
            return px + 1e-12 >= cero
        return px - 1e-12 <= cero

    def _salida_recta(
        self,
        viaje: Viaje,
        trozo: float,
        marca: float,
        quiebre: float | None,
    ) -> float | None:
        """Dólares si, desde aquí, el precio va recto y suelta lo montado hasta cero.

        Callá si no hay bolsa, o si esa bolsa todavía no va ganando.
        El primer peldaño es el siguiente, no otra venta en el mismo precio.
        """
        if not viaje.vivo() or quiebre is None or marca <= 0 or trozo <= 0:
            return None
        if self.lado == "LONG" and marca <= float(quiebre):
            return None
        if self.lado == "SHORT" and marca >= float(quiebre):
            return None
        return self._cobro(viaje, trozo, marca)

    def _anotar(self, accion: str, px: float) -> None:
        self.toques.append((accion, px))
        self.ancla = px
        coins = 1.0 / px
        if accion == "abrir":
            self._sombra.abrir(coins, px)
        else:
            self._sombra.reducir(coins, px)

    def _precio_abre(self) -> float:
        assert self.ancla is not None
        if self.lado == "LONG":
            return self.ancla * (1.0 - self.paso)
        return self.ancla * (1.0 + self.paso)

    def _precio_descarga(self) -> float:
        assert self.ancla is not None
        if self.lado == "LONG":
            return self.ancla * (1.0 + self.paso)
        return self.ancla * (1.0 - self.paso)

    def _tol(self) -> float:
        assert self.ancla is not None
        return self.ancla * 1e-9

    def _en_apertura(self, precio: float) -> bool:
        assert self.ancla is not None
        if self.lado == "LONG":
            return precio <= self._precio_abre() + self._tol()
        return precio >= self._precio_abre() - self._tol()

    def _en_descarga(self, precio: float) -> bool:
        assert self.ancla is not None
        if self.lado == "LONG":
            return precio >= self._precio_descarga() - self._tol()
        return precio <= self._precio_descarga() + self._tol()
