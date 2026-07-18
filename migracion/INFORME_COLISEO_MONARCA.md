# Informe del Coliseo — Beru Fantasma (para el Monarca)

**Fecha:** 2026-07-18 (Fase 1 fijada)  
**Qué es:** teatro con la bóveda histórica para elegir **vacío Adán** y **activos** sin soltar Beru a Bybit.

---

## Orden de batalla (lo que firmaste)

**Fase 1 — ahora (una perilla a la vez)**  
1. Encontrar el **vacío más eficiente** (desde **0,8 %** hasta 2,0 %; ya no 0,6 %).  
2. Ver qué **activos** ganan (calor / semáforos).  
3. Cascada de tiempo: **1 día → 7 días → 30 días → año**.  
4. Tras el día/semana: quédate solo con el **top** y no gastes el año en barcos que ya perdieron en todo.

**Fase 2 — después (no mezclar aún)**  
- Ensanchamiento oz/red (0,2 % / 0,1 %)  
- Sub-Berus Soldado…Mariscal  
- Legión / fusiones / Mega  

De nada sirve mil simulaciones de un año en un activo que ya es peor que los primeros.

---

## Qué hace el Fantasma hoy (Fase 1)

- Un Beru tipo **Mariscal** por activo (caza + negociador + ciclo).  
- Engorde **+$5 / 0,1 % sin techo** de $50.  
- Fees 0,1 %/pierna · slip 2 bps · calor 20/50/30.  
- **No** fusiones, **no** malla doble, **no** tiers chicos.

---

## Cómo correrlo (cascada)

```text
# 1) Smoke de 1 día — toda la flota, todos los vacíos 0.8…2.0
python scripts/coliseo_beru_fantasma.py --dias 1 --top 8

# 2) Mira data/coliseo/comparativa_vacios.md y top_activos_siguiente.txt
#    Luego 7 días solo con el top:
python scripts/coliseo_beru_fantasma.py --dias 7 --only BTC,ETH,... 

# 3) Mes, luego año — mismo --only (poda)
python scripts/coliseo_beru_fantasma.py --dias 30 --only ...
python scripts/coliseo_beru_fantasma.py --dias 365 --only ...
```

El script te imprime un **comando sugerido** para el siguiente horizonte.

Más rápido (menos castigo de camino): `--path-policy ohlc`

---

## Dónde mirar resultados

- `data/coliseo/comparativa_vacios.md` — vacío dorado de esa pasada + ranking de activos  
- `data/coliseo/top_activos_siguiente.txt` — lista para `--only`  
- `ranking_h1d_v1p2.md` etc. — detalle por vacío

---

## Engorde

**+$5 / 0,1 %** libre (sin techo $50). Único freno en vivo: oxígeno Tusk.

---

## Siguiente del camino

Terminar Fase 1 (vacío + top activos en cascada).  
Solo entonces Fase 2 (malla ancha / sub-Berus / legión).
