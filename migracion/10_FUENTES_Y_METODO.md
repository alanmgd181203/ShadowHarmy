# 10 — Fuentes y método

## Objetivo de esta destilación

**Fase A** del plan acordado: exprimir el Analista (`fundacional_qwen14_v1`) en documentación operativa para Cursor, **sin** mega corrida F1–F3 y **sin** auditoría de código final (Fase B).

Generado: **2026-06-30**

---

## Fuentes primarias

| Fuente | Tamaño | Uso |
|--------|--------|-----|
| `manual_v2/01_capas_reglas.md` | 6.8 KB | Reglas firmes Códice |
| `manual_v2/02_perfiles_bots.md` | 2.0 KB | Igris cristalizado |
| `manual_v2/03_gestion_intercambios.md` | 2.3 KB | Beru/Iron/Tusk v2.3 |
| `manual_v2/04_logica_tecnica.md` | 1.8 KB | Simuladores |
| `manual_v2/sandbox/*.md` | ~335 KB | 122 bloques ideas |
| `1M.txt` | 1.26M chars | Referencia cruzada keywords |
| `logs_caja_negra/DESTILACION_EDITORIAL_RESPUESTAS.md` | — | Política P0 |
| `logs_caja_negra/CHECKPOINT_FUNDACIONAL_QWEN14_V1.md` | — | Estado pipeline |
| `../ShadowHarmy/` | 12 archivos | Notas prototipo (no canónico) |

## Frecuencias en `1M.txt` (muestreo)

| Keyword | Apariciones |
|---------|-------------|
| Tusk | 1039 |
| Igris | 883 |
| Monarca | 957 |
| Beru | 775 |
| Iron | 604 |
| Bellion | 479 |
| Tank | 315 |
| Greed | 216 |
| LTC | 140 |
| Bybit | 136 |
| arbitraje | 107 |

## Método

1. **Extracción** — `_destilar_fuentes.py` copia manual → `_fuentes_extraidas/` + `catalog.json`.
2. **Clasificación** — cada bloque → tipo REGLA | DISENO | DOCTRINA | CRISTALIZADO | EXPLORACION.
3. **Síntesis** — documentos 00–08 redactados para implementación (no copia literal sandbox).
4. **Catálogo** — SA-001…SA-139 en `09_CATALOGO_ESPECIFICACIONES.md`.
5. **Exclusión** — texto narrativo puro, duplicados obvios, plantillas vacías (`incubacion`, `perfiles_bots` sandbox).

## Lo que NO se incluyó

- Volcado íntegro `1M.txt` (disponible en raíz para disputas).
- 307 documentos Chroma (accesibles vía Monarca si hace falta).
- `archive/legacy_bots/` (cursorignored; referencia histórica).
- Código fuente completo ShadowHarmy (solo citas en Fase B template).

## Re-generar

```bat
python migracion\_destilar_fuentes.py
```

Luego revisar manualmente 00–08 si el manual cambió.

## Provenance Analista

| Fase | Modelo | Shards |
|------|--------|--------|
| 1 Aduana | Qwen 14B checkpoint | 308 |
| 2 Destilación | gemma2:27b | 308 |
| 3 Bibliotecario | llama3:latest | 308 |

## Fase B (2026-06-30)

- Código canónico auditado: `C:\Users\alans\Desktop\ShadowHarmy` (12 `.py`)
- Entregables: `13_ANALISIS_SHADOWHARMY.md`, `11_MATRIZ` (completa), `14_ROADMAP`, `15_IDEAS_FUTURO`
- Principio: **código manda**; manual aporta backlog sin descartar ideas
