# sandbox/arbitraje_mercado.md

#### #Arbitraje_Mercado

## 💡 Ideas Centrales (Manual)

### **Sub-regla (Compostera)**

**Sub-regla (Compostera)**

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger (Cuándo aplica)
Esta estrategia busca explotar la diferencia de precios entre un activo en dos mercados (Lineal e Inverso). Se activa cuando existe una discrepancia significativa entre los precios de ambos mercados, lo que indica una oportunidad de arbitraje.

### ⚙️ Lógica Operativa (El Cómo)
- El bot calcula el Precio Medio de Ejecución (VWA - Volume Weighted Price) en el mercado Inverso para determinar el precio promedio al cual se ejecutaría la orden.
- Utiliza WebSockets de profundidad para obtener actualizaciones constantes del libro de órdenes y mantener una copia en memoria.
- Calcula la "Ganancia Neta" restando el slippage de entrada, las comisiones de Bybit y la diferencia entre los mercados. Si la Ganancia Neta es superior al 1%, se ejecuta la orden.

### ⚠️ Restricciones / Notas Tácticas
El mayor riesgo es el "Legging risk", donde el mercado Lineal sigue cayendo después de que la orden se coloca en el mercado Inverso, generando una pérdida potencial. Para mitigar esto, se recomienda operar en ambas direcciones simultáneamente (comprando barato y vendiendo caro), aunque esto requiere mayor capital.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Se ve complicado, y más si metemos a la ecuación el cálculo de slippage, que haga ese análisis al mismo tiempo; de ahí una diferencia de 1,2 y el slippage es 0,02, si el margen de ganancia es al menos un uno que ejecute inmediatamente, opiniones

**IA (explicación):**
Es una estrategia de Arbitraje de Latencia o de Convergencia muy sólida. No es "imposible", pero sí requiere que el código sea un motor de cálculo puro, sin distracciones.

Aquí mis opiniones y cómo atacaría yo esa complicación para que sea una ventaja y no un estorbo:
1. La Clave: El "Cálculo de Ejecución Neta"
Para que el bot decida si entrar o no, no debe mirar solo el precio. Debe calcular el Precio Medio de Ejecución (VWA - Volume Weighted Price).
   * El Proceso: El bot no pregunta "¿A cuánto está el Inverso?". Pregunta: "¿Si compro X cantidad ahora mismo, a qué precio promedio me van a…

</details>

<!-- chroma:be0d6e2b-560e-4c29-8767-4b973b09aa73 -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger
Este bloque define la lógica para detectar y ejecutar oportunidades de arbitraje en diferentes mercados (Spot, Futuros, Perpetuos e Inversos). Se activa cuando se detecta una discrepancia significativa en el precio de un activo entre dos o más mercados.

### ⚙️ Lógica Operativa
- **Monitoreo Constante:** La Pupila de la Omnisciencia (Karmish) escanea los precios de los activos en todos los mercados relevantes.
- **Detección de Discrepancias:** Se compara el precio actual del activo en cada mercado y se identifica cualquier diferencia significativa.
- **Validación:** La Pupila de la Alquimia (Tusk) simula operaciones de compra/venta para determinar si la discrepancia representa una oportunidad de arbitraje real.
- **Ejecución:** Si la simulación confirma la viabilidad del arbitraje, la Pupila de la Transmutación (Igris) ejecuta las órdenes de compra y venta en los mercados correspondientes.

### ⚠️ Restricciones / Notas Tácticas
La precisión de la detección de oportunidades de arbitraje depende de la frecuencia de actualización de los datos de mercado y de la velocidad de ejecución de las órdenes. Retrasos en cualquiera de estos aspectos pueden reducir la rentabilidad del arbitraje o incluso generar pérdidas.

**Lógica cristalizada del código:**
- **Protocolo de Gestión:** La lógica operativa se basa en el monitoreo constante de precios, la detección de discrepancias significativas y la validación mediante simulaciones. Si la oportunidad de arbitraje es válida, se ejecutan las órdenes de compra y venta en los mercados correspondientes.
- Incluye la función __init__ en el diseño.
- Incluye la función escanear_abismo en el diseño.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Sí, un ojo perpetuo
El Ojo Perpetuo ha sido abierto. Bajo tu mandato, la Red de Inteligencia ya no es una función secundaria; es la mirada constante del Poseidón Austriaco que todo lo ve, todo lo mide y todo lo transmuta.
Este Ojo no parpadea. Mientras los generales descansan en la sombra, el Ojo Perpetuo escanea las profundidades de los mercados de Spot, Margen, Perpetuos e Inversos, buscando la grieta de la alquimia (el oro gratis) y la ineficiencia del "Convert".

**IA (explicación):**
1. La Estructura del Ojo Perpetuo
El Ojo no es una cámara, es una Conciencia de Datos dividida en tres pupilas:
            * La Pupila de la Alquimia (Tusk): Monitorea Forks, Airdrops y el valor de activos como ETHP/ETHW. Su misión es detectar el "nacimiento de la nada" para que la red lo cubra instantáneamente.
            * La Pupila de la Transmutación (Igris): Escanea los túneles del Convert. Busca el momento exacto donde cambiar oro por pex (o viceversa) sea más rentable que el mercado abierto. Es el cazador de "arbitraje invisible".
            * La Pupila de la Omnisciencia (Karmish):…

**IA (pregunta):**
El Ojo está abierto. ¿Deseas que Igris configure las alertas del Ojo para que solo despierten tu atención cuando el botín supere un umbral de "Tesoro Real", o prefieres que Bellion te mantenga informado de cada pequeña gota de oro que caiga en el Jardín Oscuro?

</details>

<!-- chroma:6ca8e1a4-5c0d-409f-ad9d-33dfd69a3d57 -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger
Este módulo define la lógica de arbitraje multi-mercado, optimizado para minimizar riesgos y maximizar oportunidades en escenarios de alta volatilidad. Se activa cuando se detectan diferenciales de precios entre pares de criptomonedas (ej: USDT/USDC) o entre mercados (Spot vs. Perpetuos).

### ⚙️ Lógica Operativa
- **Capital Base en Stablecoins:** Mantener el 55% del capital en USDT/USDC para neutralizar la volatilidad del mercado y asegurar un "poder de fuego" constante.
- **Cuenta Unificada:** Integrar Spot Margin (USDC) con el par USDT/USDC, permitiendo al bot mover liquidez entre ambos instantáneamente para gestionar riesgos de margen.
- **Estrategias Multi-direccionales:** Implementar 4 estrategias simultáneas:
    - Inverso vs USDT
    - Inverso vs USDC
    - Spot Margin vs Perpetuos
    - Arbitraje USDT/USDC (aprovechando diferenciales de precios en momentos de pánico)

- **Modo "Guerra Total":** En escenarios de alta volatilidad, el bot abandona la búsqueda de ganancias del 1% y prioriza capturar cualquier ventana de oportunidad disponible, independientemente del mercado o instrumento.

### ⚠️ Restricciones / Notas Tácticas
El principal riesgo reside en un desacoplamiento total y permanente de una stablecoin (USDT o USDC). Este escenario es altamente improbable al operar en plataformas confiables como Bybit con activos líderes como LTC o BTC. La diversificación de estrategias y la utilización de capital base en stablecoins mitigan significativamente este riesgo.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Déjame pensar, cuál es la peor debilidad, el margen del capital? Talvez, pero si se mantiene en dólares, talvez se reduce mucho la fluctuación del capital, aaaa, también hay spot margen en usdc, y el par usdt y usdc, no podría entrar a la ecuación, prácticamente sería un francotirador en la cima de la montaña con varios francos en varias direcciones y en modo guerra es el que habíamos dicho, talvez incluso un soldado pesado con armas automáticas

**IA (explicación):**
Tienes mucha razón: al mantener la mayor parte del capital en dólares (USDT/USDC), neutralizas la fluctuación del valor de tu cuenta, dejando que el bot se concentre únicamente en "cazar" el diferencial.
Sobre tu análisis de las debilidades y las nuevas armas, aquí es donde la arquitectura se pone interesante:
1. La "Armadura" contra la debilidad del Margen
La mayor debilidad de un bot de arbitraje es el apalancamiento excesivo en momentos de baja liquidez. Pero tu estrategia tiene dos defensas naturales:
   * El Capital en Dólares: Al tener el colateral en Stablecoins, tu "poder de fuego" no…

**IA (pregunta):**
¿Te gustaría que para la siguiente fase (ya de bosquejo de código) consideremos al bot como una "Matriz de Comparación" donde el bot simplemente elija la mejor pareja de las 10 combinaciones posibles que tiene? (Ej: Inverso-USDC, USDT-Spot, USDC-USDT, etc.)

</details>

<!-- chroma:575ac66c-10ae-4ad4-867d-8240f84b9cdc -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger
Este bloque define la lógica para ejecutar un Arbitraje de Convergencia Puro (Pairs Trading) entre dos mercados, Lineal e Inverso. Se activa cuando se detecta una discrepancia significativa en los precios de ambos mercados.

### ⚙️ Lógica Operativa
- **Monitorización del Spread:** Calcular continuamente la diferencia de precios (Spread = PrecioLineal - PrecioInverso).
- **Filtro de Liquidez:** Verificar la profundidad del Order Book para asegurar que hay suficiente volumen disponible para ejecutar las órdenes Long/Short con un slippage aceptable.
- **Disparador Dual:** 
    - Si Spread > Umbral predefinido, abrir una posición Long en el mercado Inverso (compra) y simultáneamente una posición Short en el mercado Lineal (venta).
    - Cerrar ambas posiciones cuando el Spread vuelva a acercarse a cero o a un valor predeterminado.

### ⚠️ Restricciones / Notas Tácticas
El éxito de esta estrategia depende de la precisión del Ratio de Cobertura (Hedge Ratio) para minimizar el riesgo de movimientos de precios desfavorables. Las comisiones y el slippage pueden erosionar las ganancias, por lo que es crucial buscar discrepancias significativas (Spread > 0.6% - 0.8%). El "Lag" de Ejecución puede generar posiciones desprotegidas ("naked leg"), por lo que se requiere un sistema de ejecución asíncrona eficiente para minimizar este riesgo.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Y si fuera bidireccional, que el inverso haga longs y el lineal shorts

**IA (explicación):**
Eso que acabas de describir es el Arbitraje de Convergencia Puro (también conocido como Pairs Trading intrínseco). Es el "Santo Grial" del trading de bajo riesgo porque, en teoría, eres delta-neutral: no te importa si el mercado sube o baja, solo te importa que la diferencia entre los dos precios vuelva a cero. La Mecánica del Arbitraje Bidireccional Cuando detectas que el mercado Inverso está un 1.2% más barato que el Lineal, haces esto simultáneamente:   1. LONG en el mercado Inverso (compras lo "barato").   2. SHORT en el mercado Lineal (vendes lo "caro"). ¿Qué ganas con esto? Has "bloquea…

**IA (pregunta):**
Mi Opinión: ¿Cómo lo construiría yo? Si decides ir por el camino bidireccional, el bot "Centinela" que platicamos antes cambia su objetivo. Ya no busca "comprar barato para el futuro", sino que busca "picos de ineficiencia". Pasos para tu nuevo Bot de Arbitraje:   1. Monitor de Spread: Calcula continuamente: Spread=PrecioLineal−PrecioInverso.   2. Filtro de Liquidez: El bot mira el Order Book y dice: "Hay suficiente volumen para meter $500 USD con un slippage menor a 0.1%".   3. Disparador Dual:   * Si Spread>Umbral, abre Long Inverso / Short Lineal.   * Cierre: Cuando el Spread vuelva a ser casi 0 (o lo suficientemente pequeño), cierra ambas posiciones y cobra la diferencia.

</details>

<!-- chroma:b8e45852-6088-465a-9988-fbfbb8cc4ee4 -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger (Cuándo aplica)
Esta estrategia se activa cuando existe una discrepancia de precios significativa entre dos mercados para un mismo activo. El objetivo es aprovechar la volatilidad del mercado para generar ganancias, tanto en el corto como en el largo plazo.

### ⚙️ Lógica Operativa (El Cómo)
- **Escalado por Discrepancia:** Se utiliza una tabla de "marchas" basada en umbrales estáticos de spread. Cada marcha dispara diferentes cantidades de capital al Long y al Short, creando un desbalance a favor de la acumulación en momentos de mayor volatilidad.

- **Desbalance Calculado (Posición Neta):** El bot calcula constantemente la diferencia entre las posiciones Long y Short, generando una "Posición Neta". Esta posición representa la cantidad de activos acumulados durante el proceso de arbitraje.

- **Toma de Ganancias y Auto-Equilibrio:** Cuando el precio del activo sube un porcentaje predefinido por encima del precio promedio de la Posición Neta, el bot vende automáticamente la cantidad correspondiente a la Posición Neta, generando ganancias y regresando a una posición Delta-Neutral.

### ⚠️ Restricciones / Notas Tácticas
La acumulación agresiva durante periodos de baja puede generar una exposición significativa al riesgo si el mercado experimenta una caída prolongada. Es crucial establecer un Límite Máximo de Exposición Neta para evitar pérdidas excesivas en escenarios de mercado bajista.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Sí que analicé en base a la discrepancia, que tenga como parámetros de qué hacer en cada caso, pero sencillos que no retracen o lo atonten, además no importa si no es estrictamente igual, como me gusta la moneda, no me importaría holdear "o desbalancear ligeramente a favor del Long", el bot también podría calcular cuando cerrar ese desbalance", o sea ya que diga, ok, el desbalance está en un promedio de x precio, si sube el valor un 2 o tres por ciento, me equilibro nuevamente, si baja no pasa…

**IA (explicación):**
Es una evolución tremenda. Al aceptar que no te importa quedarte con monedas porque confías en el proyecto a largo plazo, eliminas el mayor estrés del arbitrajista puro: el pánico de cerrar a la fuerza. Estás usando la volatilidad y las fallas del mercado no solo para ganar en el corto plazo, sino para construir un portafolio a precio de descuento.
Vamos a estructurar esta lógica para que siga siendo rápida ("sin atontar al bot") pero que gestione ese desbalance de manera inteligente.
1. Entradas Dinámicas: Escalado por Discrepancia
Para que el bot no se quede pensando con matemáticas complej…

</details>

<!-- chroma:6064d690-daa0-42a7-a7a1-18be4638dff3 -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger (Cuándo aplica)
Este bloque define estrategias de arbitraje dentro del ecosistema de Bybit, aprovechando desajustes de precios entre diferentes instrumentos financieros. Se activa cuando se detectan oportunidades de compra/venta simultánea en mercados relacionados para obtener ganancias sin exposición al riesgo de mercado.

### ⚙️ Lógica Operativa (El Cómo)
- **Arbitraje de Índices:** Detectar desviaciones del precio Spot de Bybit respecto al Index Price de los contratos perpetuos. Comprar en Spot cuando el precio es inferior al Index y vender en Perpetuo, aprovechando la convergencia natural.

- **Arbitraje de Pares LST:** Identificar 'depegs' (pérdida de paridad) entre tokens de Liquid Staking (LST) y sus criptomonedas subyacentes. Comprar el LST infravalorado y vender la criptomoneda correspondiente en Perpetuo, esperando la recuperación de la paridad.

- **Arbitraje de Mercado Convert:** Aprovechar retrasos en la cotización del sistema 'Convert' respecto al libro de órdenes Spot Margin. Comprar a un precio antiguo en 'Convert' y vender al precio actual en el mercado abierto.

- **Arbitraje de Funding Rate:** Abrir posiciones Long/Short simultáneas en criptomonedas correlacionadas con Funding Rates opuestos. Obtener ganancias por los pagos de Funding sin exposición al riesgo de mercado.

### ⚠️ Restricciones / Notas Tácticas
La velocidad de ejecución es crucial para el éxito del arbitraje. Cualquier retraso puede eliminar la oportunidad de ganancia. La liquidez disponible en cada mercado también limita el tamaño de las operaciones.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Algún otro mercado que pueda aprovecharse de bybyt? Dijimos que opcióned no o sí? Qué más hay que no hayamos considerado?
Has hecho un trabajo de exploración táctica excelente, pero si queremos ser el "asesino de líderes" definitivo, hay un par de campos de batalla ocultos en Bybit que la mayoría de los traders ni siquiera saben que existen.

**IA (explicación):**
Sobre las Opciones, mi consejo técnico es: Mantén el ojo puesto, pero no el gatillo. Las opciones en Bybit tienen una liquidez muy pobre en las 'alts', lo que genera spreads gigantes. Para un carroñero, eso es tentador, pero el riesgo de quedar atrapado es alto.
Sin embargo, aquí hay tres territorios vírgenes que no hemos considerado y que encajan perfecto con tu mentalidad de Berserker/Carroñero:
________________

1. El Arbitraje de 'Índices' (Spot vs. Index Price)
Bybit calcula un Index Price (un promedio de varios exchanges como Binance, Kraken, Coinbase) para liquidar sus contratos perpet…

</details>

<!-- chroma:d5b26dec-1882-4b87-9b77-5eaadd753aaa -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger
Se activa cuando se detectan divergencias significativas de precios entre diferentes mercados (Spot, Perpetuos, Pares Fiat e Inversos) para un activo dado.

### ⚙️ Lógica Operativa
- **Escaneo:** La Red Omnisciente escanea los datos de mercado para Spot, Perpetuos, Pares Fiat e Inversos del activo objetivo.
- **Análisis:** El módulo "Tusk" analiza los datos de mercado en busca de divergencias significativas entre los precios de diferentes mercados.
- **Decisión:** Si se detecta una divergencia, la Red Omnisciente decide ejecutar un ataque multidimensional coordinando acciones de trading en los mercados afectados.

### ⚠️ Restricciones / Notas Tácticas
La precisión del arbitraje depende de la velocidad y calidad de los datos de mercado. Retrasos o errores en los datos pueden resultar en pérdidas. La ejecución simultánea de operaciones en múltiples mercados requiere una infraestructura robusta y confiable para evitar errores de ejecución.

**Lógica cristalizada del código:**
- Incluye la función escanear_matriz en el diseño.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Todavía no nos metamos tanto con igris, recuerdas que habíamos dicho que el monarca anterior solo tenía dos ventanas o una guerra con dos frentes, pero con el ejército podría exponerse por ejemplo el pez litcoin a muchas más ventanas por spot perpetuos futuros, pares de euro, etc., necesitamos que la red de inteligencia sea más omnisciente,

**IA (explicación):**
Para que la red sea Omnisciente, necesitamos que los generales dejen de mirar un solo 'par' y empiecen a mirar la Matriz de Correlación Total. Bajo tu manto, un solo activo (ej. Litecoin) deja de ser un punto y se convierte en una Estrella de Múltiples Puntas. El ejército ahora vigila y opera simultáneamente en: * Frente de Spot: La posesión física, la base del Jardín. * Frente de Perpetuos y Futuros: Donde Beru y Greed cazan con apalancamiento y traen los trofeos más sangrientos. * Frente de Divisas (Pares Euro/USD/BTC): Donde Igris transmuta el valor para evitar que la erosión del dinero fí…

**IA (pregunta):**
Soberano, hemos roto las cadenas de los 'dos frentes'. El jardín ahora tiene ventanas hacia todas las dimensiones del valor. ¿Deseas que Igris comience a mapear la flota de los 23 barcos en estos frentes específicos (Spot/Perps/Inversos) para que la Red Omnisciente empiece a latir, o prefieres que Tusk haga una simulación de 'Guerra Total' primero?

</details>

<!-- chroma:93d462f0-c041-40fa-8f6f-7c400e72ec98 -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger (Cuándo aplica)
Este módulo se activa cuando se detecta un deslizamiento de precios significativo (>1%) entre pares de criptomonedas con bajo volumen de negociación, utilizando monedas de reserva como EUR, MNT, BTC y la moneda estable sintética USDE.

### ⚙️ Lógica Operativa (El Cómo)
- El bot compara el precio efectivo de una criptomoneda en diferentes ventanas de cambio (LTC/USDT, LTC/EUR, LTC/MNT, LTC/BTC, LTC/USDE).
- Si se detecta un deslizamiento superior al 1% en una ventana con bajo volumen (ej. LTC/EUR), el bot ejecuta una orden de compra en esa ventana utilizando Spot Margin.
- El bot cubre el riesgo vendiendo la criptomoneda adquirida en el Perpetuo de USDT, aprovechando la mayor liquidez de este mercado.

### ⚠️ Restricciones / Notas Tácticas
El uso de Spot Margin en pares con dos criptomonedas (ej. LTC/BTC) expone al bot a la volatilidad de ambas monedas. Se requiere una gestión de riesgo efectiva, como el Alivio Agresivo y un margen del 85%, para minimizar el impacto de las fluctuaciones de precios. La eficiencia de capital puede variar según la moneda base utilizada en la conversión.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Podrían entrar a la ecuación los pares de spot del euro, mnt y BTC, ya vez que esos también están en spot margen, y está euro usdt o el de usde, pueden tener también oportunidades por submenor volumen de mercado.

¡Brillante! Estás encontrando las "grietas de liquidez" más profundas del mercado. Los pares de Euro (EUR), Mantle (MNT), BTC y la nueva estable sintética USDE (de Ethena) son minas de oro para un bot de guerrilla por una razón técnica sencilla: Bajo Arbitraje Institucional.

**IA (explicación):**
Mientras los fondos gigantes se pelean por milésimas de centavo en el par BTC/USDT, los pares como LTC/EUR o LTC/MNT suelen estar "abandonados". Si alguien vende una cantidad mediana de LTC por Euros, el precio en esa ventana se va a desplomar mucho más que en la de USDT. Ahí es donde tu soldado entra a barrer.
Aquí te explico cómo estas nuevas variables potencian la ecuación:
1. El Arbitraje de "Divisas de Reserva" (EUR, MNT, BTC)
Al meter estos pares en Spot Margin, tu bot ahora tiene "Ventanillas de Cambio" adicionales. La lógica de mejora de precio se expande así:
   * La Ventana del Euro…

**IA (pregunta):**
¿El General está listo para dar la orden de empezar a diseñar la lógica de estos pares exóticos?

</details>

<!-- chroma:c2dbf46c-6f6c-42f8-924f-8e33d114d6e2 -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger (Cuándo aplica)
Explota ineficiencias temporales entre mercados Lineales e Inversos de criptomonedas. Se activa cuando se detectan discrepancias significativas en los precios de un activo en ambos tipos de mercados.

### ⚙️ Lógica Operativa (El Cómo)
- Monitorear constantemente los libros de órdenes de mercados Lineales e Inversos para identificar oportunidades de arbitraje.
- Calcular la diferencia de precio entre el mercado Lineal y el Inverso.
- Ejecutar órdenes simultáneas: Long en el mercado Inverso y Short en el mercado Lineal, aprovechando la discrepancia.
- Gestionar el riesgo de liquidación mediante el monitoreo constante del margen disponible en ambas posiciones.

### ⚠️ Restricciones / Notas Tácticas
La capacidad de ejecución (Depth) limita el volumen que se puede arbitrar sin afectar el precio. El slippage autogenerado por órdenes grandes puede reducir la rentabilidad. La tasa de financiación (Funding Rate) puede generar ganancias adicionales o pérdidas, dependiendo de su dirección y magnitud.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
¿Es mejor que el bot de Grid?
Es más sofisticado. El Grid gana dinero con el "zig-zag" del precio. Este bot gana dinero con el "pánico" y la desincronización de los mercados. Son excelentes compañeros: el Grid trabaja en mercados normales, y el Arbitrajista trabaja en colapsos o subidas parabólicas.
¿Te suena muy loco o quieres que empecemos a esbozar cómo sería esa lógica de comparación de precios entre LTCUSDT y LTCUSD?
Continúa, teóricamente, qué rendimientos podría tener?? Más o menos respo…

**IA (explicación):**
Hablar de rendimientos en arbitraje es entrar en el terreno de la eficiencia pura. A diferencia del Grid (que depende de que el precio se mueva mucho), aquí dependes de que el mercado se "rompa" temporalmente.
Teóricamente, los rendimientos en este tipo de arbitraje (Lineal vs. Inverso) se calculan bajo tres escenarios:
________________
1. El Escenario de "Caza de Cisnes Negros"
Este es el más lucrativo. En un crash como el que mencionas (BTC cayendo 15k en horas), las ineficiencias no son del 0.1%, sino que pueden llegar al 2% o 3% por operación.
   * Frecuencia: Rara (1 o 2 veces al mes en…

**IA (pregunta):**
¿Qué opinas de estos números? ¿Te parece suficiente para el esfuerzo de programar la lógica de comparación de libros de órdenes?

</details>

<!-- chroma:8eddb63e-1910-4a12-a530-44cfdb9d1d1f -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger (Cuándo aplica)
Este módulo se activa cuando se busca aumentar la rentabilidad (APR) del portafolio mediante estrategias de arbitraje estadístico de alta frecuencia.

### ⚙️ Lógica Operativa (El Cómo)
- Identificar oportunidades de arbitraje en múltiples mercados (mínimo 120 frentes).
- Ejecutar operaciones de compra y venta simultáneas para aprovechar las diferencias de precios.
- Capturar micro-oportunidades con un margen de ganancia neto del 0.15% por operación.

### ⚠️ Restricciones / Notas Tácticas
La eficiencia del módulo depende de la liquidez de los mercados y la velocidad de ejecución. Un factor clave es el uso estratégico del capital, ya que no se recomienda utilizar el 100% en cada operación. La rentabilidad real puede verse afectada por comisiones de intercambio y deslizamiento.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
Primero, de forma muy conservadora, para ver si este ejército será se ayuda o no al nuevo monarca, qué porcentaje de apr podría llegar a conseguir, así muy conservadoramente y muy teóricamente porque mi monarca ya tiene datos que son reales y quiero ver si sería correcto fusionarlos o solo el ejército o solo el monarca

**IA (explicación):**
Para tomar esta decisión, hay que entender que el Ejército de Sombras no busca una rentabilidad basada en la "suerte" o la dirección del mercado, sino en la fricción.
Siendo extremadamente conservadores y puramente teóricos, analicemos el potencial de este sistema. En el mundo del arbitraje estadístico de alta frecuencia (que es lo que hemos diseñado), el APR no se mide por "grandes saltos", sino por la suma de micro-migajas.
1. El Cálculo del "Botín de Guerra" (APR Teórico Conservador)
Imagina que tu capital total son $1,000 USD.
      * Frecuencia de captura (Carroñero): Digamos que el merc…

</details>

<!-- chroma:b0b0e38a-1d9a-4a16-9251-e96dad17d3bb -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger
Ejecutar cuando se detecta una diferencia de precio del 1% o mayor entre un activo en su versión Inverso (Coin-M) y su equivalente en USDT (Linear-M) o Spot.

### ⚙️ Lógica Operativa
- Identificar el activo objetivo con la brecha de precios superior al 1%.
- Si el Inverso es más barato que el USDT: Abrir una posición Long en el Inverso y una posición Short en el USDT.
- Si el Inverso es más caro que el USDT: Abrir una posición Short en el Inverso y una posición Long en el USDT.
- Ejecutar entradas escalonadas de $50 USD para cada posición, manteniendo un ratio máximo de desbalance del 55/45 entre las posiciones Long y Short.

### ⚠️ Restricciones / Notas Tácticas
La estrategia asume la existencia de liquidez suficiente en ambos mercados (Inverso y USDT) para ejecutar las operaciones sin deslizamiento significativo. Un cambio brusco en el mercado puede invalidar la brecha de precios y generar pérdidas.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
No tienes recuerdos de esa conversación? Estábamos platicando en teoría aún.

**IA (explicación):**
Estábamos diseñando el "Arbitrage Hunter" (o el bot de convergencia). La teoría que establecimos es la "Biblia" para este proyecto:
El Plano Teórico (Lo que tenemos en la mesa)
   1. El Objetivo: Capturar la ineficiencia entre el Inverso (Coin-M) y el USDT (Linear-M) o Spot.
   2. La Condición de Disparo: No entrar por entrar, sino esperar a que el "Gap" (la brecha) sea de al menos 1%.
   3. El Método de "Cero a Pro":
   * Empezamos con posiciones en 0.
   * Si el Inverso se pone 1% más barato que el USDT -> Long Inverso / Short USDT.
   * Si el Inverso se pone 1% más caro que el USDT -> Shor…

**IA (pregunta):**
¿Qué nos falta para pasar de la teoría a la acción?

</details>

<!-- chroma:d9f329e8-ead2-4981-8d79-531d4fcd8e4c -->

## 💡 Ideas Centrales (Manual)

## 💡 Arbitraje_Mercado

### 🎯 Contexto y Trigger
Aplicar esta estrategia cuando existe una diferencia significativa (spread) entre los precios de un activo en mercados Lineales e Inversos.

### ⚙️ Lógica Operativa
- Abrir una posición Long en el mercado Inverso donde el precio es más bajo.
- Abrir simultáneamente una posición Short en el mercado Lineal para cubrir el riesgo.
- Esperar a que el spread se reduzca (convergencia de precios).
- Cerrar la posición Short en el mercado Lineal, dejando la posición Long activa en el mercado Inverso.

### ⚠️ Restricciones / Notas Tácticas
Esta estrategia implica un mayor riesgo debido a la exposición al apalancamiento en el mercado Inverso. La convergencia de precios no está garantizada y puede tomar tiempo, exponiendo a posibles pérdidas si el spread se amplía en lugar de reducirse. Requiere una gestión de riesgos cuidadosa y comprensión profunda de los mercados de criptomonedas.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
¿Otra posibilidad? ¿Y si no cerramos inmediatamente? O sea, si simplemente estamos mejorando el precio de entrada?

**IA (explicación):**
Lo que estás planteando es usar el Arbitraje como una estrategia de entrada (Entry Optimization) en lugar de un trade cerrado. Es una de las formas más inteligentes de operar.
Básicamente, estás diciendo: "Si de todos modos quiero comprar Litecoin (LTC) a largo plazo, ¿por qué comprarlo en el mercado Lineal si el Inverso me lo está ofreciendo con un 1% de descuento?".
Aquí te analizo qué pasa si no cierras inmediatamente y dejas que esa ventaja trabaje a tu favor:
1. El "Descuento Real" en el Costo de Adquisición
Si el mercado Lineal marca 100 USDT y el Inverso marca 98.8 USD, y tú entras Lon…

</details>