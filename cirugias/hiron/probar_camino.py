"""Paso 7 en seco. Si las piezas, juntas, mienten, es tumor.

Los números de abajo están sacados a mano. No se copian de la salida.
"""
from cirugias.hiron.camino import cierre
from cirugias.hiron.probar_reloj import (
    el_corto_dificil_igual,
    el_salto_no_es_una_sola_decima,
    la_dificil_no_espera_al_final,
    la_normal_suelta_en_el_camino,
    la_recta_no_suelta_al_llegar,
)
from cirugias.hiron.descarga import Descarga
from cirugias.hiron.guardian import Hiron
from cirugias.hiron.masacre_precio import Sello, precio_para_ganar
from cirugias.hiron.papel import Papel, ganancia_de_la_pierna, paso_del_tonto
from cirugias.hiron.subida import Subida
from cirugias.hiron.viaje import Libro


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(float(a) - b) > 1e-6:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def _no_es(a: float | None, mentira: float, nombre: str) -> None:
    if a is not None and abs(float(a) - mentira) < 1e-6:
        raise SystemExit(f"TUMOR {nombre}: cayo en {mentira}")
    print(f"OK  {nombre} no es {mentira}")


def _calla(a: float | None, nombre: str) -> None:
    if a is not None:
        raise SystemExit(f"TUMOR {nombre}: hablo {a}")
    print(f"OK  {nombre} no habla")


def el_viaje_no_se_recetea() -> None:
    """Seis compras, dos ventas baratas. Sigue siendo el mismo largo.

    Pagó 570. Cobró 91 y 93. Quedan 4. Caja 386. Quiebre 96,5.
    La casa, que no resta, se queda en 95. Vender barato no abre corto.
    """
    libro = Libro()
    for p in (100, 98, 96, 94, 92, 90):
        libro.abrir_largo(1, p)
    libro.reducir_largo(1, 91)
    libro.reducir_largo(1, 93)
    v = libro.largo
    if not v.vivo():
        raise SystemExit("TUMOR el viaje murio a mitad")
    _cerca(v.quiebre(), 96.5, "quiebre del viaje")
    _no_es(v.quiebre(), 95.0, "quiebre")
    _cerca(v.cantidad, 4.0, "siguen 4 monedas")
    _cerca(v.masa_negociada, 570.0, "la masa negociada no baja al vender")
    if libro.corto.vivo():
        raise SystemExit("TUMOR la venta barata abrio corto")
    print("OK  vender barato no abre corto")

    libro.abrir_largo(1, 80)
    if abs(v.quiebre() - 80) < 1e-9:
        raise SystemExit("TUMOR una compra nueva receteo el viaje")
    _cerca(v.quiebre(), 466 / 5, "la compra entra al mismo viaje")
    _cerca(v.cantidad, 5.0, "siguen en el mismo largo")
    libro.reducir_largo(1, 80)
    _cerca(v.quiebre(), 96.5, "al soltar esa compra vuelve el 96,5")


def _bolsa() -> Libro:
    libro = Libro()
    for p in (100, 98, 96, 94, 92, 90):
        libro.abrir_largo(1, p)
    libro.reducir_largo(1, 91)
    libro.reducir_largo(1, 93)
    return libro


def el_papel_alimenta_la_masacre(libro: Libro) -> tuple[Sello, float]:
    """El tonto, con paso de laboratorio 0,1: 100, 90, 99.

    Tres toques, trozo 190. La marca de hoy no alimenta la masacre.
    La salida es el uno por ciento de la pierna. Iron lee esa cifra.
    La masacre es la mecha recta desde el cero de Beru, no el cierre
    de un golpe ni la marca de hoy. El cero de Beru no es el del papel.
    """
    if abs(paso_del_tonto("verde", "LONG") - 0.005) > 1e-12:
        raise SystemExit("TUMOR el peldaño verde ya no es 0,5")
    papel = Papel("verde", "LONG")
    papel.paso = 0.1
    papel.ver_precio(100)
    papel.ver_precio(90)
    papel.ver_precio(99)
    masa = libro.largo.masa_negociada
    cuentas = papel.cuentas(masa, 99)
    f = papel.peaje
    puerta = (200 * (1 + f) / (1 + 100 / 90)) / (1 - f)
    _cerca(cuentas["quiebre"], puerta, "quiebre del papel")
    monedas = 1 + 100 / 90 - 100 / 99
    caja = 200 * (1 + f) - 100 * (1 - f)
    quiebre_vivo = (caja / monedas) / (1 - f)
    marca = (99 - quiebre_vivo) * monedas * (masa / 300)
    salida = ganancia_de_la_pierna(masa)
    _cerca(cuentas["dolares"], marca, "la marca de hoy no es la salida")
    _cerca(cuentas["salida"], salida, "la promesa es la pierna completa")
    _no_es(cuentas["salida"], marca, "salida")
    _no_es(cuentas["salida"], 41.591, "salida")
    resto = 4 * 96.5
    mentira = papel.cuentas(resto, 99)["salida"]
    if mentira is not None and abs(mentira - salida) < 1e-6:
        raise SystemExit("TUMOR el resto abierto dio la misma salida que toda la masa")
    print(f"OK  con el resto abierto serian {mentira}, no {salida}")

    q = libro.largo.quiebre() or 0.0
    monedas_abiertas = libro.largo.cantidad
    del_suelo = ganancia_de_la_pierna(monedas_abiertas * q)
    paso = paso_del_tonto("verde", "LONG")
    masacre = precio_para_ganar("LONG", q, monedas_abiertas, del_suelo or 0.0, paso)
    if del_suelo is None or masacre is None:
        raise SystemExit("TUMOR el suelo de lo abierto no salio")
    hinchado = precio_para_ganar("LONG", q, monedas_abiertas, salida or 0.0, paso)
    if hinchado is None or masacre >= hinchado:
        raise SystemExit(f"TUMOR la pierna entera siguio alargando el suelo {masacre} {hinchado}")
    sello = Sello()
    activador = masacre * 1.01
    px = sello.leer_papel(libro.largo, masa, activador, "limpia")
    _cerca(sello.promesa("LONG"), salida, "iron leyo la pierna entera")
    _cerca(salida, masa * 0.01, "la promesa es el uno por ciento")
    _cerca(px, masacre, "masacre")
    doble = Sello().leer_papel(libro.largo, masa * 2)
    _cerca(doble, px, "la historia no alarga el suelo")
    _no_es(px, 96.5 + marca / 570, "masacre")
    if not sello.quieto("LONG"):
        raise SystemExit("TUMOR el activador no dejo quieta la masacre")
    libro.abrir_largo(1, 50)
    if sello.marcar(libro.largo, 80, 50, "limpia") != px:
        raise SystemExit("TUMOR el precio se corrio despues del activador")
    _cerca(sello.precio("LONG"), masacre, "el precio sigue quieto")
    if abs(libro.largo.quiebre() - masacre) < 1e-6:
        raise SystemExit("TUMOR el viaje se igualo a la masacre")
    libro.reducir_largo(1, 50)
    _cerca(libro.largo.quiebre(), 96.5, "el viaje sigue en 96,5")
    return sello, salida


def la_subida_limpia_no_toca_la_masa(sello: Sello) -> str:
    meta = sello.precio("LONG")
    if meta is None:
        raise SystemExit("TUMOR no hay masacre para clasificar")
    subida = Subida("verde", "LONG")
    subida.anclar_oz(96)
    subida.anclar_meta(meta)
    if abs(subida.meta - (sello.precio("LONG") or 0)) > 1e-9:
        raise SystemExit("TUMOR la subida no uso el precio quieto")
    subida.ver(100)
    subida.ver(99.6)
    clase = subida.ver(meta)
    if clase != "limpia":
        raise SystemExit(f"TUMOR la recta salio {clase}")
    print("OK  la recta hasta la masacre es limpia")
    if subida.ver(90) != "limpia":
        raise SystemExit("TUMOR la caida de despues reescribio la clase")
    if abs(subida.meta - meta) > 1e-12:
        raise SystemExit("TUMOR la meta se fue detras del precio")
    print("OK  la clase quedo sellada")

    descarga = Descarga("LONG", clase, 96, meta)
    _calla(descarga.al_pie(400), "limpia")
    _calla(descarga.soltar(96, meta, 400), "limpia en el camino")
    if descarga.habla:
        raise SystemExit("TUMOR la limpia se puso a soltar")
    return clase


def hiron_cierra_lo_que_queda(libro: Libro, sello: Sello, clase: str) -> Hiron:
    libro.abrir_corto(1, 50)
    meta = sello.precio("LONG")
    if meta is None:
        raise SystemExit("TUMOR se perdio la masacre")
    libro.reducir_largo(1, 100)
    if not libro.largo.vivo():
        raise SystemExit("TUMOR se acabo el largo antes de tiempo")
    _cerca(libro.largo.cantidad, 3.0, "quedan 3")
    _cerca(libro.largo.quiebre(), 286 / 3, "vender arriba bajo el quiebre")
    _cerca(sello.a_cerrar(libro.largo), 3.0, "el sello ve 3")
    _cerca(sello.precio("LONG"), meta, "soltar no movio la masacre")
    _cerca(libro.corto.quiebre(), 50.0, "el corto sigue en 50")
    if libro.corto.cantidad != 1:
        raise SystemExit("TUMOR el corto se mezclo con el largo")
    print("OK  el corto no murio")

    h = Hiron("LONG", clase, meta)
    if h.ver(meta):
        raise SystemExit("TUMOR Hiron cerro al tocar la masacre")
    if h.nacido:
        raise SystemExit("TUMOR Hiron nacio en la masacre")
    print("OK  en la masacre Hiron sigue dormido")
    nacimiento = meta * 1.01
    if h.ver(nacimiento):
        raise SystemExit("TUMOR nacer ya cerro")
    _cerca(h.oz, nacimiento * 0.99, "la oz un uno por ciento detras")
    _calla(cierre(h, libro.largo, sello), "antes del toque")
    if not h.ver(h.oz):
        raise SystemExit("TUMOR no toco su oz")
    cerrado = cierre(h, libro.largo, sello)
    _cerca(cerrado, 3.0, "cierra las 3 que quedan")
    _no_es(cerrado, 4.0, "cierre")
    _calla(cierre(h, libro.corto, sello), "no cierra el corto")
    if not h.beru_sigue:
        raise SystemExit("TUMOR Hiron apago a Beru")
    print("OK  Beru sigue")
    return h


def el_viaje_nuevo_no_hereda(libro: Libro, sello: Sello, viejo: Hiron) -> None:
    libro.reducir_largo(libro.largo.cantidad, 110)
    if libro.largo.vivo():
        raise SystemExit("TUMOR el largo no murio")
    if sello.marcar(libro.largo, 17.1) is not None:
        raise SystemExit("TUMOR el viaje muerto dejo el precio")
    _calla(cierre(viejo, libro.largo, sello), "el viejo no cierra un muerto")

    libro.abrir_largo(2, 80)
    px = sello.marcar(libro.largo, 8)
    golpe = 62.0
    if px is None or px <= golpe:
        raise SystemExit(f"TUMOR la mecha heredada no paso el golpe {px}")
    _no_es(px, 84.0, "el mismo lado")
    nuevo = Hiron("LONG", "limpia", px)
    if viejo.ver(80):
        raise SystemExit("TUMOR el guardian viejo, ya tocado, volvio a cazar")
    nacido = Hiron("LONG", "limpia", viejo.meta)
    nacido.ver(viejo.meta * 1.01)
    if cierre(nacido, libro.largo, sello) is not None:
        raise SystemExit("TUMOR el guardian del precio viejo cerro la bolsa nueva")
    print("OK  la bolsa nueva no hereda al guardian viejo")
    if nuevo.ver(px):
        raise SystemExit("TUMOR el nuevo cerro en su propia masacre")
    if nuevo.ver(px * 1.01):
        raise SystemExit("TUMOR el nuevo cerro al nacer")
    _cerca(nuevo.oz, px * 1.01 * 0.99, "el nuevo mide desde la mecha")


def el_reloj_de_la_descarga() -> None:
    """Beru suelta en el camino. La clase se sella al tocar, y el toque no vacía de un golpe."""
    la_recta_no_suelta_al_llegar()
    la_normal_suelta_en_el_camino()
    el_salto_no_es_una_sola_decima()
    la_dificil_no_espera_al_final()
    el_corto_dificil_igual()

    monedas = sum(10 / p for p in (100.1, 100.2, 100.3, 100.4))
    monton = 40 / 100.4
    if abs(monedas - monton) < 1e-9:
        raise SystemExit("TUMOR convertir al final dio las mismas monedas")
    print(f"OK  cuatro decimas son {monedas} monedas, no {monton} al ultimo precio")

    h = Hiron("LONG", "dificil", 104)
    if h.ver(102.51):
        raise SystemExit("TUMOR Hiron nacio en el fin de la descarga, no en la masacre")
    if h.nacido:
        raise SystemExit("TUMOR el 0,5 se midio desde la mitad")
    print("OK  Hiron mide desde la masacre, no desde donde acaba la descarga")
    if h.ver(104 * 1.005):
        raise SystemExit("TUMOR nacer ya cerro")
    _cerca(h.oz, 104 * 1.005 * 0.995, "dificil, oz al 0,5")


def main() -> None:
    el_viaje_no_se_recetea()
    libro = _bolsa()
    sello, _dolares = el_papel_alimenta_la_masacre(libro)
    clase = la_subida_limpia_no_toca_la_masa(sello)
    viejo = hiron_cierra_lo_que_queda(libro, sello, clase)
    el_viaje_nuevo_no_hereda(libro, sello, viejo)
    el_reloj_de_la_descarga()
    print("PASO_7_REVISADO")


if __name__ == "__main__":
    main()
