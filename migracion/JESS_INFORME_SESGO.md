# Jess — informes sesgo + ETA marchas

```bash
cd ~/Desktop/btc/jubilacion/ShadowHarmy   # o tu ruta
git pull

# 1) Sesgo detallado (residencia + volteos)
python scripts/informe_sesgo_monarca.py

# 2) ETA manto en las 3 marchas (cero estructural)
python scripts/informe_eta_marchas.py --equity 1525

git add migracion/INFORME_SESGO_ESTRUCTURAL.md data/informe_sesgo_estructural.json \
        migracion/INFORME_ETA_MARCHAS.md data/informe_eta_marchas.json
git commit -m "Informes Monarca: sesgo detallado + ETA 3 marchas."
git push
```

El Monarca usa ETA para elegir Tactico / Marcha Forzada / Asalto con tiempos honestos.
