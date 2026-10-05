"""Paso 4 en seco. Si el lineal entra como capa, o el giro le cambia el nombre, es tumor."""
from cirugias.escudo_dual.escudo import Escudo


def _poner(escudo: Escudo, monto: float, metal: str) -> None:
    if metal == "rey":
        entro = escudo.engordar(
            monto,
            permiso_rey=True,
            permiso_reina=False,
            relacion_rey=2.0,
            relacion_reina=None,
        )
    else:
        entro = escudo.engordar(
            monto,
            permiso_rey=False,
            permiso_reina=True,
            relacion_rey=None,
            relacion_reina=0.5,
        )
    if entro != metal:
        raise SystemExit(f"TUMOR no entro {metal}, entro {entro}")


def la_bolsa_dicta_el_lado() -> None:
    """Más largo que corto: el escudo va corto. 1000 y 400 dan neto 600."""
    escudo = Escudo()
    lado = escudo.ver_bolsa(1000, 400)
    if lado != "SHORT":
        raise SystemExit(f"TUMOR lado {lado}, debia SHORT")
    print("OK  bolsa mas larga, escudo corto")

    otro = Escudo()
    if otro.ver_bolsa(200, 800) != "LONG":
        raise SystemExit("TUMOR mas corto en la bolsa no puso el escudo largo")
    print("OK  bolsa mas corta, escudo largo")


def un_negativo_no_voltea_el_lado() -> None:
    """Un largo escrito al revés no es un corto. Se toma como cero."""
    escudo = Escudo()
    if escudo.ver_bolsa(-500, 0) is not None:
        raise SystemExit("TUMOR un largo negativo invento lado")
    print("OK  un numero al reves no inventa bolsa")


def el_polvo_no_es_un_lado() -> None:
    escudo = Escudo()
    if escudo.ver_bolsa(300, 100, polvo=250) is not None:
        raise SystemExit("TUMOR dentro del polvo habia lado")
    if escudo.ver_bolsa(300, 100, polvo=0) != "SHORT":
        raise SystemExit("TUMOR sin polvo el mismo neto se quedo mudo")
    print("OK  el polvo lo pone quien llama, aqui no hay un numero escondido")


def el_lineal_no_es_capa() -> None:
    """Ver la bolsa, por grande que sea, no escribe capas."""
    escudo = Escudo()
    escudo.ver_bolsa(5000, 0)
    if escudo.cubierta() > 1e-9:
        raise SystemExit("TUMOR el lineal se anoto como capa")
    _poner(escudo, 40, "rey")
    _poner(escudo, 15, "reina")
    if abs(escudo.cubierta() - 55) > 1e-9:
        raise SystemExit(f"TUMOR la cubierta es {escudo.cubierta()}, debian ser 55")
    if escudo.lado != "SHORT":
        raise SystemExit("TUMOR las dos capas no comparten el lado")
    print("OK  dos metales, un lado, y el lineal no es capa")


def no_son_dos_escudos_sumados() -> None:
    """La cubierta no es la bolsa por la relacion del rey mas la de la reina."""
    escudo = Escudo()
    escudo.ver_bolsa(1000, 0)
    _poner(escudo, 40, "rey")
    doble = 1000 * 2.0 + 1000 * 0.5
    if abs(escudo.cubierta() - doble) < 1e-6:
        raise SystemExit("TUMOR sumo las dos relaciones como dos escudos")
    print("OK  no se suman las dos relaciones")


def el_giro_no_le_cambia_el_nombre() -> None:
    escudo = Escudo()
    escudo.ver_bolsa(1000, 0)
    _poner(escudo, 40, "rey")
    escudo.ver_bolsa(0, 1000)
    if escudo.lado != "LONG":
        raise SystemExit("TUMOR no giro con la bolsa")
    if abs(escudo.cubierta()) > 1e-9:
        raise SystemExit("TUMOR lo corto de antes cuenta como largo")
    if abs(escudo.guardado("SHORT") - 40) > 1e-9:
        raise SystemExit("TUMOR el giro borro o renombro las capas cortas")
    _poner(escudo, 10, "reina")
    if abs(escudo.guardado("SHORT") - 40) > 1e-9:
        raise SystemExit("TUMOR la capa nueva cayo en el lado viejo")
    if abs(escudo.cubierta() - 10) > 1e-9:
        raise SystemExit("TUMOR la cubierta de ahora no es solo lo largo")
    print("OK  el giro no renombra y no mezcla los lados")

    escudo.ver_bolsa(1000, 0)
    if abs(escudo.cubierta() - 40) > 1e-9:
        raise SystemExit("TUMOR al volver no encontro las capas cortas")
    if abs(escudo.guardado("LONG") - 10) > 1e-9:
        raise SystemExit("TUMOR al volver se perdio lo largo")
    print("OK  al volver cada lado sigue con lo suyo")


def sin_lado_no_engorda() -> None:
    escudo = Escudo()
    entro = escudo.engordar(
        10,
        permiso_rey=True,
        permiso_reina=False,
        relacion_rey=1.0,
        relacion_reina=None,
    )
    if entro is not None or escudo.cubierta() > 1e-9:
        raise SystemExit("TUMOR engordo sin bolsa")
    escudo.ver_bolsa(1000, 0)
    _poner(escudo, 40, "rey")
    escudo.ver_bolsa(100, 100, polvo=0)
    if abs(escudo.guardado("SHORT") - 40) > 1e-9:
        raise SystemExit("TUMOR el polvo borro las capas al mirar la bolsa")
    salio = escudo.desinflar(10, permiso_rey=False, permiso_reina=True)
    if abs(salio - 10) > 1e-9 or abs(escudo.guardado("SHORT") - 30) > 1e-9:
        raise SystemExit("TUMOR la bolsa neutra no pudo soltar el unico lado con capas")
    print("OK  sin lado no engorda; soltar solo toca el unico lado que tenia capas")

    escudo.ver_bolsa(0, 1000)
    _poner(escudo, 10, "reina")
    escudo.ver_bolsa(100, 100)
    if escudo.desinflar(5, permiso_rey=True, permiso_reina=True) != 0:
        raise SystemExit("TUMOR sin lado solto de los dos lados a la vez")
    if abs(escudo.guardado("SHORT") - 30) > 1e-9 or abs(escudo.guardado("LONG") - 10) > 1e-9:
        raise SystemExit("TUMOR el polvo eligio un lado y lo vacio")
    print("OK  si los dos lados tienen capas, sin lado no elige a quien vaciar")


def main() -> None:
    la_bolsa_dicta_el_lado()
    un_negativo_no_voltea_el_lado()
    el_polvo_no_es_un_lado()
    el_lineal_no_es_capa()
    no_son_dos_escudos_sumados()
    el_giro_no_le_cambia_el_nombre()
    sin_lado_no_engorda()
    print("PASO_4_REVISADO")


if __name__ == "__main__":
    main()
