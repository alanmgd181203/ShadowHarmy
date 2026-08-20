# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Puerta única: este archivo. Sin recetas PEGAR (purgadas).

---

## 1) Arranque (obligatorio)

```
git pull origin master
```

Luego **abre solo este archivo** y ejecuta la misión de abajo.

---

## 2) Misión actual — Beru flota viva 100% (vigilar hasta las 12)

**Qué es:** despertar **toda la flota Beru** con **Hoz real** en Bybit.
Los 22 Santos. Cada uno nace en el grado que aguante su manto
(Soldado / Capitán / General / Mariscal). Vacío ±1,1 · Hoz 1,0.
Igris y Greed **dormidos**. Margen spot ON. Bitácora viva encendida.

**Manos reales:** ON (toda la legión).  
**Importante:** correr desde **México** (IP de la API Bybit). Desde USA
la reconciliación del manto falla y la siembra aborta sola.

**Duración:** default **4 h**. Si sigue vivo a las **12:00 México**,
Ctrl+C sella. No cancelar cartas a mano.

### Comandos exactos

```
git pull origin master
python scripts/validar_beru_cazador_smoke.py
python scripts/validar_beru_fantasma_smoke.py
python scripts/arise_beru_flota_viva.py
```

Equivalente con corte a las 12 (ajusta segundos si arrancas más tarde):

```
python scripts/arise_beru_flota_viva.py --segundos 14400
```

`0` = hasta Ctrl+C (si quieres cortar tú a las 12).

---

## 3) Qué NO hacer

- No `arise_igris` / dual / engorde Igris / Greed.
- No `arise_beru_flota_mixta` ni `arise_beru_hype_mariscal` (esos ya no son hoy).
- No `arise_beru_manos_chiquitas` (techo de ensayo).
- No regenerar pase / ranking.
- No subir `.env` ni secretos.
- No cancelar órdenes spot a mano en Bybit.
- No cambiar la lista de Santos ni forzar PLENO a toda la flota.
- No tocar Tusk / oxígeno a mano.

---

## 4) Qué mirar (arranque + cada ~20 min + al sellar)

1. Consola: `RITUAL BERU — FLOTA VIVA (100%)` · `[BERU_VIVO]` al plantar Hoz.
2. Crónica ~20 s: `cazando=HYPE:VIVO+carta,...` · cuántas cartas.
3. Latido: `data/logs/beru_fantasma/heartbeat.json`
4. Pergamino: `data/logs/beru_fantasma/disparos.jsonl`
   (LLAMADO, ALTAR_ARMADO / FALLIDO, fill, engorde).
5. Al sellar: `data/logs/beru_fantasma/ultimo_informe.json`
   — veredicto `flota_viva_sellada` · cartas colgadas · cazando.
6. Si siembra aborta («sin foto fresca del manto») → avisar ya, no insistir.
7. Oxígeno Tusk: si sale CRÍTICO, avisar; **no** apagues tú salvo que el
   Monarca lo pida.

**Avisar al Monarca al arrancar:** «Beru flota viva ON · N semillas ·
rangos …».  
**Al sellar (12:00 o 4 h):** «Sellado · cartas=N · cazando=… · disparos≈…»
+ 4–6 líneas de qué Santos cazaron / fallaron al plantar.

---

## 5) HECHO (Jess / Cursor marca)

- [ ] `git pull origin master` hecho
- [ ] Smokes cazador + fantasma OK
- [ ] `arise_beru_flota_viva.py` corrido (hasta 12:00 o 4 h)
- [ ] Bitácora / informe revisados
- [ ] Monarca avisado (arranque y sello)

**Fecha / notas Jess:** _(vacío)_

---

## Nota Monarca

- Esto **sí planta condicionales reales**. No es fantasma.
- Al Ctrl+C el pergamino sella; las cartas que queden colgadas **siguen
  en Bybit** hasta que el Monarca pida funeral. No las toques a mano.
