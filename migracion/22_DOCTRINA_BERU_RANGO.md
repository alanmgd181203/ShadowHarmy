# 22b — Doctrina Beru rango (trailing de activación)

**Estado:** sellado Monarca **2026-08-22** · Vacío/Red/Sangre nacen $5 · engorde desde activación · techo meta−ya  
**Referencia:** Beru spot (`22_DOCTRINA_BERU.md`) = fósil · no se mezcla.

## Veredicto

Todo el molino es **trailing stop**:
- **Activación** = precio donde el rastro se enciende
- **Callback 0,2 %** = distancia que persigue (Oz)

**0 absoluto = wake** (no se mueve con Oz ni fill).  
**Fill = plata (Tusk)** · **Peldaño Oz = mapa (Red)**.  
**Nacimiento = $5** en Vacío, Red y Sangre.  
**Engorde = +$1 / 0,1 % solo desde el precio de activación** (no recontar el camino desde wake).  
**Techo del saco = meta − ya en el lado** (anti-stack: no volver a meter la profundidad entera).

## Geometría

| Pieza | Rol | Valor |
|-------|-----|------:|
| Wake / 0 | Referencia absoluta | precio al despertar |
| Vacío / sangre | **Activación** | ±**1,2 %** desde el **wake** |
| Oz | **Callback** | **0,2 %** detrás del extremo |
| Red | **Activación** | **0,7 %** desde **Oz desplegada** |
| Meta saco | Techo a profundidad | **$5 + $1 × peldaños 0,1 % desde wake** |
| Nacimiento Vacío / Red / Sangre | Lo que se arma al nacer | **$5** (o menos si el cupo es menor) |
| Engorde (todos) | Mientras CAZA | **+$1 / 0,1 % desde precio de activación** |
| Cupo Vacío / Red | Techo del tramo | **min(viva, meta − saco ya)** |
| Sangre gana | | **elimina** Red · arma trailing $5 |
| Misma vela | | **sangre primero** |

## Regla Red (fill vs peldaño)

- Ancla Red = **Oz desplegada**.
- Fill **peor** (hacia Red) → ancla = fill.
- Fill **mejor o igual** → mapa **no baja**.

## Oficio

1. Wake → **0 absoluto** · ledger saco LONG/SHORT = 0.  
2. Vacío → **$5** · trailing; si Oz sigue desde la activación, engorda (techo meta).  
3. Oz detona → suma masa al saco del lado · wake intacto · planta sangre + Red.  
4. Red → **$5** · engorde desde activación · cupo = meta − saco (si 0, no arma).  
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
| Vacío / sangre | 1,2 % | **2,4 %** |
| Oz callback | 0,2 % | **0,4 %** |
| Red | 0,7 % | **1,4 %** |
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

— Shadow Army · wake eterno · nace $5 · engorde desde activación · techo meta−ya · perfil normal|feria · flota multi —
