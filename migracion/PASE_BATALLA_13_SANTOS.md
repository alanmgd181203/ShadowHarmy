# Pase de batalla — 13 Santos del Grial

**Firma Monarca:** 2026-07-19  
**Fuente:** Mega Coliseo (vacío Adán **1,6 %**, malla **normal** ×1) + costo Igris (`X` = margen L+S + colchón Tusk 5 %).  
**Código espejo:** `core/plan_crecimiento.py` · UI `ui/ascensionScaffold.js`

---

## Doctrina corta

1. El **Coliseo** dice *quién pelea bien* (efi).  
2. **Igris** dice *cuánto tesoro come el manto* (capital del barco por grado).  
3. El pase ordena cada paso por **efi / dólar Igris**, sin saltar rangos Beru del mismo Santo (Soldado → Caballero → General → Mariscal).  
4. Entre Santos **sí** se mezcla (p. ej. AVAX Caballero antes que FIL Soldado).

**13 Santos (sillas fijas):**  
MNT · LINK · AVAX · LTC · HYPE · BCH · XRP · SOL · ETH · ADA · AAVE · FIL · OP

**Meta teórica (13 Mariscales):** **~$3161** de capital Igris acumulado.

---

## Rangos de cuenta (sobre el pase)

| Rango | Pasos | Cierra en | Techo acum. ~$ |
|-------|------:|-----------|---------------:|
| **Aspirante** | 1 → 5 | LTC Soldado | **123** |
| **Aprendiz** | 6 → 13 | OP Soldado | **411** |
| **Brujo** | 14 → 27 | LTC Mariscal | **1451** |
| **Chamán** | 28 → 52 | XRP Mariscal (13 Mariscales) | **3161** |

Más allá de Chamán: Capitán / General / Señor de las Sombras (horizonte sin tallar en este pase).

---

## Tabla del pase (52 pasos)

Costo = Δ capital Igris del barco al subir de grado (o despertar).

| # | Paso | +$ | Acum. $ | Rango cuenta |
|--:|------|---:|--------:|--------------|
| 1 | ETH → Soldado | 14 | 14 | Aspirante |
| 2 | HYPE → Soldado | 28 | 42 | Aspirante |
| 3 | XRP → Soldado | 18 | 60 | Aspirante |
| 4 | MNT → Soldado | 36 | 96 | Aspirante |
| 5 | LTC → Soldado | 27 | **123** | Aspirante *(corona)* |
| 6 | SOL → Soldado | 18 | 141 | Aprendiz |
| 7 | LINK → Soldado | 38 | 179 | Aprendiz |
| 8 | ADA → Soldado | 22 | 201 | Aprendiz |
| 9 | BCH → Soldado | 38 | 239 | Aprendiz |
| 10 | AVAX → Soldado | 38 | 277 | Aprendiz |
| 11 | AVAX → Caballero | 37 | 314 | Aprendiz |
| 12 | FIL → Soldado | 59 | 373 | Aprendiz |
| 13 | OP → Soldado | 38 | **411** | Aprendiz *(corona)* |
| 14 | LINK → Caballero | 37 | 448 | Brujo |
| 15 | LINK → General | 75 | 523 | Brujo |
| 16 | LINK → Mariscal | 151 | 674 | Brujo |
| 17 | SOL → Caballero | 17 | 691 | Brujo |
| 18 | SOL → General | 35 | 726 | Brujo |
| 19 | SOL → Mariscal | 70 | 796 | Brujo |
| 20 | MNT → Caballero | 34 | 830 | Brujo |
| 21 | MNT → General | 70 | 900 | Brujo |
| 22 | MNT → Mariscal | 141 | 1041 | Brujo |
| 23 | AVAX → General | 75 | 1116 | Brujo |
| 24 | AVAX → Mariscal | 151 | 1267 | Brujo |
| 25 | LTC → Caballero | 26 | 1293 | Brujo |
| 26 | LTC → General | 52 | 1345 | Brujo |
| 27 | LTC → Mariscal | 106 | **1451** | Brujo *(corona)* |
| 28 | ADA → Caballero | 20 | 1471 | Chamán |
| 29 | ADA → General | 42 | 1513 | Chamán |
| 30 | ADA → Mariscal | 84 | 1597 | Chamán |
| 31 | BCH → Caballero | 37 | 1634 | Chamán |
| 32 | BCH → General | 75 | 1709 | Chamán |
| 33 | BCH → Mariscal | 151 | 1860 | Chamán |
| 34 | OP → Caballero | 37 | 1897 | Chamán |
| 35 | OP → General | 75 | 1972 | Chamán |
| 36 | OP → Mariscal | 151 | 2123 | Chamán |
| 37 | ETH → Caballero | 12 | 2135 | Chamán |
| 38 | ETH → General | 27 | 2162 | Chamán |
| 39 | ETH → Mariscal | 52 | 2214 | Chamán |
| 40 | AAVE → Soldado | 28 | 2242 | Chamán |
| 41 | AAVE → Caballero | 27 | 2269 | Chamán |
| 42 | FIL → Caballero | 58 | 2327 | Chamán |
| 43 | FIL → General | 117 | 2444 | Chamán |
| 44 | FIL → Mariscal | 234 | 2678 | Chamán |
| 45 | AAVE → General | 56 | 2734 | Chamán |
| 46 | AAVE → Mariscal | 111 | 2845 | Chamán |
| 47 | HYPE → Caballero | 27 | 2872 | Chamán |
| 48 | HYPE → General | 56 | 2928 | Chamán |
| 49 | HYPE → Mariscal | 111 | 3039 | Chamán |
| 50 | XRP → Caballero | 17 | 3056 | Chamán |
| 51 | XRP → General | 35 | 3091 | Chamán |
| 52 | XRP → Mariscal | 70 | **3161** | Chamán *(meta teórica)* |

---

## Notas de guerra

- **HYPE y XRP** en Mariscal: el Coliseo los castiga vs quedarse Soldado. En este pase teórico **sí** se suben al final (pasos 47–52) porque el Monarca pidió meta = 13 Mariscales. En despliegue vivo conviene **parar en Soldado** salvo override.  
- **FIL** es el Santo más caro (Mariscal $468) — por eso asciende tarde.  
- **AAVE** ocupa silla 13; efi/dólar floja — cola del Chamán.  
- Costo **no** es el margen de volumen del teatro Coliseo (~$1–7); es **X Igris** del diccionario.

---

## Jobs Coliseo de referencia

`data/coliseo/mega/jobs/x1__tier__v1p6__{BERUBBY|PROTO2|PROTO1|PLENO}__{ACTIVO}.json`  
Vacío dorado firmado: **1,6 %** (segundo dorado; alineado Normal en `22`).

---

*Actualizar este pergamino si el Monarca cambia cortes de rango o la lista de Santos.*
