"""Paso 3 en seco. Si el malo se cierra entero, o el empate corona al rey, es tumor."""
from cirugias.escudo_dual.capas import Libro


def _exige_metal(salio: str | None, esperado: str, nombre: str) -> None:
    if salio != esperado:
        raise SystemExit(f"TUMOR {nombre}: entro {salio}, debia {esperado}")
    print(f"OK  {nombre} = {salio}")


def _no_entro(salio: str | None, nombre: str) -> None:
    if salio is not None:
        raise SystemExit(f"TUMOR {nombre}: entro {salio}")
    print(f"OK  {nombre} no entra")


def la_mas_chica_si_los_dos_pueden() -> None:
    """Rey en 2, reina en 0,5. Los dos con permiso. Entra la reina, no el que más salta."""
    libro = Libro()
    metal = libro.engordar(
        10,
        permiso_rey=True,
        permiso_reina=True,
        relacion_rey=2.0,
        relacion_reina=0.5,
    )
    _exige_metal(metal, "reina", "los dos pueden")
    if abs(libro.total("rey")) > 1e-9:
        raise SystemExit("TUMOR el rey recibio capa sin ser el mas chico")
    print("OK  el rey no recibio esa capa")


def solo_uno_aunque_pida_mas() -> None:
    """La reina pide más (relación 2) pero es la única con permiso."""
    libro = Libro()
    metal = libro.engordar(
        10,
        permiso_rey=False,
        permiso_reina=True,
        relacion_rey=0.5,
        relacion_reina=2.0,
    )
    _exige_metal(metal, "reina", "solo la reina")
    if abs(libro.total() - 10) > 1e-9:
        raise SystemExit("TUMOR no entro la capa entera")


def ninguno_no_entra_y_no_vacia() -> None:
    libro = Libro()
    libro.engordar(40, permiso_rey=True, permiso_reina=False, relacion_rey=1.5, relacion_reina=0.4)
    antes = libro.total()
    nada = libro.engordar(
        10,
        permiso_rey=False,
        permiso_reina=False,
        relacion_rey=1.5,
        relacion_reina=0.4,
    )
    _no_entro(nada, "los dos sin permiso")
    if abs(libro.total() - antes) > 1e-9:
        raise SystemExit("TUMOR el no-permiso movio las capas viejas")
    print("OK  las viejas se quedaron")


def el_que_no_se_sabe_no_es_un_si() -> None:
    libro = Libro()
    nada = libro.engordar(
        10,
        permiso_rey=None,
        permiso_reina=None,
        relacion_rey=1.0,
        relacion_reina=0.4,
    )
    _no_entro(nada, "permiso sin numero")
    sin_relacion = libro.engordar(
        10,
        permiso_rey=True,
        permiso_reina=False,
        relacion_rey=None,
        relacion_reina=0.4,
    )
    _no_entro(sin_relacion, "permiso sin relacion")


def el_empate_no_corona_al_rey() -> None:
    libro = Libro()
    nada = libro.engordar(
        10,
        permiso_rey=True,
        permiso_reina=True,
        relacion_rey=1.0,
        relacion_reina=1.0,
    )
    _no_entro(nada, "empate")
    if libro.total() > 1e-9:
        raise SystemExit("TUMOR el empate le dio la capa al rey")
    print("OK  el empate no le dio la capa a nadie")


def al_desinflar_sale_el_malo_primero() -> None:
    """Capa vieja del rey, capa nueva de la reina. El rey dejo de acompañar.

    Piden soltar 10. Salen del rey, no de la última capa.
    """
    libro = Libro()
    libro.engordar(40, permiso_rey=True, permiso_reina=False, relacion_rey=2.0, relacion_reina=None)
    libro.engordar(30, permiso_rey=False, permiso_reina=True, relacion_rey=None, relacion_reina=0.5)
    salio = libro.desinflar(10, permiso_rey=False, permiso_reina=True)
    if abs(salio - 10) > 1e-9:
        raise SystemExit(f"TUMOR salio {salio}")
    if abs(libro.total("rey") - 30) > 1e-9:
        raise SystemExit(f"TUMOR el rey quedo en {libro.total('rey')}")
    if abs(libro.total("reina") - 30) > 1e-9:
        raise SystemExit(f"TUMOR la reina quedo en {libro.total('reina')}")
    print("OK  salio el malo, la capa nueva se quedo")


def los_dos_malos_no_cierran_el_escudo() -> None:
    libro = Libro()
    libro.engordar(40, permiso_rey=True, permiso_reina=False, relacion_rey=2.0, relacion_reina=None)
    libro.engordar(30, permiso_rey=False, permiso_reina=True, relacion_rey=None, relacion_reina=0.5)
    salio = libro.desinflar(10, permiso_rey=False, permiso_reina=False)
    if abs(salio - 10) > 1e-9:
        raise SystemExit(f"TUMOR salio {salio}, debian ser 10")
    if abs(libro.total() - 60) > 1e-9:
        raise SystemExit(f"TUMOR el escudo quedo en {libro.total()}, debia 60")
    if abs(libro.total("reina") - 20) > 1e-9:
        raise SystemExit("TUMOR no salio la ultima capa")
    if abs(libro.total("rey") - 40) > 1e-9:
        raise SystemExit("TUMOR castigo al rey aunque los dos iban mal")
    print("OK  los dos malos sueltan solo lo pedido, la ultima capa primero")


def los_dos_bien_tampoco_eligen_castigo() -> None:
    libro = Libro()
    libro.engordar(40, permiso_rey=True, permiso_reina=False, relacion_rey=2.0, relacion_reina=None)
    libro.engordar(30, permiso_rey=False, permiso_reina=True, relacion_rey=None, relacion_reina=0.5)
    libro.desinflar(10, permiso_rey=True, permiso_reina=True)
    if abs(libro.total("reina") - 20) > 1e-9 or abs(libro.total("rey") - 40) > 1e-9:
        raise SystemExit("TUMOR con los dos bien no respeto la ultima capa")
    print("OK  con los dos bien sale la ultima capa")


def no_suelta_de_mas() -> None:
    libro = Libro()
    libro.engordar(40, permiso_rey=True, permiso_reina=False, relacion_rey=2.0, relacion_reina=None)
    salio = libro.desinflar(100, permiso_rey=False, permiso_reina=True)
    if abs(salio - 40) > 1e-9 or libro.total() > 1e-9:
        raise SystemExit(f"TUMOR solto {salio} y dejo {libro.total()}")
    otra = libro.desinflar(10, permiso_rey=False, permiso_reina=True)
    if abs(otra) > 1e-9:
        raise SystemExit("TUMOR un libro vacio siguio soltando")
    print("OK  no suelta mas de lo que hay")


def main() -> None:
    la_mas_chica_si_los_dos_pueden()
    solo_uno_aunque_pida_mas()
    ninguno_no_entra_y_no_vacia()
    el_que_no_se_sabe_no_es_un_si()
    el_empate_no_corona_al_rey()
    al_desinflar_sale_el_malo_primero()
    los_dos_malos_no_cierran_el_escudo()
    los_dos_bien_tampoco_eligen_castigo()
    no_suelta_de_mas()
    print("PASO_3_REVISADO")


if __name__ == "__main__":
    main()
