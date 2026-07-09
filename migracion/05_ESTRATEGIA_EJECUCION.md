# 05 — Estrategia y ejecución

## Filosofía

1. **Plancton y ballenas** — micro-ineficiencias continuas; escalar densidad si hay "rastro de sangre" (volatilidad / liquidaciones).
2. **Tres personalidades** — protocolo de personalidades de trading (conservador / cazador / berserker) vía Capitanes.
3. **Pentiverso** — misma tesis LTC en 5 frentes; Greed elige mejor precio (`_escanear_mejor_precio`).
4. **Acordeón asimétrico** — Beru expande/contrae posiciones en grid dinámico.
5. **Arbitraje USDT/USDC** — regalos de desviación ≥ 0.3% (config).

---

## BeruShip — ciclo de vida

```
PLANTAR_SEMILLA → ACECHANDO → (gatillo) → ACTIVO → COSECHA / RELEVO
                      ↓
              evaluar_colisiones_y_fusion
```

**Campos críticos:** `centro_local`, `masa`, `distancia_gatillo` (default 0.005), `adn_capitan`, `frente_asignado`.

**Super Beru / generación / veterano** — flags para ships evolucionados.

---

## Tipos de `IntencionAccion`

> **Nota runtime:** el altar `PriorityQueue` de Greed **no está activo**. Beru/Igris manto van directo a Bridge. Tipos manto abajo = contrato legacy / futuro Beru.

| Tipo | General | Efecto |
|------|---------|--------|
| CAZA | BERU | Abrir / aumentar spot |
| COSECHA | BERU | Tomar ganancias multiverso |
| PODAR_MANTO | IGRIS (Bridge directo) | Reducir muelle saturado |
| LIMPIAR_ESPEJOS | IGRIS (Bridge directo) | Cerrar reflejos |
| ATAQUE_OPORTUNISTA | GREED | Arbitraje Kaiser / VIP |

Prioridad menor número = más urgente (PriorityQueue).

---

## Arbitraje y mercado

**Fuente:** `sandbox/arbitraje_mercado.md`, Códice Inquisidor/MILAGRO

- Comparar rendimiento histórico vs patrón visual (experimental).
- Volatilidad promedio en acumulación.
- Verificar botín > pérdida por spread.

**Producción mínima:** arbitraje USDT/USDC lineal LTC (ya en Greed radar).

---

## Estrategia por activo (Bellion)

- Bellion clasifica activos con datos Tusk (latidos/amputaciones).
- Activos eficientes → refuerzo; parásitos → poda o exclusión.
- Reportes Telegram horarios (manual).

---

## Grid y reponer niveles

Del manual / `1M.txt` (grid, reponer):

- Eventos "Reponiendo nivel…" → **solo consola** (no Telegram).
- Grid ajuste cada loop ~10 s — cuidado fatiga de notificaciones.

---

## Liquidaciones y "Surge" (DOCTRINA)

- Metáfora: liquidación ajena = nueva sombra / soldado.
- Implementación técnica **no cerrada** — candidato a detector Tank + trigger Beru.

---

## Versiones cristalizadas en chat (elegir una)

| Versión | Énfasis |
|---------|---------|
| v2.0.0ti | Cuatro extremidades del Cónclave |
| v2.3.0ti | Verdugo — sin reparación Iron |
| v2.4.0ti | Ojo del Oráculo — diagnóstico fallo |

**Decisión Fase B:** congelar **v2.3.0ti + ShadowHarmy v2.0** como base salvo tu voz.

---

## Modo Curación / Nutrientes (Beru post-mortem)

Tras trade exitoso en entorno dañado, Beru clasifica:

- **Nutriente A** — inercia pura
- **Nutriente B** — elasticidad
- **Nutriente C** — (tercer tipo en manual)

Actualiza "receta maestra" Iron — diseño avanzado.

---

## 120 frentes / multidivisa (VISIÓN)

Manual menciona expansión más allá de LTC — **Capa 3**. No bloquear v1 por esto; diseñar interfaces `MarketContext` extensibles.

---

## Orden sugerido implementación estrategia

1. Un solo frente LTCUSDT perp — CAZA/COSECHA real.
2. Segundo frente USDC — arbitraje.
3. BeruShip completo con Capitanes.
4. Acordeón + grid.
5. Expansión multidivisa.
