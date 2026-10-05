# Escudo BTC — lateral artificial para Beru (viejita)

**Estado:** portado a la viejita por orden del Monarca (2026-09-23) · lab NuevoBeru sigue siendo el teatro.  
**Beru no se toca.** Igris Escudo BTC es **otro oficio** que el manto clásico L/S por Santo.

---

## Idea en una frase

Beru sigue cazando rango en alts. Igris mira la **masa abierta** de Beru (balanza L/S sin BTC) y planta un **escudo en BTC** del lado contrario × relación R. Cosecha Oz → masa baja → Igris achica. Engorde → Igris aumenta.

---

## Convivencia en la viejita (cómo probar)

1. Beru caza como siempre (campamento / manos piedra).  
2. La balanza sella el oído (`balanza_legion`).  
3. Escudo latea en **papel** (libro sim) — **no** abre BTC real hasta GO + `LIVE_OK`.

### Despertar desde 0 (mandato Monarca)

El ejército nace **sin memoria**: Beru con semilla nueva (`--desde-cero`) e Igris
con el libro del escudo en cero (sin ancla, sin peldaño armado, sin papel BTC).

0. Al prender la viejita (todo OFF, sin memoria)::

```
python scripts/sellar_viejita_parada_limpia.py
```

1. Preparar con escudo listo (opcional; enciende ACTIVO en esa sesión)::

```
python scripts/preparar_despertar_con_escudo.py
```

2. Despertar campamento con escudo listo::

```
python scripts/arise_beru_rango_campamento.py --santos A,B,C --manos-go --desde-cero --con-escudo
```

Igris **espera** hasta que la masa abierta cruce el primer umbral (**$400** neto
en peldaños). Luego va **desplegando** el manto BTC en papel conforme Beru engorda,
y lo **achica** cuando Oz diluye. No es el manto L/S clásico por Santo.

Ritual a mano (oído)::

```
python scripts/vigilar_escudo_btc_convivencia.py --una-vez
python scripts/vigilar_escudo_btc_convivencia.py 60
```

Dentro del campamento: `--con-escudo` o `IGRIS_ESCUDO_BTC_ACTIVO=1`.

---

## Relación R

| Modo | Cómo | Nota |
|------|------|------|
| Fija | `IGRIS_ESCUDO_BTC_R=1.0` (u otro número) | Lab / teatro |
| Dinámica | `IGRIS_ESCUDO_BTC_R=dinamico` | TOTAL3/BTC + under-hedging (−0.2, piso 1.0) — default del ritual convivencia |

---

## Dónde se despliega el manto (frente)

Peldaños doctrinales: **de $200 en $200** · primer armado a **$400**. Verificado OKX público 2026-09-23:

| Familia | Frente OKX | Paso mínimo | ¿Sirve peldaño $200? |
|---------|------------|-------------|----------------------|
| **inverso USD** ✅ | `BTC-USD-SWAP` | **$10 fijo** (`0.1×ctVal100`) | Sí — 20 pasos exactos |
| **lineal USDT** | `BTC-USDT-SWAP` | ~**$10** @ BTC 100k | Sí, pero el $ deriva con el precio |
| **USDC** | `BTC-USDC-SWAP` **no existe** en OKX | — | Fuera |

**Tarifas:** OKX no rebaja peaje por liquidar en USDC vs USDT. El peaje va por VIP / volumen / equity de cuenta — misma tabla de futuros. No hay atajo USDC.

**Sellado Monarca 2026-09-23:** frente = **inverso OKX** (`IGRIS_ESCUDO_BTC_FRENTE=inverso`).  
Paso fijo $10 · peldaños de **$200** · arma a **$400** · margen/PnL en BTC.

---

## Separación de oficios (anti-tumor)

| Pieza | Rol |
|-------|-----|
| **Beru** | Rango, Oz, Red, sangre. No mira BTC. |
| **Igris Escudo BTC** | Sigue acumulado Beru → meta BTC (papel primero). |
| **Igris Manto clásico** | L/S por Santo. **No mezclar** con el escudo. |
| **Greed / Tusk** | Fuera del escudo v1 / oxígeno después. |

---

## Candados

- `IGRIS_ESCUDO_BTC_MODO=sim` (default).  
- Live: `IGRIS_ESCUDO_BTC_MODO=live` **y** `IGRIS_ESCUDO_BTC_LIVE_OK=1`.  
- **Manos OKX cableadas** en `BTC-USD-SWAP`: siempre **limit** + amend si no llena.  
  Nunca market. Sin `LIVE_OK` no sale ni una orden.  
- **Si el límite no llena:** Igris lo **acerca** al precio cada ~20 s (pasos chicos).  
- USA no dispara live del escudo sin orden explícita del Monarca.

---

## Origen lab

Diseño y teatro serio viven en `ShadowHarmy_NuevoBeru` (teatro LTC ×10, informes Gemini).  
La viejita recibe el **contador + ojos + papel** para convivencia real de casa.
