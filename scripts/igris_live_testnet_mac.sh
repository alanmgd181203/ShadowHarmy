#!/bin/bash
# Terminal macOS: ./scripts/igris_live_testnet_mac.sh [segundos] [activos]
# Default: 90 s, ETH,BTC,LTC,SOL,OP — checklist 3.10.7b
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SEGUNDOS="${1:-${LIVE_IGRIS_SEGUNDOS_OJOS:-90}}"
ACTIVOS="${2:-${LIVE_IGRIS_ACTIVOS:-ETH,BTC,LTC,SOL,OP}}"

export LIVE_IGRIS_TESTNET=true
export LIVE_IGRIS_SEGUNDOS_OJOS="$SEGUNDOS"
export LIVE_IGRIS_ACTIVOS="$ACTIVOS"
export LIVE_IGRIS_MORDIDA_MAX_USD="${LIVE_IGRIS_MORDIDA_MAX_USD:-12}"
export MODO_TESTNET=True
export MODO_SIMULACION=False
export ARENA_IGRIS_ACTIVA=false
export ARENA_IGRIS_FILLS_VIRTUALES=false
export GREED_KAISER_ENABLED=false
export GREED_VIP_ENABLED=false
export GREED_BASIS_HOLD_ENABLED=false
export SAFE_MODE=true

if [[ -d "$ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

echo "[live-mac] smoke + live testnet ${SEGUNDOS}s · ${ACTIVOS}"
python scripts/validar_igris_smoke.py
python scripts/igris_live_testnet.py --segundos "$SEGUNDOS" --activos "$ACTIVOS"
echo "[live-mac] reporte → data/igris_live_testnet_report.json"
