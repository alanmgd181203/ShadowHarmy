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

---

## 2) Misión actual — Revisar Beru rango (Oz trailing)

**Qué es:** el Monarca selló Beru rango como **trailing de activación**:
Vacío/sangre act. **1,2** · Oz callback **0,2** · **Red también trailing**
(act. **0,7** + callback 0,2 · $5). Sangre cancela Red pendiente.
Jess **revisa** (smokes + teatro). **No** manos ni Bybit live.

**Receta / detalle:** ninguna · doctrina [`22_DOCTRINA_BERU_RANGO.md`](22_DOCTRINA_BERU_RANGO.md)

### Comandos exactos

```
git pull origin master
python scripts/validar_beru_rango_smoke.py
python scripts/validar_teatro_beru_rango_smoke.py
python scripts/teatro_beru_rango.py --activo HYPE --dias 3 --abrir
```

Lee la crónica y el HTML del teatro (Play). Comprueba que la narración diga
trailing (Vacío arma rastro · Oz detona al pullback/rebote · Red→$5).

---

## 3) Qué NO hacer

- No `BERU_RANGO_MANOS=true` ni place_order / Bridge live.
- No despertar Beru spot / flota / `arise_beru_*` / Igris / Greed.
- No cancelar ni tocar órdenes en Bybit.
- No regenerar pase / ranking.
- No subir `.env` ni secretos.
- No mezclar este oficio con el Beru spot fósil.

---

## 4) Qué mirar al terminar

1. Ambos smokes: línea `OK validar_beru_rango_smoke` y `OK validar_teatro_beru_rango_smoke`.
2. Teatro: `data/coliseo/rango_teatro/teatro_HYPE_3d.html` + `cronica_HYPE_3d.md`.
3. Doctrina `22_DOCTRINA_BERU_RANGO.md`: Oz = trailing 0,2; sangre 1,2; Red→$5.
4. Marcar **HECHO** y avisar al Monarca: smokes OK/FALLO + 2–3 frases de si el
   teatro se entiende (trailing vs Oz fija).

---

## 5) HECHO (Jess / Cursor marca)

- [ ] `git pull origin master` hecho
- [ ] `validar_beru_rango_smoke` OK
- [ ] `validar_teatro_beru_rango_smoke` OK
- [ ] Teatro HYPE 3d abierto / crónica leída
- [ ] Aviso al Monarca con veredicto corto

---

*Shadow Army · puerta única · Beru rango Oz trailing · sin manos*
