#!/bin/bash
# Doble clic en Finder (macOS) → arranca arise.py + panel web.
# Libera el puerto del Pergamino de forma agresiva antes de servir.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PORT="${PANEL_PORT:-8080}"
LOG_DIR="$ROOT/data/logs"
mkdir -p "$LOG_DIR" "$ROOT/data"

echo ""
echo "═══════════════════════════════════════════════"
echo "  🌑 Shadow Army — Iniciar Panel"
echo "═══════════════════════════════════════════════"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo ""
  echo "❌ No existe .venv en $ROOT"
  echo "   Ejecuta: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  echo ""
  read -r -p "Pulsa Enter para cerrar..."
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

liberar_puerto() {
  local port="$1"
  echo "→ Liberando puerto ${port}..."
  # Solo el servidor web del Pergamino — NO matar arise_igris / rituales live
  pkill -f "http.server ${port}" 2>/dev/null || true
  pkill -f "http.server.*${port}" 2>/dev/null || true
  # Matar lo que escuche el puerto (macOS)
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${pids}" ]]; then
      echo "  · Procesos en :${port} → ${pids//$'\n'/ }"
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
liberar_puerto "$PORT"

# Si Igris live (u otro ejército) ya corre, solo servir el Pergamino
SKIP_ARISE=0
if [[ "${PANEL_SOLO_WEB:-}" == "1" ]] || pgrep -f "scripts/arise_igris.py" >/dev/null 2>&1; then
  SKIP_ARISE=1
  echo "→ Ritual live detectado (o PANEL_SOLO_WEB=1) — no arranco arise.py"
fi

if [[ "$SKIP_ARISE" -eq 0 ]]; then
  echo "→ Activando arise.py (ejército)..."
  PYTHONUNBUFFERED=1 nohup python "$ROOT/arise.py" >> "$LOG_DIR/arise_panel.log" 2>&1 &
  ARISE_PID=$!
  echo "$ARISE_PID" > "$ROOT/data/panel_arise.pid"

  ARISE_OK=0
  for i in $(seq 1 30); do
    if ! kill -0 "$ARISE_PID" 2>/dev/null; then
      echo "❌ arise.py murió al arrancar. Revisa: data/logs/arise_panel.log"
      tail -n 40 "$LOG_DIR/arise_panel.log" 2>/dev/null || true
      read -r -p "Pulsa Enter para cerrar..."
      exit 1
    fi
    if [[ -f "$ROOT/data/estado_vivo.json" ]] || [[ "$i" -ge 6 ]]; then
      ARISE_OK=1
      break
    fi
    sleep 0.5
  done

  if [[ "$ARISE_OK" -ne 1 ]]; then
    echo "❌ Timeout esperando arise.py"
    read -r -p "Pulsa Enter para cerrar..."
    exit 1
  fi
  echo "  ✓ arise.py activo (PID ${ARISE_PID})"
else
  echo "  ✓ Solo Pergamino web (estado_vivo lo escribe el ritual ya vivo)"
fi

# Si el puerto sigue ocupado tras liberar, reintentar una vez
if command -v lsof >/dev/null 2>&1; then
  if lsof -tiTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ⚠ Puerto ${PORT} aún ocupado — segundo intento de liberación..."
    liberar_puerto "$PORT"
  fi
fi

echo "→ Levantando servidor del Pergamino (puerto ${PORT})..."
nohup python -m http.server "$PORT" --directory "$ROOT" >> "$LOG_DIR/panel_http.log" 2>&1 &
HTTP_PID=$!
echo "$HTTP_PID" > "$ROOT/data/panel_http.pid"
sleep 1

if ! kill -0 "$HTTP_PID" 2>/dev/null; then
  # ¿Alguien más quedó sirviendo el puerto? Reutilizar y abrir igual
  if command -v lsof >/dev/null 2>&1 && lsof -tiTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    HTTP_PID="$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN | head -1)"
    echo "$HTTP_PID" > "$ROOT/data/panel_http.pid"
    echo "  ✓ Reutilizando servidor ya activo en :${PORT} (PID ${HTTP_PID})"
  else
    echo "❌ http.server no arrancó. Revisa: data/logs/panel_http.log"
    tail -n 20 "$LOG_DIR/panel_http.log" 2>/dev/null || true
    read -r -p "Pulsa Enter para cerrar..."
    exit 1
  fi
else
  echo "  ✓ http.server activo (PID ${HTTP_PID})"
fi

CACHE_BUST="$(date +%s)"
URL_CLASICO="http://localhost:${PORT}/dashboard_sombras.html?v=${CACHE_BUST}"

# Pergamino React (Cascada + Manto Igris Figma) — puerto 5173
VITE_PORT="${VITE_PORT:-5173}"
URL_REACT="http://localhost:${VITE_PORT}/"
echo "→ Levantando Pergamino React (Vite :${VITE_PORT})..."
if [[ ! -d "$ROOT/ui/node_modules" ]]; then
  echo "  · npm install en ui/ (primera vez)..."
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
VITE_PID=$!
echo "$VITE_PID" > "$ROOT/data/panel_vite.pid"
sleep 2
echo "→ Abriendo Cascada React (clic Igris = Manto Figma)..."
open "$URL_REACT"

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ Panel listo — arise activo al abrir"
echo "  arise.py      → PID ${ARISE_PID}"
echo "  http.server   → PID ${HTTP_PID} (puerto ${PORT})"
echo "  Vite React    → PID ${VITE_PID} (puerto ${VITE_PORT})"
echo "  Cascada Igris → ${URL_REACT}   ← USA ESTA (clic Igris)"
echo "  Clásico HTML  → ${URL_CLASICO}"
echo "  Logs          → data/logs/"
echo "═══════════════════════════════════════════════"
echo ""
read -r -p "Pulsa Enter para cerrar esta ventana (arise y el servidor siguen activos)..."
