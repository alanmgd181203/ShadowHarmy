"""La casa de la bolsa no se mezcla, y el contrato lineal se cuenta en dólares."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cirugias.escudo_dual.bolsa import es_cazador, sala
from cirugias.escudo_dual.manos_bolsa import contratos, dolares


def _exige(ok: bool, frase: str) -> None:
    if not ok:
        raise SystemExit(frase)


def la_plata_y_corea_se_quedan() -> None:
    _exige(not es_cazador("XAG"), "la plata entro a la bolsa")
    _exige(not es_cazador("KORU"), "corea de tres entro a la bolsa")
    _exige(not es_cazador("US100"), "la reina no caza")
    _exige(not es_cazador("US500"), "el rey no caza")
    _exige(es_cazador("SOXL"), "el semiconductor no esta")
    _exige(es_cazador("SPCX"), "spacex no esta")
    _exige(es_cazador("SNXX"), "sandisk no esta")
    _exige(sala("SOXL") == "rojo", "el semiconductor no cupo en rojo")


def el_lineal_vale_el_precio() -> None:
    """Diez milésimas a treinta mil son trescientos dólares, no diez centavos."""
    _exige(abs(dolares(0.01, 1.0, 30000.0) - 300.0) < 1e-6, "el vivo no es el precio")
    qty = contratos(100.0, 30000.0, 1.0, 0.0001, 0.0001)
    _exige(abs(qty - 0.0033) < 1e-9, f"los contratos salieron {qty}")
    _exige(contratos(1.0, 30000.0, 1.0, 0.0001, 0.0001) == 0.0, "un dolar abrio un contrato")


if __name__ == "__main__":
    la_plata_y_corea_se_quedan()
    el_lineal_vale_el_precio()
    print("OK  bolsa")
