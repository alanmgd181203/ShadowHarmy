#!/bin/bash
# Reinicio Igris 4.0.3 Asalto — manto ETH mainnet YA
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
source "$ROOT/.venv/bin/activate"
# Matar guardián/orquestador previo
pkill -f 'vigilar_arise_igris.py' 2>/dev/null || true
pkill -f 'scripts/arise_igris.py' 2>/dev/null || true
sleep 1
python3 scripts/set_marcha_cli.py --id asalto
# Lentes más tolerantes mientras WS se estabiliza + REST
export IGRIS_LIBRO_STALE_S=45
export IGRIS_LIBRO_REST_FALLBACK=true
export ESCALERA_IGRIS_ACTIVA=false
export MODO_SIMULACION=False
export BRIDGE_WS_SUBSCRIBE_BOOKS=true
echo "→ Asalto Igris mainnet hasta 2026-08-07T18:30"
exec python3 scripts/vigilar_arise_igris.py --confirmar-go \
  --durar-hasta 2026-08-07T18:30:00 --permitir-mainnet-manos
