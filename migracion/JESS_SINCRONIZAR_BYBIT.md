# Jess — Sincronizar Bybit (México)

**Para:** Cursor en la Mac de Jess  
**Por qué:** la forja del Monarca recibe HTTP 403 de `api.bybit.com`. México sí llega.

---

## Mandato listo para pegar en Cursor (Agent)

```
Actualiza el repo (git pull origin master) y ejecuta el ritual Bybit de México.

Objetivo: apalancamientos MÁXIMOS reales + MÍNIMOS de orden reales
(perps linear/inverse para Igris/Tank, y spot USDT/USDC para Beru).

1) git status && git pull origin master

2) python scripts/jess_sincronizar_bybit_mexico.py
   (desde la raíz del repo ShadowHarmy)

3) Revisa data/jess_bybit_sync/RESUMEN.md
   - Confirma lev BTC/ETH/LTC/SOL/XRP
   - Confirma minimos USD est. y piso_manto (max de las dos piernas)
   - Mira spot USDT (Beru) en la misma tabla foco

4) Commit y push SOLO el sync + bases:

git add data/jess_bybit_sync/ data/bybit_parametros_mercado.json config/diccionario_beru_flota_manto.json core/config.py
git commit -m "Sync Bybit Mexico: lev max, minimos orden, piso manto y spot Beru."
git push origin HEAD

5) Avisa al Monarca: ya esta en origin para git pull.

No subas Ima/, tools/, data/kaiser/samples, videos ni logs basura.
```

---

## Qué genera el ritual

| Salida | Contenido |
|--------|-----------|
| `data/bybit_parametros_mercado.json` | **BD** por activo: maxLev L/I, min qty, min USD est., **piso_manto_usd**, spot USDT/USDC |
| `data/jess_bybit_sync/RESUMEN.md` | Tabla foco lev + minimos |
| `instrumentos_*.jsonl` | Dump crudo linear / inverse / spot |
| `apalancamientos_vivo.json` | Contraste vs `config.py` |
| `config/diccionario_beru_flota_manto.json` | Regenerado |
| `core/config.py` | `MANTO_LEVERAGE_*` alineados |

## Unidades (importante)

- **Linear / spot:** `minOrderQty` suele ser **fracción de moneda** (ej. 0.001 BTC) → USD = qty × precio.
- **Inverse:** `minOrderQty` suele ser **USD de contrato** → ese número ya es el mínimo en dólares.
- **Piso manto Igris** = `max(min_usd_linear, min_usd_inverse)` — no se puede abrir el par L/S por debajo de eso.

## Refresh futuro (Kaiser)

Cuando Bybit mueva filtros (sin ritual completo Jess):

```bash
python scripts/kaiser_actualizar_parametros_bybit.py
```

Scripts: `bybit_parametros_mercado.py`, `jess_sincronizar_bybit_mexico.py`, `verificar_apalancamientos_bybit.py`, `generar_diccionario_beru.py`, `kaiser_actualizar_parametros_bybit.py`.
