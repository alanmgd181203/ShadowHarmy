# 22b — Doctrina Beru rango (trailing de activación)

**Estado:** sellado Monarca **2026-08-22** · Vacío/Red/Sangre nacen $5 · engorde desde activación · **escalera sin tope** (2026-08-23)  
**Referencia:** Beru spot (`22_DOCTRINA_BERU.md`) = fósil · no se mezcla.

## Veredicto

Todo el molino es **trailing stop**:
- **Activación** = precio donde el rastro se enciende
- **Callback 0,2 %** = distancia que persigue (Oz)

**0 absoluto = wake** (no se mueve con Oz ni fill).  
**Fill = plata (Tusk)** · **Peldaño Oz = mapa (Red)**.  
**Nacimiento = $5** en Vacío, Red y Sangre.  
**Engorde = +$1 / 0,1 % solo desde el precio de activación** (no recontar el camino desde wake).  
**Ledger saco** = bitácora LONG/SHORT (panel · teatro) — **no frena** Vacío ni Red.

## Geometría

| Pieza | Rol | Valor |
|-------|-----|------:|
| Wake / 0 | Referencia absoluta | precio al despertar |
| Vacío (semilla) | **Activación** | ±**1,2 %** desde el **wake** |
| Sangre (post-Oz) | **Activación** | ±**1,2 %** desde el **peldaño Oz** (lado contrario) |
| Oz | **Callback** | **0,2 %** detrás del extremo |
| Red LONG | **Activación** | **0,7 %** desde **Oz desplegada** |
| Red SHORT | **Activación** | **0,8 %** desde **Oz desplegada** (aire vs sesgo del %) |
| Meta saco | Referencia a profundidad | **$5 + $1 × peldaños 0,1 % desde wake** (informativa) |
| Nacimiento Vacío / Red / Sangre | Lo que se arma al nacer | **$5** |
| Engorde (todos) | Mientras CAZA | **+$1 / 0,1 % desde precio de activación** |
| Sangre gana | | **elimina** Red · arma trailing $5 |
| Misma vela | | **sangre primero** |

## Regla Red (fill vs peldaño)

- Ancla Red = **Oz desplegada**.
- Fill **peor** (hacia Red) → ancla = fill.
- Fill **mejor o igual** → mapa **no baja**.

## Oficio

1. Wake → **0 absoluto** · ledger saco LONG/SHORT = 0.  
2. Vacío → **$5** · trailing; si Oz sigue desde la activación, engorda.  
3. Oz detona → suma masa al saco del lado · wake intacto · planta sangre (1,2 % del peldaño Oz, contraria) + Red (**LONG 0,7 %** / **SHORT 0,8 %** del mismo ancla).  
4. Red → **$5** · engorde desde activación · **siempre puede re-armar** (saco no corta) · al cosechar Oz otra vez, la sangre **renace** junto al nuevo peldaño (no se queda en el wake).  
5. Sangre → **$5** · engorde desde activación · mata Red.  
6. Manos ON: Stop Oz + amend; Market si hace falta.

## Candados

| Flag | Default |
|------|---------|
| `BERU_RANGO_PERFIL` | `normal` (o `feria`) |
| `BERU_RANGO_MASA_USD` / `MASA_RED` / `MASA_SANGRE` | 5 |
| `BERU_RANGO_ENGORDE_USD` | 1 |
| `BERU_RANGO_ENGORDE_PASO_PCT` | 0.001 (normal) · 0.002 (feria) |
| `BERU_RANGO_MANOS` | false |

### Perfil feria (paralelo — monedas violentas)

No sustituye al normal. Checkpoint del canónico: `data/beru/rango/checkpoint_doctrina_normal.json`.

| Pieza | Normal | Feria |
|-------|-------:|------:|
| Vacío (semilla) / sangre (post-Oz) | 1,2 % | **2,4 %** |
| Oz callback | 0,2 % | **0,4 %** |
| Red LONG | 0,7 % | **1,4 %** |
| Red SHORT | 0,8 % | **1,6 %** |
| Engorde | +$1 / 0,1 % | +$1 / **0,2 %** |
| Nacimiento | $5 | $5 |

```powershell
$env:BERU_RANGO_PERFIL = "feria"
python scripts/validar_beru_rango_feria_smoke.py
```

## Smoke / teatro / flota

```powershell
# Sanidad (sin despertar)
python scripts/preparar_beru_rango_ejercito.py

# Teatro de sombras (bóveda, ranking nuevo Beru)
python -u scripts/teatro_beru_rango_juicio.py --perfil reciente

# Ojos multi — un Bridge HTTP/WS por Santo (no una boca por todos)
python scripts/arise_beru_rango_ojos.py --santos A,B,C

# Manos — un Santo, solo con GO explícito
python scripts/arise_beru_rango_manos.py --activo X --manos-go
```

**Arquitectura flota ojos:** cada Santo = Bridge propio + Tank propio + pulso propio. El panel fusiona; no hay fila única hablando por todos.

— Shadow Army · wake eterno · nace $5 · engorde desde activación · Red LONG 0,7 / SHORT 0,8 · escalera sin tope · perfil normal|feria · flota multi —
