# Migración — Códice operativo Shadow Army

**Destilación Fase A** (2026-06-30) — exprime el output del Analista (`fundacional_qwen14_v1`) en documentación usable por **Cursor** para programar el Ejército de Sombras.

**Empieza aquí:** [`RESUMEN_EJECUTIVO.md`](RESUMEN_EJECUTIVO.md) → [`CODEX_VIVO.md`](CODEX_VIVO.md) → [`17_GUIA_MONARCA.md`](17_GUIA_MONARCA.md) (tono con el Monarca)

| Fase | Estado |
|------|--------|
| **A** — Destilación manual → planos | ✅ 2026-06-30 |
| **B** — ShadowHarmy vs planos | ✅ 2026-06-30 |

**Código canónico:** `C:\Users\alans\Desktop\ShadowHarmy` — **codex junto al código:** `ShadowHarmy/migracion/`

## Para qué sirve esto

| No es | Sí es |
|-------|-------|
| Reemplazo del `manual_v2/` original | Planos de implementación + índice |
| El archivo `1M.txt` completo | Síntesis de ~139 bloques destilados |
| Auditoría de código (Fase B) | Fuente de verdad para la Fase B |

## Orden de lectura

1. [`00_NORTE.md`](00_NORTE.md) — visión y límites de v1
2. [`01_ARQUITECTURA.md`](01_ARQUITECTURA.md) — capas, flujo de datos, async
3. [`02_GENERALES.md`](02_GENERALES.md) — roles Igris, Beru, Tusk, Tank, Greed, Bellion, Capitanes, Iron
4. [`03_RIESGO_Y_REGLAS.md`](03_RIESGO_Y_REGLAS.md) — reglas firmes del Códice + sandbox
5. [`04_INFRA_API.md`](04_INFRA_API.md) — Bybit, bridge, persistencia
6. [`05_ESTRATEGIA_EJECUCION.md`](05_ESTRATEGIA_EJECUCION.md) — ships, arbitraje, grid, pentiverso
7. [`06_NOTIFICACIONES.md`](06_NOTIFICACIONES.md) — Telegram y consola
8. [`07_GLOSARIO.md`](07_GLOSARIO.md) — vocabulario Monarca
9. [`08_DECISIONES_PENDIENTES.md`](08_DECISIONES_PENDIENTES.md) — cerrado vs abierto
10. [`09_CATALOGO_ESPECIFICACIONES.md`](09_CATALOGO_ESPECIFICACIONES.md) — SA-001…SA-139
11. [`10_FUENTES_Y_METODO.md`](10_FUENTES_Y_METODO.md) — de dónde salió cada cosa
12. [`11_MATRIZ_FASE_B.md`](11_MATRIZ_FASE_B.md) — matriz ✅⚠️❌ completada
13. [`12_PROTOCOLO_CURSOR.md`](12_PROTOCOLO_CURSOR.md) — cómo usar esto en sesiones de código
14. [`13_ANALISIS_SHADOWHARMY.md`](13_ANALISIS_SHADOWHARMY.md) — análisis código canónico
15. [`14_ROADMAP.md`](14_ROADMAP.md) — milestones M0–M5
16. [`15_IDEAS_FUTURO.md`](15_IDEAS_FUTURO.md) — ideas manual (backlog)
17. [`16_CHECKLIST_MAESTRO.md`](16_CHECKLIST_MAESTRO.md) — **camino completo** tareas/subtareas (agente nuevo)
18. [`17_GUIA_MONARCA.md`](17_GUIA_MONARCA.md) — **cómo hablar con el Monarca** (tono, perfil, proactividad)
19. [`19_BACKLOG_SENTIDOS.md`](19_BACKLOG_SENTIDOS.md) — sentidos Tank + pendientes estrategia
20. [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md) — **doctrina Kaiser** (anclas, perfiles, pendientes manos)

## Carpetas auxiliares

- `_fuentes_extraidas/` — copia literal de `manual_v2/` + `catalog.json` (no editar a mano)
- `_destilar_fuentes.py` — script de re-extracción si cambia el manual

## Prototipo / código canónico

**`C:\Users\alans\Desktop\ShadowHarmy`** — Lilit de Hierro v2.0. Análisis Fase B en `13_ANALISIS_SHADOWHARMY.md`.

~~Existe `../ShadowHarmy/` como prototipo~~ → **es el repo de referencia para implementación.**

## Checkpoint Analista

Pipeline F1→F3 cerrado. Ver `logs_caja_negra/CHECKPOINT_FUNDACIONAL_QWEN14_V1.md`.
