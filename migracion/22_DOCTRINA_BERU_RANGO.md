# 22b — Doctrina Beru rango (lineal · laterales · Oz trailing)

**Estado:** sellado Monarca **2026-08-20** · oficio **NUEVO** · manos/hilo **OFF**  
**Referencia:** el Beru spot/cazador continuo (`22_DOCTRINA_BERU.md`) queda como fósil; **no** se mezcla.

## Veredicto

Beru rango vive de laterales. El **Vacío ±1,2 %** no es la entrada: **arma un trailing de 0,2 %**.
Esa Oz trailing, al detonar, mete SHORT (si subía) o LONG (si bajaba). Un vivo activo. Ladder Red $5.

## Geometría

| Pieza | Valor |
|-------|------:|
| Vacío de Adán (semilla / sangre) | ±**1,2 %** desde el 0 → **arma** el trailing |
| Oz | **trailing 0,2 %** detrás del extremo (persigue) |
| Entrada SHORT | precio subía · trailing se dispara al **bajar** 0,2 |
| Entrada LONG | precio bajaba · trailing se dispara al **subir** 0,2 |
| Red continuación | **0,7 %** mismo sentido tras Oz → Beru **$5** (otro trailing) |
| Masa semilla / sangre | **$10** |
| Masa Red | **$5** |
| Sangre contraria | **1,2 %** → tramo opuesto $10 (trailing otra vez) |
| Ladder | repetible ambos lados |
| Vivos | uno activo |

## Oficio

1. Despierta → 0 = wake · Vacío dual ±1,2.  
2. Silba Vacío → arma trailing Oz 0,2 · masa $10 · CAZANDO.  
3. Extremo nuevo → Oz se mueve detrás (Bybit: Stop enmendado).  
4. Trailing detona → entrada SHORT/LONG · 0 = fill.  
5. Bifurcación: sangre 1,2 ($10) **o** Red 0,7 ($5 + trailing).  
6. Manos ON: StopOrder en la Oz del rastro + amend al moverse; si el cerebro detona sin fill, Market.

## Candados

| Flag | Default |
|------|---------|
| `BERU_RANGO_MANOS` | false |
| `BERU_RANGO_TRAILING_PCT` / `OZ_GAP` | 0.002 |
| `BERU_RANGO_SANGRE_PCT` | 0.012 |
| `BERU_RANGO_MASA_USD` | 10 |
| `BERU_RANGO_MASA_RED_USD` | 5 |

## Smoke / teatro

```powershell
python scripts/validar_beru_rango_smoke.py
python scripts/teatro_beru_rango.py --activo HYPE --dias 3 --abrir
```

— Shadow Army · Beru rango · Oz trailing Bybit —
