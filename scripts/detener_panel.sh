#!/bin/bash
# Detiene arise.py y el servidor del dashboard (libera el puerto con lsof).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PANEL_PORT:-8080}"

pkill -f "python.*arise.py" 2>/dev/null || true
pkill -f "http.server ${PORT}" 2>/dev/null || true
pkill -f "http.server.*${PORT}" 2>/dev/null || true

if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${PIDS}" ]]; then
    # shellcheck disable=SC2086
    kill ${PIDS} 2>/dev/null || true
    sleep 0.3
    PIDS="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${PIDS}" ]]; then
      # shellcheck disable=SC2086
      kill -9 ${PIDS} 2>/dev/null || true
    fi
  fi
fi

rm -f "$ROOT/data/panel_arise.pid" "$ROOT/data/panel_http.pid"

echo "🌑 Panel detenido (arise + http:${PORT})."
