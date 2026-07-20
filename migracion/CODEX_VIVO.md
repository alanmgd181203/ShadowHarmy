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
- **M0–M2:** COMPLETADO — 2026-07-05 (pentiverso dual + ciclo ejército)
- **M2.7–M2.12:** Tank sentidos · Kaiser · Greed · Beru Proto · Igris §E v1 · plan 23
- **M2.13 Beru doctrina cirugía:** residual / frontera / colisión oz / Mega reset / fricción / flota — 2026-07-09→12 (smokes ✅)
- **M2.14 Igris §E v2 + panel:** `igris_despliegue` · jurisdicción · Pergamino — 2026-07-11→12
- **3.10.7b Igris live:** PASS México 2026-07-12
- **3.9.9 Beru live:** PASS México 2026-07-16 (Jess · `61d7c2e` · flota 22 USDT)
- **Pergamino React (local):** Cascada → Manto → AssetDetail; Sub-Santuario **cableado Bridge**; smoke asset_detail 6/6
- **3.5.8c:** doctrina + **motor v1** `manto_ventana` (2026-07-17) · ranking fusión pendiente
- **Cuartel México:** remoto público + colaboradora Jessica — 2026-07-09
- **Checklist global:** ~69% (125/184 [x] + 4 [~]) · núcleo Fases 0–3 ~95%
- **Estado código:** Fase 3 ~92% · lives ✅ · pase Chamán firmado · falta Telegram/ranking fusión
- **Jess sync Bybit (2026-07-18):** lev+mínimos+piso manto vivos · LTC 50/50
- **Pase batalla 13 Santos (2026-07-19):** vacío 1,6 % · rangos Aspirante→Chamán · [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md)
- **Candado rango (2026-07-19):** `MONARCA_RANK_GATE` → Igris auditoría/despliegue + Beru casa (no live) + Ascensión viva desde `estado_vivo`
- **Director pase (2026-07-19):** `pase_director` — potencia/lote/reserva · 3 marchas (fees / ½ fees / asalto) · Beru tras manto · altar UI on · `panel_http_server` guarda marcha · Táctico=Limit
- **Disparo dual Igris (2026-07-19):** L+S a la vez + salvavidas Market si una pierna huérfana (`IGRIS_DUAL_*`)
- **Escalera precios (2026-07-20):** micro-bocados Limit Igris+Greed · cancel no llenos · equilibrar Market · `core/escalera_precios.py`
- **Lotes Bybit qtyStep (2026-07-20):** `core/lote_bybit.py` lee BD Jess · peldaños/órdenes en múltiplos reales · [`CHECKPOINT_LOTES_BYBIT_2026-07-20.md`](CHECKPOINT_LOTES_BYBIT_2026-07-20.md) · Jess: `JESS_SINCRONIZAR_BYBIT.md`
- **Kaiser memoria barcos (2026-07-19):** Tank horario → `data/kaiser/memoria/` · digest vivo · [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md)
- **Oído Monarca:** **Pergamino** (app); Telegram = legado (`06_NOTIFICACIONES.md` v2)
- **Próximo ítem checklist:** **4.1.2** eventos Pergamino · **3.5.8c** fusión · **3.7.P***
- **Validar:** `validar_lote_bybit_smoke.py` · `validar_pase_director_smoke.py` · `validar_escalera_precios_smoke.py` · `validar_igris_smoke.py`
- **Tono obligatorio:** `17_GUIA_MONARCA.md`

---

*Copiar este folder al repo del ejército y mantenerlo ahí como codex oficial.*
