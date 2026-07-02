# 01 — Arquitectura

## Capas del sistema (runtime Shadow Army)

```
                    ┌─────────────┐
                    │   Monarca   │  (humano / Telegram / config)
                    └──────┬──────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐         ┌───────────┐          ┌──────────┐
│ Bellion │◄────────│   Tusk    │─────────►│  Bridge  │──► Bybit API/WS
│ (audit) │         │ (tesoro)  │          │ (Bybit)  │
└─────────┘         └─────┬─────┘          └──────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    ┌─────────┐     ┌──────────┐     ┌─────────┐
    │  Tank   │────►│ Capitanes │────►│  Beru   │
    │ (radar) │     │ (filtro)  │     │ (caza)  │
    └─────────┘     └──────────┘     └────┬────┘
         │                               │
         └───────────────┬───────────────┘
                         ▼
                  ┌─────────────┐
                  │    Greed    │  PriorityQueue + TTL
                  │   (altar)   │  DISPARO → exchange
                  └──────┬──────┘
                         ▼
                  ┌─────────────┐
                  │    Igris    │  margen, espejos, poda
                  │  (escudo)   │
                  └─────────────┘
```

## Flujo de una intención de trade

1. **Tank** actualiza `MarketContext` por frente (precio, spread, volatilidad, latencia, semáforo VERDE/AMARILLO/ROJO).
2. **Beru** / **Igris** crean `IntencionAccion` (tipo, masa, dirección, prioridad, `dedupe_key`, TTL).
3. **Tusk** `solicitar_reserva` — valida oxígeno (`masa_autorizada`).
4. **Greed** `arbitrar` — cola por prioridad; valida TTL y semáforo Tank; enruta a ejecutores.
5. **Bridge** debería enviar orden y confirmar fill → hoy prototipo: **DISPARO_SIMULADO** (actualiza `pesos` en memoria).
6. **Bellion** anota eventos; **Tusk** persiste `tusk_data.json` cada ~10s.

## Orquestación (`arise`)

Patrón: `asyncio.gather` de hilos eternos:

| Hilo | Responsable |
|------|-------------|
| `tusk.latido_persistencia` | JSON atómico |
| `tank.vigilar_aguas` | WS / contextos |
| `bridge.conectar` | tickers |
| `bridge.hilo_sincronizacion_nav` | balance wallet |
| `beru.hilo_beru_berserker` | legión / ships |
| `igris.vigilar_manto_operativo` | margen 80–95% |
| `greed.arbitrar` | altar |
| `dashboard.refrescar` | consola 1 Hz |

## Modelos de datos clave

### `BeruShip`

Unidad de combate: `uid`, `centro_local`, `masa`, `direccion`, `estado` (ACECHANDO…), `red`/`oz`, `distancia_gatillo`, `adn_capitan`, frentes entrada/salida.

### `MarketContext`

Foto de un "mar": symbol, market_type, last_price, spread, depth, volatilidad, jitter.

### `IntencionAccion`

Contrato hacia Greed: `prioridad`, `tipo` (CAZA, COSECHA, PODAR_MANTO, LIMPIAR_ESPEJOS, ATAQUE_OPORTUNISTA…), `masa`, `expira_en_ms`, `barco_ref`.

## Pentiverso / 5 mares (LTC)

Nombres en prototipo ShadowHarmy:

- `LTCUSDT_LINEAL` (perp USDT)
- `LTCUSDC_LINEAL`
- `LTCUSDT_SPOT`
- `LTCUSD_INVERSE` (o similar)
- Quinto frente según expansión

Greed compara USDT vs USDC para **regalos** (`UMBRAL_REGALO_SQUAD`).

## Iron vs Tusk (drift nombre)

| Manual antiguo | ShadowHarmy actual |
|----------------|------------------|
| Iron = acumulación / Arca USDT / gaps | **No hay módulo `iron.py`** — funciones repartidas en Tusk + config |
| Tusk = gaps dinámicos post-pérdida | `TuskBoveda` = tesoro + reservas + NAV |

En Fase B: decidir si Iron revive como módulo o queda absorbido por Tusk.

## Monarca (dos significados)

| Contexto | Significado |
|----------|-------------|
| Repo Monarca | Pipeline ingesta / Códice |
| Shadow Army | Operador o agente macro opcional |
| Código histórico | Módulo "Monarca" ciclo 10 latidos = 1% — ver versiones v1.x en manual |

## Capas del manual (Códice editorial)

- **Capa 1** — ideas descartadas
- **Capa 2** — lógica madura (promover a REGLA)
- **Capa 3** — visión futura / incubación

## Repo runtime

**Canónico:** `C:\Users\alans\Desktop\ShadowHarmy` (12 módulos Python, fase HIERRO v2.0).

Monarca repo = conocimiento + `migracion/`. No mezclar pipelines ingesta con fixes Beru.
