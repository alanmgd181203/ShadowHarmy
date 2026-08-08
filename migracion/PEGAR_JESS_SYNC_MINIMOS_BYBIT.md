# PEGAR Jess — Sync mínimos de orden Bybit (G_min por Santo)

> **Puerta oficial:** [`ORDEN_ACTIVA_JESS.md`](ORDEN_ACTIVA_JESS.md) — este archivo es **receta/anexo**, no la puerta.

**Para:** Cursor en la Mac de Jess (México)  
**Qué es:** ritual de **ojos** — actualiza el peaje real de cada Santo (mínimo spot/lineal/inverso) para que Beru calcule `G_min` vivo.  
**Qué NO es:** no regenera el pase/ranking · no dispara órdenes · no es Asalto Igris · no enciende Beru manos.

Motor: `scripts/sync_bybit_minimos_orden.py`  
Salida canónica: `data/bybit_minimos_orden.json`  
Doctrina: Mariscal PnL/0,1 % = **G_min del Santo** · PLENO 1 % = **10×G_min**.

---

## Mandato listo para pegar en Cursor (Agent)

```
Actualiza el repo y sincroniza SOLO los mínimos de orden Bybit (G_min por Santo).
NO arranques arise / vigilante / manos / Beru live.
NO regeneres el pase ni el ranking.

1) git status && git pull origin master

2) Un solo terminal (red a Bybit):

python scripts/sync_bybit_minimos_orden.py --also-parametros

   Por defecto:
   - Pide instruments-info spot / linear / inverse
   - Escribe data/bybit_minimos_orden.json con G_min por base
   - También refresca data/bybit_parametros_mercado.json
   - SIN órdenes · SIN manos

   Si solo quieres la flota manto/Beru (más rápido):

python scripts/sync_bybit_minimos_orden.py --flota-only --also-parametros

3) Mira en la salida:
   - ETH / BTC / SOL / XRP / MNT — columna G_min y si salió de spot_usdt o linear
   - Si spot < 5 en algún Santo, anotar para el Monarca (peaje real)

4) Smoke frío (sin red):

python scripts/validar_g_min_variable_smoke.py
python scripts/validar_beru_capital_smoke.py

5) Avisa al Monarca con 5–10 G_min de la flota (sin pegar el JSON entero).
   El pase/ranking queda PENDIENTE hasta su análisis.

NO subas .env, Ima/, tools/, videos ni logs.
NO mezclar con ritual Asalto 4.0.3 ni noche historial en el mismo terminal.
```

### Si Bybit timeout / 403 desde USA (o falla la red)

```
python scripts/sync_bybit_minimos_orden.py --from-parametros --flota-only
```

Deriva G_min de la BD `bybit_parametros_mercado.json` ya existente (puede estar desfasada).  
La salida lleva `advertencia` en meta — el Monarca lo sabrá.

### Qué mirar en el pergamino de salida

| Campo | Significado ejército |
|-------|----------------------|
| `G_min` | Peaje del Santo para Beru (mordida / Mariscal 0,1 %) |
| `G_min_fuente` | De qué rail salió (`spot_usdt` preferido → `linear`) |
| `spot_usdt.min_usd_est` | Mínimo estimado casa spot |
| `linear` / `inverse` | Peajes del manto (Igris; no bajar Ley de Masa aquí) |

---

## Relación con otros rituales Jess

| Ritual | Archivo | Manos |
|--------|---------|-------|
| Sync mínimos G_min | este | OFF |
| Sync parámetros Coliseo / lev | [`JESS_SINCRONIZAR_BYBIT.md`](JESS_SINCRONIZAR_BYBIT.md) | OFF |
| Noche historial Igris | [`PEGAR_JESS_NOCHE_HISTORIAL_IGRIS.md`](PEGAR_JESS_NOCHE_HISTORIAL_IGRIS.md) | OFF |
| Asalto live | [`PEGAR_JESS_IGRIS_LIVE_ASALTO.md`](PEGAR_JESS_IGRIS_LIVE_ASALTO.md) | ON selectivo |

Checkpoint: [`CHECKPOINT_POST_GMIN_VARIABLE_2026-08-07.md`](CHECKPOINT_POST_GMIN_VARIABLE_2026-08-07.md)
