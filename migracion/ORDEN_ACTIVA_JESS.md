# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`

---

## 1) Arranque (rama de esta misión)

```
git fetch origin
git checkout orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md scripts/jess_boveda_coliseo_noche.py data/coliseo/rango_top100_jess.txt data/coliseo/rango_top100_jess_hasta44.txt data/coliseo/rango_top100_usa_cola_jess.txt data/coliseo/INSTRUCCIONES_MERGE_RANGO_TOP100.md
```

Confirmar: `scripts/jess_boveda_coliseo_noche.py`

---

## 2) Misión — Jess hasta #44 (PLUME inclusive)

Tu lista oficial son los **primeros 44** de `rango_top100_jess.txt` (índices 0–43), hasta **PLUME** inclusive.  
Archivo listo: `data/coliseo/rango_top100_jess_hasta44.txt`

**USA** ya terminó su top50 propio y ahora baja **solo los últimos 6 de tu lista, de abajo hacia arriba**:

`PENDLE,STRK,JUP,DASH,SPX,PNUT`

No bajes esos 6. Tú te detienes en **PLUME**.

### Comando (reanuda checkpoint — solo hasta #44)

```
python -u scripts/jess_boveda_coliseo_noche.py --dias 365 --interval 1 --markets linear --workers 3 --sleep 0.12 --watchdog --ritual rango_top100_jess --only AKE,1000BONK,MAGMA,FIL,PEOPLE,RED,KAITO,CASHCAT,GALA,VIRTUAL,ONT,INJ,ATOM,BIO,TRX,POL,ETHFI,TUT,OP,SHIB1000,ICP,GRASS,CHIP,GRAM,H,PRL,VVV,VELVET,AERO,MET,ZRO,USELESS,ETC,JTO,CAP,TIA,MORPHO,SEI,CYS,LDO,GPS,ALGO,STABLE,PLUME
```

Al terminar: zip → Drive → avisar Monarca.

---

## 3) Qué NO hacer

- No manos / arise / Igris.
- No subir `.env`.
- No borrar bóvedas.
- No bajar `PNUT,SPX,DASH,JUP,STRK,PENDLE` (esos van por USA, cola de abajo).

---

## 4) Qué mirar

1. `PROGRESO.md`: bases AKE…PLUME en ok (44).
2. Zip en Drive + aviso.

---

## 5) HECHO

- [ ] 44 bases hasta PLUME en ok (o huecos rematados)
- [ ] Zip en Drive + aviso al Monarca

---

*Shadow Army · Jess #1–44 hasta PLUME · USA cola 6 abajo→arriba*
