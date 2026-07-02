# Resumen ejecutivo — Migración Shadow Army

**Fase A + B completas** — 2026-06-30

## Código canónico

`C:\Users\alans\Desktop\ShadowHarmy` — **Lilit de Hierro v2.0**, fase HIERRO.

## Veredicto en una frase

**Buena arquitectura async multi-General; Beru roto; sin órdenes reales aún — M0 desbloquea, M1 testnet.**

## Qué leer según urgencia

| Urgencia | Documento |
|----------|-----------|
| Arreglar ya | [`14_ROADMAP.md`](14_ROADMAP.md) M0 |
| Entender gaps | [`13_ANALISIS_SHADOWHARMY.md`](13_ANALISIS_SHADOWHARMY.md) |
| Tabla ✅⚠️❌ | [`11_MATRIZ_FASE_B.md`](11_MATRIZ_FASE_B.md) |
| Ideas manual sin perder | [`15_IDEAS_FUTURO.md`](15_IDEAS_FUTURO.md) |
| Spec implementación | `00`–`07` |

## Bugs bloqueantes

1. `beru.py` — IndentationError línea 98
2. `limpiar_legion` — no existe
3. Sin `place_order` / fill
4. Greed sin ruta REBALANCEO/ENGORDAR

## Lo que ya funciona

Tusk reservas · Igris manto · Tank clima+capitanes · Greed altar+TTL · Bridge WS+wallet · Bellion log · Dashboard

## Manual vs código

El Analista aportó ~139 specs; el código **ya supera** al manual en acordeón/ADN Capitanes/delta Igris. Reglas 0.012/0.035 del Códice van a **futuro** (`15`), no se imponen sobre lo construido.

## Siguiente paso

**Agente nuevo:** [`16_CHECKLIST_MAESTRO.md`](16_CHECKLIST_MAESTRO.md) — empezar Fase 1, ítem 1.1.1.

~~PR #1 en ShadowHarmy~~ — ver checklist Fase 1 completa.

---

*Planos: `migracion/` · Código: `ShadowHarmy/` · Manual crudo: `manual_v2/` + `1M.txt`*
