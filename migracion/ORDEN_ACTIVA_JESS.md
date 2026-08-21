# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`

---

## 1) Arranque (rama de esta misión)

```
git fetch origin
git checkout orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md scripts/jess_boveda_coliseo_noche.py data/coliseo/rango_top100_jess.txt data/coliseo/rango_top100_usa_cola_jess.txt data/coliseo/rango_top100_jess_resto.txt data/coliseo/INSTRUCCIONES_MERGE_RANGO_TOP100.md
```

Confirmar: `scripts/jess_boveda_coliseo_noche.py`

---

## 2) Misión — Remate Jess (lo que te falte)

Monarca USA **ya terminó** ranks 1–50 y ahora baja **de abajo hacia arriba** los 14 que te faltaban:

`PENDLE,STRK,JUP,DASH,SPX,PNUT,PLUME,STABLE,ALGO,GPS,LDO,CYS,SEI,MORPHO`

**Tú:** sigue bajando **solo lo que te falte** de tu lista (si vas en ~36/50, prioriza huecos de **AKE…TIA**). Si el ritual ya iba en MORPHO…PENDLE, puedes dejarlo: el merge tolera duplicados.

### Comando (reanuda checkpoint — misma lista completa OK)

```
python -u scripts/jess_boveda_coliseo_noche.py --dias 365 --interval 1 --markets linear --workers 3 --sleep 0.12 --watchdog --ritual rango_top100_jess --only AKE,1000BONK,MAGMA,FIL,PEOPLE,RED,KAITO,CASHCAT,GALA,VIRTUAL,ONT,INJ,ATOM,BIO,TRX,POL,ETHFI,TUT,OP,SHIB1000,ICP,GRASS,CHIP,GRAM,H,PRL,VVV,VELVET,AERO,MET,ZRO,USELESS,ETC,JTO,CAP,TIA,MORPHO,SEI,CYS,LDO,GPS,ALGO,STABLE,PLUME,PNUT,SPX,DASH,JUP,STRK,PENDLE
```

O, si quieres **solo rematar huecos del frente** (primeros 36):

```
python -u scripts/jess_boveda_coliseo_noche.py --dias 365 --interval 1 --markets linear --workers 3 --sleep 0.12 --watchdog --ritual rango_top100_jess_frente --only AKE,1000BONK,MAGMA,FIL,PEOPLE,RED,KAITO,CASHCAT,GALA,VIRTUAL,ONT,INJ,ATOM,BIO,TRX,POL,ETHFI,TUT,OP,SHIB1000,ICP,GRASS,CHIP,GRAM,H,PRL,VVV,VELVET,AERO,MET,ZRO,USELESS,ETC,JTO,CAP,TIA
```

Al terminar: zip → Drive → avisar Monarca.

---

## 3) Qué NO hacer

- No manos / arise / Igris.
- No subir `.env`.
- No borrar bóvedas.

---

## 4) Qué mirar

1. `PROGRESO.md`: bases en ok.
2. Zip en Drive + aviso.

---

## 5) HECHO

- [ ] Huecos Jess rematados (o lista completa ok)
- [ ] Zip en Drive + aviso al Monarca

---

*Shadow Army · remate top100 · Jess frente + USA cola abajo→arriba*
