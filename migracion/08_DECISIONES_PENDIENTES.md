# 08 — Decisiones cerradas y pendientes

## Cerradas (respetar en código)

| ID | Decisión |
|----|----------|
| D-01 | Vocabulario Monarca en docs y logs (P0.1 B) |
| D-02 | Sandbox se conserva como historial; no podar agresivo (P0.2 C) |
| D-03 | Pipeline Analista fundacional **no** re-correr |
| D-04 | Greed es el ejecutor único vía cola prioridad |
| D-05 | Tusk es dueño de reservas y NAV |
| D-06 | Sin reparación Iron de posiciones cortadas (espíritu v2.3) |
| D-07 | Fill confirmado antes de contar ejecución (REGLA-R07) — **pendiente implementar** |
| D-08 | Jerarquía Telegram documentada en `06_NOTIFICACIONES.md` |
| D-09 | Esta carpeta `migracion/` es fuente Cursor para implementación |
| **D-10** | **Repo canónico = `C:\Users\alans\Desktop\ShadowHarmy`** — código manda |
| **D-11** | **Sin módulo Iron** — rol en Tusk + Greed "Hierro" |
| **D-12** | **Umbrales margen Igris 80/90/95%** — no 85% del manual |
| **D-13** | **Beru acordeón/vacío Adán** — estrategia activa; umbral 0.012 manual → backlog |

## Pendientes — humano

| ID | Tema | Fuente |
|----|------|--------|
| H-01 | Estrategia trading en Códice vs sandbox | CORRECCIONES_PENDIENTES #1 |
| H-02 | Versión canónica gestión riesgo | #2 |
| H-03 | Promover bloques sandbox → Códice | P0.4, Bloques 1–8 |
| H-04 | `<details>` en Códice | P0.5 |
| H-05 | ¿Iron módulo separado o dentro Tusk? | drift código |
| H-06 | ¿Repo canónico = ShadowHarmy evolucionado u otro? | Fase B |
| H-07 | ¿Mainnet live o testnet hasta milestone X? | riesgo |
| H-08 | Versión cristalizada única (v2.3 vs v2.4…) | manual |

## Pendientes — técnicas (ShadowHarmy)

Ver [`14_ROADMAP.md`](14_ROADMAP.md) — resumen:

| ID | Tema | Prioridad |
|----|------|-----------|
| T-01 | **beru.py no compila** + limpiar_legion | **M0** |
| T-02 | Greed handlers REBALANCEO/ENGORDAR | **M0** |
| T-03 | `place_order` + fill confirmado | **M1** |
| T-04 | MODO_SIMULACION vs live | **M1** |
| T-05 | WS 5 mares | **M2** |
| T-06 | Telegram | **M3** |
| T-07 | requirements.txt | **M0** |
| T-08 | SUPER_FUSION: fusión dual (contacto + promedio selectivo) — **implementado** | **cerrado** |

## Contradicciones convivientes (no resolver ahora — P0.3)

1. Códice MAP sin `<details>` vs sandbox con contexto Monarca.
2. Iron en manual vs ausente en ShadowHarmy.
3. Igris margen 80–95% vs protocolo 85% margen.
4. Múltiples nombres legacy (Homunculus, Lilit, Verdugo).

## Milestone sugerido post-Fase B

**M1 — Hierro vivo:** 1 par, órdenes reales testnet, Tusk+NAV+Greed+fill, Bellion log, Telegram crítico.

**M2 — Pentiverso:** 5 mares + arbitraje USDT/USDC.

**M3 — Legión:** BeruShip + Capitanes + grid.

**M4 — Acero:** mainnet size limitado + safe mode.

## Cómo actualizar este archivo

Al cerrar decisión en sesión Cursor: mover fila de Pendiente → Cerrada con fecha.
