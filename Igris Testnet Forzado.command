#!/bin/bash
# Maniobra táctica — Igris LIVE TESTNET fuego forzado (Ley de la Masa)
# Manos: testnet · Ojos: stale 60s · umbral~0 · solo ETH
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR"

echo ""
echo "═══════════════════════════════════════════════"
echo "  Igris TESTNET — fuego forzado · Ley de la Masa"
echo "═══════════════════════════════════════════════"

# Abortar si quedó fire real mainnet
if pgrep -f 'arise_igris.py' >/dev/null 2>&1; then
  echo "ABORT: detectado arise_igris — matando zombi..."
  pkill -f 'arise_igris.py' || true
  sleep 1
fi

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "No existe .venv"
  read -r -p "Enter para cerrar..."
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

export LIVE_IGRIS_FORZAR_DISPARO=true
export LIVE_IGRIS_ACTIVOS=ETH
export LIVE_IGRIS_MORDIDA_MAX_USD=25
export LIVE_IGRIS_SEGUNDOS_OJOS=45
export IGRIS_LIBRO_STALE_S=60
export ARENA_IGRIS_UMBRAL_PCT=0
export MODO_TESTNET=True
export MODO_SIMULACION=False
export SAFE_MODE=true

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/igris_live_forzado_${STAMP}.log"

echo "→ LIVE forzado ETH (stale 60s, umbral 0)..."
echo "   Log: $LOG_FILE"
echo ""

set +e
python scripts/igris_live_testnet.py --segundos 45 --activos ETH 2>&1 | tee -a "$LOG_FILE"
RC=${PIPESTATUS[0]}
set -e

echo ""
echo "Reporte: $ROOT/data/igris_live_testnet_report.json"
if [[ -f "$ROOT/data/igris_live_testnet_report.json" ]]; then
  python3 - <<'PY'
import json
from pathlib import Path
r = json.loads(Path("data/igris_live_testnet_report.json").read_text())
print("veredicto:", r.get("veredicto"))
print("disparos_ok:", r.get("disparos_ok"))
lm = r.get("ley_masa_impacto") or {}
print("ley_masa:", json.dumps(lm, indent=2, ensure_ascii=False))
pos = r.get("posiciones_exchange") or {}
print("posiciones:", json.dumps(pos, indent=2, ensure_ascii=False)[:2000])
PY
fi

read -r -p "Enter para cerrar..."
exit "$RC"
