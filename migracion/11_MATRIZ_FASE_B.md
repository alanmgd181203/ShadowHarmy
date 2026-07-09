# 11 — Matriz Fase B (ShadowHarmy vs especificación)

**Completada:** 2026-06-30  
**Código canónico:** `C:\Users\alans\Desktop\ShadowHarmy`  
**Especificación:** `migracion/` + SA-IDs  
**Análisis completo:** [`13_ANALISIS_SHADOWHARMY.md`](13_ANALISIS_SHADOWHARMY.md)

## Leyenda

| Estado | Significado |
|--------|-------------|
| ✅ | Implementado; código es referencia |
| ⚠️ | Parcial o diverge del manual (código gana) |
| ❌ | Ausente o roto |
| 🔮 | Futuro — ver `15_IDEAS_FUTURO.md` |
| 📝 | Manual tiene idea; código tiene otra mejor |

---

## P0 — Infraestructura

| ID | Especificación | Archivo SH | Estado | Notas |
|----|----------------|------------|--------|-------|
| T-01 | place_order + fill | `core/bridge.py` | ✅ | M1: BTCUSDT testnet round-trip; `place_order`, `esperar_fill`, `cancel/amend` |
| T-02 | NAV → Tusk | `generales/tusk.py` | ✅ | `actualizar_nav_real` |
| T-03 | REGLA-R07 fill confirmado | bridge+greed | ✅ | Greed live → fill poll → `confirmar_reserva(fill_confirmado=True)` |
| T-04 | .env keys | `core/config.py` | ✅ | BYBIT_* + TESTNET |
| T-05 | Persistencia | `tusk_data.json` + bellion | ✅ | Tusk 10s + jsonl |
| T-06 | requirements.txt | raíz | ✅ | pybit, websockets, streamlit |

## P0 — Generales

| ID | Spec | Archivo | Estado | Notas |
|----|------|---------|--------|-------|
| G-Tusk | Reservas + oxígeno | `tusk.py` | ✅ | confirmar/liberar/consumar |
| G-Greed | Kaiser + Ancla + VIP + multicruce + basis | `greed.py`, `greed_mision.py` | ✅ | Consume `kaiser.consumir_greed()`; basis hold; legacy squad off |
| G-Beru | Legión + ProtoBeru + rail stable | `beru.py`, `beru_tier.py`, `beru_rail.py` | ✅ | Capital tiers; elige rail USDT/USDC/USDE/USD1 |
| G-Igris | Manto 80-95% + §E v1 | `igris.py`, `igris_manto.py` | ⚠️ | Bootstrap inverse L + lineal S; promedios; Ancla maniobras pendiente |
| G-Tank | 10 mares + semáforo | `tank.py` | ✅ | LTC+BTC dual; USDC lineal = reflejo spot |
| G-Tank-S | Matriz spreads + funding/index WS | `spreads.py`, `tank.py` | ✅ | SPOT_ALL ampliado; top 50; multicruce filas |
| G-Tank-S1 | Desvío perp vs indexPrice (Fase 1) | `spreads.py` | ✅ | Bybit local; huérfanas marcadas |
| G-Tank-S2 | Panorama Binance (Fase 2) | `binance_ref.py` | ⚠️ | Código ✅; WS 451 desde USA |
| G-Kaiser | Vocero + pipeline Greed | `kaiser.py`, `kaiser_pipeline.py` | ✅ | Cola viva, abort, perfiles, metaverso, Ancla |
| G-Trinidad | Catálogo instrumentos + huérfanas | `trinidad.py` | ✅ | Cache + `ACTIVOS_HUERFANOS` |
| G-Bellion | Audit | `bellion.py` | ⚠️ | log OK; sin clasificación activos |
| G-Cap | ADN clima | `capitanes.py` | ✅ | 3 capitanes wired vía Tank |
| G-Iron | Arca / safe | — | 📝 | Absorbido Tusk+Greed; sin iron.py |
| G-Dash | HUD consola | `dashboard.py` | ✅ | |
| G-Arise | Orquestación | `arise.py` | ✅ | 8+ tareas gather |
| G-Plan | Crecimiento / convivencia | `plan_crecimiento.py` | ✅ | `23` v1 checkpoint |

## P0 — Reglas numéricas

| Regla | Manual | ShadowHarmy | Estado |
|-------|--------|-------------|--------|
| R-Beru 0.012 | Códice | — | 🔮 | Código usa vacío Adán 0.6–2% |
| R-Beru vol 0.035 | Códice | — | 🔮 | Ver 15_IDEAS |
| R-Igris vol 0.04 | Códice | — | 🔮 | Usa % margen config |
| R-Igris fuga 1.5% | Códice | — | 🔮 | |
| R-Gap 2.5× | Códice | — | 🔮 | |
| R-TTL 2000 ms | migracion | config | ✅ | |
| R-Regalo 0.003 | migracion | config | ✅ | |
| R-Cosecha 0.01 | implícito | config UMBRAL_COSECHA_MIN | ✅ | |
| R-Muro 95% | implícito | MURO_LEY_MARCIAL | ✅ | |
| R-Expansión 80% | implícito | RANGO_EXPANSION_MIN | ✅ | |
| R-Limpieza 90% | implícito | RANGO_LIMPIEZA_MAX | ✅ | |
| R-Delta 48-52% | implícito | igris/greed banda adaptativa | ✅ | 45-55→50-50 dinámico + slippage por frente |

## P1 — Notificaciones

| ID | Spec | Estado | Notas |
|----|------|--------|-------|
| N-01 | Telegram crítico | 🔧 | stub `core/telegram.py` |
| N-02 | Fill sin sonido | ❌ | |
| N-03 | Salud diaria | ❌ | |
| N-04 | Consola only | ✅ | prints + Bellion |

## P2 — Estrategia

| ID | Spec | Estado | Notas |
|----|------|--------|-------|
| S-01 | BeruShip ciclo | ✅ | modelo con red_adan/oz_adan/max_favor; sincronizado |
| S-02 | Acordeón 1.1/0.9 | ✅ | compila; engorde + negociador |
| S-03 | Arbitraje USDT/USDC + Kaiser | ✅ | Greed Kaiser pipeline; multicruce; basis hold |
| S-08 | Ojos arbitraje → disparo Greed | ✅ | Matriz + Ancla + cola; VIP en ley marcial |
| S-09 | Beru rail stable | ✅ | `beru_rail.py` elige mejor frente casa |
| S-10 | Igris bootstrap §E | ⚠️ | Inverse L + lineal S; promedios; Ancla pendiente |
| S-04 | Fusión super_beru | ✅ | fusión dual: contacto (bola de nieve) + promedio selectivo |
| S-05 | Escalera desbalance | 🔮 | manual |
| S-06 | Bellion Ratio activos | 🔮 | manual |
| S-07 | Igris REBALANCEO handler | ✅ | igris→Bridge directo (ex-Greed altar) |

## P3 — Visión

| ID | Spec | Estado |
|----|------|--------|
| V-01 | Ragnarok fusión | 🔮 |
| V-02 | Campo de Marte | 🔮 |
| V-03 | 120 frentes | 🔮 |
| V-04 | Fusión Monarcas | 🔮 |

---

## Resumen ejecutivo

| Prioridad | Total | ✅ | ⚠️ | ❌ | 🔮 |
|-----------|-------|----|----|-----|-----|
| P0 infra+gen | 16 | 7 | 4 | 5 | 0 |
| P0 reglas | 12 | 6 | 0 | 0 | 6 |
| P1 | 4 | 1 | 0 | 3 | 0 |
| P2 | 7 | 0 | 4 | 1 | 2 |
| P3 | 4 | 0 | 0 | 0 | 4 |

**Veredicto:** Núcleo operativo ~95% (Fases 0–3). **Siguiente:** Fase 4 M3 ops + cerrar Igris §E Ancla.

**Fecha revisión:** 2026-07-05 (Greed basis, Beru Proto, Igris §E v1)  
**Revisor:** Cursor + Monarca
