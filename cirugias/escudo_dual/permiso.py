"""El permiso. Paso 2. El escudo vivo no lee esto.

No mide cuánto se sacude el metal. Eso ya es la relación.
Aquí solo si fue en el mismo sentido que la marea, en el tramo
reciente. Una hora atrás no vota.

El tramo se parte sin contar dos veces el mismo minuto:

- últimos 3 minutos: la mitad
- de 3 a 5: un 30 %
- de 5 a 15: un 20 %

En cada parte, el metal está junto o no. Si va al mismo lado,
aunque sea poquito, esa parte dice sí. Si no se mueve, es ruido.
Si va al revés por menos de un 0,5 %, también es un temblor:
no alcanza para llamarlo traidor. Si va al revés por un 0,5 %
o más, esa parte dice no, y el no pesa solo lo de ella.

Los sí tienen que ganarle a los no. Si empatan, ese metal no
se lleva la capa nueva, y tampoco queda marcado como traidor.
Una vela sola no alcanza: hace falta el tramo de 3 minutos.
"""
from __future__ import annotations

from typing import Sequence

_EPS = 1e-12
_CONTRA = 0.005
# (minutos más cerca, minutos más lejos, peso). Sin solaparse.
_PARTES = (
    (0, 3, 0.50),
    (3, 5, 0.30),
    (5, 15, 0.20),
)


def mirar(marea: Sequence[float], metal: Sequence[float]) -> dict[str, float | int | bool]:
    """Pesa las tres partes. No concede."""
    vacio = _vacio()
    if not marea or not metal:
        return vacio

    niveles_m, niveles_x = _mismo_tramo(marea, metal)
    if len(niveles_m) < 2:
        return vacio

    junto = 0.0
    contra = 0.0
    for cerca, lejos, peso in _PARTES:
        voto = _voto(niveles_m, niveles_x, cerca, lejos)
        if voto == "junto":
            junto += peso
        elif voto == "contra":
            contra += peso

    return {
        "junto": junto,
        "contra": contra,
        "habla": junto > _EPS or contra > _EPS,
        "valido": True,
    }


def conceder(mirada: dict) -> bool | None:
    """Sí si lo junto pesa más. No si lo contrario pesa más. Empate: no habla."""
    if not mirada.get("valido", False):
        return None
    if not mirada.get("habla", False):
        return None
    junto = float(mirada["junto"])
    contra = float(mirada["contra"])
    if junto > contra + _EPS:
        return True
    if contra > junto + _EPS:
        return False
    return None


def _voto(
    marea: Sequence[float],
    metal: Sequence[float],
    cerca: int,
    lejos: int,
) -> str | None:
    salto_m = _salto(marea, cerca, lejos)
    salto_x = _salto(metal, cerca, lejos)
    if salto_m is None or salto_x is None:
        return None
    if abs(salto_m) <= _EPS or abs(salto_x) <= _EPS:
        return None
    mismo = (salto_m > 0 and salto_x > 0) or (salto_m < 0 and salto_x < 0)
    if mismo:
        return "junto"
    if abs(salto_x) + _EPS < _CONTRA:
        return None
    return "contra"


def _salto(niveles: Sequence[float], cerca: int, lejos: int) -> float | None:
    n = len(niveles)
    i_lejos = n - 1 - lejos
    i_cerca = n - 1 - cerca
    if i_lejos < 0 or i_cerca < 0 or i_lejos >= i_cerca:
        return None
    antes = float(niveles[i_lejos])
    ahora = float(niveles[i_cerca])
    if antes <= 0 or ahora <= 0:
        return None
    return (ahora / antes) - 1.0


def _vacio() -> dict[str, float | int | bool]:
    return {"junto": 0.0, "contra": 0.0, "habla": False, "valido": True}


def _mismo_tramo(
    a: Sequence[float], b: Sequence[float]
) -> tuple[list[float], list[float]]:
    n = min(len(a), len(b))
    if n <= 0:
        return [], []
    return list(a)[-n:], list(b)[-n:]
