# Informe Monarca — sesgo estructural (detallado)

**Fecha:** 2026-08-02 17:02  
**Ventana analisis gap:** mediano  
**Que mide:** ceros vs indice Bybit + **% del tiempo** que el gap lineal↔inverso vive en ese desfase + **volteos** (lado opuesto del cero).

**Para que:** el gap eterno no es oportunidad. Hay que saber si el desfase es abrumador y que pasa cuando se voltea (planear / aprovechar).

## 1. Ceros por mar (vs indice)

| Base | Spot cero % | Lineal cero % | Inverso cero % | Gap est. lineal-inv |
|------|-------------|---------------|----------------|---------------------|
| LTC | +0.0000 (n~1435) | -0.0668 (n~1509) | -0.2214 (n~1463) | +0.155 |
| BTC | -0.0003 (n~1435) | -0.0446 (n~1509) | -0.1296 (n~1435) | +0.085 |
| AAVE | +0.0000 (n~1435) | -0.0764 (n~1509) | -0.2278 (n~1438) | +0.151 |
| ADA | +0.0000 (n~1435) | -0.0601 (n~1509) | -0.1589 (n~1459) | +0.099 |
| APT | +0.0000 (n~1435) | -0.0641 (n~1509) | -0.2035 (n~1473) | +0.139 |
| AVAX | +0.0000 (n~1431) | -0.0609 (n~1510) | -0.1347 (n~1474) | +0.074 |
| BCH | -0.0085 (n~1431) | -0.0856 (n~1510) | -0.3288 (n~1433) | +0.243 |
| DOGE | +0.0000 (n~1431) | -0.0550 (n~1510) | -0.0996 (n~1431) | +0.045 |
| DOT | +0.0000 (n~1431) | -0.0712 (n~1510) | -0.1383 (n~1464) | +0.067 |
| ETC | +0.0285 (n~1431) | -0.0600 (n~1510) | -0.1556 (n~1431) | +0.096 |
| ETH | +0.0000 (n~1431) | -0.0465 (n~1510) | -0.1502 (n~1456) | +0.104 |
| FIL | — (n~0) | -0.0694 (n~88) | -0.4856 (n~8) | +0.416 |
| HYPE | — (n~0) | -0.0497 (n~88) | +0.5793 (n~15) | -0.629 |
| LINK | — (n~0) | -0.0360 (n~88) | -0.4677 (n~10) | +0.432 |
| MNT | +0.0000 (n~1435) | -0.0753 (n~1509) | -0.1637 (n~1435) | +0.088 |
| NEAR | — (n~0) | -0.0412 (n~88) | +0.0059 (n~6) | -0.047 |

## 2. Residencia — ¿cuanto tiempo vive en el desfase?

Veredicto: **abrumador** ≥85% · **dominante** ≥65% · **mitad_mitad** ≥45% · si no → **inestable**.

| Base | % en desfase | % clima normal | % volteado | Veredicto | n |
|------|--------------|----------------|------------|-----------|---|
| LTC | 100.0% | 0.0% | 0.0% | **abrumador** | 22 |
| BTC | 99.2% | 97.6% | 0.0% | **abrumador** | 1507 |
| AAVE | 73.9% | 61.0% | 7.2% | **dominante** | 1509 |
| ADA | 100.0% | 0.0% | 0.0% | **abrumador** | 29 |
| APT | 100.0% | 0.0% | 0.0% | **abrumador** | 48 |
| AVAX | 100.0% | 0.0% | 0.0% | **abrumador** | 50 |
| BCH | 65.1% | 50.5% | 19.6% | **dominante** | 1508 |
| DOGE | 92.7% | 68.2% | 1.1% | **abrumador** | 1508 |
| DOT | 100.0% | 0.0% | 0.0% | **abrumador** | 30 |
| ETC | 63.9% | 33.4% | 6.0% | **mitad_mitad** | 1508 |
| ETH | 100.0% | 0.0% | 0.0% | **abrumador** | 39 |
| FIL | 100.0% | 100.0% | 0.0% | **abrumador** | 36 |
| HYPE | 0.0% | 0.0% | 100.0% | **inestable** | 21 |
| LINK | 100.0% | 100.0% | 0.0% | **abrumador** | 48 |
| MNT | 71.5% | 41.4% | 4.2% | **dominante** | 1507 |
| NEAR | 49.4% | 0.0% | 50.6% | **mitad_mitad** | 79 |

## 3. Volteos — cuando se sale del clima natural

Volteo = el gap va al **lado opuesto** del cero estructural (mas alla de epsilon). Esos episodios son los candidatos a planear / aprovechar; no el gap eterno.

| Base | Episodios | Duracion media (h) | Exceso medio % | Lectura |
|------|-----------|--------------------|----------------|---------|
| LTC | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| BTC | 0 | — | — | Vive ~99% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| AAVE | 44 | 0.1 | +0.1902 | Vive ~74% del tiempo en el desfase estructural (dominante). Volteos: 44 episodios (~7.2% del tiempo). |
| ADA | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| APT | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| AVAX | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| BCH | 100 | 0.42 | +0.2249 | Vive ~65% del tiempo en el desfase estructural (dominante). Volteos: 100 episodios (~19.6% del tiempo). |
| DOGE | 2 | 3.0 | +0.3117 | Vive ~93% del tiempo en el desfase estructural (abrumador). Volteos: 2 episodios (~1.1% del tiempo). |
| DOT | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| ETC | 41 | 0.08 | +0.1874 | Vive ~64% del tiempo en el desfase estructural (mitad_mitad). Volteos: 41 episodios (~6.0% del tiempo). |
| ETH | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| FIL | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| HYPE | 1 | 16.75 | +1.3442 | Vive ~0% del tiempo en el desfase estructural (inestable). Volteos: 1 episodios (~100.0% del tiempo). |
| LINK | 0 | — | — | Vive ~100% del tiempo en el desfase estructural (abrumador). Volteos: 0 episodios (~0.0% del tiempo). |
| MNT | 20 | 0.32 | +0.1868 | Vive ~72% del tiempo en el desfase estructural (dominante). Volteos: 20 episodios (~4.2% del tiempo). |
| NEAR | 1 | 2.08 | +1.3062 | Vive ~49% del tiempo en el desfase estructural (mitad_mitad). Volteos: 1 episodios (~50.6% del tiempo). |

## 4. Muestra de episodios (hasta 5 por base con volteos)

### AAVE

- desde 2026-07-04 21:00: 0.0h · gap medio -0.0343% · exceso max +0.1856%
- desde 2026-07-05 04:00: 0.0h · gap medio -0.0113% · exceso max +0.1627%
- desde 2026-07-05 12:00: 1.0h · gap medio +0.0000% · exceso max +0.1514%
- desde 2026-07-06 06:00: 0.0h · gap medio -0.0330% · exceso max +0.1844%
- desde 2026-07-06 09:00: 0.0h · gap medio -0.0104% · exceso max +0.1617%

### BCH

- desde 2026-07-03 18:00: 0.0h · gap medio +0.0483% · exceso max +0.1949%
- desde 2026-07-04 00:00: 2.0h · gap medio +0.0265% · exceso max +0.2387%
- desde 2026-07-04 10:00: 3.0h · gap medio +0.0237% · exceso max +0.2560%
- desde 2026-07-04 15:00: 0.0h · gap medio +0.0427% · exceso max +0.2005%
- desde 2026-07-04 17:00: 0.0h · gap medio +0.0169% · exceso max +0.2262%

### DOGE

- desde 2026-08-01 11:00: 5.0h · gap medio -0.4117% · exceso max +0.5991%
- desde 2026-08-01 18:00: 1.0h · gap medio -0.1224% · exceso max +0.1738%

### ETC

- desde 2026-07-03 21:00: 0.0h · gap medio -0.0976% · exceso max +0.1932%
- desde 2026-07-04 22:00: 0.0h · gap medio -0.1400% · exceso max +0.2357%
- desde 2026-07-06 05:00: 0.0h · gap medio -0.1128% · exceso max +0.2084%
- desde 2026-07-06 16:00: 0.0h · gap medio -0.0561% · exceso max +0.1517%
- desde 2026-07-07 10:00: 0.0h · gap medio -0.1276% · exceso max +0.2232%

### HYPE

- desde 2026-08-01 23:14: 16.75h · gap medio +0.7152% · exceso max +1.9415%

### MNT

- desde 2026-07-17 08:00: 0.0h · gap medio -0.0797% · exceso max +0.1680%
- desde 2026-07-23 09:00: 0.0h · gap medio -0.0977% · exceso max +0.1861%
- desde 2026-07-23 12:00: 0.0h · gap medio -0.0738% · exceso max +0.1622%
- desde 2026-07-23 15:00: 0.0h · gap medio -0.0956% · exceso max +0.1840%
- desde 2026-07-27 10:00: 0.0h · gap medio -0.1081% · exceso max +0.1965%

### NEAR

- desde 2026-08-02 12:56: 2.08h · gap medio +1.2591% · exceso max +1.9109%

## Como leerlo (Monarca)

1. Si **% en desfase** es abrumador/dominante → el spread 'bonito' casi siempre es clima normal; sin cero estructural el ETA mentia hacia Asalto.
2. Los **volteos** son raros: ahi el gap se pone en contra del sesgo. Ahi se planifica / aprovecha; el resto es mantenimiento del cero.
3. Cable activo: `MANTO_CERO_ESTRUCTURAL=true` (frecuencia/ETA + puerta Igris).

JSON maquina: `/Users/jessicareyesmuro/Desktop/btc/jubilacion/ShadowHarmy/data/informe_sesgo_estructural.json`

### Jess — regenerar

```bash
git pull
python scripts/informe_sesgo_monarca.py
# opcional: python scripts/informe_sesgo_monarca.py --ventana corto
# opcional: python scripts/informe_sesgo_monarca.py --backfill --dias 30
git add migracion/INFORME_SESGO_ESTRUCTURAL.md data/informe_sesgo_estructural.json
git commit -m "Informe sesgo detallado: residencia + volteos."
git push
```
