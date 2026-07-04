# 04 — Infraestructura y API

## Exchange: Bybit

### Capacidades requeridas (estado destilado)

| Capacidad | Prioridad | Notas |
|-----------|-----------|-------|
| WebSocket tickers públicos | P0 | LTC perp/spot |
| REST wallet balance | P0 | NAV → Tusk |
| REST place order | P0 | **Ausente en prototipo** |
| REST cancel / amend | P1 | Grid / acordeón |
| Private WS fills | P1 | REGLA-R07 |
| Testnet vs mainnet | P0 | Híbrido "ojos mainnet, manos testnet" en prototipo |

### Bridge (`BybitBridge`)

**Ojos (Mainnet — precios reales siempre):**
- `conectar()` — WS loop con reconexión automática.
- `_procesar_latido` — actualizar Tank con last price + latencia.

**Manos (Testnet por defecto — órdenes):**
- `place_order(symbol, side, qty, order_type, price, link_id)` — envía orden con `orderLinkId` idempotente.
- `cancel_order(symbol, order_id, link_id)` — cancela por ID o linkId.
- `amend_order(symbol, order_id, link_id, new_qty, new_price)` — modifica precio/cantidad.
- `esperar_fill(symbol, order_id, link_id, timeout_s)` — polling hasta fill confirmado (REGLA-R07).

**Balance:**
- `hilo_sincronizacion_nav` — poll balance + margen → `tusk.actualizar_nav_real`. Backoff exponencial en error + log Bellion.

**Clase `OrdenResultado`:** respuesta estandarizada con `exito`, `order_id`, `link_id`, `mensaje`, `datos`.

**Arquitectura híbrida:**
```
MAINNET ──precio WS──→ Tank (ojos)
TESTNET ←──órdenes REST── Greed (manos)
        ──fill poll──→ Tusk confirma reserva
```

Cuando `config.TESTNET=False`, las manos apuntan a mainnet (solo con validación completa Fase 6).

### Configuración

```env
BYBIT_API_KEY=
BYBIT_API_SECRET=
MODO_TESTNET=True
```

Cargador: `core/config.py` → `.env` en raíz del proyecto runtime.

---

## Persistencia

| Artefacto | Contenido | Frecuencia |
|-----------|-----------|------------|
| `data/tusk_data.json` | reservas, ciclos, serialización BeruShip | ~10 s |
| Bellion log | eventos por General | continuo |
| Estado dashboard | solo consola | 1 Hz |

**Futuro:** SQLite o JSON rotado para Informe de Guerra.

---

## Async y concurrencia

- Un proceso: `asyncio.run(arise())`.
- Locks en Tusk (`asyncio.Lock`) para NAV y reservas.
- `Greed.altar` = `asyncio.PriorityQueue`.
- Tank semáforo compartido con Greed antes de disparar.

---

## Infraestructura API (manual sandbox)

Temas recurrentes en `infraestructura_api.md`:

- Reportes automáticos por hora (órdenes activadas).
- Rate limits Bybit — backoff en bridge.
- Health del loop cada 10 s (consola, no Telegram).
- Safe Mode / interruptor emergencia **antes** de conectar live (Iron doctrina).

---

## Simuladores (no producción)

| Script | Uso |
|--------|-----|
| `simulador_infierno.py` | Stress Pandas |
| `DarkSeed_Core.py` | Entrenamiento caos (mención Códice) |
| Campo de Marte | Ruido browniano + masa artificial |

Separar paquete `training/` del runtime live.

---

## Dependencias Python (runtime esperado)

Mínimo destilado:

- `asyncio` (stdlib)
- `pybit` o SDK Bybit vigente
- `websockets`
- `python-dotenv` o cargador propio

Monarca `requirements.txt` **no** incluye trading deps — el repo del ejército lleva su propio `requirements.txt`.

---

## Seguridad

- API keys solo lectura+trade; sin withdraw.
- IP whitelist en Bybit recomendado.
- Telegram bot token en `.env` separado.

---

## Checklist P0 infra (Fase B)

- [x] `place_order` con idempotencia (`orderLinkId` único por despacho)
- [x] Confirmación fill antes de actualizar Tusk.pesos (`esperar_fill` polling)
- [x] Reconexión WS con jitter (ojos) + backoff exponencial (NAV)
- [x] `cancel_order` / `amend_order` wrappers
- [ ] Modo dry-run flag global (ver 2.2.1 — `MODO_SIMULACION`)
- [x] Logs sin secretos (Bellion registra acciones, no keys)
