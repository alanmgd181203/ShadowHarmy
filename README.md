# Shadow Army — Lilit de Hierro v2.0

Bot de trading algorítmico multi-General para Bybit. Arquitectura async con 7 Generales que operan en paralelo.

## Arranque rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar secretos (crear archivo .env en la raíz)
#    BYBIT_API_KEY=tu_clave
#    BYBIT_API_SECRET=tu_secreto
#    MODO_SIMULACION=True
#    TICKER_BASE=BTC
#    (MODO_TESTNET abolido 2026-08-11 — solo mainnet; True → ABORT)

# 3. Validar estado (opcional, recomendado)
python scripts/validar_beru_sin_tumores_smoke.py
python scripts/validar_beru_altar_nativo_smoke.py
python scripts/validar_arise_ojos_smoke.py

# 4. Despertar (rituales vivos; no el arise legacy a ciegas)
#    python scripts/arise_ojos_tusk.py
#    python scripts/arise_igris.py
#    python scripts/arise_beru_flota_viva.py

# 5. Panel visual (en otra terminal)
streamlit run panel.py
```


## Estructura

```
arise.py              ← Orquestador (despierta a todos)
panel.py              ← Dashboard Streamlit (visual en navegador)
core/
  config.py           ← Configuración central + bandas + slippage
  models.py           ← BeruShip, MarketContext, IntencionAccion
  bridge.py           ← Ojos y manos hacia Bybit (WS + REST)
  bellion.py          ← Crónica y persistencia
  dashboard.py        ← Panel consola (legacy)
  validacion.py       ← Gates checklist (Fases 3–4)
  telegram.py         ← Stub Telegram (Fase 4)
generales/
  beru.py             ← Cazador casa (CAZA/COSECHA directo Bridge)
  greed.py            ← Regalo USDT×USDC dual LTC+BTC
  igris.py            ← Escudo manto (FRENTES_MANTO_ALL)
  tusk.py             ← Bóveda (reservas, masa, NAV)
  tank.py             ← Visión (10 mares LTC+BTC, semáforo)
  capitanes.py        ← ADN por clima (Ansiedad, Cazador, Berserker)
scripts/
  validar_beru_sin_tumores_smoke.py
  validar_beru_altar_nativo_smoke.py
  arise_ojos_tusk.py / arise_igris.py / arise_beru_flota_viva.py
migracion/            ← Codex operativo (planos, checklist, doctrina)
```

## Documentación

Todo el conocimiento del ejército vive en `migracion/`:
- `16_CHECKLIST_MAESTRO.md` — checklist por fases / qué toca hacer
- `17_GUIA_MONARCA.md` — cómo hablar con el agente
- Arena / Arise = ensayo sim o mainnet (DEMO Bybit abolido 2026-08-11)

## Estado actual

**Fase:** M0 — el ejército despierta (código que arranca).
