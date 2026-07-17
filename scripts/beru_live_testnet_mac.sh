#!/bin/bash
# Terminal macOS: ./scripts/beru_live_testnet_mac.sh [segundos] [activos]
# Default: 3600 s (1 h), flota 22 barcos USDT — checklist 3.9.9
# Ansiedad 1.2% → gatillo ±0.6% · Mariscal · CAZA · ~$20 · spot margen 10x
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SEGUNDOS="${1:-${LIVE_BERU_SEGUNDOS:-3600}}"
ACTIVOS="${2:-${LIVE_BERU_ACTIVOS:-flota}}"
MORDIDA="${LIVE_BERU_MORDIDA_USD:-20}"
LEV="${BERU_SPOT_MARGEN_LEVERAGE:-10}"

export LIVE_BERU_TESTNET=true
export LIVE_BERU_SEGUNDOS="$SEGUNDOS"
export LIVE_BERU_ACTIVOS="$ACTIVOS"
export LIVE_BERU_MORDIDA_USD="$MORDIDA"
export BERU_CAZADOR_MORDIDA_USD="$MORDIDA"
export BERU_CAZA_CAPA1_USD="$MORDIDA"
export BERU_TIER_DEFAULT=PLENO
export BERU_MODO_COMBATE_DEFAULT=CAZA
export BERU_VACIO_ANSIEDAD=0.012
export BERU_SPOT_MARGEN_ENABLED=true
export BERU_SPOT_MARGEN_LEVERAGE="$LEV"
export BERU_RAIL_USDT_ONLY=true
export MODO_TESTNET=True
export MODO_SIMULACION=False
export GREED_KAISER_ENABLED=false
export GREED_VIP_ENABLED=false
export GREED_BASIS_HOLD_ENABLED=false
export SAFE_MODE=true

if [[ -d "$ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

echo "[live-mac] Beru live ${SEGUNDOS}s · ${ACTIVOS} · Ansiedad/Mariscal/\$${MORDIDA} · margen ${LEV}x USDT"
python scripts/validar_beru_cazador_smoke.py
python scripts/beru_live_testnet.py --segundos "$SEGUNDOS" --activos "$ACTIVOS"
echo "[live-mac] reporte → data/beru_live_testnet_report.json"
