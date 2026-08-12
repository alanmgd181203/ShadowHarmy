# Informe Beru — Cursor del Monarca

**Fecha:** 2026-08-12 · Checklist **4.0.4**

## Qué hace Beru

Cazador de **spot** (casa). Planta una semilla en un Santo, pone el 0 al precio del momento (wake), espera que el precio se aleje ~**1,6 %** (Capitán Normal) y muerde ~**peaje mínimo** del Santo (MNT ≈ **$5**). Luego puede cosechar.

**No** engorda el manto de Igris. **No** apalanca margen. Ley: neutro + engorde OFF.

## Qué se cableó hoy

1. **Nivel 2 — fantasma:** ojos reales, cerebro late, **cero órdenes**. Bitácora `[BERU_FANTASMA]`. Parches: ojos estrechos, muleta REST si cae el torrente, caza por Santo del barco, corte sin zombie.  
   Run OK: siembra ADA/BCH/MNT · 1 “disparo” fantasma MNT · sellado limpio.

2. **Nivel 3 — manos chiquitas:** misma cabeza, **1 orden real** acotada (MNT, solo LONG, techo 1 caza, ~$5). Consola `[BERU_LIVE]`.  
   Run 15 min: sembró y acechó · **0 fills** (precio quieto + IP de la llave bloqueada). Sellado limpio. Ritual listo; fill real **pendiente**.

## Simulación / fantasma vs mainnet

| | Fantasma (nivel 2) | Mainnet chiquito (nivel 3) |
|--|--------------------|----------------------------|
| Precios | Reales | Reales |
| Orden a Bybit | No | Sí (~$5) |
| Para qué | Probar cerebro y ojos | Probar manos de verdad |
| Comando | `arise_beru_fantasma.py` | `arise_beru_manos_chiquitas.py` |

**Ejército libre (Beru ON dentro de arise Igris):** aún no. Manos OFF salvo ritual nivel 3 o mandato explícito.

## Estado ahora

- Cableado OK · smokes OK  
- 4.0.4 `[~]` hasta fill real o decisión Monarca  
- Bloqueo: **whitelist IP** Bybit (error 10010)  
- Siguiente: IP OK → relanzar nivel 3 → buscar `ORDEN_OK` en consola

## Rituales

```
python3 scripts/arise_beru_fantasma.py --segundos 1200
python3 scripts/arise_beru_manos_chiquitas.py --segundos 900
```

Checkpoints: `CHECKPOINT_BERU_FANTASMA_2026-08-12.md` · `CHECKPOINT_BERU_MANOS_CHIQUITAS_2026-08-12.md`  
Doctrina: `22_DOCTRINA_BERU.md`
