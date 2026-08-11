# Informe al Monarca — el mapa del margen real (2026-08-11)

**Para ti:** lectura de campo, sin jerga de ingeniería.  
**Para el agente/Cursor:** el espejo técnico está en `CONTEXTO_AGENTE_PASE_IM_PIERNAS_2026-08-11.md`.

---

## Qué pasó en el campo

Con ~\$1 500 de capital, el ranking decía que podías aspirar a la corona **Brujo** (cerca de 27–28 pasos). En la batalla real el ejército se quedó sin **oxígeno** (margen ~97 %) mucho antes. No era que Bybit “no respetara Asalto”: el **pergamino mentía** sobre cuánto tesoro come el manto.

---

## Por qué mentía el mapa

Imagina dos piernas del mismo Santo: una **inversa** y una **lineal**. Bybit cobra margen de **cada una** con su propio apalancamiento máximo (ej. LINK 20× en inversa y 50× en lineal).

El cálculo viejo hacía un **promedio** (como si fueran 35×) y por eso el peaje salía barato. En la guerra real, 20× + 50× come **más** que el promedio. Ese “ahorro fantasma” se acumuló en LINK, AVAX, OP, MNT manto, etc., hasta ahogar la cuenta.

**Analogía:** el Coliseo te cobraba la media de dos peajes de camino; el puente de Bybit te cobra **ambos peajes enteros**.

---

## Qué ordenaste y qué cumplimos

1. **No tocar la bóveda en el presupuesto ofensivo.** El short MNT de colateral ya vive dentro del **colchón del 5 %** (el aire hasta el muro 95 %). No lo sumamos otra vez al costo del Asalto.

2. **Matar el promedio.** El peaje del ranking ahora se calcula **pierna a pierna** con el apalancamiento máximo real de cada contrato.

3. **No hinchar tamaños al leer el exchange.** En contratos inversos, un número de Bybit (`positionValue`) son **monedas**, no dólares. Confundirlo hizo parecer glotones a OP/ADA. Quedó clavado: el tamaño en dólares del inverso es el **size** (cara en USD).

4. **Sellos OP / ADA** (28, 34, 35) por tu orden, con candado para que el sync no los borre solos.

5. **Bisturí de recorte** (script de nivelar): forjado y medido en dry-run; **abortado** — no se vendió nada. Arise **no** se reinició.

---

## Cómo cambió la proyección (solo manto ofensivo)

| Idea | Antes (promedio) | Ahora (mapa real) |
|------|-----------------:|------------------:|
| Corona Brujo (paso 27 del pase) | ~\$1 451 | **~\$1 673** |
| Margen que exigen los mantos ideales 1–27 | subestimado | **~\$1 585** |
| Qué alcanza \$1 500 en potencia | casi 28 pasos | **~24 pasos** |

Traducción: con \$1 500 **ya no finge** que te alcanza la corona Brujo completa. El mapa y el puente hablan el mismo idioma.

---

## Archivos que importan (nombres para citar)

**Para el Monarca (este informe):**  
`migracion/INFORME_MONARCA_MAPA_MARGEN_REAL_2026-08-11.md`

**Para Cursor / agente (contexto técnico):**  
`migracion/CONTEXTO_AGENTE_PASE_IM_PIERNAS_2026-08-11.md`

**Código del peaje y del pase:**  
- `core/beru_capital.py` — corazón del peaje pierna a pierna  
- `core/pase_director.py` — pasos, acum, sellos forzados  
- `core/plan_crecimiento.py` — techos Aspirante→Chamán  
- `core/lote_bybit.py` — unidades USD vs coins en inverso  
- `core/telemetria_igris.py` — ojos del margen sin inflar  
- `generales/igris.py` — Igris deja de usar el promedio  
- `data/pase_progreso.json` — libro de sellos (28, 34, 35 forzados)

**Herramientas / pruebas:**  
- `scripts/nivelar_manto_pase.py` — bisturí (solo dry-run; no usado en vivo)  
- `scripts/validar_beru_capital_smoke.py`  
- `scripts/validar_lote_bybit_smoke.py`  
- `scripts/validar_pase_director_smoke.py`  
- `scripts/validar_plan_crecimiento_smoke.py`

---

## Qué sigue (sin obligación)

Cuando quieras volver a la mainnet: orden directa de encender manos. Hasta entonces el ritual sigue apagado; el manto en Bybit sigue abierto por su cuenta. Si regeneras los pergaminos viejos (`PASE_BATALLA_13_SANTOS.md`, etc.), aún pueden mostrar \$1451/\$3161 — el **código vivo** ya usa \$1673/\$3735.
