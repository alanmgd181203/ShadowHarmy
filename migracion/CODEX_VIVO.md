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
- **Caja USDT (mega-cirugía 2026-08-12):** Tusk para en USDT · no compra MNT · no short de equilibrio · potencia pase = caja · MNT = Santo · [`CHECKPOINT_MEGA_CIRUGIA_EJERCITO_2026-08-12.md`](CHECKPOINT_MEGA_CIRUGIA_EJERCITO_2026-08-12.md)
- **Beru Vacío 1,1 desde wake (cirugía 2026-08-17):** un oficio · primer silbato Vacío ±1,1 / Hoz 1,0 desde el precio de wake, puntos del metro del manto · Mariscal nace con 10×G_min ($50 si G_min=$5) · relevo intacto 0,9/0,5/0,3 desde última Red · Mariscal cierra sin hijo · tumor «esperar ±0,9 del manto» extirpado · negociador/ping-pong/residual/capas/fusión/Mega extirpados · manos OFF · doctrina [`22_DOCTRINA_BERU.md`](22_DOCTRINA_BERU.md)
- **Beru lecturas cosecha + sin manto fuera (2026-08-19):** cada fill anota metro (vs manto) y Hoz (vs última Oz) · tierra sin metro no se siembra ni ensucia ojos Beru (casa ticker puede quedar) · flota Pergamino: cazando → acecho por % al oído · Mariscal cerrado al fondo · cache `v19`
- **Beru flota viva 100% (GO 2026-08-18):** ritual `arise_beru_flota_viva.py` · Hoz real en 22 Santos · grado = manto · bitácora viva · Igris OFF · Jess México hasta las 12
- **Beru ojos spot-only Tank (2026-08-18):** en ritual Beru el puente no abre lineal/inverso/futuros · Tank solo last spot Santos · garganta muda escribe `LLAMADO_AHOGADO` · HYPE ≠ HYPER en el metro · peldaño `PASO_HOZ_CAZA` restaurado (sin él el primer llamado mataba el pulso)
- **Beru red de ráfaga (2026-08-18):** Hoz gorda primero; si Bybit ahoga → mínima + acecho; si ni eso → radar interno al tocar oz. Bocados al lote mínimo, en serie, 0,25 s. Polvo no se planta. Camino feliz sin Market. Smoke `validar_beru_rafaga_smoke`
- **Beru cantidad = moneda del Santo (2026-08-18):** la Hoz y la ráfaga sellan qty como moneda, no como dólares. Rechazo de lote (170140) se anota una vez y no se trocea. Smoke altar + ráfaga.
- **Beru ojos + 0 vivo (precisión 2026-08-13):** last spot solo · sin fallback perp · 0 = promedio manto L+S · refresco al engorde Igris · basis → Greed · smoke `validar_beru_ojos_smoke`
- **Teatro Beru continuo v2 (FÓSIL 2026-08-16):** reiniciaba al mismo Beru desde la Hoz con Vacío 1,6; sus 30/90/365d son históricos y no prueban el relevo restaurado. Bloqueado para nuevas coronas. Prueba vigente: altar + 300 relevos fríos.
- **Pase batalla 17 capacidad segura (2026-08-15):** 22 candidatos auditados · 68 pasos por calor continuo / dólar incremental · inverso convierte límite base×last · 20% holgura · MNT inverso 40x · APT/LINK/BCH fuera · DOGE/SUI/XLM dentro · coronas $136/$457/$1295/$5024 · progreso migra por Santo+grado · [`PASE_BATALLA_17_SANTOS.md`](PASE_BATALLA_17_SANTOS.md)
- **Tusk caja USDT escalonada (2026-08-15):** LTC Funding→USDT Funding→UTA
  (no mezcla LTC colateral) · diario atómico con IDs reutilizables ·
  confirma transfer/convert antes de repetir · peaje >0,75% bloquea ·
  smoke frío ✅ · live LTC pendiente IP.
- **Igris liberación por niveles (2026-08-15):** libro mainnet permanente ·
  0 ojos · 1/3/10 duales · autónomo · reinicio no concede cupo · env solo baja ·
  ascenso explícito · smoke reinicio ✅.
- **Teatro legión (APAGADO 2026-08-15):** actor de capas/negociadores/fusión/Mega declarado fósil; ritual aborta y sus rankings no coronan · [`TEATRO_BERU_LEGION_SANO_2026-08-14.md`](TEATRO_BERU_LEGION_SANO_2026-08-14.md)
- **Pre-fuego 2026-08-12:** sello git antes de alinear este Codex · [`CHECKPOINT_PRE_FUEGO_2026-08-12.md`](CHECKPOINT_PRE_FUEGO_2026-08-12.md)
- **Bóveda MNT 4.0.1b/c (2026-08-02, LEGADO):** el ritual MNT+short+fees quedó **extirpado**. Checkpoint Tusk reescrito a caja USDT · [`CHECKPOINT_TUSK_BOVEDA_MNT.md`](CHECKPOINT_TUSK_BOVEDA_MNT.md)
- **Kaiser índice+sesgo 3.8.P4/P5 (2026-08-02):** índice absoluto · digest `sesgo_estructural` · backfill 3 mares (LTC/BTC/…+MNT) · metaverso pairs después · [`CHECKPOINT_KAISER_INDICE_SESGO.md`](CHECKPOINT_KAISER_INDICE_SESGO.md)
- **Kaiser sesgo vivo anti-ROJO (Jess `a1f2e7e`, 2026-08-02):** si Tank no tiene líder verde, el sesgo vivo lee del **nodo más fresco** (`_lider_para_sesgo`) — el clima no se apaga solo por latencia del semáforo
- **Manto vs cero estructural (2026-08-02):** frecuencia/ETA + puerta Igris cuentan **exceso vs cero** (no gap eterno) · `MANTO_CERO_ESTRUCTURAL` · informe `scripts/informe_sesgo_monarca.py` · [`INFORME_SESGO_ESTRUCTURAL.md`](INFORME_SESGO_ESTRUCTURAL.md)
- **Ritual ojos vivo México (Jess, 2026-08-02):** mainnet reiniciado · Tusk ~1525 sana · 15 bases × 3 mares con sesgo vivo tras calentamiento · Mac CPU alta al backfill (semáforo puede parpadear) · manos OFF
- **Teatro de sombras Igris (lab, 2026-08-04→06):** 1 óptica + **2** marchas de papel (asalto · personalizado) · preparado, no soltado · no es 4.0.3 · [`TEATRO_SOMBRAS_IGRIS.md`](TEATRO_SOMBRAS_IGRIS.md)
- **Oído Bellion 4.1.2 (2026-07-24):** tabla evento→nivel · `bellion_oido` · portal Cascada · sin LLM/Telegram
- **Pergamino React (local + celular):** Cascada → Manto Igris · Beru Sub-Santuario (flota por calor · botón Santos por rango · sin huecos ni 00 · tarjetita grado/saco/cazas · velas + rayas; 0 local = wake de esta vida · dual Vacío **solo semilla** · luego sangre contraria a la Hoz · Hoz/Red · hijo $G_min · chip saco = masa del Vacío ahora (acecho) o Hoz viva (caza) · lienzo clava encuadre (no replanta el campo) · × solo desde este arise; Hoz amarilla · Red azul · masa a la izquierda) · **Bellion susurro + foto viva completa** · Tusk/Tank/Greed dump crudo · Ascensión Tusk · **túnel PWA** `iniciar_panel_pwa` (HTTPS, sin matar Beru) · sello cache `v19`
- **Sub-Santuario Beru (2026-07-24):** `beru_asset_detail` · flota caza/neg · red engorde frontera · crónica `data/beru/cronicas/` · Bellion `beru_flota` / `beru_asset_details` · panel Streamlit
- **3.5.8c:** doctrina + **motor v1** `manto_ventana` (2026-07-17) · ranking fusión pendiente
- **Cuartel México:** remoto público + colaboradora Jessica — 2026-07-09
- **Checklist global:** ~69% (125/184 [x] + 5 [~]) · núcleo Fases 0–3 ~95%
- **Estado código:** Fase 3 ~92% · lives ✅ · pase Chamán firmado · falta Telegram/ranking fusión
- **Jess sync Bybit (2026-07-21):** lev+mínimos+piso manto vivos · 780 bases · origin sync México
- **Protocolo Jess puerta única (2026-08-07):** mandato vigente = [`ORDEN_ACTIVA_JESS.md`](ORDEN_ACTIVA_JESS.md) · PEGAR = recetas · regla `.cursor/rules/orden-jess.mdc` · índice [`ordenes_jess/README.md`](ordenes_jess/README.md)
- **G_min variable por Santo (2026-08-07→15):** peaje Beru = mínimo spot USDT (fallback linear, piso $1) · `core/g_min.py` · pase/ranking recalculado en el pase 17.
- **Pase batalla 13 Santos (2026-07-19):** **HISTÓRICO**, superado por el pase 17 · [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md)
- **Candado rango (2026-07-19):** `MONARCA_RANK_GATE` → Igris auditoría/despliegue + Beru casa (no live) + Ascensión viva desde `estado_vivo`
- **Director pase (2026-07-19→08-06):** `pase_director` — potencia/lote · **2 marchas operativas (asalto · personalizado)** · **fill 100% · reserva 1** · personalizado por T · legado táctico/forzada → asalto · altar hidrata JSON · `set_marcha_cli` · sello [`CHECKPOINT_MEGA_PRE_IGRIS.md`](CHECKPOINT_MEGA_PRE_IGRIS.md)
- **Ley Igris≠Greed · Asalto (2026-08-06):** Igris peaje aceptado / plantar; caza edge = Greed después; indicadores/peinado Kaiser después; orden Igris→Beru→Greed · [`CHECKPOINT_LEY_IGRIS_ASALTO_2026-08-06.md`](CHECKPOINT_LEY_IGRIS_ASALTO_2026-08-06.md) · doctrina `21`
- **Ritmo engorde dual (2026-08-06):** tras dual OK, aire ≥~5s (`IGRIS_ENGORDE_RITMO_S`) mismo Santo — Asalto exige no ametrallar libro · smoke `validar_igris_ritmo_engorde_smoke.py` · ley de Igris (no Greed)
- **Medidor+bocado Igris (2026-08-14):** Tusk 20 s Asalto / 60 s sueño + reconciliación del Santo pre-dual; asimetría calcula sobre mordida real, corrige como máximo el hueco y ≤50% del bocado · smoke sueño/misión
- **Libros Tusk / duración / ritmo:** `tusk_libros` · `marcha_duracion` · `marcha_ritmo_lote` (legado dormido tras sello 2 marchas)
- **Disparo dual Igris (2026-07-19):** L+S a la vez + salvavidas Market si una pierna huérfana (`IGRIS_DUAL_*`)
- **Escalera precios (2026-07-20):** micro-bocados Limit Igris+Greed · cancel no llenos · equilibrar Market · `core/escalera_precios.py`
- **Lotes Bybit qtyStep (2026-07-20):** `core/lote_bybit.py` lee BD Jess · peldaños/órdenes en múltiplos reales · [`CHECKPOINT_LOTES_BYBIT_2026-07-20.md`](CHECKPOINT_LOTES_BYBIT_2026-07-20.md)
- **Meta engorde pase (2026-07-20→08-06):** `meta_engorde_usd` = **100% acum del activo hasta el paso en foco** (alineado `sincronizar_logrados`) · etapas Soldado→… · Igris no engorda si `restante≤0` · smoke `validar_pase_metas_etapas_smoke.py` ✅
- **Semáforos matriz 3.7.P1 (2026-07-20):** `matriz_luces` V/A/R en digest Kaiser · sin órdenes · **3.7.P3** reclasificado a Greed (pausa)
- **Frecuencia manto 3.5.8b2 (2026-07-24):** 4 umbrales · ETA por marcha + `eta_lote_por_marcha` · rama personalizado
- **Kaiser memoria barcos (2026-07-19):** Tank horario → `data/kaiser/memoria/` · digest vivo · [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md)
- **Oído Monarca:** **Pergamino** (app) + susurro Bellion; Telegram = legado (`06_NOTIFICACIONES.md` v2)
- **Cuartel VPS (2026-08-02→03):** droplet SG · pivot **túnel VIP WireGuard** · [`27_VPS_TUNEL_WIREGUARD.md`](27_VPS_TUNEL_WIREGUARD.md)
- **Próximo:** cirugías menores **una a una** desde el cajón de dudas · **4.0.4** Beru (despertar aparte; manos chiquitas = duda B1, no GO) · Greed al último · USA no Arise live salvo orden
- **Panel cableado (2026-08-06):** estado_vivo → marcha · ventana 48–52 · meta engorde · ley_masa lectura · Tusk O₂/equity; Jess corre 4.0.3 Asalto · USA no ejecuta · [`PEGAR_JESS_IGRIS_LIVE_ASALTO.md`](PEGAR_JESS_IGRIS_LIVE_ASALTO.md)
- **Noche historial flota Igris (2026-08-06):** bóveda velas 1m spot+L+S de la flota manto · función ejército · **≠ 4.0.3** · [`PEGAR_JESS_NOCHE_HISTORIAL_IGRIS.md`](PEGAR_JESS_NOCHE_HISTORIAL_IGRIS.md) · motor Coliseo
- **Jess runbook informe:** [`JESS_INFORME_SESGO.md`](JESS_INFORME_SESGO.md)
- **Validar:** `validar_arise_igris_sim_smoke.py` · `validar_pase_director_smoke.py` · `validar_pase_metas_etapas_smoke.py` · `validar_marcha_duracion_smoke.py` · `validar_marcha_ritmo_lote_smoke.py` · `validar_tusk_libros_smoke.py` · `validar_manto_ventana_smoke.py` · `validar_igris_ritmo_engorde_smoke.py` · (+ smokes previos)
- **Igris sim 4.0.2:** [`CHECKPOINT_IGRIS_SIM_4_0_2.md`](CHECKPOINT_IGRIS_SIM_4_0_2.md) · manos atadas / ilusorias
- **Tono obligatorio:** `17_GUIA_MONARCA.md`

---

*Copiar este folder al repo del ejército y mantenerlo ahí como codex oficial.*
