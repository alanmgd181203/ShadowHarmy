#!/bin/bash
# Terminal macOS: ./scripts/arena_igris_mac.sh [segundos] [activos]
# Default: 120 s (~2 min), flota completa
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SEGUNDOS="${1:-${ARENA_IGRIS_SEGUNDOS_OJOS:-120}}"
ACTIVOS="${2:-${ARENA_IGRIS_ACTIVOS:-flota}}"

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

if [[ -d "$ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

echo "[arena-mac] smoke + arena ${SEGUNDOS}s (~$(awk "BEGIN{printf \"%.1f\", $SEGUNDOS/60}") min) · ${ACTIVOS}"
python scripts/validar_igris_smoke.py
python scripts/arena_igris_aislado.py --segundos "$SEGUNDOS"
echo "[arena-mac] reporte → data/arena_igris_report.json"
