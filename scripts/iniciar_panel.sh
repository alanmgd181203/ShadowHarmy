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

matar_arise() {
  pkill -f "python.*arise.py" 2>/dev/null || true
  pkill -f "ShadowHarmy/arise.py" 2>/dev/null || true
  if [[ -f "$ROOT/data/panel_arise.pid" ]]; then
    local old
    old="$(cat "$ROOT/data/panel_arise.pid" 2>/dev/null || true)"
    if [[ -n "${old}" ]]; then
      kill "${old}" 2>/dev/null || true
      sleep 0.2
      kill -9 "${old}" 2>/dev/null || true
    fi
  fi
  if command -v pgrep >/dev/null 2>&1; then
    while read -r p; do
      [[ -n "$p" ]] || continue
      kill "$p" 2>/dev/null || true
      sleep 0.1
      kill -9 "$p" 2>/dev/null || true
    done < <(pgrep -f "$ROOT/arise.py" 2>/dev/null || true)
  fi
}

liberar_http() {
  local port="$1"
  pkill -f "http.server ${port}" 2>/dev/null || true
  pkill -f "http.server.*${port}" 2>/dev/null || true
  pkill -f "panel_http_server.py" 2>/dev/null || true
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
  sleep 0.3
}

echo ""
echo "🌑 Shadow Army — preparando panel..."
matar_arise
liberar_http "$PORT"

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

# Solo liberar http — NUNCA matar arise aquí
if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  liberar_http "$PORT"
fi

nohup python scripts/panel_http_server.py --port "$PORT" --directory "$ROOT" >> "$LOG_DIR/panel_http.log" 2>&1 &
HTTP_PID=$!
echo "$HTTP_PID" > "$ROOT/data/panel_http.pid"
sleep 1

if ! kill -0 "$HTTP_PID" 2>/dev/null; then
  if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    HTTP_PID="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN | head -1)"
    echo "$HTTP_PID" > "$ROOT/data/panel_http.pid"
    echo "  ✓ Reutilizando servidor en :${PORT} (PID ${HTTP_PID})"
  else
    echo "❌ panel_http no arrancó — ver data/logs/panel_http.log"
    exit 1
  fi
fi

if ! kill -0 "$ARISE_PID" 2>/dev/null; then
  echo "❌ arise.py murió tras abrir http — ver data/logs/arise_panel.log"
  exit 1
fi

CACHE_BUST="$(date +%s)"
URL_CLASICO="http://localhost:${PORT}/dashboard_sombras.html?v=${CACHE_BUST}"

VITE_PORT="${VITE_PORT:-5173}"
URL_REACT="http://localhost:${VITE_PORT}/"
echo "→ Levantando Pergamino React (Vite :${VITE_PORT})..."
if [[ ! -d "$ROOT/ui/node_modules" ]]; then
  (cd "$ROOT/ui" && npm install --silent) || true
fi
if command -v lsof >/dev/null 2>&1; then
  pids="$(lsof -tiTCP:"${VITE_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    # shellcheck disable=SC2086
    kill ${pids} 2>/dev/null || true
    sleep 0.3
  fi
fi
nohup bash -c "cd \"$ROOT/ui\" && npm run dev -- --host --port ${VITE_PORT}" >> "$LOG_DIR/panel_vite.log" 2>&1 &
echo $! > "$ROOT/data/panel_vite.pid"
sleep 2
open "$URL_REACT"

echo ""
echo "  Cascada React → ${URL_REACT}  (clic Igris = Manto)"
echo "  Clásico HTML  → ${URL_CLASICO}"
echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ Panel listo (arise activo al abrir)"
echo "  arise.py      → PID ${ARISE_PID}"
echo "  panel_http    → PID ${HTTP_PID} (puerto ${PORT})"
echo "  Pergamino     → http://localhost:${PORT}/dashboard_sombras.html"
echo "  Logs          → data/logs/"
echo "═══════════════════════════════════════════════"
echo ""
