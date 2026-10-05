"""Paso 1 en seco. No es un smoke de camino feliz.

Cada caso dice qué número tiene que salir, y qué mentira
diría el promedio de lo que sigue abierto.
"""
from cirugias.hiron.viaje import Libro


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(a - b) > 1e-9:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def casa_promedio_solo_suma(compras: list[tuple[float, float]]) -> float:
    """Lo que hace el promedio de la casa: solo pondera entradas. Las ventas no existen."""
    masa = 0.0
    costo = 0.0
    for cantidad, precio in compras:
        masa += cantidad
        costo += cantidad * precio
    return costo / masa


def caso_venta_barata() -> None:
    """Seis compras de 100 a 90. Promedio 95.
    Vende 1 en 91 y 1 en 93. El viaje exige 96.5, no 95.
    """
    libro = Libro()
    for px in (100, 98, 96, 94, 92, 90):
        libro.abrir_largo(1, px)
    _cerca(libro.largo.quiebre(), 95.0, "antes de vender, quiebre 95")
    libro.reducir_largo(1, 91)
    libro.reducir_largo(1, 93)
    mentira = casa_promedio_solo_suma([(1, px) for px in (100, 98, 96, 94, 92, 90)])
    real = libro.largo.quiebre()
    if real is None or abs(real - mentira) < 1e-9:
        raise SystemExit(f"TUMOR se quedo en el promedio de la casa {mentira}")
    _cerca(real, 96.5, "venta barata sube el quiebre a 96.5")
    _cerca(libro.largo.masa_negociada, 570.0, "la masa negociada no olvida lo vendido")
    if abs(libro.largo.cantidad - 4) > 1e-9:
        raise SystemExit("TUMOR cantidad")
    # Promedio de lo que quedaria si se vendieran primero los baratos (90 y 92):
    # quedan 100, 98, 96, 94 → 97. Tampoco es el quiebre.
    promedio_resto_barato = (100 + 98 + 96 + 94) / 4
    if abs(real - promedio_resto_barato) < 1e-6:
        raise SystemExit("TUMOR quiebre = promedio del resto")
    print(f"    la casa diria {mentira}; el resto barato diria {promedio_resto_barato}")


def caso_venta_cara_baja_quiebre() -> None:
    """Compra 1 en 100. Vende la mitad en 150.
    Queda media unidad y 25 de caja. Quiebre 50, no 100.
    """
    libro = Libro()
    libro.abrir_largo(1, 100)
    libro.reducir_largo(0.5, 150)
    _cerca(libro.largo.quiebre(), 50.0, "venta cara baja el quiebre")
    _cerca(libro.largo.masa_negociada, 100.0, "masa negociada sigue en 100")


def caso_no_voltea() -> None:
    libro = Libro()
    libro.abrir_largo(2, 100)
    tomado = libro.reducir_largo(5, 80)
    if abs(tomado - 2) > 1e-9:
        raise SystemExit(f"TUMOR redujo {tomado}, debia 2")
    if libro.largo.vivo() or libro.corto.vivo():
        raise SystemExit("TUMOR el sobrante abrio el otro lado")
    if libro.largo.quiebre() is not None:
        raise SystemExit("TUMOR sin monedas invento quiebre")
    _cerca(libro.largo.masa_negociada, 200.0, "vaciar no olvida la masa")
    _cerca(libro.largo.entrada(), 100.0, "la entrada sigue en 100")
    libro.abrir_largo(1, 100)
    _cerca(libro.largo.quiebre(), 140.0, "el mismo lado sigue con la perdida")
    print("OK  morir no abre corto")


def caso_voltear_si_reinicia() -> None:
    """Vaciar no recetea. Cambiar de lado, sí."""
    libro = Libro()
    libro.abrir_largo(1, 100)
    libro.reducir_largo(1, 110)
    libro.abrir_largo(1, 100)
    _cerca(libro.largo.entrada(), 100.0, "las ventas no mueven la entrada")
    _cerca(libro.largo.quiebre(), 90.0, "la venta cara ya bajo el quiebre")
    _cerca(libro.largo.masa_negociada, 200.0, "siguen las dos entradas")
    libro.voltear()
    if libro.largo.entrada() is not None or libro.largo.masa_negociada != 0:
        raise SystemExit("TUMOR el volteo dejo memoria")
    libro.abrir_corto(1, 40)
    _cerca(libro.corto.quiebre(), 40.0, "el corto nace en 40")
    _cerca(libro.corto.masa_negociada, 40.0, "el corto no hereda la masa larga")
    if libro.largo.vivo():
        raise SystemExit("TUMOR el largo volvio al voltear")
    print("OK  voltear nace de cero")


def caso_dos_viajes() -> None:
    libro = Libro()
    libro.abrir_largo(2, 100)
    libro.abrir_corto(3, 50)
    libro.reducir_largo(1, 90)
    if not libro.corto.vivo():
        raise SystemExit("TUMOR reducir el largo mato al corto")
    _cerca(libro.corto.quiebre(), 50.0, "el corto no se entero del largo")
    # Largo: caja 200-90=110, cantidad 1, quiebre 110.
    _cerca(libro.largo.quiebre(), 110.0, "el largo no se entero del corto")


def caso_corto_cobertura_cara() -> None:
    """Abre 1 en 100. Cubre la mitad en 120.
    Caja 100-60=40, cantidad 0.5, quiebre 80.
    Cubrir caro obliga a comprar el resto más abajo.
    """
    libro = Libro()
    libro.abrir_corto(1, 100)
    libro.reducir_corto(0.5, 120)
    _cerca(libro.corto.quiebre(), 80.0, "cobertura cara baja el quiebre del corto")
    if libro.largo.vivo():
        raise SystemExit("TUMOR cubrir el corto abrio un largo")
    print("OK  cubrir no abre largo")


def caso_precios_no_se_promedian_por_orden() -> None:
    """100 dólares en 100 y 100 dólares en 50.
    Cantidad 1+2=3, caja 200, quiebre 66.666..., no 75.
    """
    libro = Libro()
    libro.abrir_largo(100 / 100, 100)
    libro.abrir_largo(100 / 50, 50)
    _cerca(libro.largo.quiebre(), 200 / 3, "pesa la cantidad, no el numero de ordenes")


def caso_reducir_en_cero_no_hace_nada() -> None:
    libro = Libro()
    tomado = libro.reducir_largo(1, 100)
    if tomado != 0 or libro.largo.vivo() or libro.corto.vivo():
        raise SystemExit("TUMOR reducir en vacio invento bolsa")
    print("OK  reducir en vacio no inventa bolsa")


def main() -> None:
    caso_venta_barata()
    caso_venta_cara_baja_quiebre()
    caso_no_voltea()
    caso_voltear_si_reinicia()
    caso_dos_viajes()
    caso_corto_cobertura_cara()
    caso_precios_no_se_promedian_por_orden()
    caso_reducir_en_cero_no_hace_nada()
    print("PASO_1_REVISADO")


if __name__ == "__main__":
    main()
