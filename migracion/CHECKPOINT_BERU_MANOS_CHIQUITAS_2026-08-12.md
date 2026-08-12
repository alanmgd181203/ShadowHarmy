# Checkpoint — Beru manos chiquitas (nivel 3 ensayo)

**Fecha:** 2026-08-12  
**Mandato Monarca:** ojos reales · Beru late · **órdenes reales acotadas** · todo en consola · Igris dormido.

## Candados del ritual

| Flag | Valor | Rol |
|------|-------|-----|
| `MODO_SIMULACION` | **false** | place_order real |
| `BERU_MANOS` | **true** | Manos ON |
| `BERU_MANOS_FANTASMA` | **false** | Si fantasma ON, no llega a Bybit |
| `BERU_ENSAYO_NIVEL3` | **true** | Candados + bitácora `[BERU_LIVE]` |
| `BERU_ENSAYO_MAX_ORDENES` | **1** | Techo de **cazas** nuevas |
| `BERU_ENSAYO_SOLO_LONG` | **true** | No SHORT (evita vender sin inventario) |
| `BERU_ENGORDE_PERMITIDO` | false | Sin engorde |
| `BERU_NEUTRO_MARGEN` | true | No come oxígeno Igris |
| Ojos | estrechos + muleta REST | Igual que nivel 2 |

Santo default: **MNT** (mordida ≈ G_min ~$5).

## Qué ver en consola

- `[BERU_LIVE] … CAZA_ENVIANDO` → va a Bybit  
- `[BERU_LIVE] … ORDEN_OK` → fill real  
- `[BERU_LIVE] … TECHO_CAZAS` → no abre más cazas (puede cosechar lo abierto)  
- `[BERU_LIVE] … SKIP_SHORT` → precio subió; ensayo espera bajada para LONG  
- `[OJOS_REST]` · `[BERU] casa=MNT…` · al corte: Sellado y el proceso **termina**

## Cómo correr

```
python3 scripts/arise_beru_manos_chiquitas.py --segundos 900
python3 scripts/arise_beru_manos_chiquitas.py --segundos 600 --activos MNT --max-ordenes 1
```

Ctrl+C también sella. Bitácora: `data/logs/beru_ensayo/disparos.jsonl`.

## Smoke frío

```
python3 scripts/validar_beru_manos_chiquitas_smoke.py
```

## Qué NO hace

No engorda Igris. No abre flota de 3 Santos. No SHORT. No es ejército libre sin techo.

## Predecesor

Nivel 2 fantasma: [`CHECKPOINT_BERU_FANTASMA_2026-08-12.md`](CHECKPOINT_BERU_FANTASMA_2026-08-12.md).
