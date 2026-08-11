# Checkpoint — Soladura ranking / peaje IM (2026-08-11)

**Manos Igris:** atadas (sin arise, sin mordida live, sin bisturí en campo).

## Veredicto

El peaje del ranking ya no miente con el *promedio* de apalancamiento. Cada pierna (inversa + lineal) paga su propio peaje. El muro de oxígeno del pase cuadra con la corona **Brujo \$1673** y **Chamán \$3735**. Si un Santo ya pesa más de lo que el paso pide, el director dice *no engordes más* (`OVERSHOOT_RANKING`).

## Qué se soldó

1. **Apalancamientos** — tabla del ejército alineada con la BD local de Bybit (modo frío; en USA a veces 403). Foco LINK/AVAX/OP/LTC/SOL/ETH: techos coinciden.
2. **Peaje** — IM = notional/lev_inv + notional/lev_lin. Promedio solo fantasma de pantalla vieja.
3. **Altar** — muestra lev inv / lev lin + IM por pierna; nota de peaje honesta.
4. **Doctrina Beru** — actualizada a pierna a pierna + corona viva.
5. **Candado engorde** — `have > need` → restante 0 + telemetría `OVERSHOOT_RANKING` (sin órdenes).
6. **Smoke** — `scripts/validar_pase_im_ranking_smoke.py` (muro 95%, techos, peaje LINK/AVAX/OP, candado).

## Overshoot en campo (lectura fría)

Con el libro vivo actual (equity ~\$1528) y posiciones que el ojo USA ve en cero en el snapshot frío revisado aquí: **no hay lista de overshoot vivo en ese corte**. Sellos forzados siguen: **28, 34, 35** (ADA Cap + OP Cap/Gen). Nivelar el manto en mainnet sigue **prohibido** hasta orden del Monarca; el bisturí dry-run puede listar cortes cuando haya masa real que recortar.

## Qué sigue

Jess (México): sync vivo de techos/mínimos si la BD local envejeciera. Luego, cuando el Monarca abra manos, Igris respeta meta + candado ranking — sin hinchar Santos por encima del pase.
