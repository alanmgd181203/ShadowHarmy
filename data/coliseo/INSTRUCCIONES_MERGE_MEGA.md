# Unir mega bóveda USA + Jess (linear 1m)

**Estado 2026-08-22 noche:** ambas mitades en disco · merge **preparado** · aún **sin ejecutar**.  
Ver checklist: [`LISTO_MERGE_Y_TEATRO.md`](LISTO_MERGE_Y_TEATRO.md)

| Lap | Entrega | Cobertura |
|-----|---------|-----------|
| USA | `boveda_linear_1m.sqlite` | AAL→BITO previos + cola SUSHI→VET (38) OK |
| Jess | `boveda_linear_1m_jess.sqlite` (desde zip Drive) | AAL→BITO (183) + W→ZRX (38) OK |

## Ritual (solo con GO)

```powershell
python -u scripts/merge_mega_usa_jess.py          # dry-run
python -u scripts/merge_mega_usa_jess.py --go     # backup + INSERT OR IGNORE
```

Tras el merge: teatro normal/feria × reciente/anual (matriz ya preparada; ver `rango_juicio/matriz/plan.json`).

## Notas

- Cada lap escribe su propio sqlite — no compartir a medias mientras descargan.  
- `INSERT OR IGNORE` tolera solapes.
