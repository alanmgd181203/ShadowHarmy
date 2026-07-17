#!/bin/bash
# Doble clic Finder (macOS México) → Beru LIVE TESTNET checklist 3.9.9
# Órdenes REALES en Bybit DEMO. Ansiedad 1.2% (gatillo ±0.6%), Mariscal, CAZA ~$20.
# 22 barcos flota · solo USDT · spot margen 10x. Sin Igris/Greed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR" "$ROOT/data"

SEGUNDOS="${LIVE_BERU_SEGUNDOS:-3600}"
ACTIVOS="${LIVE_BERU_ACTIVOS:-flota}"
MORDIDA="${LIVE_BERU_MORDIDA_USD:-20}"
LEV="${BERU_SPOT_MARGEN_LEVERAGE:-10}"

echo ""
echo "═══════════════════════════════════════════════"
echo "  Shadow Army — Beru LIVE TESTNET (3.9.9)"
echo "═══════════════════════════════════════════════"
echo "  Manos: Bybit DEMO (órdenes reales spot)"
echo "  Capitán: ANSIEDAD 1.2% → gatillo ±0.6%"
echo "  Tier: Mariscal (PLENO) · clon 0.1%"
echo "  Modo: CAZA · Mordida \$${MORDIDA} · margen ${LEV}x"
echo "  Rails: solo USDT · Activos: ${ACTIVOS}"
echo "  Ojos: ${SEGUNDOS}s (~$((SEGUNDOS / 60)) min)"
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

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/beru_live_testnet_${STAMP}.log"

echo "→ Smoke Beru cazador..."
if ! python scripts/validar_beru_cazador_smoke.py 2>&1 | tee -a "$LOG_FILE"; then
  echo "Smoke falló — $LOG_FILE"
  read -r -p "Enter para cerrar..."
  exit 1
fi

echo ""
echo "→ LIVE testnet (~$((SEGUNDOS / 60)) min ojos)..."
echo "   Log: $LOG_FILE"
echo "   Esperando movimiento ±0.6% desde el 0 de cada semilla."
echo ""

if python scripts/beru_live_testnet.py --segundos "$SEGUNDOS" --activos "$ACTIVOS" 2>&1 | tee -a "$LOG_FILE"; then
  echo ""
  echo "Live terminado."
  echo "  Reporte: $ROOT/data/beru_live_testnet_report.json"
  echo "  Log: $LOG_FILE"
  echo "  Veredicto: abrir el JSON y leer campo veredicto"
else
  echo "Live falló — $LOG_FILE"
  read -r -p "Enter para cerrar..."
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  open "$ROOT/data/beru_live_testnet_report.json" 2>/dev/null || true
fi

read -r -p "Enter para cerrar..."
exit 0
