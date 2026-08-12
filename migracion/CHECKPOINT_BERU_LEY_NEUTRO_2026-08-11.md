# Checkpoint — Beru ley neutro (revisión profunda 2026-08-11)

**Mandato Monarca:** Beru **no toca margen**. Solo intercambia en spot lo que una pierna gana por lo que la otra pierde. **No engorda.** Abortar solo si está **ciego** (sin precio / coma de muchos segundos), no por ROJO ligero de Tank. Manos OFF hasta que el Monarca despierte.

## Flags (default)

| Flag | Valor | Efecto |
|------|-------|--------|
| `BERU_NEUTRO_MARGEN` | true | No consume `masa_autorizada` (oxígeno Igris) |
| `BERU_ENGORDE_PERMITIDO` | **false** | Sin +G_min frontera · sin clon capas · sin masa% negociador |
| `BERU_ABORTAR_SOLO_CEGUERA` | true | ROJO con precio vivo → sigue |
| `BERU_CEGUERA_COMA_S` | 15 | Sin update en nodos → ciego |
| `BERU_MANOS` / `BERU_HILO_ENABLED` | **false** | Dormido hasta GO |

## Código tocado

- `core/beru_ley.py` — ley central
- `generales/beru.py` — caza/cosecha/trail sin engorde; visión ceguera
- `generales/tusk.py` — reserva con masa registrada sin restar oxígeno si neutro
- Wake previo: reset-0 · flota · Normal 1.6 (`beru_wake`)

## Smokes

```
python scripts/validar_beru_ley_neutro_smoke.py
python scripts/validar_beru_wake_reset0_smoke.py
```

## Qué NO está activo

Hilo Beru en arise / órdenes spot. El Monarca decide el DESPIERTA (`BERU_HILO_ENABLED=true` + `BERU_MANOS=true`).
