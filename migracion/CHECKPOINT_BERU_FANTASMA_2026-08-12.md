# Checkpoint — Beru manos fantasma (nivel 2 ensayo)

**Fecha:** 2026-08-12  
**Mandato Monarca:** ojos reales Bybit · Beru late · **cero órdenes** · bitácora de lo que habría disparado · Igris dormido.

## Candados del ritual

| Flag | Valor | Rol |
|------|-------|-----|
| `MODO_SIMULACION` | true | Nunca `place_order` real |
| `BERU_MANOS_FANTASMA` | true | Imprime + jsonl cada disparo |
| `BERU_HILO_ENABLED` | true | Pulso Beru ON |
| `BERU_MANOS` | false | Manos reales OFF |
| `BERU_ENGORDE_PERMITIDO` | false | Sin engorde |
| `BERU_NEUTRO_MARGEN` | true | No come oxígeno Igris |
| `BERU_SPOT_MARGEN_ENABLED` | false | Sin apalancar spot |
| `BRIDGE_WS_BASES` | Santos del ensayo | **Ojos estrechos** (no trinidad completa) |
| `BRIDGE_WS_SUBSCRIBE_BOOKS` | false | Sin muros pesados |
| `BINANCE_REF_ENABLED` | false | Menos torrentes al arrancar |
| `BRIDGE_WS_PROXY` | direct | Sin SOCKS (evita ceguera por proxy de entorno) |
| `BERU_OJOS_REST_FALLBACK` | true | Muleta ticker spot si WS muere |

Santos default: **ADA, BCH, MNT** (manto vivo).

## Parches 2026-08-12

1. Ojos estrechos (no trinidad completa) + proxy direct.
2. Siembra fantasma sin candado de pasos Igris.
3. **Muleta REST** de precios cuando el torrente WS cae.
4. **Caza por Santo del barco** (BCH→BCH, no todo a ADA).
5. **Corte de tiempo mata hilos** (no deja zombie reconectando).

## Cómo correr

```
python3 scripts/arise_beru_fantasma.py --segundos 1200
python3 scripts/arise_beru_fantasma.py --segundos 600 --activos ADA,BCH,MNT
```

Al arrancar: `Sentidos[estrecho]` · `[OJOS] Modo estrecho…` · luego `px>0` / `[OJOS_REST] muleta` si hace falta · siembra · al corte: Sellado y el proceso **termina**.

Ctrl+C también sella. Bitácora: `data/logs/beru_fantasma/disparos.jsonl`.

## Smoke frío

```
python3 scripts/validar_beru_fantasma_smoke.py
```

## Qué NO hace

No engorda Igris. No manda mercado a Bybit. No es nivel 3 (manos chiquitas reales).

## Siguiente

Si la bitácora cuadra 20–40 min con ojos vivos o muleta → nivel 3 con orden Monarca.

Nivel 3 listo: [`CHECKPOINT_BERU_MANOS_CHIQUITAS_2026-08-12.md`](CHECKPOINT_BERU_MANOS_CHIQUITAS_2026-08-12.md) · ritual `arise_beru_manos_chiquitas`.
