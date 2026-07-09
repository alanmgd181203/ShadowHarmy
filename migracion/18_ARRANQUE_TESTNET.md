# 18 — Arranque testnet (runbook Monarca)

**Cuándo usar:** antes de `python arise.py` en testnet o al retomar sesión.

---

## 1. Variables `.env` mínimas

```env
BYBIT_API_KEY=tu_key_testnet
BYBIT_API_SECRET=tu_secret_testnet
MODO_TESTNET=True
MODO_SIMULACION=True
TICKER_BASE=BTC
```

| Flag | Recomendado ahora | Cuándo cambiar |
|------|-------------------|----------------|
| `MODO_TESTNET` | `True` | Mainnet → Fase 6 |
| `MODO_SIMULACION` | `True` | Tras ciclo live testnet → `False` (check 3.6.2) |
| `SAFE_MODE` | omitir o `False` | Emergencia → Fase 4.2 |
| `TICKER_BASE` | `BTC` o `LTC` | Beru/manos testnet; ojos siempre LTC+BTC |

---

## 2. Validar antes de arrancar

```powershell
cd C:\Users\alans\Desktop\ShadowHarmy

# Pentiverso 10 mares (~25s, requiere red)
python scripts/validar_m2.py

# Ciclo Beru CAZA→COSECHA (sim, ~1s)
python scripts/probar_ciclo_beru.py

# Checklist completo → data/validacion_checklist.json
python scripts/validar_checklist.py
python scripts/validar_checklist.py --all   # refresca m2 si stale
```

**Gates automáticos al arrancar `arise.py`:** aviso si `MODO_SIMULACION=False` sin ciclo documentado.

---

## 3. Arrancar el ejército

```powershell
python arise.py
```

Panel (otra terminal):

```powershell
streamlit run panel.py
```

---

## 4. Qué esperar en testnet

| General | Comportamiento |
|---------|----------------|
| **Tank/Bridge** | Ojos mainnet LTC+BTC (10 mares) |
| **Beru** | Casa en `TICKER_BASE` (spot USDT/USDC) |
| **Igris** | Manto LTC+BTC; bootstrap si `pesos` vacíos |
| **Greed** | Regalo USDT×USDC en ambos activos |
| **Tusk** | NAV real si keys OK; sim anota sin fill |

Con `MODO_SIMULACION=True`: CAZA/COSECHA/Greed escriben en Bellion con precios mainnet pero **no exigen fill** en testnet.

---

## 5. Pasar a live testnet (3.6.2)

1. Confirmar checklist Fase 3 ✅: `python scripts/validar_checklist.py --fase 3`
2. Opcional: dejar `arise.py` corriendo horas y ver CAZA+COSECHA en `data/historial_hierro.jsonl`
3. Cambiar `.env`: `MODO_SIMULACION=False`
4. Reiniciar; verificar que Bridge dispara en testnet

**No pasar a mainnet** hasta Fase 6 (tope masa, runbook incidentes).

---

## 6. Apagado digno

`Ctrl+C` → signal handler sella `data/estado_hierro.json` (ley de sucesión).

---

## 7. Reportes generados

| Archivo | Contenido |
|---------|-----------|
| `data/validacion_m2.json` | Pentiverso 10/10 |
| `data/validacion_ciclo_ejercito.json` | Ciclo 3.6.1 |
| `data/validacion_checklist.json` | Estado todos los checks |
| `data/historial_hierro.jsonl` | Crónica Bellion |
| `data/m1_btc_roundtrip.json` | Trade M1 documentado |

---

*Actualizado: 2026-07-05 — pentiverso dual LTC+BTC*
