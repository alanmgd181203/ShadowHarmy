# 15 — Ideas a futuro (manual → backlog)

**No descartadas.** El código ShadowHarmy manda hoy; estas ideas del Analista/manual siguen válidas para versiones posteriores.

---

## Doctrina / visión

| Idea | Fuente | Por qué no v1 |
|------|--------|---------------|
| Fusión dual / Ragnarok (todos los generales uno) | sandbox shadow_army | Complejidad; Beru ya tiene SUPER_FUSION parcial |
| Coro de Sombras / walkie-talkies permanentes | sandbox | Event bus futuro; hoy Bellion jsonl |
| Eco del Trono (autonomía sin Monarca) | sandbox | Parcial — loops ya autónomos |
| Surge en liquidaciones | 1M.txt / doctrina | Requiere feed liquidaciones Bybit |
| Fusión con otro Monarca/Gobernador | sandbox | Fuera scope Lilit |
| 120 frentes multidivisa | sandbox visión | Tras Pentiverso LTC estable |
| Campo de Marte / DarkSeed entrenamiento | Códice + sandbox | Paquete `training/` separado |
| LegionSombras / MareaSombras clases | sandbox | Nombres distintos a arise+generales |

---

## Reglas manual no en código (evaluar después M1)

| Idea | Spec manual | Notas |
|------|-------------|-------|
| Beru umbral 0.012 + vol 0.035 | Códice v2.3 | Código usa vacío Adán + acordeón — **más sofisticado**; no revertir sin A/B |
| Igris cierre vol>0.04 fuga>1.5% | Códice 02 | Complementa manto %; buen M4 |
| Gap Tusk 2.5× tras pérdida | Códice 03 | Falta en tusk.py |
| Escalera salida desbalance 1% | Códice 01 | P2 gestión posición |
| Sin reparación Iron | Códice | **Ya alineado** en espíritu (cortes Beru) |
| Guerra infinita / Velo Carnicero | sandbox riesgo | Sim vs real — flag entrenamiento |
| Prohibido disparar sin fill | REGLA-R07 | **P0 M1** — implementar, no idea |

---

## Infra / ops futuro

| Idea | Fuente |
|------|--------|
| Indicador de slippage real por frente (reemplazar `SLIPPAGE_FACTOR` manual) | Monarca sesión 2026-07-03 |
| Reporte automático órdenes/hora | infraestructura_api |
| Simulador infierno / Maestro del Dolor | 01_capas, logica_tecnica |
| Ojo del Oráculo v2.4 diagnóstico | 04_logica_tecnica |
| Inquisidor / patrón MILAGRO | 03_arbitraje |
| WhatsApp (descartado vs Telegram) | notificaciones — Telegram gana |

---

## Mejoras que el código sugiere (mejor que manual)

| Idea código | Ventaja sobre manual genérico |
|-------------|-------------------------------|
| ADN Capitanes por clima Tank | Parametriza vacío Adán sin LLM |
| Acordeón 1.1/0.9 + engorde 0.1% | Más concreto que "grid" abstracto |
| Delta adaptativo + personalidad slippage por frente | Banda viva según margen + riesgo moneda |
| Bizantino 4 nodos Tank | Tolerancia glitch 0.2% |
| Cosecha con UMBRAL_COSECHA_MIN | Evita salidas prematuras |

**Retroalimentación al manual:** promover estos bloques a Códice cuando cierre M1 (P0.4 selectivo).

---

## Cómo usar este archivo

1. Antes de implementar algo del manual, buscar aquí si ya hay equivalente en código.
2. Al cerrar milestone, mover ítem a `08_DECISIONES` (cerrada o descartada explícitamente).
3. No borrar ideas — marcar "implementada en Mx" cuando aplique.
