# 22 — Doctrina Beru (caza spot + capital manto + ProtoBeru)

**Estado:** Monarca 2026-07-09 · **ley vivo 2026-08-11** · **molino 2026-08-12**  
**Código:** `generales/beru.py`, `core/beru_ley.py`, `core/beru_wake.py`, `core/beru_cazador.py`, …  
**Dudas finas:** [`DUDAS_CIRUGIAS_MENORES_2026-08-12.md`](DUDAS_CIRUGIAS_MENORES_2026-08-12.md)

---

## Ley dura (Monarca — no negociable)

1. **Beru no toca el margen.** 0 % margen extra. No abre piernas de futuros ni suma IM.
2. **Solo intercambia spot:** lo que una pierna gana ↔ lo que la otra pierde (acordeón sobre manto que ya plantó Igris).
3. **No engorda.** Sin +G_min de frontera, sin capas nuevas de masa, sin crecer inventario “a costa del oxígeno”. (`BERU_ENGORDE_PERMITIDO=false`)
4. **Abortar solo si está ciego:** sin precio / Tank en coma muchos segundos — no por ROJO ligero de latencia. (`BERU_ABORTAR_SOLO_CEGUERA`)
5. **Wake = Mega-reset del 0** al precio actual · flota · Normal **1,6 %** · manos OFF hasta orden.
6. **Molino (2026-08-12):** spot margen ON (permiso Bybit al 95 %). No pregunta si hay USDT. No descansa mientras haya manto. No planta futuros. Manos/hilo **OFF** hasta orden (cirugía ≠ despertar).

Detalle: [`CHECKPOINT_BERU_LEY_NEUTRO_2026-08-11.md`](CHECKPOINT_BERU_LEY_NEUTRO_2026-08-11.md) · wake [`CHECKPOINT_BERU_WAKE_RESET0_2026-08-11.md`](CHECKPOINT_BERU_WAKE_RESET0_2026-08-11.md) · ejército [`CHECKPOINT_MEGA_CIRUGIA_EJERCITO_2026-08-12.md`](CHECKPOINT_MEGA_CIRUGIA_EJERCITO_2026-08-12.md).

---

## Dos capitanes (solo 2)

| Modo | Vacío gatillo | Uso |
|------|---------------|-----|
| **Ansiedad** | **1,2 %** | Más ciclos; clima lateral o tsunami |
| **Normal** | **1,6 %** | Legión principal |

Tercer perfil (berserker) **eliminado** — tsunami → Ansiedad.

---

## ProtoBeru — tiers de la red oz/red

Arranque Monarca: **semilla ETH** + tier según equity + modo **Negociador**.

| Tier | Rango | Trailing oz/red | Clon `red_residual` | Negociador (oz / red) | Manto ETH ~ |
|------|-------|-----------------|---------------------|------------------------|-------------|
| **PLENO** | **Mariscal** | **0,1 % / 0,1 %** | **+0,1 %** | 0,1 % / 0,05 % | **$100** |
| **PROTO1** | **General** | **0,1 % / 0,1 %** | **+0,2 %** | 0,2 % / 0,1 % | **$50** |
| **PROTO2** | **Caballero** | **0,1 % / 0,1 %** | **+0,4 %** | 0,4 % / 0,2 % | **$25** |
| **BERUBBY** | **Soldado** | **0,1 % / 0,1 %** | **+0,8 %** | red 1 % → oz 2 % tras toque | **~$12,5** |

**Resolución dinámica:** el **trailing** (Hoz y Red en caza) es **siempre 0,1 %** en todos los rangos. Solo varía la **distancia inicial de la red** al gatillar (columna clon) según el tier.

**Desbloqueo por equity:** &lt;$25 BERUBBY · $25 PROTO2 · $50 PROTO1 · $100 PLENO.  
Auto-tier: promedio **3 días** (`MONARCA_TIER_AUTO_DIAS`). Ver [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md).

- Cada barco hereda `tier_id` y `modo_combate` al nacer; relevo conserva tier.
- **Legión paralela autorizada:** Negociador abajo + Cazador arriba en el mismo activo.

### Fusión (2026-07-09)

| Tipo | Cuándo | Resultado |
|------|--------|-----------|
| **Colisión Hoz** | ≥2 activos con `oz_adan` en el **mismo precio** (ε **0,01 %**) | Masa sumada · oz/red/ancla promedio ponderado |
| **Mega Beru** *(sagrado)* | ≥2 en `ESPERANDO_CONDICIONAL` con ancla **bajo el promedio** | Super Beru en el promedio del manto |

### Reset Mega Beru (toque de red)

Cuando el **Mega Beru** (`es_super_beru`) negocia y el precio **toca su red** (no un negociador normal del ciclo infinito):

| Paso | Efecto |
|------|--------|
| 1 | **Cosecha / suelta** del Mega — capital vuelve a la **bóveda** (margen cruzado Tusk); nada exclusivo salvo doctrina Greed |
| 2 | **Nuevo 0** = precio del toque de red (`centro_manto` local) |
| 3 | **Semilla nueva** con **masa $0** — otro soldado, no hereda los $100 del Mega |
| 4 | Modo **CAZA** — al gatillar pide reserva a Tusk (`capa1`); **engorde** +G_min/0,1 % en red como primera caza real |

Negociador normal del ciclo infinito: toque red → `ESPERANDO_ABISMO` (caza fantasma, masa congelada). Solo Mega hace reset generacional.

**Código:** `core/beru_mega_reset.py`, `_reset_mega_por_red` en `generales/beru.py`.  
**Validación:** `python scripts/validar_beru_mega_reset_smoke.py`

No fusionar en `ESPERANDO_ABISMO` ni sin grid desplegada.  
**Validación:** `validar_beru_fusion_smoke.py` · `validar_beru_multiberu_smoke.py`

**Config default:** `BERU_TIER_DEFAULT=PROTO1`, `BERU_MODO_COMBATE_DEFAULT=NEGOCIADOR`.

---

## Modo Cazador — clonación, frontera y engorde (2026-07-09)

**Centro 0:** precio equilibrio del **manto** L/S (`centro_manto_desde_tusk` o `centro_manto` local tras Mega reset).

**Wake / DESPIERTA (Monarca 2026-08-11):** como un Mega-reset de ciclo — al plantar, **ambos centros = precio actual** (`BERU_WAKE_RESET_0`). Flota completa (`BERU_SIEMBRA_FLOTA`), Capitán **Normal 1,6 %** (`BERU_CAPITAN_WAKE=NORMAL`). Manos spot solo con `BERU_MANOS=true` (default OFF). Ver [`CHECKPOINT_BERU_WAKE_RESET0_2026-08-11.md`](CHECKPOINT_BERU_WAKE_RESET0_2026-08-11.md).

**Ensayo manos (2026-08-12):** nivel 2 = fantasma (ojos ON, cero órdenes) · nivel 3 = manos chiquitas (1 Santo, techo de cazas, solo LONG, consola `[BERU_LIVE]`). Rituales: `arise_beru_fantasma` / `arise_beru_manos_chiquitas`. Ver checkpoints del mismo día.

| Regla | Valor |
|-------|--------|
| Gatillo Normal | ±**0,8 %** desde el 0 |
| Al gatillar | oz **−0,1 %** del toque; red a **distancia de clon** del tier (Mariscal +0,1 % … Soldado +0,8 %) |
| Toque de red (frontera) | Solo el Beru con la **red más extrema** **arrastra** oz/red +0,1 %; **sin sumar masa** si engorde OFF (ley 2026-08-11). Legado +G_min solo con `BERU_ENGORDE_PERMITIDO=true`. |
| Peloteo en rangos intermedios | Caza fantasma / ciclo infinito **sin engorde** |
| Cosecha (Hoz) | Pasa a **Negociador** · deja `red_residual` en memoria |
| Clonación | Toque de `red_residual` → **Capa N+1** con **G_min** (legión paralela OK) |
| Capa 1 (masa) | Arranque **+G_min** (mordida) · engorde libre **+G_min / 0,1 %** · único límite = **oxígeno Tusk** (`BERU_CAZA_CAPA1_MAX_USD=0` = sin techo; Monarca 2026-07-18) |

**Eliminado:** techo fijo ~**$50** de capa 1 — era miope ante corridas largas.  
**Eliminado:** spawn automático cada **0,3 %** durante caza activa — el cazador de frontera **engorda solo**.

**Código:** `core/beru_cazador.py`, `core/beru_residual.py`, `generales/beru.py`.  
**Validación:** `python scripts/validar_beru_cazador_smoke.py` · `python scripts/validar_ciclo_beru_eth.py`

---

## Modo Negociador — post-cazador (2026-07)

Tras cosecha de **capa 1** del Cazador, Beru pasa a negociar **sin engordar** (solo el Cazador suma posición).

| Regla | Valor (tier PLENO) |
|-------|---------------------|
| Ancla | Nivel oz de la cosecha cazador (ej. **+0,7 %**) |
| Oz condicional | Ancla **− abismo 1,6 %** → **−0,9 %** |
| 1.ª activación | Oz y red **0,1 %** juntas; red más cerca del 0 (orden inverso) |
| Toques 2–5 | Oz **0,1 %**; red **0,05 %**; **sin engorde** |
| 6.º toque | **Resorte**: red salta a 0,1 % bajo la oz condicional; oz +0,1 % extra |
| Ciclo | Se repite de 5 en 5 |

### Ciclo infinito Cazador ↔ Negociador

Tras la **primera caza real**, la masa queda **congelada** (ej. $35) — **nunca más engorde**.

| Evento | Efecto |
|--------|--------|
| Toca **oz cazador** (+0,7 %) | → vuelta a **Negociador** (condicional −0,9 %) |
| Toca **red negociador** (−0,8 %) | = tocar oz en caza → **ESPERANDO_ABISMO** hacia gatillo +0,8 % |
| Cruza abismo → **+0,8 %** | Grid cazador fantasma oz +0,7 % / red +0,9 % **sin engorde** |
| Repetir | Negociación infinita entre ambos lados del manto |

**Estado:** `ESPERANDO_CONDICIONAL` → `NEGOCIANDO` (neg) ↔ `ESPERANDO_ABISMO` → `NEGOCIANDO` (caza fantasma).  
**Código:** `core/beru_negociador.py`, `_pulsar_negociador_post_cazador`, `_flip_*` en `generales/beru.py`.  
**Validación:** `python scripts/validar_beru_negociador_smoke.py`

---

## Beru al 100 % — tamaño del manto (tier PLENO)

**G_min variable por Santo (2026-08-07):** el peaje ya no es un $5 fijo para toda la flota.  
`G_min` = mínimo de orden del **rail spot USDT** del Santo (si existe); si no, linear; piso configurable (default **$1**). Fuente: `data/bybit_minimos_orden.json` (sync Bybit).

Objetivo Mariscal: **PnL / 0,1 % = G_min del Santo**  
→ PLENO **PnL / 1 % = 10×G_min** (antes se leía “$50 / 1 %” cuando G_min era $5).

| Fórmula | Valor |
|---------|--------|
| Notional / pierna (PLENO / Mariscal) | (10×G_min) ÷ 0,01 |
| IM pierna inversa | notional ÷ **lev_inv** (máx Bybit) |
| IM pierna lineal | notional ÷ **lev_lin** (máx Bybit) |
| **Manto L+S (peaje IM)** | **IM_inv + IM_lin** (prohibido promediar lev) |

**Apalancamiento (2026-08-11):** peaje y ranking usan techos **por pierna** (`MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET` + `MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET`). El “promedio” es solo legado de UI — **no** es el peaje.

Proto tiers dividen el manto: `margen_tier = margen_pleno ÷ escala_manto` (×2 → PROTO1, ×4 → PROTO2).

### Mordida Cazador

Default = **G_min del Santo**. Override fijo solo si `BERU_CAZADOR_MORDIDA_USD > 0` (p.ej. live testnet). Engorde frontera: **+G_min / 0,1 %** sin techo artificial (oxígeno Tusk), con candado ranking: si `have > need` → `restante=0` / `OVERSHOOT_RANKING`.

### Ejemplos PLENO (manto solo, *con G_min=$5 legado*)

| Activo | Lev inv / lin | IM manto PLENO (~) |
|--------|---------------|---------------------|
| **ETH** | 100 / 100 | **$100** (50+50) |
| **BTC** | 100 / 100 | **$100** |
| **LINK** | 20 / 50 | **$350** (250+100) |
| **LTC** | 50 / 50 | **$200** |
| **SOL** | 50 / 100 | **$150** |
| **WIF** | 20 / 50 | **$350** (si hay inverso; si no, solo pierna lineal) |

Con G_min real distinto, los $ del manto **escalan solos** (fricción fija).

### Equity mínima recomendada

`margen_manto_por_tier(activo, tier)` — **sin colchón spot extra** (`BERU_SPOT_COLCHON_USD=0`).  
Spot margen usa la misma equity; ganancias/pérdidas se compensan ahí.

Ej. ETH **PROTO1** con G_min=$5: **~$50** equity (manto L+S a escala ×2).

### Pase / ranking (vivo 2026-08-11)

Peaje regenerado pierna a pierna: corona **Brujo \$1673** · **Chamán \$3735**. Smoke: `scripts/validar_pase_im_ranking_smoke.py`. Candado engorde: `OVERSHOOT_RANKING` si have > need.

---

## Semilla

**`BERU_ACTIVO_SEMILLA=ETH`** — arranque con poco capital y máximo apalancamiento líquido.

## Rail casa — elegir oveja entre stables (2026-07-05)

Beru **no** hace multicruce triangular (eso es **Greed**). Sí elige el **mejor frente spot** frente a stables:

| Stable | Ejemplo frente ETH |
|--------|-------------------|
| USDT | ETHUSDT_SPOT |
| USDC | ETHUSDC_SPOT |
| USDE / USD1 | si existen en Trinidad |

Módulo: `core/beru_rail.py` — precio efectivo + fee + muro; **Ancla/Kaiser** si hay libro.

Evento Bellion: `RAIL_ELEGIDO` cuando hay más de un candidato.

---

Pentiverso operativo (LTC/BTC) puede convivir; la semilla doctrinal para crecer rápido es ETH en **ProtoBeru 1**.

---

## Sub-Santuario Beru (Pergamino + panel)

**Estado:** vivo 2026-07-24  
**Código:** `core/beru_asset_detail.py` · Bellion `beru_flota` / `beru_asset_details` · `ui/BeruPanel.jsx` · `ui/BeruAssetDetail.jsx` · sección flota en `panel.py`

Por moneda (semilla y flota): barrita **caza vs negociando**, **red que permite engordar** (solo frontera), rails USDT/USDC, mapa de niveles (centro 0 / oz / red), PnL estimado vs entrada, **crónica** de ciclos (`data/beru/cronicas/{ACTIVO}.jsonl` — cosecha, vuelta caza/neg, Mega reset, fusión).

Abrir: portal **Beru** en la Cascada (mismo gesto que Igris). Fees ledger aún hueco preparado.

**Validación:** `python scripts/validar_beru_asset_detail_smoke.py`

---

## App / cuestionario (futuro)

Variables por usuario: activo semilla, tier (auto por equity), vacíos, modo combate, `BERU_PNL_OBJETIVO_POR_1PCT_USD`, catálogo `ACTIVOS_BERU_FLOTA`. Ver escalera completa en [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md).

**Pase de batalla (2026-07-19):** vacío Adán preferido del grial **1,6 %** · malla normal · orden de despertar/ascenso en [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md). HYPE/XRP: en vivo conviene **Soldado** (Mariscal solo en meta teórica del pase).

---

## Validación

`python scripts/validar_beru_capital_smoke.py` · `python scripts/validar_g_min_variable_smoke.py` · `python scripts/validar_beru_asset_detail_smoke.py`  
Sync mínimos: `python scripts/sync_bybit_minimos_orden.py` · Jess: [`PEGAR_JESS_SYNC_MINIMOS_BYBIT.md`](PEGAR_JESS_SYNC_MINIMOS_BYBIT.md)
