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

- [ ] **0.1** Copia `migracion/` vive en `ShadowHarmy/migracion/` (junto al código)
- [ ] **0.2** Leer `00_NORTE.md` + `13_ANALISIS_SHADOWHARMY.md` (estado actual)
- [ ] **0.3** `.env` con `BYBIT_API_KEY`, `BYBIT_API_SECRET`, `MODO_TESTNET=True`
- [ ] **0.4** Regla Cursor / prompt fijo: citar `migracion/` + protocolo `CODEX_VIVO.md`
- [ ] **0.5** Decisión registrada en `08`: solo ShadowHarmy para runtime (D-10)

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

## FASE 2 — 🟠 M1: Primer sangre real (testnet)

*Criterio fase:* 1 ciclo CAZA → fill confirmado → COSECHA en testnet, log en Bellion.

### 2.1 Bridge — manos (no solo ojos)
- [x] **2.1.1** `place_order(market/limit)` wrapper con idempotencia (`orderLinkId`)
- [x] **2.1.2** `cancel_order` / `amend_order` básico
- [x] **2.1.3** Poll o WS privado para **fill confirmado** (REGLA-R07)
- [x] **2.1.4** Reemplazar `except: pass` en NAV por log Bellion + reintento
- [x] **2.1.5** Documentar mainnet-ojos + testnet-manos en `04_INFRA_API.md`

### 2.2 Modo simulación vs real
- [ ] **2.2.1** Flag `MODO_SIMULACION` en config (default True hasta validar)
- [ ] **2.2.2** Si `MODO_SIMULACION=False` → prohibir `DISPARO_SIMULADO`
- [ ] **2.2.3** `confirmar_reserva` solo tras fill real cuando modo live

### 2.3 Cableado Greed → Bridge
- [ ] **2.3.1** `_ejecutar_caza_multiverse` → orden real + fill → luego `confirmar_reserva`
- [ ] **2.3.2** `_ejecutar_cosecha_multiverse` → cierre real + fill
- [ ] **2.3.3** Poda / espejos → órdenes de reducción reales (o sim hasta validar lógica)

### 2.4 Tusk — coherencia NAV
- [ ] **2.4.1** Tras fill, reconciliar `pesos` con posiciones exchange
- [ ] **2.4.2** No liberar reserva si orden rechazada

### 2.5 Validación M1
- [ ] **2.5.1** 1 trade redondo testnet documentado (timestamp, ids, PnL)
- [ ] **2.5.2** Matriz: T-01, T-03 → ✅
- [ ] **2.5.3** 24 h testnet sin crash (stretch goal dentro de M1)

---

## FASE 3 — 🟡 M2: Pentiverso de verdad (5 mares LTC)

*Criterio fase:* los 5 `MarketContext` con precio real; arbitraje USDT/USDC con datos reales.

### 3.1 Tank — visión completa
- [ ] **3.1.1** WS/REST para `LTCUSDC_LINEAL`
- [ ] **3.1.2** WS/REST para `LTCUSDT_SPOT`
- [ ] **3.1.3** WS/REST para `LTCUSD_INVERSE` (o inverse según Bybit)
- [ ] **3.1.4** WS/REST para `LTCUSDC_SPOT`
- [ ] **3.1.5** Poblar `TankNode.muros` (depth) para `_escanear_mejor_precio`

### 3.2 Greed — multiverso operativo
- [ ] **3.2.1** Escuadrón suicida con USDC/USDT **reales**
- [ ] **3.2.2** Caza/cosecha eligen frente ganador con liquidez real

### 3.3 Persistencia — muerte digna
- [ ] **3.3.1** `signal` handler → `bellion.ley_de_sucesion` + flush Tusk
- [ ] **3.3.2** Recovery al arranque desde `estado_hierro.json`

### 3.4 Cierre M2
- [ ] **3.4.1** Matriz: G-Tank, S-03 → ✅
- [ ] **3.4.2** Dashboard muestra 5 frentes con precio ≠ 0

---

## FASE 4 — 🟡 M3: Operaciones Monarca (vivir con el bot)

*Criterio fase:* Telegram crítico funciona; puedes apagar todo en emergencia.

### 4.1 Notificaciones
- [ ] **4.1.1** `core/telegram.py` — `enviar_telegram(msg, critico=)`
- [ ] **4.1.2** Tabla evento → nivel (`06_NOTIFICACIONES.md`)
- [ ] **4.1.3** Crítico: crash, API error, desconexión prolongada
- [ ] **4.1.4** Fill: sin sonido
- [ ] **4.1.5** Resumen salud 1×/día (cron o timer)

### 4.2 Safe mode (Iron absorbido)
- [ ] **4.2.1** Comando/flag `SAFE_MODE` — cancela órdenes, bloquea nuevas CAZA
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
- [ ] **5.3.3** Clasificar activos parásitos vs eficientes

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

- [ ] **7.1** Parametrizar `ticker_base` en config (no solo LTC)
- [ ] **7.2** Plantilla Pentiverso por activo (5 mares × N)
- [ ] **7.3** Tusk: límites de exposición por activo
- [ ] **7.4** Bellion: métricas por activo
- [ ] **7.5** Decisión en `08`: orden de expansión (BTC, ETH, …)

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
- [ ] **10.3.1** UI web o panel más allá de consola (`arquitectura_render` manual)
- [ ] **10.3.2** Mapa neuronal del Códice en vivo (opcional Monarca UI)
- [ ] **10.3.3** Documentación pública del protocolo Shadow Army
- [ ] **10.3.4** El Monarca puede retirarse; el ejército caza solo 🌑

---

## Resumen por horizonte

| Horizonte | Fases | Meta en una frase |
|-----------|-------|-------------------|
| **Ahora** | 0–1 | Que el código **arranque** |
| **Semanas** | 2–3 | **Testnet** + **5 mares** reales |
| **Meses** | 4–6 | **Ops** + **mainnet** + estrategia madura |
| **Trimestres** | 7–9 | Más activos, Surge, entrenamiento |
| **Utopía** | 10 | Autonomía, fusión, escala masiva |

---

## Progreso global (rellenar a mano)

```
Fase 0:  _ / 5
Fase 1: 18 / 18  ✅ COMPLETA
Fase 2:  _ / 14
Fase 3:  _ / 11
Fase 4:  _ / 12
Fase 5:  _ / 12
Fase 6:  _ / 6
Fase 7:  _ / 5
Fase 8:  _ / 6
Fase 9:  _ / 5
Fase 10: _ / 11
```

**Última actualización checklist:** 2026-07-03  
**Próximo ítem recomendado:** **2.1.1** (Bridge: `place_order` wrapper con idempotencia)

---

## Para el agente nuevo (copy-paste)

```
Proyecto: ShadowHarmy — Lilit de Hierro v2.0
Codex: ./migracion/ (CODEX_VIVO.md + este 16_CHECKLIST_MAESTRO.md)
Regla: código manda en hechos; codex manda en meta; actualizar migracion cada sesión.
Empezar por Fase 1 ítem 1.1.1. No saltar fases sin cerrar criterio de la anterior.
Si propongo algo contra 08/03 sin "Override codex" → avisar al Monarca.
```
