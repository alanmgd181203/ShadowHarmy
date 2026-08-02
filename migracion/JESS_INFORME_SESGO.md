# Jess — regenerar informe sesgo detallado

```bash
cd ~/Desktop/btc/jubilacion/ShadowHarmy   # o tu ruta
git pull
python scripts/informe_sesgo_monarca.py
# opcional ventana corta:
# python scripts/informe_sesgo_monarca.py --ventana corto

git add migracion/INFORME_SESGO_ESTRUCTURAL.md data/informe_sesgo_estructural.json
git commit -m "Informe sesgo detallado: residencia + volteos."
git push
```

El Monarca necesita: % tiempo en desfase (abrumador?) + episodios cuando se voltea el spread.
