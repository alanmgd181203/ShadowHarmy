# 13 — Análisis ShadowHarmy (código canónico)

**Fase B completada** — 2026-06-30  
**Repo:** `C:\Users\alans\Desktop\ShadowHarmy`  
**Principio:** el código manda; el manual alimenta ideas futuras (`15_IDEAS_FUTURO.md`).

---

## Inventario

```
ShadowHarmy/
  arise.py              # Orquestador asyncio.gather
  core/
    config.py           # .env, umbrales, identidad LILIT DE HIERRO v2.0
    bridge.py           # Bybit WS mainnet + HTTP wallet testnet
    bellion.py          # Log jsonl + estado
    dashboard.py        # Consola HUD
    models.py           # BeruShip, MarketContext, IntencionAccion
  generales/
    tusk.py             # NAV, reservas, pesos por frente
    tank.py             # 4 nodos, 5 mares, capitanes clima
    beru.py             # Legión, acordeón, fusión — ⚠️ NO COMPILA
    igris.py            # Manto, poda, espejos, delta
    greed.py            # Altar, caza/cosecha sim, escuadrón suicida
    capitanes.py        # ADN Ansiedad/Cazador/Berserker
```

**12 archivos Python.** Sin `requirements.txt`, sin `iron.py`, sin Telegram, sin tests.

---

## Lo que el código YA hace bien (mantener)

| Área | Evidencia |
|------|-----------|
| Orquestación async | `arise.py` — 8 hilos paralelos |
| Modelo intenciones | `IntencionAccion` + dedupe + TTL |
| Tusk reservas | solicitar / confirmar / liberar / cosecha atómica |
| Igris manto | Ley marcial 95%, limpieza 90%, delta 48–52%, expansión 80% |
| Tank clima | Ansiedad / Cazador / Berserker por inercia 30s |
| Capitanes ADN | vacio_adan, margen_apertura por fase HIERRO |
| Greed multiverso | `_escanear_mejor_precio` en 3 frentes |
| Arbitraje USDT/USDC | `_radar_escuadron_suicida` |
| Bridge real | WS mainnet LTCUSDT + wallet poll 30s |
| Bellion | historial jsonl + guardar_estado + ley_de_sucesion |
| Dashboard | telemetría Tank, altar, manto, legión |

---

## Bugs bloqueantes (P0 — antes de live)

### B-01 `beru.py` no compila

```
IndentationError: line 98
```

Métodos `plantar_semilla_adan`, `auditar_gatillos_adan`, `ejecutar_acordeon_asimetrico`, `evaluar_colisiones_y_fusion` están **fuera de la clase** `BeruCazador`. El hilo llama `self.plantar_semilla_adan` → no arranca.

### B-02 `limpiar_legion` no existe

Línea 43 `self.limpiar_legion()` — **AttributeError** si beru compilara.

### B-03 `BeruShip` vs atributos dinámicos

Código usa `red_adan`, `oz_adan`, `max_favor`; dataclass define `red`, `oz`. Funciona por atributos dinámicos pero **debe formalizarse** en `models.py`.

### B-04 Greed: Igris REBALANCEO / ENGORDAR sin handler

`igris._delegar_maniobra` emite `REBALANCEO_IGRIS`, `ENGORDAR_MANTO` → Greed cae en `else` → `_ejecutar_ataque_autonomo` (simulado incorrecto).

### B-05 Sin órdenes exchange

`CAZA`/`COSECHA` actualizan `tusk.pesos` en memoria — **no** `place_order`. Solo `DISPARO_SIMULADO` para GREED_SQUAD.

### B-06 Bridge: 1 de 5 mares con precio real

WS solo `LTCUSDT` lineal → todos los nodos reciben mismo precio; USDC/inverse/spot quedan en 0 → arbitraje y multiverso **parcialmente ciego**.

### B-07 Bridge traga errores NAV

`hilo_sincronizacion_nav` — `except: pass` silencioso.

---

## Divergencias código vs manual (código gana; manual → futuro)

| Tema | Manual / Códice | ShadowHarmy (verdad) | Acción |
|------|-------------------|----------------------|--------|
| Beru umbral 0.012 / vol 0.035 | REGLA-R01 Códice | **No implementado** — lógica es vacío Adán + acordeón 1.1/0.9 | Manual → idea alternativa; no forzar 0.012 sin decisión |
| Igris vol 0.04 / fuga 1.5% | Códice perfiles | **No implementado** — usa % margen Tusk | Futuro o absorber en Igris |
| Gap Tusk 2.5× | Códice v2.3 | **No en tusk.py** | Futuro |
| Iron módulo | Manual | **Absorbido en Tusk** + Greed "Hierro" | D-10 cerrada: sin iron.py |
| Capitanes 2 opciones a Beru | Manual Tank→Cap→Beru | **ADN inyectado en semilla**; no `procesar_señal_tank` | Código más elegante; manual es variante |
| Margen 85% | Sandbox protocolo | **80/90/95%** en config Igris | Código gana |
| Escalera desbalance | Códice | **Ausente** | Futuro P2 |
| Telegram | Manual limpio | **Ausente** | P1 |
| Bellion clasificación activos | Manual | **Solo log**; no Ratio_Eficiencia | P2 |

---

## Flujo real implementado (vs diagrama migración)

```
Bridge(WS) → Tank.nodos → Tusk.ultimo_precio
                ↓
         capitan_activo (ADN)
                ↓
Beru.hilo [ROTO] → IntencionAccion → Greed.altar
                ↓
         confirmar_reserva → tusk.pesos (sim)
Igris.vigilar → PODAR/LIMPIAR/REBALANCEO*/ENGORDAR* → Greed
```

---

## Config actual (`core/config.py`)

| Variable | Valor |
|----------|-------|
| SISTEMA_NOMBRE | LILIT DE HIERRO V2.0.0 |
| FASE_ACTUAL | HIERRO |
| RANGO_EXPANSION_MIN | 80.0 |
| RANGO_LIMPIEZA_MAX | 90.0 |
| MURO_LEY_MARCIAL | 95.0 |
| UMBRAL_COSECHA_MIN | 0.01 |
| UMBRAL_REGALO_SQUAD | 0.003 |
| TTL_ORDEN_MS | 2000 |
| UMBRAL_VERDE_MS | 400 |
| UMBRAL_AMARILLO_MS | 800 |
| TOLERANCIA_GLITCH | 0.002 |
| TOLERANCIA_COMA_S | 15.0 |

---

## Evaluación global

| Dimensión | Nota | Comentario |
|-----------|------|------------|
| Arquitectura | 8/10 | Bien pensada; alineada con manual en espíritu |
| Completitud ejecución | 3/10 | Sim memoria; sin fills |
| Calidad código | 4/10 | beru roto; handlers faltantes |
| Alineación manual | 6/10 | Mucho manual es otra era (Homunculus, 0.012…) |
| Listo testnet live | **No** | Tras B-01…B-05 |

---

## Próximo documento

- Roadmap ordenado: [`14_ROADMAP.md`](14_ROADMAP.md)
- Ideas manual no descartadas: [`15_IDEAS_FUTURO.md`](15_IDEAS_FUTURO.md)
- Matriz detallada: [`11_MATRIZ_FASE_B.md`](11_MATRIZ_FASE_B.md)
