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
| T-01 | place_order + fill | `core/bridge.py` | ❌ | Solo WS + get_wallet_balance |
| T-02 | NAV → Tusk | `generales/tusk.py` | ✅ | `actualizar_nav_real` |
| T-03 | REGLA-R07 fill confirmado | bridge+greed | ❌ | pesos en memoria sin fill |
| T-04 | .env keys | `core/config.py` | ✅ | BYBIT_* + TESTNET |
| T-05 | Persistencia | `tusk_data.json` + bellion | ✅ | Tusk 10s + jsonl |
| T-06 | requirements.txt | raíz | ❌ | Falta archivo |

## P0 — Generales

| ID | Spec | Archivo | Estado | Notas |
|----|------|---------|--------|-------|
| G-Tusk | Reservas + oxígeno | `tusk.py` | ✅ | confirmar/liberar/consumar |
| G-Greed | Altar + TTL | `greed.py` | ⚠️ | altar OK; handlers Igris OK; banda adaptativa + slippage; sin orden real (M1) |
| G-Beru | Legión + acordeón | `beru.py` | ✅ | Compila; fusión dual; limpiar_legion; modelo completo |
| G-Igris | Manto 80-95% | `igris.py` | ✅ | poda, espejos, delta adaptativo (45-55→50-50 según margen) |
| G-Tank | 5 mares + semáforo | `tank.py` | ⚠️ | estructura OK; 1 precio real WS |
| G-Bellion | Audit | `bellion.py` | ⚠️ | log OK; sin clasificación activos |
| G-Cap | ADN clima | `capitanes.py` | ✅ | 3 capitanes wired vía Tank |
| G-Iron | Arca / safe | — | 📝 | Absorbido Tusk+Greed; sin iron.py |
| G-Dash | HUD consola | `dashboard.py` | ✅ | |
| G-Arise | Orquestación | `arise.py` | ✅ | 8 tareas gather |

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
| N-01 | Telegram crítico | ❌ | |
| N-02 | Fill sin sonido | ❌ | |
| N-03 | Salud diaria | ❌ | |
| N-04 | Consola only | ✅ | prints + Bellion |

## P2 — Estrategia

| ID | Spec | Estado | Notas |
|----|------|--------|-------|
| S-01 | BeruShip ciclo | ✅ | modelo con red_adan/oz_adan/max_favor; sincronizado |
| S-02 | Acordeón 1.1/0.9 | ✅ | compila; engorde + negociador |
| S-03 | Arbitraje USDT/USDC | ⚠️ | radar OK; precios USDC=0 |
| S-04 | Fusión super_beru | ✅ | fusión dual: contacto (bola de nieve) + promedio selectivo |
| S-05 | Escalera desbalance | 🔮 | manual |
| S-06 | Bellion Ratio activos | 🔮 | manual |
| S-07 | Igris REBALANCEO handler | ❌ | intención sin ruta greed |

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

**Veredicto:** Arquitectura sólida; **no listo live** hasta M0+M1 (`14_ROADMAP.md`).

**Fecha revisión:** 2026-06-30  
**Revisor:** Cursor (Fase B) + Monarca
