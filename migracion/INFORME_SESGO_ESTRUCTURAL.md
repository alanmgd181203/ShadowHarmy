# Informe Monarca — sesgo estructural vs índice

**Fecha:** 2026-08-02 16:54  
**Qué mide:** cuánto suele cotizar cada mar (spot / lineal / inverso) respecto al índice Bybit. Cero = mediana histórica; positivo = caro vs índice.

**Para qué:** el gap eterno no es oportunidad. El reloj del manto y el disparo deben contar solo cuando el clima **se sale** de este cero.

| Base | Spot cero % | Lineal cero % | Inverso cero % | Lectura |
|------|-------------|---------------|----------------|---------|
| LTC | +0.0000 (n~1437) | -0.0668 (n~1511) | -0.2214 (n~1465) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.155% estructural |
| BTC | -0.0003 (n~1437) | -0.0445 (n~1511) | -0.1297 (n~1437) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.085% estructural |
| AAVE | +0.0000 (n~1437) | -0.0764 (n~1511) | -0.2280 (n~1440) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.152% estructural |
| ADA | +0.0000 (n~1437) | -0.0601 (n~1511) | -0.1591 (n~1461) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.099% estructural |
| APT | +0.0000 (n~1437) | -0.0641 (n~1511) | -0.2035 (n~1475) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.139% estructural |
| AVAX | +0.0000 (n~1433) | -0.0609 (n~1512) | -0.1346 (n~1476) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.074% estructural |
| BCH | -0.0085 (n~1433) | -0.0857 (n~1512) | -0.3285 (n~1435) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.243% estructural |
| DOGE | +0.0000 (n~1433) | -0.0549 (n~1512) | -0.0996 (n~1433) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.045% estructural |
| DOT | +0.0000 (n~1433) | -0.0712 (n~1512) | -0.1382 (n~1466) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.067% estructural |
| ETC | +0.0285 (n~1433) | -0.0600 (n~1512) | -0.1560 (n~1433) | inverso suele barato; gap lineal−inverso≈+0.096% estructural |
| ETH | +0.0000 (n~1433) | -0.0465 (n~1512) | -0.1502 (n~1458) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.104% estructural |
| FIL | — (n~0) | -0.0694 (n~88) | -0.4856 (n~8) | inverso suele barato; gap lineal−inverso≈+0.416% estructural |
| HYPE | — (n~0) | -0.0497 (n~88) | +0.5793 (n~15) | gap lineal−inverso≈-0.629% estructural |
| LINK | — (n~0) | -0.0360 (n~88) | -0.4677 (n~10) | inverso suele barato; gap lineal−inverso≈+0.432% estructural |
| MNT | +0.0000 (n~1437) | -0.0753 (n~1511) | -0.1637 (n~1437) | inverso suele barato; spot pegado; gap lineal−inverso≈+0.088% estructural |
| NEAR | — (n~0) | -0.0412 (n~88) | +0.0059 (n~6) | gap lineal−inverso≈-0.047% estructural |

## Como leerlo

Si el **inverso** sale casi siempre negativo (barato vs indice) y el lineal un poco arriba, el spread lineal↔inverso **parece** oportunidad todo el dia. Eso es el sesgo eterno — no Asalto.

Con el cable de frecuencia/ETA (cero estructural), solo cuentan las veces que el spread se **aleja** de ese clima normal.

JSON maquina: `/Users/jessicareyesmuro/Desktop/btc/jubilacion/ShadowHarmy/data/informe_sesgo_estructural.json`
