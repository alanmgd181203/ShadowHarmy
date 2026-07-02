# 12 — Protocolo Cursor (cómo usar esta migración)

## Antes de cada sesión de código

1. Lee `00_NORTE.md` si es sesión nueva o pasó tiempo.
2. Identifica el **General** o capa (`02`, `04`, `05`…).
3. Consulta SA-ID en `09_CATALOGO_ESPECIFICACIONES.md` si la duda es "¿qué pidió el manual?".
4. No re-debatas decisiones en `08` marcadas como cerradas.

## Prompt sugerido al abrir chat

```
Contexto: Shadow Army — repo C:\Users\alans\Desktop\ShadowHarmy
Fuente spec: Monarca/migracion/ (13 si es auditoría, 14 si es implementar)
Código manda; ideas manual en 15_IDEAS_FUTURO si divergen.
Tarea: [concreta]
```

## Indexación

- `manual_v2/` puede estar en `.cursorignore` — **usa `migracion/`** como entrada.
- Regla Cursor: `.cursor/rules/monarca-comunicacion.mdc` (tono Monarca, `alwaysApply`).
- Opcional extra: regla `@migracion/README.md` en `.cursor/rules/shadow-army.mdc`.

## Cuando dudar del manual original

1. Buscar en `1M.txt` (raíz repo) keyword del glosario.
2. Bloque completo en `_fuentes_extraidas/sandbox_*.md`.
3. Chroma vía Monarca solo si hace falta trazabilidad chroma id.

## Anti-patrones (evitar quimera)

| No hacer | Hacer |
|----------|-------|
| Pegar 1M chars al chat | CitAR SA-ID o sección migracion |
| Nuevo General sin D-xx | Propuesta en `08` pendientes primero |
| Arreglar Beru e Igris en mismo PR sin mapa | Un milestone, una fila matriz |
| Copiar código Gemini suelto | Integrar vía Greed→Bridge |
| Mezclar fix Monarca pipeline con ShadowHarmy | Repos separados |

## Actualización del códice

Si cierras decisión o implementas spec:

1. `08_DECISIONES_PENDIENTES.md` — mover a cerradas.
2. `11_MATRIZ_FASE_B.md` — estado ✅⚠️❌.
3. Opcional: nueva fila SA en `09` si nace regla nueva (ingesta incremental futura).

## Fase B (completada 2026-06-30)

- Repo: `C:\Users\alans\Desktop\ShadowHarmy`
- Entregables: `13_ANALISIS_SHADOWHARMY.md`, `11_MATRIZ` actualizada, `14_ROADMAP`, `15_IDEAS_FUTURO`

## Archivos mínimos por tipo de tarea

| Tarea | Leer |
|-------|------|
| Bridge / Bybit | 04, 03 R07, 11 T-01 |
| Beru / ships | 02 Beru, 05, 09 tag Perfiles |
| Margen | 02 Igris, 03 R02/R04 |
| Telegram | 06 |
| Arbitraje | 05, 09 Arbitraje |
| Refactor arise | 01, 02 matriz archivos |
