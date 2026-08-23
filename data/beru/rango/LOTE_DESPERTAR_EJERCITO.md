# Lote despertar — Beru rango original (sin wake aún)

Generado: 2026-08-23T20:35:32.398210+00:00
Perfil: **normal** · apalancamiento: **máximo** al `--manos-go`
Santos: **14**

## Antes de despertar (otra lap / nueva máquina)

1. **Pausar LIT** si sigue vivo aquí (Ctrl+C en terminal manos, o cerrar PID del panel).
2. `git pull` si el código viene del repo.
3. API Bybit cargada · `MODO_SIMULACION=false` solo en manos con `--manos-go`.

## Ojos (una flota · sin manos)

```powershell
$env:BERU_RANGO_PERFIL = "normal"
python scripts/arise_beru_rango_ojos.py --santos VVV,AKT,XLM,CC,HYPE,NEAR,ZEREBRO,LIT,MORPHO,MON,KORU,AXTI,NBIS,SAMSUNG
```

## Manos (un proceso por Santo · GO explícito)

```powershell
$env:BERU_RANGO_PERFIL = "normal"
$env:IGRIS_FORCE_MAX_LEVERAGE = "true"
# Repetir en terminal aparte por Santo:
python scripts/arise_beru_rango_manos.py --activo VVV --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo AKT --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo XLM --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo CC --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo HYPE --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo NEAR --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo ZEREBRO --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo LIT --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo MORPHO --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo MON --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo KORU --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo AXTI --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo NBIS --manos-go --continuar
python scripts/arise_beru_rango_manos.py --activo SAMSUNG --manos-go --continuar
```

## Santos

| Santo | Symbol | Lev máx | TradeFi | Vivo ahora |
|-------|--------|---------|---------|------------|
| VVV | VVVUSDT | 20.0 |  | — |
| AKT | AKTUSDT | 25.0 |  | — |
| XLM | XLMUSDT | 50.0 |  | — |
| CC | CCUSDT | 25.0 |  | — |
| HYPE | HYPEUSDT | 75.0 |  | — |
| NEAR | NEARUSDT | 50.0 |  | — |
| ZEREBRO | ZEREBROUSDT | 12.5 |  | — |
| LIT | LITUSDT | 25.0 |  | ACECHANDO (pid 14492) |
| MORPHO | MORPHOUSDT | 25.0 |  | — |
| MON | MONUSDT | 50.0 |  | — |
| KORU | KORUUSDT | 20.0 |  | — |
| AXTI | AXTIUSDT | 20.0 | ✓ | — |
| NBIS | NBISUSDT | 20.0 | ✓ | — |
| SAMSUNG | SAMSUNGUSDT | 25.0 | ✓ | — |

JSON: `C:\Users\alans\Desktop\ShadowHarmy\data\beru\rango\lote_despertar_ejercito.json`

