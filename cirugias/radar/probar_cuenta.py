"""En seco. Si Igris adivina, pondera, o suma el hacha dos veces, es tumor."""
from cirugias.radar.cuenta import Mente, deber, firmada


def _cerca(a: float, b: float, nombre: str) -> None:
    if abs(float(a) - b) > 1e-6:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def la_suma_no_adivina() -> None:
    """Doce mil crudos. Uno ya espera dos mil. Otro calla. El tercero, quinientos."""
    uno = Mente()
    uno.declarar(2000)
    callado = Mente()
    tres = Mente()
    tres.declarar(500)
    mentes = [uno, callado, tres]
    _cerca(firmada(mentes), 2500, "la mente sumada")
    _cerca(deber(12000, mentes), 9500, "el deber sin el brinco")


def el_arrepentimiento_vuelve_a_cargar() -> None:
    """La mente baja de dos mil a quinientos. El deber sube. No se pondera."""
    uno = Mente()
    uno.declarar(2000)
    antes = deber(12000, [uno])
    uno.declarar(500)
    despues = deber(12000, [uno])
    _cerca(antes, 10000, "con dos mil firmados")
    _cerca(despues, 11500, "al arrepentirse")
    if despues <= antes:
        raise SystemExit("TUMOR el escudo no volvio a cargarse")
    print("OK  el deber subio")


def al_cobrarse_declara_cero() -> None:
    """La bolsa ya bajó a diez mil. Si la mente sigue en dos mil, miente."""
    uno = Mente()
    uno.declarar(2000)
    uno.declarar(0)
    _cerca(deber(10000, [uno]), 10000, "cobrado, la mente en cero")


def sin_activador_el_resto_no_cuenta() -> None:
    """Apuntar monedas antes de tiempo no sienta el hacha."""
    uno = Mente()
    uno.declarar(2000)
    uno.monedas_hacha = 90
    _cerca(uno.firmada(), 2000, "sin activador manda la Oz")


def el_activador_guarda_monedas() -> None:
    """Cuarenta monedas condenadas. La marca de hoy las valúa. La voz nueva no se oye."""
    uno = Mente()
    uno.declarar(2000)
    uno.sentar_hacha(40)
    uno.sentar_hacha(80)
    uno.declarar(3500)
    _cerca(uno.monedas_hacha, 40, "una segunda sentada no mueve el hacha")
    _cerca(uno.firmada(100), 4000, "a cien, cuarenta monedas valen cuatro mil")
    _cerca(deber(6000, [uno], 100), 2000, "lo engordado despues sigue cubierto")
    try:
        uno.firmada()
    except ValueError:
        print("OK  sin la marca de hoy el hacha no inventa dolares")
    else:
        raise SystemExit("TUMOR valuo el hacha sin marca")
    _cerca(uno.firmada(122), 4880, "la misma condena, con la marca de ahora")
    _cerca(deber(4880, [uno], 122), 0, "la bolsa condenada no vuelve a pedir")
    _cerca(deber(6100, [uno], 122), 1220, "la grasa de diez monedas queda cubierta")


def al_cobrar_se_calla() -> None:
    """Sale lo condenado. La grasa sigue abierta y el número viejo no descuenta."""
    uno = Mente()
    uno.declarar(2000)
    uno.sentar_hacha(40)
    uno.cobrar()
    _cerca(uno.firmada(), 0, "cobrado, la mente se callo")
    _cerca(deber(1220, [uno]), 1220, "la grasa no queda desnuda")
    uno.declarar(200)
    _cerca(deber(1220, [uno]), 1020, "despues de callarse puede volver a hablar")


def el_otro_cazador_sigue_hablando() -> None:
    """El hacha de uno no apaga la Oz de otro."""
    condenado = Mente()
    condenado.sentar_hacha(40)
    otro = Mente()
    otro.declarar(500)
    _cerca(firmada([condenado, otro], 100), 4500, "hacha mas la otra Oz")
    _cerca(deber(12000, [condenado, otro], 100), 7500, "el deber de los dos")


def no_voltea_ni_se_pasa() -> None:
    """Firmar más que la bolsa no abre el lado contrario."""
    uno = Mente()
    uno.declarar(2000)
    _cerca(deber(500, [uno]), 0, "el deber no baja de cero")
    try:
        uno.declarar(-1)
    except ValueError:
        print("OK  la mente no declara negativo")
    else:
        raise SystemExit("TUMOR acepto masa negativa")
    try:
        uno.sentar_hacha(-1)
    except ValueError:
        print("OK  el hacha no agarra negativo")
        return
    raise SystemExit("TUMOR el hacha acepto monedas negativas")


def el_latido_no_come_la_grasa() -> None:
    """Iron y la mente, en el mismo camino. La grasa de después no sale ni queda desnuda."""
    from cirugias.hiron.guardian import Hiron
    from cirugias.hiron.masacre_precio import Sello
    from cirugias.hiron.viaje import Viaje

    viaje = Viaje("LONG")
    viaje.abrir(40, 100)
    sello = Sello("verde")
    mente = Mente()
    px = 100.0
    suelo = None
    for _ in range(400):
        px = round(px + 0.25, 10)
        suelo = sello.marcar(viaje, 400.0, px, "limpia")
        if sello.quieto("LONG"):
            break
    else:
        raise SystemExit("TUMOR el activador no prendio")
    if suelo is None:
        raise SystemExit("TUMOR el suelo no quedo")
    mente.sentar_hacha(viaje.cantidad)
    hiron = Hiron("LONG", "limpia", float(suelo))
    if hiron.ver(px, viaje.cantidad):
        raise SystemExit("TUMOR nacer ya cerro")
    if not hiron.nacido or hiron.condenadas != 40:
        raise SystemExit("TUMOR iron no condeno las cuarenta del activador")
    while px < 159:
        px = round(px + 0.5, 10)
        if hiron.ver(px, viaje.cantidad):
            raise SystemExit("TUMOR cobro de camino al extremo")
    bolsa = viaje.cantidad * px
    if deber(bolsa, [mente], px) > 1e-6:
        raise SystemExit("TUMOR la misma condena volvio a pedir cubierta")
    print("OK  la marca subio y la condena siguio en cero")
    viaje.abrir(10, px)
    bolsa = viaje.cantidad * px
    grasa = 10 * px
    _cerca(deber(bolsa, [mente], px), grasa, "la grasa cubierta antes de cobrar")
    if hiron.oz is None or not hiron.ver(hiron.oz, viaje.cantidad):
        raise SystemExit("TUMOR iron no cobro")
    cierre = hiron.a_cerrar(viaje.cantidad)
    _cerca(cierre, 40.0, "cobra las condenadas y deja la grasa")
    mente.cobrar()
    viaje.reducir(cierre or 0, hiron.oz)
    queda = viaje.cantidad * hiron.oz
    _cerca(deber(queda, [mente], hiron.oz), queda, "la grasa viva despues de cobrar")


def main() -> None:
    la_suma_no_adivina()
    el_arrepentimiento_vuelve_a_cargar()
    al_cobrarse_declara_cero()
    sin_activador_el_resto_no_cuenta()
    el_activador_guarda_monedas()
    al_cobrar_se_calla()
    el_otro_cazador_sigue_hablando()
    el_latido_no_come_la_grasa()
    no_voltea_ni_se_pasa()
    print("RADAR_REVISADO")


if __name__ == "__main__":
    main()
