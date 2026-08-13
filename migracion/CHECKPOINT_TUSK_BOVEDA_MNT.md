# CHECKPOINT — Tusk / Iron: caja USDT (visión original)

> **2026-08-12 — mega-cirugía:** el ritual “MNT + short + descuento fees” quedó **extirpado**.  
> Caja = **USDT**. MNT = Santo de Igris, no saco. Ver [`CHECKPOINT_MEGA_CIRUGIA_EJERCITO_2026-08-12.md`](CHECKPOINT_MEGA_CIRUGIA_EJERCITO_2026-08-12.md).  
> Lo de abajo que hable de comprar MNT / short de equilibrio = **legado**, no ley vigente.

**Estado:** caja USDT · **manos OFF** · código: lectura / cálculo  
**Código frío:** `core/tusk_boveda_mnt.py` + `tusk_tesoreria.boveda_mnt`  
**Smoke:** `python scripts/validar_tusk_boveda_mnt_smoke.py`  
**Dudas:** [`DUDAS_CIRUGIAS_MENORES_2026-08-12.md`](DUDAS_CIRUGIAS_MENORES_2026-08-12.md)

---

## Qué está fundido vs qué no

| Pieza | Estado |
|-------|--------|
| Doctrina escenario ideal + Convert vs spot | ✅ pergamino + `plan_ritual_ideal()` |
| **Ley: estado sucio → reset → ritual ideal** | ✅ **firmada Monarca 2026-08-02** (pergamino; manos aún OFF) |
| Capital de mando del short MNT | ⚠️ **legado** — solo diagnóstico de sucio |
| Equilibrio spot/short + sesgo spot | ⚠️ lectura legado (no reconstruir) |
| Foto viva spot vs inverso | ⚠️ lectura legado |
| Potencia del **pase** desde **caja USDT** | ✅ cálculo frío (no mueve Igris) |
| Oxígeno UTA / equity vivo | ✅ tesorería previa (sigue existiendo) |
| Ritual manos (Funding→UTA, Convert/spot, shorts, **reset**) | ❌ **no** — `TUSK_BOVEDA_MANOS=false` |
| capital_mando → `masa_autorizada` de Igris | ❌ pendiente (gate Monarca) |
| Catálogo fino de rarezas / ahorrar último céntimo sin cerrar | ❌ **aplazado** (ejército más pensante) |
| Fundir Tusk al 100% con todas las herramientas | ❌ **no ahora** |

**Decisión Monarca:** no inventariar todos los casos raros en código ahora. Si la bóveda está sucia → **cerrar/sanear y nacer limpio** (peaje = costo de inauguración). Manos solo con orden explícita + México/testnet.

---

## Rol

**Tusk** (e **Iron** en el futuro) = amos / escribas del tesoro.

- No solo “ver cuánto hay”.
- **Preparar** la caja: lo que sea → UTA → **USDT**. Ya.
- **No** comprar MNT. **No** abrir short de equilibrio.
- Hoy el código **mira y calcula**; manos ritual OFF.

**Tank** = extractor de datos (no analiza). Kaiser = indicadores (índice + sesgo). Generales leen Tank/Kaiser.  
Metaverso / uso fino de datos = después. Mundos paralelos = posible Iron, no este checkpoint.  
Oído Monarca = Pergamino/Cascada (Telegram = legado a marcar, no reimplementar).

---

## Ley firmada — estado sucio → reset → ideal (2026-08-02)

**Problema:** cuentas con short MNT heredado, entradas muy distintas, spot sin avg fiable, restos de monedas, etc. Analizar y “parchar” cada rareza es caro en ingenio y propenso a sesgos (avg sucio, qty parejo pero dólares mentira).

**Ley Monarca (ahora):**

1. Tusk **diagnostica**: ¿la bóveda ya está en estado **óptimo limpio** (MNT spot + short inverso ≈1:1, entradas coherentes, sin basura relevante)?  
2. Si **sí** → no rehacer; sellar capital_mando + foto (+ clima Kaiser cuando se firme el sello duro).  
3. Si **no** (sucio / medio hecho / short heredado caro o barato vs ahora) →  
   - **Sanear la capa bóveda a cero** (cerrar short MNT de hedge, liquidar/convertir restos no deseados hacia el camino limpio).  
   - **Aceptar comisiones** como peaje de inauguración — no es fracaso.  
   - Correr el **ritual ideal** desde cero (sección siguiente).  
4. **Ámbito del reset:** capa **bóveda** (spot/stables sueltos, hedge MNT). No mezclar por defecto con un manto Igris ya desplegado (eso sería otro ritual).  
5. **Excepción:** solo si el Monarca marca a mano “dejar esta posición como apuesta personal” — no es el default.  
6. **Después** (ejército más pensante): sí se podrá optimizar para no cerrar todo y ahorrar el último céntimo. **Ahora no.**

**Porqué:** la preparación es (en teoría) **una vez**. Igris también prefiere manto sobre bóveda limpia. Pagar fees una vez > programar un tratado por cada rareza.

---

## Escenario ideal (cuenta nueva o tras reset limpio)

Orden vigente (aún **sin** ejecutar en código):

1. **Funding → Trading unificado (UTA)**.  
2. **Mejor camino a USDT** — Convert solo si conviene como atajo; si no, spot: crypto → USDT.  
3. **STOP.** Caja = USDT. No comprar MNT. No short.  
4. Tres cajones: caja USDT · manto Igris · casa Beru (no mezclar).  
5. Potencia del pase = caja/equity USDT.

Si hay MNT+short legado: **sucio**. Saneo a mano (peaje OK). El código no reconstruye.

### Camino Convert vs spot (ley Monarca)

**Convert no es la ley** — atajo **solo si conviene** para llegar a **USDT**.

USDT = casa. USDC u otras estables = restos (duda C2: no mandan potencia).

---

## Potencia del pase (caja USDT)

Referencia = **USDT en UTA** (caja), no el short MNT.

Con ese número, el pase dice cuántos pasos caben.

**Ejemplo:** ~100 USD de caja → potencia hasta paso **3** (acum 76); paso 4 pide acum 116.

El número `capital_mando` del short, si aparece, es **sucio visible** — no gobierna.

---

## Foto de inauguración

Al sellar la preparación **limpia**:

- Precio marca/promedio **spot** MNT.  
- Precio marca/promedio **inverso** MNT.  
- **Spread de nacimiento**.

Micro-ajustes (reponer spot) no borran la foto.  
Capital nuevo engordando bóveda: ahí sí actualizar/mezclar.

Persistencia: `data/tusk_boveda_inauguracion.json` (`sellar` / `cargar`; **no** auto al arise).

---

## Mantenimiento (futuro, sin manos ahora)

- Vigilancia de sucio MNT (alerta, no auto-saneo).  
- Reposición de spot **del molino Beru** ≠ reponer saco MNT.  
- Ajuste de short legado: **prohibido reconstruir**; duda C1.

---

## Orden de trabajo acordado (no saltar a manos)

1. ~~Casos especiales~~ → **cerrados por ley reset** (2026-08-02).  
2. Sello duro capital + clima Kaiser (números/umbrales).  
3. ~~capital_mando hedge → masa Igris~~ **cancelado** (tumor). Potencia = caja USDT.  
4. **Manos** ritual caja USDT solo con `TUSK_BOVEDA_MANOS` + orden Monarca.

---

## Flags

| Flag | Default | Significado |
|------|---------|-------------|
| `TUSK_BOVEDA_MNT_DOCTRINA` | true | Publica `boveda_mnt` (cálculo) |
| `TUSK_BOVEDA_MANOS` | **false** | Prohibido ejecutar ritual / reset |
| `TUSK_BOVEDA_EQUILIBRIO_TOL_PCT` | 0.03 | Tolerancia spot vs short |

---

## Purge docs (cuando toque el mega checkpoint)

- Tank en `02`: extractor multi-frente (no “parcial LTC”); Capitanes no son el centro.  
- Telegram → legado; oído = Pergamino.  
- 95% = colchón/seguro, no muro de poda del modelo viejo (purge §A / código).  
- Greed “en pausa” debe coincidir con `arise` o dejar de decirse pausa.

**Ancla de precios:** índice Bybit = referencia absoluta; Kaiser sesgos vs índice — [`CHECKPOINT_KAISER_INDICE_SESGO.md`](CHECKPOINT_KAISER_INDICE_SESGO.md).
