# 00 — Norte (Shadow Army)

## Qué es

**Shadow Army** (operacionalmente: *Lilit de Hierro*, fase HIERRO v2.x) es un sistema de trading automatizado multi-agente inspirado en *Solo Leveling*: un **Monarca** (operador humano) comanda **Generales** (módulos Python async) que operan en mercados Bybit — hoy centrados en **LTC** y el **Pentiverso** (5 mares / pares relacionados).

No es un bot monolítico: es una **legión** con tesorería (Tusk), visión de mercado (Tank), caza (Beru), escudo de margen (Igris), ejecutor (Greed) y auditoría (Bellion).

## Qué NO es (v1 / esta migración)

- **No** es el pipeline Monarca de ingesta (`panel_sombras.py`, Fase 1–3) — eso es la fábrica de manuales.
- **No** es Homunculus/Lilit legacy en `archive/legacy_bots/` — referencia histórica solamente.
- **No** incluye fusión con otros "Monarcas/Gobernadores" como runtime — es **doctrina** (SA-IDs en catálogo), no código cerrado.
- **No** asume órdenes reales live hasta que Fase B cierre el gap `place_order` / fills confirmados.

## Meta operativa

1. **Nunca descansar** — loops async permanentes; adaptación continua.
2. **Supervivencia > maximización** — cortes rápidos (Beru), margen bajo control (Igris), sin "reparación" de posiciones muertas (Códice v2.3.0ti).
3. **Ineficiencias como presa** — arbitraje USDT/USDC, micro-movimientos (plancton), escalado si hay "rastro de sangre" (liquidaciones / volatilidad).
4. **Trazabilidad** — Bellion registra; Tusk persiste estado; Telegram solo para lo crítico.
5. **Vocabulario Monarca** — Beru, Igris, Arca, Generales (criterio editorial P0.1).

## Arquetipo narrativo (DOCTRINA — guía, no spec técnica)

- **Monarca** = tú + visión macro; el ejército debe operar con autonomía si te retiras.
- **Surge** = capitalizar liquidaciones ajenas (metáfora de reanimar sombras).
- **Soldados de rango**: Igris (élite futuros/exóticos), Iron/Tank (fuerza bruta), soldados raso (carroñeros / grid pequeña).
- **Comunicación** = "walkie-talkies" (Coro de Sombras); **fusión** de generales en crisis (Ragnarok) — diseño aspiracional.

## Activo y mercado foco (estado destilado)

| Dimensión | Valor predominante en manual + prototipo |
|-----------|------------------------------------------|
| Exchange | Bybit |
| Par ancla | LTC (USDT lineal, USDC lineal, spot, inverse — "5 mares") |
| Modo bridge | Mainnet ojos (WS público) + testnet manos (balance) en prototipo |
| Capital | NAV real → Tusk → masa autorizada → reservas por BeruShip |

## Éxito de la Fase B (cuando contrastes código)

- Cada **REGLA** en `03_RIESGO_Y_REGLAS.md` tiene fila en `11_MATRIZ_FASE_B.md` con estado IMPLEMENTADO | PARCIAL | AUSENTE.
- Un solo repo canónico declarado.
- Milestone P0 definido (típicamente: bridge + orden mínima + Igris margen + Bellion + Telegram crítico).

## Frase guía para sesiones Cursor

> Lee `migracion/00_NORTE.md` y el módulo del General que toques. No re-arquitectes sin actualizar `08_DECISIONES_PENDIENTES.md`.
