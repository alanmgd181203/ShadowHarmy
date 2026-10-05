"""El reloj, en seco. Si al llegar suelta los 400 de un golpe, es tumor.

Los números están sacados a mano. No se copian de la salida.
Verde largo: el peldaño es 0,5 %.
"""
from cirugias.hiron.reloj import Reloj


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


def la_recta_no_suelta_al_llegar() -> None:
    """Sin retroceso, llegar de un salto a la masacre no vacía la bolsa."""
    r = Reloj("verde", "LONG", 100, 104)
    _calla(r.ver(104, 400), "recta de un salto")
    if r.clase_sellada() != "limpia":
        raise SystemExit(f"TUMOR la recta sello {r.clase_sellada()}")
    _calla(r.ver(90, 400), "despues de sellar la limpia")
    print("OK  la limpia quedo sellada y Beru no cambio")


def la_normal_suelta_en_el_camino() -> None:
    """Pico 103,1 y suelo en 102. Fracción (102-100)/4 = 0,5. Normal.

    De 102 a 104 faltan 2 %, veinte décimas. 400 / 20 = 20.
    El paso que toca 104 paga 20, no los 400.
    """
    r = Reloj("verde", "LONG", 100, 104)
    _calla(r.ver(103.1, 400), "antes del retroceso")
    if r.clase_sellada() is not None:
        raise SystemExit("TUMOR sello la normal antes de la masacre")
    suelo = r.ver(102, 400)
    _cerca(suelo, 0.0, "el retroceso no suelta")
    if r.subida.ahora() != "normal":
        raise SystemExit(f"TUMOR en el suelo salio {r.subida.ahora()}")

    masa = 400.0
    total = 0.0
    ultimo = None
    for i in range(1, 21):
        sol = r.ver(102 + i * 0.1, masa)
        if sol is None:
            raise SystemExit(f"TUMOR la normal callo en el paso {i}")
        _no_es(sol, 400.0, f"paso {i}")
        _cerca(sol, 20.0, f"normal paso {i}")
        masa -= sol
        total += sol
        ultimo = sol
    _cerca(total, 400.0, "la normal del camino suma 400")
    _cerca(masa, 0.0, "al tocar ya no queda")
    _cerca(ultimo, 20.0, "el toque paga una decima")
    if r.clase_sellada() != "normal":
        raise SystemExit(f"TUMOR sello {r.clase_sellada()}")
    print("OK  la normal se sello al toque")


def el_salto_no_es_una_sola_decima() -> None:
    """Ya es normal en 102. Un salto a 103 son diez décimas: 200, no 20 ni 400."""
    r = Reloj("verde", "LONG", 100, 104)
    r.ver(103.1, 400)
    r.ver(102, 400)
    salto = r.ver(103, 400)
    _cerca(salto, 200.0, "salto de diez decimas")
    _no_es(salto, 20.0, "salto")
    _no_es(salto, 400.0, "salto")


def la_dificil_no_espera_al_final() -> None:
    """De 100 a 110. Pico 109, suelo 108. Fracción 0,8. Difícil, y la mitad ya pasó.

    De 108 a 110 falta un 2 %. La mitad de eso acaba en 109.
    Diez décimas, 40 cada una. En 110 ya no queda montón.
    """
    r = Reloj("verde", "LONG", 100, 110)
    _calla(r.ver(109, 400), "la subida todavia limpia")
    retro = r.ver(108, 400)
    _cerca(retro, 0.0, "el retroceso tardio no suelta")
    if r.subida.ahora() != "dificil":
        raise SystemExit(f"TUMOR el suelo tardio salio {r.subida.ahora()}")
    if r.clase_sellada() is not None:
        raise SystemExit("TUMOR la dificil se sello en el suelo")

    masa = 400.0
    total = 0.0
    for i in range(1, 11):
        sol = r.ver(108 + i * 0.1, masa)
        if sol is None:
            raise SystemExit(f"TUMOR la dificil callo en el paso {i}")
        _cerca(sol, 40.0, f"dificil paso {i}")
        _no_es(sol, 400.0, f"dificil paso {i}")
        masa -= sol
        total += sol
    _cerca(total, 400.0, "la dificil suma 400 antes de la marca")
    _cerca(masa, 0.0, "en 109 ya no queda")
    llegada = r.ver(110, masa)
    _cerca(llegada, 0.0, "llegar no paga otro monton")
    if r.clase_sellada() != "dificil":
        raise SystemExit(f"TUMOR sello {r.clase_sellada()}")
    cola = r.ver(111, 25)
    _cerca(cola, 25.0, "lo que nace pasada la ventana sale de una vez")


def el_corto_dificil_igual() -> None:
    """De 100 a 90. El verde corto usa peldaño de 0,6 %.

    Suelo 91,4 y rebote a 92: 91,4 por 1,006 es 91,948, así que 92 sí
    es peldaño. Fracción (100-92)/10 = 0,8. Desde 92, la mitad de lo
    que falta acaba en 91. Diez pasos de 40.

    Desde 92, la mitad de lo que falta acaba en 91. Diez pasos de 40.
    """
    r = Reloj("verde", "SHORT", 100, 90)
    _calla(r.ver(91.4, 400), "el corto todavia limpio")
    rebote = r.ver(92, 400)
    _cerca(rebote, 0.0, "el rebote no suelta")
    if r.subida.ahora() != "dificil":
        raise SystemExit(f"TUMOR el corto salio {r.subida.ahora()}")
    masa = 400.0
    total = 0.0
    for i in range(1, 11):
        sol = r.ver(92 - i * 0.1, masa)
        if sol is None:
            raise SystemExit(f"TUMOR el corto callo en el paso {i}")
        _cerca(sol, 40.0, f"corto paso {i}")
        masa -= sol
        total += sol
    _cerca(total, 400.0, "el corto dificil suma 400")
    llegada = r.ver(90, 0)
    _cerca(llegada, 0.0, "el corto al llegar no paga otro monton")
    if r.clase_sellada() != "dificil":
        raise SystemExit(f"TUMOR el corto sello {r.clase_sellada()}")


def main() -> None:
    la_recta_no_suelta_al_llegar()
    la_normal_suelta_en_el_camino()
    el_salto_no_es_una_sola_decima()
    la_dificil_no_espera_al_final()
    el_corto_dificil_igual()
    print("RELOJ_REVISADO")


if __name__ == "__main__":
    main()
