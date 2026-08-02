# Informe Monarca — sesgo estructural vs índice

**Fecha:** 2026-08-02  
**Estado del cable:** frecuencia/ETA del manto e Igris (puerta) ya miden **exceso vs cero estructural** (`MANTO_CERO_ESTRUCTURAL=true`).  
**Estado de los números:** la tabla completa y viva está en la **Mac de Jess** (ritual ojos + backfill). Desde este PC Bybit responde 403 (geo/rate USA), así que aquí no se pudo refrescar el histórico real.

---

## Qué debes saber (sin rodeos)

Kaiser ya sabe medir el sesgo de cada mar vs el índice. Lo que **faltaba** —y ya se cableó— es que el reloj del manto y el disparo de Igris **no traten el gap eterno como oportunidad**.

Ejemplo de la trampa (forma típica):

- Inverso suele ir **un poco barato** vs índice.  
- Lineal un poco caro o pegado.  
- El spread lineal↔inverso se ve “bonito” casi siempre → el cálculo viejo decía “oportunidad todo el día” → ETA corto = ansiedad disfrazada.

Con cero estructural: solo cuenta cuando el spread **se aleja** de ese clima normal. Oportunidades **menos frecuentes**, tiempos de espera **más largos**, según la marcha (Táctico / Forzada / Asalto).

Smoke de prueba en cuartel: con gap eterno pegado al cero, el legado contaba **40/40** muestras; con cero, **0/40**.

---

## Cómo sacar TU informe con números reales (Jess)

En la Mac donde corren los ojos (memoria ya caliente):

```bash
cd ~/ruta/ShadowHarmy
git pull
python scripts/informe_sesgo_monarca.py
# opcional refresco:
python scripts/informe_sesgo_monarca.py --backfill --dias 30
```

Eso escribe:

- `migracion/INFORME_SESGO_ESTRUCTURAL.md` (esta hoja, actualizada)  
- `data/informe_sesgo_estructural.json` (máquina)

Ahí verás por base: cero spot / lineal / inverso y el **gap estructural lineal−inverso** (el que alimenta el manto).

---

## Lectura rápida de la marcha

| Marcha | Qué exige encima del cero |
|--------|---------------------------|
| **Táctico** | exceso ≥ fees enteros |
| **Marcha Forzada** | exceso ≥ ½ fees |
| **Asalto** | exceso ≥ casi nada (tablas) — sigue siendo *exceso*, no el gap eterno |

---

## Flags

- `MANTO_CERO_ESTRUCTURAL=true` (default) — cable activo  
- Apagar solo para comparar legado / arena

---

*Generador: `scripts/informe_sesgo_monarca.py` · doctrina: `CHECKPOINT_KAISER_INDICE_SESGO.md`*
