"""Paso 3 en seco. Si el precio se confunde con un quiebre, es tumor."""
import math

from cirugias.hiron.masacre_precio import (  # noqa: E402
    caja_con_lo_realizado,
    Sello,
    golpe_de_un_golpe,
    precio_para_ganar,
)
from cirugias.hiron.viaje import Libro, Viaje


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(float(a) - b) > 1e-9:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def _no_es(a: float | None, mentira: float, nombre: str) -> None:
    if a is not None and abs(float(a) - mentira) < 1e-9:
        raise SystemExit(f"TUMOR {nombre}: cayo en {mentira}")
    print(f"OK  {nombre} no es {mentira}")


def largo_a_mano() -> None:
    """Quiebre 93, cinco monedas, 10 dólares. El golpe es 95.

    Hay peldaños de 0,5 % entre 93 y 95, así que la mecha acaba
    más arriba. Cerrar de un golpe no junta los 10.
    """
    paso = 0.005
    golpe = 95.0
    px = precio_para_ganar("LONG", 93, 5, 10, paso)
    if px is None or px <= golpe:
        raise SystemExit(f"TUMOR la mecha no quedo mas lejos que {golpe}: {px}")
    promedio = (px - 93) / math.log(px / 93)
    if abs(promedio - golpe) > 1e-6:
        raise SystemExit(f"TUMOR el promedio de la mecha es {promedio}, debia {golpe}")
    _no_es(px, 93.0, "precio")
    _no_es(px, 96.0, "precio")
    print(f"OK  la mecha larga junta los 10 en {px}")


def corto_por_debajo() -> None:
    paso = 0.006
    golpe = 98.0
    px = precio_para_ganar("SHORT", 100, 5, 10, paso)
    if px is None or px >= golpe:
        raise SystemExit(f"TUMOR la mecha corta no quedo mas abajo que {golpe}: {px}")
    promedio = (100 - px) / math.log(100 / px)
    if abs(promedio - golpe) > 1e-6:
        raise SystemExit(f"TUMOR el promedio corto es {promedio}")
    print(f"OK  la mecha corta junta los 10 en {px}")


def un_peldano_no_estira_la_mecha() -> None:
    """Si el golpe cabe en el peldaño, no hay sueltas de camino."""
    px = precio_para_ganar("LONG", 100, 10, 0.2, 0.005)
    _cerca(px, 100.02, "un peldaño es el golpe")


def usa_el_quiebre_del_viaje_no_el_de_la_casa() -> None:
    """Seis compras de 100 a 90, vende en 91 y en 93.

    La casa se queda en 95. El viaje está en 96.5. La mecha usa ese
    cero, no la casa ni la masa negociada.
    """
    libro = Libro()
    for p in (100, 98, 96, 94, 92, 90):
        libro.abrir_largo(1, p)
    libro.reducir_largo(1, 91)
    libro.reducir_largo(1, 93)
    v = libro.largo
    if abs(v.quiebre() - 96.5) > 1e-9:
        raise SystemExit("el paso 1 ya no da 96.5")
    sello = Sello()
    px = sello.marcar(v, 10)
    golpe = 96.5 + 10 / 4
    if px is None or px <= golpe:
        raise SystemExit(f"TUMOR la mecha no paso el golpe {golpe}: {px}")
    _no_es(px, 95 + 10 / 4, "precio de masacre")
    migaja = 96.5 + 10 / v.masa_negociada
    _no_es(px, migaja, "precio de masacre")
    print(f"OK  la mecha sale de 96,5 y no de la casa, en {px}")


def el_suelo_se_arrima_hasta_el_activador() -> None:
    """Comprar más barato arrima el suelo. Pisar no lo deja quieto.

    El activador es uno por ciento más allá de la mecha de entonces.
    """
    libro = Libro()
    libro.abrir_largo(4, 96.5)
    sello = Sello()
    primero = sello.marcar(libro.largo, 10, 90, "limpia")
    golpe = 96.5 + 10 / 4
    if primero is None or primero <= golpe:
        raise SystemExit(f"TUMOR primera mecha {primero}")
    if sello.quieto("LONG"):
        raise SystemExit("TUMOR se quedo quieto antes del activador")
    libro.abrir_largo(4, 90)
    segundo = sello.marcar(libro.largo, 10, 90, "limpia")
    if segundo is None or segundo >= primero:
        raise SystemExit(f"TUMOR la entrada mejor no arrimo {primero} -> {segundo}")
    if sello.quieto("LONG"):
        raise SystemExit("TUMOR el arrime ya lo dejo quieto")
    pasado = sello.marcar(libro.largo, 10, segundo, "limpia")
    if pasado != segundo or sello.quieto("LONG"):
        raise SystemExit("TUMOR pisar el suelo lo dejo quieto")
    toque = sello.marcar(libro.largo, 10, segundo * 1.01, "limpia")
    if toque != segundo or not sello.quieto("LONG"):
        raise SystemExit("TUMOR el activador no dejo el suelo quieto")
    libro.abrir_largo(4, 50)
    despues = sello.marcar(libro.largo, 80, 40, "limpia")
    if despues != segundo:
        raise SystemExit("TUMOR despues del activador el suelo se corrio")
    print(f"OK  arrimo de {primero} a {segundo} y ahi se queda")


def el_corto_espera_su_activador() -> None:
    libro = Libro()
    libro.abrir_corto(5, 100)
    sello = Sello()
    primero = sello.marcar(libro.corto, 10, 102, "dificil")
    golpe = 98.0
    if primero is None or primero >= golpe:
        raise SystemExit(f"TUMOR mecha corta {primero}")
    if sello.quieto("SHORT"):
        raise SystemExit("TUMOR el corto se quedo quieto arriba")
    libro.abrir_corto(5, 102)
    segundo = sello.marcar(libro.corto, 10, 102, "dificil")
    if segundo is None or segundo <= primero:
        raise SystemExit(f"TUMOR el corto no se arrimo {primero} -> {segundo}")
    if sello.quieto("SHORT"):
        raise SystemExit("TUMOR el corto quieto antes de bajar al activador")
    toque = sello.marcar(libro.corto, 10, segundo * 0.995, "dificil")
    if toque != segundo or not sello.quieto("SHORT"):
        raise SystemExit("TUMOR el activador del corto no dejo el suelo")
    libro.abrir_corto(5, 80)
    despues = sello.marcar(libro.corto, 40, 90, "dificil")
    if despues != segundo:
        raise SystemExit("TUMOR el corto ya no debia correrse")
    if sello.quieto("LONG"):
        raise SystemExit("TUMOR el largo se entero del activador del corto")
    print(f"OK  el corto arrimo de {primero} a {segundo}")


def lo_que_cierra_si_cambia() -> None:
    libro = Libro()
    libro.abrir_largo(4, 96.5)
    sello = Sello()
    suelo = sello.marcar(libro.largo, 10)
    if abs(sello.a_cerrar(libro.largo) - 4) > 1e-9:
        raise SystemExit("TUMOR al marcar no vio 4")
    libro.reducir_largo(1, 99)
    queda = sello.a_cerrar(libro.largo)
    if abs(queda - 3) > 1e-9:
        raise SystemExit(f"TUMOR cierra {queda}, ya se solto 1")
    dolares = sello.a_cerrar_dolares(libro.largo, 100)
    if abs(dolares - 300) > 1e-6:
        raise SystemExit(f"TUMOR cierra {dolares} dolares, debian quedar 300")
    if sello.precio("LONG") != suelo:
        raise SystemExit("TUMOR al soltar masa, sin preguntar, se movio el precio")
    print("OK  cierra 3, el precio no se mueve solo")


def el_viaje_muerto_no_deja_el_precio() -> None:
    libro = Libro()
    libro.abrir_largo(4, 96.5)
    sello = Sello()
    sello.marcar(libro.largo, 10)
    libro.reducir_largo(4, 100)
    if sello.marcar(libro.largo, 10) is not None:
        raise SystemExit("TUMOR un viaje muerto dejo el precio")
    if sello.a_cerrar(libro.largo) != 0:
        raise SystemExit("TUMOR cierra un viaje muerto")
    libro.abrir_largo(2, 80)
    px = sello.marcar(libro.largo, 8)
    q = libro.largo.quiebre()
    golpe = golpe_de_un_golpe("LONG", q, 2, 8)
    if px is None or golpe is None or px <= golpe:
        raise SystemExit(f"TUMOR la herencia no camino la mecha {px} golpe {golpe}")
    _no_es(px, 80.0, "viaje heredado")
    print(f"OK  el mismo lado hereda la caja y la mecha queda en {px}")


def sin_ganancia_no_hay_precio() -> None:
    if precio_para_ganar("LONG", 93, 5, 0) is not None:
        raise SystemExit("TUMOR dolares en cero inventaron precio")
    if precio_para_ganar("LONG", 93, 5, -4) is not None:
        raise SystemExit("TUMOR una perdida invento precio")
    if precio_para_ganar("LONG", 93, 0, 10) is not None:
        raise SystemExit("TUMOR sin bolsa invento precio")
    print("OK  sin ganancia o sin bolsa no hay precio")


def quiebre_bajo_cero_no_se_clava() -> None:
    """Bajo cero no hay peldaños. Se queda el golpe, y no se recorta a cero."""
    px = precio_para_ganar("LONG", -100, 0.5, 10, 0.005)
    _cerca(px, -80.0, "quiebre bajo cero no se recorta")
    _no_es(px, 0.0, "precio")


def el_otro_lado_no_se_entera() -> None:
    libro = Libro()
    libro.abrir_largo(5, 93)
    libro.abrir_corto(5, 100)
    sello = Sello()
    largo = sello.marcar(libro.largo, 10)
    corto = sello.marcar(libro.corto, 10)
    if largo is None or corto is None or largo <= 95 or corto >= 98:
        raise SystemExit(f"TUMOR los lados se mezclaron {largo} {corto}")
    print(f"OK  largo en {largo}, corto en {corto}")


def el_lejos_espera_y_la_limpia_cerca_no() -> None:
    """Lejos, un engorde chico espera. En la limpia, ya cerca, se lee ya."""
    libro = Libro()
    libro.abrir_largo(4, 96.5)
    sello = Sello()
    lejos = sello.marcar(libro.largo, 10, 50, "limpia")
    if lejos is None:
        raise SystemExit("TUMOR no hubo suelo")
    libro.abrir_largo(0.05, 96.5)
    espera = sello.marcar(libro.largo, 10, 50, "limpia")
    if espera != lejos:
        raise SystemExit(f"TUMOR lejos el engorde chico movio el suelo {lejos} -> {espera}")
    cerca = lejos * (1 - 4 * 0.005)
    libro.abrir_largo(0.05, 96.5)
    ahora = sello.marcar(libro.largo, 10, cerca, "limpia")
    if ahora == lejos:
        raise SystemExit("TUMOR cerca, en limpia, el engorde no se leyo")
    if ahora <= 0:
        raise SystemExit("TUMOR el engorde cerca rompio el suelo")
    print(f"OK  lejos se quedo en {lejos}; cerca, la limpia lo movio a {ahora}")


def lo_realizado_mueve_el_cero() -> None:
    """A favor arrima el suelo. En contra lo empuja. El promedio no basta."""
    perdido = Viaje("SHORT")
    perdido.cantidad = 10
    perdido.caja = caja_con_lo_realizado("SHORT", 100, 10, -20)
    _cerca(perdido.quiebre(), 98.0, "perdida empuja el cero del corto")
    ganado = Viaje("SHORT")
    ganado.cantidad = 10
    ganado.caja = caja_con_lo_realizado("SHORT", 100, 10, 15)
    _cerca(ganado.quiebre(), 101.5, "ganancia arrima el cero del corto")
    largo_malo = Viaje("LONG")
    largo_malo.cantidad = 10
    largo_malo.caja = caja_con_lo_realizado("LONG", 100, 10, -20)
    _cerca(largo_malo.quiebre(), 102.0, "perdida empuja el cero del largo")
    largo_bueno = Viaje("LONG")
    largo_bueno.cantidad = 10
    largo_bueno.caja = caja_con_lo_realizado("LONG", 100, 10, 15)
    _cerca(largo_bueno.quiebre(), 98.5, "ganancia arrima el cero del largo")
    casa = Viaje("SHORT")
    casa.cantidad = 10
    casa.caja = caja_con_lo_realizado("SHORT", 100, 10, 0)
    sello_casa = Sello("verde")
    sello_mal = Sello("verde")
    sello_bien = Sello("verde")
    suelo_casa = sello_casa.leer_papel(casa, 1000)
    suelo_mal = sello_mal.leer_papel(perdido, 1000)
    suelo_bien = sello_bien.leer_papel(ganado, 1000)
    if None in (suelo_casa, suelo_mal, suelo_bien):
        raise SystemExit("TUMOR el realizado dejo el suelo vacio")
    if not (suelo_mal < suelo_casa < suelo_bien):
        raise SystemExit(
            f"TUMOR el corto no oyó lo realizado {suelo_mal} {suelo_casa} {suelo_bien}"
        )
    print(f"OK  corto: en contra {suelo_mal}, casa {suelo_casa}, a favor {suelo_bien}")


def main() -> None:
    largo_a_mano()
    corto_por_debajo()
    un_peldano_no_estira_la_mecha()
    usa_el_quiebre_del_viaje_no_el_de_la_casa()
    el_suelo_se_arrima_hasta_el_activador()
    el_corto_espera_su_activador()
    lo_que_cierra_si_cambia()
    el_viaje_muerto_no_deja_el_precio()
    sin_ganancia_no_hay_precio()
    quiebre_bajo_cero_no_se_clava()
    el_otro_lado_no_se_entera()
    el_lejos_espera_y_la_limpia_cerca_no()
    lo_realizado_mueve_el_cero()
    print("PASO_3_REVISADO")


if __name__ == "__main__":
    main()
