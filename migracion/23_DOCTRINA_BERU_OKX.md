# 23 — Beru rango en OKX (mar único)

**Estado:** migración Monarca **2026-08-31** · sin inverso · sin pentiverso

## Veredicto

Beru rango opera en **OKX SWAP USDT** por defecto (`BERU_MAR=okx`). Igris / manto dual pueden seguir en Bybit; **no se mezclan** en el mismo Santo vivo.

## Geometría (igual doctrina 22b)

Vacío · Oz · Red · Sangre — perfiles `normal` / `feria`. Solo cambia el **mar** y el **piso de orden** (menor en muchas alts).

## Mar

| Variable | Default | Rol |
|----------|---------|-----|
| `BERU_MAR` | `okx` | `okx` \| `bybit` (legacy) |
| `OKX_API_KEY` / `SECRET` / `PASSPHRASE` | `.env` | Manos |
| `OKX_FLAG` | `0` | `1` = paper trading |

Frente interno sigue siendo `ETHUSDT_LINEAL`; en OKX es `ETH-USDT-SWAP`.

## Ritual (orden correcto)

**1. Catalogo completo OKX** (todo lo que la API publica permite):

```bash
python scripts/sync_okx_catalogo_completo.py
```

Salida: `data/okx_catalogo_completo.json` (SPOT, MARGIN, SWAP, FUTURES, OPTION) + refresco `okx_parametros_mercado.json`.

**2. Tabla corta Santos Beru** (opcional):

```bash
python scripts/sync_okx_minimos_beru.py
```

**2. Smoke** · **3. Ojos** · **4. Manos** (como abajo).

## Purga doctrinal

- **No** usar inverso ni ley de masa en Beru rango.
- **No** reconciliar Tusk Bybit cuando `BERU_MAR=okx` (posiciones OKX = fase siguiente).
- Bybit queda para Igris / coliseo / bóveda histórica.

## Archivos del altar OKX

- `core/okx_bridge.py` — ojos WS + manos REST
- `core/lote_okx.py` — contratos / minSz
- `core/beru_bridge.py` — fábrica del puente
- `data/okx_parametros_mercado.json` — sync público

## Despertar escalonado (reloj BTC mil)

Entrada despromediada: cada cruce de **mil USD** en BTC despierta **1 rojo + 1 amarillo** de `piedra_asignacion.json`.

**Regla dura:** cada Santo = **proceso propio** (sin fila API compartida como Bybit viejo).

```bash
python scripts/inicializar_cola_despertar_mil_btc.py
python scripts/vigilar_btc_mil_despertar.py --intervalo 30
```

Estado: `data/beru/rango/despertar_mil_btc.json` · logs: `data/beru/rango/despertar_mil/`

Modos cruce: `cada_zona` (default) · `por_direccion` · `unico`.

Manos solo con `--manos-go` en el vigilante (después de ojos validados).
