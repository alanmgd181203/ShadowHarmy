# CHECKPOINT — 4.0.2 Igris sim (manos atadas / ilusorias)

**Fecha:** 2026-08-04 · **Estado: SELLADO (corrida viva Monarca)**  
**Ritual:** `python scripts/arise_igris_sim.py` · sello forzada `--segundos 180`

## Definición (Monarca)

Despertar **Kaiser · Tank · Tusk · Igris**.  
Manos reales **atadas** (`MODO_SIMULACION=True`).  
Manos **ilusorias** (Igris confirma fills sin `place_order` a Bybit).  
**Greed / Beru** hibernados. Bóveda manos OFF.

## Doctrina — manto en lote (no Beru a Beru)

Igris prepara el **manto de todo el lote en potencia** en paralelo: ojos y mordidas sobre todos los Santos/activos de `trabajo`, no solo el foco.  
El Pase marca progreso **dentro del lote** por cobertura de cada Santo, sin cola forzada 1→2→3. La cola fina (reserva) sigue en orden.

## Ojos estrechos → puerta por ticker

Con `BRIDGE_WS_SUBSCRIBE_BOOKS=false` la puerta §E usa ticker sintético (`IGRIS_TICKER_PUERTA_SI_SIN_LIBRO=auto`) + piso min-orden. HTTP: `BYBIT_RECV_WINDOW_MS=60000`.

## Sellos vivos

- **Asalto (~90 s):** `BOOTSTRAP_MANTO` ETH+HYPE · masa ~0,20→0,38 · frentes→7.
- **Marcha Forzada (~180 s, 2026-08-04):** `ENGORDE_DUAL` MNT+SOL+LINK · masa bruta **~94** · **15 frentes** · log `data/logs/arise_igris_sim_forzada_4_0_2.log` · reporte `data/arise_igris_sim_report.json`. Manos reales nunca soltadas.

## Vs arena

| | Arena `3.10.7a` | Sim `4.0.2` |
|--|-----------------|-------------|
| Tusk | mock limpio | bóveda/oxígeno real |
| Doctrina pase | a menudo saltada | marcha + fill 100% + reserva 1 |
| Objetivo | prueba corta | dry-run camino a live |

## Siguiente

**4.0.3** Igris live hasta manto 100% del paso (**solo con orden explícita del Monarca**).
