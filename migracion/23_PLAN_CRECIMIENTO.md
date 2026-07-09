# 23 — Plan de crecimiento del Ejército (capital del Monarca)

**Estado:** v1 — Monarca 2026-07-06 (checkpoint antes de profundizar Beru)  
**Código espejo:** `core/plan_crecimiento.py`  
**Relacionado:** [`22_DOCTRINA_BERU.md`](22_DOCTRINA_BERU.md) · [`21_DOCTRINA_IGRIS.md`](21_DOCTRINA_IGRIS.md) · [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md)

---

## Propósito

Definir **cómo crece el ejército según el capital (equity UTA) del Monarca**: qué rangos, qué cazas Beru, qué tier de red, cuánto manto, cuándo encender Greed, y **cómo conviven** Beru, Igris y Greed.

> Con **$100** no se despliega el mismo ejército que con **$1.000**.

---

## Principios (v1)

| # | Principio |
|---|-----------|
| 1 | **Un solo tesoro** — Tusk reparte oxígeno; no hay bolsillos secretos |
| 2 | **95% manto / 5% colchón** — Igris escudo L/S; colchón fijo para slippage + Greed |
| 3 | **Beru intercambia spot** — no suma apalancamiento; opera sobre el manto del barco |
| 4 | **Meritocracia** — desde todos los rangos; eficiencia relativa; baja de tier, no eliminación |
| 5 | **Colchón 5% fijo** — siempre, independiente del margen ocupado |
| 6 | **Concentración 20%** — tope del **manto de ese barco**; al pasar, Igris no engorda más |
| 7 | **Botín Greed** — victorias Greed: mitad retiene Greed, mitad tesorería ejército |

---

## Rangos del Monarca (equity UTA)

Subniveles por **barcos desbloqueados**, no por % dentro del rango.

| Rango | Equity | Cazas desbloqueadas | Greed |
|-------|--------|---------------------|-------|
| **Aspirante** | &lt; $100 | ETH (tier BERUBBY→PROTO hasta $100) | off |
| **Recluta** (Aprendiz de brujo) | $100 – $499 | ETH pleno | colchón 5% |
| **Soldado** (Chamán) | $500 – $1.999 | ETH, SOL, FIL, LTC | colchón |
| **Capitán** (Invocador) | $2.000+ | Flota `ACTIVOS_BERU_FLOTA` | colchón |
| **General** (Nigromante) | $10.000+ | Flota completa | colchón + VIP |
| **Señor de las Sombras** | $100.000+ | Flota completa | full |

---

## Tiers Beru (por equity del barco / cuenta)

| Equity | Tier | Nombre | Manto ETH ~ |
|--------|------|--------|-------------|
| &lt; $25 | **BERUBBY** | Beru Aspirante | ~$12,5 |
| $25+ | **PROTO2** | Aprendiz | ~$25 |
| $50+ | **PROTO1** | Guerrero | ~$50 |
| $100+ | **PLENO** | Comandante | ~$100 |

**North star PLENO:** $50 PnL por 1% movimiento. Protos buscan órdenes mínimas ~$5.

**Auto-tier:** `MONARCA_NIVEL_AUTO=true` — sube/baja tras **3 días** promedio sobre/bajo umbral (`MONARCA_TIER_AUTO_DIAS`).

### BERUBBY — red especial

- **Negociador:** red a **1%** del centro; al tocar red → **oz a 2%** en sentido contrario.
- **Cazador:** 1% simétrico oz/red.

---

## Presupuesto del tesoro

| Destino | % | General |
|---------|---|---------|
| **Manto L/S** | **95%** | Igris |
| **Colchón** | **5%** | Slippage + Greed (misiones que cubran fees mínimo) |
| **Beru** | 0% margen extra | Intercambio spot sobre manto existente |

**Margen objetivo de operación:** ~**93%** (`MONARCA_MARGEN_OBJETIVO_PCT`). No vivir en 95%+ salvo excepciones VIP.

---

## Convivencia (prioridad cuando falta oxígeno)

```
1. Beru — COSECHA / NEGOCIANDO
2. Beru — nueva CAZA
3. Igris — banda delta (escudo)
4. Greed — si margen OK y oportunidad VIVA
```

| Situación | Beru | Igris | Greed |
|-----------|------|-------|-------|
| Margen &lt; 80% | caza | engorde/bootstrap | colchón |
| ~93% ideal | caza | rebalanceo | colchón |
| 93–95% | moderado | espejos | colchón |
| ≥ 95% ley marcial | operativo | poda ~15% | **solo VIP/Mega VIP** |
| SAFE_MODE | **caza NO bloqueada** | poda sí | pausa radar |

**Mega VIP** desde equity **≥ $100** (primer Beru ETH pleno).

---

## Multi-Beru (doctrina)

- **1 caza activa por activo** — no dos ETH en paralelo por diseño.
- **Relevo:** COSECHA → generación +1.
- **Colisión:** fusión → super Beru.
- **Abandono:** baja a **BERUBBY** (Beru Aspirante); sigue vivo al mínimo.

---

## Mérito (todos los rangos)

| Señal | Acción |
|-------|--------|
| Alta eficiencia ($/margen vs pares) | sube tier en próximo ciclo |
| Parásito relativo | baja tier; modo abandono gradual |
| Puerto roto | capital → colchón → reasignar |

Sin amputaciones. Igris busca mejor salida en abandono.

---

## Botín

- **Ganancia general** → tesorería conjunta (Tusk).
- **Victorias Greed** → `reparto_botin_greed()`: **50% Greed** / **50% ejército**.

---

## Ciclo operativo del Monarca

1. **Manto** — Igris bootstrap L/S  
2. **Caza Beru** — transmutación oro / pex (acordeón spot)  
3. **Botín Greed** — arbitraje sin romper escudo  
4. **Oxígeno** — Tusk NAV → rango → tier auto  
5. **Susurro de las sombras** — Bellion + panel  

Tank y Kaiser: vigilantes transversales (radar), no pasos del ciclo.

---

## Knobs (config / env)

| Variable | Default v1 | Rol |
|----------|------------|-----|
| `MONARCA_RESERVA_PCT` | **0.05** | Colchón 5% fijo |
| `MONARCA_CONCENTRACION_MAX_PCT` | **0.20** | Tope manto por barco |
| `MONARCA_MARGEN_OBJETIVO_PCT` | **93.0** | Zona ideal operación |
| `MONARCA_TIER_AUTO_DIAS` | **3** | Días promedio para subir/bajar tier |
| `MONARCA_MEGA_VIP_EQUITY_MIN` | **100** | Mega VIP desde Recluta+ |
| `MONARCA_NIVEL_AUTO` | **true** | Tier auto al NAV sync |

---

## Implementación

| Pieza | Estado |
|-------|--------|
| Doctrina este doc | ✅ v1 |
| `core/plan_crecimiento.py` | ✅ rangos, tiers, colchón, convivencia, hist equity |
| `core/beru_tier.py` BERUBBY | ✅ |
| Tusk NAV → nivel + tier | ✅ |
| Beru tier desde Tusk + oz BERUBBY | ✅ |
| SAFE_MODE sin bloqueo caza | ✅ |
| `distribuir_botin` runtime | ❌ pendiente |
| Mérito Bellion runtime | ❌ Fase 5 |
| Tope 20% por barco enforced | ❌ pendiente |
| Beru contabilidad neutra al margen | ❌ pendiente |

**Validar:** `python scripts/validar_plan_crecimiento_smoke.py`

---

*Planos: `migracion/` · Código: `core/plan_crecimiento.py`*
