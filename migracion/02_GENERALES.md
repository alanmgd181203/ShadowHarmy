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

**Rol:** Ejecución ofensiva; legión de `BeruShip`; acordeón asimétrico; cosecha y relevo.

**Reglas Códice firmes:**
- Umbral venta **0.012**; si volatilidad **> 0.035** → venta automática.
- Posiciones cortadas **sin reparación** (Iron deshabilitado como cirujano).

**Debe hacer:**
- Plantar semillas / gatillos / acordeón según precio y capitanes.
- Emitir `IntencionAccion` CAZA / COSECHA hacia Greed.
- Modo "guerra infinita" — no distinguir simulación de real (doctrina).

**Estado código (Fase B):** `beru.py` — **no compila** (IndentationError L98); falta `limpiar_legion`. Lógica diseñada: vacío Adán, acordeón 1.1/0.9, SUPER_FUSION.

---

## Igris — Escudo / Senescal del Manto

**Rol:** Margen, espejos, poda quirúrgica, limpieza de posiciones reflejo.

**Reglas Códice:**
- Si vol **> 0.04** y fuga por spread **> 1.5%** del valor → cierre inmediato.

**Config prototipo:**
- `RANGO_EXPANSION_MIN` 80%, `RANGO_LIMPIEZA_MAX` 90%, `MURO_LEY_MARCIAL` 95%.

**Manual adicional:**
- Administra la "semilla" del manto (no solo táctico).
- Liberación atómica / red densa en versiones Iron+Igris históricas.

**Prototipo:** `ShadowHarmy/generales/igris.py` — lógica margen parcial.

---

## Greed — Francotirador / Altar

**Rol:** **Único ejecutor material** de intenciones (juez + parte); cola prioridad; anti-duplicado.

**Debe hacer:**
- `arbitrar` loop; respetar TTL (`TTL_ORDEN_MS` ~2000 ms).
- Escuadrón suicida: desviación USDT/USDC ≥ `UMBRAL_REGALO_SQUAD`.
- Cosecha multiverso, poda manto, limpieza espejos.
- **En producción:** llamar API orden + confirmar fill (hoy `DISPARO_SIMULADO`).

**Doctrina:** Comandante exploración / mutación en tiempos de paz.

**Prototipo:** `ShadowHarmy/generales/greed.py` — altar sólido; ejecución simulada.

---

## Bellion — Mariscal / Auditor

**Rol:** Intermediario entre Generales y Monarca; analiza latidos/amputaciones; Telegram/reportes.

**Debe hacer:**
- `anotar(general, evento, mensaje)` — log estructurado.
- Clasificar activos (éficientes vs parásitos); reportes horarios (manual).
- "Informe de Guerra" cada N batallas (pendiente).

**Prototipo:** `ShadowHarmy/core/bellion.py` — logging básico.

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
| Beru | `generales/beru.py` |
| Igris | `generales/igris.py` |
| Greed | `generales/greed.py` |
| Bellion | `core/bellion.py` |
| Capitanes | `generales/capitanes.py` |
| Bridge | `core/bridge.py` |
| Config | `core/config.py` |
| Models | `core/models.py` |
| Orquestador | `arise.py` |
