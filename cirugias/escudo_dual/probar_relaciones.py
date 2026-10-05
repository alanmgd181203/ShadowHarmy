"""Paso 1 en seco. Si la relación chica se confunde con parecerse, es tumor."""
from cirugias.escudo_dual.relaciones import las_dos, relacion


def _camino(saltos: list[float]) -> list[float]:
    precio = 100.0
    out = [precio]
    for salto in saltos:
        precio = precio * (1.0 + salto)
        out.append(precio)
    return out


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(float(a) - b) > 1e-9:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def _no_es(a: float | None, mentira: float, nombre: str) -> None:
    if a is not None and abs(float(a) - mentira) < 1e-9:
        raise SystemExit(f"TUMOR {nombre}: cayo en {mentira}")
    print(f"OK  {nombre} no es {mentira}")


def _calla(a: float | None, nombre: str) -> None:
    if a is not None:
        raise SystemExit(f"TUMOR {nombre}: hablo {a}")
    print(f"OK  {nombre} no habla")


MAREA = [0.1, -0.1, 0.1, -0.1]
REY = [0.05, -0.05, 0.05, -0.05]
REINA = [0.2, -0.2, 0.2, -0.2]


def la_reina_que_se_sacude_mas_pide_menos() -> None:
    """La marea salta 10. El rey, 5. La reina, 20.

    Relación del rey = 2. La de la reina = 0,5. No 1,5 restando.
    El que copia la marea queda en 1, que es más grande: no es el parecido.
    """
    marea = _camino(MAREA)
    par = las_dos(marea, _camino(REY), _camino(REINA))
    _cerca(par["rey"], 2.0, "el rey pide el doble")
    _cerca(par["reina"], 0.5, "la reina pide la mitad")
    _no_es(par["reina"], 2.0 - 0.5, "reina")
    _no_es(par["rey"], 1.6, "rey")
    _no_es(par["rey"], 1.8, "rey")
    copia = relacion(marea, _camino(MAREA))
    _cerca(copia, 1.0, "el que copia la marea")
    if par["reina"] is None or copia is None or par["reina"] >= copia:
        raise SystemExit("TUMOR la mas chica resulto la que se parece")
    print("OK  la mas chica es la que se sacude mas, no la que se parece")


def al_reves_sigue_siendo_tamano() -> None:
    """Mismos saltos, sentido contrario. El tamaño no se entera. El permiso, después."""
    marea = _camino(MAREA)
    invertida = relacion(marea, _camino([-0.1, 0.1, -0.1, 0.1]))
    _cerca(invertida, 1.0, "invertida, el tamano sigue en uno")
    _no_es(invertida, 0.0, "invertida")


def sin_datos_no_inventa_uno() -> None:
    marea = _camino(MAREA)
    _calla(relacion(marea, []), "reina sin precios")
    _calla(relacion([], _camino(REY)), "marea vacia")
    _calla(relacion(marea, [100, 100, 100, 100, 100]), "metal quieto")
    par = las_dos(marea, _camino(REY), [])
    _cerca(par["rey"], 2.0, "el rey sigue midiendo")
    _calla(par["reina"], "la reina ausente")
    _no_es(par["reina"], 1.0, "ausente")


def la_marea_es_la_misma() -> None:
    marea = _camino(MAREA)
    solo_rey = relacion(marea, _camino(REY))
    con_reina = las_dos(marea, _camino(REY), _camino(REINA))["rey"]
    _cerca(con_reina, solo_rey if solo_rey is not None else -1, "el rey no cambia porque exista la reina")


def main() -> None:
    la_reina_que_se_sacude_mas_pide_menos()
    al_reves_sigue_siendo_tamano()
    sin_datos_no_inventa_uno()
    la_marea_es_la_misma()
    print("PASO_1_REVISADO")


if __name__ == "__main__":
    main()
