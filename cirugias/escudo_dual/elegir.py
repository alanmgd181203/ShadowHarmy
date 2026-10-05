"""Quién recibiría la próxima capa. No planta.

La relación lenta ya medida: el rey pide 1,7 y la reina 1,6.
El permiso se mira en el tramo reciente. Si no se sabe, no es un sí.

Si esa medida cambia, el metal no se engorda ni se desinfla en el
mismo latido. Entra la próxima vez que se toca un escalón.
"""
from __future__ import annotations

import json
from pathlib import Path

from cirugias.escudo_dual.capas import _quien_recibe
from cirugias.escudo_dual.ojo import ver

RELACION_LENTA = {"rey": 1.7, "reina": 1.6}
# La casa (monedas + cabeza). El escudo calla en el ruido.
ABRE = 5000.0
CIERRA = 2500.0
CALMA = 8000.0
ALERTA = 12000.0
# Al bajar, el vestido no suelta en la misma raya donde se puso.
BAJA_LLENA = 10000.0
BAJA_MEDIA = 7000.0
_SELLO = Path(__file__).resolve().parents[2] / "data" / "beru" / "escudo" / "relacion_sello.json"


def _medida() -> dict[str, float]:
    return {"rey": float(RELACION_LENTA["rey"]), "reina": float(RELACION_LENTA["reina"])}


def _leer_sello(path: Path | None = None) -> dict | None:
    ruta = path or _SELLO
    try:
        dato = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    if not isinstance(dato, dict):
        return None
    try:
        return {
            "rey": float(dato["rey"]),
            "reina": float(dato["reina"]),
            "asiento": float(dato["asiento"]),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _guardar_sello(
    relacion: dict[str, float],
    asiento: float,
    path: Path | None = None,
) -> None:
    ruta = path or _SELLO
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps(
                {"rey": relacion["rey"], "reina": relacion["reina"], "asiento": float(asiento)}
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


def _parte(asiento: float) -> float:
    """Subida: mitad hasta 8 mil, tres cuartos hasta 12 mil, luego el indicador."""
    a = abs(float(asiento or 0))
    if a <= CALMA:
        return 0.5
    if a <= ALERTA:
        return 0.75
    return 1.0


def _parte_del_sello(previo: dict | None) -> float | None:
    if not previo:
        return None
    llena = _medida()["reina"]
    if llena <= 0:
        return None
    ratio = float(previo["reina"]) / llena
    if abs(ratio - 1.0) < 0.08:
        return 1.0
    if abs(ratio - 0.75) < 0.08:
        return 0.75
    if abs(ratio - 0.5) < 0.08:
        return 0.5
    return None


def _parte_baja(asiento: float, previa: float | None) -> float:
    """La bajada suelta el vestido más abajo de donde lo tomó.

    El lleno aguanta hasta caer de 10 mil. Los tres cuartos, hasta 7 mil.
    Ahí el cambio es de un golpe. Si no hay memoria, manda la subida.
    """
    a = abs(float(asiento or 0))
    if a <= 0 or previa is None:
        return 0.5 if a <= 0 else _parte(a)
    if previa > 0.9:
        if a >= BAJA_LLENA:
            return 1.0
        previa = 0.75
    if previa > 0.6:
        if a > ALERTA:
            return 1.0
        if a <= BAJA_MEDIA:
            return 0.5
        return 0.75
    if a > ALERTA:
        return 1.0
    if a > CALMA:
        return 0.75
    return 0.5


def _por_modo(asiento: float, previa: float | None = None) -> dict[str, float]:
    parte = _parte_baja(asiento, previa)
    medida = _medida()
    return {"rey": medida["rey"] * parte, "reina": medida["reina"] * parte}


def asiento_en_banda(
    neto: float,
    *,
    armado: bool,
    lado: str,
    valor: float | None,
) -> tuple[float, bool, str]:
    """Apagado hasta 5000. Prendido, baja de peldaño. En 2500, se apaga de un tajo."""
    from core.igris_escudo_btc import neto_peldaño_atrasado

    n = float(neto or 0)
    if not armado:
        if abs(n) < ABRE:
            return 0.0, False, ""
        return neto_peldaño_atrasado(n, armado=False, lado_armado="", asentado=None)
    asiento, sigo, lado_nuevo = neto_peldaño_atrasado(
        n,
        armado=True,
        lado_armado=lado,
        asentado=valor,
    )
    if (not sigo) or abs(n) <= CIERRA:
        return 0.0, False, ""
    return float(asiento), True, lado_nuevo


def relacion_vigente(asiento: float, sello: Path | None = None) -> dict[str, float]:
    """La medida del modo entra al tocar un escalón.

    El sello viejo, con el indicador entero en una silla chica,
    se corrige en el primer latido de la cirugía.
    Otro manto trae su propio sello. Si no, se usa el de las monedas.
    """
    previo = _leer_sello(sello)
    medida = _por_modo(asiento, _parte_del_sello(previo))
    llena = _medida()
    sello_viejo = previo is not None and (
        abs(float(previo["reina"]) - llena["reina"]) < 0.02
        and abs(float(previo["rey"]) - llena["rey"]) < 0.02
        and abs(medida["reina"] - llena["reina"]) > 0.02
    )
    if previo is None or abs(float(asiento) - float(previo["asiento"])) > 1.0 or sello_viejo:
        _guardar_sello(medida, asiento, sello)
        return medida
    return {"rey": float(previo["rey"]), "reina": float(previo["reina"])}


def metal_de_la_siguiente() -> str | None:
    """rey, reina, o None si no entra nadie."""
    dato = ver()
    return _quien_recibe(
        dato.get("permiso_rey"),
        dato.get("permiso_reina"),
        RELACION_LENTA["rey"],
        RELACION_LENTA["reina"],
    )


def frase_eleccion(metal: str | None) -> str:
    if metal == "reina":
        return "siguiente capa: reina, si el cruce llena el peldaño"
    if metal == "rey":
        return "siguiente capa: rey, si el cruce llena el peldaño"
    return "siguiente capa: nadie, no entra"
