# 16 — Checklist maestro (camino a la utopía)

**Lista ordenada de tareas y subtareas** — de lo urgente a la visión final del Ejército de Sombras.

- **Repo código:** `C:\Users\alans\Desktop\ShadowHarmy`
- **Codex:** esta carpeta `migracion/`
- **Para agente nuevo:** leer `RESUMEN_EJECUTIVO.md` → `CODEX_VIVO.md` → **este archivo**
- **Al completar ítem:** marcar `[x]` aquí + actualizar `11_MATRIZ` / `14_ROADMAP`

**Leyenda prioridad:** 🔴 bloqueante · 🟠 P0 negocio · 🟡 P1 · 🟢 P2 · 🔮 utopía

---

## FASE 0 — Arranque del proyecto (antes de codear)

*Sin esto, cada sesión vuelve a ser quimera.*

- [x] **0.1** Copia `migracion/` vive en `ShadowHarmy/migracion/` (junto al código)
- [x] **0.2** Leer `00_NORTE.md` + `13_ANALISIS_SHADOWHARMY.md` (estado actual)
- [x] **0.3** `.env` con `BYBIT_API_KEY`, `BYBIT_API_SECRET`, `MODO_TESTNET=True`
- [x] **0.4** Regla Cursor / prompt fijo: citar `migracion/` + protocolo `CODEX_VIVO.md`
- [x] **0.5** Decisión registrada en `08`: solo ShadowHarmy para runtime (D-10)

---

## FASE 1 — 🔴 M0: El ejército despierta (código que arranca)

*Criterio fase:* `python arise.py` corre 60 s sin excepción.

### 1.1 Beru — cirugía estructural
- [x] **1.1.1** Indentar `plantar_semilla_adan` dentro de `BeruCazador`
- [x] **1.1.2** Indentar `auditar_gatillos_adan` dentro de la clase
- [x] **1.1.3** Indentar `ejecutar_acordeon_asimetrico` dentro de la clase
- [x] **1.1.4** Indentar `evaluar_colisiones_y_fusion` dentro de la clase
- [x] **1.1.5** Implementar `limpiar_legion()` (expurgar COSECHADO, FUSIONADO, fantasmas)
- [x] **1.1.6** `python -m py_compile generales/beru.py` OK
- [x] **1.1.7** Decidir criterio SUPER_FUSION: ¿total o selectiva? (ver `08` T-08)

### 1.2 Modelos — contrato BeruShip
- [x] **1.2.1** Añadir `red_adan: float = 0.0` a `BeruShip`
- [x] **1.2.2** Añadir `oz_adan: float = 0.0`
- [x] **1.2.3** Añadir `max_favor: float = 0.0`
- [x] **1.2.4** Revisar uso de `red`/`oz` legacy vs nuevos campos (unificado: eliminados legacy)

### 1.3 Greed — rutas Igris faltantes
- [x] **1.3.1** Handler `REBALANCEO_IGRIS` (evalúa reducir gordo vs abrir flaco, respeta banda)
- [x] **1.3.2** Handler `ENGORDAR_MANTO` (crece manto sin BeruShip, divide si rompe banda)
- [x] **1.3.3** Tests manuales: Igris delega → Greed ejecuta sin error (arise.py 51s+ sin crash)

### 1.4 Proyecto — higiene
- [x] **1.4.1** Crear `requirements.txt` (pybit, websockets, streamlit)
- [x] **1.4.2** README.md raíz ShadowHarmy (cómo arrancar, env, migracion)
- [x] **1.4.3** Panel Streamlit (`panel.py`) + estado vivo en Bellion

### 1.5 Cierre M0
- [x] **1.5.1** Actualizar `11_MATRIZ`: G-Beru, S-01, S-02, S-04 → ✅
- [x] **1.5.2** Marcar M0 completo en `14_ROADMAP.md` (test arise.py 51s+ sin crash — 2026-07-03)

---

## FASE 2 — 🟠 M1: Primer sangre real (testnet) — **COMPLETA** (2026-07-04)

*Criterio infra:* Bridge dispara, fill confirmado, NAV sync, trade manual documentado. ✅  
*Criterio doctrina (ciclo ejército + manto):* **movido a Fase 3.5 / 3.6** — ver abajo.

### 2.1 Bridge — manos (no solo ojos)
- [x] **2.1.1** `place_order(market/limit)` wrapper con idempotencia (`orderLinkId`)
- [x] **2.1.2** `cancel_order` / `amend_order` básico
- [x] **2.1.3** Poll o WS privado para **fill confirmado** (REGLA-R07)
- [x] **2.1.4** Reemplazar `except: pass` en NAV por log Bellion + reintento
- [x] **2.1.5** Documentar mainnet-ojos + testnet-manos en `04_INFRA_API.md`

### 2.2 Modo simulación vs real
- [x] **2.2.1** Flag `MODO_SIMULACION` en config (default True hasta validar)
- [x] **2.2.2** Si `MODO_SIMULACION=False` → prohibir `DISPARO_SIMULADO`
- [x] **2.2.3** `confirmar_reserva` solo tras fill real cuando modo live

### 2.3 Cableado Greed → Bridge
- [x] **2.3.1** `_ejecutar_caza_multiverse` → orden real + fill → luego `confirmar_reserva`
- [x] **2.3.2** `_ejecutar_cosecha_multiverse` → cierre real + fill
- [x] **2.3.3** Poda / espejos → órdenes de reducción reales (o sim hasta validar lógica)

### 2.4 Tusk — coherencia NAV
- [x] **2.4.1** Tras fill, reconciliar `pesos` con posiciones exchange
- [x] **2.4.2** No liberar reserva si orden rechazada

### 2.5 Validación M1
- [x] **2.5.1** 1 trade redondo testnet documentado (timestamp, ids, PnL)
- [x] **2.5.2** Matriz: T-01, T-03 → ✅
- [x] **2.5.3** 24 h testnet sin crash (stretch) — *~20 h continuas 2026-07-04, sin crash fatal*

### 2.6 Cierre M1 (infra)
- [x] **2.6.1** Marcar avance M1 en `14_ROADMAP.md`
- [x] **2.6.2** Matriz T-01, T-03 → ✅ en `11_MATRIZ_FASE_B.md`
- [x] **2.6.3** ~~Ciclo ejército~~ → **reubicado 3.6**
- [x] **2.6.4** ~~Igris→Bridge manto~~ → **reubicado 3.5**

---

## FASE 3 — 🟡 M2: Pentiverso dual LTC+BTC — **~91%** (2026-07-12)

*Criterio fase:* 10 `MarketContext` con precio real; Greed USDT×USDC en LTC y BTC; ciclo ejército validado (3.6). **Beru doctrina 3.9** + **live 3.9.9 ✅**. **Igris §E v2 + live 3.10.7b ✅**. **3.5.8c** doctrina ventana 48–52 ✅ checkpoint · motor/ranking pendientes. **Pendiente:** 3.7.P*, Karmish.

*Validación 2026-07-05:* `validar_m2.py` → **10/10 mares**. *Validación Beru 2026-07-09:* smokes + `validar_ciclo_beru_eth.py`. *Igris 2026-07-12:* `validar_igris_smoke.py` + `igris_despliegue`. Runbook: `18_ARRANQUE_TESTNET.md`.

### 3.1 Tank — visión completa
- [x] **3.1.0–3.1.4** — ✅ 10/10 mares dual LTC+BTC (USDC lineal = reflejo spot)
- [x] **3.1.5** Poblar `TankNode.muros` — ✅

### 3.2 Greed — multiverso operativo
- [x] **3.2.1** Escuadrón suicida — ✅ mezcla USDT×USDC por activo (LTC+BTC)
- [x] **3.2.2** Radares Beru / Igris — ✅ Beru casa; Igris `FRENTES_MANTO_ALL`
- [x] **3.2.3** Multicruce spot 3–4p — `greed_multicruce.py` + smoke (`validar_greed_multicruce_smoke.py`)
- [x] **3.2.4** Basis hold / manto temporal — `greed_basis.py` + panel + smoke (`validar_greed_basis_smoke.py`)

### 3.3 Persistencia — muerte digna
- [x] **3.3.1** `signal` handler → `bellion.ley_de_sucesion` — ✅ probado
- [x] **3.3.2** Recovery al arranque — ✅ probado

### 3.4 Cierre M2 (infra)
- [x] **3.4.1** Matriz: G-Tank, S-03 → ✅
- [x] **3.4.2** Dashboard pentiverso — ✅ panel + consola agrupado LTC/BTC

### 3.5 Primer manto operativo *(ex M1 — 2.6.4)*
- [x] **3.5.1** Igris engorde/rebalanceo/poda/espejos → Bridge + fill en live *(código; validar con MODO_SIMULACION=False)*
- [x] **3.5.2** Bootstrap manto: primer par L/S cuando `pesos` vacíos *(BOOTSTRAP_MANTO_FRACCION=0.25)*
- [x] **3.5.3** Smoke Igris — `scripts/validar_igris_smoke.py` (banda, fases, frentes)
- [x] **3.5.4** Panel + Bellion — bloque `igris` en `estado_vivo.json` (fase, acción heurística, funding pasivo)
- [x] **3.5.5** Doctrina Igris §A — [`21_DOCTRINA_IGRIS.md`](21_DOCTRINA_IGRIS.md) *(2026-07-05)*
- [x] **3.5.6** §C parcial — VIP en ley marcial + `manto_touch` Greed→Igris
- [x] **3.5.7** Beru capital + ProtoBeru — `22_DOCTRINA_BERU.md`, `beru_tier.py`, `beru_capital.py`, cableado `beru.py`, capitanes 1.2/1.6%
- [x] **3.5.8a** Igris §E v1 — bootstrap inverse L + lineal S + promedios pierna *(2026-07-05)*
- [x] **3.5.8b** Igris §E v2 — Ancla + paciencia Ask/Bid + mordida sin pinza 85% + reloj invertido Kaiser (`core/igris_despliegue.py`, 2026-07-12)
- [~] **3.5.8c** Igris §E — **ventana 48–52 / long-primero** — doctrina ✅ · motor ✅ `core/manto_ventana.py` (Igris/mercado/Bellion) · ranking/mitad/dual-Kaiser/manto-completo aplazados a fusión

- [~] **3.5.9** Plan crecimiento Monarca — [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md) + `plan_crecimiento.py` *(v1 checkpoint 2026-07-06; botín runtime y mérito pendiente)*

### 3.6 Validación ciclo ejército *(ex M1 — 2.6.3)*
- [x] **3.6.1** 1 ciclo CAZA → COSECHA en Bellion — ✅ `scripts/probar_ciclo_beru.py` + historial
- [x] **3.6.2** Gate `MODO_SIMULACION=False` — ✅ `core/validacion.py` advierte en `arise.py`; live testnet cuando Monarca decida

### Scripts de validación (automatizados)
- [x] **3.V1** `scripts/validar_m2.py` — pentiverso 10 mares
- [x] **3.V2** `scripts/probar_ciclo_beru.py` — ciclo 3.6.1 sim
- [x] **3.V3** `scripts/validar_checklist.py` — informe `data/validacion_checklist.json`
- [x] **3.V4** `core/validacion.py` — gates reutilizables por fase

### 3.7 Tank — sentidos ampliados *(post M2 — COMPLETA 2026-07-05)*

*Criterio fase:* matriz spreads + desvío índice vivos por WS; panorama global cableado; Bellion/panel publican; **sin disparos** (solo ojos).  
*Validación:* `python scripts/validar_panorama_tank.py --segundos 35` → `data/validacion_panorama_tank.json`.  
*Nota geo:* Binance WS (451) y REST Spread/Alpha/Convert (403) pueden fallar desde USA; Fase 1 Bybit OK.

#### Catálogo Bybit (Trinidad + Bridge)
- [x] **3.7.1** Spot completo ~598 pares + shards WS (`trinidad`, `bridge`)
- [x] **3.7.2** Linear/inverse perp + futuros dated en cache/config
- [x] **3.7.3** `bases_huerfanas` — perp sin spot USDT Bybit (`calcular_bases_huerfanas`)

#### Ojos calculados (WS Bybit)
- [x] **3.7.4** Matriz spreads — lineal↔inverso, spot↔perp, basis, USDT↔USDC (`core/spreads.py`)
- [x] **3.7.5** Funding + `indexPrice` inyectados desde ticker derivados
- [x] **3.7.6** **Fase 1** — `calcular_desvios_indice` (perp vs indexPrice local)

#### Segundo mar + REST
- [x] **3.7.7** **Fase 2** — `BinanceRefBridge` + `calcular_panorama_global` (huérfanas vs Binance spot)
- [x] **3.7.8** Sentidos REST: spread producto, alpha, convert, convert quotes (`sentidos_extra.py`)

#### Integración ejército
- [x] **3.7.9** Tank snapshots: `desvios_indice`, `panorama_global`, `convert_quotes`
- [x] **3.7.10** Bellion → `estado_vivo.json`; panel secciones panorama/desvíos/convert quotes
- [x] **3.7.11** `arise.py` — gather único + Binance ref opcional (`BINANCE_REF_ENABLED`)
- [x] **3.7.12** Fix arranque `TankCluster.sentidos_extra` + `ACTIVOS_HUERFANOS` / `BASES_PANORAMA` en config

#### Validación sentidos
- [x] **3.V5** `scripts/validar_sentidos_extra.py` — matriz + REST poll
- [x] **3.V6** `scripts/validar_panorama_tank.py` — Fase 1 + Fase 2 (35 s WS)
- [x] **3.V7** Backlog vivo: `19_BACKLOG_SENTIDOS.md`

#### Pendiente estrategia *(no bloquea Fase 4)*
- [ ] **3.7.P1** Semáforos sobre matriz spreads — umbral disparo
- [ ] **3.7.P2** Convert quote vs spot — lag Greed
- [ ] **3.7.P3** Semáforo aliado spot por perp (Igris)

### 3.8 Kaiser — vocero interno *(COMPLETA v0 — 2026-07-05)*

*Criterio:* interpreta Tank → digest en `estado_vivo.kaiser`; alertas críticas en Bellion; **sin órdenes**.

- [x] **3.8.1** `core/kaiser_indicators.py` — reglas desvío, matriz, panorama, funding, clima
- [x] **3.8.2** `generales/kaiser.py` — hilo `vigilar_indicadores`, cooldown log
- [x] **3.8.3** Config umbrales `KAISER_*` en `config.py`
- [x] **3.8.4** `arise.py` — Kaiser en gather
- [x] **3.8.5** Bellion + panel publican digest Kaiser
- [x] **3.8.6** Perfiles multietiqueta 3d/1m/1a (`kaiser_perfil.py` + sampler)
- [x] **3.8.7** Metaverso — grafo aristas + rutas precargadas + ranking neto
- [x] **3.8.8** Backfill kline mark/index al arranque (plazo largo)
- [x] **3.8.9** `scripts/validar_kaiser_perfil.py`
- [x] **3.8.10** **Ancla** — `core/ancla.py` orderbook walk + max USD + regla neto≥fees
- [x] **3.8.11** Tank/Bridge guardan libro completo (snapshot/delta)
- [x] **3.8.12** Kaiser `OPORTUNIDAD_LIQUIDEZ` + `consultar_liquidez(intencion)` → Greed/Bellion
- [x] **3.8.13** Metaverso usa Ancla cuando hay libro (`scripts/validar_ancla_smoke.py`)
- [x] **3.8.14** Pipeline Kaiser→Greed — `kaiser_pipeline.py`, cola, abort, spread estable
- [x] **3.8.P1** Greed consume Kaiser + sizing 1% (`validar_greed_sizing_smoke.py`)
- [x] **3.8.P2** VIP / Mega VIP micro-órdenes (`validar_greed_vip_smoke.py`)
- [ ] **3.8.P3** Karmish (mundo externo) — pausa doctrinal

### 3.9 Beru — doctrina cirugía final *(2026-07-09 → 07-12 — COMPLETA en smokes)*

*Criterio:* clonación residual, fusión por colisión oz, engorde solo frontera, Mega reset, capital por fricción, flota Inverse∩Linear.  
*Doctrina:* [`22_DOCTRINA_BERU.md`](22_DOCTRINA_BERU.md).

- [x] **3.9.1** Clonación por `red_residual` (no spawn +0,3 % durante caza) — `beru_residual.py`
- [x] **3.9.2** Engorde exclusivo de frontera (red más extrema) + trailing caza fijo 0,1 %
- [x] **3.9.3** Fusión por colisión `oz_adan` (ε 0,01 %) — Mega Beru intacto
- [x] **3.9.4** Reset Mega Beru al tocar red — `beru_mega_reset.py`
- [x] **3.9.5** Capital por fricción directa (sin error compuesto 8×) — `beru_capital.py`
- [x] **3.9.6** Diccionario Flota del Manto Inverse∩Linear — `config/diccionario_beru_flota_manto.json`
- [x] **3.9.7** Engorde dual L/S estable + cooldown log `ENGORDE_BLOQUEADO`
- [x] **3.9.8** Smokes: cazador, fusión, multiberu, mega_reset, capital, ciclo ETH
- [x] **3.9.9** Ciclo Beru **live** testnet (`MODO_SIMULACION=False`) — ritual `scripts/beru_live_testnet.py` (Ansiedad 1.2%→gatillo 0.6%, Mariscal PLENO, CAZA ~\$20, flota 22 USDT, spot margen 10x); PASS México 2026-07-16 (`data/beru_live_testnet_report.json`); orden: `CURSOR_MEXICO_EJECUTAR_3_9_9.md`

### 3.10 Igris — jurisdicción, despliegue y panel *(2026-07-11 → 07-12)*

- [x] **3.10.1** Jurisdicción manto Igris→Greed — `core/manto_jurisdiccion.py`
- [x] **3.10.2** Despliegue §E Ask/Bid + umbral fees±urgencia — `core/igris_despliegue.py`
- [x] **3.10.3** Mordida = techo_misión × fracción(confianza); sin pinza 85% ni tope 1% equity
- [x] **3.10.4** Telemetría Igris → Árbol de Evolución — `core/telemetria_igris.py`
- [x] **3.10.5** Panel Pergamino — `dashboard_sombras.html` + `index.html` + scripts panel macOS
- [x] **3.10.6** Smoke Igris actualizado (`validar_igris_smoke.py`)
- [x] **3.10.7a** Arena aislada — `scripts/arena_igris_aislado.py` (Kaiser→Igris, fills virtuales, matriz forzada, Tusk limpio/activo, ~2 min)
- [x] **3.10.7b** Validar despliegue §E en **live** testnet con manto real — `PASS_LIVE` México 2026-07-12 (ETH/BTC dual DEMO; ritual `igris_live_testnet.py`)
- [x] **3.10.8** Modo `IGRIS_EVENT_DRIVEN` + alerta Kaiser `OPORTUNIDAD_MANTO` (morado Ask/Bid = Puerta §E) · arena micro / prod ≥ fees · lanzadores Win/Mac

### 3.11 Cuartel compartido (México) *(ops — 2026-07-09 → 07-12)*

- [x] **3.11.1** Remoto GitHub público `alanmgd181203/ShadowHarmy` + `.env` testnet
- [x] **3.11.2** Colaboradora `Jessica-Reyes06` (write) + sync desde `shadow-army`
- [x] **3.11.3** Checkpoint tag `checkpoint-mexico-2026-07-09` + `master` al día con feature

---

## FASE 4 — 🟡 M3: Operaciones Monarca (vivir con el bot)

*Criterio fase:* Telegram crítico funciona; puedes apagar todo en emergencia.

### 4.1 Notificaciones
- [~] **4.1.1** `core/telegram.py` — stub ✅; envío real pendiente
- [ ] **4.1.2** Tabla evento → nivel (`06_NOTIFICACIONES.md`)
- [ ] **4.1.3** Crítico: crash, API error, desconexión prolongada
- [ ] **4.1.4** Fill: sin sonido
- [ ] **4.1.5** Resumen salud 1×/día (cron o timer)

### 4.2 Safe mode (Iron absorbido)
- [~] **4.2.1** Flag `SAFE_MODE` en config + bloqueo CAZA Beru — stub ✅; cancel órdenes pendiente
- [ ] **4.2.2** Telegram crítico al entrar safe mode
- [ ] **4.2.3** Documentar en `08` como D-xx cerrada

### 4.3 Observabilidad
- [ ] **4.3.1** Rotación `historial_*.jsonl` (no crecer infinito)
- [ ] **4.3.2** Métricas mínimas: uptime, trades/día, margen max

### 4.4 Cierre M3
- [ ] **4.4.1** Matriz N-01…N-03 → ✅

---

## FASE 5 — 🟢 M4: Estrategia madura (manual + código)

*Criterio fase:* reglas avanzadas del Códice integradas o rechazadas explícitamente en `08`.

### 5.1 Beru / Igris — reglas opcionales del manual
- [ ] **5.1.1** Decisión A/B: ¿umbral 0.012/0.035 del Códice o solo acordeón? → `08`
- [ ] **5.1.2** Si aplica: Igris vol>0.04 / fuga>1.5% como capa extra
- [ ] **5.1.3** Gap Tusk 2.5× tras pérdida en `tusk.py`

### 5.2 Gestión posición
- [ ] **5.2.1** Escalera salida desbalance (REGLA-R03) — módulo o en Igris
- [ ] **5.2.2** Tests con posición simulada desbalanceada

### 5.3 Bellion — mariscal de verdad
- [ ] **5.3.1** Ratio_Eficiencia latidos/amputaciones por activo
- [ ] **5.3.2** Reporte horario (manual) — Telegram resumen
- [~] **5.3.3** Clasificar activos parásitos vs eficientes — Coliseo Beru Fantasma **v2** (caza+negociador+ciclo · barrido vacío 0.6–2.0%) · bóveda en `data/coliseo/` · informe [`INFORME_COLISEO_MONARCA.md`](INFORME_COLISEO_MONARCA.md) · barrido completo pendiente de corrida

### 5.4 Beru — legión completa
- [ ] **5.4.1** SUPER_FUSION estable bajo carga
- [ ] **5.4.2** Relevo generacional sin fugas de reserva
- [ ] **5.4.3** Capitanes: validar ADN en los 3 climas (Ansiedad/Cazador/Berserker)

### 5.5 Cierre M4
- [ ] **5.5.1** Matriz P2 ≥ 70% ✅
- [ ] **5.5.2** Promover acordeón/ADN a “reglas firmes” en `03_RIESGO` si aplica

---

## FASE 6 — 🟢 Robustez producción (mainnet acotado)

*Criterio fase:* mainnet con capital límite, 7 días supervisados.

- [ ] **6.1** `MODO_TESTNET=False` con tope de masa por Tusk (cap hard)
- [ ] **6.2** IP whitelist Bybit verificada
- [ ] **6.3** Rate limit / backoff en bridge
- [ ] **6.4** Reconciliación periódica exchange ↔ Tusk.pesos
- [ ] **6.5** Runbook incidentes en `migracion/` (qué hacer si ROJO, si margen 95%)
- [ ] **6.6** Backup `data/` automatizado

---

## FASE 7 — 🟢 Expansión mercado (más allá de LTC)

*Criterio fase:* segundo activo ancla o N frentes configurables sin reescribir Generales.

- [x] **7.1** Parametrizar `ticker_base` en config — ✅ `TICKER_BASE` + `ACTIVOS_PENTIVERSO`
- [x] **7.2** Plantilla Pentiverso por activo (5 mares × N) — ✅ LTC+BTC en código
- [ ] **7.3** Tusk: límites de exposición por activo
- [ ] **7.4** Bellion: métricas por activo
- [ ] **7.5** Decisión en `08`: orden de expansión (ETH, …)

---

## FASE 8 — 🔮 Inteligencia y entrenamiento

*Doctrina: nunca dejar de aprender (Campo de Marte, guerra infinita).*

- [ ] **8.1** Paquete `training/` separado del runtime live
- [ ] **8.2** Campo de Marte — simulador caos (ruido + masa artificial)
- [ ] **8.3** Modo `GUERRA_INFINITA` — Beru no distingue sim/real (flag entrenamiento)
- [ ] **8.4** Velo del Carnicero — Tusk inyecta pérdidas simuladas realistas
- [ ] **8.5** Informe de Guerra cada N ciclos (Bellion)
- [ ] **8.6** Simulador infierno / stress (manual) — solo offline

---

## FASE 9 — 🔮 Caza macro (Surge, liquidaciones, ballenas)

*Metáfora Solo Leveling → mecánicas de mercado.*

- [ ] **9.1** Feed liquidaciones Bybit (o proxy volatilidad extrema)
- [ ] **9.2** Tank detecta “rastro de sangre” → densidad Beru
- [ ] **9.3** Surge: reglas de entrada post-liquidación (doctrina → spec en `03`)
- [ ] **9.4** Modo plancton vs ballena — escala de masa dinámica
- [ ] **9.5** Inquisidor / arbitraje visual (solo si sigue en `15` como prioridad)

---

## FASE 10 — 🔮 Utopía: Ejército definitivo

*Visión del manual — no bloquea v1; es el horizonte.*

### 10.1 Autonomía total
- [ ] **10.1.1** Eco del Trono — operación 30 días sin intervención Monarca
- [ ] **10.1.2** Coro de Sombras — bus de eventos entre Generales (más allá de jsonl)
- [ ] **10.1.3** Memoria de la Familia — aprendizaje colectivo post-trade

### 10.2 Fusión y escalas extremas
- [ ] **10.2.1** Fusión dual entre dos Generales bajo reglas formales
- [ ] **10.2.2** Protocolo Ragnarok — fusión total en crisis
- [ ] **10.2.3** 120 frentes / multidivisa masiva
- [ ] **10.2.4** Fusión con otro Monarca/Gobernador (multi-bot) — si sigue en visión

### 10.3 Producto acabado
- [~] **10.3.1** UI web / panel Pergamino — Cascada 6 portales ✅ · PWA/install ✅ · Manto Igris + AssetDetail · Ascensión Aspirante (estrella 5 · techo ~$86 post-Jess) · **cosas apagadas** `ui/featuresApagadas.js` · sync Bybit México ✅ · bóveda Coliseo: [`JESS_BOVEDA_COLISEO.md`](JESS_BOVEDA_COLISEO.md) · unificar Streamlit pendiente
- [ ] **10.3.2** Mapa neuronal del Códice en vivo (opcional Monarca UI)
- [ ] **10.3.3** Documentación pública del protocolo Shadow Army
- [ ] **10.3.4** El Monarca puede retirarse; el ejército caza solo 🌑

---

## Resumen por horizonte

| Horizonte | Fases | Meta en una frase |
|-----------|-------|-------------------|
| **Ahora** | 3 cierre + 4 | 3.5.8c motor (doctrina ✅) · ranking fusión · Telegram 4.1 · commit Pergamino |
| **Semanas** | 2–3 | ✅ Testnet + pentiverso + Beru doctrina + Igris despliegue |
| **Meses** | 4–6 | **Ops** + **mainnet** + estrategia madura |
| **Trimestres** | 7–9 | Más activos, Surge, entrenamiento |
| **Utopía** | 10 | Autonomía, fusión, escala masiva |

---

## Progreso global

```
Fase 0:   5 /  5   ✅ 100%
Fase 1:  19 / 19   ✅ 100%
Fase 2:  20 / 20   ✅ 100%
Fase 3:  72 / 78   ~92%  (3.5.8c doctrina✅/motor~; 3.7.P1–P3; 3.8.P3; plan 23 ~)
Fase 4:   0 / 11   ~9%   ← ops Monarca (2 stubs Telegram/Safe)
Fase 5:   0 / 13     0%
Fase 6:   0 /  6     0%
Fase 7:   2 /  5    40%
Fase 8:   0 /  6     0%
Fase 9:   0 /  5     0%
Fase 10:  0 / 11  ~10%   (Cascada ✅ · Manto/AssetDetail React forja local)
─────────────────────────────
TOTAL:  118 / 179  ítems [x]  →  ~66% checklist completo
        + 3 parciales [~]     →  ~67% (parciales al 50%)
Núcleo operativo (Fases 0–3): 116 / 122  →  ~95%
```

**Última actualización checklist:** 2026-07-17 (checkpoint 3.5.8c doctrina ventana 48–52 · Sub-Santuario Bridge · lives ✅)  
**Próximo ítem recomendado:** motor 3.5.8c **o** ranking fusión · **4.1.2** Telegram · commit Pergamino · **3.7.P***  
 
**Smokes Beru:** `validar_ciclo_beru_eth.py` · cazador/fusión/multiberu/mega_reset/capital · `beru_live_testnet.py`  
**Smokes Igris:** `validar_igris_smoke.py` · `validar_igris_asset_detail_smoke.py`  
**Runbook testnet:** `18_ARRANQUE_TESTNET.md`  
**Validar estado:** `python scripts/validar_checklist.py`  
**Validar sentidos Tank:** `python scripts/validar_panorama_tank.py --segundos 35`

---

## Para el agente nuevo (copy-paste)

```
Proyecto: ShadowHarmy — Lilit de Hierro v2.0
Codex: ./migracion/ (primero 17_GUIA_MONARCA.md — tono Ejército)
Checklist: 16_CHECKLIST_MAESTRO.md · código manda en hechos; actualizar migracion cada sesión.
Fases 0–2 ✅ · Fase 3 ~92% (Beru 3.9.9 live ✅ · Igris §E v2 + 3.10.7b live ✅).
Siguiente: 3.5.8c motor (doctrina checkpoint ✅) · ranking fusión · 4.1.2 Telegram · commit Pergamino.
Validar: scripts/validar_*_smoke.py + validar_ciclo_beru_eth.py + validar_igris_smoke.py + validar_igris_asset_detail_smoke.py
Si propongo algo contra 08/03 sin "Override codex" → avisar al Monarca.
Hablar siempre en términos del Ejército (Beru, Greed, Tusk, manto, legión).
```
