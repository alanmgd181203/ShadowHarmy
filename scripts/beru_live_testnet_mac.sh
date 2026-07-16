#!/bin/bash
# Terminal macOS: ./scripts/beru_live_testnet_mac.sh [segundos] [activos]
# Default: 1800 s (30 min), ETH,BTC,LTC,SOL,OP — checklist 3.9.9
# Ansiedad 1.2% → gatillo ±0.6% · Mariscal · CAZA · ~$10
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SEGUNDOS="${1:-${LIVE_BERU_SEGUNDOS:-1800}}"
ACTIVOS="${2:-${LIVE_BERU_ACTIVOS:-ETH,BTC,LTC,SOL,OP}}"
MORDIDA="${LIVE_BERU_MORDIDA_USD:-10}"

export LIVE_BERU_TESTNET=true
export LIVE_BERU_SEGUNDOS="$SEGUNDOS"
export LIVE_BERU_ACTIVOS="$ACTIVOS"
export BERU_CAZADOR_MORDIDA_USD="$MORDIDA"
export BERU_CAZA_CAPA1_USD="$MORDIDA"
export BERU_TIER_DEFAULT=PLENO
export BERU_MODO_COMBATE_DEFAULT=CAZA
export BERU_VACIO_ANSIEDAD=0.012
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

echo "[live-mac] Beru live testnet ${SEGUNDOS}s · ${ACTIVOS} · Ansiedad/Mariscal/\$${MORDIDA}"
python scripts/validar_beru_cazador_smoke.py
python scripts/beru_live_testnet.py --segundos "$SEGUNDOS" --activos "$ACTIVOS"
echo "[live-mac] reporte → data/beru_live_testnet_report.json"
