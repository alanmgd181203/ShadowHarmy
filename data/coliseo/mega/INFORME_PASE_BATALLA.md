# Informe Mega Coliseo — Pase de batalla Beru

- UTC: `2026-07-19T17:34:03.743130+00:00`
- Status checkpoint: `running`
- Jobs: **684**
- Vacíos dorados malla×1: `[1.8, 1.6]`
- Vacíos dorados malla×2: `[2.0, 1.2]`
- Outliers re-run: `['AAVE', 'ADA', 'APT', 'AVAX', 'BCH', 'DOGE', 'ETC', 'ETH', 'HYPE', 'LINK', 'LTC', 'MNT', 'NEAR', 'OP', 'SOL']`

## Qué se midió

Legión al máximo (capas + fusión hoz + Mega), contabilidad masa seca, indicador **calor pase** = 3d 20% · mes 50% · año 30%. Dos campañas: malla oz/red normal y ×2. Sub-Berus Soldado→Mariscal sobre los 2 vacíos dorados.

## Pase de batalla (ranking de rangos)

Vacío de referencia ~**1.8%** · malla ×1 · mejor rango por activo.

| # | Activo | Rango | Tier | Calor | Efi año | Plata $ | Capas | Fusiones | Megas | Semáforo |
|---|--------|-------|------|------:|--------:|--------:|------:|---------:|------:|----------|
| 1 | MNT | Mariscal | PLENO | 17112.09 | 56906.7 | 1896889 | 703 | 629 | 0 | VERDE |
| 2 | AVAX | Mariscal | PLENO | 12096.86 | 38730.3 | 1383225 | 509 | 444 | 0 | VERDE |
| 3 | LINK | Mariscal | PLENO | 12079.37 | 39607.7 | 1414562 | 250 | 215 | 0 | VERDE |
| 4 | LTC | Mariscal | PLENO | 10589.02 | 35291.5 | 882287 | 541 | 480 | 0 | VERDE |
| 5 | HYPE | Soldado | BERUBBY | 10015.42 | 27890.3 | 733954 | 532 | 200 | 312 | VERDE |
| 6 | BCH | Mariscal | PLENO | 8039.66 | 26402.1 | 942934 | 520 | 465 | 0 | VERDE |
| 7 | SOL | General | PROTO1 | 5987.75 | 14967.2 | 249454 | 169 | 146 | 0 | VERDE |
| 8 | XRP | Soldado | BERUBBY | 5651.49 | 17831.9 | 297199 | 188 | 74 | 97 | AMARILLO |
| 9 | ETH | Mariscal | PLENO | 5192.72 | 17247.8 | 215598 | 557 | 488 | 0 | AMARILLO |
| 10 | ADA | Mariscal | PLENO | 4933.72 | 13610.3 | 272206 | 355 | 299 | 0 | AMARILLO |
| 11 | DOGE | Mariscal | PLENO | 4073.90 | 13551.0 | 338776 | 504 | 430 | 0 | AMARILLO |
| 12 | AAVE | Mariscal | PLENO | 3884.83 | 2995.2 | 78822 | 132 | 115 | 0 | AMARILLO |
| 13 | NEAR | Mariscal | PLENO | 3836.10 | 12027.7 | 429560 | 341 | 290 | 0 | AMARILLO |
| 14 | FIL | Mariscal | PLENO | 3794.68 | 12422.2 | 690120 | 210 | 167 | 0 | AMARILLO |
| 15 | OP | Mariscal | PLENO | 3760.53 | 12351.6 | 441130 | 326 | 270 | 0 | ROJO |
| 16 | APT | Soldado | BERUBBY | 3542.70 | 10394.2 | 371222 | 272 | 94 | 162 | ROJO |
| 17 | UNI | Mariscal | PLENO | 3069.79 | 6610.8 | 236100 | 408 | 357 | 0 | ROJO |
| 18 | ETC | Mariscal | PLENO | 2424.95 | 8015.2 | 286257 | 687 | 595 | 0 | ROJO |
| 19 | DOT | Soldado | BERUBBY | 2290.28 | 6022.5 | 150564 | 217 | 85 | 115 | ROJO |
| 20 | BTC | Soldado | BERUBBY | 1996.83 | 5412.5 | 67657 | 158 | 47 | 89 | ROJO |
| 21 | SUI | Soldado | BERUBBY | 1706.22 | 4330.1 | 154646 | 138 | 58 | 64 | ROJO |
| 22 | XLM | Soldado | BERUBBY | 1322.71 | 3301.4 | 117908 | 206 | 61 | 125 | ROJO |

## Gráficas

- `data\coliseo\mega\charts\calor_malla_x1.png`
- `data\coliseo\mega\charts\vacios_vs_calor.png`
- `data\coliseo\mega\charts\heatmap_rangos_x1.png`
- `data\coliseo\mega\charts\efi_mensual_flota.png`
- `data\coliseo\mega\charts\malla_x1_vs_x2.png`

## Conclusiones (auto)

1. El pase de batalla ordena **activo × rango** para despertar legión, no solo el coin.
2. Comparar gráficas malla ×1 vs ×2: si ×2 gana en mediana, conviene red más ancha en vivo.
3. Outliers (masa_cap / efi extrema) deben leerse con el job `outlier` path=min.
4. El desglose mensual está en cada job JSON bajo `meses`.

## Cómo reanudar / repetir

```text
python scripts/coliseo_mega_campana.py --resume
python scripts/coliseo_mega_informe.py
```

