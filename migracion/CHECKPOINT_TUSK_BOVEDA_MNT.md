# CHECKPOINT — Tusk / Iron: bóveda MNT (escenario ideal)

**Estado:** doctrina Monarca 2026-08-01 (actualizado misma noche) · **código: lectura / cálculo**  
**Manos:** **OFF** — no ejecutar ritual, no mainnet de preparación.  
**Código frío:** `core/tusk_boveda_mnt.py` + `tusk_tesoreria.boveda_mnt`  
**Smoke:** `python scripts/validar_tusk_boveda_mnt_smoke.py`

---

## Qué está fundido vs qué no

| Pieza | Estado |
|-------|--------|
| Doctrina escenario ideal + Convert vs spot | ✅ pergamino + `plan_ritual_ideal()` |
| Capital de mando = short×entrada (avg) | ✅ cálculo en `boveda_mnt` |
| Equilibrio spot/short + sesgo spot | ✅ cálculo |
| Foto viva spot vs inverso (+ sellar inauguración API) | ✅ cálculo / persist opcional |
| Potencia del **pase** desde capital_mando | ✅ cálculo frío (no mueve Igris) |
| Oxígeno UTA / equity vivo | ✅ tesorería previa (sigue existiendo) |
| Ritual manos (Funding→UTA, Convert/spot, shorts) | ❌ **no** — `TUSK_BOVEDA_MANOS=false` |
| capital_mando → `masa_autorizada` de Igris | ❌ pendiente (gate Monarca) |
| Casos especiales / PnL bóveda | ❌ siguiente bloque doctrinal |
| Fundir Tusk al 100% con todas las herramientas | ❌ **no ahora** |

**Decisión Monarca:** no es buen momento de fundir manos al 100%. Primero casos especiales en pergamino; luego cableados fríos; manos solo con orden explícita + testnet/México.

---

## Rol

**Tusk** (e **Iron** en el futuro) = amos / escribas del tesoro.

- No solo “ver cuánto hay”.
- **Preparar** la bóveda para que el ejército pueda usarla.
- **Mantener** el equilibrio spot MNT ↔ short inverso.
- Hoy el código **mira y calcula**; el ritual de manos es **futuro**.

**Tank** = extractor de datos (no analiza). Kaiser = indicadores. Generales leen Tank/Kaiser.  
Metaverso / uso fino de datos = después. Mundos paralelos = posible Iron, no este checkpoint.  
Oído Monarca = Pergamino/Cascada (Telegram = legado a marcar, no reimplementar).

---

## Escenario ideal (cuenta nueva o capital suelto)

Orden doctrinal (aún **sin** ejecutar en código):

1. **Funding → Trading unificado (UTA)** — el capital en financiamiento no sirve al ejército.  
2. Activar **descuento de tarifa MNT** / MNT como colateral desde el minuto uno.  
3. **Mejor camino** a MNT (ver § Camino Convert vs spot).  
4. **Lote semilla** (~1–5% o mínimo para abrir short) → vía ese camino → **MNT spot**.  
5. Abrir **short inverso MNT** ≈ ese spot.  
6. Repetir **a poquitos** hasta casi todo el capital así.  
7. Sesgo: un poco **más spot** que short (el spot paga fees y se gasta).  
8. Tolerancia de equilibrio (no exigir igualdad al céntimo).  
9. **Sellar** foto inauguración + fijar **capital de mando**.  
10. Tusk pregunta al pase: **con este capital_mando, ¿hasta qué paso/rango hay potencia?** — antes de manto/Beru.

### Camino Convert vs spot (ley Monarca)

**Convert no es la ley** — es un atajo **solo si conviene**.

1. Evaluar si **Convert** (Bybit) ofrece buena oportunidad (precio/peaje vs mercado).  
2. Si **sí** → se puede usar Convert para ese tramo.  
3. Si **no** → **todo por spot**: p. ej. vender LTC/XRP/… → **USDT o USDC** (mejor peaje + spread) → comprar **MNT** spot.  
4. USDT = casa natural del ejército; USDC = válido si el camino es claramente mejor.  
5. El juicio (Tank/Kaiser/Ancla + Tusk) elige el **mejor camino** hacia MNT spot + short.

**Porqués**

- Poquitos: fees/spreads; el short se ata a lo **realmente** llegado a MNT.  
- Más spot: comisiones consumen MNT spot → sin reposición gana el short.  
- Convert vs spot: no regalar peaje.

---

## Capital de mando → pase (después de preparar)

Referencia del ejército = **pierna short (inverso)**:

`capital_mando_usd ≈ size_MNT × precio_entrada (avg)`

- Equity vivo puede ser un poco mayor (sesgo spot / polvo).  
- Ganancias/pérdidas mark-to-market: **capítulo aparte** (calma).  
- **No** usar el baile del equity como única verdad del tamaño del ejército.

Con ese número, el **pase** (`pase_director.potencia_n`) dice cuántos pasos caben.

**Ejemplo:** ~100 USD de capital_mando → potencia hasta paso **4** (acum 96); paso 5 pide acum 123. Zona primeros Soldados / Aspirante — no Aprendiz (411) ni Brujo.

Hoy: el bloque `boveda_mnt.potencia_pase` publica ese cálculo.  
Igris/masa_autorizada **aún no** se gobiernan solo por capital_mando.

---

## Foto de inauguración

Al sellar la preparación:

- Precio marca/promedio **spot** MNT.  
- Precio marca/promedio **inverso** MNT.  
- **Spread de nacimiento**.

Sirve para distinguir sesgo normal de anomalía después.  
Micro-ajustes (reponer spot) no borran la foto.  
Capital nuevo engordando bóveda: ahí sí actualizar/mezclar.

Persistencia: `data/tusk_boveda_inauguracion.json` (`sellar` / `cargar`; **no** auto al arise).

---

## Mantenimiento (futuro, sin manos ahora)

- Contar MNT gastado en fees.  
- Reponer spot cuando salga de banda / haya mínimo de orden.  
- Si el short se ajusta en cada reposición: **pendiente de firmar**.

---

## Orden de trabajo acordado (no saltar a manos)

1. **Casos especiales** en pergamino (siguiente charla).  
2. Cableados fríos restantes (PnL lectura, etc.).  
3. Opcional: capital_mando → masa Igris con gate explícito.  
4. **Manos** ritual solo con `TUSK_BOVEDA_MANOS` + orden Monarca + México/testnet.

---

## Flags

| Flag | Default | Significado |
|------|---------|-------------|
| `TUSK_BOVEDA_MNT_DOCTRINA` | true | Publica `boveda_mnt` (cálculo) |
| `TUSK_BOVEDA_MANOS` | **false** | Prohibido ejecutar ritual |
| `TUSK_BOVEDA_EQUILIBRIO_TOL_PCT` | 0.03 | Tolerancia spot vs short |

---

## Purge docs (cuando toque el mega checkpoint)

- Tank en `02`: extractor multi-frente (no “parcial LTC”); Capitanes no son el centro.  
- Telegram → legado; oído = Pergamino.  
- 95% = colchón/seguro, no muro de poda del modelo viejo (purge §A / código).  
- Greed “en pausa” debe coincidir con `arise` o dejar de decirse pausa.

**Ancla de precios (2026-08-02):** índice Bybit = referencia absoluta; Kaiser medirá sesgos vs índice — ver [`CHECKPOINT_KAISER_INDICE_SESGO.md`](CHECKPOINT_KAISER_INDICE_SESGO.md). El sello de capital de bóveda podrá contrastar contra ese clima **cuando** el Monarca lo firme; hoy no es ley dura de Tusk.
