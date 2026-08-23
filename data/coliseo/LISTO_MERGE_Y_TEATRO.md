# Listo para merge + teatro (NO ejecutado)

**Sello revisión:** 2026-08-22 ~21:25 local USA  
**Zip Jess:** `Downloads/ShadowHarmy_Coliseo_mega_jess_AALBITO_WZRX_20260823_0312.zip`

## Jess — OK

| Pieza | Estado |
|-------|--------|
| AAL→BITO (183) | **183/183** en checkpoint + sqlite |
| Extra W→ZRX (38) | **38/38** |
| Archivo canónico | `data/coliseo/boveda_linear_1m_jess.sqlite` (~3.97 GB) |
| Checkpoint | `data/coliseo/mega_boveda/checkpoint_mega_1m_jess.json` |
| Progreso | `data/coliseo/mega_boveda/PROGRESO_MEGA_jess.md` |

## USA — OK

| Pieza | Estado |
|-------|--------|
| Bóveda | `data/coliseo/boveda_linear_1m.sqlite` (~18.7 GB) |
| Cola SUSHI→VET (38) | **38/38** |

## Qué falta (GO Monarca) — aún NO corrido

1. **Merge** (backup + unir Jess → USA):

```powershell
python -u scripts/merge_mega_usa_jess.py          # chequeo
python -u scripts/merge_mega_usa_jess.py --go     # ejecutar
```

2. **Teatro matriz** (después del merge), un slot a la vez o paralelo:

```powershell
python -u scripts/servir_teatro_live.py
# luego, con GO:
python -u scripts/teatro_beru_rango_juicio.py --beru-perfil normal --perfil reciente --out data/coliseo/rango_juicio/matriz/normal_reciente
python -u scripts/teatro_beru_rango_juicio.py --beru-perfil feria --perfil reciente --out data/coliseo/rango_juicio/matriz/feria_reciente
python -u scripts/teatro_beru_rango_juicio.py --beru-perfil normal --perfil anual --out data/coliseo/rango_juicio/matriz/normal_anual
python -u scripts/teatro_beru_rango_juicio.py --beru-perfil feria --perfil anual --out data/coliseo/rango_juicio/matriz/feria_anual
```

Página viva: http://127.0.0.1:8765/teatro_live.html

## Candado

- **No** se ha corrido merge.  
- **No** se ha arrancado ningún juicio nuevo de la matriz.
