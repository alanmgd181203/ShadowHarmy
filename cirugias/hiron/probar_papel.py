"""Paso 2 en seco. El camino feliz no basta.

Si el quiebre coincide con el promedio de los precios, o con la
línea recta, es tumor: no contó el recorrido.
"""
from cirugias.hiron.papel import (
    Papel,
    cuenta_de_la_pierna,
    ganancia_de_la_pierna,
    paso_del_tonto,
)


def _cerca(a: float | None, b: float, nombre: str) -> None:
    if a is None or abs(float(a) - b) > 1e-6:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def _no_es(a: float | None, mentira: float, nombre: str) -> None:
    if a is not None and abs(float(a) - mentira) < 1e-6:
        raise SystemExit(f"TUMOR {nombre}: cayo en la mentira {mentira}")
    print(f"OK  {nombre} no es {mentira}")


def peldaños() -> None:
    _cerca(paso_del_tonto("verde", "LONG"), 0.005, "verde largo 0.5")
    _cerca(paso_del_tonto("verde", "SHORT"), 0.006, "verde corto 0.6")
    _cerca(paso_del_tonto("amarillo", "LONG"), 0.008, "amarillo largo 0.8")
    _cerca(paso_del_tonto("amarillo", "SHORT"), 0.009, "amarillo corto 0.9")
    _cerca(paso_del_tonto("rojo", "LONG"), 0.012, "rojo largo 1.2")
    _cerca(paso_del_tonto("rojo", "SHORT"), 0.014, "rojo corto 1.4")


def salto_no_es_un_toque() -> None:
    """De 100 a 98.5. Verde (0,5 %) cabe tres peldaños más el de salida.
    Rojo (1,2 %) cabe uno más el de salida. Un solo toque sería mentira.
    """
    verde = Papel("verde", "LONG")
    verde.ver_precio(100)
    verde.ver_precio(98.5)
    if verde.cuentas(400, 98.5)["n"] != 4:
        raise SystemExit(f"TUMOR salto verde conto {len(verde.toques)} {verde.toques}")
    rojo = Papel("rojo", "LONG")
    rojo.ver_precio(100)
    rojo.ver_precio(98.5)
    if rojo.cuentas(400, 98.5)["n"] != 2:
        raise SystemExit(f"TUMOR salto rojo conto {len(rojo.toques)} {rojo.toques}")
    print("OK  el salto se parte en peldaños", verde.toques, rojo.toques)


def ruido_no_cuenta() -> None:
    p = Papel("verde", "LONG")
    p.ver_precio(100)
    p.ver_precio(99.7)
    if len(p.toques) != 1:
        raise SystemExit(f"TUMOR el ruido conto {p.toques}")
    print("OK  un movimiento menor al peldaño no es toque")


def recorrido_con_regreso() -> None:
    """Paso 10 % para poder hacer la cuenta a mano.
    Abre en 100, baja a 90, sube y vende en 99.
    Masa 300, tres toques, 100 dólares cada uno.

    Monedas: 100/100 + 100/90 - 100/99.
    Caja que falta: 100.
    Quiebre: 100 / esa cantidad.
    La recta diría 95. El promedio de los tres precios, 96.333.
    """
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(90)
    p.ver_precio(99)
    if [a for a, _ in p.toques] != ["abrir", "abrir", "reducir"]:
        raise SystemExit(f"TUMOR secuencia {p.toques}")
    precios = [px for _, px in p.toques]
    if abs(precios[0] - 100) > 1e-9 or abs(precios[1] - 90) > 1e-9 or abs(precios[2] - 99) > 1e-9:
        raise SystemExit(f"TUMOR precios {precios}")
    f = p.peaje
    monedas = 100 / 100 + 100 / 90
    caja = 100 * (1 + f) + 100 * (1 + f)
    esperado = (caja / monedas) / (1 - f)
    c = p.cuentas(300, 99)
    _cerca(c["quiebre"], esperado, "quiebre del recorrido")
    resto = (caja - 100 * (1 - f)) / (monedas - 100 / 99) / (1 - f)
    _no_es(c["quiebre"], resto, "la suelta reescribio el cero")
    _no_es(c["quiebre"], 95.0, "quiebre")
    _no_es(c["quiebre"], (100 + 90 + 99) / 3, "quiebre")
    # La masa de Beru aunque ya haya reducido en la vida real.
    c2 = p.cuentas(300, 99)
    if abs(c2["trozo"] - 100) > 1e-9:
        raise SystemExit("TUMOR no partio la masa entre todos los toques")
    print(f"    precios {precios} quiebre {c['quiebre']} dolares_a_99 {c['dolares']}")


def recompra_si_vuelve_a_bajar() -> None:
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(90)
    p.ver_precio(99)
    p.ver_precio(89.1)
    precios = [round(px, 10) for _, px in p.toques]
    if precios != [100, 90, 99, 89.1]:
        raise SystemExit(f"TUMOR recompra {precios}")
    if p.toques[-1][0] != "abrir":
        raise SystemExit("TUMOR al bajar no volvio a comprar")
    print("OK  si vuelve a bajar, compra otra vez", precios)


def subida_no_abre_corto() -> None:
    """Mientras la bolsa vive, subir solo reduce. No nace el corto."""
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(110)
    if p.lado != "LONG":
        raise SystemExit(f"TUMOR volteo con bolsa viva {p.lado}")
    if [a for a, _ in p.toques] != ["abrir", "reducir"]:
        raise SystemExit(f"TUMOR la subida abrio {p.toques}")
    print("OK  mientras hay bolsa, subir solo reduce")


def al_morir_el_siguiente_peldano_nace_corto() -> None:
    """La bolsa muerta no corre el ancla. El siguiente peldaño nace el corto."""
    p = Papel("verde", "LONG")
    p.ver_precio(100)
    px = 100.0
    for _ in range(40):
        px *= 1.0 + p.paso
        antes = p.lado
        p.ver_precio(px)
        if not p._sombra.vivo() and antes == "LONG" and p.lado == "LONG":
            break
    if p.lado != "LONG" or p._sombra.vivo():
        raise SystemExit(f"TUMOR el cierre ya volteo {p.lado} {p._sombra.vivo()}")
    muerte = p.ancla
    siguiente = float(muerte) * (1.0 + p.paso)
    p.ver_precio(siguiente)
    if p.lado != "SHORT":
        raise SystemExit(f"TUMOR no nacio el corto {p.lado}")
    if len(p.toques) != 1 or p.toques[0][0] != "abrir":
        raise SystemExit(f"TUMOR la cuenta vieja siguio {p.toques}")
    if abs(p.toques[0][1] - siguiente) > 1e-6:
        raise SystemExit(f"TUMOR el corto no nacio en el peldaño {p.toques}")
    f = p.peaje
    c = p.cuentas(55.17, siguiente)
    _cerca(c["quiebre"], siguiente * (1.0 - f) / (1.0 + f), "cero del corto nuevo")
    print(f"OK  al morir, el siguiente peldaño nace corto en {siguiente}, cero {c['quiebre']}")


def la_salida_recta_suelta_hasta_cero() -> None:
    """Mismos tres toques. La marca y la salida ya descuentan el peaje.

    Sin peaje la salida era 21,89. Con comisión de abrir y de cerrar, baja.
    """
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(90)
    p.ver_precio(99)
    f = p.peaje
    monedas = 100 / 100 + 100 / 90 - 100 / 99
    caja = 200 * (1 + f) - 100 * (1 - f)
    cero = (caja / monedas) / (1 - f)
    marca = (99 - cero) * monedas
    queda = monedas
    cobrado = 0.0
    px = 99.0
    while queda > 1e-12:
        px *= 1.1
        tomado = min(queda, 100 / px)
        cobrado += tomado * px * (1 - f)
        queda -= tomado
    c = p.cuentas(300, 99)
    _cerca(c["dolares"], marca, "la marca de hoy")
    _cerca(c["salida"], ganancia_de_la_pierna(300), "la promesa de la pierna")
    _no_es(c["salida"], cobrado - caja, "salida")
    _no_es(c["salida"], 21.89, "salida")
    doble = p.cuentas(600, 99)
    _cerca(doble["salida"], ganancia_de_la_pierna(600), "el doble de pierna, doble promesa")
    abajo = p.cuentas(300, 90)
    _cerca(abajo["salida"], c["salida"], "a mitad de camino la pierna no se encoge")
    if abajo["salida"] is None or abajo["quiebre"] is None:
        raise SystemExit(f"TUMOR el camino callo abajo del cero {abajo}")
    if abajo["quiebre"] <= 90:
        raise SystemExit("TUMOR el cero del camino no subio del precio")
    print(f"OK  debajo del golpe el camino habla  cero {abajo['quiebre']} salida {abajo['salida']}")


def masa_que_crece_no_mueve_el_quiebre() -> None:
    """Mismos toques, el doble de masa: el quiebre no cambia. Los dólares sí."""
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(90)
    a = p.cuentas(200, 90)
    b = p.cuentas(400, 90)
    _cerca(a["quiebre"], b["quiebre"], "el doble de masa, mismo quiebre")
    if abs(b["dolares"] - 2 * a["dolares"]) > 1e-6:
        raise SystemExit(f"TUMOR dolares no escalan {a['dolares']} {b['dolares']}")
    print("OK  la masa escala los dolares, no el quiebre")


def vaciar_no_borra_la_entrada() -> None:
    """Sube hasta vaciar y luego compra de nuevo. La entrada no nace en el último precio."""
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(130)
    p.ver_precio(80)
    c = p.cuentas(100, 80)
    if c["entrada"] is None or abs(c["entrada"] - 80) < 1e-6:
        raise SystemExit(f"TUMOR la entrada se receteo {c['entrada']}")
    if c["quiebre"] is not None and abs(c["quiebre"] - c["entrada"]) < 1e-9:
        raise SystemExit("TUMOR la venta no movio el quiebre")
    print(f"OK  vaciar sigue el mismo lado  entrada {c['entrada']} quiebre {c['quiebre']}")
    p.voltear()
    if p.cuentas(100, 80)["n"] != 0:
        raise SystemExit("TUMOR voltear dejo toques")
    print("OK  voltear borra la cuenta del papel")


def diez_y_cinco_no_es_mitad() -> None:
    """Diez toques de un lado y cinco del otro. La masa no se parte a la mitad."""
    largo = Papel("verde", "LONG")
    corto = Papel("verde", "SHORT")
    largo.paso = 0.1
    corto.paso = 0.1
    for px in (100, 90, 99, 89.1, 98.01, 88.209, 97.0299, 87.32691, 96.059601, 86.4536409):
        largo.ver_precio(px)
    for px in (100, 110, 99, 108.9, 98.01):
        corto.ver_precio(px)
    if len(largo.toques) != 10 or len(corto.toques) != 5:
        raise SystemExit(f"TUMOR toques {len(largo.toques)} {len(corto.toques)}")
    masa = 150
    total = 15
    cl = largo.cuentas(masa, 86.45, toques=total)
    cc = corto.cuentas(masa, 98.01, toques=total)
    if abs(cl["trozo"] - 10) > 1e-9 or abs(cc["trozo"] - 10) > 1e-9:
        raise SystemExit(f"TUMOR parte {cl['trozo']} {cc['trozo']}")
    if abs(cl["trozo"] * 10 - 100) > 1e-6 or abs(cc["trozo"] * 5 - 50) > 1e-6:
        raise SystemExit("TUMOR no cayo 10 y 5")
    if abs(cl["trozo"] * 10 - masa / 2) < 1e-6:
        raise SystemExit("TUMOR salio mitad y mitad")
    print("OK  diez largos se quedan cien, cinco cortos cincuenta")


def el_viaje_nuevo_no_hereda() -> None:
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(90)
    p.reiniciar()
    p.ver_precio(80)
    if len(p.toques) != 1 or abs(p.toques[0][1] - 80) > 1e-9:
        raise SystemExit(f"TUMOR herencia {p.toques}")
    f = p.peaje
    c = p.cuentas(50, 80)
    _cerca(c["quiebre"], 80 * (1 + f) / (1 - f), "papel nuevo en el cero de la bolsa")
    _no_es(c["quiebre"], 88.0, "papel nuevo")
    _no_es(c["quiebre"], 80.0, "papel nuevo")
    if c["salida"] is None or c["salida"] <= 0:
        raise SystemExit(f"TUMOR el papel nuevo no dijo la ganancia {c['salida']}")
    print(f"OK  aun debajo del golpe, al vaciar serian {c['salida']}")


def corto_sube_abre_y_baja_cubre() -> None:
    p = Papel("verde", "SHORT")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(110)
    p.ver_precio(99)
    acciones = [a for a, _ in p.toques]
    if acciones != ["abrir", "abrir", "reducir"]:
        raise SystemExit(f"TUMOR corto {p.toques}")
    print("OK  el corto abre al subir y cubre al bajar", [px for _, px in p.toques])


def dos_compras_el_peaje_sube_el_cero() -> None:
    """85 y un peldaño abajo. El cero lleva el peaje, y no salta al peldaño de más.

    El engorde siguiente, otro peldaño más abajo, baja ese cero.
    """
    p = Papel("verde", "LONG")
    p.ver_precio(85)
    bajo = 85 * (1 - p.paso)
    p.ver_precio(bajo)
    f = p.peaje
    sin = 2 / (1 / 85 + 1 / bajo)
    con = sin * (1 + f) / (1 - f)
    siguiente = bajo * (1 + p.paso)
    c = p.cuentas(1600, bajo)
    _cerca(c["quiebre"], con, "cero del paso dos")
    _no_es(c["quiebre"], siguiente, "cero")
    _no_es(c["quiebre"], sin, "cero sin peaje")
    if c["salida"] is None or c["salida"] <= 0:
        raise SystemExit(f"TUMOR el camino no dijo la ganancia {c['salida']}")
    mas = bajo * (1 - p.paso)
    p.ver_precio(mas)
    tres = p.cuentas(1600, mas)
    if tres["quiebre"] is None or tres["quiebre"] >= float(c["quiebre"]) - 0.05:
        raise SystemExit(
            f"TUMOR el engorde no bajo el cero {c['quiebre']} -> {tres['quiebre']}"
        )
    print(
        f"OK  paso 2 en {c['quiebre']}, el engorde lo baja a {tres['quiebre']}"
    )


def el_corto_tambien_camina() -> None:
    """Corto en 100. El cero queda un poco abajo del precio, no en el peldaño lejano."""
    p = Papel("verde", "SHORT")
    p.paso = 0.1
    p.ver_precio(100)
    f = p.peaje
    c = p.cuentas(50, 100)
    _cerca(c["quiebre"], 100 * (1 - f) / (1 + f), "corto, el cero de la bolsa")
    _no_es(c["quiebre"], 90.0, "corto")
    if c["salida"] is None or c["salida"] <= 0:
        raise SystemExit(f"TUMOR el corto no dijo la ganancia {c['salida']}")
    if c["dolares"] >= 0:
        raise SystemExit("TUMOR el corto ya ganaba al soltar ahora")
    print(f"OK  el corto camina y al vaciar serian {c['salida']}")


def la_masa_de_ahora_no_queda_grabada() -> None:
    """El saco de la lámina no vive en el papel.

    Al enganchar, se recorre una vez lo que ya está despierto.
    La masa es la de esa pregunta. Si Beru negocia más, la siguiente
    pregunta dobla la ganancia y no mueve el cero. Preguntar no suma
    toques. Recorrer otra vez el archivo, sí sería tumor.
    """
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.enganchar([100, 90])
    n = len(p.toques)
    try:
        p.enganchar([100, 90])
    except RuntimeError:
        print("OK  el recorrido no se vuelve a andar")
    else:
        raise SystemExit("TUMOR el papel recorrio dos veces el mismo archivo")
    if len(p.toques) != n:
        raise SystemExit(f"TUMOR el segundo archivo sumo toques {p.toques}")
    p.ver_precio(90)
    if len(p.toques) != n:
        raise SystemExit("TUMOR el mismo precio sumo toque")
    chica = p.cuentas(100, 90)
    grande = p.cuentas(200, 90)
    saco = p.cuentas(1600, 90)
    if len(p.toques) != n:
        raise SystemExit("TUMOR preguntar la ganancia sumo toques")
    _cerca(chica["quiebre"], grande["quiebre"], "mas masa, mismo cero")
    if chica["salida"] is None or grande["salida"] is None or saco["salida"] is None:
        raise SystemExit(f"TUMOR sin salida {chica['salida']} {grande['salida']}")
    _cerca(grande["salida"], 2 * chica["salida"], "la masa de ahora dobla la ganancia")
    if abs(float(saco["salida"]) - float(chica["salida"])) < 1e-6:
        raise SystemExit("TUMOR la masa chica salio igual que el saco de la lamina")
    otra = p.cuentas(100, 90)
    _cerca(otra["salida"], float(chica["salida"]), "no se quedo con la masa grande")
    print(f"OK  masa 100 al vaciar {chica['salida']}, masa 200 al vaciar {grande['salida']}")


def el_trozo_fijo_no_se_adelgaza() -> None:
    """Si los escalones máximos ya se saben, el peldaño no se adelgaza.

    Engordar suma esa parte. Partir el saco solo entre los toques de ahora
    sí lo adelgaza, y esa es otra cuenta.
    """
    p = Papel("verde", "LONG")
    p.paso = 0.1
    p.ver_precio(100)
    p.ver_precio(90)
    dos = p.cuentas(290, 90, toques=29)
    p.ver_precio(81)
    tres = p.cuentas(290, 81, toques=29)
    partido = p.cuentas(290, 81)
    _cerca(dos["trozo"], 10.0, "el peldaño vale diez")
    _cerca(tres["trozo"], 10.0, "el peldaño sigue valiendo diez")
    if abs(partido["trozo"] - 10) < 1e-6:
        raise SystemExit("TUMOR partir entre los toques de ahora no adelgazo")
    if tres["salida"] is None or dos["salida"] is None:
        raise SystemExit("TUMOR la pierna no prometio")
    _cerca(tres["salida"], dos["salida"], "el mismo saco no cambia la promesa")
    print(f"OK  el peldaño sigue en 10, la promesa se queda en {tres['salida']}")


def el_ruido_dentro_del_peldano_no_inventa_ganancia() -> None:
    p = Papel("verde", "LONG")
    px = 85.0
    p.ver_precio(px)
    for _ in range(12):
        px *= 1.0 - p.paso
        p.ver_precio(px)
    quieto = p.cuentas(1600, px)
    ruido = px * 1.002
    antes = len(p.toques)
    p.ver_precio(ruido)
    if len(p.toques) != antes:
        raise SystemExit("TUMOR el ruido conto un toque")
    movido = p.cuentas(1600, ruido)
    _cerca(movido["quiebre"], quieto["quiebre"], "el ruido no movio el cero")
    _cerca(movido["salida"], quieto["salida"], "el ruido no movio la ganancia")
    if movido["n"] != quieto["n"]:
        raise SystemExit("TUMOR el ruido cambio los toques de la cuenta")
    print(
        "OK el ruido no mueve el cero "
        + str(quieto["quiebre"])
        + " ni la ganancia "
        + str(quieto["salida"])
    )


def el_polvo_no_cambia_la_ganancia_prometida() -> None:
    p = Papel("verde", "LONG")
    px = 85.0
    paso = p.paso
    precios = [px]
    for _ in range(12):
        px *= 1.0 - paso
        precios.append(px)
    fondo = px
    precios.append(fondo * 1.002)
    for _ in range(9):
        px *= 1.0 + paso
        precios.append(px)
    px *= 1.0 - paso
    precios.append(px)
    for _ in range(7):
        px *= 1.0 + paso
        precios.append(px)
    puerta = None
    sueltas = 0
    polvo = None
    precio_polvo = None
    muerto = None
    for marca in precios:
        antes = len(p.toques)
        p.ver_precio(marca)
        c = p.cuentas(1600, marca, toques=29)
        if not c["vivo"]:
            muerto = c
            break
        if len(p.toques) > antes and p.toques[-1][0] == "abrir":
            puerta = c["quiebre"]
            sueltas = 0
        elif puerta is not None and c["quiebre"] is not None:
            sueltas += 1
            _cerca(c["quiebre"], puerta, "la suelta movio el cero")
        if c["cantidad"] * marca < c["trozo"]:
            polvo = c
            precio_polvo = marca
    if puerta is None or polvo is None or precio_polvo is None or muerto is None or sueltas < 1:
        raise SystemExit("TUMOR no aparecio el polvo")
    _cerca(polvo["quiebre"], puerta, "el polvo arrastro el cero")
    if polvo["montado"] <= 0:
        raise SystemExit("TUMOR el polvo se pinto en cero")
    _cerca(polvo["montado"], polvo["cantidad"] * precio_polvo, "la masa del polvo")
    if muerto["quiebre"] is not None:
        raise SystemExit("TUMOR la bolsa muerta siguio con cero")
    _cerca(muerto["salida"], ganancia_de_la_pierna(1600), "al morir la promesa sigue siendo la pierna")
    _cerca(polvo["salida"], muerto["salida"], "el polvo no cambia la promesa")
    print(
        "OK las sueltas dejan el cero en "
        + str(puerta)
        + " y al morir la marca es "
        + str(muerto["dolares"])
    )


def la_pierna_promete_ochenta_y_seis() -> None:
    """Cien de pierna prometen un dólar, aunque la recta vaya a la mitad.

    Cerrar a mercado, o ir a la mitad, no encoge lo negociado.
    Si la casa volteó, el lado viejo no entra.
    """
    _cerca(ganancia_de_la_pierna(100), 1.0, "cien prometen 1")
    _cerca(ganancia_de_la_pierna(50), 0.5, "cincuenta son la mitad")
    if ganancia_de_la_pierna(0) is not None:
        raise SystemExit("TUMOR una pierna vacia prometio ganancia")
    media = cuenta_de_la_pierna([(-10.0, 100.0), (5.0, 50.0)], "SHORT")
    _cerca(media["pierna"], 100.0, "cerrar a la mitad no encoge el corto")
    _cerca(media["cerrada"], 50.0, "lo cerrado se anota aparte")
    _cerca(ganancia_de_la_pierna(media["pierna"]), 1.0, "la mitad sigue en 1")
    crece = cuenta_de_la_pierna(
        [(-10.0, 100.0), (5.0, 50.0), (-3.0, 30.0)],
        "SHORT",
    )
    _cerca(crece["pierna"], 130.0, "un engorde nuevo si suma")
    _cerca(ganancia_de_la_pierna(crece["pierna"]), 1.30, "ciento treinta prometen 1,30")
    volteo = [(-10.0, 100.0), (15.0, 150.0)]
    largo = cuenta_de_la_pierna(volteo, "LONG")
    corto = cuenta_de_la_pierna(volteo, "SHORT")
    _cerca(largo["pierna"], 50.0, "al voltear solo queda el largo nuevo")
    _cerca(corto["pierna"], 100.0, "el corto viejo no se mezcla con el largo")
    print("OK  la pierna vacia no promete")


def main() -> None:
    la_pierna_promete_ochenta_y_seis()
    peldaños()
    salto_no_es_un_toque()
    ruido_no_cuenta()
    recorrido_con_regreso()
    la_salida_recta_suelta_hasta_cero()
    vaciar_no_borra_la_entrada()
    diez_y_cinco_no_es_mitad()
    recompra_si_vuelve_a_bajar()
    subida_no_abre_corto()
    al_morir_el_siguiente_peldano_nace_corto()
    masa_que_crece_no_mueve_el_quiebre()
    la_masa_de_ahora_no_queda_grabada()
    el_trozo_fijo_no_se_adelgaza()
    el_viaje_nuevo_no_hereda()
    dos_compras_el_peaje_sube_el_cero()
    el_corto_tambien_camina()
    corto_sube_abre_y_baja_cubre()
    el_ruido_dentro_del_peldano_no_inventa_ganancia()
    el_polvo_no_cambia_la_ganancia_prometida()
    print("PASO_2_REVISADO")


if __name__ == "__main__":
    main()
