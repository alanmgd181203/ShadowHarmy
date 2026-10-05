"""Precio de la masacre. Paso 3. El cazador vivo no lee esto.

No es el quiebre del tonto ni el de Beru.
La promesa sigue siendo el uno por ciento de la pierna entera.
El suelo es otra cosa: el uno por ciento de las monedas que todavía
están. Lo ya soltado no se le vuelve a cobrar a lo que queda.
Los primeros peldaños cobran menos, así que ese último puede quedar
más lejos que cerrar todo de un golpe.

La clase de la subida no mueve ese precio. Solo dice cuándo hay que
volver a leer la bolsa. Lejos, un engorde chico espera. Cerca, y en
la limpia cuando el precio ya se arrima, la cacería de verdad se lee
enseguida. El activador, más allá del suelo, lo deja quieto.
Pisar el suelo no. Lo que se cierra es lo que todavía queda.
"""
from __future__ import annotations

import math

from cirugias.hiron.papel import ganancia_de_la_pierna, paso_del_tonto
from cirugias.hiron.viaje import Viaje

_EPS = 1e-9
_GAP = {
    "limpia": 0.01,
    "normal": 0.007,
    "dificil": 0.005,
}


def caja_con_lo_realizado(
    lado: str,
    promedio: float,
    cantidad: float,
    realizado: float,
) -> float:
    """La caja del cero, con lo ya cerrado metido.

    El promedio de la casa no se mueve al soltar un trozo. Lo realizado
    sí: en contra empuja el cero, a favor lo arrima. El uno por ciento
    se pide después, por encima de ese cero.
    """
    base = float(promedio or 0) * float(cantidad or 0)
    hecho = float(realizado or 0)
    if str(lado or "").upper() == "SHORT":
        return base + hecho
    return base - hecho


def distancia_activador(clase: str) -> float | None:
    """Lo lejos del suelo donde nace la Oz. Lo pone el tipo de subida."""
    nombre = str(clase or "").strip().lower().replace("í", "i")
    return _GAP.get(nombre)


# Más de cinco peldaños: todavía lejos. La limpia, al arrimarse
# (quince peldaños), ya lee cada cacería. Un engorde de menos de
# una décima de la bolsa, lejos, puede esperar.
_CERCA = 5
_ARRIME_LIMPIA = 15
_CAMBIO_CHICO = 0.10


def golpe_de_un_golpe(
    lado: str,
    quiebre: float | None,
    cantidad: float,
    dolares: float,
) -> float | None:
    """Cerrar todas las monedas en un solo precio. La mecha queda más lejos."""
    q = float(quiebre) if quiebre is not None else 0.0
    c = float(cantidad or 0)
    d = float(dolares or 0)
    if quiebre is None or c <= _EPS or d <= _EPS:
        return None
    lado_u = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
    if lado_u == "LONG":
        return q + d / c
    return q - d / c


def _raiz_larga(golpe_sobre_cero: float) -> float:
    """R > 1 tal que el promedio de la recta, de 1 a R, es ese cociente."""
    objetivo = float(golpe_sobre_cero)
    lo = 1.0
    hi = max(objetivo, 1.0 + 1e-6)
    for _ in range(80):
        if (hi - 1.0) / math.log(hi) >= objetivo:
            break
        hi *= 2.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if mid <= 1.0:
            lo = mid
            continue
        if (mid - 1.0) / math.log(mid) >= objetivo:
            hi = mid
        else:
            lo = mid
    return hi


def _raiz_corta(golpe_sobre_cero: float) -> float:
    """u > 1. El promedio de bajar de 1 a 1/u es ese cociente, menor que 1."""
    objetivo = float(golpe_sobre_cero)
    lo = 1.0
    hi = 2.0
    for _ in range(80):
        if (1.0 - 1.0 / hi) / math.log(hi) <= objetivo:
            break
        hi *= 2.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if mid <= 1.0:
            lo = mid
            continue
        if (1.0 - 1.0 / mid) / math.log(mid) <= objetivo:
            hi = mid
        else:
            lo = mid
    return hi


def precio_para_ganar(
    lado: str,
    quiebre: float | None,
    cantidad: float,
    dolares: float,
    paso: float | None = None,
) -> float | None:
    """Último precio de la mecha recta donde ya se juntaron esos dólares.

    Las sueltas se reparten parejo entre el cero y ese final.
    Si el golpe de un solo precio cabe en un peldaño, la mecha no se estira.
    """
    golpe = golpe_de_un_golpe(lado, quiebre, cantidad, dolares)
    if golpe is None or quiebre is None:
        return None
    q = float(quiebre)
    lado_u = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
    if q <= 0 or golpe <= 0:
        return golpe
    if paso is None:
        paso = paso_del_tonto("verde", lado_u)
    paso_f = float(paso)
    if paso_f <= 0:
        return golpe
    if lado_u == "LONG":
        if golpe <= q:
            return golpe
        ultimo = q * _raiz_larga(golpe / q)
        if ultimo <= q * (1.0 + paso_f):
            return golpe
        return ultimo
    if golpe >= q:
        return golpe
    ultimo = q / _raiz_corta(golpe / q)
    if ultimo <= 0 or ultimo >= q * (1.0 - paso_f):
        return golpe
    return ultimo


class Sello:
    """El suelo se reescribe hasta el activador. Después se queda.

    La bolsa que cierra, no. Lejos, un engorde chico no lo mueve todavía.
    """

    def __init__(self, color: str = "verde") -> None:
        self.color = str(color or "verde")
        self._precio = {"LONG": None, "SHORT": None}
        self._quieto = {"LONG": False, "SHORT": False}
        self._bolsa = {"LONG": None, "SHORT": None}
        self._leido = {"LONG": None, "SHORT": None}

    def leer_papel(
        self,
        viaje: Viaje,
        masa_pierna: float,
        precio: float | None = None,
        clase: str | None = None,
    ) -> float | None:
        """La promesa es la pierna entera. El suelo, lo que aún sigue.

        Cien de pierna son un dólar, y eso queda anotado. El suelo no
        le pide a las monedas que quedan que junten también lo ya
        soltado: solo el uno por ciento de lo que todavía está.
        """
        promesa = ganancia_de_la_pierna(masa_pierna)
        lado = viaje.lado
        self._leido[lado] = promesa
        if promesa is None or not viaje.vivo():
            self._precio[lado] = None
            self._quieto[lado] = False
            self._bolsa[lado] = None
            return None
        cero = viaje.quiebre()
        if cero is None or cero <= 0:
            return None
        abierta = float(viaje.cantidad) * float(cero)
        return self.marcar(viaje, ganancia_de_la_pierna(abierta) or 0.0, precio, clase)

    def promesa(self, lado: str) -> float | None:
        """Los dólares que leyó de la pierna. No es la marca de hoy."""
        lado_u = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        return self._leido[lado_u]

    def marcar(
        self,
        viaje: Viaje,
        dolares: float,
        precio: float | None = None,
        clase: str | None = None,
    ) -> float | None:
        """Suelo de ahora. Si el activador ya se tocó, el de entonces.

        ``dolares`` es la promesa del papel: el uno por ciento de la
        pierna. Sin precio de mercado, o sin tipo de subida, no hay
        activador que tocar: la cuenta se reescribe.
        """
        lado = viaje.lado
        if not viaje.vivo():
            self._precio[lado] = None
            self._quieto[lado] = False
            self._bolsa[lado] = None
            return None
        if self._quieto[lado]:
            return self._precio[lado]
        guardado = self._precio[lado]
        if (
            guardado is not None
            and precio is not None
            and not self._prioridad(lado, precio, guardado, clase)
            and self._cambio_chico(lado, viaje)
        ):
            if self._toco_activador(lado, precio, guardado, clase):
                self._quieto[lado] = True
            return guardado
        paso = paso_del_tonto(self.color, lado)
        px = precio_para_ganar(
            lado, viaje.quiebre(), viaje.cantidad, dolares, paso
        )
        if px is None:
            self._precio[lado] = None
            self._bolsa[lado] = None
            return None
        self._precio[lado] = px
        self._bolsa[lado] = (float(viaje.cantidad), float(viaje.caja))
        if self._toco_activador(lado, precio, px, clase):
            self._quieto[lado] = True
        return px

    def _prioridad(
        self,
        lado: str,
        precio: float,
        suelo: float,
        clase: str | None,
    ) -> bool:
        """Cerca, o limpia ya arrimándose, la bolsa se lee ahora."""
        if suelo == 0:
            return True
        paso = paso_del_tonto(self.color, lado)
        dist = abs(float(precio) - suelo) / abs(suelo)
        if dist <= _CERCA * paso:
            return True
        nombre = str(clase or "").strip().lower().replace("í", "i")
        return nombre == "limpia" and dist <= _ARRIME_LIMPIA * paso

    def _cambio_chico(self, lado: str, viaje: Viaje) -> bool:
        """Lejos, menos de una décima de la bolsa puede esperar."""
        prev = self._bolsa[lado]
        if prev is None:
            return False
        c0, k0 = prev
        if c0 <= _EPS:
            return False
        monedas = abs(viaje.cantidad - c0) / c0
        caja = abs(viaje.caja - k0) / max(abs(k0), _EPS)
        return monedas < _CAMBIO_CHICO and caja < _CAMBIO_CHICO

    def quieto(self, lado: str) -> bool:
        lado_u = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        return bool(self._quieto[lado_u])

    def _toco_activador(
        self,
        lado: str,
        precio: float | None,
        meta: float,
        clase: str | None,
    ) -> bool:
        gap = distancia_activador(clase) if clase else None
        if gap is None or precio is None or meta <= 0:
            return False
        px = float(precio)
        if px <= 0:
            return False
        if lado == "LONG":
            return (px - meta) / meta + _EPS >= gap
        return (meta - px) / meta + _EPS >= gap

    def precio(self, lado: str) -> float | None:
        lado_u = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
        return self._precio[lado_u]

    def a_cerrar(self, viaje: Viaje) -> float:
        """Monedas que todavía están. Cero si el viaje murió."""
        if not viaje.vivo():
            return 0.0
        return float(viaje.cantidad)

    def a_cerrar_dolares(self, viaje: Viaje, precio: float) -> float:
        """Lo que vale ahora lo que queda. No es el monto anotado al marcar."""
        px = float(precio or 0)
        if px <= 0:
            return 0.0
        return self.a_cerrar(viaje) * px
