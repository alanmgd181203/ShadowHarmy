# CHECKPOINT — Mundo A abolido (DEMO Bybit / testnet)

**Fecha:** 2026-08-11 · **Orden Monarca:** solo Mundo B (Arena/sim) + Mundo C (mainnet + candados).

## Qué se cortó

- Rituales / lanzadores: `igris_live_testnet*`, `beru_live_testnet*`, `limpiar_eth_testnet`, `.command` Testnet, runbook `18_ARRANQUE_TESTNET`, recetas México 3.9.9 / 3.10.7b.
- Flags `LIVE_IGRIS_TESTNET` / `LIVE_BERU_TESTNET` y llaves duales DEMO.
- Bridge fija `testnet=False`. `MODO_TESTNET=True` → **ABORT** al cargar `core.config`.

## Qué quedó

- Actas históricas PASS 3.9.9 / 3.10.7b / M1 en checklist (sin paths vivos).
- Arena + `MODO_SIMULACION`.
- Arise mainnet + `--permitir-mainnet-manos`.

## .env cuartel

Dejar `MODO_TESTNET=False` (o quitar la línea). Quitar `BYBIT_TESTNET_*` si existían. No commitear secretos.
