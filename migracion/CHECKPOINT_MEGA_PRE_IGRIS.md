# CHECKPOINT — Mega pre-Igris (sello)

**Tag:** `mega-pre-igris`  
**Fecha:** 2026-08-03  
**Alcance:** reglas de marcha / manto / libros Tusk **antes** de sim Igris.  
**Prohibido en este sello:** forja · campo · `arise_campo` · informes ETA · `arise_igris_sim`.

## Las 8 reglas

1. Engorde al **100%** del delta (`fill_ratio=1.0`).
2. **Reserva = 1** en todas las marchas.
3. Marcha **personalizado** por duración T (umbral por par + reajuste).
4. Altar solo si no hay marcha en `data/marcha_despliegue.json`.
5. Libros Tusk: MtM bóveda ≠ riqueza Beru; equity UTA = testigo; guerra stub.
6. Aporte guerra→bóveda = transferencia explícita (asiento futuro).
7. Equilibrio manto = ratio L/S sobre **desplegado @ entrada**; meta llena → no engordar.
8. Ritmo de lote (legado táctico/forzada): **fuera del altar operativo** tras sello 2 marchas; módulo dormido. Operativas = **asalto** + **personalizado**.

## Sello 2 marchas (Monarca, 2026-08-06)

| Marcha | Intención |
|--------|-----------|
| **asalto** | Desplegar el manto lo más rápido posible (peaje aceptado). Default si no hay T. |
| **personalizado** | El Monarca elige duración ~T; calib de umbral por par. |

**Legado:** `tactico` y `marcha_forzada` no se ofrecen en el altar. Al cargar / CLI / ETA, `normalizar_marcha` las mapea a **asalto** (lectura segura; `guardar_marcha` con id legado también persiste asalto).
## Código

| Pieza | Ruta |
|-------|------|
| Director | `core/pase_director.py` |
| Duración | `core/marcha_duracion.py` |
| Ritmo lote | `core/marcha_ritmo_lote.py` |
| Libros | `core/tusk_libros.py` |
| Ventana USD | `core/manto_ventana.py` |
| Frecuencia/ETA | `core/manto_frecuencia.py` |
| Backfill L↔I | `core/kaiser_backfill.py` |
| CLI marcha | `scripts/set_marcha_cli.py` |

## Smokes

```bash
python scripts/validar_pase_director_smoke.py
python scripts/validar_marcha_duracion_smoke.py
python scripts/validar_tusk_libros_smoke.py
python scripts/validar_manto_ventana_smoke.py
python scripts/validar_marcha_ritmo_lote_smoke.py
```

## Siguiente ritual

Igris sim (**4.0.2**) — otro trabajo. Manos siguen OFF.

---

## Addendum ley 2026-08-06

Sello doctrinal aparte (oficio Igris ≠ Greed · preferencia Asalto · camino Igris→Beru→Greed): [`CHECKPOINT_LEY_IGRIS_ASALTO_2026-08-06.md`](CHECKPOINT_LEY_IGRIS_ASALTO_2026-08-06.md). Este mega-pre-Igris **no** se reescribe; el disco de marcha no se fuerza aquí.
