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

## 2) Misión actual — MNT inverso: modo posición + re-equilibrar pierna larga

**Qué es:** el Monarca soltó Arise Igris (ojos estrechos · Asalto · canal MNT). El **short lineal** llenó; el **long inverso** falló con Bybit `position idx not match position mode`. El manto quedó más torcido (más short). Ritual **apagado**. Hay que dejar el **MNTUSD inverso en Both Sides / hedge** y luego equilibrar el long que faltó.

**Contexto (no reabrir debate):**
- Ojos = Santos last price · **books OFF** (`ojos_estrechos` · Arise Igris igual).
- Beru/Greed **dormidos**.
- Ranking: foco MNT General ~\$537 de nocional; tras el short unilateral el Δ puede haber cambiado — reconciliar antes de plantar.

**Manos:** solo las que hacen falta para **arreglar modo** + **equilibrar long MNT inverso** (o dual limpio). No Beru. No Greed. No engorde de otros Santos.

### Comandos exactos

```
git pull origin master

# Fríos primero
python scripts/validar_ojos_estrechos_smoke.py
python scripts/validar_beru_ojos_smoke.py

# Ojos (sin manos) — confirmar Tank VERDE estrecho
python scripts/arise_ojos_tusk.py --segundos 90

# En Bybit (UI o API): MNTUSD inverso = Both Sides / hedge mode
# (mismo espíritu que el lineal). Confirmar que positionIdx 1 = long hedge funciona.

# Solo-ojos Igris (plan, sin plantar) — canal MNT
set IGRIS_FORZAR_EXCLUSIVOS=MNT
python scripts/arise_igris.py --solo-ojos --segundos 90

# Si el modo ya es hedge OK y el Monarca/esta orden autoriza equilibrar:
# (tope corto — no 12 min a ciegas)
set IGRIS_FORZAR_EXCLUSIVOS=MNT
python scripts/arise_igris.py --permitir-mainnet-manos --segundos 180
```

Si PowerShell:

```
$env:IGRIS_FORZAR_EXCLUSIVOS='MNT'
python scripts/arise_igris.py --solo-ojos --segundos 90
```

---

## 3) Qué NO hacer

- No despertar Beru ni Greed.
- No `ARISE_IGRIS_BOOKS=true` salvo que Tank muera otra vez y el Monarca lo pida.
- No engordar flota completa / otros Santos — solo **MNT** hasta equilibrar.
- No regenerar pase/ranking.
- No subir `.env`, `Ima/`, secretos ni logs gordos.
- Si el long inverso sigue con ErrCode 10001 → **parar** y avisar; no martillar shorts.

---

## 4) Qué mirar al terminar

1. Bybit: MNT inverso en **hedge/Both Sides**; long avanza o dual L+S limpio.
2. Short lineal no se dispara solo otra vez.
3. Parte al Monarca: ¿modo OK? ¿cuánto long plantó? ¿restante MNT del pase?
4. Marcar **HECHO** abajo.

---

## 5) HECHO (Jess / Cursor marca)

- [ ] `git pull origin master` hecho
- [ ] Smokes ojos OK
- [ ] Modo posición MNT inverso corregido / confirmado
- [ ] Solo-ojos o equilibrado (según pudo)
- [ ] Monarca avisado (modo + nocional L/S MNT + restante)

**Fecha / notas Jess:** _(vacío)_

---

## Nota

Tumor visto USA 2026-08-13: `ORDEN_ERROR position idx not match position mode` en `MNTUSD` Buy Market `positionIdx=1`. Short `MNTUSDT` sí fill. No repetir engorde a una pierna.
