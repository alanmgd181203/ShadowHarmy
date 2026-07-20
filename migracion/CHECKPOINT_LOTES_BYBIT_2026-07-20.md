# Checkpoint — Lotes Bybit + escalera cuantizada (2026-07-20)

**Para el Monarca:** cada bocado de la escalera (Igris y Greed) ahora respeta el **lote real de Bybit** que Jess trae de México — no un piso genérico de $5.

## Qué cerró

- `core/lote_bybit.py` — lee `data/bybit_parametros_mercado.json` (BD Jess): `minOrderQty` + `qtyStep` por frente.
- Escalera: `armar_peldaños_lote` — peldaños en múltiplos válidos (ej. BTC 0.001 → saltos ~$65, no micro-dólares inventados).
- Igris materializa y Greed disparan / equilibran con qty ya cuantizada.
- Smokes: `validar_lote_bybit_smoke.py` · escalera · igris.

## Jess — solo corre el script

Pegar en Cursor de Jess (Agent):

```
git pull origin master
python scripts/jess_sincronizar_bybit_mexico.py
```

Detalle del ritual + commit de sync: `migracion/JESS_SINCRONIZAR_BYBIT.md`.

## Validar en forja (Alan)

```
python scripts/validar_lote_bybit_smoke.py
python scripts/validar_escalera_precios_smoke.py
python scripts/validar_igris_smoke.py
```

## Siguiente checklist (`16`)

**4.1.2** eventos Pergamino · **3.5.8c** ranking fusión · **3.7.P***
