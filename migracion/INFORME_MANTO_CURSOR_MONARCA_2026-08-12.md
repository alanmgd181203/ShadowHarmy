# Informe Manto (Igris) — Cursor del Monarca

**Fecha:** 2026-08-12 · Checklist **4.0.3** (en curso)

## Qué es el manto

El **manto** son las piernas **long + short** de futuros que Igris planta y engorda en los Santos del pase. Es el “escudo” dual: no es spot de Beru ni caza fina de Greed.

**Igris** = plantar y engordar hasta la meta del paso (peaje aceptado, marcha **Asalto**).  
**Greed** = edge / arbitraje fino — **después**, no ahora.  
**Beru** = spot — solo cuando el manto ya sirva (4.0.4).

## Qué hace Igris en la práctica

1. Mira libros/precios (Tank + Bridge).  
2. Reserva oxígeno en Tusk.  
3. Dispara **dual** L+S (o bootstrap) en Santos del lote.  
4. Engorda hasta `meta_engorde` del paso en foco (100 % del acum del Santo).  
5. Si `restante ≤ 0` en ese Santo, deja de engordar ahí.

Ley Asalto: no exigir spread “bonito”; peaje OK; ritmo entre mordidas; no ametrallar el libro.

## Simulación vs mainnet

| | Sim **4.0.2** | Live **4.0.3** |
|--|---------------|----------------|
| Ritual | `arise_igris_sim.py` | `arise_igris.py` (+ guardián) |
| Órdenes | Ilusorias (no Bybit) | Reales (`--permitir-mainnet-manos`) |
| Quién late | Tusk·Tank·Kaiser·Igris | Igual; Beru/Greed hibernan |
| Sello | OK (masa ilusoria ~94, 15 frentes) | En curso — **no PASS** hasta meta/paso |
| Quién corre live | — | **Jess (México)**; USA no suelta manos Igris salvo orden |

Sim sirve para ver el camino del engorde sin gastar. Live es el manto de verdad en la cuenta.

## Estado ahora

- Manto **vivo** en cuenta (varios Santos L/S); oxígeno Tusk **crítico** (~1 %).  
- 4.0.3 abierto: engorde hacia 100 % del paso bajo Asalto.  
- Preferencia: Asalto (ley 2026-08-06).  
- Candados recientes: dual 1× aire, sin poda auto, ojos Asalto holgados, MNT bóveda ≠ manto.  
- Si la IP de la llave no está en whitelist, NAV/reconciliación fallan (mismo candado que Beru nivel 3).

## Qué no confundir

- **Bóveda MNT** (colateral / Convert) ≠ piernas del manto.  
- **Historial noche / Coliseo** = fotos de velas; **no** es engorde 4.0.3.  
- Beru fantasma/nivel 3 **no** toca el manto.

## Rituales (referencia)

```
# Sim (manos atadas)
python3 scripts/arise_igris_sim.py --segundos 180

# Live — solo con mandato; Jess / flag mainnet
python3 scripts/arise_igris.py --permitir-mainnet-manos
# Guardián: scripts/vigilar_arise_igris.py
```

## Siguiente

Seguir **4.0.3** hasta evidencia de meta del paso. Beru nivel 3 solo como ensayo spot aparte (no engorda manto). Greed al último.

Checkpoints: `CHECKPOINT_IGRIS_SIM_4_0_2.md` · `CHECKPOINT_IGRIS_LIVE_4_0_3.md` · `CHECKPOINT_LEY_IGRIS_ASALTO_2026-08-06.md`  
Doctrina: `21_DOCTRINA_IGRIS.md` · Checklist: `16` §4.0.3
