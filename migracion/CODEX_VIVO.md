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
- **Tusk tesorería UTA (2026-08-01):** MNT/hedge/disponible → oxígeno de guerra · `tusk_tesoreria` · masa_autorizada real
- **Ritual ojos 4.0.1 (2026-08-01):** `arise_ojos_tusk.py` — Tusk+Tank+Kaiser sin disparos · Igris/Greed/Beru hibernados
- **Bóveda MNT 4.0.1b/c (2026-08-02):** ideal + Convert≠ley · **sucio→reset→ideal** (peaje OK) · capital_mando frío · manos OFF · [`CHECKPOINT_TUSK_BOVEDA_MNT.md`](CHECKPOINT_TUSK_BOVEDA_MNT.md)
- **Kaiser índice+sesgo 3.8.P4/P5 (2026-08-02):** índice absoluto · digest `sesgo_estructural` · backfill 3 mares (LTC/BTC/…+MNT) · metaverso pairs después · [`CHECKPOINT_KAISER_INDICE_SESGO.md`](CHECKPOINT_KAISER_INDICE_SESGO.md)
- **Kaiser sesgo vivo anti-ROJO (Jess `a1f2e7e`, 2026-08-02):** si Tank no tiene líder verde, el sesgo vivo lee del **nodo más fresco** (`_lider_para_sesgo`) — el clima no se apaga solo por latencia del semáforo
- **Manto vs cero estructural (2026-08-02):** frecuencia/ETA + puerta Igris cuentan **exceso vs cero** (no gap eterno) · `MANTO_CERO_ESTRUCTURAL` · informe `scripts/informe_sesgo_monarca.py` · [`INFORME_SESGO_ESTRUCTURAL.md`](INFORME_SESGO_ESTRUCTURAL.md)
- **Ritual ojos vivo México (Jess, 2026-08-02):** mainnet reiniciado · Tusk ~1525 sana · 15 bases × 3 mares con sesgo vivo tras calentamiento · Mac CPU alta al backfill (semáforo puede parpadear) · manos OFF
- **Oído Bellion 4.1.2 (2026-07-24):** tabla evento→nivel · `bellion_oido` · portal Cascada · sin LLM/Telegram
- **Pergamino React (local):** Cascada → Manto Igris · Beru Sub-Santuario · **Bellion susurro** · Ascensión Tusk
- **Sub-Santuario Beru (2026-07-24):** `beru_asset_detail` · flota caza/neg · red engorde frontera · crónica `data/beru/cronicas/` · Bellion `beru_flota` / `beru_asset_details` · panel Streamlit
- **3.5.8c:** doctrina + **motor v1** `manto_ventana` (2026-07-17) · ranking fusión pendiente
- **Cuartel México:** remoto público + colaboradora Jessica — 2026-07-09
- **Checklist global:** ~69% (125/184 [x] + 5 [~]) · núcleo Fases 0–3 ~95%
- **Estado código:** Fase 3 ~92% · lives ✅ · pase Chamán firmado · falta Telegram/ranking fusión
- **Jess sync Bybit (2026-07-21):** lev+mínimos+piso manto vivos · 780 bases · origin sync México
- **Pase batalla 13 Santos (2026-07-19):** vacío 1,6 % · rangos Aspirante→Chamán · [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md)
- **Candado rango (2026-07-19):** `MONARCA_RANK_GATE` → Igris auditoría/despliegue + Beru casa (no live) + Ascensión viva desde `estado_vivo`
- **Director pase (2026-07-19→08-03):** `pase_director` — potencia/lote · **4 marchas** · **fill 100% · reserva 1** · ritmo de lote · personalizado por T · altar hidrata JSON · `set_marcha_cli` · sello [`CHECKPOINT_MEGA_PRE_IGRIS.md`](CHECKPOINT_MEGA_PRE_IGRIS.md)
- **Libros Tusk / duración / ritmo:** `tusk_libros` · `marcha_duracion` · `marcha_ritmo_lote`
- **Disparo dual Igris (2026-07-19):** L+S a la vez + salvavidas Market si una pierna huérfana (`IGRIS_DUAL_*`)
- **Escalera precios (2026-07-20):** micro-bocados Limit Igris+Greed · cancel no llenos · equilibrar Market · `core/escalera_precios.py`
- **Lotes Bybit qtyStep (2026-07-20):** `core/lote_bybit.py` lee BD Jess · peldaños/órdenes en múltiplos reales · [`CHECKPOINT_LOTES_BYBIT_2026-07-20.md`](CHECKPOINT_LOTES_BYBIT_2026-07-20.md)
- **Meta engorde pase (2026-07-20→08-03):** `meta_engorde_usd` = **100% delta** · Igris no engorda si `restante≤0` (solo ventana) · ratio USD@entrada
- **Semáforos matriz 3.7.P1 (2026-07-20):** `matriz_luces` V/A/R en digest Kaiser · sin órdenes · **3.7.P3** reclasificado a Greed (pausa)
- **Frecuencia manto 3.5.8b2 (2026-07-24):** 4 umbrales · ETA por marcha + `eta_lote_por_marcha` · rama personalizado
- **Kaiser memoria barcos (2026-07-19):** Tank horario → `data/kaiser/memoria/` · digest vivo · [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md)
- **Oído Monarca:** **Pergamino** (app) + susurro Bellion; Telegram = legado (`06_NOTIFICACIONES.md` v2)
- **Cuartel VPS (2026-08-02→03):** droplet SG · pivot **túnel VIP WireGuard** · [`27_VPS_TUNEL_WIREGUARD.md`](27_VPS_TUNEL_WIREGUARD.md)
- **Próximo:** corrida viva **4.0.2** `arise_igris_sim.py` (VIP OK) → luego **4.0.3** live
- **Jess runbook informe:** [`JESS_INFORME_SESGO.md`](JESS_INFORME_SESGO.md)
- **Validar:** `validar_arise_igris_sim_smoke.py` · `validar_pase_director_smoke.py` · `validar_marcha_duracion_smoke.py` · `validar_marcha_ritmo_lote_smoke.py` · `validar_tusk_libros_smoke.py` · `validar_manto_ventana_smoke.py` · (+ smokes previos)
- **Igris sim 4.0.2:** [`CHECKPOINT_IGRIS_SIM_4_0_2.md`](CHECKPOINT_IGRIS_SIM_4_0_2.md) · manos atadas / ilusorias
- **Tono obligatorio:** `17_GUIA_MONARCA.md`

---

*Copiar este folder al repo del ejército y mantenerlo ahí como codex oficial.*
