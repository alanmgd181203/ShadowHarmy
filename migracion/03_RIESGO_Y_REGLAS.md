# 03 — Riesgo y reglas firmes

Reglas extraídas del **Códice** (`01–04`) y consolidadas del sandbox donde no hay contradicción explícita. En conflicto Códice↔Sandbox: **conviven** (P0.3) — filas marcadas ⚠️.

---

## REGLA-R01 — Supervivencia sobre reparación

**Fuente:** Códice `03_gestion_intercambios.md` (v2.3.0ti)

- Beru corta con umbral **0.012**.
- Si volatilidad **> 0.035** → venta automática.
- **Iron no repara** posiciones cortadas — eliminación sin recuperación.
- Tusk aplica **Gap 2.5×** en entrada siguiente tras pérdida.

**Estado código prototipo:** parcial (umbrales en config/beru no verificados 1:1).

---

## REGLA-R02 — Igris anti-fuga por volatilidad

**Fuente:** Códice `02_perfiles_bots.md`

- Si `vol > 0.04` y potencial fuga por spread **> 1.5%** de posición → **cierre inmediato**.
- Coste de reparación descontado del PnL del barco.

**Prototipo:** rangos 80/90/95% en `config.py` — alinear semántica.

---

## REGLA-R03 — Escalera de salida por desbalance

**Fuente:** Códice `01_capas_reglas.md` (#Gestion_Riesgo)

- Detectar desbalance (ej. +10% Long).
- Consultar volumen extra + precio promedio.
- Salida gradual por escalones % fijos (ej. 1% por escalón) vía **Limit** en Bybit.

---

## REGLA-R04 — Margen operativo ~85%

**Fuente:** Sandbox Shadow Army (protocolo tres personalidades)

- Gestión de margen al **85%** como techo operativo habitual (no 100%).

**Prototipo Igris:** muro 95% — ⚠️ reconciliar.

---

## REGLA-R05 — Greed TTL y semáforo

- Intenciones expiran (`TTL_ORDEN_MS`, default 2000 ms).
- No ejecutar CAZA si Tank en `ROJO` o `GLITCH_DETECTADO` (salvo tipos de alivio: COSECHA, PODAR, ESPEJOS).

**Prototipo:** implementado en `greed.arbitrar`.

---

## REGLA-R06 — Oxígeno antes de disparar

- Tusk `solicitar_reserva` rechaza si `masa_autorizada < masa` solicitada.
- Escuadrón suicida usa ~50% de masa autorizada máx.

---

## REGLA-R07 — Prohibición disparo sin fill (ingesta)

**Fuente:** tests/pre_digestor, múltiples chats en `1M.txt`

- **Prohibido disparar sin fill confirmado en Bybit.**

**Prototipo:** violado por diseño (`DISPARO_SIMULADO`) — **P0 Fase B**.

---

## REGLA-R08 — Credenciales y API

- Claves en `.env`; nunca en Códice ni logs.
- Errores API/red = alerta **crítica** Telegram.

---

## REGLA-R09 — Guerra infinita / Velo del Carnicero

**Fuente:** Sandbox `#Gestion_Riesgo` (doctrina operativa)

- Beru no debe saber si la batalla es simulada o real.
- Tusk inyecta caos controlado en entrenamiento.
- Sin culpables en la familia — aprendizaje colectivo.

**Implementación:** parcial (simulación sí; caos Mars field no en ShadowHarmy).

---

## REGLA-R10 — Simulación forense (Maestro del Dolor)

**Fuente:** Códice `01_capas_reglas.md`

- Simulador agresivo para stress (spread, decoupling).
- Solo entornos de prueba; interpretación humana requerida.

---

## REGLA-R11 — Auditoría Tusk por activo

- Registrar latidos (ganancias) y amputaciones (pérdidas).
- `Ratio_Eficiencia = latidos / amputaciones` — activo "traidor" si Arca Iron se agota antes min 2410.

---

## REGLA-R12 — Dedupe de intenciones

- `dedupe_key` = `{tipo}_{uid_barco}` — evitar fuego amigo en Greed.

---

## Umbrales numéricos (tabla config)

| Parámetro | Valor prototipo | Origen |
|-----------|-----------------|--------|
| `UMBRAL_COSECHA_MIN` | 0.01 | config.py |
| `UMBRAL_REGALO_SQUAD` | 0.003 | config.py |
| `TTL_ORDEN_MS` | 2000 | config.py |
| Beru venta | 0.012 | Códice |
| Beru vol auto | 0.035 | Códice |
| Igris vol | 0.04 | Códice |
| Igris fuga | 1.5% | Códice |
| Tank verde | <400 ms | config.py |
| Tank amarillo | <800 ms | config.py |

---

## Riesgos conocidos del manual (no reglas — alertas)

1. Solapamiento gestión riesgo Códice ↔ sandbox — revisión humana pendiente.
2. Estrategia trading cargada en Códice mezclada con exploración.
3. Múltiples versiones cristalizadas (v1.1.9ti … v2.4.0ti) — **una sola** debe ganar en Fase B.
