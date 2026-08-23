# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

**Cambio 2026-08-22 noche:** USA ya remató AAL→BITO y ahora baja **BLEND→ZRX** en su lap.  
**Tú bajas la otra mitad: AAL→BITO** (`lista_usa_resto.txt`). No improvises paths.

---

## 1) Arranque (obligatorio) — traer TODO el paquete

Desde la raíz del repo:

```
git fetch origin
git checkout orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md core/coliseo_catalogo.py core/coliseo_boveda.py scripts/coliseo_mega_boveda.py scripts/jess_boveda_coliseo_noche.py data/coliseo/mega_boveda/lista_usa_resto.txt data/coliseo/mega_boveda/lista_usa_resto.csv data/coliseo/mega_boveda/split_mega_usa_jess.json data/coliseo/INSTRUCCIONES_MERGE_MEGA.md
```

Si la rama no está local:

```
git fetch origin orden-jess-boveda-rango-top50
git checkout origin/orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md core/coliseo_catalogo.py core/coliseo_boveda.py scripts/coliseo_mega_boveda.py scripts/jess_boveda_coliseo_noche.py data/coliseo/mega_boveda/lista_usa_resto.txt data/coliseo/mega_boveda/lista_usa_resto.csv data/coliseo/mega_boveda/split_mega_usa_jess.json data/coliseo/INSTRUCCIONES_MERGE_MEGA.md
```

### Comprobar que existen (si falta uno → PARA y avisa; no inventes)

- `migracion/ORDEN_ACTIVA_JESS.md`
- `core/coliseo_catalogo.py`
- `core/coliseo_boveda.py`
- `scripts/coliseo_mega_boveda.py`
- `scripts/jess_boveda_coliseo_noche.py`
- `data/coliseo/mega_boveda/lista_usa_resto.txt`

### Humo de import (obligatorio antes del mega)

```
python -c "from core import coliseo_catalogo, coliseo_boveda; import scripts.coliseo_mega_boveda; print('OK imports mega')"
```

Si eso falla: **no corras el mega**. Avisa al Monarca con el error exacto.

Luego **abre solo** esta orden y ejecuta la misión.

---

## 2) Misión — Mega bóveda 1m · MITAD JESS (AAL → BITO)

**Qué es:** completar **183** bases linear USDT 1m (365d) en **tu** máquina: lista `lista_usa_resto.txt` (AAL→BITO).  
USA en paralelo baja BLEND→ZRX. Después el Monarca **une** las dos bóvedas (no lo haces tú).

**Anexo merge (solo lectura):** [`data/coliseo/INSTRUCCIONES_MERGE_MEGA.md`](../data/coliseo/INSTRUCCIONES_MERGE_MEGA.md)

### Comando exacto (uno solo)

```
python -u scripts/coliseo_mega_boveda.py --dias 365 --workers 2 --sleep 0.12 --watchdog --only-file data/coliseo/mega_boveda/lista_usa_resto.txt
```

Dejar corriendo (watchdog relanza si cae). No cortes a mano salvo orden del Monarca.

### Qué mirar mientras corre

1. `data/coliseo/mega_boveda/PROGRESO_MEGA.md` — bases AAL…BITO pasando a **ok**.  
2. `data/coliseo/heartbeat.json` — `fase` mega_ingest / detalle con esos símbolos.  
3. `data/coliseo/boveda_linear_1m.sqlite` crece (es **tu** bóveda local).

### Al terminar (obligatorio)

1. Comprobar que las **183** de `lista_usa_resto.txt` están en ok (o avisar huecos).  
2. Zip de:
   - `data/coliseo/boveda_linear_1m.sqlite`
   - `data/coliseo/mega_boveda/checkpoint_mega_1m.json`
   - `data/coliseo/mega_boveda/PROGRESO_MEGA.md`
3. Subir zip a **Drive** (carpeta del ejército).  
4. Avisar al Monarca: «mitad Jess mega AAL-BITO lista · Drive».

---

## 3) Qué NO hacer

- No manos / arise / Igris / Beru live.  
- No subir `.env` ni secretos.  
- No borrar bóvedas a lo bruto.  
- **No bajar** `lista_jess_mitad.txt` (BLEND→ZRX) — esa es USA ahora.  
- No hagas el merge tú.  
- No cambies `--workers` ni `--sleep`.  
- No uses `jess_boveda_coliseo_noche` como comando principal (solo es dependencia del mega).  
- No inventes archivos ni copies de otro path si falta un pergamino: **para y avisa**.

---

## 4) HECHO

- [ ] Arranque: checkout del paquete completo desde `orden-jess-boveda-rango-top50`  
- [ ] Humo de imports OK  
- [ ] Ritual mega corriendo con `--only-file …/lista_usa_resto.txt`  
- [ ] 183 bases AAL→BITO en ok (o huecos reportados)  
- [ ] Zip en Drive + aviso al Monarca  

---

*Shadow Army · Jess AAL→BITO · USA BLEND→ZRX · luego merge*
