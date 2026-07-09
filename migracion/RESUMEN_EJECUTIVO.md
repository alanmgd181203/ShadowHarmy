# Resumen ejecutivo — Migración Shadow Army

**Actualizado:** 2026-07-05 (Greed basis/multicruce, Beru Proto, Igris §E v1)

## Código canónico

`C:\Users\alans\Desktop\ShadowHarmy` — **Lilit de Hierro v2.0**, fase HIERRO.

## Veredicto en una frase

**Fases 0–2 cerradas · Fase 3 ~92%.** Pentiverso dual, Tank omnimercado (matriz + Kaiser + Ancla), **Greed consume Kaiser** (sizing, VIP, multicruce, basis hold), **Beru Proto** (capital + rail stable), **Igris §E v1** (bootstrap inverse L + lineal S, promedios). **Siguiente: Fase 4 M3** (Telegram, safe mode) o cerrar **3.5.8** (Ancla en maniobras Igris).

## Progreso checklist (16)

| Horizonte | % |
|-----------|---|
| **Global (Fases 0–10)** | **~64%** (100/160 + 3 parciales) |
| **Núcleo operativo (0–3)** | **~95%** (98/103) |
| **Fase 4 ops Monarca** | **~9%** (stubs listos) |

## Qué leer según urgencia

| Urgencia | Documento |
|----------|-----------|
| Arrancar testnet | [`18_ARRANQUE_TESTNET.md`](18_ARRANQUE_TESTNET.md) |
| Siguiente paso ops | [`16_CHECKLIST_MAESTRO.md`](16_CHECKLIST_MAESTRO.md) Fase 4 |
| Doctrina Greed/Kaiser | [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md) |
| Doctrina Beru | [`22_DOCTRINA_BERU.md`](22_DOCTRINA_BERU.md) |
| Doctrina Igris | [`21_DOCTRINA_IGRIS.md`](21_DOCTRINA_IGRIS.md) |
| **Plan crecimiento (capital)** | [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md) |
| Sentidos Tank / backlog | [`19_BACKLOG_SENTIDOS.md`](19_BACKLOG_SENTIDOS.md) |
| Checklist detallado | [`16_CHECKLIST_MAESTRO.md`](16_CHECKLIST_MAESTRO.md) |
| Roadmap | [`14_ROADMAP.md`](14_ROADMAP.md) |
| Tabla ✅⚠️❌ | [`11_MATRIZ_FASE_B.md`](11_MATRIZ_FASE_B.md) |

## Validación rápida

```powershell
python scripts/validar_checklist.py
python scripts/validar_m2.py
python scripts/probar_ciclo_beru.py
python scripts/validar_panorama_tank.py --segundos 35
python scripts/validar_greed_sizing_smoke.py
python scripts/validar_greed_multicruce_smoke.py
python scripts/validar_greed_basis_smoke.py
python scripts/validar_igris_smoke.py
python scripts/validar_beru_capital_smoke.py
python scripts/validar_beru_rail_smoke.py
python scripts/validar_plan_crecimiento_smoke.py
```

Reportes: `data/validacion_checklist.json`, `data/validacion_panorama_tank.json`

## Lo que ya funciona

- **M0–M1:** arranque, Bridge testnet, fill, simulación, trade BTC documentado
- **M2:** 10 mares WS, muros, persistencia, panel dual
- **M2.7 Sentidos Tank:** catálogo spot/perp; matriz; desvío índice; panorama Binance; Bellion + panel
- **M2.8 Kaiser:** vocero + perfiles + metaverso + Ancla + pipeline → cola Greed
- **M2.9 Greed omnimercado v1:** Kaiser sizing 1%, VIP/Mega VIP, multicruce 3–4p, basis hold, `manto_touch`
- **M2.10 Beru Proto:** tiers oz/red, capital, rail stable (USDT/USDC/USDE/USD1)
- **M2.11 Igris §E v1:** bootstrap inverse L + lineal S; `precio_medio` por pierna
- **Plan crecimiento v1:** [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md) + `core/plan_crecimiento.py` (checkpoint 2026-07-06)
- **Gates:** `core/validacion.py` + avisos en `arise.py`

## Limitaciones conocidas (2026-07-05)

- **Geo USA:** Binance WS → 451; REST Bybit spread/alpha/convert → 403. Fase 1 Bybit WS sí funciona.
- **Greed omnimercado:** grafo completo ~598 spot + rutas mixtas 3+ piernas spot+perp — pendiente.
- **Igris §E:** Ancla antes engorde/rebalanceo y sesgo long — pendiente (3.5.8).
- **Estrategia:** semáforos matriz, lag Convert, semáforo spot aliado → backlog `19`, no bloquea Fase 4.

## Pendiente (no bloquea escalar Fase 4–5)

- Telegram envío real (stub listo)
- SAFE_MODE cancel órdenes (bloqueo CAZA listo)
- Ciclo **live** testnet con `MODO_SIMULACION=False` (cuando Monarca decida)
- Reglas Códice avanzadas → Fase 5 backlog
- Mainnet → Fase 6

## Manual vs código

El código **supera** al manual en acordeón/ADN/delta Igris, pentiverso dual, **Kaiser→Greed con Ancla**, Beru capital/rail y basis hold. Reglas 0.012/0.035 → Fase 5 / `15_IDEAS_FUTURO.md`.

---

*Planos: `migracion/` · Código: `ShadowHarmy/`
