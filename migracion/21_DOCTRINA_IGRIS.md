# 21 — Doctrina Igris (escudo del manto)

**Estado:** mega-cirugía v1 **2026-08-12** — sueño+misión · solo Asalto · bocado asimétrico · §A sin piloto · MNT Santo no saco.  
**Dudas finas:** [`DUDAS_CIRUGIAS_MENORES_2026-08-12.md`](DUDAS_CIRUGIAS_MENORES_2026-08-12.md)  
**Código:** `generales/igris.py`, `core/igris_mision.py`, `core/igris_bocado.py`, `core/manto_ventana.py`, `core/pase_director.py`  
**Sellos:** [`DEBATE_SELLADO_ANATOMIA_IGRIS_2026-08-11.md`](DEBATE_SELLADO_ANATOMIA_IGRIS_2026-08-11.md) · intestinos PDF

---

## Rol

**Igris** = brazo del **manto** (derivados L/S). Por defecto **duerme**; el sargento encola **misiones** (sembrar / engordar / dormir / reducir-con-confirma). Ejecuta **directo en Bridge**.  
**Greed** = arbitraje Kaiser. No administra el manto.  
**Beru** = casa spot — después del manto.

---

## Ley Monarca — Igris ≠ Greed · solo Asalto (sello 2026-08-12)

1. **Oficio.** Igris acepta peaje y planta (Market Asalto). No caza edge.
2. **Marcha.** Solo **Asalto**. Personalizado fuera del Escudo (`IGRIS_SOLO_ASALTO`).
3. **Sueño.** `IGRIS_SUENO_MISION` — no detective cada segundo. Sargento auto arma misiones desde pase/Tusk.
4. **Dual.** Ambas piernas a la vez. Desigualdad chica → **siguiente bocado** (`IGRIS_BOCADO_ASIMETRICO`). Empate Market OFF; emergencia pierna muerta ON.
5. **§A oxígeno.** Solo lectura (`IGRIS_OXIGENO_PILOTO=false`). Poda auto OFF.
6. **Reducir.** Cableado; sin confirmación no ejecuta.
7. **Orden camino:** Igris → Beru cuando manto sirva → Greed último.

### MNT (2026-08-12, sellado en mega-cirugía ejército)

Santo del manto (`IGRIS_BOVEDA_EN_LOTE=true`): long inverso + short lineal.  
**No** es saco. Igris **no** reconstruye short de “bóveda”. Si queda short inverso = sucio (duda C1). Hedge obligatorio al arranque = **OFF**.

Detalle fechado anatomía: intestinos + debate sellado.

---

## §A — Umbrales margen — CONGELADO COMO PILOTO

| Margen usado | Fase | Igris |
|--------------|------|-------|
| cualquier | lectura | Aviso si ≥95%; **no** manda engorde/poda |

```
IGRIS_PODA_AUTO=false
IGRIS_OXIGENO_PILOTO=false
```

---

## Validación cirugía

- `python scripts/validar_igris_sueno_mision_smoke.py`
- `python scripts/validar_igris_smoke.py` (legado)
- `python scripts/validar_ley_masa_smoke.py`


---

## §C — Igris vs Greed — PARCIAL

| Decisión | Estado |
|----------|--------|
| ≥95%: Greed parado salvo **VIP/Mega VIP** (regalitos) | ✅ `filtrar_planes_ley_marcial` |
| Greed toca manto → Igris no rebalancea ~45s | ✅ `manto_touch` |
| Igris veta Greed desde margen > X | Pendiente |
| Mega VIP requiere OK Igris | Pendiente |
| SAFE_MODE: Igris sin engorde, sí poda | ❌ Contradice ley 2026-08-09 — poda auto OFF |
| Greed exento de ventana 48–52 | ❄️ Congelado — no abrir aún |

---

## §E — Armado del manto — PARCIAL (v2 + checkpoint 3.5.8c)

### Piernas
- **LONG** = inversos (USD) + futuros dated (rotación al vencer o si hay mejora).
- **SHORT** = lineales stable (USDT/USDC).
- Un activo (ej. SOL) puede tener **varias piernas** que se turnan con oportunidades Kaiser.

### Implementado v1 + v2
| Ítem | Estado |
|------|--------|
| Bootstrap inverse L + lineal S | ✅ `igris_manto.frentes_bootstrap` + `_bootstrap_manto` |
| `precio_medio` por pierna en `pesos` | ✅ `igris_manto.actualizar_promedio` vía Tusk fill |
| Baseline + fees en anclaje | ✅ `baseline_*` / `fees_paid_*` (2026-07-17) |
| Panel promedios | ✅ `igris.promedios_pierna` en `estado_vivo.json` |
| Jurisdicción manto Igris→Greed | ✅ `core/manto_jurisdiccion.py` |
| Puerta §E Ask/Bid + fees ± urgencia | ✅ `core/igris_despliegue.evaluar_puerta_se` |
| Reloj invertido Kaiser (paciencia) | ✅ `tau_paciencia_horas` / `factor_urgencia` |
| **Frecuencia manto 4 umbrales** (fees / ½ / tablas / morado) × plazos **50/40/10** | ✅ `core/manto_frecuencia.py` → tau + ranking + ETA marchas (2026-07-24) |
| Mordida = techo_misión × fracción(confianza) | ✅ sin pinza 85% ni tope 1% equity |
| Ancla en techo de liquidez | ✅ `techo_mision_usd` usa profundidad Ancla |
| Telemetría / Sub-Santuario Bridge | ✅ `telemetria_igris` + `igris_asset_details` |
| Live testnet despliegue | ✅ **3.10.7b** PASS_LIVE México |

---

### Checkpoint doctrina 3.5.8c — Ventana 48–52 / long-primero (2026-07-17)

**Estado:** doctrina **estipulada** + **motor v1 en código** (`core/manto_ventana.py`, 2026-07-17) · ranking (meta bloque, mitad engorde, Kaiser dual-book) = **aplazado a fusión**.

**Motor v1:** `MANTO_VENTANA_4852_ACTIVA` (default true) · banda fija **49–52%** operativa (hard 48–52) · rebalanceo/engorde long-primero en Igris · `igris.ventana_manto` en estado_vivo · smoke `scripts/validar_manto_ventana_smoke.py`.

#### Nombre provisional
**Ventana 48–52 / long-primero (por barco)** — paridad de manto con sesgo long.

#### Contabilidad del ratio (por barco = activo en mando, no global de cuenta)
1. El candado se mide en **dólares abiertos** (nocional USD de cada pierna).
2. Lineal (si Bybit cotiza en moneda): USD = `qty × precio_entrada` (nunca mark actual para empatar con lo abierto).
3. **Manda el inverso** para el ratio (Bybit piensa el inverso en dólares). El lineal se convierte y se muestra para auditoría.
4. Pergamino / Sub-Santuario: mostrar **USD + moneda en ambas piernas** + **sello de unidad de apertura** (`INVERSE→USD` / `LINEAR→COIN`), marca visual distinta.

#### Candado (crecimiento del manto)
| Regla | Valor |
|-------|--------|
| Meta ideal | ~**50/50**, acercarse lo más posible (50.1/49.9 long = prácticamente perfecto) |
| Techo long | **52%** — **duro** para Igris; no violar en expansión |
| Piso long | **48%** |
| Short gordo (long &lt; 50%) | más apretado: long no baja de **49%** → short ≤ **51%** |
| Ámbito | Solo fase de **crecimiento** por ahora; manto completo (solo mejorar entradas) = intención “52 sigue duro”, mecánica fina **después** (con ranking) |

**No es** la holgura vieja ±5% que se estrecha con margen 70→95. Esa lógica **deja de ser la ley** de equilibrio L/S (sustituir en código cuando se implemente este checkpoint).

#### Long-primero y corrección
- La intención: el **primer** desequilibrio favorezca **long**.
- En el **camino** hacia la meta del bloque (disparos chicos), puede haber momentos con short un poco arriba; al **llegar a la meta** → lo más cerca de 50/50 con ligera preferencia long.
- Short ligeramente mayor solo **por barco**, y solo si en ese barco ya hubo más USD long (corregir hacia 50/50).
- Cuanto más tiempo el manto esté desequilibrado, peor (sin timer aún — se revisa al desplegar).

#### Redondeo / mínimos de exchange
- Si una pierna no encaja por decimales/mínimos: **acoplar/recortar la pierna que cotiza en dólares** para no salir de 48–52.
- **Ley de la Masa (Monarca, 2026-08-06):** el contrato **Inverso jamás pelea con su mínimo aislado**. Alfa = mínimo real del **Lineal** (`max` fracción-en-USD, p.ej. 0.01 ETH, y piso ~$5). Esa **Masa Absoluta** obliga al Inverso a espejar el mismo USD. Si \|USD_L − USD_S\| / ref > **5%** → disparo **prohibido** (`LEY_MASA_BLOQUEO`). **Redondeo del espejo:** candidatos ceil/floor del Inverso; el más cercano al USD del Lineal gana; **ante la duda** (equidistantes / cercanía despreciable) → favorece al **long** (= Inverso; short = Lineal). El Lineal sigue mandando la masa absoluta — no se invierte la jerarquía. Código: `lote_bybit.ley_de_la_masa_dual` · puerta §E · `_disparo_dual_simultaneo` · smoke `scripts/validar_ley_masa_smoke.py` · flag `IGRIS_MASA_ASIMETRIA_MAX_PCT`.

#### Disparo dual
- Ante oportunidad: **ambas órdenes a la vez** (limit/limit, market/market o mix — da igual).
- No encadenar “espero fill de una y luego la otra” (el precio se mueve).
- Si una falla: **market inmediato** en la que falta; el chiste es llenar **ambas**.
- **Escalera de precios:** micro-bocados Limit a distintos niveles (`core/escalera_precios.py`); cancelar no llenos; equilibrar Market; manto parcial OK.
- **Lotes Bybit:** cada peldaño/orden respeta `minOrderQty` + `qtyStep` de la BD Jess (`core/lote_bybit.py` · `data/bybit_parametros_mercado.json`). Sync México **2026-07-21** en origin (`349b375`).
- **Frecuencia / paciencia (2026-07-24):** cuatro contadores en paralelo sobre historia `lineal_vs_inverse` — **fees** · **½ fees** · **tablas** (~0 edge / Asalto) · **morado** (`OPORTUNIDAD_MANTO`). Fusión de plazos: corto **50%** · mediano **40%** · anual **10%**. Alta frecuencia → más tau (espera) / sugerir **personalizado**; baja → **Asalto**. ETA solo para marchas operativas.
- **Marchas operativas (sello Monarca):** solo **asalto** (desplegar ya, peaje aceptado) y **personalizado** (el Monarca elige ~T; calib de umbral por par). **Fuera del altar:** `tactico` y `marcha_forzada` — al cargar/CLI se **normalizan a asalto** (sin reescritura agresiva de disco solo por lectura). Ritmo de lote queda legado/dormido. Default sin JSON/`MARCHA_DESPLIEGUE` = **asalto**.
- **Código:** `IgrisEscudo._disparo_dual_simultaneo` + `_salvavidas_market_pierna` · Greed `_ejecutar_dos_piernas` · flags `ESCALERA_*` / `IGRIS_DUAL_*`.
- Kaiser viendo order book dual a fondo: **revisar después** (metaverso / si ya vive).

#### Violación del candado (ej. long 53%)
- **Antes de la mitad** del engorde → corregir en la **siguiente** apertura.
- **Pasada la mitad** → corregir ya: cerrar lo excedido **o** abrir lo que falta, lo más conveniente.
- Definición exacta de “mitad” y meta USD del bloque → **cuando se cablee el ranking**.

#### Meta del bloque / ranking (aplazado — fusión del ejército)
- Ejemplo doctrinal (no números finales): Beru Mariscal ETH necesita X de **margen** → mitad long / mitad short de margen × apalancamientos máx → nocional grande.
- Rangos de **cuenta** Aspirante / Aprendiz / Brujo / Chamán: **firmados** en [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md) (2026-07-19). Lo pendiente es cablear meta de engorde Igris a ese pase (fusión ranking).
- Al completar meta de crecimiento: cerrar engorde; solo **mejorar entradas** dentro de la ventana (detalle con ranking).
- **No** cerrar 3.5.8c motor+ranking en una sola sesión: el Monarca aplazó H1–H4 (mitad, manto completo fino, corte ✅ exacto, nombre final) hasta fusionar ranking + Beru + Kaiser + Igris + Tusk.

#### Qué entra vs qué no (corte actual)
| Entra en doctrina 3.5.8c (checkpoint) | Aplazado al ranking / fusión |
|--------------------------------------|------------------------------|
| Ventana 48–52 / 49–51 short-gordo | Meta margen × leverage |
| Long-primero + corrección por barco | Definición “mitad del engorde” |
| USD@entrada + sello unidad | Mecánica fina manto completo |
| Dual simultáneo + market si falla una | ✅ v1 `_disparo_dual_simultaneo` + salvavidas (2026-07-19) · Kaiser dual-book a fondo pendiente |
| Sustituir banda-por-margen% como ley L/S | Greed exento 48–52 |
| | Timer por tiempo desequilibrado |

---

### Pendiente §E (resto)
| Ítem | Estado |
|------|--------|
| **3.5.8c motor** — ventana en Igris + smoke | ✅ v1 `manto_ventana` · ranking pendiente |
| Semáforos morado/gris (bloque B) | Pendiente (morado arena ✅) |
| Sangrado útil / margen económico | Pendiente |
| Ranking → meta USD manto | ✅ MVP `pase_director.meta_engorde_usd` → Igris bloque (2026-07-20) · mitad/manto-completo fino pendiente |

### En ~90% (zona ideal)
Igris sigue armando / rebalanceando con peaje aceptado y horizonte largo (mínimo orden, Ancla). La **caza fina** de entradas/salidas, slippage y spreads = oficio de **Greed** (después; ley 2026-08-06) — no pedir a Igris que “sea Greed”.

### Contabilidad
- Equilibrio por **promedio de entrada** y **USD@entrada** para el ratio, no tick/mark.
- **Margen económico** vs % exchange — no desinflar por falso >100%.
- Sangrado útil: si slippage mejora promedio, **aprovechar**, no podar.

### Semáforos (bloque B)
| Color | Significado | Código |
|-------|-------------|--------|
| V/A/R spot / huérfano / global | **No es de Igris** — es luz de **Greed** (cruzar lineal+spot o desvío vs marca Bybit). Checklist **3.7.P3** · *pausa con Greed mainnet* | — |
| **Morado** | Oportunidad L/S Ask/Bid (misma visión que Puerta §E) → **`OPORTUNIDAD_MANTO`** | ✅ arena micro / prod ≥ fees |
| **Gris/slippage** | Paridad rota temporal — falsa alarma, esperar | Pendiente |

**Regla de manto:** Igris solo arma activos con **inverse + lineal**. Sin inverse → fuera del Escudo.

Con `IGRIS_EVENT_DRIVEN=true` en `.env`, Igris **no escanea** cada segundo: solo actúa ante `OPORTUNIDAD_MANTO` o `MATRIZ_SPREAD` (lineal_vs_inverse) del activo en mando.

**Arena (prueba rápida):** `python scripts/arena_igris_aislado.py` — ojos mainnet, fills virtuales al Ask/Bid, sin Beru/Greed/rangos. Reporte: `data/arena_igris_report.json`.

### Deuda Greed ↔ Igris (limpieza hecha / por hacer)

| Ítem | Estado |
|------|--------|
| Handlers manto en Greed | ✅ eliminados — solo Igris→Bridge |
| Docs “Greed poda espejos” | ✅ corregidos |
| `IntencionAccion` manto | Legacy Beru — no cola activa |
| Ancla + despliegue §E | ✅ `igris_despliegue.py` (2026-07-12) |
| `pesos` + precio medio por pierna | ✅ v1 `igris_manto.py` |
| Bootstrap inverse L + lineal S | ✅ v1 |
| Ventana 48–52 / long-primero | ✅ motor v1 2026-07-17 · meta pase MVP 2026-07-20 · mitad fina pendiente |
| Live testnet despliegue | ✅ **3.10.7b** PASS_LIVE México (ETH/BTC dual DEMO) |
| Arena aislada (fills virtuales) | ✅ **3.10.7a** `arena_igris_aislado.py` |
| Event-driven Kaiser→Igris | ✅ **3.10.8** `IGRIS_EVENT_DRIVEN` |

---

## Otros bloques

| Bloque | Tema |
|--------|------|
| **B** | Semáforos spot + morado + slippage paridad |
| **D** | Funding → maniobra vs aviso; Ancla antes engorde |
| **F** | Vol 0.04 / fuga 1.5%; escalera R03 |

---

## Validación

- `python scripts/validar_igris_smoke.py`
- `python scripts/validar_igris_asset_detail_smoke.py`
- `python scripts/arena_igris_aislado.py` — arena morado + fills virtuales (recomendado antes de live)
- `python scripts/validar_greed_manto_smoke.py`
- Live manto testnet (**3.10.7b**)
