#!/bin/bash
# Doble clic Finder (macOS México) → arena Igris ~2 min.
# Ojos mainnet Bybit; fills virtuales; Tusk limpio por activo; matriz forzada.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR" "$ROOT/data"

SEGUNDOS="${ARENA_IGRIS_SEGUNDOS_OJOS:-120}"
ACTIVOS="${ARENA_IGRIS_ACTIVOS:-flota}"

echo ""
echo "═══════════════════════════════════════════════"
echo "  Shadow Army — Arena Igris (~2 min)"
echo "═══════════════════════════════════════════════"
echo "  Carpeta: $ROOT"
echo "  Ojos WS: ${SEGUNDOS}s · Activos: ${ACTIVOS}"
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

export ARENA_IGRIS_ACTIVA=true
export ARENA_IGRIS_FILLS_VIRTUALES=true
export ARENA_IGRIS_SIN_RANGOS=true
export ARENA_IGRIS_SIN_PACIENCIA=true
export ARENA_IGRIS_SIN_BANDA_DELTA=true
export ARENA_IGRIS_TUSK_LIMPIO_POR_ACTIVO=true
export ARENA_IGRIS_UMBRAL_PCT="${ARENA_IGRIS_UMBRAL_PCT:-0.01}"
export ARENA_IGRIS_MORDIDA_USD="${ARENA_IGRIS_MORDIDA_USD:-5}"
export ARENA_IGRIS_EQUITY_USD="${ARENA_IGRIS_EQUITY_USD:-500}"
export ARENA_IGRIS_ACTIVOS="$ACTIVOS"
export ARENA_IGRIS_SEGUNDOS_OJOS="$SEGUNDOS"
export MODO_SIMULACION=true
export MODO_TESTNET="${MODO_TESTNET:-True}"

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/arena_igris_${STAMP}.log"

echo "→ Smoke Igris..."
if ! python scripts/validar_igris_smoke.py 2>&1 | tee -a "$LOG_FILE"; then
  echo "Smoke falló — $LOG_FILE"
  read -r -p "Enter para cerrar..."
  exit 1
fi

echo ""
echo "→ Arena ~$((SEGUNDOS / 60)) min (ojos mainnet)..."
echo "   Log: $LOG_FILE"
echo ""

if python scripts/arena_igris_aislado.py --segundos "$SEGUNDOS" 2>&1 | tee -a "$LOG_FILE"; then
  echo ""
  echo "Arena terminada."
  echo "  Reporte: $ROOT/data/arena_igris_report.json"
  echo "  Log: $LOG_FILE"
else
  echo "Arena falló — $LOG_FILE"
  read -r -p "Enter para cerrar..."
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  open "$ROOT/data/arena_igris_report.json" 2>/dev/null || true
fi

read -r -p "Enter para cerrar..."
exit 0
