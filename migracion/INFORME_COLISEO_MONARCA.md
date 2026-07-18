# Informe del Coliseo — Beru Fantasma (para el Monarca)

**Fecha:** 2026-07-18  
**Qué es:** el teatro donde Beru pelea en el pasado (bóveda de Jess) para saber qué barcos merecen oxígeno.

---

## Qué quedó listo

1. **Bóveda en su sitio** — `data/coliseo/boveda_spot_1m.sqlite`  
   Los 22 spots · 1 minuto · 1 año que bajó Jess.

2. **Beru Fantasma v2 (al 100 % de un barco)**  
   Ya no es solo “salir a cazar una vez”. Ahora el fantasma hace:
   - **Caza real** (engorda en la red, cosecha en la oz)
   - **Negociador** (pelotea sin engordar)
   - **Ciclo infinito** (red → espera gatillo → caza fantasma sin engorde → otra vez negociador)

   **No** simula fusiones ni Mega Beru (eso es cuando varios Berus del mismo activo se juntan; aquí cada activo pelea **solo**).

3. **Barrido del Vacío de Adán**  
   Prueba: **0,6 % · 0,8 % · 1,0 % · 1,2 % · 1,4 % · 1,6 % · 1,8 % · 2,0 %**  
   El “abismo” del negociador va **amarrado** al mismo vacío (una sola perilla), para buscar el Adán perfecto sin mezclar dos diales.

4. **Cómo se corona al ganador**  
   - Botín **después** de comisiones ÷ **dólares de manto** (margen del diccionario vivo)  
   - Tres miradas: **día · semana · año**  
   - **Calor** = 20 % día + **50 % semana** + 30 % año  
   - Semáforos verde / amarillo / rojo por terciles

5. **Fricción**  
   - Comisión **0,1 %** por pierna (ida y vuelta ≈ 0,2 %) — pesimista a propósito  
   - **Slippage 2 bps** por defecto (el precio “real” un poquito peor que el latido) — se puede cambiar

6. **Latidos**  
   Velas de 1 minuto → pasos de **0,05 %**.  
   Política **min**: prueba dos caminos dentro del minuto y se queda con el **peor** resultado (no se autoengaña).

---

## Cómo lo corres tú (forja, sin Bybit)

Prueba corta (2 activos, 2 vacíos, “año” = 30 días):

```text
python scripts/coliseo_beru_fantasma.py --only BTC,ETH --vacios 0.012,0.016 --quick
```

Barrido completo (puede tardar; deja la laptop trabajando):

```text
python scripts/coliseo_beru_fantasma.py
```

Salidas en `data/coliseo/`:
- `ranking_v1p2.md` (y los demás vacíos)
- `comparativa_vacios.md` ← **mira este** para el vacío dorado de la flota y el óptimo por activo

Más rápido (menos castigo de camino): `--path-policy ohlc`  
Sin slippage: `--slip-bps 0`  
Más slippage: `--slip-bps 5`

---

## Qué puedes modificar después (perillas)

| Perilla | Qué mueve | Dónde |
|---------|-----------|--------|
| Lista de vacíos | Buscar Adán más fino | `--vacios 0.011,0.012,0.013…` |
| Comisión | Más/menos dura | `--fee-pct 0.001` |
| Slippage | Realismo de fill | `--slip-bps` |
| Camino OHLC | Honestidad vs velocidad | `--path-policy min\|ohlc` |
| Pesos del calor | Si semana debe mandar más | en código `PESOS_CALOR` (hoy 20/50/30, firmado) |
| Abismo ≠ vacío | Si quieres desacoplar negociador | hoy van juntos a propósito |

---

## Lectura honesta de los números

Puedes ver **eficiencias negativas**. No es un bug del ranking: con fee 0,2 % ida-vuelta, cosechas muy chicas (≈0,1 %) **pierden** dinero. Beru solo “gana” de verdad cuando el movimiento capturado (o el engorde) supera esa fricción.  

Para decidir despertar, mira el **orden** (quién sangra menos / quién rinde más), el **calor**, y la **comparativa de vacíos** — no un dólar contable de Bybit.

---

## Qué no hace (a propósito)

- No manda órdenes reales  
- No fusiona Berus  
- No es el código vivo de `generales/beru.py` línea por línea (es el mismo **espíritu** de doctrina, en teatro)  
- El Pergamino aún no muestra estos rankings (eso sería después)

---

## Siguiente paso del camino

1. Correr el barrido completo cuando tengas tiempo de máquina.  
2. Leer `comparativa_vacios.md`: vacío dorado de flota + óptimo por barco.  
3. Con eso, decidir semilla / orden de Ascensión Aprendiz con evidencia (checklist **5.3.3**).

Si algo del teatro no cuadra con cómo tú sientes la batalla real de Beru (pasos del negociador, abismo fijo 2 % en vez de acoplado, etc.), se retoca la perilla y se vuelve a correr — la bóveda ya no hay que bajarla otra vez.
