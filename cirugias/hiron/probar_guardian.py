"""Paso 6 en seco. Si nace en la masacre, o cierra un número viejo, es tumor."""
from cirugias.hiron.guardian import Hiron


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(float(a) - b) > 1e-9:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def _no_es(a: float | None, mentira: float, nombre: str) -> None:
    if a is not None and abs(float(a) - mentira) < 1e-9:
        raise SystemExit(f"TUMOR {nombre}: cayo en {mentira}")
    print(f"OK  {nombre} no es {mentira}")


def _sigue_callado(h: Hiron, nombre: str) -> None:
    if h.nacido or h.oz is not None or h.tocada:
        raise SystemExit(f"TUMOR {nombre}: nacio o toco")
    if h.a_cerrar(4) is not None:
        raise SystemExit(f"TUMOR {nombre}: ya queria cerrar")
    print(f"OK  {nombre}")


def no_nace_en_la_masacre() -> None:
    h = Hiron("LONG", "limpia", 100)
    if h.ver(100):
        raise SystemExit("TUMOR cerro al tocar la masacre")
    _sigue_callado(h, "en 100 sigue dormido")
    if h.ver(100.9):
        raise SystemExit("TUMOR una red a 0,9 lo desperto")
    _sigue_callado(h, "a 0,9 de la masacre no nace")
    if h.meta != 100:
        raise SystemExit("TUMOR la masacre se corrio")


def la_limpia_nace_al_uno() -> None:
    h = Hiron("LONG", "limpia", 100)
    if h.ver(100.2):
        raise SystemExit("TUMOR uso el 0,2 de la caza")
    _sigue_callado(h, "el 0,2 de Beru no lo despierta")
    if h.ver(101):
        raise SystemExit("TUMOR la impresion en que nace ya cierra")
    if not h.nacido:
        raise SystemExit("TUMOR no nacio en 101")
    _cerca(h.oz, 99.99, "al nacer la oz queda un uno por ciento detras")
    _no_es(h.oz, 100.0, "oz")
    _no_es(h.oz, 101.0, "oz")
    _no_es(h.oz, 101 * 0.998, "oz de la caza")
    if h.a_cerrar(4) is not None:
        raise SystemExit("TUMOR cerro al nacer")
    print("OK  nacer no cierra")
    if not h.beru_sigue:
        raise SystemExit("TUMOR apago a Beru en la limpia")


def normal_y_dificil_nacen_antes() -> None:
    n = Hiron("LONG", "normal", 100)
    if n.ver(100.69):
        raise SystemExit("TUMOR normal cerro antes de nacer")
    _sigue_callado(n, "normal dormida en 100,69")
    if n.ver(100.7):
        raise SystemExit("TUMOR normal cerro al nacer")
    _cerca(n.oz, 100.7 * 0.993, "normal nace al 0,7")
    d = Hiron("LONG", "dificil", 100)
    _sigue_callado(d, "dificil dormida en el arranque")
    if d.ver(100.5):
        raise SystemExit("TUMOR dificil cerro al nacer")
    _cerca(d.oz, 100.5 * 0.995, "dificil nace al 0,5")
    _no_es(d.oz, 100.7 * 0.993, "dificil")
    if not d.beru_sigue:
        raise SystemExit("TUMOR en la dificil Hiron sustituyo a Beru")
    print("OK  Beru sigue en la dificil")


def persigue_y_no_se_devuelve() -> None:
    h = Hiron("LONG", "limpia", 100)
    h.ver(101)
    h.ver(110)
    _cerca(h.oz, 108.9, "en 110 la oz va a 108,9")
    _no_es(h.oz, 109.0, "oz")
    _no_es(h.oz, 110 * 0.998, "oz")
    if h.ver(109.5):
        raise SystemExit("TUMOR un retroceso corto ya cerro")
    _cerca(h.oz, 108.9, "el retroceso no arrastra la oz")
    if h.extremo != 110:
        raise SystemExit(f"TUMOR el extremo se devolvio a {h.extremo}")
    print("OK  el extremo se quedo en 110")
    if h.meta != 100:
        raise SystemExit("TUMOR la masacre persiguio el precio")
    print("OK  la masacre se quedo en 100")


def cierra_lo_que_queda() -> None:
    h = Hiron("LONG", "limpia", 100)
    h.ver(101)
    if h.a_cerrar(4) is not None:
        raise SystemExit("TUMOR guardo las 4 monedas al nacer")
    h.ver(110)
    h.ver(109.5)
    if h.a_cerrar(3) is not None:
        raise SystemExit("TUMOR cerro antes de tocar")
    if not h.ver(108.9):
        raise SystemExit("TUMOR no toco en 108,9")
    _cerca(h.a_cerrar(3), 3.0, "cierra las 3 que quedan")
    _no_es(h.a_cerrar(3), 4.0, "cierre")
    _cerca(h.a_cerrar(1), 1.0, "si otra mano solto, cierra la que queda")
    if h.ver(120):
        raise SystemExit("TUMOR despues de tocar siguio cazando")
    _cerca(h.oz, 108.9, "tocada, la oz ya no persigue")
    _cerca(h.a_cerrar(0), 0.0, "bolsa vacia no inventa monedas")


def el_salto_no_cierra_en_la_misma_impresion() -> None:
    h = Hiron("LONG", "limpia", 100)
    if h.ver(110):
        raise SystemExit("TUMOR el salto de 100 a 110 ya cerro")
    _cerca(h.extremo, 110.0, "el salto dejo el extremo en 110")
    _cerca(h.oz, 108.9, "y la oz un uno por ciento detras")
    if h.ver(100):
        pass
    else:
        raise SystemExit("TUMOR la vuelta a 100 no toco")
    _cerca(h.a_cerrar(2), 2.0, "al volver cierra lo de ahora")


def el_corto_nace_hacia_abajo() -> None:
    h = Hiron("SHORT", "limpia", 100)
    if h.ver(100) or h.ver(99.5):
        raise SystemExit("TUMOR el corto nacio o cerro antes del uno")
    _sigue_callado(h, "corto dormido antes del uno")
    if h.ver(99):
        raise SystemExit("TUMOR el corto cerro al nacer")
    _cerca(h.oz, 99.99, "la oz del corto queda por encima del extremo")
    if h.oz is None or h.oz <= 99:
        raise SystemExit("TUMOR la oz del corto quedo debajo")
    h.ver(90)
    _cerca(h.oz, 90.9, "en 90 la oz va a 90,9")
    _no_es(h.oz, 90 * 0.99, "corto")
    if h.ver(90.5):
        raise SystemExit("TUMOR un rebote chico ya cerro el corto")
    _cerca(h.oz, 90.9, "el rebote chico no mueve la oz")
    if not h.ver(90.9):
        raise SystemExit("TUMOR el corto no toco en 90,9")
    _cerca(h.a_cerrar(5), 5.0, "el corto cierra las 5 vivas")
    _no_es(h.a_cerrar(5), 8.0, "corto")


def no_se_come_la_grasa() -> None:
    """Al nacer se condenan cuarenta. Cincuenta al cobrar: salen cuarenta."""
    h = Hiron("LONG", "limpia", 100)
    if h.ver(101, 40):
        raise SystemExit("TUMOR nacer ya cerro")
    if h.condenadas != 40:
        raise SystemExit(f"TUMOR no condeno las cuarenta: {h.condenadas}")
    h.ver(110, 50)
    if h.condenadas != 40:
        raise SystemExit("TUMOR la grasa subio el techo")
    if not h.ver(108.9):
        raise SystemExit("TUMOR no toco para cobrar lo condenado")
    _cerca(h.a_cerrar(50), 40.0, "cierra las 40 condenadas y deja la grasa")
    _no_es(h.a_cerrar(50), 50.0, "cierre")
    _cerca(h.a_cerrar(3), 3.0, "si ya quedaba menos, no cobra el techo entero")
    _cerca(h.a_cerrar(0), 0.0, "bolsa vacia no inventa monedas")


def clase_desconocida_no_inventa() -> None:
    h = Hiron("LONG", "agresiva", 100)
    if h.ver(120):
        raise SystemExit("TUMOR una clase desconocida cerro")
    _sigue_callado(h, "sin clase no hay guardian")
    if h.gap is not None:
        raise SystemExit("TUMOR invento una distancia")
    print("OK  sin distancia inventada")


def main() -> None:
    no_nace_en_la_masacre()
    la_limpia_nace_al_uno()
    normal_y_dificil_nacen_antes()
    persigue_y_no_se_devuelve()
    cierra_lo_que_queda()
    el_salto_no_cierra_en_la_misma_impresion()
    el_corto_nace_hacia_abajo()
    no_se_come_la_grasa()
    clase_desconocida_no_inventa()
    print("PASO_6_REVISADO")


if __name__ == "__main__":
    main()
