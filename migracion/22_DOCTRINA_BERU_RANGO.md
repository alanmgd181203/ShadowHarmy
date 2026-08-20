# 22b — Doctrina Beru rango (trailing de activación)

**Estado:** sellado Monarca **2026-08-20** · oficio **NUEVO** · manos/hilo **OFF**  
**Referencia:** Beru spot (`22_DOCTRINA_BERU.md`) = fósil · no se mezcla.

## Veredicto

Todo el molino es **trailing stop**:
- **Activación** = precio donde el rastro se enciende  
- **Callback 0,2 %** = distancia que persigue (Oz)  
Vacío y Red usan el mismo mecanismo; solo cambian activación y masa.

## Geometría

| Pieza | Rol | Valor |
|-------|-----|------:|
| Vacío / sangre | **Activación** | ±**1,2 %** desde el 0 (o desde la última Oz) |
| Oz | **Callback** del trailing | **0,2 %** detrás del extremo |
| Red | **Activación** de otro trailing | **0,7 %** mismo sentido desde la Oz |
| Callback Red | igual | **0,2 %** |
| Masa Vacío / sangre | | **$10** |
| Masa Red | | **$5** |
| Tras Oz | | 0 = fill · planta sangre 1,2 **y** Red act. 0,7 |
| Sangre gana | | **elimina** la Red que esperaba |
| Ladder | | Red→$5 repetible ambos lados |
| Vivos | | uno activo |

## Oficio

1. Wake → 0 local. Activaciones duales ±1,2.  
2. Toca activación Vacío → trailing ON (callback 0,2) · $10.  
3. Extremo nuevo → Oz persigue.  
4. Callback detona → SHORT (subía) o LONG (bajaba) · 0 = fill.  
5. Planta: sangre act. 1,2 contraria ($10) **y** Red act. 0,7 mismo sentido ($5 trailing).  
6. Toca Red act. → trailing $5 (callback 0,2). Tras fill otra vez sangre+Red.  
7. Toca sangre primero → trailing opuesto $10 y **cancela** Red pendiente.  
8. Manos ON: Stop en la Oz del rastro + amend; Market si el cerebro detona sin fill.

## Candados

| Flag | Default |
|------|---------|
| `BERU_RANGO_MANOS` | false |
| `BERU_RANGO_TRAILING_PCT` / `OZ_GAP` | 0.002 (callback) |
| `BERU_RANGO_VACIO_PCT` / `SANGRE` | 0.012 (activación) |
| `BERU_RANGO_RED_DESDE_OZ_PCT` | 0.007 (activación Red) |
| `BERU_RANGO_MASA_USD` | 10 |
| `BERU_RANGO_MASA_RED_USD` | 5 |

## Smoke / teatro

```powershell
python scripts/validar_beru_rango_smoke.py
python scripts/teatro_beru_rango.py --activo HYPE --dias 3 --abrir
```

— Shadow Army · Beru rango · activación + callback · Red también trailing —
