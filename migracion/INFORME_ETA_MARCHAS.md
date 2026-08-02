# Informe Monarca — ETA manto por las 3 marchas

**Estado:** script listo en `scripts/informe_eta_marchas.py` · **tabla con numeros vivos = correr en Jess**.

Desde el cuartel USA a menudo sale `sin_tasa` (faltan muestras `lineal_vs_inverse` locales). La Mac de Jess, con ojos/Kaiser calientes, debe regenerar y subir.

```bash
git pull
python scripts/informe_eta_marchas.py --equity 1525
git add migracion/INFORME_ETA_MARCHAS.md data/informe_eta_marchas.json
git commit -m "Informe ETA manto: 3 marchas con cero estructural."
git push
```

Runbook: [`JESS_INFORME_SESGO.md`](JESS_INFORME_SESGO.md)

**Ley:** ETA usa exceso vs cero estructural (`MANTO_CERO_ESTRUCTURAL`), no el gap eterno.
