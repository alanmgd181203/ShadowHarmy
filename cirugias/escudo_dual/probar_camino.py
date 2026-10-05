"""Paso 5 en seco. El camino entero. Si la relación chica manda sin permiso, es tumor.

El permiso ya tiene sus pesos: mitad en 3 minutos, 30 % de 3 a 5,
20 % de 5 a 15. Cada precio de estos caminos es un minuto.
"""
from cirugias.escudo_dual.escudo import Escudo
from cirugias.escudo_dual.permiso import conceder, mirar
from cirugias.escudo_dual.relaciones import las_dos, relacion


def _camino(saltos: list[float]) -> list[float]:
    precio = 100.0
    out = [precio]
    for salto in saltos:
        precio = precio * (1.0 + salto)
        out.append(precio)
    return out


def _permiso(marea: list[float], metal: list[float]) -> bool | None:
    return conceder(mirar(marea, metal))


def _tres(saltos: list[float]) -> list[float]:
    """Tres minutos. Hace falta para que el permiso pueda hablar."""
    return _camino(saltos)


def _quince(a15: float, a5: float, a3: float, a0: float) -> list[float]:
    """Hace 15, hace 5, hace 3, y ahora. Lo de en medio no cambia el corte."""
    precios = [a15] * 16
    precios[10] = a5
    precios[12] = a3
    precios[15] = a0
    return precios


def la_chica_sin_la_marea_no_entra() -> None:
    """La reina se sacude el doble, así que pide la mitad.

    En el tramo de ahora va al revés, y más fuerte que el rey.
    El rey sí va con la marea. La capa es del rey.
    """
    marea_lenta = _camino([0.1, -0.1, 0.1, -0.1])
    par = las_dos(
        marea_lenta,
        _camino([0.05, -0.05, 0.05, -0.05]),
        _camino([0.2, -0.2, 0.2, -0.2]),
    )
    if par["rey"] is None or abs(par["rey"] - 2.0) > 1e-6:
        raise SystemExit(f"TUMOR relacion del rey {par['rey']}")
    if par["reina"] is None or abs(par["reina"] - 0.5) > 1e-6:
        raise SystemExit(f"TUMOR relacion de la reina {par['reina']}")

    ahora = _tres([0.01, 0.01, 0.01])
    rey_si = _permiso(ahora, _tres([0.01, 0.01, 0.01]))
    reina_no = _permiso(ahora, _tres([-0.01, -0.01, -0.01]))
    if rey_si is not True or reina_no is not False:
        raise SystemExit(f"TUMOR permisos rey {rey_si} reina {reina_no}")

    escudo = Escudo()
    if escudo.ver_bolsa(1000, 0) != "SHORT":
        raise SystemExit("TUMOR la bolsa larga no puso el escudo en corto")
    if escudo.cubierta() > 1e-9:
        raise SystemExit("TUMOR ver la bolsa escribio capa")
    metal = escudo.engordar(
        10,
        permiso_rey=rey_si,
        permiso_reina=reina_no,
        relacion_rey=par["rey"],
        relacion_reina=par["reina"],
    )
    if metal != "rey":
        raise SystemExit(f"TUMOR la capa fue a {metal}")
    if abs(escudo.cubierta() - 10) > 1e-9:
        raise SystemExit("TUMOR la cubierta no es el engorde")
    if abs(escudo.cubierta() - (1000 * 0.5)) < 1e-6:
        raise SystemExit("TUMOR la cubierta salio de la relacion, no del engorde")
    print("OK  la relacion chica, yendo en contra, no se llevo la capa")


def una_vela_no_abre_capa() -> None:
    marea = _camino([0.3])
    metal = _camino([0.8])
    if relacion(marea, metal) is not None:
        raise SystemExit("TUMOR una vela ya tenia relacion")
    if _permiso(marea, metal) is not None:
        raise SystemExit("TUMOR una vela ya tenia permiso")
    escudo = Escudo()
    escudo.ver_bolsa(1000, 0)
    entro = escudo.engordar(
        10,
        permiso_rey=True,
        permiso_reina=None,
        relacion_rey=None,
        relacion_reina=None,
    )
    if entro is not None or escudo.cubierta() > 1e-9:
        raise SystemExit("TUMOR una vela abrio capa")
    print("OK  una vela no abre capa")


def el_ahora_puede_ganar_y_los_dos_se_resuelven_por_lo_chico() -> None:
    """De 5 a 15 la reina iba en contra. Los últimos 5 van con la marea.

    El no de ella pesa 0,20 y no le gana al ahora. El rey va en
    contra en los últimos 5, así que pesa 0,80 y no tiene permiso.
    Luego los dos acompañan y entra la relación más chica.
    """
    marea = _quince(100, 101, 102, 103)
    reina = _permiso(marea, _quince(100, 99, 99 * 1.01, 99 * 1.01 * 1.01))
    rey = _permiso(marea, _quince(100, 101, 101 * 0.994, 101 * 0.994 * 0.994))
    if reina is not True:
        raise SystemExit("TUMOR el ahora no le gano a la manana")
    if rey is not False:
        raise SystemExit("TUMOR el rey en contra recibio permiso")

    escudo = Escudo()
    escudo.ver_bolsa(0, 800)
    primero = escudo.engordar(
        40,
        permiso_rey=rey,
        permiso_reina=reina,
        relacion_rey=2.0,
        relacion_reina=0.5,
    )
    if primero != "reina" or abs(escudo.cubierta() - 40) > 1e-9:
        raise SystemExit(f"TUMOR primero {primero} cubierta {escudo.cubierta()}")

    ambos = _tres([0.01, 0.01, 0.01])
    rey_si = _permiso(ambos, _tres([0.03, 0.03, 0.03]))
    reina_si = _permiso(ambos, _tres([0.002, 0.002, 0.002]))
    if rey_si is not True or reina_si is not True:
        raise SystemExit("TUMOR los dos debian acompanar")
    segundo = escudo.engordar(
        25,
        permiso_rey=rey_si,
        permiso_reina=reina_si,
        relacion_rey=2.0,
        relacion_reina=0.5,
    )
    if segundo != "reina":
        raise SystemExit(f"TUMOR gano el que mas se movio: {segundo}")
    if abs(escudo.guardado("LONG") - 65) > 1e-9:
        raise SystemExit("TUMOR el segundo engorde no se sumo en el mismo lado")
    print("OK  el ahora puede abrir, y si los dos van, gana la relacion chica")
    return escudo


def al_soltar_no_se_vacia_por_estar_mal(escudo: Escudo) -> None:
    salio = escudo.desinflar(10, permiso_rey=False, permiso_reina=True)
    if abs(salio - 10) > 1e-9:
        raise SystemExit(f"TUMOR salio {salio}")
    if abs(escudo.cubierta() - 55) > 1e-9:
        raise SystemExit("TUMOR no quedaron 55")
    # Las dos capas son de la reina. El rey no tiene. Soltar 10 sale de ella
    # porque es la única. Luego los dos malos: solo lo pedido, no el cierre.
    salio_mal = escudo.desinflar(10, permiso_rey=False, permiso_reina=False)
    if abs(salio_mal - 10) > 1e-9 or abs(escudo.cubierta() - 45) > 1e-9:
        raise SystemExit(f"TUMOR los dos malos dejaron {escudo.cubierta()}")
    print("OK  estar mal no vacia el escudo")


def el_giro_no_se_trae_la_cubierta() -> None:
    escudo = Escudo()
    escudo.ver_bolsa(1000, 0)
    escudo.engordar(
        40,
        permiso_rey=True,
        permiso_reina=False,
        relacion_rey=2.0,
        relacion_reina=0.5,
    )
    escudo.ver_bolsa(0, 1000)
    if abs(escudo.cubierta()) > 1e-9:
        raise SystemExit("TUMOR el corto de antes cuenta en el largo")
    if abs(escudo.guardado("SHORT") - 40) > 1e-9:
        raise SystemExit("TUMOR el giro borro el lado viejo")
    print("OK  el giro no arrastra la cubierta")


def main() -> None:
    la_chica_sin_la_marea_no_entra()
    una_vela_no_abre_capa()
    escudo = el_ahora_puede_ganar_y_los_dos_se_resuelven_por_lo_chico()
    al_soltar_no_se_vacia_por_estar_mal(escudo)
    el_giro_no_se_trae_la_cubierta()
    print("PASO_5_REVISADO")


if __name__ == "__main__":
    main()
