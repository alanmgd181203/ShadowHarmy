#!/bin/bash
# Detiene arise.py y el servidor del dashboard (libera el puerto con lsof).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PANEL_PORT:-8080}"

pkill -f "python.*arise.py" 2>/dev/null || true
pkill -f "ShadowHarmy/arise.py" 2>/dev/null || true
if [[ -f "$ROOT/data/panel_arise.pid" ]]; then
  OLD_PID="$(cat "$ROOT/data/panel_arise.pid" 2>/dev/null || true)"
  if [[ -n "${OLD_PID}" ]]; then
    kill "${OLD_PID}" 2>/dev/null || true
    sleep 0.2
    kill -9 "${OLD_PID}" 2>/dev/null || true
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

pkill -f "http.server ${PORT}" 2>/dev/null || true
pkill -f "http.server.*${PORT}" 2>/dev/null || true
pkill -f "panel_http_server.py" 2>/dev/null || true

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

# Vite Cascada React
VITE_PORT="${VITE_PORT:-5173}"
if [[ -f "$ROOT/data/panel_vite.pid" ]]; then
  VP="$(cat "$ROOT/data/panel_vite.pid" 2>/dev/null || true)"
  if [[ -n "${VP}" ]]; then
    kill "${VP}" 2>/dev/null || true
    sleep 0.2
    kill -9 "${VP}" 2>/dev/null || true
  fi
fi
if command -v lsof >/dev/null 2>&1; then
  VPIDS="$(lsof -tiTCP:"${VITE_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${VPIDS}" ]]; then
    # shellcheck disable=SC2086
    kill ${VPIDS} 2>/dev/null || true
    sleep 0.2
    VPIDS="$(lsof -tiTCP:"${VITE_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${VPIDS}" ]]; then
      # shellcheck disable=SC2086
      kill -9 ${VPIDS} 2>/dev/null || true
    fi
  fi
fi

rm -f "$ROOT/data/panel_arise.pid" "$ROOT/data/panel_http.pid" "$ROOT/data/panel_vite.pid"

echo "🌑 Panel detenido (arise + http:${PORT} + vite:${VITE_PORT})."
