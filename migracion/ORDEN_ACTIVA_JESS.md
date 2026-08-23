# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

**Actualización 2026-08-22 ~19:15 local USA:**  
Si ya casi terminas **AAL→BITO** (~151+), **no pares el zip**. Cuando esa lista esté OK, lanza **ya** la cola extra **W→ZRX** (38 bases). USA sigue **SUSHI→VET** en paralelo. Luego merge en USA.

---

## 1) Arranque (obligatorio) — traer TODO el paquete

Desde la raíz del repo:

```
git fetch origin
git checkout orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md core/coliseo_catalogo.py core/coliseo_boveda.py scripts/coliseo_mega_boveda.py scripts/jess_boveda_coliseo_noche.py data/coliseo/mega_boveda/lista_usa_resto.txt data/coliseo/mega_boveda/lista_usa_resto.csv data/coliseo/mega_boveda/lista_jess_extra_blend.txt data/coliseo/mega_boveda/lista_jess_extra_blend.csv data/coliseo/mega_boveda/split_blend_cola_usa_jess.json data/coliseo/INSTRUCCIONES_MERGE_MEGA.md
```

Si la rama no está local:

```
git fetch origin orden-jess-boveda-rango-top50
git checkout origin/orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md core/coliseo_catalogo.py core/coliseo_boveda.py scripts/coliseo_mega_boveda.py scripts/jess_boveda_coliseo_noche.py data/coliseo/mega_boveda/lista_usa_resto.txt data/coliseo/mega_boveda/lista_usa_resto.csv data/coliseo/mega_boveda/lista_jess_extra_blend.txt data/coliseo/mega_boveda/lista_jess_extra_blend.csv data/coliseo/mega_boveda/split_blend_cola_usa_jess.json data/coliseo/INSTRUCCIONES_MERGE_MEGA.md
```

### Comprobar que existen (si falta uno → PARA y avisa; no inventes)

- `migracion/ORDEN_ACTIVA_JESS.md`
- `core/coliseo_catalogo.py`
- `core/coliseo_boveda.py`
- `scripts/coliseo_mega_boveda.py`
- `scripts/jess_boveda_coliseo_noche.py`
- `data/coliseo/mega_boveda/lista_usa_resto.txt`
- `data/coliseo/mega_boveda/lista_jess_extra_blend.txt`

### Humo de import (si aún no lo corriste hoy)

```
python -c "from core import coliseo_catalogo, coliseo_boveda; print('OK imports mega')"
```

Si falla: **no corras el mega**. Avisa al Monarca con el error exacto.

Luego **abre solo** esta orden y ejecuta.

---

## 2) Misión — dos pasos en tu misma bóveda

### Paso A — terminar AAL→BITO (si aún no acabas)

```
python -u scripts/coliseo_mega_boveda.py --dias 365 --workers 2 --sleep 0.12 --watchdog --only-file data/coliseo/mega_boveda/lista_usa_resto.txt
```

Si **ya** tienes las 183 AAL→BITO en ok: **salta al Paso B** (no relances A).

### Paso B — cola extra W→ZRX (38 bases) · YA

Misma bóveda local (`boveda_linear_1m.sqlite`). No borres nada.

```
python -u scripts/coliseo_mega_boveda.py --dias 365 --workers 2 --sleep 0.12 --watchdog --only-file data/coliseo/mega_boveda/lista_jess_extra_blend.txt
```

Lista: **W → ZRX** (38). USA en paralelo hace **SUSHI → VET** (38). No bajes la cola USA.

### Qué mirar

1. `data/coliseo/mega_boveda/PROGRESO_MEGA.md` — ok en AAL…BITO y luego W…ZRX.  
2. `data/coliseo/heartbeat.json` — símbolos de tu lista.  
3. `data/coliseo/boveda_linear_1m.sqlite` crece.

### Al terminar (obligatorio)

1. 183 AAL→BITO ok **y** 38 W→ZRX ok (o huecos reportados).  
2. Zip de:
   - `data/coliseo/boveda_linear_1m.sqlite`
   - `data/coliseo/mega_boveda/checkpoint_mega_1m.json`
   - `data/coliseo/mega_boveda/PROGRESO_MEGA.md`
3. Subir zip a **Drive**.  
4. Avisar: «Jess mega AAL-BITO + extra W-ZRX lista · Drive».

---

## 3) Qué NO hacer

- No manos / arise / Igris / Beru live.  
- No subir `.env` ni secretos.  
- No borrar la bóveda.  
- **No bajar** `lista_usa_blend_cola.txt` (SUSHI→VET) — eso es USA.  
- No hagas el merge.  
- No cambies `--workers` ni `--sleep`.  
- No inventes archivos: si falta pergamino → **para y avisa**.

---

## 4) HECHO

- [ ] Checkout del paquete (incluye `lista_jess_extra_blend.txt`)  
- [ ] Paso A: 183 AAL→BITO ok (o ya estaba)  
- [ ] Paso B: 38 W→ZRX ok  
- [ ] Zip Drive + aviso al Monarca  

---

*Shadow Army · Jess AAL→BITO + extra W→ZRX · USA cola SUSHI→VET · luego merge*
