# PEGAR Jess — Noche historial flota Igris (bóveda / gráficas)

**Para:** Cursor en la Mac de Jess (México)  
**Qué es:** función del **ejército de noche** — llena historial y gráficas de la flota que Igris desplegará (manto Inverse∩Linear) **y** sus spots.  
**Qué NO es:** **no** es el live **4.0.3 Asalto** (manos). No dispara órdenes. No sustituye `PEGAR_JESS_IGRIS_LIVE_ASALTO.md`.

Motor: mismo Coliseo (`jess_boveda_coliseo_noche`) con mercados spot + linear + inverse.  
Detalle técnico Coliseo: [`JESS_BOVEDA_COLISEO.md`](JESS_BOVEDA_COLISEO.md).

---

## Mandato listo para pegar en Cursor (Agent) — NOCHE HISTORIAL

```
Actualiza el repo y deja corriendo SOLO la noche de historial Igris (bóveda velas).
NO arranques arise / vigilante Asalto / manos.

1) git status && git pull origin master

2) Laptop en corriente, sin dormir. Un solo terminal:

python scripts/jess_noche_historial_igris.py --dias 365 --watchdog

   Por defecto:
   - Flota del diccionario manto (~22 barcos Inverse∩Linear)
   - Velas 1m: spot + linear + inverse (spot primero)
   - 3 puentes en paralelo + vigilante cada 10 min
   - Al terminar: zip en data/coliseo/ para Drive
   - SIN ranking Fantasma · SIN manos Igris

3) Por la mañana revisa:
   - data/coliseo/PROGRESO.md   (bases × mar OK)
   - data/coliseo/MANIFIESTO.md
   - data/coliseo/ShadowHarmy_Coliseo_*.zip
   - Bóvedas: boveda_spot_1m.sqlite · boveda_linear_1m.sqlite · boveda_inverse_1m.sqlite

4) Sube el ZIP (o la carpeta data/coliseo) a Google Drive y avisa al Monarca.

NO subas el sqlite/zip a GitHub.
NO subas .env, Ima/, tools/, videos ni logs.
NO mezclar con el ritual Asalto 4.0.3 en el mismo terminal.
```

### Si se cae a media noche

```
python scripts/jess_noche_historial_igris.py --dias 365 --once
```

Es reanudable (checkpoint). El vigilante ya lo relanza solo si usaste `--watchdog`.

### Si Bybit frena mucho (429 / errores)

```
python scripts/jess_noche_historial_igris.py --dias 365 --watchdog --workers 2 --sleep 0.2
```

### Solo spots (sin lineal/inverso) — Coliseo clásico

```
python scripts/jess_boveda_coliseo_noche.py --dias 365 --watchdog
```

(o el mismo historial con `--solo-spot`)

---

## Opcional — Kaiser más frecuente de noche (no bloquea)

Solo si sobra máquina y el Monarca pidió pulso `lineal_vs_inverse` más denso.  
**Otro terminal.** Manos OFF. No es bóveda de velas.

```
# Ejemplo: ojos vivos ~8h con muestreo Kaiser cada 15s (default suele ser 60s)
# Ajustar según .env / config de la forja Jess:
KAISER_SAMPLE_INTERVAL_S=15 python scripts/arise_ojos_tusk.py
```

Si no existe ese ritual en la máquina o la CPU se indigna: **omitir**. La bóveda de velas es la misión principal.

*(Kaiser a 1s / memoria barcos no es foco de esta noche.)*

---

## Relación con otros rituales

| Ritual | Qué hace | Manos |
|--------|----------|-------|
| **Esta noche (historial Igris)** | Llena velas 1m flota manto + spots | OFF |
| Coliseo solo-spot | Igual motor, solo spot (teatro Fantasma) | OFF |
| 4.0.3 Asalto | Igris live despliega manto | ON (orden Monarca) |

Camino Asalto: [`PEGAR_JESS_IGRIS_LIVE_ASALTO.md`](PEGAR_JESS_IGRIS_LIVE_ASALTO.md).
