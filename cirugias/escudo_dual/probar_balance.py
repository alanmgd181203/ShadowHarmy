"""El sobrante no se corta. Al engordar solo entra el restante."""
from cirugias.escudo_dual.balance import cuanto_entra, faltante, redondear


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(float(a) - b) > 1e-9:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def la_decima_no_resta() -> None:
    """1,63 se queda en 1,6. No en 1,4. Un metal que pide menos no sube a 1."""
    _cerca(redondear(1.63), 1.6, "la decima")
    if redondear(1.63) == 1.4:
        raise SystemExit("TUMOR se le restaron dos decimas")
    _cerca(redondear(0.74), 0.7, "el que pide menos")
    if redondear(0.74) == 1.0:
        raise SystemExit("TUMOR el chico se subio a uno")
    if redondear(None) is not None:
        raise SystemExit("TUMOR sin relacion invento un numero")
    print("OK  sin relacion no habla")


def el_faltante_entra_y_el_sobrante_no_se_corta() -> None:
    """Cubierta 150, meta nueva 140. Sobran 10. No se inventa un corte."""
    _cerca(faltante(150, 140), 0.0, "no se corta el sobrante")
    _cerca(faltante(140, 150), 10.0, "el faltante")


def al_engordar_solo_el_restante() -> None:
    """Sobran 10. El pedido es 25. Entran 15, no 25 y no 0."""
    entro = cuanto_entra(25, 150, 140)
    _cerca(entro, 15.0, "el restante")
    _cerca(cuanto_entra(10, 150, 140), 0.0, "el sobrante alcanza")
    _cerca(cuanto_entra(25, 140, 140), 25.0, "sin sobra entra el pedido")


def main() -> None:
    la_decima_no_resta()
    el_faltante_entra_y_el_sobrante_no_se_corta()
    al_engordar_solo_el_restante()
    print("BALANCE_REVISADO")


if __name__ == "__main__":
    main()
