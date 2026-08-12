# Checkpoint — Beru cableado reset-0 (manos OFF)

**Fecha:** 2026-08-11  
**Mandato Monarca:** despertar = Mega-reset del 0 al precio actual · flota (no solo ETH) · vacío Normal **1,6 %** · **manos OFF** (modificable antes de activar).

## Ley

Al plantar / wake: `centro_local` y `centro_manto` = precio del momento (no promedio L/S de Tusk). Después, Mega/fusiones/resets reales siguen igual.

## Flags (default)

| Flag | Default | Rol |
|------|---------|-----|
| `BERU_WAKE_RESET_0` | true | 0 = precio wake |
| `BERU_SIEMBRA_FLOTA` | true | nacer flota con candado pase |
| `BERU_CAPITAN_WAKE` | NORMAL | 1,6 % (no Ansiedad 1,2) |
| `BERU_MANOS` | **false** | sin órdenes spot |
| `BERU_HILO_ENABLED` | **false** | hilo dormido en arise |

## Código

- `core/beru_wake.py` — centros, capitán, flota, resumen
- `generales/beru.py` — `plantar_semilla_adan` / `despertar_flota_reset_0` / gate manos
- Smoke: `python scripts/validar_beru_wake_reset0_smoke.py`

## Qué NO hace aún

No enciende Beru en `arise_igris` (sigue hibernado). Para activar más adelante: `BERU_HILO_ENABLED=true` + `BERU_MANOS=true` con orden Monarca (checklist **4.0.4**).

## Checklist

`16` · **4.0.4** → cableado dormido `[~]` · activación live pendiente.
