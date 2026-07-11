#!/bin/bash
# Reinicia arise.py + servidor del dashboard y abre el Pergamino.
# Libera el puerto con lsof antes de servir (evita Address already in use).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PORT="${PANEL_PORT:-8080}"
LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR" "$ROOT/data"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo ""
  echo "❌ No existe .venv en $ROOT"
  echo "   Ejecuta primero: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

liberar_puerto() {
  local port="$1"
  pkill -f "http.server ${port}" 2>/dev/null || true
  pkill -f "http.server.*${port}" 2>/dev/null || true
  pkill -f "python.*arise.py" 2>/dev/null || true
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${pids}" ]]; then
      # shellcheck disable=SC2086
      kill ${pids} 2>/dev/null || true
      sleep 0.5
      pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
      if [[ -n "${pids}" ]]; then
        # shellcheck disable=SC2086
        kill -9 ${pids} 2>/dev/null || true
      fi
    fi
  fi
  sleep 0.5
}

echo ""
echo "🌑 Shadow Army — preparando panel..."
liberar_puerto "$PORT"

echo "→ Activando arise.py..."
PYTHONUNBUFFERED=1 nohup python "$ROOT/arise.py" >> "$LOG_DIR/arise_panel.log" 2>&1 &
ARISE_PID=$!
echo "$ARISE_PID" > "$ROOT/data/panel_arise.pid"

for i in $(seq 1 30); do
  if ! kill -0 "$ARISE_PID" 2>/dev/null; then
    echo "❌ arise.py murió al arrancar — ver data/logs/arise_panel.log"
    exit 1
  fi
  if [[ -f "$ROOT/data/estado_vivo.json" ]] || [[ "$i" -ge 6 ]]; then
    break
  fi
  sleep 0.5
done
echo "  ✓ arise.py PID ${ARISE_PID}"

if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  liberar_puerto "$PORT"
fi

nohup python -m http.server "$PORT" --directory "$ROOT" >> "$LOG_DIR/panel_http.log" 2>&1 &
HTTP_PID=$!
echo "$HTTP_PID" > "$ROOT/data/panel_http.pid"
sleep 1

if ! kill -0 "$HTTP_PID" 2>/dev/null; then
  if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    HTTP_PID="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN | head -1)"
    echo "$HTTP_PID" > "$ROOT/data/panel_http.pid"
    echo "  ✓ Reutilizando servidor en :${PORT} (PID ${HTTP_PID})"
  else
    echo "❌ http.server no arrancó — ver data/logs/panel_http.log"
    exit 1
  fi
fi

CACHE_BUST="$(date +%s)"
open "http://localhost:${PORT}/dashboard_sombras.html?v=${CACHE_BUST}"

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ Panel listo (arise activo al abrir)"
echo "  arise.py      → PID ${ARISE_PID}"
echo "  http.server   → PID ${HTTP_PID} (puerto ${PORT})"
echo "  Pergamino     → http://localhost:${PORT}/dashboard_sombras.html"
echo "  Logs          → data/logs/"
echo "═══════════════════════════════════════════════"
echo ""
