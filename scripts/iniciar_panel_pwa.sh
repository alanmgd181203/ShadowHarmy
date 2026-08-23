#!/bin/bash
# Shadow Army — Cascada React en el celular (PWA + túnel HTTPS)
# NO despierta ni mata Beru / Igris / arise.
#
# Uso:
#   ./scripts/iniciar_panel_pwa.sh
#   VITE_PORT=5173 ./scripts/iniciar_panel_pwa.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
UI="$ROOT/ui"
PORT="${VITE_PORT:-5173}"
LOG_DIR="$ROOT/data/logs"
TOOLS="$ROOT/tools"
mkdir -p "$LOG_DIR" "$TOOLS" "$ROOT/data"

find_cloudflared() {
  if command -v cloudflared >/dev/null 2>&1; then
    command -v cloudflared
    return
  fi
  if [[ -x "$TOOLS/cloudflared" ]]; then
    echo "$TOOLS/cloudflared"
    return
  fi
  echo ""
}

liberar_puerto() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${pids}" ]]; then
      # shellcheck disable=SC2086
      kill ${pids} 2>/dev/null || true
      sleep 0.4
    fi
  fi
}

echo ""
echo "=== Shadow Army - Cascada al celular (HTTPS) ==="
echo "No toca Beru ni Igris. Solo abre el Pergamino nuevo."
echo ""

if ! command -v npm >/dev/null 2>&1; then
  echo "No hay npm/Node en PATH. Instálalo y vuelve a correr este ritual."
  exit 1
fi

CF="$(find_cloudflared)"
if [[ -z "$CF" ]]; then
  echo "cloudflared no encontrado. Instálalo (brew install cloudflared)"
  echo "o coloca el binario en tools/cloudflared"
  exit 1
fi

if [[ ! -d "$UI/node_modules" ]]; then
  echo "Instalando piezas del Pergamino (npm install)..."
  (cd "$UI" && npm install --no-fund --no-audit)
fi

echo "Forjando Cascada (npm run build)..."
(cd "$UI" && npm run build)

liberar_puerto "$PORT"

echo "Sirviendo Cascada en :${PORT} ..."
nohup bash -c "cd \"$UI\" && npm run preview -- --host --port ${PORT}" \
  >> "$LOG_DIR/panel_vite.log" 2>&1 &
echo $! > "$ROOT/data/panel_vite.pid"
sleep 2

echo "Abriendo túnel Cloudflare (HTTPS) ..."
rm -f "$LOG_DIR/cloudflared_pwa_out.log" "$LOG_DIR/cloudflared_pwa_err.log"
nohup "$CF" tunnel --url "http://127.0.0.1:${PORT}" \
  >> "$LOG_DIR/cloudflared_pwa_out.log" 2>> "$LOG_DIR/cloudflared_pwa_err.log" &
echo $! > "$ROOT/data/panel_vite_tunnel.pid"

HTTPS_URL=""
for _ in $(seq 1 40); do
  sleep 0.5
  TXT="$(cat "$LOG_DIR/cloudflared_pwa_err.log" "$LOG_DIR/cloudflared_pwa_out.log" 2>/dev/null || true)"
  if echo "$TXT" | grep -Eo 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' >/dev/null 2>&1; then
    HTTPS_URL="$(echo "$TXT" | grep -Eo 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' | head -n 1)"
    break
  fi
done

echo ""
if [[ -n "$HTTPS_URL" ]]; then
  echo "LISTO — usa ESTA URL en el celular (raíz, no dashboard_sombras):"
  echo "  $HTTPS_URL"
  echo ""
  echo "En Android Chrome: abrir URL → ⋮ Instalar app → borra el icono viejo."
  echo "En iPhone: Compartir → Añadir a pantalla de inicio."
  echo ""
  echo "En esta PC: http://127.0.0.1:${PORT}/"
else
  echo "Túnel arrancó pero no leí la URL a tiempo."
  echo "Revisa data/logs/cloudflared_pwa_err.log"
  echo "Cascada local: http://127.0.0.1:${PORT}/"
fi

echo "  Detener: ./scripts/detener_panel.sh"
echo ""
