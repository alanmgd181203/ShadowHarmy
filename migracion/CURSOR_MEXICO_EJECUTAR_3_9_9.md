# Orden para Cursor (México) — Checklist 3.9.9 Beru LIVE TESTNET

**Para:** Jessica / Cursor en la Mac del cuartel México  
**Commit base:** pull de `master` (incluye ritual `scripts/beru_live_testnet.py`)  
**Qué es:** campo de entrenamiento Bybit DEMO — Beru **aislado** caza y negocia en spot con sangre real. Sin Igris ni Greed.

## Doctrina de esta sesión (orden Monarca)

| Parámetro | Valor |
|-----------|--------|
| Capitán | **Ansiedad** — vacío **1,2 %** → gatillo caza **±0,6 %** (no Normal 1,6 % / 0,8 %) |
| Tier | **PLENO / Mariscal** — nacimiento / clon cada **0,1 %** |
| Modo | **CAZA** |
| Mordida | **~$10** por caza |
| Activos | **ETH, BTC, LTC, SOL, OP** (5 monedas spot) |
| Duración default | **30 min** (1800 s); se puede alargar |

---

## Pegar esto en Cursor (Agent Mode)

```
Ejecuta el checklist 3.9.9 exactamente como está preparado en el repo.

1) git pull origin master
2) Confirma que existe scripts/beru_live_testnet.py y el .env tiene BYBIT_API_KEY/SECRET y MODO_TESTNET=True (no cambies el .env salvo que falten keys).
3) Dale permiso de ejecución si hace falta:
   chmod +x "Beru Live Testnet.command" scripts/beru_live_testnet_mac.sh
4) Corre el ritual (elige UNA vía):
   - Finder: doble clic en «Beru Live Testnet.command»
   - o terminal: ./scripts/beru_live_testnet_mac.sh 1800 ETH,BTC,LTC,SOL,OP
   - vigilia larga: ./scripts/beru_live_testnet_mac.sh 3600 ETH,BTC,LTC,SOL,OP
   - hasta Ctrl+C: python scripts/beru_live_testnet.py --segundos 0 --activos ETH,BTC,LTC,SOL,OP
5) Cuando termine (o tras Ctrl+C), abre data/beru_live_testnet_report.json y reporta al Monarca:
   - veredicto
   - cazas_materializadas / cosechas
   - orden_enviada_log (historial)
   - si Bybit testnet UI muestra posiciones spot en algún activo disparado
6) Si veredicto == PASS_LIVE: marca [x] el ítem 3.9.9 en migracion/16_CHECKLIST_MAESTRO.md, commit con mensaje «3.9.9 Beru live testnet PASS» y push a master.
7) Si veredicto == SIN_DISPARO_MERCADO: no marques el checklist; el mercado no movió ±0.6% desde el 0 — reintenta con más minutos. No fuerces fills.
8) No actives MODO_SIMULACION=False en arise.py completo ni toques mainnet. Este script ya fuerza la sesión segura.

Habla al Monarca en términos del Ejército (Beru, Ansiedad, Mariscal, caza, campo de entrenamiento, Bridge).
```

---

## Criterio de éxito

| Campo en el reporte | Significado |
|---------------------|-------------|
| `PASS_LIVE` | ≥1 caza materializada + `ORDEN_ENVIADA` en historial — **cerrar 3.9.9** |
| `PASS_PARCIAL_SIN_LOG_BRIDGE` | Caza en memoria Tusk pero sin log Bridge — revisar historial |
| `SIN_DISPARO_MERCADO` | Ritual OK; precio no cruzó ±0.6% — reintentar más tiempo |
| `INTERRUMPIDO_SIN_DISPARO` | Ctrl+C antes de caza |

---

## Seguridad (ya cableada en el script)

- `MODO_TESTNET=True` obligatorio (si no → ABORT)
- `MODO_SIMULACION=False` solo en esta sesión (no reescribe `.env`)
- Igris bootstrap OFF; Greed hibernado; SAFE_MODE on
- Ojos: spot mainnet REST (+ WS Tank); manos: Bybit DEMO

## Tras el PASS

Reportar al Monarca el JSON. El Monarca puede seguir mejorando el Pergamino mientras Beru deja crónica en `historial_hierro.jsonl`.
