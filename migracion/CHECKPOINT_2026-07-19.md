# Checkpoint cuartel — 2026-07-19

**Commits:** pre-purge `253147f` · post-purge (este sello).  
**Firma Monarca:** pase 13 Santos · rangos Aspirante→Chamán.

## Qué quedó vivo

| Pieza | Estado |
|-------|--------|
| Mega Coliseo | done · vacío 1,6 % · malla ×1 |
| Pase batalla | [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md) |
| Plan crecimiento | [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md) v2 + `plan_crecimiento.py` |
| Ascensión UI | estrella ETH/HYPE/XRP/MNT/LTC · techos pase |
| Checklist 5.3.3 / 3.5.9 | ✅ doctrinal |

## Qué no va a git (Drive / local)

- `data/coliseo/mega/jobs/` (~685) · charts · bóvedas sqlite  
- `data/kaiser/samples/` · `Ima/` · `tools/cloudflared.exe` · `ShadowHarmy_Coliseo_*`  
- Rankings horarios regenerables (`ranking_h*`, `h365/`)

## Purge hecho en este checkpoint

- `.gitignore` ampliado (jobs, media, samples, rankings)  
- Borrados scripts muertos: `debug_ws*.py`, `probar_ciclo_beru_testnet.py` (sustituido por `beru_live_testnet.py`)  
- Índice `README.md` + progreso checklist + doctrina Igris alineada al pase  
- Roadmap M2.12 → v2 pase

## Siguiente del camino (checklist)

1. **4.1.2** Telegram — tabla evento → nivel  
2. **4.1.3** Alertas críticas  
3. **3.5.8c** ranking fusión (motor parcial)  
4. **3.7.P*** Semáforos matriz  

Validar: `python scripts/validar_plan_crecimiento_smoke.py`
