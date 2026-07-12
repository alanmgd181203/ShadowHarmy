# Resumen ejecutivo — Migración Shadow Army

**Actualizado:** 2026-07-12 (Beru doctrina 3.9 · Igris §E v2 · panel Pergamino · cuartel México)

## Código canónico

`C:\Users\alans\Desktop\ShadowHarmy` — **Lilit de Hierro v2.0**, fase HIERRO.  
Remoto: https://github.com/alanmgd181203/ShadowHarmy (público; colaboradora Jessica-Reyes06).

## Veredicto en una frase

**Fases 0–2 cerradas · Fase 3 ~91%.** El ejército ya caza en doctrina Beru nueva (residual, frontera, Mega reset, fricción) e Igris despliega el manto con Ancla y paciencia Ask/Bid. **Falta sangre live** en testnet y el sesgo long. **Siguiente:** 3.9.9/3.10.7 live · o Fase 4 (Telegram / safe mode).

## Progreso checklist (16)

| Horizonte | % |
|-----------|---|
| **Global (Fases 0–10)** | **~66%** (117/179 + 3 parciales) |
| **Núcleo operativo (0–3)** | **~94%** (115/122) |
| **Fase 4 ops Monarca** | **~9%** (stubs listos) |

## Qué leer según urgencia

| Urgencia | Documento |
|----------|-----------|
| **Cómo hablar (agente)** | [`17_GUIA_MONARCA.md`](17_GUIA_MONARCA.md) — **siempre primero** |
| Arrancar testnet | [`18_ARRANQUE_TESTNET.md`](18_ARRANQUE_TESTNET.md) |
| Siguiente paso | [`16_CHECKLIST_MAESTRO.md`](16_CHECKLIST_MAESTRO.md) — 3.9.9 / 3.10.7 / 4.1 |
| Doctrina Beru (cirugía) | [`22_DOCTRINA_BERU.md`](22_DOCTRINA_BERU.md) |
| Doctrina Igris (§E v2) | [`21_DOCTRINA_IGRIS.md`](21_DOCTRINA_IGRIS.md) |
| Doctrina Greed/Kaiser | [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md) |
| Plan crecimiento | [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md) |
| Sentidos Tank | [`19_BACKLOG_SENTIDOS.md`](19_BACKLOG_SENTIDOS.md) |
| Roadmap | [`14_ROADMAP.md`](14_ROADMAP.md) |
| Tabla ✅⚠️❌ | [`11_MATRIZ_FASE_B.md`](11_MATRIZ_FASE_B.md) |

## Validación rápida

```powershell
python scripts/validar_checklist.py
python scripts/validar_ciclo_beru_eth.py
python scripts/validar_beru_cazador_smoke.py
python scripts/validar_beru_fusion_smoke.py
python scripts/validar_beru_mega_reset_smoke.py
python scripts/validar_beru_capital_smoke.py
python scripts/validar_igris_smoke.py
python scripts/validar_m2.py
```

Reportes: `data/validacion_checklist.json`, `data/validacion_ciclo_beru_eth.json`

## Lo que ya funciona

- **M0–M1:** arranque, Bridge testnet, fill, simulación, trade BTC documentado
- **M2:** 10 mares WS, muros, persistencia, panel dual
- **Tank/Kaiser/Greed:** sentidos, Ancla, pipeline, sizing, VIP, multicruce, basis
- **Beru Proto + cirugía 3.9:** residual, frontera, colisión oz, Mega reset, capital fricción, flota Inverse∩Linear
- **Igris §E v2 (3.10):** bootstrap + promedios + `igris_despliegue` (Ask/Bid, mordida, reloj invertido) + jurisdicción manto
- **Panel Pergamino:** `dashboard_sombras.html` (cuartel México)
- **Plan crecimiento v1:** [`23`](23_PLAN_CRECIMIENTO.md)
- **Cuartel:** GitHub público + colaboradora México

## Limitaciones conocidas (2026-07-12)

- **Live testnet** Beru/Igris §E aún no sellado con `MODO_SIMULACION=False` (3.9.9 / 3.10.7).
- **Sesgo long** Igris (banda asimétrica) — 3.5.8c pendiente.
- **Geo USA:** Binance WS 451; REST Bybit spread/alpha/convert 403. Fase 1 Bybit OK.
- **Greed omnimercado:** grafo completo ~598 spot + rutas mixtas 3+ piernas — pendiente.
- **Estrategia sentidos:** semáforos matriz → `19`, no bloquea Fase 4.
- **`.env` testnet en repo público** — no subir keys mainnet.

## Pendiente inmediato (elige el Monarca)

1. **Campo de entrenamiento live** — un ciclo Beru + un despliegue Igris con sangre testnet  
2. **Sesgo long** del manto (3.5.8c)  
3. **Telegram / safe mode** (Fase 4) — vivir con el bot sin mirar la consola  

## Manual vs código

El código **supera** al manual en acordeón/ADN, pentiverso, Kaiser→Greed, Beru residual/fricción e Igris despliegue §E. Reglas 0.012/0.035 → Fase 5 / `15_IDEAS_FUTURO.md`.

---

*Planos: `migracion/` · Código: `ShadowHarmy/` · Tono: `17_GUIA_MONARCA.md`*
