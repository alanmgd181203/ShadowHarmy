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

## 2) Misión actual — Sync mínimos Bybit (G_min por Santo)

**Qué es:** ritual de **ojos** — peaje real de cada Santo para Beru (`G_min`).  
**Receta / detalle (anexo, no puerta):** [`PEGAR_JESS_SYNC_MINIMOS_BYBIT.md`](PEGAR_JESS_SYNC_MINIMOS_BYBIT.md)

### Comandos exactos

```
python scripts/sync_bybit_minimos_orden.py --also-parametros
```

Más rápido (solo flota manto/Beru):

```
python scripts/sync_bybit_minimos_orden.py --flota-only --also-parametros
```

Smoke frío (sin red), después del sync:

```
python scripts/validar_g_min_variable_smoke.py
python scripts/validar_beru_capital_smoke.py
```

Si Bybit falla / timeout:

```
python scripts/sync_bybit_minimos_orden.py --from-parametros --flota-only
```

(marca advertencia en el pergamino; avisar al Monarca).

---

## 3) Qué NO hacer

- No `arise` / vigilante / manos / Beru live / Igris Asalto.
- No regenerar pase ni ranking (aún pendiente del análisis Monarca).
- No subir `.env`, `Ima/`, `tools/`, videos ni logs.
- No mezclar con noche historial Coliseo en el mismo terminal.

---

## 4) Qué mirar al terminar

1. **`data/bybit_minimos_orden.json`** — existe, fresco; G_min de flota (ETH, BTC, SOL, XRP, MNT…) y fuente (`spot_usdt` / `linear`).
2. Si algún Santo sale con peaje spot &lt; 5 → anotar para el Monarca.
3. Smokes arriba en verde.
4. Avisar al Monarca con **5–10 G_min** de flota (no el JSON entero).
5. Marcar **HECHO** abajo.

---

## 5) HECHO (Jess / Cursor marca)

- [ ] `git pull origin master` hecho
- [ ] Sync mínimos corrido (vivo o `--from-parametros` con aviso)
- [ ] `data/bybit_minimos_orden.json` revisado (muestra G_min flota)
- [ ] Smokes OK
- [ ] Monarca avisado (5–10 peajes + si hubo advertencia)

**Fecha / notas Jess:** _(vacío)_

---

## Plantilla próximas misiones

Ver [`ORDEN_ACTIVA_JESS.plantilla.md`](ORDEN_ACTIVA_JESS.plantilla.md).  
Índice de recetas: [`ordenes_jess/README.md`](ordenes_jess/README.md).
