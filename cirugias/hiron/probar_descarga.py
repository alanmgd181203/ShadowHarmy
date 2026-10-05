"""Paso 5 en seco. Si la limpia calla la masa, o queda cola, es tumor."""
from cirugias.hiron.descarga import Descarga


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


def limpia_no_apaga_la_masa() -> None:
    """Cero sería «no sueltes nada». La limpia es Beru original: este libro no habla."""
    d = Descarga("LONG", "limpia", 100, 104)
    _calla(d.al_pie(400), "limpia al pie")
    _calla(d.soltar(100, 100.1, 400), "limpia en el camino")
    if d.fin() is not None:
        raise SystemExit("TUMOR limpia anoto un fin")
    print("OK  limpia sin fin")


def normal_al_pie() -> None:
    """4 % desde 100 hasta 104. 400 / 40 décimas = 10. No 10,4 ni 50 ni 0,1 monedas."""
    d = Descarga("LONG", "normal", 100, 104)
    px = d.al_pie(400)
    _cerca(px, 10.0, "normal al pie")
    _no_es(px, 400 * 0.001 / (4 / 104), "normal")
    _no_es(px, 50.0, "normal")
    _no_es(px, 0.1, "normal")
    if d.fin() is None or abs(d.fin() - 104) > 1e-9:
        raise SystemExit(f"TUMOR fin normal {d.fin()}")
    print("OK  la normal acaba en la masacre")


def dificil_en_la_mitad() -> None:
    """La misma masa, el doble de ritmo, y acaba en 102. No en 104 y no a 5."""
    d = Descarga("LONG", "dificil", 100, 104)
    px = d.al_pie(400)
    _cerca(px, 20.0, "dificil al pie")
    _no_es(px, 10.0, "dificil")
    _no_es(px, 5.0, "dificil")
    if d.fin() is None or abs(d.fin() - 102) > 1e-9:
        raise SystemExit(f"TUMOR fin dificil {d.fin()}")
    print("OK  la dificil acaba a la mitad")


def lo_que_queda_no_es_la_masa_de_antes() -> None:
    """Ya soltó 50. No se vuelve a contar 10. 350 / 40 = 8,75."""
    d = Descarga("LONG", "normal", 100, 104)
    _cerca(d.al_pie(350), 8.75, "lo que queda al pie")
    _no_es(d.al_pie(350), 10.0, "resto")


def el_salto_cuenta_cada_decima() -> None:
    """De 100 a 100,4 hay cuatro décimas. 40 dólares, no 10."""
    d = Descarga("LONG", "normal", 100, 104)
    sol = d.soltar(100, 100.4, 400)
    _cerca(sol, 40.0, "salto de cuatro decimas")
    _no_es(sol, 10.0, "salto")


def a_mitad_no_reparte_sobre_las_cuarenta() -> None:
    """En 102, con 200 todavía, faltan 20 décimas. La próxima es 10, no 5.
    Cinco sería partir el resto entre las 40 de origen, y sobra cola.
    """
    d = Descarga("LONG", "normal", 100, 104)
    sol = d.soltar(102, 102.1, 200)
    _cerca(sol, 10.0, "mitad con la mitad de masa")
    _no_es(sol, 5.0, "mitad")


def tarde_todavia_vacia() -> None:
    """Llegó a 102 sin soltar. Quedan 200 del camino, no 10 de recuerdo.
    Si siguiera a 10, en la masacre todavía tendría 200.
    """
    d = Descarga("LONG", "normal", 100, 104)
    sol = d.soltar(102, 102.1, 400)
    _cerca(sol, 20.0, "tarde, la decima se pone al dia")
    _no_es(sol, 10.0, "tarde")


def el_recorrido_vacia() -> None:
    """Cuarenta pasos de 0,1 desde 100. Tiene que sumar 400 y no dejar cola."""
    d = Descarga("LONG", "normal", 100, 104)
    masa = 400.0
    precio = 100.0
    total = 0.0
    for i in range(1, 41):
        sig = 100.0 + i * 0.1
        sol = d.soltar(precio, sig, masa)
        if sol is None:
            raise SystemExit(f"TUMOR callo en el paso {i}")
        masa -= sol
        total += sol
        precio = sig
    _cerca(total, 400.0, "el recorrido normal suma 400")
    _cerca(masa, 0.0, "al llegar no queda bolsa")


def la_dificil_no_sigue_despues_de_la_mitad() -> None:
    d = Descarga("LONG", "dificil", 100, 104)
    masa = 400.0
    precio = 100.0
    total = 0.0
    for i in range(1, 21):
        sig = 100.0 + i * 0.1
        sol = d.soltar(precio, sig, masa)
        if sol is None:
            raise SystemExit(f"TUMOR dificil callo en el paso {i}")
        masa -= sol
        total += sol
        precio = sig
    _cerca(total, 400.0, "la dificil suma 400 antes de la mitad")
    _cerca(masa, 0.0, "en 102 ya no queda")
    despues = d.soltar(102, 104, masa)
    _cerca(despues, 0.0, "pasada la mitad no inventa masa")


def el_rebote_no_compra() -> None:
    d = Descarga("LONG", "normal", 100, 104)
    sol = d.soltar(100.5, 100.2, 400)
    _cerca(sol, 0.0, "un retroceso no suelta")
    _no_es(sol, 30.0, "rebote")


def antes_de_la_oz_no_es_terreno() -> None:
    d = Descarga("LONG", "normal", 100, 104)
    _calla(d.soltar(99, 99.5, 400), "debajo de la oz")
    sol = d.soltar(99, 100.2, 400)
    _cerca(sol, 20.0, "al cruzar la oz cuenta desde ella")


def la_masa_que_crecio_sale_al_cerrar_la_ventana() -> None:
    """Si al pasar el fin todavía hay bolsa, sale ahora. No se queda en la caza."""
    d = Descarga("LONG", "dificil", 100, 104)
    sol = d.soltar(102, 103, 50)
    _cerca(sol, 50.0, "la cola atrasada sale de una vez")
    _no_es(sol, 20.0, "cola")


def el_corto_baja() -> None:
    """De 100 a 96 hay otro 4 %. Al pie, 10. La difícil acaba en 98, no en 102."""
    n = Descarga("SHORT", "normal", 100, 96)
    _cerca(n.al_pie(400), 10.0, "corto normal al pie")
    sol = n.soltar(100, 99, 400)
    _cerca(sol, 100.0, "el corto suelta cien al bajar uno")
    if n.fin() is None or abs(n.fin() - 96) > 1e-9:
        raise SystemExit(f"TUMOR fin corto {n.fin()}")
    f = Descarga("SHORT", "dificil", 100, 96)
    _cerca(f.al_pie(400), 20.0, "corto dificil al pie")
    if f.fin() is None or abs(f.fin() - 98) > 1e-9:
        raise SystemExit(f"TUMOR fin corto dificil {f.fin()}")
    print("OK  el corto dificil acaba en 98")


def al_reves_no_inventa_tramo() -> None:
    d = Descarga("LONG", "normal", 100, 96)
    _calla(d.al_pie(400), "masacre del lado malo")
    _calla(d.soltar(100, 99, 400), "camino al reves")


def main() -> None:
    limpia_no_apaga_la_masa()
    normal_al_pie()
    dificil_en_la_mitad()
    lo_que_queda_no_es_la_masa_de_antes()
    el_salto_cuenta_cada_decima()
    a_mitad_no_reparte_sobre_las_cuarenta()
    tarde_todavia_vacia()
    el_recorrido_vacia()
    la_dificil_no_sigue_despues_de_la_mitad()
    el_rebote_no_compra()
    antes_de_la_oz_no_es_terreno()
    la_masa_que_crecio_sale_al_cerrar_la_ventana()
    el_corto_baja()
    al_reves_no_inventa_tramo()
    print("PASO_5_REVISADO")


if __name__ == "__main__":
    main()
