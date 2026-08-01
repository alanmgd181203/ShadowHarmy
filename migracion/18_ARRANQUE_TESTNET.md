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

## 3. Ritual de ojos primero (recomendado con capital real / mainnet-ojos)

Antes del ejército completo: Tusk ve la bóveda, Tank abre mares, Kaiser actualiza indicadores. **Sin órdenes** (Igris/Greed/Beru no disparan).

```powershell
# .env: claves Bybit (mainnet o testnet) + TUSK_TESORERIA_ACTIVA=true
# El ritual fuerza MODO_SIMULACION=true salvo ARISE_OJOS_PERMITIR_MANOS=true
python scripts/arise_ojos_tusk.py
# o corte corto:
python scripts/arise_ojos_tusk.py --segundos 90
```

Qué mirar en consola / panel (`estado_vivo`):

- `tusk_tesoreria`: equity, disponible, MNT, hedges, **oxígeno de guerra**, estado
- digest Kaiser (perfiles / frecuencia manto)
- matriz Tank

Cuando el oxígeno cuadre con Bybit → siguiente paso doctrinal: Igris en sim (manto), luego live; Beru solo tras manto del paso.

Smoke estático: `python scripts/validar_arise_ojos_smoke.py`

---

## 3b. Arrancar el ejército completo

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
| `data/arena_igris_report.json` | Arena Igris aislada (Kaiser→escudo, fills virtuales) |
| `data/igris_live_testnet_report.json` | Live Igris testnet 3.10.7b (órdenes DEMO reales) |
| `data/beru_live_testnet_report.json` | Live Beru testnet 3.9.9 (Ansiedad/Mariscal, spot DEMO) |

---

## 8. Arena Igris aislada (antes de live 3.10.7b)

Prueba **solo el escudo** — sin Beru, Greed ni rangos Beru. Ojos **mainnet**; fills **virtuales** al Ask/Bid del libro.

```powershell
python scripts/arena_igris_aislado.py
python scripts/arena_igris_aislado.py --segundos 35
```

**En Windows (tu terminal):**

```powershell
.\scripts\arena_igris_win.ps1
.\scripts\arena_igris_win.ps1 -Segundos 120 -Activos "ETH,BTC"
# o:
python scripts/arena_igris_aislado.py --segundos 120
```

**En la Mac (México):** doble clic `Arena Igris.command` (~2 min)  
o:

```bash
chmod +x "Arena Igris.command" scripts/arena_igris_mac.sh
./scripts/arena_igris_mac.sh 120 flota
./scripts/arena_igris_mac.sh 120 ETH
```

Kaiser emite `OPORTUNIDAD_MANTO` con la misma visión Ask/Bid que la Puerta §E (no last price). El barrido de flota deja el Bridge vivo y debe terminar en segundos. El reporte incluye `via_kaiser`, `via_puerta`, `oportunidad_manto` y `barrido_s`.

Variables útiles (`.env` o entorno):

| Variable | Default | Rol |
|----------|---------|-----|
| `ARENA_IGRIS_EQUITY_USD` | 500 | NAV mock Tusk |
| `ARENA_IGRIS_UMBRAL_PCT` | 0.01 | Umbral micro spread (no fees) |
| `ARENA_IGRIS_MORDIDA_USD` | 5 | Mordida fija por disparo |
| `ARENA_IGRIS_ACTIVOS` | flota | `ETH,BTC` o lista del diccionario flota |
| `ARENA_IGRIS_SEGUNDOS_OJOS` | 25 | WS mainnet antes de disparar |

En `arise.py` (producción gradual): `IGRIS_EVENT_DRIVEN=true` — Igris solo despierta con `OPORTUNIDAD_MANTO` / matriz L/S de Kaiser.

---

## 9. Live Igris testnet (checklist 3.10.7b)

Órdenes **reales** en Bybit DEMO. Sin Beru/Greed. Umbral = **fees** (no micro arena). Mordida tope default $12/pata.

**Orden lista para Cursor México:** `migracion/CURSOR_MEXICO_EJECUTAR_3_10_7b.md`

```bash
# Mac
chmod +x "Igris Live Testnet.command" scripts/igris_live_testnet_mac.sh
./scripts/igris_live_testnet_mac.sh 90 ETH,BTC,LTC,SOL,OP
# o doble clic: Igris Live Testnet.command
```

```powershell
# Windows
.\scripts\igris_live_testnet_win.ps1
.\scripts\igris_live_testnet_win.ps1 -Segundos 90 -Activos "ETH,BTC,LTC"
```

Reporte: `data/igris_live_testnet_report.json` → campo `veredicto`:
- `PASS_LIVE` → marcar **3.10.7b** [x]
- `SIN_DISPARO_MERCADO` → reintentar (spread < fees)

---

## 10. Live Beru testnet (checklist 3.9.9)

Órdenes **reales** spot en Bybit DEMO. Beru **aislado** (sin Igris/Greed).

| Doctrina sesión | Valor |
|-----------------|--------|
| Capitán | **Ansiedad** 1,2 % → gatillo **±0,6 %** |
| Tier | **Mariscal / PLENO** · clon **0,1 %** |
| Modo | **CAZA** · mordida **~$10** |
| Activos default | ETH, BTC, LTC, SOL, OP |

**Orden lista para Cursor México:** `migracion/CURSOR_MEXICO_EJECUTAR_3_9_9.md`

```bash
# Mac
chmod +x "Beru Live Testnet.command" scripts/beru_live_testnet_mac.sh
./scripts/beru_live_testnet_mac.sh 1800 ETH,BTC,LTC,SOL,OP
# vigilia larga / hasta Ctrl+C:
python scripts/beru_live_testnet.py --segundos 0 --activos ETH,BTC,LTC,SOL,OP
```

```powershell
# Windows
.\scripts\beru_live_testnet_win.ps1
.\scripts\beru_live_testnet_win.ps1 -Segundos 3600 -Activos "ETH,BTC,LTC,SOL,OP"
```

Reporte: `data/beru_live_testnet_report.json` → campo `veredicto`:
- `PASS_LIVE` → marcar **3.9.9** [x]
- `SIN_DISPARO_MERCADO` → el mercado no movió ±0,6 %; alargar minutos

---

*Actualizado: 2026-07-16 — live Beru 3.9.9 (Ansiedad/Mariscal) + Igris 3.10.7b*
