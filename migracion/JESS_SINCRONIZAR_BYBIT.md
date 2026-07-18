# Jess — Sincronizar Bybit (México)

**Para:** Cursor en la Mac de Jess  
**Por qué:** la forja del Monarca recibe HTTP 403 de `api.bybit.com`. México sí llega.

---

## Mandato listo para pegar en Cursor (Agent)

```
Actualiza el repo (git pull origin master) y ejecuta el ritual Bybit de México.

1) git status && git pull origin master
2) python scripts/jess_sincronizar_bybit_mexico.py
   (si falla el import, desde la raíz del repo: python -m no hace falta; solo python scripts/...)
3) Revisa data/jess_bybit_sync/RESUMEN.md — confirma LTC/SOL/BTC/ETH/XRP
4) Commit y push SOLO lo del sync + config + diccionario:

git add data/jess_bybit_sync/ config/diccionario_beru_flota_manto.json core/config.py
git commit -m "$(cat <<'EOF'
Sync Bybit Mexico: apalancamientos vivos, flota Beru y snapshot Tank.

EOF
)"
git push origin HEAD

5) Avisa al Monarca: ya está en origin para git pull.

No subas Ima/, tools/, data/kaiser/samples, videos ni logs basura.
```

---

## Qué genera el ritual

| Salida | Contenido |
|--------|-----------|
| `data/jess_bybit_sync/apalancamientos_vivo.json` | maxLeverage linear/inverse vs config |
| `data/jess_bybit_sync/instrumentos_*.jsonl` | Universo Tank (perps Trading) |
| `data/jess_bybit_sync/risk_limits_muestra.json` | Risk limit tiers (muestra) |
| `data/jess_bybit_sync/fees.json` | Fees si hay API keys; si no, nota |
| `config/diccionario_beru_flota_manto.json` | Regenerado |
| `core/config.py` | `MANTO_LEVERAGE_*` alineados al vivo |

Scripts base: `verificar_apalancamientos_bybit.py`, `generar_diccionario_beru.py`, `jess_sincronizar_bybit_mexico.py`.
