# 14 — Roadmap (código ShadowHarmy)

**Orden de trabajo.** Código canónico: `C:\Users\alans\Desktop\ShadowHarmy`

---

## M0 — Desbloquear arranque (**COMPLETADO** — 2026-07-03)

| # | Tarea | Archivo | Estado |
|---|-------|---------|--------|
| 1 | Indentar métodos dentro `BeruCazador` | `generales/beru.py` | ✅ |
| 2 | Implementar `limpiar_legion()` (purga COSECHADO/FUSIONADO) | `beru.py` | ✅ |
| 3 | Añadir `red_adan`, `oz_adan`, `max_favor` a `BeruShip` | `core/models.py` | ✅ |
| 4 | Handlers Greed: `REBALANCEO_IGRIS`, `ENGORDAR_MANTO` | `generales/greed.py` | ✅ |
| 5 | `requirements.txt` (pybit, websockets, streamlit) | raíz | ✅ |
| 6 | Verificar `python arise.py` arranca sin crash | — | ✅ (51s+) |

**Extras sesión 2026-07-03:** fusión dual, banda adaptativa, personalidad slippage, panel Streamlit.

**Criterio done:** `py_compile` OK + loop 60s sin excepción. **CUMPLIDO.**

---

## M1 — Ejecución testnet (P0 negocio)

| # | Tarea |
|---|-------|
| 1 | `bridge.place_order` + `cancel_order` wrapper |
| 2 | Confirmar fill (poll o private WS) antes de `confirmar_reserva` |
| 3 | Flag `MODO_SIMULACION` — si False, prohibir DISPARO_SIMULADO |
| 4 | Cablear CAZA/COSECHA a órdenes reales |
| 5 | Logging errores bridge (no `pass`) |

**Criterio done:** 1 ciclo CAZA→fill→COSECHA en testnet documentado en Bellion.

---

## M2 — Pentiverso real (P1)

| # | Tarea |
|---|-------|
| 1 | WS múltiple o REST para USDC, spot, inverse |
| 2 | Muros liquidez en `TankNode.muros` |
| 3 | Arbitraje USDT/USDC con precios reales |
| 4 | `ley_de_sucesion` en shutdown (signal handler) |

---

## M3 — Operaciones (P1)

| # | Tarea |
|---|-------|
| 1 | `enviar_telegram` + tabla evento→nivel (`06_NOTIFICACIONES.md`) |
| 2 | Safe mode / kill switch (manual Iron → Tusk) |
| 3 | Informe salud diario |

---

## M4 — Estrategia avanzada (P2 — manual como backlog)

| # | Tarea | Ref manual |
|---|-------|------------|
| 1 | Escalera desbalance | REGLA-R03 |
| 2 | Bellion Ratio_Eficiencia / latidos | SA gestión riesgo |
| 3 | Gap 2.5× post-pérdida | Códice v2.3 |
| 4 | Beru volatilidad 0.035 (si se decide) | REGLA-R01 alternativa |

---

## M5 — Visión (P3 — no bloquea v1)

Ver [`15_IDEAS_FUTURO.md`](15_IDEAS_FUTURO.md): Campo de Marte, Ragnarok, 120 frentes, fusión Monarcas.

---

## PR sugerido #1 (mínimo)

```
fix(beru): repair class structure + limpiar_legion + BeruShip fields
fix(greed): route IGRIS REBALANCEO and ENGORDAR_MANTO
chore: add requirements.txt
```

---

## Métricas de éxito v1

- [ ] Testnet: 24h sin crash
- [ ] 0 DISPARO_SIMULADO en prod path
- [ ] Telegram en errores API
- [ ] `migracion/11_MATRIZ` P0 ≥ 80% ✅
