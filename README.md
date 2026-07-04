# Shadow Army — Lilit de Hierro v2.0

Bot de trading algorítmico multi-General para Bybit. Arquitectura async con 7 Generales que operan en paralelo.

## Arranque rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar secretos (crear archivo .env en la raíz)
#    BYBIT_API_KEY=tu_clave
#    BYBIT_API_SECRET=tu_secreto
#    MODO_TESTNET=True

# 3. Despertar al ejército
python arise.py

# 4. Panel visual (en otra terminal)
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
generales/
  beru.py             ← Cazador (legión, acordeón, fusión)
  greed.py            ← Ejecutor (altar, arbitraje, rebalanceo)
  igris.py            ← Escudo (manto, delta, banda adaptativa)
  tusk.py             ← Bóveda (reservas, masa, NAV)
  tank.py             ← Visión (5 mares, semáforo, capitanes)
  capitanes.py        ← ADN por clima (Ansiedad, Cazador, Berserker)
data/
  estado_hierro.json  ← Snapshot del estado (Bellion)
  estado_vivo.json    ← Estado en vivo para el panel Streamlit
migracion/            ← Codex operativo (planos, checklist, doctrina)
```

## Documentación

Todo el conocimiento del ejército vive en `migracion/`:
- `RESUMEN_EJECUTIVO.md` — estado en una página
- `16_CHECKLIST_MAESTRO.md` — qué toca hacer
- `17_GUIA_MONARCA.md` — cómo hablar con el agente

## Estado actual

**Fase:** M0 — el ejército despierta (código que arranca).
