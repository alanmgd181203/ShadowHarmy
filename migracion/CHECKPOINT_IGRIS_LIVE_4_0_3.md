# CHECKPOINT — 4.0.3 Igris live parcial (manos sueltas / books ON)

**Fecha:** 2026-08-05 · **Estado: EN CURSO** (smoke OK · GO bajo guardián hasta ~18:30)  
**Checklist:** `16` ítem **4.0.3** — en progreso; **no PASS** hasta evidencia de manto/meta.

### Smoke 2026-08-05 (~07:34)

`--solo-ojos --segundos 90` → **OJOS_Y_LIBROS_OK**: ETH lineal+inverso 50 bids/asks · Tank VERDE · equity ~1526 · marcha_forzada. Igris no disparó. (Aviso: reconciliación Tusk limpió pesos ilusorios de la sim 4.0.2 al confrontar exchange vacío — esperado en live.)

### GO 2026-08-05 (~07:42)

Guardián + ritual hasta **2026-08-05T18:30:00** · `--permitir-mainnet-manos` (`.env` tiene `MODO_TESTNET=False`). Igris manos ON tras libros. Ver PIDs en `data/logs/arise_igris/guardian.pid` y `orquestador.pid`.

**Riesgos observados:** mordidas bajo mínimo Bybit (~5 USD) en activos chicos (FIL) → `ORDEN_ERROR` / skip; no es crash. Mainnet real.

## Definición (Monarca)

Despertar **Tusk · Tank · Kaiser · Igris**.  
Hibernan **Greed · Beru**.  
Manos reales **sueltas** (`MODO_SIMULACION=False`) — camino hacia manto/paso.  
Orderbook **real** (`BRIDGE_WS_SUBSCRIBE_BOOKS=true`) — no ojos estrechos de la sim.  
Marcha: **marcha_forzada** sellada en `data/marcha_despliegue.json`.  
Bóveda Convert (`TUSK_BOVEDA_MANOS`): **OFF** — engorde Igris no exige ritual MNT manos.

## Rituales

| Pieza | Rol |
|-------|-----|
| `scripts/arise_igris.py` | Ritual oficial parcial 4.0.3 |
| `scripts/vigilar_arise_igris.py` | Guardián (relance + caffeinate + deadline) |
| `data/arise_igris_report.json` | Parte al sellar |
| `data/logs/arise_igris/` | Heartbeat, orquestador, PID guardián |

### Flags útiles

```bash
# Smoke ~90s — solo ojos/libros, sin Igris manos
python3 scripts/arise_igris.py --solo-ojos --segundos 90

# GO ~12h (mainnet exige flag explícito)
python3 scripts/vigilar_arise_igris.py --confirmar-go \
  --durar-hasta 2026-08-05T18:30:00 --permitir-mainnet-manos
```

**Seguridad:** si `MODO_TESTNET=False`, manos Igris ABORTAN sin `--permitir-mainnet-manos` (o `ARISE_IGRIS_PERMITIR_MAINNET=true`). Preferible campo de entrenamiento.

## Qué mirar (parte al Monarca)

- Marcha activa: `marcha_forzada`
- Ojos: Tank VERDE + libros ETH (bids/asks)
- Igris: engorde/ventana hacia meta del paso
- Hibernados: Greed, Beru
- Heartbeat: `data/logs/arise_igris/heartbeat.json`
- Reporte: `data/arise_igris_report.json`

## Criterio PASS (aún no)

Manto ~100% de la meta de engorde del paso bajo marcha forzada, con evidencia en reporte/historial — **no** marcar `[x]` en `16` hasta entonces.

## Vs 4.0.2 sim

| | Sim 4.0.2 | Live parcial 4.0.3 |
|--|-----------|-------------------|
| Manos | atadas / fills ilusorios | sueltas Bybit |
| Books | OFF (ojos estrechos) | ON |
| Guardián | opcional | `vigilar_arise_igris` |

## Siguiente

Mantener corrida hasta deadline (~18:30 local). Al volver: leer reporte + heartbeat; decidir si amplía ventana o cierra sello hacia PASS.


## Para Jess (revisar estado ~1 h)

En la Mac del cuartel el ritual **ya debería estar corriendo** bajo guardián hasta ~18:30.

```bash
# ¿Vive?
pgrep -fl 'arise_igris|vigilar_arise'
cat data/logs/arise_igris/heartbeat.json
tail -30 data/logs/arise_igris/guardian.log
tail -50 data/logs/arise_igris/orquestador.log

# Relanzar solo si murió (mainnet — flag explícito)
python3 scripts/vigilar_arise_igris.py --confirmar-go \
  --durar-hasta 2026-08-05T18:30:00 --permitir-mainnet-manos
```

Marcha: **forzada**. Greed/Beru hibernan. Manos ON. No editar `.env` en el commit.
