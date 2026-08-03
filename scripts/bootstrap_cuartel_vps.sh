#!/usr/bin/env bash
# Bootstrap cuartel VPS — Shadow Army (ojos 24/7, sin manos).
# Correr como root en el VPS (Cursor Remote / SSH):
#   bash scripts/bootstrap_cuartel_vps.sh
# O sin repo aún:
#   curl -fsSL https://raw.githubusercontent.com/alanmgd181203/ShadowHarmy/master/scripts/bootstrap_cuartel_vps.sh | bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/alanmgd181203/ShadowHarmy.git}"
# Casa del monarca (evita /root 700 bloqueando al usuario monarca)
APP_DIR="${APP_DIR:-/home/monarca/ShadowHarmy}"
USER_NAME="${USER_NAME:-monarca}"

echo "[1/6] apt update + paquetes base"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git python3 python3-pip python3-venv tmux ufw curl ca-certificates

echo "[2/6] usuario ${USER_NAME} (si no existe)"
if ! id -u "$USER_NAME" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "Shadow Monarca" "$USER_NAME" || true
  usermod -aG sudo "$USER_NAME" || true
  echo "${USER_NAME} ALL=(ALL) NOPASSWD:ALL" >"/etc/sudoers.d/${USER_NAME}"
  chmod 440 "/etc/sudoers.d/${USER_NAME}"
fi
# Homedir usable
chmod 755 "/home/${USER_NAME}" 2>/dev/null || true

echo "[3/6] firewall SSH"
ufw allow OpenSSH || true
ufw --force enable || true

echo "[4/6] clone repo → ${APP_DIR}"
if [[ ! -d "${APP_DIR}/.git" ]]; then
  sudo -u "$USER_NAME" git clone "$REPO_URL" "$APP_DIR"
else
  sudo -u "$USER_NAME" git -C "$APP_DIR" pull --ff-only || true
fi
chown -R "${USER_NAME}:${USER_NAME}" "$APP_DIR"

echo "[5/6] venv + pip"
sudo -u "$USER_NAME" bash -lc "
  cd '$APP_DIR'
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -U pip
  pip install -r requirements.txt
"

echo "[6/6] recordatorio .env"
if [[ ! -f "${APP_DIR}/.env" ]]; then
  cat >"${APP_DIR}/.env.ejemplo_ojos" <<'EOF'
# Copiar a .env y rellenar (NUNCA subir a git)
BYBIT_API_KEY=
BYBIT_API_SECRET=
MODO_TESTNET=False
MODO_SIMULACION=True
ARISE_OJOS_TUSK=true
TUSK_BOVEDA_MANOS=false
EOF
  chown "${USER_NAME}:${USER_NAME}" "${APP_DIR}/.env.ejemplo_ojos" 2>/dev/null || true
  echo "  → Falta ${APP_DIR}/.env  (usa .env.ejemplo_ojos como plantilla)"
else
  chmod 600 "${APP_DIR}/.env"
  echo "  → .env ya existe (ok)"
fi

echo
echo "=== LISTO bootstrap ==="
echo "Siguiente:"
echo "  1) Crear ${APP_DIR}/.env con llaves Bybit (manos OFF)."
echo "  2) Probar:  su - ${USER_NAME} -c 'cd ${APP_DIR} && source .venv/bin/activate && python scripts/arise_ojos_tusk.py --segundos 90'"
echo "  3) 24/7:     tmux new -s ojos → mismo comando sin --segundos → Ctrl+B D"
echo "  4) Cursor:   carpeta ${APP_DIR} como Remote SSH"
echo "Runbook: migracion/24_CUARTEL_VPS.md"
