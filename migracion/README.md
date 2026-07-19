# Migración — Códice operativo Shadow Army

**Destilación Fase A** (2026-06-30) — planos para Cursor / el Monarca.  
**Actualizado índice:** 2026-07-12.

**Empieza aquí (agente):** [`17_GUIA_MONARCA.md`](17_GUIA_MONARCA.md) → [`RESUMEN_EJECUTIVO.md`](RESUMEN_EJECUTIVO.md) → [`CODEX_VIVO.md`](CODEX_VIVO.md) → [`16_CHECKLIST_MAESTRO.md`](16_CHECKLIST_MAESTRO.md)

| Fase | Estado |
|------|--------|
| **A** — Destilación manual → planos | ✅ 2026-06-30 |
| **B** — ShadowHarmy vs planos | ✅ 2026-06-30 |
| **Código** — Fases 0–2 | ✅ · Fase 3 ~91% (2026-07-12) |

**Código canónico:** `C:\Users\alans\Desktop\ShadowHarmy`  
**Remoto:** https://github.com/alanmgd181203/ShadowHarmy  
**Codex junto al código:** `ShadowHarmy/migracion/`

## Para qué sirve esto

| No es | Sí es |
|-------|-------|
| Reemplazo del `manual_v2/` original | Planos de implementación + índice |
| El archivo `1M.txt` completo | Síntesis usable por el agente |
| Chat suelto | Fuente de verdad meta (checklist + doctrina) |

## Orden de lectura (núcleo)

1. [`17_GUIA_MONARCA.md`](17_GUIA_MONARCA.md) — **cómo hablar** (tono, Ejército, formato)
2. [`RESUMEN_EJECUTIVO.md`](RESUMEN_EJECUTIVO.md) — estado en una página
3. [`CODEX_VIVO.md`](CODEX_VIVO.md) — anti-quimera + snapshot
4. [`16_CHECKLIST_MAESTRO.md`](16_CHECKLIST_MAESTRO.md) — camino completo tareas
5. [`14_ROADMAP.md`](14_ROADMAP.md) — milestones M0–M5
6. [`11_MATRIZ_FASE_B.md`](11_MATRIZ_FASE_B.md) — tabla ✅⚠️❌

## Planos base (arquitectura)

7. [`00_NORTE.md`](00_NORTE.md) — visión y límites de v1
8. [`01_ARQUITECTURA.md`](01_ARQUITECTURA.md) — capas, flujo, async
9. [`02_GENERALES.md`](02_GENERALES.md) — roles Igris, Beru, Tusk, Tank, Greed, Bellion…
10. [`03_RIESGO_Y_REGLAS.md`](03_RIESGO_Y_REGLAS.md) — reglas firmes + sandbox
11. [`04_INFRA_API.md`](04_INFRA_API.md) — Bybit, Bridge, persistencia
12. [`05_ESTRATEGIA_EJECUCION.md`](05_ESTRATEGIA_EJECUCION.md) — ships, grid, pentiverso
13. [`06_NOTIFICACIONES.md`](06_NOTIFICACIONES.md) — Telegram y consola
14. [`07_GLOSARIO.md`](07_GLOSARIO.md) — vocabulario Monarca
15. [`08_DECISIONES_PENDIENTES.md`](08_DECISIONES_PENDIENTES.md) — cerrado vs abierto

## Catálogo / método / protocolo

16. [`09_CATALOGO_ESPECIFICACIONES.md`](09_CATALOGO_ESPECIFICACIONES.md) — SA-001…SA-139
17. [`10_FUENTES_Y_METODO.md`](10_FUENTES_Y_METODO.md) — de dónde salió cada cosa
18. [`12_PROTOCOLO_CURSOR.md`](12_PROTOCOLO_CURSOR.md) — cómo usar esto en sesiones
19. [`13_ANALISIS_SHADOWHARMY.md`](13_ANALISIS_SHADOWHARMY.md) — análisis código canónico
20. [`15_IDEAS_FUTURO.md`](15_IDEAS_FUTURO.md) — backlog utopía

## Doctrinas y runbooks (vivos)

21. [`18_ARRANQUE_TESTNET.md`](18_ARRANQUE_TESTNET.md) — cómo despertar el ejército en testnet
22. [`19_BACKLOG_SENTIDOS.md`](19_BACKLOG_SENTIDOS.md) — sentidos Tank + pendientes estrategia
23. [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md) — Kaiser (anclas, perfiles, manos)
24. [`21_DOCTRINA_IGRIS.md`](21_DOCTRINA_IGRIS.md) — Igris manto · §E v2 despliegue
25. [`22_DOCTRINA_BERU.md`](22_DOCTRINA_BERU.md) — Beru caza · residual · Mega · fricción
26. [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md) — capital, tiers, escalera Monarca  
26b. [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md) — pase Coliseo Aspirante→Chamán (2026-07-19)

## Carpetas auxiliares

- `_fuentes_extraidas/` — copia literal de `manual_v2/` + `catalog.json` (no editar a mano)
- `_destilar_fuentes.py` — script de re-extracción si cambia el manual

## Prototipo / código canónico

**`C:\Users\alans\Desktop\ShadowHarmy`** — Lilit de Hierro v2.0. Análisis Fase B en `13_ANALISIS_SHADOWHARMY.md`.

## Checkpoint Analista

Pipeline F1→F3 cerrado. Ver `logs_caja_negra/CHECKPOINT_FUNDACIONAL_QWEN14_V1.md` (si existe en origen).
