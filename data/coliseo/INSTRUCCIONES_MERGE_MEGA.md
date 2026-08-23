# Unir mega bóveda USA + Jess (linear 1m)

**Roles noche 2026-08-22 (actualizado cola):**

| Lap | Listas | Rango |
|-----|--------|-------|
| USA | (ya OK) AAL→BITO en bóveda USA · ahora `lista_usa_blend_cola.txt` | SUSHI → VET (38) |
| Jess | `lista_usa_resto.txt` + luego `lista_jess_extra_blend.txt` | AAL → BITO (183) + W → ZRX (38) |

Sello del split cola: `data/coliseo/mega_boveda/split_blend_cola_usa_jess.json`.

Mismos parámetros: `--dias 365 --workers 2 --sleep 0.12`.

## Cuando ambas partes estén OK

1. Jess sube zip Drive → Monarca lo deja como `data/coliseo/boveda_linear_1m_jess.sqlite`.
2. **Backup** bóveda USA.
3. Fusionar:

```powershell
python -c "from pathlib import Path; import sqlite3; usa=Path('data/coliseo/boveda_linear_1m.sqlite'); jess=Path('data/coliseo/boveda_linear_1m_jess.sqlite'); bak=usa.with_name(usa.stem+'_pre_merge_jess.sqlite'); import shutil; shutil.copy2(usa, bak); con=sqlite3.connect(usa); con.execute('ATTACH ? AS j', (str(jess),)); con.execute('INSERT OR IGNORE INTO candles SELECT * FROM j.candles'); con.execute('INSERT OR REPLACE INTO ingest_meta SELECT * FROM j.ingest_meta'); con.commit(); print('usa_rows', con.execute('select count(*) from candles').fetchone()[0]); print('bases', con.execute('select count(distinct base) from candles').fetchone()[0]); con.close(); print('backup', bak)"
```

4. Re-correr juicio de sombras sobre la bóveda unida.

## Notas

- Cada lap escribe su propio `boveda_linear_1m.sqlite` — no compartir a medias.  
- `INSERT OR IGNORE` tolera solapes si algún Santo se bajó dos veces.
