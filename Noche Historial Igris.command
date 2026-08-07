#!/bin/bash
# Noche historial Igris — velas 1 SEGUNDO · ~1 año (L+S) manos OFF
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
mkdir -p "$ROOT/data/coliseo" "$ROOT/data/logs"
source "$ROOT/.venv/bin/activate"
echo "Noche 1s · 365d pedido · linear+inverse · watchdog (Bybit 1s ~1 día real)"
exec caffeinate -i python -u scripts/jess_noche_historial_igris.py --dias 365 --watchdog --watchdog-min 15 --interval 1s --markets linear,inverse
