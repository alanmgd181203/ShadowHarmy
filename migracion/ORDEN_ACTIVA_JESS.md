# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México (viejita).**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

**Actualización 2026-10-07 — despertar limpio neto + Beru desde 0**

---

## 1) Arranque (obligatorio)

```
git pull origin master
```

Luego **abre solo este archivo** y ejecuta la misión de abajo.

---

## 2) Misión — despertar limpio (vaso neto · Beru desde 0)

**Qué es:** La casa OKX ya está en **neto** (un vaso: la contraria reduce). El código nuevo no arma piernas. Hay que **traer el código**, sellar memoria del escudo, y despertar la flota Beru **desde cero** (semilla nueva), más Igris / Iron / vigilantes como antes.

**Receta / detalle:** ninguna.

### Comandos exactos (PowerShell, raíz del repo en la viejita)

```
cd C:\Users\lenovo\ShadowHarmy
git pull origin master

# Verdad de casa: debe decir net_mode y 0 SWAP abiertas (BTC spot no cuenta)
C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe -u -c "from core import okx_rest; c=okx_rest.get_private('/api/v5/account/config') or []; print('modo', (list(c) or [{}])[0].get('posMode')); p=okx_rest.get_private('/api/v5/account/positions', params={'instType':'SWAP'}) or []; print('swap_abiertas', sum(1 for x in p if abs(float(x.get('pos') or 0))>1e-12))"

# Memoria escudo a 0 (no abre manos)
C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe -u scripts\sellar_viejita_parada_limpia.py

# Hierro: borrar memoria vieja de piernas (casa plana)
C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe -u -c "from pathlib import Path; p=Path('data/beru/papel/iron_memoria.json'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text('{}', encoding='utf-8'); e=Path('data/beru/papel/descarga_estado.json'); e.write_text('{}', encoding='utf-8') if e.exists() or True else None; print('iron_memoria_cero')"

# Despertar ejército (Beru cuarteles con --desde-cero + Igris + Iron + vigilantes)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\_despertar_ejercito.ps1
```

Espera ~1 min. Luego pulso:

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\_pulso_despertar.ps1
```

---

## 3) Qué NO hacer

- No volver a `long_short_mode` / piernas.
- No `--continuar` en Beru (debe ser **desde cero**).
- No tocar `.env` ni secretos.
- No despertar éxtasis vivo (solo papel, ya va en el script).
- No aplanar BTC spot (solo SWAP estaba plano).

---

## 4) Qué mirar al terminar

1. `modo` = **net_mode** · `swap_abiertas` solo lo que Beru vaya abriendo (al inicio ~0).
2. `_pulso_despertar`: campamentos vivos, Igris BTC vivo, Iron vivo.
3. Un log de cuartel (`data/beru/rango/vigilante_flota/campamentos/CAMP_001/stdout.log`) dice **DESDE CERO**.
4. Avisar al Monarca: cuántos cuarteles, si Igris late, si el primer Santo ya planta semilla.

---

## 5) HECHO (Jess / Cursor marca)

- [ ] `git pull origin master` hecho
- [ ] Modo neto confirmado
- [ ] Escudo sellado + Iron memoria en cero
- [ ] `_despertar_ejercito.ps1` OK
- [ ] Pulso OK · Monarca avisado

**Fecha / notas Jess:** _(vacío)_
