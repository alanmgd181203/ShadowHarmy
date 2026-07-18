# Jess — Bóveda Coliseo + Beru Fantasma (noche México)

**Para:** Cursor en la Mac de Jess  
**Por qué:** la forja del Monarca tiene HTTP 403 a Bybit. México descarga la memoria; el teatro se reparte.

---

## Orden de batallas

1. **Ya hecho:** sync lev + mínimos (`jess_sincronizar_bybit_mexico.py`).
2. **Esta noche:** Gran Consumo spot **1m** (bóveda) + ranking Normal **1,6 %**.
3. **Día siguiente:** Monarca (y/o Jess) corre Ansiedad / barrido de vacíos **sin** Bybit, sobre el pack Drive.

---

## Mandato listo para pegar en Cursor (Agent) — NOCHE

```
Actualiza el repo y deja corriendo el ritual nocturno del Coliseo (bóveda spot 1m).

1) git pull origin master

2) Deja la laptop conectada a corriente y sin dormir.
   Ejecuta EN UN TERMINAL (toda la noche):

python scripts/jess_boveda_coliseo_noche.py --dias 365 --watchdog

   - Descarga velas spot USDT 1m de la flota Beru (~22 activos, ~1 año)
   - Vigilante cada 10 min: si se cae o se congela, reanuda solo
   - Al terminar: ranking Beru Fantasma Normal (vacío 1.6%) + zip para Drive

3) Por la mañana revisa:
   - data/coliseo/PROGRESO.md
   - data/coliseo/MANIFIESTO.md
   - data/coliseo/ranking_normal_1p6.md
   - data/coliseo/ShadowHarmy_Coliseo_*.zip

4) Sube el ZIP (o la carpeta data/coliseo) a Google Drive y avisa al Monarca.

NO subas el sqlite/zip enorme a GitHub.
NO subas Ima/, tools/, videos ni logs basura.
Si quieres commit solo de scripts/docs que hayan cambiado localmente, OK —
pero la bóveda NO va a git.
```

### Si se cae a media noche (manual)

```
python scripts/jess_boveda_coliseo_noche.py --dias 365 --once
```

Es **reanudable**: sigue desde el checkpoint.

---

## Mandato Monarca — teatro paralelo (después del Drive)

```
1) Copia el pack a data/coliseo/ (bóveda sqlite + manifiestos)

2) Barrido Ansiedad / número dorado (sin Bybit):

python scripts/coliseo_beru_fantasma.py --vacios 0.010,0.012,0.016,0.020

3) Compara ranking_*.md — métrica corona = botín neto / dólar de manto
   Semáforos: día / semana / año · calor (semana manda 50%)
```

Jess puede correr solo `0.016` (ya lo hace la noche) o repetir `0.012` si sobra CPU.

---

## Qué hay dentro

| Pieza | Rol |
|-------|-----|
| `data/coliseo/boveda_spot_1m.sqlite` | Memoria OHLC 1m |
| Latidos 0,05 % | Los fabrica el Fantasma al simular (path peor de dos caminos) |
| Fees | Fee spot rail (~0,1 %/pierna) restado del botín |
| Calor | Como Kaiser: semana manda, año confirma, día testigo |

## Notas honestas

- El Fantasma es **replay simplificado** (cazador + cosechas), no el Beru vivo completo con Mega/fusión.
- Sirve para **ranking relativo** y buscar el vacío dorado; no para PnL contable exacto.
- Piso de datos: si un activo tiene pocas velas → semáforo GRIS / DATOS_INSUFICIENTES.
