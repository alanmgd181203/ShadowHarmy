# Jess Bybit sync — 2026-07-21T04:00:27Z

## Hecho
- Linear Trading: **678** · Inverse: **26**
- Spot USDT: **425** · Spot USDC: **87**
- Bases en `bybit_parametros_mercado.json`: **774**
- Diccionario flota Beru: **22** activos
- Config `MANTO_LEVERAGE_*` alineado al vivo (salvo --skip-apply-config)

## Foco apalancamiento

| Activo | Linear | Inverse |
|--------|-------:|--------:|
| BTC | 100.0 | 100.0 |
| ETH | 100.0 | 100.0 |
| LTC | 50.0 | 50.0 |
| SOL | 100.0 | 50.0 |
| XRP | 100.0 | 50.0 |
| ADA | 75.0 | 50.0 |

## Foco minimos (USD est.)

| Activo | Lin min | Inv min | **Piso manto** | Spot USDT |
|--------|--------:|--------:|---------------:|----------:|
| BTC | 5.0 | 1.0 | **5.0** | 5.0 |
| ETH | 5.0 | 1.0 | **5.0** | 5.0 |
| LTC | 5.0 | 1.0 | **5.0** | 5.0 |
| SOL | 5.0 | 1.0 | **5.0** | 5.0 |
| XRP | 5.0 | 1.0 | **5.0** | 5.0 |
| ADA | 5.0 | 1.0 | **5.0** | 5.0 |

## Fees
Maker/taker por simbolo: GET /v5/account/fee-rate (autenticado). Sin API keys solo queda deliveryFeeRate en instrumentos.
- Se obtuvo fee-rate autenticado (muestra).

## Archivos
- `data/bybit_parametros_mercado.json` — BD lev + minimos + piso_manto + spot
- `data/jess_bybit_sync/apalancamientos_vivo.json`
- `instrumentos_linear.jsonl` / `inverse` / `spot_usdt` / `spot_usdc`
- `risk_limits_muestra.json` · `fees.json`
- `config/diccionario_beru_flota_manto.json` · `core/config.py`

## Siguiente
1. Revisar este RESUMEN (LTC/SOL/BTC + pisos manto)
2. Commit + push (ver migracion/JESS_SINCRONIZAR_BYBIT.md)
3. Monarca: `git pull`

Refresh futuro: `python scripts/kaiser_actualizar_parametros_bybit.py`
