# Checkpoint — Cirugía Beru v1 (injerto Jess útil) · 2026-08-12

**Manos:** no implica Beru libre ni spot real en USA. Nivel 3 dormido.

## Qué se soldó (útil de Jess)

1. **Ley neutro** — `core/beru_ley.py`: no engorda, no come oxígeno Igris, abortar solo ceguera.
2. **Wake reset-0** — `core/beru_wake.py`: 0 = precio del despertar; flota; Capitán Normal 1,6 %.
3. **Ojos** — `core/beru_ojos.py`: muleta REST si cae el torrente.
4. **Fantasma (nivel 2)** — `core/beru_fantasma.py` + `scripts/arise_beru_fantasma.py`: bitácora, cero órdenes.
5. **Cuerpo** — `generales/beru.py` alineado a ley/wake/fantasma/ensayo.
6. **Tusk** — sombra registra masa siempre; `consumio_auth` para neutro.
7. **Rail** — USDT-only solo con flag explícito (no acoplado a LIVE_BERU).
8. **Doctrina 22** + checkpoints Jess + smokes ley/wake/fantasma.
9. **Nivel 3** — módulos/ritual/smoke **traídos pero OFF** (ver DUDAS B1).

## Qué no se hizo

- No borrar `beru_live_testnet*` (DUDAS B2).
- No encender `BERU_MANOS` / `BERU_ENSAYO_NIVEL3` / hilo en Arise Igris.
- No merge ciego del resto de master (Beru fantasma/simulación de Jess aparte de Igris USA).

## Dudas

Ver `DUDAS_CIRUGIAS_MENORES_2026-08-12.md` (B1…B10).

## Smoke

```
python scripts/validar_beru_ley_neutro_smoke.py
python scripts/validar_beru_wake_reset0_smoke.py
python scripts/validar_beru_fantasma_smoke.py
```

## Siguiente

Ensayo fantasma en cuartel cuando el Monarca diga · nivel 3 solo con GO explícito · Igris sigue su propio camino.
