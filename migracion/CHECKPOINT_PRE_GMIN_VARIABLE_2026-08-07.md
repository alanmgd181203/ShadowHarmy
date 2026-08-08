# Checkpoint previo — G_min variable por Santo

**Fecha:** 2026-08-07  
**Tag git:** `checkpoint-pre-gmin-variable-2026-08-07`  
**Árbol:** limpio al sellar (sin suciedad previa).

---

## Estado del ejército (antes del rearme)

| Pieza | Valor vivo |
|-------|------------|
| **G_min** | **Fijo $5** por Santo (diccionario estático + default 5) |
| **Mordida Cazador** | **$5** (`BERU_CAZADOR_MORDIDA_USD`) |
| **Mariscal / 0,1 %** | Pensado como **$5 = G_min**; PLENO ~**10×G_min** PnL/1 % (= $50 con G_min=5) |
| **Pase / ranking** | [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md) — **intactos**; no regenerar aún |

Motor de capital: fricción Soldado 0,8 % → Capitán 0,4 % → General 0,2 % → Mariscal 0,1 %.  
Con G_min=5 y lev≈100 (ETH/BTC): Soldado ceil ~**14** · Mariscal ~**105**.

BD de parámetros Bybit (`data/bybit_parametros_mercado.json`) ya guarda mínimos por pierna, pero Beru **no** leía `G_min` vivo por Santo: todo caía en el 5 fijo.

---

## Por qué el cambio

Bybit no peajea igual en todos los rails:

- **Spot** (casa Beru) puede pedir mínimo real distinto — a veces cerca de **~$1**, no siempre $5.
- **Lineal / inverso** (manto Igris) siguen su propio peaje; el piso del manto L+S no se confunde con la mordida Beru.

Si Mariscal = **PnL / 0,1 % = G_min del Santo**, y el spot de ese Santo vale $1, entonces el pensamiento del ejército debe ser **G_min real**, no un 5 clavado. De ahí: **variables por Santo** alimentadas por mínimos Bybit.

**Analogía:** cada Santo tiene su peaje de entrada al temple. Antes cobrábamos 5 a todos; ahora cada altar declara su peaje.

---

## Qué NO se hace en este corte

- Regenerar pase / ranking de batalla.
- Soltar Beru manos.
- Bajar el piso de Ley de Masa Igris a 1 en lineal (derivados mantienen peaje).

---

## Siguiente

Cablear lectura `G_min(activo)` → sync Bybit → análisis Monarca → **entonces** regenerar pase.
