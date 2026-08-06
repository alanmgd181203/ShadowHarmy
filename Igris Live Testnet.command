#!/bin/bash
# Doble clic Finder (macOS México) → Igris LIVE TESTNET checklist 3.10.7b
# Órdenes REALES en Bybit DEMO. Sin Beru/Greed. Ojos mainnet.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR" "$ROOT/data"

SEGUNDOS="${LIVE_IGRIS_SEGUNDOS_OJOS:-90}"
ACTIVOS="${LIVE_IGRIS_ACTIVOS:-ETH,BTC,LTC,SOL,OP}"
MORDIDA="${LIVE_IGRIS_MORDIDA_MAX_USD:-12}"

echo ""
echo "═══════════════════════════════════════════════"
echo "  Shadow Army — Igris LIVE TESTNET (3.10.7b)"
echo "═══════════════════════════════════════════════"
echo "  Manos: Bybit DEMO (órdenes reales)"
echo "  Ojos: ${SEGUNDOS}s · Activos: ${ACTIVOS}"
echo "  Mordida max: \$${MORDIDA}/pata"
echo "═══════════════════════════════════════════════"
echo ""

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "No existe .venv"
  echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  read -r -p "Enter para cerrar..."
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

export LIVE_IGRIS_TESTNET=true
export LIVE_IGRIS_SEGUNDOS_OJOS="$SEGUNDOS"
export LIVE_IGRIS_ACTIVOS="$ACTIVOS"
export LIVE_IGRIS_MORDIDA_MAX_USD="$MORDIDA"
export MODO_TESTNET=True
export MODO_SIMULACION=False
export ARENA_IGRIS_ACTIVA=false
export ARENA_IGRIS_FILLS_VIRTUALES=false
export GREED_KAISER_ENABLED=false
export GREED_VIP_ENABLED=false
export GREED_BASIS_HOLD_ENABLED=false
export SAFE_MODE=true

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/igris_live_testnet_${STAMP}.log"

echo "→ Smoke Igris..."
if ! python scripts/validar_igris_smoke.py 2>&1 | tee -a "$LOG_FILE"; then
  echo "Smoke falló — $LOG_FILE"
  read -r -p "Enter para cerrar..."
  exit 1
fi

echo ""
echo "→ LIVE testnet (~$((SEGUNDOS / 60)) min ojos)..."
echo "   Log: $LOG_FILE"
echo ""

if python scripts/igris_live_testnet.py --segundos "$SEGUNDOS" --activos "$ACTIVOS" 2>&1 | tee -a "$LOG_FILE"; then
  echo ""
  echo "Live terminado."
  echo "  Reporte: $ROOT/data/igris_live_testnet_report.json"
  echo "  Log: $LOG_FILE"
  echo "  Veredicto: abrir el JSON y leer campo veredicto"
else
  echo "Live falló — $LOG_FILE"
  read -r -p "Enter para cerrar..."
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  open "$ROOT/data/igris_live_testnet_report.json" 2>/dev/null || true
fi

read -r -p "Enter para cerrar..."
exit 0
