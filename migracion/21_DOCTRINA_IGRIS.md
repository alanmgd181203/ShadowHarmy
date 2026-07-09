# 21 — Doctrina Igris (escudo del manto)

**Estado:** §A + §C (parcial) + §E (v1 bootstrap/promedio) — Ancla Igris pendiente  
**Código:** `generales/igris.py`, `core/igris_estado.py`, `core/manto_touch.py`, `core/mercado.py`

---

## Rol

**Igris** = dueño del **manto** (derivados L/S). Ejecuta **directo en Bridge**.  
**Greed** = arbitraje Kaiser. No administra el manto; si toca un frente del manto, `core/manto_touch.py` marca cooldown para que Igris no rebalancee en falso.

**Beru** = casa spot — fuera de oleada Kaiser→Greed.

---

## §A — Umbrales margen — CERRADO

| Margen usado | Fase | Igris | Greed |
|--------------|------|-------|-------|
| **< 80%** | EXPANSION | Engorde / bootstrap | Caza |
| **80–85%** | TERRENO_CAZA | Solo rebalanceo | Caza → piso 85% |
| **85–90%** | IDEAL | Solo rebalanceo | Caza — zona objetivo |
| **90–93%** | ALTA_PRESION | Solo rebalanceo | Caza — único inflado activo |
| **93–95%** | PRE_PODA | Espejos si L+S | Caza |
| **≥ 95%** | LEY_MARCIAL | Poda ~15% | **Solo VIP/Mega VIP** |

```
RANGO_EXPANSION_MIN=80  RANGO_PISO_IDEAL=85  RANGO_OBJETIVO_MARGEN=90
RANGO_LIMPIEZA_MAX=93   MURO_LEY_MARCIAL=95
```

---

## §C — Igris vs Greed — PARCIAL

| Decisión | Estado |
|----------|--------|
| ≥95%: Greed parado salvo **VIP/Mega VIP** (regalitos) | ✅ `filtrar_planes_ley_marcial` |
| Greed toca manto → Igris no rebalancea ~45s | ✅ `manto_touch` |
| Igris veta Greed desde margen > X | Pendiente |
| Mega VIP requiere OK Igris | Pendiente |
| SAFE_MODE: Igris sin engorde, sí poda | Pendiente |

---

## §E — Armado del manto — PARCIAL (v1)

### Piernas
- **LONG** = inversos (USD) + futuros dated (rotación al vencer o si hay mejora).
- **SHORT** = lineales stable (USDT/USDC).
- Un activo (ej. SOL) puede tener **varias piernas** que se turnan con oportunidades Kaiser.

### Implementado v1
| Ítem | Estado |
|------|--------|
| Bootstrap inverse L + lineal S | ✅ `igris_manto.frentes_bootstrap` + `_bootstrap_manto` |
| `precio_medio` por pierna en `pesos` | ✅ `igris_manto.actualizar_promedio` vía Tusk fill |
| Panel promedios | ✅ `igris.promedios_pierna` en `estado_vivo.json` |

### Pendiente
| Ítem | Estado |
|------|--------|
| Ancla en maniobras Igris | Pendiente |
| Banda delta asimétrica (sesgo long) | Pendiente |
| Semáforos morado/gris (bloque B) | Pendiente |
| Sangrado útil / margen económico | Pendiente |

### En ~90% (zona ideal)
Igris **pulir entradas/salidas** con rigor tipo Greed (mínimo orden, Ancla, neto ≥ fees) pero **más tolerancia** y horizonte largo.

### Contabilidad
- Equilibrio por **promedio de entrada**, no tick instantáneo.
- **Margen económico** vs % exchange — no desinflar por falso >100%.
- Sangrado útil: si slippage mejora promedio, **aprovechar**, no podar.

### Sesgo long
- Neutralidad meta ~50/50; si hay carga, **preferir LONG** (inversos).
- SHORT pesado → mejorar entrada/salida del short, no panic-rebalance.

### Semáforos (bloque B — diseño)
| Color | Significado |
|-------|-------------|
| V/A/R spot | Salud spot aliado del perp |
| **Morado** | Oportunidad mejora entrada/salida en frente con manto → Igris revisa |
| **Gris/slippage** | Paridad rota temporal — falsa alarma, esperar |

### Deuda Greed ↔ Igris (limpieza hecha / por hacer)

| Ítem | Estado |
|------|--------|
| Handlers manto en Greed | ✅ eliminados — solo Igris→Bridge |
| Docs “Greed poda espejos” | ✅ corregidos |
| `IntencionAccion` manto | Legacy Beru — no cola activa |
| Ancla en maniobras Igris | Pendiente |
| `pesos` + precio medio por pierna | ✅ v1 `igris_manto.py` |
| Bootstrap inverse L + lineal S | ✅ v1 |
| Banda delta asimétrica (sesgo long) | Pendiente |

---

## Otros bloques

| Bloque | Tema |
|--------|------|
| **B** | Semáforos spot + morado + slippage paridad |
| **D** | Funding → maniobra vs aviso; Ancla antes engorde |
| **F** | Vol 0.04 / fuga 1.5%; escalera R03 |

---

## Validación

- `python scripts/validar_igris_smoke.py`
- `python scripts/validar_greed_manto_smoke.py`
- Live manto testnet (3.5.1)
