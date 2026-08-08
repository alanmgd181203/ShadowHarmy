# PEGAR Jess — 4.0.3 Igris live bajo Asalto (México corre · USA no ejecuta)

> **Puerta oficial:** [`ORDEN_ACTIVA_JESS.md`](ORDEN_ACTIVA_JESS.md) — este archivo es **receta/anexo**, no la puerta.

**Para:** Cursor / terminal en la Mac de Jess (México)  
**Ley:** preferencia **Asalto** (2026-08-06). Igris ≠ Greed. Hibernan Greed y Beru.  
**Ritmo:** tras cada dual **exitoso** de engorde/bootstrap, Igris espera ≥**5 s** (`IGRIS_ENGORDE_RITMO_S`) antes del siguiente dual del **mismo Santo**. No ametralladora cada ~1 s (protege libro / spread). Fallo de puerta ya tenía ~5 s; mismo espíritu.  
**USA laptop:** solo sello / panel cableado — **no** corre arise ni manos.

```
git pull origin master

# Marcha Asalto (si el disco no está ya en asalto)
python3 scripts/set_marcha_cli.py --id asalto

# Opcional: smoke frío solo-ojos (~90s) — sin manos Igris
# python3 scripts/arise_igris.py --solo-ojos --segundos 90

# GO bajo guardián + flag mainnet (manos reales — orden Monarca)
python3 scripts/vigilar_arise_igris.py --confirmar-go \
  --durar-hasta 2026-08-07T18:30:00 --permitir-mainnet-manos
```

## Mirar

- Panel / Pergamino / Ascensión Tusk: marcha **Asalto**, ventana 48–52, meta engorde, O₂ / equity Tusk.
- `data/estado_vivo.json` → bloques `igris.marcha` · `ventana_manto` · `meta_engorde` · `ley_masa` · `tusk_tesoreria`.
- Heartbeat: `data/logs/arise_igris/heartbeat.json`
- Parte al sellar: `data/arise_igris_report.json`
- Engorde: duales del mismo Santo **espaciados ≥5 s** (no ráfaga de latido)

## Checklist al Monarca

- Ojos VERDE + libros ETH
- Marcha = **asalto**
- Engorde / restante meta del paso · **ritmo ≥5s entre duales** (mismo Santo)
- Greed · Beru hibernados
- Panel refleja estado_vivo (sin números inventados)

Detalle ritual: `CHECKPOINT_IGRIS_LIVE_4_0_3.md` · ley Asalto: `CHECKPOINT_LEY_IGRIS_ASALTO_2026-08-06.md`
