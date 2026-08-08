# Jess — Bóveda Coliseo (noche México · SOLO descarga)

> **Puerta oficial:** [`ORDEN_ACTIVA_JESS.md`](ORDEN_ACTIVA_JESS.md) — este archivo es **receta/anexo**, no la puerta.

**Para:** Cursor en la Mac de Jess  
**Objetivo de esta noche (Coliseo clásico):** armar la bóveda **spot** 1m lo más rápido posible.  
**No** simular Beru Fantasma ahora — eso es mañana en paralelo (Monarca + Jess).

---

## Noche historial flota Igris (mandato preferido)

Si el Monarca pide **llenar historial/gráficas de la flota Igris** (spots **+** lineal/inverso del manto), usa el pergamino:

→ **[`PEGAR_JESS_NOCHE_HISTORIAL_IGRIS.md`](PEGAR_JESS_NOCHE_HISTORIAL_IGRIS.md)**

```
python scripts/jess_noche_historial_igris.py --dias 365 --watchdog
```

Eso es **función del ejército de noche**, **no** el live **4.0.3 Asalto** (manos).  
Este documento abajo sigue siendo el Coliseo **solo-spot** (compat / teatro Fantasma).

---

## Mandato listo para pegar en Cursor (Agent) — NOCHE SOLO SPOT

```
Actualiza el repo y deja corriendo SOLO la descarga de la bóveda Coliseo (spot).

1) git status && git pull origin master

2) Laptop en corriente, sin dormir. Un solo terminal:

python scripts/jess_boveda_coliseo_noche.py --dias 365 --watchdog

   Por defecto:
   - Solo Gran Consumo (spot USDT 1m, ~22 barcos, ~1 año)
   - 3 puentes en paralelo (activos distintos)
   - Vigilante cada 10 min (si se cae, reanuda)
   - Al terminar: zip en data/coliseo/ para Drive
   - SIN ranking / SIN simulación

3) Por la mañana revisa:
   - data/coliseo/PROGRESO.md  (todas las bases OK)
   - data/coliseo/MANIFIESTO.md
   - data/coliseo/ShadowHarmy_Coliseo_*.zip

4) Sube el ZIP (o la carpeta data/coliseo) a Google Drive y avisa al Monarca.

NO subas el sqlite/zip a GitHub.
NO subas Ima/, tools/, videos ni logs.
```

### Si se cae a media noche

```
python scripts/jess_boveda_coliseo_noche.py --dias 365 --once
```

Es reanudable (checkpoint). El vigilante ya lo relanza solo si usaste `--watchdog`.

### Si Bybit frena mucho (429 / errores)

Bajar presión a 2 puentes:

```
python scripts/jess_boveda_coliseo_noche.py --dias 365 --watchdog --workers 2 --sleep 0.2
```

### Solo si sobra tiempo y quieren ranking esa misma noche

```
python scripts/jess_boveda_coliseo_noche.py --dias 365 --once --with-ranking
```

(No es el plan: el Monarca prefiere teatro paralelo mañana.)

---

## Mandato Monarca — teatro (después del Drive)

```
1) Copia el pack a data/coliseo/

2) Barrido (sin Bybit):

python scripts/coliseo_beru_fantasma.py --vacios 0.010,0.012,0.016,0.020

3) Compara ranking_*.md — botín neto / dólar de manto
```

---

## Por qué debería tardar menos

| Antes | Ahora |
|-------|--------|
| 1 activo a la vez | **3** activos en paralelo |
| Simulación al final | **Omitida** (default) |
| sleep 0.25s | sleep **0.12s** + backoff solo si falla |

Estimación orientativa (solo spot): de ~1–3 h según red/límites Bybit.  
Historial Igris (spot+L+S) tarda más — ~3× los pares. Si tarda de más, usar `--workers 2`.
