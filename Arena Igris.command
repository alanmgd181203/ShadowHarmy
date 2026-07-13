#!/bin/bash
# Doble clic en Finder (macOS México) → arena aislada Igris.
# Ojos mainnet Bybit; fills virtuales; sin Beru/Greed/rangos.
# Desde México evita el cuello de IP/geo de USA (Binance 451, etc.).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR" "$ROOT/data"

SEGUNDOS="${ARENA_IGRIS_SEGUNDOS_OJOS:-35}"
ACTIVOS="${ARENA_IGRIS_ACTIVOS:-ETH,BTC,SOL}"

echo ""
echo "═══════════════════════════════════════════════"
echo "  🌑 Shadow Army — Arena Igris (aislada)"
echo "═══════════════════════════════════════════════"
echo "  Carpeta: $ROOT"
echo "  Ojos WS: ${SEGUNDOS}s · Activos: ${ACTIVOS}"
echo "  Fills: virtuales (Ask/Bid mainnet)"
echo "═══════════════════════════════════════════════"
echo ""

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "❌ No existe .venv"
  echo "   Ejecuta una vez:"
  echo "   python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  echo ""
  read -r -p "Pulsa Enter para cerrar..."
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

# Arena flags (no tocan .env permanente; solo esta sesión)
export ARENA_IGRIS_ACTIVA=true
export ARENA_IGRIS_FILLS_VIRTUALES=true
export ARENA_IGRIS_SIN_RANGOS=true
export ARENA_IGRIS_SIN_PACIENCIA=true
export ARENA_IGRIS_UMBRAL_PCT="${ARENA_IGRIS_UMBRAL_PCT:-0.01}"
export ARENA_IGRIS_MORDIDA_USD="${ARENA_IGRIS_MORDIDA_USD:-5}"
export ARENA_IGRIS_EQUITY_USD="${ARENA_IGRIS_EQUITY_USD:-500}"
export ARENA_IGRIS_ACTIVOS="$ACTIVOS"
export ARENA_IGRIS_SEGUNDOS_OJOS="$SEGUNDOS"
export MODO_SIMULACION=true
export MODO_TESTNET="${MODO_TESTNET:-True}"

# Ojos Bybit mainnet — no hace falta API key para WS público
# (si .env tiene keys testnet, no se usan en fills virtuales)

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/arena_igris_${STAMP}.log"

echo "→ Smoke Igris (rápido)..."
if ! python scripts/validar_igris_smoke.py 2>&1 | tee -a "$LOG_FILE"; then
  echo ""
  echo "❌ Smoke falló — revisa $LOG_FILE"
  read -r -p "Pulsa Enter para cerrar..."
  exit 1
fi

echo ""
echo "→ Arena aislada (ojos mainnet ${SEGUNDOS}s)..."
echo "   Log: $LOG_FILE"
echo ""

if python scripts/arena_igris_aislado.py --segundos "$SEGUNDOS" 2>&1 | tee -a "$LOG_FILE"; then
  echo ""
  echo "✅ Arena terminada."
  echo "   Reporte: $ROOT/data/arena_igris_report.json"
  echo "   Historial: $ROOT/data/historial_hierro.jsonl"
  echo "   Log: $LOG_FILE"
else
  echo ""
  echo "❌ Arena falló — revisa $LOG_FILE"
  read -r -p "Pulsa Enter para cerrar..."
  exit 1
fi

echo ""
if command -v open >/dev/null 2>&1; then
  open "$ROOT/data/arena_igris_report.json" 2>/dev/null || true
fi

read -r -p "Pulsa Enter para cerrar..."
exit 0
