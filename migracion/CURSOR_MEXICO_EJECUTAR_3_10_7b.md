# Orden para Cursor (México) — Checklist 3.10.7b Igris LIVE TESTNET

**Para:** Jessica / Cursor en la Mac del cuartel México  
**Commit base:** pull de `master` (incluye ritual `scripts/igris_live_testnet.py`)  
**Qué es:** campo de entrenamiento Bybit DEMO — órdenes **reales** del escudo Igris (dual §E), sin Beru ni Greed. No es la arena de fills virtuales.

---

## Pegar esto en Cursor (Agent Mode)

```
Ejecuta el checklist 3.10.7b exactamente como está preparado en el repo.

1) git pull origin master
2) Confirma que existe scripts/igris_live_testnet.py y el .env tiene BYBIT_API_KEY/SECRET y MODO_TESTNET=True (no cambies el .env salvo que falten keys).
3) Dale permiso de ejecución si hace falta:
   chmod +x "Igris Live Testnet.command" scripts/igris_live_testnet_mac.sh
4) Corre el ritual (elige UNA vía):
   - Finder: doble clic en «Igris Live Testnet.command»
   - o terminal: ./scripts/igris_live_testnet_mac.sh 90 ETH,BTC,LTC,SOL,OP
5) Cuando termine, abre data/igris_live_testnet_report.json y reporta al Monarca:
   - veredicto
   - disparos_ok / via_kaiser / via_puerta
   - orden_enviada_log (historial)
   - si Bybit testnet UI muestra LONG inverse + SHORT lineal en algún activo disparado
6) Si veredicto == PASS_LIVE: marca [x] el ítem 3.10.7b en migracion/16_CHECKLIST_MAESTRO.md, commit con mensaje «3.10.7b Igris live testnet PASS» y push a master.
7) Si veredicto == SIN_DISPARO_MERCADO: no marques el checklist; reintenta más tarde (spread < fees) o amplía activos. No fuerza fills.
8) No actives MODO_SIMULACION=False en arise.py completo ni toques mainnet. Este script ya fuerza la sesión segura.

Habla al Monarca en términos del Ejército (Igris, manto, campo de entrenamiento, Bridge).
```

---

## Criterio de éxito

| Campo en el reporte | Significado |
|---------------------|-------------|
| `PASS_LIVE` | Al menos 1 dual §E con `ORDEN_ENVIADA` en historial — **cerrar 3.10.7b** |
| `SIN_DISPARO_MERCADO` | Ritual OK; el mercado no dio spread ≥ fees — reintentar |
| `PASS_PARCIAL_SIN_LOG_BRIDGE` | Raro; revisar historial / Bridge a mano |

---

## Seguridad (ya cableada en el script)

- `MODO_TESTNET=True` obligatorio (si no → ABORT)
- `MODO_SIMULACION=False` solo en esta sesión (no reescribe `.env`)
- Arena OFF (fills no virtuales)
- Greed hibernado; SAFE_MODE on
- Mordida tope default **$12** por pata (`LIVE_IGRIS_MORDIDA_MAX_USD`)

---

## Tras el PASS

Siguiente del checklist `16`: ops Fase 4 / lo que el Monarca indique. No saltar a mainnet con capital serio sin orden explícita.
