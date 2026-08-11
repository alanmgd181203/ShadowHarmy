# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

---

## 1) Arranque (obligatorio)

```
git pull origin master
```

Luego **abre solo este archivo** y ejecuta la misión de abajo.  
No busques otro pergamino como mandato principal.

---

## 2) Misión actual — Sync techos de apalancamiento + smokes fríos

**Qué es:** ritual de **ojos** — confirmar que los techos L/I de Bybit coinciden con la tabla del ejército (peaje pierna a pierna). USA a menudo recibe 403; México sí puede mirar vivo.

**Manos:** ATADAS. Ni arise, ni engorde, ni bisturí live.

**Anexo (detalle, no puerta):** si hace falta el ritual de mínimos G_min, ver receta `PEGAR_JESS_SYNC_MINIMOS_BYBIT.md` — **no** es esta misión.

### Comandos exactos

```
python scripts/verificar_apalancamientos_bybit.py --json data/apalancamientos_bybit_vivo.json
```

Si Bybit falla / timeout:

```
python scripts/verificar_apalancamientos_bybit.py --from-parametros --json data/apalancamientos_bybit_vivo.json
```

(usar BD local; avisar al Monarca que fue frío).

Solo aplicar a config si el reporte marca **diff** claro y Monarca/USA lo pidió:

```
python scripts/verificar_apalancamientos_bybit.py --apply-config --json data/apalancamientos_bybit_vivo.json
```

Smokes fríos (obligatorios al terminar):

```
python scripts/validar_pase_im_ranking_smoke.py
python scripts/validar_beru_capital_smoke.py
```

---

## 3) Qué NO hacer

- No `arise` / vigilante / manos / Beru live / Igris Asalto.
- No `nivelar_manto_pase.py` en LIVE / reduceOnly.
- No regenerar pase ni ranking salvo orden escrita nueva.
- No subir `.env`, `Ima/`, `tools/`, videos ni logs.
- No mezclar con noche historial Coliseo en el mismo terminal.

---

## 4) Qué mirar al terminar

1. **`data/apalancamientos_bybit_vivo.json`** — fresco; foco LINK / AVAX / OP / LTC / SOL / ETH L y I vs config.
2. Si `n_diff_config` > 0 → anotar diffs al Monarca (no aplicar a ciegas).
3. Smokes arriba en verde.
4. Avisar al Monarca: «techos OK» o lista corta de diffs + fuente (vivo / BD).
5. Marcar **HECHO** abajo.

---

## 5) HECHO (Jess / Cursor marca)

- [ ] `git pull origin master` hecho
- [ ] Verificar apalancamientos corrido (vivo o `--from-parametros` con aviso)
- [ ] `data/apalancamientos_bybit_vivo.json` revisado (foco flota)
- [ ] Smokes OK (`validar_pase_im_ranking_smoke` + `validar_beru_capital_smoke`)
- [ ] Monarca avisado (OK o diffs)

---

## Nota

Peaje IM = notional/lev_inv + notional/lev_lin. Corona Brujo \$1673 · Chamán \$3735. Candado engorde: `OVERSHOOT_RANKING` si el Santo ya pasa la meta del paso.
