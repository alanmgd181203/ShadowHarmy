# 14 — Roadmap (código ShadowHarmy)

**Orden de trabajo.** Código canónico: `C:\Users\alans\Desktop\ShadowHarmy`

---

## M0 — Desbloquear arranque (**COMPLETADO** — 2026-07-03)

| # | Tarea | Archivo | Estado |
|---|-------|---------|--------|
| 1 | Indentar métodos dentro `BeruCazador` | `generales/beru.py` | ✅ |
| 2 | Implementar `limpiar_legion()` (purga COSECHADO/FUSIONADO) | `beru.py` | ✅ |
| 3 | Añadir `red_adan`, `oz_adan`, `max_favor` a `BeruShip` | `core/models.py` | ✅ |
| 4 | Handlers Greed: `REBALANCEO_IGRIS`, `ENGORDAR_MANTO` | `generales/greed.py` | ✅ |
| 5 | `requirements.txt` (pybit, websockets, streamlit) | raíz | ✅ |
| 6 | Verificar `python arise.py` arranca sin crash | — | ✅ (51s+) |

**Extras sesión 2026-07-03:** fusión dual, banda adaptativa, personalidad slippage, panel Streamlit.

**Criterio done:** `py_compile` OK + loop 60s sin excepción. **CUMPLIDO.**

---

## M1 — Ejecución testnet (P0 negocio) — **COMPLETADO** (2026-07-04)

| # | Tarea | Estado |
|---|-------|--------|
| 1 | `bridge.place_order` + `cancel_order` wrapper | ✅ |
| 2 | Confirmar fill (poll) antes de `confirmar_reserva` | ✅ |
| 3 | Flag `MODO_SIMULACION` — si False, prohibir DISPARO_SIMULADO | ✅ |
| 4 | Cablear CAZA/COSECHA a órdenes reales | ✅ |
| 5 | Logging errores bridge (no `pass`) | ✅ |

**Notas:** Cuenta testnet verificada; **BTCUSDT** temporal (LTC linear cerrado en testnet; ETH reservado para bot paralelo). Trade redondo documentado en `data/m1_btc_roundtrip.json`. `arise.py` 3+ min live sin crash.

**Criterio done:** 1 ciclo documentado en testnet. **Parcial** — round-trip manual BTC (plomería); ciclo ejército CAZA→COSECHA y manto Igris **pendiente** (ver nota abajo).

**Nota honesta M1 (2026-07-04):** Lo validado fue **infra** (API, cuenta verificada, Bridge dispara). En `arise.py` live con BTC: no hay manto (pesos L/S vacíos), Igris solo intenta ENGORDAR y Greed lo bloquea por banda delta; Beru acecha sin referencia de grid; maniobras Igris (engorde/rebalanceo) aún **no** mandan órdenes al exchange en live — solo CAZA/COSECHA. BTC fue puente porque LTC testnet cerrado.

---

## M2 — Pentiverso real (P1) — **COMPLETADO** (2026-07-05)

| # | Tarea | Checklist |
|---|-------|-----------|
| 1 | WS múltiple LTC+BTC (10 mares) | 3.1.x ✅ |
| 2 | Muros liquidez en `TankNode.muros` | 3.1.5 ✅ |
| 3 | Greed USDT×USDC dual activo | 3.2.1 ✅ |
| 4 | `ley_de_sucesion` en shutdown | 3.3.1 ✅ |
| 5 | Primer manto + Igris→Bridge | 3.5 ✅ |
| 6 | Ciclo CAZA→COSECHA | 3.6 ✅ |

**Validación:** `validar_m2.py` 10/10 · `probar_ciclo_beru.py` · `validar_checklist.py --fase 3`

---

## M2.7 — Sentidos Tank ampliados — **COMPLETADO** (2026-07-05)

| # | Tarea | Checklist |
|---|-------|-----------|
| 1 | Catálogo spot ~598 + perps + huérfanas (Trinidad) | 3.7.1–3.7.3 ✅ |
| 2 | Matriz spreads + funding/index WS | 3.7.4–3.7.5 ✅ |
| 3 | Fase 1: desvío perp vs indexPrice | 3.7.6 ✅ |
| 4 | Fase 2: Binance ref + panorama global | 3.7.7 ✅ |
| 5 | REST spread/alpha/convert + quotes | 3.7.8 ✅ |
| 6 | Bellion, panel, arise integración | 3.7.9–3.7.11 ✅ |
| 7 | Scripts validación panorama | 3.V5–3.V7 ✅ |

**Validación:** `validar_panorama_tank.py` · `validar_sentidos_extra.py` · `data/validacion_panorama_tank.json`

**Nota:** solo ojos — generales no actúan sobre matriz/panorama aún. Estrategia → `19_BACKLOG_SENTIDOS.md` (3.7.P1–P3).

**Geo USA:** Binance 451 / REST 403 — Fase 1 Bybit OK; Fase 2 llena refs en VPS fuera USA.

---

## M2.8 — Kaiser vocero + manos Greed — **COMPLETADO** (2026-07-05)

| # | Tarea | Estado |
|---|-------|--------|
| 1 | `kaiser_indicators.py` — interpretar snapshots Tank | ✅ |
| 2 | `KaiserVocero.vigilar_indicadores` en arise | ✅ |
| 3 | Digest en `estado_vivo.kaiser` + panel | ✅ |
| 4 | Perfiles multietiqueta + metaverso + Ancla | ✅ |
| 5 | Pipeline Kaiser→Greed — cola, abort, sizing 1% | ✅ |
| 6 | VIP / Mega VIP micro-órdenes | ✅ |

**Validación:** `validar_kaiser_smoke.py` · `validar_ancla_smoke.py` · `validar_greed_sizing_smoke.py` · `validar_greed_vip_smoke.py`

---

## M2.9 — Greed omnimercado v1 — **COMPLETADO** (2026-07-05)

| # | Tarea | Checklist |
|---|-------|-----------|
| 1 | Multicruce spot 3–4p (USDC/MNT/EUR) | 3.2.3 ✅ |
| 2 | Basis hold / manto temporal | 3.2.4 ✅ |
| 3 | Matriz ampliada SPOT_ALL + top 50 | 3.7.4 🟡 |
| 4 | `manto_touch` en holds basis | 3.5.6 ✅ |

**Validación:** `validar_greed_multicruce_smoke.py` · `validar_greed_basis_smoke.py`

**Pendiente visión:** grafo completo Tank; rutas mixtas spot+perp 3+ piernas.

---

## M2.10 — Beru Proto — **COMPLETADO** (2026-07-05)

| # | Tarea | Checklist |
|---|-------|-----------|
| 1 | Tiers oz/red + capital | 3.5.7 ✅ |
| 2 | Rail stable (mejor USDT/USDC/USDE/USD1) | 22_DOCTRINA_BERU ✅ |
| 3 | ETH + PROTO1 arranque ~$50 manto | config ✅ |

**Validación:** `validar_beru_capital_smoke.py` · `validar_beru_rail_smoke.py`

---

## M2.11 — Igris §E v1 — **PARCIAL** (2026-07-05)

| # | Tarea | Estado |
|---|-------|--------|
| 1 | Bootstrap inverse L + lineal S | ✅ |
| 2 | `precio_medio` por pierna en `pesos` | ✅ |
| 3 | Ancla en maniobras Igris | ❌ 3.5.8 |
| 4 | Sesgo long / banda asimétrica | ❌ 3.5.8 |

**Validación:** `validar_igris_smoke.py`

---

## M2.12 — Plan crecimiento Monarca — **BORRADOR v0** (2026-07-05)

| # | Tarea | Estado |
|---|-------|--------|
| 1 | Doctrina `23_PLAN_CRECIMIENTO.md` | ✅ v1 |
| 2 | `core/plan_crecimiento.py` — rangos, tiers, colchón 5%, convivencia | ✅ |
| 3 | Panel/Bellion publican `plan_crecimiento` | ✅ |
| 4 | Auto-tier Tusk NAV (3 días promedio) | ✅ |
| 5 | Multi-flota Beru + mérito Bellion | ❌ pendiente |

**Validación:** `validar_plan_crecimiento_smoke.py`

---

## M3 — Operaciones (P1) ← **SIGUIENTE**

| # | Tarea |
|---|-------|
| 1 | `enviar_telegram` + tabla evento→nivel (`06_NOTIFICACIONES.md`) |
| 2 | Safe mode / kill switch (manual Iron → Tusk) |
| 3 | Informe salud diario |

---

## M4 — Estrategia avanzada (P2 — manual como backlog)

| # | Tarea | Ref manual |
|---|-------|------------|
| 1 | Escalera desbalance | REGLA-R03 |
| 2 | Bellion Ratio_Eficiencia / latidos | SA gestión riesgo |
| 3 | Gap 2.5× post-pérdida | Códice v2.3 |
| 4 | Beru volatilidad 0.035 (si se decide) | REGLA-R01 alternativa |

---

## M5 — Visión (P3 — no bloquea v1)

Ver [`15_IDEAS_FUTURO.md`](15_IDEAS_FUTURO.md): Campo de Marte, Ragnarok, 120 frentes, fusión Monarcas.

---

## PR sugerido #1 (mínimo)

```
fix(beru): repair class structure + limpiar_legion + BeruShip fields
fix(greed): route IGRIS REBALANCEO and ENGORDAR_MANTO
chore: add requirements.txt
```

---

## Métricas de éxito v1

- [ ] Testnet: 24h sin crash
- [ ] 0 DISPARO_SIMULADO en prod path
- [ ] Telegram en errores API
- [ ] `migracion/11_MATRIZ` P0 ≥ 80% ✅
