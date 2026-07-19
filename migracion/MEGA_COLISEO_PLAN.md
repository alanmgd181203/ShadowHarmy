# Mega Coliseo — plan de batalla (Monarca 2026-07-18)

**Finalidad:** pase de batalla / ranking de rangos (activo × Soldado…Mariscal) con legión al máximo.

## Orden

1. **Eje malla ×1** (oz/red doctrinal)  
   - Barrido vacíos 0.8…2.0% · PLENO + legión · 22 activos · año + meses + 3d  
   - Elige **2 vacíos dorados** (mediana calor pase)  
   - Sub-Berus: BERUBBY → PROTO2 → PROTO1 → PLENO en esos 2 vacíos × 22  
   - Re-run outliers (`path=min`)
2. **Eje malla ×2** — igual, malla al doble  
3. **Informe** `scripts/coliseo_mega_informe.py` → gráficas + tabla pase de batalla

## Indicador

Calor pase = **3d 20% · mes 50% · año 30%**.

## Checkpoints

`data/coliseo/mega/checkpoint.json` + `jobs/*.json`.  
Reanudar: `python scripts/coliseo_mega_campana.py --resume`

## Contabilidad

Fee/botín sobre **masa spot** (no nocional Igris). Techo masa teatro ≈ margen×8 (oxígeno proxy).

## Resultado firmado (2026-07-19)

- Campaña mega: **done** · vacío dorado preferido **1,6 %** · malla ×1  
- Pase de cuenta: [`PASE_BATALLA_13_SANTOS.md`](PASE_BATALLA_13_SANTOS.md)  
- Plan crecimiento: [`23_PLAN_CRECIMIENTO.md`](23_PLAN_CRECIMIENTO.md) v2  
