# 22b — Doctrina Beru rango (trailing de activación)

**Estado:** sellado Monarca **2026-08-22** · Vacío/Red/Sangre nacen $5 · engorde desde activación · **escalera sin tope** (2026-08-23)  
**Referencia:** Beru spot (`22_DOCTRINA_BERU.md`) = fósil · no se mezcla.  
**Mar OKX:** `23_DOCTRINA_BERU_OKX.md` (default desde 2026-08-31).

## Veredicto

Todo el molino es **trailing stop**:
- **Activación** = precio donde el rastro se enciende
- **Callback 0,2 %** = distancia que persigue (Oz)

**0 absoluto = wake** (no se mueve con Oz ni fill).  
**Fill = plata (Tusk)** · **Peldaño Oz = mapa (Red)**.  
**Nacimiento = $5** en Vacío, Red y Sangre.  
**Engorde = +$1 / 0,2 % solo desde el precio de activación** (no recontar el camino desde wake).  
**Ledger saco** = bitácora LONG/SHORT (panel · teatro) — **no frena** Vacío ni Red.

## Geometría

| Pieza | Rol | Valor |
|-------|-----|------:|
| Wake / 0 | Referencia absoluta | precio al despertar |
| Vacío (semilla) | **Activación** | ±**1,2 %** desde el **wake** |
| Sangre (post-Oz) | **Activación** | ±**1,2 %** desde el **peldaño Oz** (lado contrario) |
| Oz | **Callback** | **0,2 %** detrás del extremo |
| Red | **Activación** | **0,7 %** desde **Oz desplegada** (LONG=SHORT simétrica) |
| Meta saco | Referencia a profundidad | **$5 + $1 × peldaños 0,2 % desde wake** (informativa) |
| Nacimiento Vacío / Red / Sangre | Lo que se arma al nacer | **$5** |
| Engorde (todos) | Mientras CAZA | **+$1 / 0,2 % desde precio de activación** |
| Sangre gana | | **elimina** Red · arma trailing $5 |
| Misma vela | | **sangre primero** |

## Regla Red (fill vs peldaño)

- Ancla Red = **Oz desplegada**.
- Fill **peor** (hacia Red) → ancla = fill.
- Fill **mejor o igual** → mapa **no baja**.

## Oficio

1. Wake → **0 absoluto** · ledger saco LONG/SHORT = 0.  
2. Vacío → **$5** · trailing; si Oz sigue desde la activación, engorda.  
3. Oz detona → suma masa al saco del lado · wake intacto · planta sangre (1,2 % del peldaño Oz, contraria) + Red (**0,7 %** simétrica del mismo ancla).  
4. Red → **$5** · engorde desde activación · **siempre puede re-armar** (saco no corta) · al cosechar Oz otra vez, la sangre **renace** junto al nuevo peldaño (no se queda en el wake).  
5. Sangre → **$5** · engorde desde activación · mata Red.  
6. Manos ON: Stop Oz + amend; Market si hace falta.

## Candados

| Flag | Default |
|------|---------|
| `BERU_RANGO_PERFIL` | `normal` (o `feria` · `piedra`) |
| `BERU_RANGO_MASA_USD` / `MASA_RED` / `MASA_SANGRE` | 5 |
| `BERU_RANGO_ENGORDE_USD` | 1 |
| `BERU_RANGO_ENGORDE_PASO_PCT` | 0.002 (normal y feria) |
| `BERU_RANGO_MANOS` | false |

### Perfil feria (paralelo — monedas violentas)

No sustituye al normal. Checkpoint del canónico: `data/beru/rango/checkpoint_doctrina_normal.json`.

| Pieza | Normal | Feria |
|-------|-------:|------:|
| Vacío (semilla) / sangre (post-Oz) | 1,2 % | **2,2 %** |
| Oz callback | 0,2 % | **0,2 %** (misma distancia que normal; oreja en vacío/red) |
| Red | 0,7 % | **1,2 %** (simétrica) |
| Engorde | +$1 / 0,2 % | +$1 / **0,2 %** |
| Nacimiento | $5 | $5 |

```powershell
$env:BERU_RANGO_PERFIL = "feria"
python scripts/validar_beru_rango_feria_smoke.py
```

### Perfil piedra (OKX micro — 2026-08-31)

Misma alma clásica del rango, masa fina para USDT-SWAP OKX. **Una sola orden** que enmienda; engorde **peldaños sumados** ($0,20 + $0,21 + … por cada 0,1 %).

| Pieza | Piedra |
|-------|-------:|
| Vacío / sangre | ±1,2 % (sangre **desde última Oz** tocada, no wake) |
| Oz callback | 0,2 % |
| Red LONG / SHORT | 0,7 % / **0,8 %** |
| Nacimiento | **$0,20** (peldaño 1 de la serie) |
| Engorde | **serie sumada** (+$0,01 al peso de cada peldaño) |
| Oz-0 engorde | **última Oz** del movimiento contrario (recetea ancla) |

Ejemplo: 10 peldaños (≈1 %) → **$2,45** en la Oz; +0,1 % → **$2,75**; Red con offset 10 en peldaño 15 → **$1,60**.

**Manos (floor + cola):** qty en fracción **inferior** (`lotSz`); deuda = doctrina − notional. La cola se suma al siguiente objetivo; al **tocar sangre inverso** se **borra** (ciclo nuevo).

#### Semáforo por Santo (rojo / amarillo / verde)

Asignación en `data/beru/rango/piedra_asignacion.json` (teatro/ranking llena `activos`). Sin entrada → **`BERU_RANGO_SEMAFORO`** (default **amarillo**).

| Color | Nacimiento (paz) | Tope engorde / 0,1 % |
|-------|-----------------:|---------------------:|
| Rojo | $0,20 | $0,50 |
| Amarillo | $0,30 | $0,80 |
| Verde | $0,50 | $1,00 |

#### Bando de pierna (condicional sobre pierna viva)

Pierna viva = max(saco LONG, saco SHORT) + masa del tramo cazando. Al **armar** Vacío / Red / Sangre se recalcula bando y masa nacimiento:

| Pierna USD | Rojo | Amarillo | Verde |
|------------|-----:|---------:|------:|
| &lt; $100 (paz) | $0,20 | $0,30 | $0,50 |
| $100–$300 (medio) | $0,20 | $0,25 | $0,30 |
| &gt; $300 (pesado) | $0,20 | $0,20 | $0,20 |

**Histéresis 80 %** al evolucionar de vuelta: tras involución en $100 → paz si pierna ≤ $80; tras $300 → medio si pierna ≤ $240. Se registra precio al cruzar umbral (`pierna_px_involucion`).

Al llegar al **tope por peldaño** (0,1 %), ese escalón deja de subir el peso de la serie (no congela la orden entera). Smoke de geometría pura puede usar `BERU_RANGO_PIEDRA_SIN_TOPE=1` (solo laboratorio).

```powershell
$env:BERU_RANGO_PERFIL = "piedra"
$env:BERU_RANGO_SEMAFORO = "amarillo"   # o rojo / verde
python scripts/validar_beru_rango_piedra_smoke.py
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

— Shadow Army · wake eterno · nace $5 · engorde desde activación · Red 0,7 % simétrica · escalera sin tope · perfil normal|feria · flota multi —
