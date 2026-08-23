# Unir mega bóveda USA + Jess (linear 1m · catálogo 725)

**Roles 2026-08-22 noche (swap):** Jess no pudo arrancar BLEND→ZRX; USA ya tenía AAL→BITO y ahora baja BLEND→ZRX. Jess baja AAL→BITO.

| Lap | Lista | Rango |
|-----|-------|-------|
| USA (Monarca) | `data/coliseo/mega_boveda/lista_jess_mitad.txt` | BLEND → ZRX (183) |
| Jess (México) | `data/coliseo/mega_boveda/lista_usa_resto.txt` | AAL → BITO (183) |

Mismos parámetros: `--dias 365 --workers 2 --sleep 0.12`.

## Cuando ambas mitades estén OK

1. Jess sube zip Drive → Monarca lo deja en `data/coliseo/` como p. ej. `boveda_linear_1m_jess.sqlite` (+ su checkpoint si hace falta).
2. **Backup** de la bóveda USA antes de fusionar.
3. Fusionar (Agent/Monarca):

```powershell
python -c "from pathlib import Path; import sqlite3; usa=Path('data/coliseo/boveda_linear_1m.sqlite'); jess=Path('data/coliseo/boveda_linear_1m_jess.sqlite'); bak=usa.with_name(usa.stem+'_pre_merge_jess.sqlite'); import shutil; shutil.copy2(usa, bak); con=sqlite3.connect(usa); con.execute('ATTACH ? AS j', (str(jess),)); con.execute('INSERT OR IGNORE INTO candles SELECT * FROM j.candles'); con.execute('INSERT OR REPLACE INTO ingest_meta SELECT * FROM j.ingest_meta'); con.commit(); print('usa_rows', con.execute('select count(*) from candles').fetchone()[0]); print('bases', con.execute('select count(distinct base) from candles').fetchone()[0]); con.close(); print('backup', bak)"
```

4. Re-correr juicio de sombras sobre la bóveda unida.

## Notas

- Cada lap escribe su propio `boveda_linear_1m.sqlite` local — no compartir el archivo a medias mientras descargan.  
- Si una base quedó corta (<85 % de 365d×1440), el mega la vuelve a pedir: normal en TradeFi nuevos.
