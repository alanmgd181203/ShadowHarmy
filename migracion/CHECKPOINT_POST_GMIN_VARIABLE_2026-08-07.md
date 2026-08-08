# Checkpoint post — G_min variable por Santo

**Fecha:** 2026-08-07  
**Pre:** [`CHECKPOINT_PRE_GMIN_VARIABLE_2026-08-07.md`](CHECKPOINT_PRE_GMIN_VARIABLE_2026-08-07.md) · tag `checkpoint-pre-gmin-variable-2026-08-07`

---

## Qué quedó cableado

| Pieza | Estado |
|-------|--------|
| **Fuente G_min** | `data/bybit_minimos_orden.json` (prioridad) · respaldo `bybit_parametros_mercado.json` |
| **Regla** | spot USDT → linear → inverse · piso configurable (default **$1**) · default config **$1** |
| **Motor capital** | `g_min_usd(activo)` lee variable · fricción/ceil Soldado recalculan solos |
| **Mordida Cazador** | default = G_min del Santo · override solo si `BERU_CAZADOR_MORDIDA_USD > 0` |
| **Doctrina** | Mariscal 0,1 % = **G_min** · PLENO 1 % = **10×G_min** · docs 22/23/CODEX/`16` |
| **Panel** | Pergamino Beru/Igris + Streamlit muestran G_min cuando hay dato de archivo |
| **Smokes** | `validar_g_min_variable_smoke.py` · capital/pase sin romper |

**Script:** `scripts/sync_bybit_minimos_orden.py` · Jess: [`PEGAR_JESS_SYNC_MINIMOS_BYBIT.md`](PEGAR_JESS_SYNC_MINIMOS_BYBIT.md)

---

## Sync Bybit (esta forja USA)

- Intento vivo: **403 Forbidden** (Bybit desde USA).
- Fallback: `--from-parametros` → flota 22 Santos con **G_min=5.0** (spot_usdt) desde BD 2026-07-21.
- **No son mínimos frescos de hoy** — Jess en México debe correr el sync vivo.

---

## Ranking / pase — PENDIENTE

El orden de batalla **no** se regeneró. Sigue el pase firmado.  
Cuando Jess traiga peajes vivos y el Monarca analice (¿hay Santos a $1?), entonces regenerar ranking/pase.

---

## Qué NO se tocó

- Beru manos / arise live  
- Ley de Masa Igris (piso lineal)  
- PASE_BATALLA_13_SANTOS / regeneración ranking  

---

## Próximos pasos

1. Jess: pegar [`PEGAR_JESS_SYNC_MINIMOS_BYBIT.md`](PEGAR_JESS_SYNC_MINIMOS_BYBIT.md) y traer G_min vivos.  
2. Monarca: mirar peajes reales de la flota.  
3. Recién entonces: regenerar pase/ranking con G_min verdadero.
