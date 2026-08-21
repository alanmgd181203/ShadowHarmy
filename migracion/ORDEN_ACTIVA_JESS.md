# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`

---

## 1) Arranque (rama de esta misión)

En `master` el ritual de bóveda fue purgado con Beru spot. **Esta misión** se toma de la rama:

```
git fetch origin
git checkout orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md scripts/jess_boveda_coliseo_noche.py data/coliseo/rango_top100_jess.txt data/coliseo/rango_top100_usa.txt data/coliseo/rango_top100_split.json data/coliseo/INSTRUCCIONES_MERGE_RANGO_TOP100.md
```

Confirmar que existe: `scripts/jess_boveda_coliseo_noche.py`

---

## 2) Misión — Mitad Jess: bóveda linear 1m (top 100 cripto, 365 días)

**Qué es:** ojos only. Descargar **velas de 1 minuto** · mercado **linear** · **365 días** · **50 santos** (ranks 51–100 del top 100 por volumen 24h, sin ETF/oro/acciones/metales).

**La otra mitad** (ranks 1–50) la baja el Monarca en USA. Al terminar, Jess **empaqueta** y sube el zip a **Drive** para que el Monarca una las dos bóvedas.

**Lista fija Jess (no inventar otras):**

```
AKE,1000BONK,MAGMA,FIL,PEOPLE,RED,KAITO,CASHCAT,GALA,VIRTUAL,ONT,INJ,ATOM,BIO,TRX,POL,ETHFI,TUT,OP,SHIB1000,ICP,GRASS,CHIP,GRAM,H,PRL,VVV,VELVET,AERO,MET,ZRO,USELESS,ETC,JTO,CAP,TIA,MORPHO,SEI,CYS,LDO,GPS,ALGO,STABLE,PLUME,PNUT,SPX,DASH,JUP,STRK,PENDLE
```

(Misma lista en `data/coliseo/rango_top100_jess.txt`.)

### Comando exacto

```
python -u scripts/jess_boveda_coliseo_noche.py --dias 365 --interval 1 --markets linear --workers 3 --sleep 0.12 --watchdog --ritual rango_top100_jess --only AKE,1000BONK,MAGMA,FIL,PEOPLE,RED,KAITO,CASHCAT,GALA,VIRTUAL,ONT,INJ,ATOM,BIO,TRX,POL,ETHFI,TUT,OP,SHIB1000,ICP,GRASS,CHIP,GRAM,H,PRL,VVV,VELVET,AERO,MET,ZRO,USELESS,ETC,JTO,CAP,TIA,MORPHO,SEI,CYS,LDO,GPS,ALGO,STABLE,PLUME,PNUT,SPX,DASH,JUP,STRK,PENDLE
```

Dejar correr hasta `NOCHE BÓVEDA DONE`. Si se cae la luz/Cursor, **re-lanzar el mismo comando** (checkpoint reanuda).

### Al terminar — Drive

1. El ritual crea un zip bajo `data/coliseo/` tipo `ShadowHarmy_Coliseo_1m_….zip` (incluye `boveda_linear_1m.sqlite`).
2. Subir **ese zip** a Drive (carpeta que use el Monarca).
3. Avisar al Monarca: *«Mitad Jess lista · zip en Drive · nombre del archivo»*.

Detalle progreso: `data/coliseo/PROGRESO.md` · latido: `data/coliseo/heartbeat.json`

---

## 3) Qué NO hacer

- No manos / no órdenes / no arise Beru ni Igris.
- No tocar la mitad USA (BTC…RE); solo la lista de arriba.
- No `--interval 1s` ni spot/inverse en esta misión.
- No subir `.env` ni secretos.
- No borrar bóvedas ajenas.
- No hacer `git pull` que pise esta misión a mitad de descarga.

---

## 4) Qué mirar

1. Probe Bybit OK (México).
2. En `PROGRESO.md`: los 50 bases `linear` en **ok** con filas ~500k+ por santo (365d × 1m ≈ 525600).
3. Zip creado y subido a Drive.
4. Aviso al Monarca con el nombre del zip.

---

## 5) HECHO

- [ ] Archivos de la rama `orden-jess-boveda-rango-top50` en el disco
- [ ] Descarga 50 santos linear 1m 365d terminada
- [ ] Zip en Drive + aviso al Monarca

---

*Shadow Army · bóveda rango top100 mitad Jess · ojos only · 365d 1m*
