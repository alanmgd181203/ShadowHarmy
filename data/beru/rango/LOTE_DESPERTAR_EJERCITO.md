# Lote despertar — Beru rango original (sin wake aún)

Generado: 2026-08-24T21:47:42.272618+00:00
Perfil: **normal** · apalancamiento: **máximo** al `--manos-go`
Santos: **4**

## Antes de despertar (otra lap / nueva máquina)

1. **Pausar LIT** si sigue vivo aquí (Ctrl+C en terminal manos, o cerrar PID del panel).
2. `git pull` si el código viene del repo.
3. API Bybit cargada · `MODO_SIMULACION=false` solo en manos con `--manos-go`.

## Ojos (una flota · sin manos)

```powershell
$env:BERU_RANGO_PERFIL = "normal"
python scripts/arise_beru_rango_ojos.py --santos MVLL,MINIMAX,SOXL,AXTI
```

## Manos (un proceso por Santo · GO explícito)

```powershell
$env:BERU_RANGO_PERFIL = "normal"
$env:IGRIS_FORCE_MAX_LEVERAGE = "true"
# Repetir en terminal aparte por Santo:
python scripts/arise_beru_rango_manos.py --activo MVLL --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo MINIMAX --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo SOXL --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo AXTI --manos-go --continuar
```

## Santos

| Santo | Symbol | Lev máx | TradeFi | Vivo ahora |
|-------|--------|---------|---------|------------|
| MVLL | MVLLUSDT | 20.0 |  | — |
| MINIMAX | MINIMAXUSDT | 25.0 | ✓ | — |
| SOXL | SOXLUSDT | 20.0 |  | — |
| AXTI | AXTIUSDT | 20.0 | ✓ | ACECHANDO (pid 8616) |

JSON: `C:\Users\lenovo\ShadowHarmy\data\beru\rango\lote_despertar_ejercito.json`

