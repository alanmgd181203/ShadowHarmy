# Beru de papel — ficha para auditoría

Documento de lo que el código hace hoy. No es doctrina nueva y no entra en vigor.
El cazador vivo no lee estos archivos.

Lo que se hizo en las revisiones: se midió el código y se escribió aquí.
No se cambió `papel.py` ni `viaje.py`. No se reescribió el encabezado.
No se bloqueó ninguna llamada. No se borró ninguna función.
Las pruebas se volvieron a correr y siguen pasando.

---

## Mandato al auditor

Busca tumores solo en la sección «Terreno sin caminar».

Un tumor es una de estas dos cosas:

- el código contradice una regla ya cerrada en este documento
- un número de la sección «Números cerrados» no se reproduce al correr el código

No es tumor:

- proponer otro diseño
- repetir un punto de la sección «Cerrado»
- pedir un corte que este documento ya midió y rechazó
- el encabezado viejo, el código que nadie llama, o la diferencia entre
  este cero y la pantalla de la casa: ya están explicados

Fuera de este pergamino, no auditar aquí: Iron, el escudo, el Beru que
caza, Igris, el peaje del cazador vivo, el spread. Si aparecen, no son
de este libro.

Fuente de verdad:

- `cirugias/hiron/papel.py` — el bot tonto. Camina precios y responde la cuenta.
- `cirugias/hiron/viaje.py` — la bolsa (caja, monedas, entrada, cero de un golpe).
- `cirugias/sala_por_color/sala.py` — el tamaño del peldaño (red menos Oz).
- `cirugias/hiron/probar_papel.py` — `python -m cirugias.hiron.probar_papel`
  termina en `PASO_2_REVISADO`.
- `cirugias/hiron/probar_camino.py` — `python -m cirugias.hiron.probar_camino`
  termina en `PASO_7_REVISADO`. Esta segunda prueba incluye a Iron. El
  `96.5` de ahí es otra bolsa, con peaje 0. No es el cero del papel.

El dibujo `suelo-masacre-laboratorio.canvas.tsx` es una impresión. Si un
número del dibujo no sale de `Papel.ver_precio` más `Papel.cuentas`, el
dibujo miente. El código manda.

---

## Cerrado — no volver a auditar

Cada punto ya se midió o ya es la regla vigente. No pedir de nuevo el corte.

1. Sombra y bolsa de dólares. La sombra mete `1 / precio` monedas, un
   dólar de bruto por toque. La bolsa impresa mete `trozo / precio`.
   Con el trozo constante, es la misma forma por una constante. Mueren
   en el mismo toque. Laboratorio verde: 0 pasos con vida distinta.
   Otros 40 caminos: 0 vidas distintas. No sincronizar la sombra con el
   divisor. La masa se pregunta después y no hace falta.

2. Al morir, la ganancia se lee en ese peldaño, todavía en el lado viejo.
   El peldaño que vacía no voltea. El siguiente sí, y borra la cuenta a
   propósito. El lado nuevo nace limpio. No colgar la ganancia vieja
   dentro de la cuenta nueva. Medido: subiendo de a un peldaño desde el
   fondo, en `85.82637290360492` el lado sigue largo y la marca es
   `2.812649864108616`. Ese camino no trae el retroceso, por eso no es
   el 3,03 del laboratorio completo. Un solo precio que ya está en el
   nacimiento borra esa marca y deja el corto: `n = 1`, cero
   `86.16067586877264`, marca `-0.06065629421059627`. Eso es el salto
   que se come dos peldaños, no un olvido del peldaño de la muerte.

3. El primer peldaño del lado nuevo es el precio que el mercado ya tocó,
   medido con el paso del lado que se estaba soltando. En verde largo
   eso es 0,5 %, no el 0,6 % del corto. Medirlo con el paso nuevo lo
   haría nacer tarde. Los peldaños siguientes sí usan el paso nuevo.
   No cambiar ese primer precio.

4. El ancla de ahora, usada al revivir toques viejos, no mueve la puerta
   impresa. Se comparó el cero de hoy con uno que arranca cada toque en
   su propio precio. Caso 100/90/99: los dos `94.84110997890947`.
   Laboratorio ya en corto: los dos `86.15852185187589`. Oscilación de
   trece toques: los dos `98.89425058259948`. Cacería de pasos 0,5 %,
   0,6 %, 1 % y 10 %, sesenta caminos: puertas movidas, 0.

5. Una suelta que todavía no está en tablas sí vuelve a llamar a
   `_camino`. Esa llamada no se bloquea. Bloquearla baja el cero en la
   primera suelta del laboratorio, de `83.71473050383746` a
   `83.17181073785694`, en el precio `80.4381`. En el fondo, los dos
   coinciden. En el peldaño siguiente el corte vuelve a coincidir.
   Esa llamada retoma la recta del último engorde para que la suelta no
   deje otro cero. En 564 pasos de otros caminos la diferencia pasó de
   una millonésima. La peor fue 0,70. No pedir otra vez ese bloqueo.

6. `montado` del polvo es monedas por el precio de ahora, a propósito,
   para que el último resto no se imprima en cero. En el laboratorio es
   `3.8614414420640206`. No entra al cero, ni a la ganancia de vaciar,
   ni al volteo. No pedir que el polvo se valore solo al costo.

7. Líneas 11 y 12 de `papel.py` describen el cero de un golpe. La puerta
   vigente es la sección «La puerta». El manual miente en esas dos
   líneas. Las líneas 7 a 10 sí describen la recta. Reescribir el
   encabezado no mueve números y no se hizo. No es un tumor del reloj.

8. `_salida_recta` no la llama `cuentas` ni nadie más. La prueba
   `la_salida_recta_suelta_hasta_cero` usa `cuentas`. Borrarla no cambia
   el reloj y no se hizo. No es condición para Iron.

9. `_copia` solo copia lado, peaje, cantidad y caja. `_camino` y
   `_cobro` no leen la entrada ni la masa negociada de esa copia. Les
   basta la caja y las monedas para el cero de un golpe y para el cobro.
   No es una bolsa incompleta.

10. El cero impreso no es la pantalla de Bybit ni de OKX. Si la casa
    llenó las mismas órdenes a los mismos precios y cobró 0,055 % al
    abrir y al cerrar, coinciden las monedas, la caja, la entrada y el
    cero de un golpe. El cero que el papel imprime es la puerta de la
    recta. La casa muestra el de un golpe, que sí baja al vender caro.
    No hay deslizamiento, ni orden mínima, ni hacedor, ni coste de dejar
    la bolsa abierta. OKX, en su tarifa pública de entrada, no cobra
    exactamente 0,055 %. El papel usa el tomador lineal que el ejército
    ya tiene, el de Bybit. En el papel es la fracción `0.00055`. En el
    altar vivo el mismo número es `ANCLA_FEE_LINEAR_TAKER_PCT = 0.055`,
    en puntos porcentuales. No es el 0,10 % del spot. No es un spread.

11. Iron no lee la puerta del papel. Lee la ganancia de vaciar (`salida`)
    y una bolsa aparte con peaje 0, cuyo cero de mano en la prueba es
    `96.5`. La masacre de esa prueba, con la salida del papel, es
    `106.78753123750002`. Iron no reescribe el cero del papel. El papel
    no entra en vigor. `core/` no importa `cirugias.hiron`.

12. El ruido dentro de un peldaño no es toque y no mueve el cero ni la
    ganancia. Doblar la masa no mueve el cero si todos los toques pesan
    igual. Pedir otra masa no deja grabada la anterior. Recorrer el
    archivo dos veces desde el origen truena. Vaciar no recetea el mismo
    lado. Voltear sí borra. Mientras la bolsa vive, subir solo reduce.
    Diez toques y cinco no es mitad y mitad.

---

## Qué es

El Beru de papel no caza, no manda órdenes y no es un segundo proceso.
Es un libro. Recibe precios ya vistos y, cuando se le pregunta, responde
cero, masa, monedas y la ganancia de vaciar en línea recta.

Peaje del papel: `PEAJE = 0.00055` (0,055 % por lado). Un `Viaje` recién
creado trae peaje 0. El papel se lo pone. No mezclar las dos bolsas.

---

## Peldaño

`paso_del_tonto(color, lado) = red_pct(color, lado) - oz_pct(color)`.

La Oz de las tres salas es 0,2 % (`0.002`). El peldaño del tonto es la
red menos esa Oz. No es el vacío, ni la sangre, ni el estirón.

| Sala | Largo | Corto |
| --- | --- | --- |
| verde | 0,5 % = 0,007 − 0,002 | 0,6 % = 0,008 − 0,002 |
| amarillo | 0,8 % = 0,010 − 0,002 | 0,9 % = 0,011 − 0,002 |
| rojo | 1,2 % = 0,014 − 0,002 | 1,4 % = 0,016 − 0,002 |

Si el resultado no está entre 0 y 1, la función truena. Color desconocido
cae en amarillo. Al nacer el otro lado, el peldaño se mide otra vez.
Verde largo que nace corto pasa de 0,5 % a 0,6 %.

Los valores los afirma la prueba `peldaños`: 0,005, 0,006, 0,008, 0,009,
0,012, 0,014.

---

## Variables

`Papel` guarda:

- `color`, `lado` (`LONG` o `SHORT`), `paso`, `peaje`
- `ancla`: precio del último toque de verdad. `None` si no hay toque.
- `toques`: lista de `("abrir", precio)` o `("reducir", precio)`. Solo peldaños enteros.
- `_sombra`: un `Viaje` con `1 / precio` monedas por toque. Decide si el paso sigue vivo. No es la bolsa que se imprime.

`Viaje`, la bolsa que `cuentas` arma desde cero en cada pregunta:

- `cantidad`: monedas abiertas. Si no pasa de `1e-9`, está muerta.
- `caja`: largo, costo que falta cobrar. Si al morir es negativa, eso es ganancia neta.
- `masa_negociada`: suma de los brutos de las compras. Las ventas no la bajan. El papel casi no la usa para el cero.
- `monedas_entrada`, `costo_entrada`: solo las compras. Entrada = `costo_entrada / monedas_entrada`. Las ventas no la mueven.
- `peaje`: en el papel, 0,00055.

`_morir` pone `cantidad` en 0. No borra caja, masa ni entrada.
`Viaje.voltear` borra todo eso y no borra el peaje.
`Papel.voltear` cambia de lado, vuelve a medir el paso y llama a `reiniciar`.
`Papel.reiniciar` borra ancla, toques y sombra, y se queda en el mismo lado.
Preguntar `cuentas` no anota toques y no abre órdenes.

---

## Cómo un precio se vuelve toque

`ver_precio(precio)`:

1. Precio ≤ 0: no hace nada.
2. Si no hay ancla: ese precio es el primer `abrir`.
3. Largo, el precio baja un peldaño entero o más: `abrir` en cada peldaño. Un salto son varios toques.
4. Largo, el precio sube un peldaño entero o más: `reducir` en cada peldaño, mientras `_sombra` viva.
5. Movimiento menor que un peldaño: no es toque. La ancla no se mueve.
6. Si `_sombra` ya no vive y el precio alcanza el siguiente peldaño en la dirección de soltar, ese peldaño no se anota como otra suelta. `voltear` y ese precio es el primer `abrir` del otro lado. El peldaño que vació la bolsa no es el nacimiento. El nacimiento es el siguiente.
7. Si la bolsa ya murió y el precio vuelve hacia el engorde del mismo lado, eso es `abrir` en la cuenta que todavía está. No voltea.

Corto, al revés: abrir es subir, soltar es bajar.

`enganchar(precios)` recorre una lista una sola vez. Si ya hay ancla o toques, truena (`papel: el recorrido ya está andado`). Tope de 8000 peldaños en un solo precio. Si pasa, truena.

Después de `voltear`, el bucle exterior vuelve a mirar el mismo precio.
Los peldaños que falten de ese salto se cuentan con el paso nuevo.

Los precios del toque no son la marca ruidosa. Son el peldaño exacto
desde el ancla: `_precio_abre` y `_precio_descarga`. La tolerancia para
dar el peldaño por alcanzado es `ancla × 1e-9`.

---

## Matemática de la bolsa

Cada toque de la bolsa impresa: monedas = `trozo / precio`. Bruto = `trozo`.

Abrir, largo:

- `cantidad += monedas`
- `caja += bruto × (1 + peaje)`
- la entrada acumula lo mismo
- `masa_negociada += bruto`, sin peaje

Abrir, corto: `caja += bruto × (1 - peaje)`. El resto, en espejo.

Soltar, largo: se toma `min(pedido, cantidad)`. El sobrante no voltea el lado.

- `caja -= bruto × (1 - peaje)`
- si las monedas caen a ≤ `1e-9`, cantidad queda en 0 y la caja sigue

Soltar, corto: `caja -= bruto × (1 + peaje)`.

Cero de un golpe (`Viaje.quiebre`), si hay monedas:

- base = `caja / cantidad`
- largo: `base / (1 - peaje)`
- corto: `base / (1 + peaje)`
- sin peaje: el cero es la base

Este cero sí se mueve con cada venta. Vender debajo del costo lo empuja
hacia arriba. Vender por encima lo baja, porque esa ganancia ya salió de
la caja. No es el número que el papel imprime como `quiebre`.

---

## La puerta

`cuentas(masa, marca, toques)` parte la masa y reconstruye un `Viaje`
con los toques, en orden. Lleva una `puerta`.

- Cada `abrir` recalcula la puerta con `_camino`.
- Cada `reducir` cuyo precio ya está en tablas respecto de la puerta no recalcula. Esa suelta ya estaba en la recta. Si mata la bolsa, la puerta pasa a `None`.
- Cada `reducir` que todavía no está en tablas sí recalcula. Es la llamada que no se bloquea: sin ella, la primera suelta del laboratorio mueve el cero hacia abajo. Ver el punto 5 de «Cerrado».
- Lo que se devuelve como `quiebre` es esa puerta si la bolsa vive. Si murió, `None`. No es el `Viaje.quiebre()` del resto.

En tablas, largo: `precio + 1e-12 >= puerta`. Corto: `precio - 1e-12 <= puerta`.

Solo un engorde nuevo tiene permiso de dejar otra puerta. Una suelta no
la sube ni la baja. El polvo no la arrastra. Al morir, el cero calla.

La ganancia al vaciar (`salida`) es otra cuenta. Son los dólares de
soltar lo que sigue montado, peldaño a peldaño, neto de la comisión de
cada suelta. Se recalcula al final con la bolsa real. No se congela con
la puerta.

La marca de hoy (`dolares`), si la bolsa vive, usa el cero de un golpe,
no la puerta: largo `(marca - golpe) × monedas`, corto al revés. No
alimenta el suelo de la masacre.

Si la bolsa ya murió: `dolares = -caja` en largo, `caja` en corto. Es la
ganancia neta, no cobrado bruto menos pagado bruto.

---

## Cómo `_camino` arma la puerta

Copia cantidad, caja y peaje. Empieza en `_arranque(marca)`:

- si la marca está estrictamente entre `ancla×(1−paso)` y `ancla×(1+paso)`, el camino sale del ancla
- un ruido dentro del peldaño no inventa otra escalera
- si la marca ya está fuera de ese peldaño, el camino sale de la marca
- el peldaño inmediatamente anterior cabe dentro de esa banda
- dos peldaños atrás, con un paso chico, ya no caben

Luego, hasta 8000 veces:

1. Si la copia murió o no tiene cero, no hay respuesta.
2. El siguiente peldaño es `precio × (1+paso)` en largo, `× (1−paso)` en corto.
3. Si el precio de ahora ya está en tablas, o el siguiente peldaño ya las pasaría, la puerta es el cero de un golpe de lo que sigue en esa copia. No se estampa el peldaño que se pasa. Un engorde más barato puede bajar la puerta. La ganancia es `_cobro` desde aquí. Si esa ganancia no pasa de `1e-9`, la puerta se devuelve y la ganancia calla (`None`).
4. Si el siguiente peldaño todavía no alcanza el cero, se suelta un trozo ahí. Esa venta, bajo el costo, empuja el cero. Se sigue.
5. Si esa suelta vacía la bolsa, `_vacio_en_tablas`: la puerta es ese precio, no el cero de un golpe, y la ganancia es lo que sobró en la caja (largo, `−caja` si es positivo). Si esa ganancia no pasa de `1e-9`, no hay respuesta.

`_cobro` no vende en el precio actual. El primer tramo es el siguiente.
Cada suelta cobra el bruto por `(1 − peaje)` en largo, o por `(1 + peaje)` en corto.
Ganancia largo: cobrado − caja. Corto: caja − cobrado.
La caja que se resta ya trae la comisión de abrir y la de lo ya cerrado.
La de cerrar cada tramo futuro se descuenta en el cobro. No se cobra dos
veces el mismo tramo. Si no logra vaciar en 8000 peldaños, no hay ganancia.

---

## Masa

La masa no se guarda. Cada pregunta trae la masa de ahora.

`trozo = masa / divisor`.

- Si no se pasa `toques`, el divisor es cuántos toques ya existen.
- Si se pasa `toques`, ese número es el divisor, aunque hayan ocurrido menos. Diez largos y cinco cortos no es mitad: el largo se queda diez partes y el corto cinco, si el total es quince.
- Doblar la masa no mueve el cero. Dobla los dólares.
- Si el camino ya conoce la masa máxima y los escalones máximos, el llamador pasa ese total desde el primer dibujo. El trozo no se adelgaza. En el laboratorio verde eso es 1600 / 29.
- Si los escalones futuros no se conocen, se parte la masa de ahora entre los toques ya andados. Poner el saco entero en el primer peldaño es un error del llamador, no del papel.

`montado`:

- `trozo × (compras − ventas)`, y no baja de 0
- si la bolsa vive, ese entero da 0, y todavía quedan monedas, `montado = monedas × marca`
- si no hay bolsa, 0

---

## Qué devuelve `cuentas`

- `n`: toques de este lado
- `trozo`: dólares de cada peldaño en esta pregunta
- `montado`: masa sentada
- `quiebre`: la puerta. `None` si no hay bolsa
- `entrada`: promedio de las compras, con su comisión. Sobrevive a la bolsa vacía dentro de la misma cuenta. Al `voltear`, los toques se borran y la entrada nueva es la del otro lado
- `cantidad`: monedas abiertas, o 0
- `dolares`: marca de hoy
- `salida`: ganancia de vaciar en recta, o `None`
- `vivo`: si quedan monedas

---

## Nacimiento del otro lado

Las tres juntas:

1. `_sombra` ya no vive
2. el precio alcanzó el siguiente peldaño en la dirección de soltar
3. ese peldaño es el siguiente al que vació, no el mismo

Entonces el lado cambia, el paso se mide otra vez, la cuenta nace vacía,
y ese peldaño es `abrir`.

Cero del corto nuevo, una sola compra: `precio × (1 − peaje) / (1 + peaje)`.
Prueba: ancla `101.50751249999996`, cero `101.39591561453696`.

---

## Números cerrados

Peaje `f = 0.00055`. Si uno de estos no sale, eso sí es tumor. No
reinterpretar el número.

Una compra larga a 80: `80 × (1+f) / (1−f) = 80.08804842663467`.
No es 80 ni 88. Prueba `el_viaje_nuevo_no_hereda`.

Dos compras del mismo dólar, 85 y `85×(1−0,005)`: cero
`84.88028440705047`. La tercera lo baja a `84.71462024925312`.
El promedio sin peaje `84.78696741854637` no es el del papel.
Prueba `dos_compras_el_peaje_sube_el_cero`.

Corto a 100, paso 0,1: `100 × (1−f) / (1+f) = 99.89006046674328`.
No es 90. Prueba `el_corto_tambien_camina`.

Camino 100, 90, 99, paso 0,1, masa 300. Puerta
`94.84110997890947`. No es el de un golpe después de vender en 99
(`91.02561454671631`), ni 95, ni el promedio de los tres precios.
Marca en 99: `8.77987893341337`. Salida: `21.657960500000016`.
El doble de masa dobla la salida y no mueve el cero.

Laboratorio del polvo. Verde, arranque 85, paso 0,5 %, masa 1600,
divisor 29. Doce bajadas, un ruido `fondo × 1,002` que no mueve el
ancla, nueve subidas, un retroceso de un peldaño, siete subidas.
El cero de las sueltas de la subida se queda en
`83.71473050383746`. El engorde del retroceso lo baja a
`83.64883462675824`. El polvo no lo arrastra. La masa del polvo es
`3.8614414420640206`. Al morir, el cero calla y la marca es
`3.028959065103328`, igual a la salida del polvo.
Prueba `el_polvo_no_cambia_la_ganancia_prometida`.

Otro número de otra pregunta, no del laboratorio. Si se pregunta masa
1600 sin el divisor 29, la ganancia del ruido es
`6.274372773780101` y el cero `83.71473050383757`. Ese 6,27 no es la
ganancia del saco de 29 peldaños. La prueba solo afirma que el ruido
no cambia esos dos. La diferencia de una cienmilmillonésima entre
`…3757` y `…3746` cabe en la tolerancia `1e-6` de las pruebas. No es
un cero que se mueva.

En `probar_camino`, el cero del papel de 100/90/99 es
`94.84110997890946`. El `96.5` es la bolsa a mano, peaje 0.

---

## Terreno sin caminar

Solo aquí. Cada punto dice qué mirar y qué contaría como tumor.
Si el resultado cabe en la regla ya cerrada, no es tumor.

1. Engorde del mismo lado después de sueltas que ya ganaron. El
   laboratorio, después de esas sueltas, muere y el siguiente peldaño
   nace el corto. No hay un engorde nuevo en la misma cuenta. La regla
   dice que ese engorde sí recalcula, con la bolsa que esas sueltas ya
   aligeraron. Tumor sería que ese cero nuevo se desplome como el polvo
   viejo, hacia un número absurdo de lo poco que queda, en vez de ser
   la recta de la bolsa que sigue más la compra nueva. Reportar el cero
   de antes, el de después, las monedas y la caja. No pedir bloquear
   `_camino` en las sueltas: eso ya se midió y mueve mal el cero.

2. El espejo corto del laboratorio entero. Hay pruebas cortas de un
   precio, no el recorrido: arranque, varias subidas que abren, bajadas
   que sueltan debajo de la puerta, un engorde, polvo, muerte, y el
   siguiente peldaño naciendo largo. Tumor sería que una suelta mueva
   la puerta, que el polvo la arrastre, que al morir el cero no calle,
   o que la marca muerta no sea la caja neta. El primer peldaño del
   largo nuevo debe ser el paso del corto, no el del largo.

3. Un solo precio que pasa la muerte y sigue varios peldaños más allá.
   Ya se midió el salto que cae justo en el nacimiento, y la ganancia
   vieja no queda en la cuenta nueva. No reabrir eso. Lo que no se
   contó es cuántos `abrir` deja ese salto largo, a qué precios, y con
   qué paso. Tumor sería que, después del primer `abrir`, los siguientes
   de ese mismo precio sigan usando el paso del lado que murió.

4. `_vacio_en_tablas`. Si una suelta hipotética vacía la bolsa antes del
   cero de un golpe, la puerta que devuelve es el precio de ese peldaño,
   no el cero de un golpe. Buscar si una bolsa que todavía vive imprime
   ese peldaño lejano como `quiebre`, y si una suelta posterior, sin
   engorde nuevo, lo deja clavado lejos del cero de comisión. Tumor
   sería ese salto del cero impreso sin un `abrir` nuevo. Si solo
   aparece dentro de la copia de `_camino` y el `quiebre` impreso no
   cambia, no es tumor.

5. La ganancia que no pasa de `1e-9`. `_camino` puede devolver la puerta
   y callar la ganancia. Buscar si una bolsa gorda, en un recorrido
   normal de peldaños, llega a mostrar `quiebre` y `salida` en `None`
   a la vez. Tumor sería ese silencio con una ganancia que un humano
   vería. Si solo aparece cuando la ganancia es polvo de verdad, no es
   tumor.

No ampliar esta lista con puntos de «Cerrado». No proponer otro peaje,
otro peldaño, ni otra puerta.
