# Codex vivo — contrato de trabajo

Este directorio es el **mapa operativo** del Shadow Army. No es archivo muerto del Analista: se **actualiza en cada sesión de código**.

## Ubicación

| Copia | Rol |
|-------|-----|
| `ShadowHarmy/migracion/` | **Canónica** — junto al código que corre |
| `Monarca/migracion/` | Espejo / origen Fase A+B (puede quedar desfasada) |

Trabajar siempre desde la copia en **ShadowHarmy** tras el copy.

## Reglas del juego

### 1. Código + codex juntos

Cada PR o sesión que toque `ShadowHarmy/*.py` debe dejar **al menos uno** de estos actualizados:

- `11_MATRIZ_FASE_B.md` — fila afectada (estado ✅⚠️❌)
- `08_DECISIONES_PENDIENTES.md` — si cerramos o abrimos decisión
- `14_ROADMAP.md` — si completamos milestone Mx
- `13_ANALISIS_SHADOWHARMY.md` — solo si cambia arquitectura grande

### 2. El codex manda en meta; el código manda en hechos

- Si el **código ya hace X** y el codex dice otra cosa → **actualizar codex** (código gana en hechos).
- Si propones **Y contra el codex** sin decidir explícitamente → el agente **avisa** y no implementa a ciegas (anti-quimera).

### 3. Frase para contradecir el mapa

Si quieres romper una regla cerrada (`08` D-xx) o una REGLA:

> "Override codex: [D-xx o REGLA-Rxx] — nuevo criterio: …"

Sin eso, se asume que seguimos el mapa.

### 4. Qué hace el agente (Cursor) en cada sesión

0. Leer **`17_GUIA_MONARCA.md`** — tono, perfil del Monarca, cómo explicar.
1. Leer `RESUMEN_EJECUTIVO.md` + módulo relevante.
2. Implementar en código.
3. **Retroalimentar** matriz/decisiones/roadmap.
4. Si la idea contradice `03_RIESGO`, `08` o `15` sin override → **parar y avisar**.

### 5. Ideas futuro no se borran

Lo que no implementemos va a `15_IDEAS_FUTURO.md`, no se descarta.

## Anti-quimera (checklist mental)

- [ ] ¿Esta tarea está en `14_ROADMAP` o es scope creep?
- [ ] ¿Contradice una fila ✅ de `11`?
- [ ] ¿Mezcla fix Monarca pipeline con ShadowHarmy?
- [ ] ¿Hay dos fuentes de verdad (chat vs migracion)?

### 5. Snapshot actual

- **Fase A+B:** 2026-06-30
- **Estado código:** M0 pendiente — ver `16_CHECKLIST_MAESTRO.md`
- **Próximo ítem:** 1.3.3 (test arise.py) → 1.4 (higiene)

---

*Copiar este folder al repo del ejército y mantenerlo ahí como codex oficial.*
