# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México.**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`

---

## 1) Arranque (rama de esta misión)

En `master` el ritual de bóveda fue purgado con Beru spot. **Esta noche** se toma de la rama de la misión:

```
git fetch origin
git checkout orden-jess-boveda-rango-top50 -- migracion/ORDEN_ACTIVA_JESS.md scripts/jess_boveda_coliseo_noche.py data/coliseo/rango_top50_jess.txt data/coliseo/rango_top50_usa.txt data/coliseo/rango_top50_split.json data/coliseo/INSTRUCCIONES_MERGE_RANGO_TOP50.md
```

Confirmar que existe: `scripts/jess_boveda_coliseo_noche.py`

---

## 2) Misión — Mitad Jess: bóveda linear 1m (top 50 cripto, 90 días)

**Qué es:** ojos only. Descargar **velas de 1 minuto** · mercado **linear** · **90 días** · **25 santos** (mitad del top 50 por volumen, sin ETF/oro/acciones).

**La otra mitad** la baja el Monarca en USA. Al terminar, Jess **empaqueta** y sube el zip a **Drive** para que el Monarca una las dos bóvedas.

**Lista fija Jess (no inventar otras):**

```
FARTCOIN,XLM,TAO,PENGU,UNI,CRV,MON,AAVE,LTC,HEMI,ASTER,WIF,BCH,AVAAI,ARB,1000NEIROCTO,XMR,ORDI,XPL,WLFI,DOT,MNT,HBAR,APT,RE
```

(Misma lista en `data/coliseo/rango_top50_jess.txt`.)

### Comando exacto

```
python -u scripts/jess_boveda_coliseo_noche.py --dias 90 --interval 1 --markets linear --workers 3 --sleep 0.12 --watchdog --ritual rango_top50_jess --only FARTCOIN,XLM,TAO,PENGU,UNI,CRV,MON,AAVE,LTC,HEMI,ASTER,WIF,BCH,AVAAI,ARB,1000NEIROCTO,XMR,ORDI,XPL,WLFI,DOT,MNT,HBAR,APT,RE
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
- No tocar la mitad USA (BTC…TRUMP); solo la lista de arriba.
- No `--interval 1s` ni spot/inverse en esta misión.
- No subir `.env` ni secretos.
- No borrar bóvedas ajenas.
- No hacer `git pull` que pise esta misión a mitad de descarga.

---

## 4) Qué mirar

1. Probe Bybit OK (México).
2. En `PROGRESO.md`: los 25 bases `linear` en **ok** con filas ~100k+ por santo (90d × 1m).
3. Zip creado y subido a Drive.
4. Aviso al Monarca con el nombre del zip.

---

## 5) HECHO

- [ ] Archivos de la rama `orden-jess-boveda-rango-top50` en el disco
- [ ] Descarga 25 santos linear 1m 90d terminada
- [ ] Zip en Drive + aviso al Monarca

---

*Shadow Army · bóveda rango top50 mitad Jess · ojos only*
