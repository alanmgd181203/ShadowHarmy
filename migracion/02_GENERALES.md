# 02 — Generales (roles y responsabilidades)

Cada General = **un módulo Python** con un hilo async y contratos claros hacia Greed/Tusk. Nombres **intransferibles** (Códice).

---

## Tusk — Tesorero de Hierro

**Rol:** Capital, NAV, reservas de masa, persistencia, escalones de potencia.

**Debe hacer:**
- Sincronizar balance/margen real desde Bybit → `masa_bruta`, `margen_ocupado`, `masa_autorizada`.
- `solicitar_reserva` / `liberar_reserva` para cada sombra activa.
- Persistir legión en `data/tusk_data.json` (escritura atómica .tmp).
- Calcular `referencia_escalon` con `ESCALON_POTENCIA_BASE` y `FACTOR_MASA_AUTORIZADA`.

**Manual adicional:**
- Gap **2.5×** al precio de entrada del siguiente ciclo tras pérdida (Códice v2.3.0ti).
- Auditoría latidos/amputaciones → `Ratio_Eficiencia` por activo.
- "Velo del Carnicero" — caos simulado indistinguible de real (guerra infinita).

**Prototipo ShadowHarmy (Fase B):** `C:\Users\alans\Desktop\ShadowHarmy` — ver `13_ANALISIS_SHADOWHARMY.md`

---

## Tank — La Hidra / Percepción

**Rol:** Sensor de mercado; alivia presión de precisión de Beru.

**Debe hacer:**
- Mantener nodos por frente del Pentiverso; medir latencia (`UMBRAL_VERDE_MS`, `UMBRAL_AMARILLO_MS`).
- Emitir `vision_especulativa()` → `ctx_map` + semáforo (`VERDE_SEGURO`, `GLITCH_DETECTADO`, `ROJO`).
- Alimentar bridge con precios; detectar clima para **Capitanes**.

**Manual adicional:**
- "Trampa de las Sombras": Tank detecta patrón → Capitanes filtran → máx. 2 opciones a Beru.
- Emboscada vs esperar gatillo (Kaisel / Igris vanguardia).

**Prototipo:** `ShadowHarmy/generales/tank.py` — parcial (LTC focus).

---

## Kaiser — Vocero interno / Guardián de indicadores

**Rol:** Capa entre Tank y el resto del ejército. **No abre ojos** (eso es Tank); **interpreta** snapshots ya calculados y emite alertas tipadas + cola de prioridad.

**Debe hacer:**
- Leer snapshots Tank; producir alertas + **perfiles multietiqueta** (corto 3d, mediano 1m, largo 1a).
- Muestrear desvíos vs precio global (índice); backfill kline para plazo largo.
- **Metaverso:** aristas precargadas por activo; rankear rutas (regalo neto − slippage estimado).
- Registrar alertas críticas en Bellion (cooldown). **No ejecutar órdenes.**

**Manual:** “Oído de Kaiser” — filtro interno (vs Karmish = mundo externo, pausa).

**Doctrina acordada:** [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md) — §0 Ancla, §1–§2 cerrados; manos pendientes §3+.

**Estado código:** `generales/kaiser.py` + `core/ancla.py` — Ancla + perfiles + metaverso; **Greed cableado** (incl. multicruce); Beru fuera por doctrina.

---

## Capitanes — Ganglios tácticos

**Rol:** Capa entre Tank y Beru; **binario o dos opciones**, no saturar al General.

**Perfiles destilados:**
| Capitán | Función |
|---------|---------|
| Ansiedad / Inercia (Kaisel) | Fatiga del movimiento → `EMBOSCADA_AHORA` |
| Cazador | Confirmación agresiva |
| Berserker | Guerra masiva / alta vol |
| Trampa (Igris vanguardia) | Soporte/resistencia → `ESPERAR_GATILLO` |

**ADN:** `ADN_Capitan` en `BeruShip.adn_capitan`.

**Estado código:** ADN wired vía `tank.capitan_activo` → `BeruShip.adn_capitan` (mejor que manual "2 opciones").

---

## Beru — Cazador / Espada del Manto

**Rol:** Spot margen (casa); legión `BeruShip`; acordeón; cosecha.

**Capitanes (solo 2):** Ansiedad **1,2 %** vacío | Normal **1,6 %**.

**ProtoBeru:** tiers PLENO / PROTO1 / PROTO2 — pasos oz/red y manto escalado; arranque **ETH + PROTO1 + Negociador** (~**$50** manto).

**Rail casa:** elige USDT/USDC/USDE/USD1 vía `beru_rail.py` + Ancla. **No** multicruce (Greed).

Ver [`22_DOCTRINA_BERU.md`](22_DOCTRINA_BERU.md).

**Código:** `generales/beru.py`, `core/beru_capital.py`, `core/beru_tier.py`, `scripts/validar_beru_capital_smoke.py`

---

## Igris — Escudo / Senescal del Manto

**Rol:** Margen, espejos, poda quirúrgica, rebalanceo L/S, engorde del manto.

**Ejecución:** **directo en Bridge** (órdenes manto); **no** pasa por el altar Greed. Greed = arbitraje; Beru = casa spot.

**Ciclo (1 s):** poda ≥95% → limpieza espejos >90% → bootstrap → rebalanceo delta → engorde <80%.

**Config (21 §A):**
- `RANGO_EXPANSION_MIN` 80%, `RANGO_PISO_IDEAL` 85%, `RANGO_OBJETIVO_MARGEN` 90%
- `RANGO_LIMPIEZA_MAX` 93% (espejos), `MURO_LEY_MARCIAL` 95% (poda)
- `FRENTES_MANTO_ALL` — pentiverso LTC+BTC (lineal + inverse).

**Greed y el manto:** Greed no administra el manto; si arbitra en un frente del manto, puede mover L/S brevemente — Igris rebalancea después.

**Doctrina viva:** [`21_DOCTRINA_IGRIS.md`](21_DOCTRINA_IGRIS.md) — bloques A/C pendientes Monarca.

**Reglas Códice (Fase 5 — no cableadas aún):**
- Si vol **> 0.04** y fuga por spread **> 1.5%** del valor → cierre inmediato.

**Código:** `generales/igris.py`, `core/igris_estado.py` (métricas panel).

**Smoke:** `python scripts/validar_igris_smoke.py`

---

## Greed — Francotirador / Altar

**Rol:** **Único ejecutor material** de intenciones (juez + parte); cola prioridad; anti-duplicado.

**Debe hacer:**
- Loop Kaiser+Ancla+VIP; **multicruce spot** 3–4 piernas (USDC/MNT/EUR vía `greed_multicruce.py`).
- Escuadrón suicida USDT×USDC (legacy, apagado por defecto).
- **No** ejecuta poda/rebalanceo/engorde del manto — eso es **Igris** (`igris.py` → Bridge).
- Si arbitra en frente del manto, marca `toques_greed_manto` (cooldown rebalanceo Igris).

**Doctrina:** Comandante exploración / mutación en tiempos de paz.

**Prototipo:** `ShadowHarmy/generales/greed.py` — altar sólido; ejecución simulada.

---

## Bellion — Mariscal / Auditor

**Rol:** Intermediario entre Generales y Monarca; analiza latidos/amputaciones; Telegram/reportes.

**Debe hacer:**
- `anotar(general, evento, mensaje)` — log estructurado.
- Clasificar activos (éficientes vs parásitos); reportes horarios (manual).
- "Informe de Guerra" cada N batallas (pendiente).
- Oído Pergamino: `core/bellion_oido.py` → `estado_vivo.bellion_oido`.

**Prototipo:** `ShadowHarmy/core/bellion.py` — logging + oído + estado_vivo.

---

## Tusk — Tesorería UTA (2026-08-01)

**Visión real de la bóveda:** `core/tusk_tesoreria.py` + NAV Bridge.

| Campo | Significado |
|-------|-------------|
| `equity_usd` | totalEquity UTA |
| `disponible_usd` | totalAvailableBalance (Bybit ya restó IM del hedge) |
| `mnt_usd` / coins | Desglose spot (MNT para fees, stables…) |
| `hedge_shorts` | Shorts MNT (notional, IM, lev, liq) |
| `oxigeno_guerra_usd` | `min(disponible, equity×(1−reserva))` — IM hedge **dentro** del colchón |
| `estado` | sana / justa / ahogada |

Config: `TUSK_TESORERIA_ACTIVA` · `TUSK_RESERVA_MONARCA_EXTRA_PCT` · `MONARCA_RESERVA_PCT`.  
Smoke: `python scripts/validar_tusk_tesoreria_smoke.py`

**Ritual de ojos (sin disparos):** `python scripts/arise_ojos_tusk.py`  
Despierta Tusk (bóveda/oxígeno) + Tank (mares) + Kaiser (indicadores). Igris/Greed/Beru hibernados.  
Corte opcional: `--segundos 120`. Ver también `18_ARRANQUE_TESTNET.md` § ritual ojos.

---

## Iron — Guardián del Arca (histórico)

**Rol en manual:** Acumulación USDT, gaps (~2%), safe mode, impuestos internos.

**Estado código (D-11):** Sin `iron.py`. Tusk gestiona NAV/reservas; Greed usa metáfora "Hierro" en DISPARO_SIMULADO. Safe mode → backlog M3.

---

## LegionSombras / MareaSombras (diseños aspiracionales)

Clases mencionadas en sandbox no implementadas como tales:

- `LegionSombras` — fusión dual, Ragnarok, Coro de Sombras, Eco del Trono.
- `MareaSombras` — latido por tick, 23 puertos, densidad de agentes.

Marcar como **DISENO futuro** salvo promoción explícita.

---

## Matriz rápida General → archivo objetivo

| General | Archivo canónico esperado |
|---------|-------------------------|
| Tusk | `generales/tusk.py` |
| Tank | `generales/tank.py` |
| Kaiser | `generales/kaiser.py` |
| Beru | `generales/beru.py` |
| Igris | `generales/igris.py` |
| Greed | `generales/greed.py` |
| Bellion | `core/bellion.py` |
| Capitanes | `generales/capitanes.py` |
| Bridge | `core/bridge.py` |
| Config | `core/config.py` |
| Models | `core/models.py` |
| Orquestador | `arise.py` |
