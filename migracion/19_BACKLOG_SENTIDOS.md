# 19 — Backlog sentidos Tank (post spot completo)



**Checkpoint:** checklist **3.7 + 3.8 Kaiser v0** (2026-07-05).  

**Estado:** ojos spot ~598 + linear perp ~677 + inverse perp ~21 + futuros dated (cache variable). **Estrategia después.**  

**Validar:** `python scripts/validar_panorama_tank.py --segundos 35` → `data/validacion_panorama_tank.json`



---



## Hecho en 3.7 (cerrado)



| Ítem | Módulo | Notas |

|------|--------|-------|

| Matriz spreads WS | `core/spreads.py` | lineal↔inverso, spot↔perp, basis, USDT↔USDC |

| Funding + indexPrice | `bridge.py` → Tank | ticker derivados |

| Fase 1 desvío índice | `calcular_desvios_indice` | perp vs indexPrice Bybit |

| Fase 2 panorama Binance | `binance_ref.py` + `calcular_panorama_global` | huérfanas; geo USA bloquea WS |

| Bases huérfanas | `trinidad.py` | ~313 en cache local |

| REST spread/alpha/convert/quotes | `sentidos_extra.py` | 403 USA en REST |

| Panel + Bellion | `panel.py`, `bellion.py` | `desvios_indice`, `panorama_global` |

| Kaiser vocero | `generales/kaiser.py` | digest `estado_vivo.kaiser` |
| **Ancla liquidez** | `core/ancla.py` | orderbook walk, max/segura USD, alertas `OPORTUNIDAD_LIQUIDEZ` |



---



## Bridge / infra (cuellos de botella)



- [ ] **Medir lag real** con ~10 shards WS (4 spot + 5 linear + 1 inverse) en `arise.py` 30+ min.

- [ ] **Ajustar `SPOT_WS_SHARD_SIZE`** (150 hoy) según límites Bybit y CPU local.

- [ ] **Binance depth** para pierna huérfana en Ancla (hoy solo bookTicker)

- [ ] **Reconexión parcial:** si cae un shard, no reiniciar los demás.

- [ ] **Límite Bybit:** documentar tope de topics por conexión spot v5.



## Tank / memoria



- [ ] **Lazy frentes:** no prealloc 640 frentes × 4 nodos al arranque; dict bajo demanda (parcialmente hecho con `asegurar_frente`).

- [ ] **Tier de prioridad:** núcleo (trinidad) vs cola spot para alertas Bellion.

- [ ] **Snapshot liviano:** `spot_all` en panel sin serializar 640 detalles cada tick.



- [x] **Smoke Igris** — `scripts/validar_igris_smoke.py`
- [x] **Doctrina esqueleto** — `21_DOCTRINA_IGRIS.md`



- [ ] **Semáforo aliado spot / huérfano / global:** verde/amarillo/rojo para **Greed** (lineal+spot o desvío vs Bybit). No es de Igris. *(checklist 3.7.P3 · pausa mainnet)*

- [ ] **FRENTES_MANTO_ALL** expandir desde `LINEAR_PERP` + `INVERSE_PERP` filtrados, no solo LTC/BTC.



## Sentidos extra — estrategia pendiente



- [x] **Matriz spreads** — calculada desde WS.

- [x] **Funding + indexPrice** — inyectados desde ticker WS derivados.

- [x] **Spread producto Bybit** — REST poll (código listo).

- [x] **Alpha** — REST poll (código listo).

- [x] **Convert** — REST catálogo (código listo).

- [x] **Convert quotes (catálogo)** — REST poll muestra.

- [x] **Fase 1 — Desvío perp vs indexPrice** — panel/Bellion.

- [x] **Fase 2 — Binance spot ref** — WS + panorama global.

- [ ] **3.8.P1** ~~Greed/Beru/Igris consumen Kaiser~~ — **Greed ✅** (`consumir_greed` + **multicruce spot**); Beru/Igris fuera por doctrina

- [x] **Semáforos** sobre matriz spreads — luces V/A/R en digest Kaiser. *(3.7.P1 ✅ 2026-07-20)*



- [ ] **Flag `marginTrading`** en cache → filtro manos al ejecutar spot margin.

- [ ] **Modo inventario** vs **modo préstamo** (spot normal vs `isLeverage`).

- [ ] **Jerarquía:** manto → guerrilleros (EUR/MNT/BTC quote) → soldados stables.

- [ ] **Cruce ventanas:** LTC/USDT vs LTC/EUR × USDT/EUR (doctrina manual).



## Limpieza código (cuando estabilice)



- [ ] Unificar rails USDC/MNT/EUR sueltos como **vistas** sobre `SPOT_ALL_PARES`, no listas duplicadas en Bridge.

- [ ] Validación: subir umbral spot de 75% → 90% cuando shards estables.



---



*Actualizar al cerrar ítems. No bloquea fase 4 (Telegram, safe mode).*

