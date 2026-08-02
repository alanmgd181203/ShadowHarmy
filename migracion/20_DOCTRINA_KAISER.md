# 20 — Doctrina Kaiser (vocero interno)

**Estado:** acordado con el Monarca — 2026-07-05  
**Implementación manos:** Greed + **VIP/Mega VIP** cableados — ver §VIP abajo.  
**Código actual:** `generales/kaiser.py`, perfiles 3d/1m/1a, metaverso, **Ancla** (`core/ancla.py`) — ojos + digest; **sin disparos Greed**.

---

## §0 — Ancla de Realidad (liquidez orderbook) — CERRADO + IMPLEMENTADO

**Primer filtro** — antes de perfiles, calor y tendencias.

| Concepto | Definición |
|----------|------------|
| **Entrada máxima** | Techo USD que el **orderbook visible** (Bybit WS `orderbook.50`) permite llenar recorriendo niveles |
| **Entrada segura** | Hint opcional para **Greed** (fracción del muro, latencia, Tank) — **no** filtra alertas Kaiser |
| **Alerta** | `OPORTUNIDAD_LIQUIDEZ` — spread + max $ + neto % + fees % + pipe ms — destinatarios **GREED, BELLION** |
| **Abort** | `OPORTUNIDAD_ABORTADA` si la oportunidad muere antes de Greed (TTL pipeline, Tank ROJO, neto &lt; fees, spread cayó) |

### Reglas Kaiser → Greed (alerta)

1. Libro vivo + spread &gt; 0 (`ANCLA_UMBRAL_SPREAD_PCT=0` — no umbral fijo 0.15%)
2. `entrada_maxima_usd` ≥ mínimo orden del cruce (`MIN_ORDER_USD_BY_FRENTE`)
3. `regalo_neto_pct` ≥ `fees_total_pct` × `ANCLA_NETO_MIN_VS_FEES` (default 1.0 = ganamos al menos lo pagado en fees)
4. Spread estable en ventana pipeline (no colapsó &gt;35% vs histórico corto)
5. `pipeline_ms` ≤ `PIPELINE_MAX_MS` (500 ms default, Tokio ~100–500 ms)
6. Tank no ROJO

**Greed** decide tamaño final (perfiles, calor, vetos); la “segura” vive ahí.

### Pipeline (`core/kaiser_pipeline.py`)

- `estimar_pipeline_ms()` — latencia Tank + cálculo Kaiser + margen Greed/ejecución
- `RastreadorSpread` — historial spread por base:tipo
- `ColaOportunidadesGreed` — TTL, revalidación, abort antes de ejecución
- Kaiser expone `cola_greed_viva()`, `oportunidades_abortadas()`, `consumir_greed()`

### Capas

1. **Ancla (`core/ancla.py`)** — walk-the-book, fees, simulación dos piernas (USDT/USDC, spot/perp…)
2. **Kaiser** — `interpretar_ancla_liquidez`, `consultar_liquidez(intencion)` para generales
3. **Greed** — decide después con perfiles/vetos; **no cableado** aún

### Consulta por intención

Beru / Igris / Greed pueden preguntar: `{ masa, frente | frente_compra+venta }` → respuesta **max** + hint segura + `masa_viable` (≤ max y ≥ min par).

**Validar:** `python scripts/validar_ancla_smoke.py`

**Pendiente:** pierna Binance depth para huérfanas (hoy solo best bid/ask).

**Mínimo orden par:** `min_order_usd` por frente desde Trinidad/Bybit; alerta solo si `entrada_maxima_usd` ≥ mínimo del cruce.

---

## Rol en el ejército

```
Tank     → recoge (precios, matriz, índice, funding)
Kaiser   → interpreta, etiqueta, rankea rutas — NO ejecuta
Greed    → arbitraje / regalo / global / huérfanas (primero en cablearse)
Beru     → caza local — después, misma filosofía probabilística
Igris    → manto / margen local — index Bybit + rails casa
Karmish  → mundo externo — PAUSA doctrinal
Capitanes → táctica Beru pentiverso — no reemplazados por Kaiser
```

---

## §1 — Ancla de precio (“precio global”) — CERRADO

### Qué es index price (Bybit)

Precio de **referencia multi-exchange** que Bybit calcula promediando spot en varios exchanges. No es el last del perp ni necesariamente el spot USDT de Bybit. Sirve para medir si el **perp está caro o barato vs el consenso del mercado**.

### Checkpoint Monarca 2026-08-02 — índice absoluto + sesgo estructural

**Dirección firmada (doctrina):** el índice Bybit es la **referencia absoluta** del pentiverso. Kaiser etiqueta el **sesgo histórico** de cada mar vs índice (`sesgo_estructural` en digest — 3.8.P5).  
Detalle: [`CHECKPOINT_KAISER_INDICE_SESGO.md`](CHECKPOINT_KAISER_INDICE_SESGO.md). Smoke: `python scripts/validar_kaiser_sesgo_smoke.py`.

### Quién usa qué ancla

| General | Ancla principal | Global (Binance / multi) |
|---------|-----------------|---------------------------|
| **Igris** | Index **Bybit** + spot/perp **locales** (USDT/USDC, muros) | Solo **contexto** o veto — no gatillo |
| **Beru** | Idem — **mejor rail local** (ej. LTC USDT vs USDC: importa cuál conviene en casa, no si ambos están 1–2¢ bajo el mapa global) | Idem |
| **Greed** | Spreads **ejecutables** + index | **Sí** — core en huérfanas y metaverso |
| **Huérfanas** | Sin spot Bybit → **global obligatorio**: Binance primero; luego otros books | Kaiser marca stale / SIN_BINANCE |

**Regla:** situaciones “normales” en trinidad/pentiverso = optimización **intra-Bybit**. Greed es quien **toma riesgo entre mares/exchanges**.

**Semáforos matriz (3.7.P1 ✅):** `indicadores.matriz_luces` en digest — VERDE &lt; umbral · AMARILLO ≥ umbral · ROJO ≥ 2× · **sin órdenes**.

**3.7.P3 (pausa):** luz aliado spot / huérfano / panorama global → **Greed**, no Igris. Igris solo manto con inverse.

---

## §2 — Perfiles multietiqueta (3d / 1m / 1a) — CERRADO

### Jerarquía de plazos

| Plazo | Ventana | Rol |
|-------|---------|-----|
| **Corto** | ~3 días | Acompaña al mediano — puede ser ruido temporal |
| **Mediano** | ~1 mes | **Manda** (preferente) |
| **Largo** | ~1 año | Sobreconfirma — mercado viejo puede no aplicar al presente |

- **Largo plazo no manda** sobre mediano/corto.
- Regla “2 de 3 plazos” → **no es regla fija aún**; habrá más indicadores. A veces **corto + otras señales** puede imponerse a mediano/largo.

### Sin datos

- **`DATOS_INSUFICIENTES` → no actuar** (equivalente a lanzar moneda).

### Calor y probabilidad (no binario)

- Tendencia a favor = **escala de calor** (0–100), no sí/no.
- Cerca del **extremo** en **los tres plazos alineados** (ej. ~90–100% un lado y ~0–10% el otro) → **veto fuerte** al lado débil (ej. short = humo total).
- Si **no** hay extremo alineado en los tres → **no veto total**; “puede, con cautela y tamaño”.

### Beru en este paquete

- Foco actual: **Greed**. Beru usará **varios indicadores** después; misión: **morder más, pagar/perder menos**.
- Beru **no entra** en la implementación Kaiser→Greed de la primera oleada, pero comparte filosofía probabilística.

### Memoria de barcos (vivo — 2026-07-19)

Kaiser **no olvida** el grial tras el Coliseo: cada hora (default) toma lo que **Tank ya calcula** (matriz, desvío, funding, semáforo) y lo **añade al diario** de cada barco en `data/kaiser/memoria/{BASE}.jsonl`.

| Pieza | Rol |
|-------|-----|
| `core/kaiser_memoria_barcos.py` | Append horario + trim + alertas de pulso |
| Digest `memoria_barcos` | Resumen en `estado_vivo.kaiser` → Pergamino |
| Alertas `GRIAL_PULSO` / `CANDIDATO_PULSO` | Salto vs hora anterior; candidato fuera de los 13 Santos |
| Coliseo Mega | Sigue siendo el **juicio** del pase; la memoria es el **pulso continuo** |

**No** re-corre el Mega cada hora. Si un candidato insiste en el pulso → ritual Coliseo ligero / revisión del grial (Monarca).

Knob: `KAISER_MEMORIA_INTERVAL_S` (3600) · umbral Δ `KAISER_MEMORIA_DELTA_UMBRAL_PCT`.

### Rutas y tamaño (Greed)

- **Regla dura:** solo actuar si la **ruta completa** (cruces, fees, slippage) deja **neto positivo** en teoría.
- Perfiles **dudosos / más riesgo** → **entrada pequeña**, escalar de a poco.

### Pipeline Kaiser → Greed (cuando se implemente)

0. **Ancla:** ¿Libro vivo? ¿entrada segura > mínimo? No → STOP  
1. ¿Hay datos perfil? No → STOP (solo Ancla informa)  
2. ¿Mediano (+ corto alineado) dan dirección y calor?  
3. ¿Tres plazos en extremo mismo sentido? → veto lado opuesto; si no → cautela  
4. ¿Ruta idónea neto > 0 (Ancla, no constantes)? No → STOP  
5. ¿Calor bajo / dudoso? → tamaño ≤ entrada segura, escalar si confirma  

---

## §3 — Huérfanas vs metaverso — CERRADO (Greed)

- **Siempre** buscar ruta idónea (`metaverso.ruta_idonea`) antes de morder.
- Huérfana sin perfil: fracción máx **30%** del techo; rebalancear con calor/clima/ruta.
- Ruta con neto ≤ 0 → no actuar.

### Multicruce spot (2026-07-05) — v1 parcial

**Greed** ejecuta rutas **3–4 piernas** cuando el directo `base/USDT` diverge del sintético vía **USDC**, **MNT** o **EUR** (puente USDC→EUR).

| Módulo | Rol |
|--------|-----|
| `core/greed_multicruce.py` | Detecta spread + arma piernas |
| `core/spreads.py` | Inyecta filas en matriz Tank |
| `core/ancla.py` | Liquidez mínima por pierna |
| `generales/greed.py` | `_ejecutar_piernas` secuencial |

**Beru** no hace multicruce — elige rail stable local (`core/beru_rail.py`).

Validar: `python scripts/validar_greed_multicruce_smoke.py`

### Visión Greed omnimercado — PENDIENTE (Monarca 2026-07-05)

Greed debe cruzar **todo el universo Tank** (≈598 spot + perps + inverse + futuros dated), no solo un subconjunto de bases.

| Capa | Estado | Descripción |
|------|--------|-------------|
| Matriz 2 piernas | ✅ | `spot_vs_perp`, `lineal_vs_inverse`, `usdt_vs_usdc`, `perp_vs_index` |
| Multicruce spot 3–4p | ✅ v1 | USDC/MNT/EUR vía `greed_multicruce` |
| Scan todas las bases spot | 🟡 | Bases desde `SPOT_ALL_PARES` + `KAISER_SPOT_ALL_CAP` |
| Rutas mixtas spot+perp | ✅ v1 | `core/greed_basis.py` — entrada 2 piernas neutras |
| Manto temporal | ✅ v1 | Hold `spot_vs_perp` / `lineal_vs_inverse`; salida por spread/neto/timeout |
| Cola salida / hold | ✅ v1 | `_basis_estado` + `tusk.greed_basis_abiertos` + panel |

**Manto temporal (implementado v1):** `greed_basis.py` + rama `BASIS_HOLD` en `greed_mision.py`. Entrada cuando spread ≥ `GREED_BASIS_ENTRADA_SPREAD_MIN_PCT` y neto > fees; salida cuando spread ≤ `GREED_BASIS_SALIDA_SPREAD_MAX_PCT`, neto capturado ≥ objetivo, timeout o spread expande. Igris recibe `manto_touch` en cada ciclo del hold.

Validar: `python scripts/validar_greed_basis_smoke.py`

**Pendiente omnimercado:** grafo completo sobre todos `FRENTES_TANK`; rutas mixtas 3+ piernas spot+perp en una sola misión.

**Limpieza roles:** Greed **no** tiene CAZA/COSECHA/legión (Beru). Escuadrón suicida legacy **off** — duplica Kaiser.

---

## §4 — Quién consume qué — CERRADO (oleada actual)

| Destinatario | Estado |
|--------------|--------|
| **Greed** | `kaiser.consumir_greed()` — cola viva + alertas |
| **Beru / Igris** | **Fuera** de esta oleada |
| **Bellion** | Log + alertas |

---

## §6 — Indicadores y tamaño Greed — IMPLEMENTADO

`core/greed_sizing.py` + `core/greed_mision.py` + `generales/greed.py`

| Indicador | Peso default |
|-----------|--------------|
| Calor direccional | 25% (+ módulo sobre fracción) |
| Tags perfil | 25% |
| Consenso plazos | 20% |
| Calidad ruta | 15% |
| Clima (Tank/pipeline) | 10% |
| Manto (margen %) | 5% |

```
techo_real = min(Ancla, margen_libre×lev, 1% equity×lev)
mordida    = techo_real × fracción_indicadores
```

Config: `GREED_RIESGO_MAX_PCT_CUENTA=0.01`, `GREED_FRACCION_MAX=0.85`, `GREED_HUERFANA_SIN_PERFIL_FRACCION_MAX=0.30`

**Validar:** `python scripts/validar_greed_sizing_smoke.py`

---

## §7 — Gates de riesgo — CERRADO (Greed)

Pausa manos (Greed preparado); al normalizar, reintenta si oportunidad **VIVA**:

- Tank ROJO, SAFE_MODE, ley marcial (margen ≥ `MURO_LEY_MARCIAL`)
- Abort Kaiser → no disparar ese `oid`; si reaparece → nuevo intento
- Reintentos: `GREED_REINTENTO_COOLDOWN_S`

---

## §8 — Oxígeno Tusk — CERRADO (Greed)

- Tamaño capped por **equity UTA** (`masa_bruta_real`).
- **1% equity** máximo de margen en riesgo por misión (`GREED_RIESGO_MAX_PCT_CUENTA`).
- Apalancamiento por frente: `GREED_LEVERAGE_BY_FRENTE` / default 10× (spot 1×).
- Earn / plano 2–3: no cuenta para disparo.

---

## §6 (legacy umbrales) — Umbrales numéricos — PARCIAL

| Knob | Uso |
|------|-----|
| Desvío mínimo % | Evento perfil + alerta |
| Spread matriz mínimo % | Cola Greed |
| Regalo neto mínimo % | Ruta ejecutable |
| Funding \|rate\| | Alerta Igris |
| Cooldown por base | Anti-spam |
| **Escala de calor** 0–100 | Derivar de métricas perfil — **definir fórmula** |

Distintos umbrales huérfana vs trinidad — por acordar.

---

## §VIP — Pase VIP / Mega VIP — IMPLEMENTADO

`core/greed_vip.py` + `generales/greed.py`

| Banda | Neto ruta metaverso | Margen máx | Ejecución |
|-------|----------------------|------------|-----------|
| Normal | &lt; 0.5% | 1% equity | Mordida única (perfil + calor) |
| **VIP** | ≥ **0.5%** | 1% equity | 3 micros al **min_order** → escalar si neto ≥ 0.5% |
| **Mega VIP** | ≥ **1%** | **5%** equity *tras* 3 sondas OK | Mismo escalado, techo ×5 |

- Salta **perfil**; no salta Ancla ni vetos Tank/SAFE/ley marcial.
- Primera micro falla (humo) → **abort** resto de la misión.
- Neto cae &lt; `GREED_VIP_NETO_CONTINUAR_PCT` (0.5%) → STOP.
- Abort Kaiser en `oid` → limpia misión VIP.

Config: `GREED_VIP_NETO_MIN_PCT`, `GREED_MEGA_VIP_NETO_MIN_PCT`, `GREED_MEGA_VIP_RIESGO_MAX_PCT=0.05`, `GREED_VIP_SONDAS_MIN=3`

**Validar:** `python scripts/validar_greed_vip_smoke.py`

---

- Lag mínimo Convert vs spot para raid Greed.  
- REST 403/geo: ¿degradar confianza global Kaiser?

---

## §10 — Karmish — PAUSA

Nada de Karmish en disparos hasta orden explícita del Monarca.

---

## §11 — Escalada Monarca — POR RESOLVER

- ¿Solo ALERTA a Telegram?  
- ¿AVISO en huérfanas top?  
- ¿Resumen diario perfiles/rutas?

---

## Orden sugerido de pláticas

1. ~~§1 Ancla precio~~ ✅  
2. ~~§2 Perfiles~~ ✅  
3. ~~§3 Huérfanas vs metaverso~~ ✅  
4. ~~§6–§8 Greed sizing~~ ✅  
5. ~~**Pase VIP**~~ ✅  
6. §9 Convert y REST  
5. §4–§5 Greed vs Beru vs Capitanes  
6. §7 Gates + §8 Oxígeno UTA  

---

## Referencia código (sin disparos)

- Perfiles: `core/kaiser_perfil.py`
- Frecuencia manto (Igris): `core/manto_frecuencia.py` — 4 umbrales fees/½/tablas/morado · pesos 50/40/10 · muestras `lineal_vs_inverse` flota · tau + panel
- Sampler: `kaiser_sampler` incluye flota manto para arista L/S
- Rutas: `core/metaverso_grafo.py`
- Digest: `generales/kaiser.py` → `estado_vivo.kaiser` (+ `frecuencia_manto`)
- Checklist: `16` §3.8.P1 · **3.5.8b2**

*Actualizar este doc al cerrar cada §. Override codex: frase explícita del Monarca.*
