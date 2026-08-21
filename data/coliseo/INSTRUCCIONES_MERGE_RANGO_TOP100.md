# Unir mitades USA + Jess (bóveda linear 1m · top 100 · 365d)

1. USA baja ranks 1–50 y Jess ranks 51–100 (ver `rango_top100_split.json`).
2. Jess sube el zip Drive → Monarca lo deja en `data/coliseo/` (p. ej. descomprimir `boveda_linear_1m.sqlite` de Jess como `boveda_linear_1m_jess.sqlite`).
3. Agent/Monarca fusiona con:

```
python -c "from pathlib import Path; import sqlite3; usa=Path('data/coliseo/boveda_linear_1m.sqlite'); jess=Path('data/coliseo/boveda_linear_1m_jess.sqlite'); con=sqlite3.connect(usa); con.execute('ATTACH ? AS j', (str(jess),)); con.execute('INSERT OR IGNORE INTO candles SELECT * FROM j.candles'); con.execute('INSERT OR REPLACE INTO ingest_meta SELECT * FROM j.ingest_meta'); con.commit(); print('usa_rows', con.execute('select count(*) from candles').fetchone()[0]); con.close()"
```

(Si los nombres de tabla difieren, revisar con `.tables` en cada sqlite.)

Expectativa: ~525 600 velas 1m por santo × 100 ≈ 52M filas; zip por mitad suele pesar varios GB.
