# Informe Monarca — ETA manto por las 3 marchas

**Fecha:** 2026-08-02 17:29  
**Equity ref:** 1525 USD  

**Ley:** oportunidades = exceso vs **cero estructural** (`MANTO_CERO_ESTRUCTURAL=True`).

Las tres marchas:
- **Tactico** — exceso >= fees enteros (paciente)
- **Marcha Forzada** — exceso >= 1/2 fees (media)
- **Asalto** — exceso >= tablas / casi 0 (ansiosa; igual sobre el cero, no gap eterno)

## Tabla ETA (base / opt / pes)

| Base | Cero gap % | Fees % | Tactico | Forzada | Asalto | Modo sugerido |
|------|------------|--------|---------|---------|--------|---------------|
| BTC | +0.085 | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| MNT | +0.088 | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| ETH | +0.104 | 0.110 | 4.7h [3.1h–9.3h] | 4.4h [2.9h–8.8h] | 3.9h [2.6h–7.8h] | tactico |
| LTC | +0.155 | 0.110 | 15.9h [10.6h–1.3d (32h)] | 15.0h [10.0h–1.3d (30h)] | 13.2h [8.8h–1.1d (27h)] | tactico |
| DOGE | +0.045 | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| AAVE | +0.151 | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| BCH | +0.243 | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| ETC | +0.096 | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| SOL | +0.715 | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| XRP | — | 0.110 | sin_tasa | sin_tasa | sin_tasa | sin_datos |
| ADA | +0.099 | 0.110 | 9.8h [6.5h–19.7h] | 9.3h [6.2h–18.6h] | 8.2h [5.5h–16.4h] | tactico |
| APT | +0.139 | 0.110 | 1.2d (30h) [20.0h–2.5d (60h)] | 1.2d (30h) [20.0h–2.5d (60h)] | 1.2d (30h) [20.0h–2.5d (60h)] | tactico |
| AVAX | +0.074 | 0.110 | 9.8h [6.6h–19.7h] | 9.3h [6.2h–18.6h] | 8.2h [5.5h–16.4h] | tactico |
| DOT | +0.067 | 0.110 | 2.0d (48h) [1.3d (32h)–4.0d (96h)] | 2.0d (48h) [1.3d (32h)–4.0d (96h)] | 2.0d (48h) [1.3d (32h)–4.0d (96h)] | tactico |

## Detalle por base (ops/h y meta)

### BTC

- Cero gap: `0.085059` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa

### MNT

- Cero gap: `0.088346` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$32.4` · ops/h `None` · bocados `6.48` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$30.6` · ops/h `None` · bocados `6.12` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$27.0` · ops/h `None` · bocados `5.4` · ETA `—` (opt — / pes —) · sin_tasa

### ETH

- Cero gap: `0.103704` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: 1.0 / 1.0 / 1.0 · modo sugerido: **tactico**
- **Tactico (fees)**: meta `$12.6` · ops/h `0.5417` · bocados `2.52` · ETA `4.7h` (opt 3.1h / pes 9.3h) · OK
- **Marcha Forzada (1/2 fees)**: meta `$11.9` · ops/h `0.5417` · bocados `2.38` · ETA `4.4h` (opt 2.9h / pes 8.8h) · OK
- **Asalto (tablas)**: meta `$10.5` · ops/h `0.5417` · bocados `2.1` · ETA `3.9h` (opt 2.6h / pes 7.8h) · OK

### LTC

- Cero gap: `0.15463` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: 1.0 / 1.0 / 1.0 · modo sugerido: **tactico**
- **Tactico (fees)**: meta `$24.3` · ops/h `0.3056` · bocados `4.86` · ETA `15.9h` (opt 10.6h / pes 1.3d (32h)) · OK
- **Marcha Forzada (1/2 fees)**: meta `$22.95` · ops/h `0.3056` · bocados `4.59` · ETA `15.0h` (opt 10.0h / pes 1.3d (30h)) · OK
- **Asalto (tablas)**: meta `$20.25` · ops/h `0.3056` · bocados `4.05` · ETA `13.2h` (opt 8.8h / pes 1.1d (27h)) · OK

### DOGE

- Cero gap: `0.04462` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa

### AAVE

- Cero gap: `0.151379` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa

### BCH

- Cero gap: `0.243143` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$34.2` · ops/h `None` · bocados `6.84` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$32.3` · ops/h `None` · bocados `6.46` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$28.5` · ops/h `None` · bocados `5.7` · ETA `—` (opt — / pes —) · sin_tasa

### ETC

- Cero gap: `0.095617` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$100.0` · ops/h `None` · bocados `20.0` · ETA `—` (opt — / pes —) · sin_tasa

### SOL

- Cero gap: `0.7154` (fuente: mediana_lineal_vs_inverse) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$16.2` · ops/h `None` · bocados `3.24` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$15.3` · ops/h `None` · bocados `3.06` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$13.5` · ops/h `None` · bocados `2.7` · ETA `—` (opt — / pes —) · sin_tasa

### XRP

- Cero gap: `None` (fuente: None) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: None / None / None · modo sugerido: **sin_datos**
- **Tactico (fees)**: meta `$16.2` · ops/h `None` · bocados `3.24` · ETA `—` (opt — / pes —) · sin_tasa
- **Marcha Forzada (1/2 fees)**: meta `$15.3` · ops/h `None` · bocados `3.06` · ETA `—` (opt — / pes —) · sin_tasa
- **Asalto (tablas)**: meta `$13.5` · ops/h `None` · bocados `2.7` · ETA `—` (opt — / pes —) · sin_tasa

### ADA

- Cero gap: `0.098766` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: 1.0 / 1.0 / 1.0 · modo sugerido: **tactico**
- **Tactico (fees)**: meta `$19.8` · ops/h `0.4028` · bocados `3.96` · ETA `9.8h` (opt 6.5h / pes 19.7h) · OK
- **Marcha Forzada (1/2 fees)**: meta `$18.7` · ops/h `0.4028` · bocados `3.74` · ETA `9.3h` (opt 6.2h / pes 18.6h) · OK
- **Asalto (tablas)**: meta `$16.5` · ops/h `0.4028` · bocados `3.3` · ETA `8.2h` (opt 5.5h / pes 16.4h) · OK

### APT

- Cero gap: `0.139425` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: 1.0 / 1.0 / 1.0 · modo sugerido: **tactico**
- **Tactico (fees)**: meta `$100.0` · ops/h `0.6667` · bocados `20.0` · ETA `1.2d (30h)` (opt 20.0h / pes 2.5d (60h)) · OK
- **Marcha Forzada (1/2 fees)**: meta `$100.0` · ops/h `0.6667` · bocados `20.0` · ETA `1.2d (30h)` (opt 20.0h / pes 2.5d (60h)) · OK
- **Asalto (tablas)**: meta `$100.0` · ops/h `0.6667` · bocados `20.0` · ETA `1.2d (30h)` (opt 20.0h / pes 2.5d (60h)) · OK

### AVAX

- Cero gap: `0.073712` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: 1.0 / 1.0 / 1.0 · modo sugerido: **tactico**
- **Tactico (fees)**: meta `$34.2` · ops/h `0.6944` · bocados `6.84` · ETA `9.8h` (opt 6.6h / pes 19.7h) · OK
- **Marcha Forzada (1/2 fees)**: meta `$32.3` · ops/h `0.6944` · bocados `6.46` · ETA `9.3h` (opt 6.2h / pes 18.6h) · OK
- **Asalto (tablas)**: meta `$28.5` · ops/h `0.6944` · bocados `5.7` · ETA `8.2h` (opt 5.5h / pes 16.4h) · OK

### DOT

- Cero gap: `0.067086` (fuente: index_lineal_menos_inverso) · fees BE: `0.11%`
- Freq blend fees/medio/tablas: 1.0 / 1.0 / 1.0 · modo sugerido: **tactico**
- **Tactico (fees)**: meta `$100.0` · ops/h `0.4167` · bocados `20.0` · ETA `2.0d (48h)` (opt 1.3d (32h) / pes 4.0d (96h)) · OK
- **Marcha Forzada (1/2 fees)**: meta `$100.0` · ops/h `0.4167` · bocados `20.0` · ETA `2.0d (48h)` (opt 1.3d (32h) / pes 4.0d (96h)) · OK
- **Asalto (tablas)**: meta `$100.0` · ops/h `0.4167` · bocados `20.0` · ETA `2.0d (48h)` (opt 1.3d (32h) / pes 4.0d (96h)) · OK

## Como leerlo (Monarca)

1. Si ves **sin_tasa**: faltan muestras `lineal_vs_inverse` en esa base (ojos/Kaiser deben muestrear el edge de manto; el sesgo vs indice solo no basta).
2. ETA mas largo que el calculo viejo = correcto: ya no cuenta el gap eterno.
3. Elige marcha mirando la fila de tus Santos / MNT: paciencia vs velocidad.
4. Opt/pes = ritmo ×1.5 / ×0.5 de oportunidades (rango, no promesa).

JSON: `/Users/jessicareyesmuro/Desktop/btc/jubilacion/ShadowHarmy/data/informe_eta_marchas.json`

### Jess — regenerar y subir

```bash
git pull
python scripts/informe_eta_marchas.py --equity 1525
git add migracion/INFORME_ETA_MARCHAS.md data/informe_eta_marchas.json
git commit -m "Informe ETA manto: 3 marchas con cero estructural."
git push
```
