# 22 — Doctrina Beru (caza spot + capital manto + ProtoBeru)

**Estado:** Monarca 2026-07-09  
**Código:** `generales/beru.py`, `core/beru_cazador.py`, `core/beru_fusion.py`, `core/beru_residual.py`, `core/beru_tier.py`

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
| 4 | Modo **CAZA** — al gatillar pide reserva a Tusk (`capa1`); **engorde** +$5/0,1 % en red como primera caza real |

Negociador normal del ciclo infinito: toque red → `ESPERANDO_ABISMO` (caza fantasma, masa congelada). Solo Mega hace reset generacional.

**Código:** `core/beru_mega_reset.py`, `_reset_mega_por_red` en `generales/beru.py`.  
**Validación:** `python scripts/validar_beru_mega_reset_smoke.py`

No fusionar en `ESPERANDO_ABISMO` ni sin grid desplegada.  
**Validación:** `validar_beru_fusion_smoke.py` · `validar_beru_multiberu_smoke.py`

**Config default:** `BERU_TIER_DEFAULT=PROTO1`, `BERU_MODO_COMBATE_DEFAULT=NEGOCIADOR`.

---

## Modo Cazador — clonación, frontera y engorde (2026-07-09)

**Centro 0:** precio equilibrio del **manto** L/S (`centro_manto_desde_tusk` o `centro_manto` local tras Mega reset).

| Regla | Valor |
|-------|--------|
| Gatillo Normal | ±**0,8 %** desde el 0 |
| Al gatillar | oz **−0,1 %** del toque; red a **distancia de clon** del tier (Mariscal +0,1 % … Soldado +0,8 %) |
| Toque de red (frontera) | Solo el Beru con la **red más extrema** engorda: oz/red **+0,1 %** juntas; **+$5** |
| Peloteo en rangos intermedios | Caza fantasma / ciclo infinito **sin engorde** |
| Cosecha (Hoz) | Pasa a **Negociador** · deja `red_residual` en memoria |
| Clonación | Toque de `red_residual` → **Capa N+1** con **$5** (legión paralela OK) |
| Capa 1 | hasta **$50** (o `BERU_CAZA_CAPA1_USD`) |

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

Objetivo: **$50 PnL por 1 %** de movimiento **por pierna** del manto  
→ **$5 por 0,1 %** (línea del mínimo de orden ~$5).

| Fórmula | Valor |
|---------|--------|
| Notional / pierna | $50 ÷ 0,01 = **$5.000** |
| Margen / pierna | $5.000 ÷ lev_promedio |
| **Manto L+S** | **2 × margen / pierna** |

**Apalancamiento:** promedio de máx **inverse (long)** + **lineal stable (short)** por activo (`config.MANTO_LEVERAGE_*_BY_ASSET`).

Proto tiers dividen el manto: `margen_tier = margen_pleno ÷ escala_manto` (×2 → PROTO1, ×4 → PROTO2).

### Ejemplos PLENO (manto solo)

| Activo | Lev prom | Margen manto PLENO |
|--------|----------|---------------------|
| **ETH** | 100 | **$100** |
| **BTC** | 100 | **$100** |
| **LTC** | 62,5 | **$160** |
| **SOL** | 50 | **$200** |
| **WIF** | 20 | **$500** |

### Equity mínima recomendada

`margen_manto_por_tier(activo, tier)` — **sin colchón spot extra** (`BERU_SPOT_COLCHON_USD=0`).  
Spot margen usa la misma equity; ganancias/pérdidas se compensan ahí.

Ej. ETH **PROTO1:** **~$50** equity (manto L+S a escala ×2).

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

## App / cuestionario (futuro)

Variables por usuario: activo semilla, tier (auto por equity), vacíos, modo combate, `BERU_PNL_OBJETIVO_POR_1PCT_USD`, catálogo `ACTIVOS_BERU_FLOTA`. Ver escalera completa en [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md).

---

## Validación

`python scripts/validar_beru_capital_smoke.py`
