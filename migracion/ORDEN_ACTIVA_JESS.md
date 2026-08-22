# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

---

## 1) Arranque (obligatorio)

```
git fetch origin
git checkout orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md scripts/coliseo_mega_boveda.py data/coliseo/mega_boveda/lista_jess_mitad.txt data/coliseo/mega_boveda/lista_jess_mitad.csv data/coliseo/mega_boveda/split_mega_usa_jess.json data/coliseo/INSTRUCCIONES_MERGE_MEGA.md
```

Si la rama no está local:

```
git fetch origin orden-jess-boveda-rango-top50
git checkout origin/orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md scripts/coliseo_mega_boveda.py data/coliseo/mega_boveda/lista_jess_mitad.txt data/coliseo/mega_boveda/lista_jess_mitad.csv data/coliseo/mega_boveda/split_mega_usa_jess.json data/coliseo/INSTRUCCIONES_MERGE_MEGA.md
```

Luego **abre solo** `migracion/ORDEN_ACTIVA_JESS.md` y ejecuta la misión.  
Confirmar que existen los paths de arriba.
---

## 2) Misión — Mega bóveda 1m · MITAD JESS (BLEND → ZRX)

**Qué es:** completar la **mitad restante** del catálogo linear USDT 1m (365d) en **tu máquina**.  
USA ya tiene ~mitad en su lap y ahora solo remata **AAL→BITO**. Tú bajas **BLEND→ZRX** (183 bases). Mismos `workers=2` y `sleep=0.12` para terminar **más o menos a la vez**.  
Después el Monarca **une** las dos bóvedas (no lo haces tú).

**Anexo merge (solo lectura):** [`data/coliseo/INSTRUCCIONES_MERGE_MEGA.md`](../data/coliseo/INSTRUCCIONES_MERGE_MEGA.md)

### Comandos exactos

```
git pull origin master
python -u scripts/coliseo_mega_boveda.py --dias 365 --workers 2 --sleep 0.12 --watchdog --only-file data/coliseo/mega_boveda/lista_jess_mitad.txt
```

Dejar corriendo (watchdog relanza si cae). No cortes a mano salvo orden del Monarca.

### Qué mirar mientras corre

1. `data/coliseo/mega_boveda/PROGRESO_MEGA.md` — bases de tu lista pasando a **ok**.  
2. `data/coliseo/heartbeat.json` — `fase` ingest / detalle con símbolos de tu mitad (BLEND…ZRX).  
3. `data/coliseo/boveda_linear_1m.sqlite` crece (es **tu** bóveda local).

### Al terminar (obligatorio)

1. Comprobar que las **183** de `lista_jess_mitad.txt` están en ok (o avisar huecos).  
2. Zip de:
   - `data/coliseo/boveda_linear_1m.sqlite`
   - `data/coliseo/mega_boveda/checkpoint_mega_1m.json`
   - `data/coliseo/mega_boveda/PROGRESO_MEGA.md`
3. Subir zip a **Drive** (carpeta del ejército).  
4. Avisar al Monarca: «mitad Jess mega lista · Drive».

---

## 3) Qué NO hacer

- No manos / arise / Igris / Beru live.  
- No subir `.env` ni secretos.  
- No borrar bóvedas USA ni las tuyas a lo bruto.  
- **No bajar** bases de la lista USA (`lista_usa_resto.txt` · AAL→BITO).  
- No hagas el merge tú (eso es USA después).  
- No cambies `--workers` ni `--sleep` (rompería el ritmo pareja).  
- No uses otro script de bóveda viejo (`jess_boveda_coliseo_noche`) para esta misión.

---

## 4) HECHO

- [ ] Arranque desde rama `orden-jess-boveda-rango-top50` (archivos de la misión)  
- [ ] Ritual mega corriendo con `--only-file …/lista_jess_mitad.txt`  
- [ ] 183 bases BLEND→ZRX en ok (o huecos reportados)  
- [ ] Zip en Drive + aviso al Monarca  

---

*Shadow Army · mega 1m mitad Jess BLEND→ZRX · USA AAL→BITO · luego merge*
