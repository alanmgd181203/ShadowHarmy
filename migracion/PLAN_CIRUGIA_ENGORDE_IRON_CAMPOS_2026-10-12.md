# Plan de cirugía — engorde memoria + campos Iron + Red short sorda

**Fecha:** 2026-10-12  
**Checkpoint:** `checkpoint-pre-cirugias-engorde-iron-2026-10-12`  
**Estado:** **bisturí ON** · humo en seco verde (2026-10-12)  
**Manos / arise live:** aún no (espera orden del Monarca para pull en viejita)

---

## Para qué

Beru dejó de disfrutar lo que costó promediar a contramano. Tres cortes, misma alma:

1. No reiniciar el engorde en cada Oz — solo al vacío de sangre.
2. Cuando Iron diga que ya hay ganancia, engordar más fuerte (×2 / ×3).
3. Short: oreja más lejos (0,8), masa como si fuera 0,7.

Los **rangos** de Red / vacío / sangre **no** se mueven. Solo masa, memoria y brújula de Iron.

---

## Pieza A — Memoria del engorde

**Doctrina**

- Entre Reds consecutivas del mismo lado: el engorde **recuerda** (no vuelve al mínimo).
- Reinicio al mínimo del campo **solo** al tocar / cerrar con el **vacío de sangre** (ciclo nuevo).
- El tope por 0,1 % sigue siendo el freno de la racha.

**Hoy (tumor)**

- El cero del engorde se recetea en cada Oz → manos flacas otra vez → promedio más feo.

**Prueba en seco**

- Cadena Oz → Red → Oz → Red: la masa **no** vuelve al nacimiento entre medias.
- Tras vacío de sangre: sí vuelve al mínimo del campo vigente.

---

## Pieza B — Tres campos de Iron (masa × campo)

**Brújula (solo Iron)**

Mide **(realizado + flotante) / posición actual (notional vivo)** — no la pierna histórica gorda — y publica tres campos que se actualizan solos:

| Campo | Zona de ganancia | Multiplicador |
|-------|------------------|---------------|
| Guerra | pérdidas → hasta suelo de masacre actual | ×1 |
| Sangre | +1 % → +5 % | ×2 |
| Masacre real | +5 % en adelante | ×3 |

**Qué se multiplica (semáforo base × campo)**

| | Guerra | Sangre ×2 | Masacre ×3 |
|--|--------|-----------|------------|
| Rojo nace | 0,40 | 0,80 | 1,20 |
| Amarillo nace | 0,60 | 1,20 | 1,80 |
| Verde nace | 1,00 | 2,00 | 3,00 |
| Paso / 0,1 % | +0,02 | +0,04 | +0,06 |
| Tope / 0,1 % | 2,00 | 4,00 | 6,00 |

**Qué no cambia**

- Porcentajes de Red, vacío, sangre, Oz.
- Quién planta orejas (sigue Beru).
- Iron **no** engorda: solo dice el campo; Beru aplica la masa.

**Prueba en seco**

- Pierna en rojo → factores ×1.
- Cruzar +1 % → nacimiento/paso/tope ×2.
- Cruzar +5 % → ×3.
- Si el viento gira y la ganancia baja de zona, el multiplicador **baja** con el campo (Iron actualiza).

---

## Pieza C — Red short: planta 0,8 / engorda 0,7

**Doctrina**

- Oreja short sigue a **0,8 %** (y en sala por color, el short más lejos que el long).
- Al contar peldaños de masa: short usa el **% doctrinal del long** (piedra: 0,7). Ese 0,1 extra es holgura, no engorde.
- Misma alma que sangre “sorda” al estirón: el mapa se aleja, la masa no se hincha con el extra.

**Hoy**

- Short planta 0,8 y la masa cuenta 8 peldaños (0,8), no 7.

**Prueba en seco**

- Long Red @ 0,7 → N peldaños.
- Short Red @ 0,8 → **mismos** N peldaños de masa que el long a 0,7.
- La oreja short sigue cotizando a 0,8.

---

## Orden de batalla (cuando el Monarca diga “adelante”)

### Fase 0 — Checkpoint
- [x] Checkpoint en git + tag
- [x] Este plan

### Fase 1 — Doctrina viva
- [x] Anotado en `22_DOCTRINA_BERU_RANGO` + `campo_masa` Iron

### Fase 2–3 — Cableado + humo
- [x] Pieza C: Red short sorda
- [x] Pieza A: memoria engorde hasta vacío de sangre
- [x] Pieza B: campos Iron ×1/×2/×3 (nace, paso, tope)
- [x] Smoke `validar_beru_cirugia_engorde_iron_smoke.py` + piedra OK

### Fase 4 — Sello
- [x] Smokes verdes
- [x] Brújula Iron: % sobre **posición actual** (no pierna histórica)
- [x] Orden Jess lista: **solo pull + smoke** (nada despertado) — `ORDEN_ACTIVA_JESS.md`
- [ ] Despertar / manos en viejita: **solo** con orden explícita del Monarca

---

## Qué no hacer

- No mover % de Red/vacío/sangre “para compensar”.
- No reiniciar engorde en Oz “por si acaso”.
- No dejar que Beru invente el % de ganancia: **Iron manda el campo**.
- No arise live ni ranking ni secretos en esta cirugía.
- No subagentes.

---

## Criterio de victoria

- Short deja de hincharse por el 0,1 de holgura.
- Racha de Reds conserva masa (hasta sangre).
- En sangre/masacre de Iron, Beru engorda ×2/×3 y el tope acompaña.
- El ejército cobra mejor lo que ya pagó promediando a contramano.

---

— Shadow Army · plan Monarca 2026-10-12 · bisturí espera orden —
