"""Paso 4 en seco. Si cualquier mecha cuenta como tropiezo, es tumor."""
from cirugias.hiron.subida import Subida


def _exige(nombre: str, clase: str | None, esperada: str) -> None:
    if clase != esperada:
        raise SystemExit(f"TUMOR {nombre}: salio {clase}, debia {esperada}")
    print(f"OK  {nombre} = {clase}")


def recta() -> None:
    s = Subida("verde", "LONG")
    s.anclar_oz(100)
    s.anclar_meta(104)
    s.ver(102)
    if s.clase() is not None:
        raise SystemExit("TUMOR clasifico antes de tocar la masacre")
    _exige("recta", s.ver(104), "limpia")


def mecha_chica_no_es_tropiezo() -> None:
    """Verde es 0,5 %. Una bajada de 0,1 desde 103 no es peldaño."""
    s = Subida("verde", "LONG")
    s.anclar_oz(100)
    s.anclar_meta(104)
    s.ver(103)
    s.ver(102.9)
    s.ver(104)
    _exige("mecha chica sigue limpia", s.clase(), "limpia")


def el_ultimo_retroceso_manda() -> None:
    """Uno temprano y otro a mitad. No se queda con el primero."""
    s = Subida("verde", "LONG")
    s.paso = 0.01
    s.anclar_oz(100)
    s.anclar_meta(104)
    s.ver(101.5)
    s.ver(100.4)  # 101.5 * 0.99 = 100.485; 100.4 es retroceso, fracción 0.10
    s.ver(103)
    s.ver(101.9)  # 103 * 0.99 = 101.97; fracción (101.9-100)/4 = 0.475
    _exige("el retroceso de en medio", s.ver(104), "normal")
    if s.arranque is None or s.arranque < 0.25 or s.arranque > 0.75:
        raise SystemExit(f"TUMOR arranque {s.arranque}")


def tardio() -> None:
    """Pico 103.8, un peldaño de 0,5 % deja el suelo pasado el 75 %."""
    s = Subida("verde", "LONG")
    s.anclar_oz(100)
    s.anclar_meta(104)
    s.ver(103.8)
    suelo = 103.8 * (1 - 0.005)
    if (suelo - 100) / 4 <= 0.75:
        raise SystemExit(f"el ejemplo no pasa del 75: {suelo}")
    s.ver(suelo)
    _exige("retroceso tardio", s.ver(104), "dificil")


def no_se_reescribe() -> None:
    s = Subida("verde", "LONG")
    s.anclar_oz(100)
    s.anclar_meta(104)
    s.ver(104)
    s.ver(90)
    s.ver(103.2)
    s.ver(101)
    _exige("despues de sellar sigue limpia", s.clase(), "limpia")
    s.anclar_meta(120)
    if abs((s.meta or 0) - 104) > 1e-9:
        raise SystemExit("TUMOR la meta se corrio")
    print("OK  la meta se quedo en 104")


def borde_25_y_75() -> None:
    """El suelo exacto en el 25 % sigue siendo limpia. En el 75 %, normal."""
    s = Subida("verde", "LONG")
    s.paso = 2 / 103
    s.anclar_oz(100)
    s.anclar_meta(104)
    s.ver(103)
    s.ver(101)
    if abs((101 - 100) / 4 - 0.25) > 1e-12:
        raise SystemExit("el 101 no es el 25")
    _exige("el 25 sigue siendo limpia", s.ver(104), "limpia")

    n = Subida("verde", "LONG")
    n.paso = (103.2 - 103) / 103.2
    n.anclar_oz(100)
    n.anclar_meta(104)
    n.ver(103.2)
    n.ver(103)
    if n.arranque is not None:
        raise SystemExit("clasifico antes de la meta")
    _exige("el 75 sigue siendo normal", n.ver(104), "normal")
    if n.arranque is None or abs(n.arranque - 0.75) > 1e-9:
        raise SystemExit(f"TUMOR borde 75 arranque {n.arranque}")


def corto() -> None:
    """De 100 a 96. Un rebote de un peldaño cerca del final es difícil."""
    s = Subida("verde", "SHORT")
    s.anclar_oz(100)
    s.anclar_meta(96)
    s.ver(96.2)
    rebote = 96.2 * (1 + 0.006)
    s.ver(rebote)
    frac = (100 - rebote) / 4
    if frac <= 0.75:
        raise SystemExit(f"el rebote no quedo tarde: {frac}")
    _exige("corto con rebote tarde", s.ver(96), "dificil")


def antes_de_la_oz_no_cuenta() -> None:
    s = Subida("verde", "LONG")
    s.ver(50)
    s.ver(40)
    s.anclar_oz(100)
    s.anclar_meta(104)
    _exige("lo anterior a la oz no mancha", s.ver(104), "limpia")


def main() -> None:
    recta()
    mecha_chica_no_es_tropiezo()
    el_ultimo_retroceso_manda()
    tardio()
    no_se_reescribe()
    borde_25_y_75()
    corto()
    antes_de_la_oz_no_cuenta()
    print("PASO_4_REVISADO")


if __name__ == "__main__":
    main()
