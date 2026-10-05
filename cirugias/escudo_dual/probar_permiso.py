"""Paso 2 en seco. Los pesos ya están dichos. Si un no borra los quince, es tumor.

Cada precio es un minuto. El último es ahora.
Los números están sacados a mano.
"""
from cirugias.escudo_dual.permiso import conceder, mirar


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(float(a) - b) > 1e-9:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def una_vela_no_contrata() -> None:
    """Un minuto junto, por fuerte que sea, no es el tramo de 3."""
    mirada = mirar([100.0, 120.0], [100.0, 150.0])
    if mirada["habla"]:
        raise SystemExit("TUMOR una vela ya hablaba")
    if conceder(mirada) is not None:
        raise SystemExit("TUMOR una vela contrato")
    print("OK  una vela no contrata")

    en_contra = mirar([100.0, 120.0], [100.0, 50.0])
    if conceder(en_contra) is not None:
        raise SystemExit("TUMOR una vela en contra ya quitaba el permiso")
    print("OK  una vela no lo quita")


def los_tres_minutos_pesan_la_mitad() -> None:
    """Cuatro precios: ahora y hace 3. La marea sube un 1 %. El metal también.

    Solo existe esa parte. Pesa 0,50 y concede.
    """
    marea = [100.0, 100.0, 100.0, 101.0]
    metal = [100.0, 100.0, 100.0, 101.0]
    mirada = mirar(marea, metal)
    _cerca(float(mirada["junto"]), 0.50, "los tres minutos")
    _cerca(float(mirada["contra"]), 0.0, "sin no")
    if conceder(mirada) is not True:
        raise SystemExit("TUMOR tres minutos juntos no concedieron")
    print("OK  tres minutos juntos conceden")


def el_temblor_no_es_traicion() -> None:
    """En tres minutos el metal baja un 0,4 %. Menos del 0,5 %. No es no."""
    marea = [100.0, 100.0, 100.0, 101.0]
    metal = [100.0, 100.0, 100.0, 99.6]
    mirada = mirar(marea, metal)
    if mirada["habla"]:
        raise SystemExit("TUMOR el temblor voto")
    if conceder(mirada) is not None:
        raise SystemExit("TUMOR el temblor marco traidor o amigo")
    print("OK  menos de un 0,5 en contra no es traicion")


def en_contra_de_verdad_es_no() -> None:
    """Baja un 0,6 % mientras la marea sube. Eso sí es no, y pesa 0,50."""
    marea = [100.0, 100.0, 100.0, 101.0]
    metal = [100.0, 100.0, 100.0, 99.4]
    mirada = mirar(marea, metal)
    _cerca(float(mirada["contra"]), 0.50, "el no de los tres minutos")
    _cerca(float(mirada["junto"]), 0.0, "sin si")
    if conceder(mirada) is not False:
        raise SystemExit("TUMOR ir en contra de verdad no nego")
    print("OK  un 0,6 en contra es un no")


def el_poquito_a_favor_si_es_leal() -> None:
    """La marea sube un 1 %. El metal apenas un 0,02 %, pero va al mismo lado.

    Eso alcanza para decir sí. El 0,5 % no es la vara de la lealtad.
    """
    marea = [100.0, 100.0, 100.0, 101.0]
    metal = [100.0, 100.0, 100.0, 100.02]
    mirada = mirar(marea, metal)
    _cerca(float(mirada["junto"]), 0.50, "el poquito a favor")
    if conceder(mirada) is not True:
        raise SystemExit("TUMOR un poquito a favor no conto como leal")
    print("OK  un poquito a favor ya es leal")


def quedarse_quieto_no_es_traicion() -> None:
    """La marea sube y el metal no se mueve. Ruido, no traidor."""
    marea = [100.0, 100.0, 100.0, 102.0]
    metal = [100.0, 100.0, 100.0, 100.0]
    mirada = mirar(marea, metal)
    if conceder(mirada) is not None:
        raise SystemExit("TUMOR el metal quieto dijo si o no")
    print("OK  quedarse quieto no es traicion")


def la_marea_quieta_no_vota() -> None:
    """Si el resto del mercado no se movió, el mechazo del metal no contrata."""
    marea = [100.0, 100.0, 100.0, 100.0]
    metal = [100.0, 100.0, 100.0, 110.0]
    mirada = mirar(marea, metal)
    if mirada["habla"]:
        raise SystemExit("TUMOR la marea quieta dejo votar al metal")
    print("OK  la marea quieta no vota")


def _quince(a15: float, a5: float, a3: float, a0: float) -> list[float]:
    """16 minutos. El índice 0 es hace 15. Luego hace 5, hace 3, y ahora."""
    precios = [a15] * 16
    precios[15 - 5] = a5
    precios[15 - 3] = a3
    precios[15] = a0
    return precios


def un_no_viejo_no_borra_el_ahora() -> None:
    """De 5 a 15 el metal cae un 1 %. Los últimos 5 van con la marea.

    El no pesa 0,20. Los sí pesan 0,80. Concede.
    """
    marea = _quince(100, 101, 102, 103)
    metal = _quince(100, 99, 99 * 1.01, 99 * 1.01 * 1.01)
    mirada = mirar(marea, metal)
    _cerca(float(mirada["contra"]), 0.20, "el tramo viejo")
    _cerca(float(mirada["junto"]), 0.80, "los cinco recientes")
    if conceder(mirada) is not True:
        raise SystemExit("TUMOR el no de hace diez minutos borro el ahora")
    print("OK  el no viejo pesa su 20 y no borra")


def el_ahora_en_contra_empata_y_no_contrata() -> None:
    """Los últimos 3 bajan un 0,6 %. De 3 a 15 van juntos.

    0,50 contra 0,50. No se lleva la capa, y no queda como traidor.
    """
    marea = _quince(100, 101, 102, 103)
    metal = _quince(100, 101, 102, 102 * 0.994)
    mirada = mirar(marea, metal)
    _cerca(float(mirada["junto"]), 0.50, "el resto junto")
    _cerca(float(mirada["contra"]), 0.50, "los tres en contra")
    if conceder(mirada) is not None:
        raise SystemExit("TUMOR el empate contrato o marco traidor")
    print("OK  si los si no ganan, no hay capa y no hay traidor")


def lo_de_hace_una_hora_no_vota() -> None:
    """Antes del minuto 15 el metal iba al revés. Dentro de los 15, junto.

    La hora vieja no cambia el sí.
    """
    viejo = [100.0, 90.0, 80.0]
    quince = _quince(100, 101, 102, 103)
    marea = viejo + quince
    metal = viejo + quince
    mirada = mirar(marea, metal)
    _cerca(float(mirada["junto"]), 1.0, "solo los quince")
    _cerca(float(mirada["contra"]), 0.0, "la hora no entro")
    if conceder(mirada) is not True:
        raise SystemExit("TUMOR la hora vieja quito el permiso")
    print("OK  hace una hora no vota")


def main() -> None:
    una_vela_no_contrata()
    los_tres_minutos_pesan_la_mitad()
    el_temblor_no_es_traicion()
    en_contra_de_verdad_es_no()
    el_poquito_a_favor_si_es_leal()
    quedarse_quieto_no_es_traicion()
    la_marea_quieta_no_vota()
    un_no_viejo_no_borra_el_ahora()
    el_ahora_en_contra_empata_y_no_contrata()
    lo_de_hace_una_hora_no_vota()
    print("PASO_2_REVISADO")


if __name__ == "__main__":
    main()
