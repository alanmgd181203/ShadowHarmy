# ORDEN al Cursor del VPS — túnel VIP + llave git (push)

Ejecuta **todo**. El Monarca pega este mensaje entero (con el token rellenado).

---

## A) Llave de la forja (GitHub) — para pull/push

El Monarca te entrega el token **solo en este chat**. No lo guardes en archivos del repo ni hagas `git commit` de `.env`/URL con secreto.

```bash
# Sustituye PEGAR_TOKEN_AQUI por el valor que te pegó el Monarca
export GH_TOKEN='PEGAR_TOKEN_AQUI'
REPO_DIR=/root/ShadowHarmy
if [ ! -d "$REPO_DIR/.git" ]; then
  REPO_DIR=/home/monarca/ShadowHarmy
fi
cd "$REPO_DIR" || { echo "No hallé ShadowHarmy; clona:"; exit 1; }

git remote set-url origin "https://x-access-token:${GH_TOKEN}@github.com/alanmgd181203/ShadowHarmy.git"
git config --global user.email "monarca-vps@local"
git config --global user.name "ShadowArmy VPS"
git pull origin master

# Si hay cambios locales del VPS (campo/cuartel, etc.) que deban subir:
#   git status
#   git add <archivos del trabajo>   # NUNCA .env ni *.key ni shadow-vip.conf
#   git commit -m "VPS: …"
#   git push origin master

# Quita el token de la URL tras el push (deja remoto limpio; el helper/store es opcional)
git remote set-url origin https://github.com/alanmgd181203/ShadowHarmy.git
unset GH_TOKEN
```

**Pull:** el repo es público; si el pull falla por otra cosa, sigue con WireGuard.  
**Push:** sin token válido no sube. Si el push falla, reporta el error y no inventes otro remoto.

---

## B) Túnel VIP (WireGuard) — lo principal hoy

IP: `45.77.34.52`. Apaga el ejército pesado; el VPS solo es pase VIP.

### 1) Parar carga

```bash
tmux kill-session -t ojos 2>/dev/null || true
pkill -f 'arise_ojos_tusk|arise_campo|arise.py' 2>/dev/null || true
free -h
```

### 2) Instalar WireGuard + forward

```bash
apt-get update -y
apt-get install -y wireguard wireguard-tools iptables
ip -o -4 route show to default | awk '{print $5}'
echo 'net.ipv4.ip_forward=1' >/etc/sysctl.d/99-wireguard-forward.conf
sysctl -p /etc/sysctl.d/99-wireguard-forward.conf
```

### 3) Claves

```bash
umask 077
mkdir -p /etc/wireguard && cd /etc/wireguard
wg genkey | tee server_private.key | wg pubkey > server_public.key
wg genkey | tee client_private.key | wg pubkey > client_public.key
chmod 600 server_private.key client_private.key
```

### 4) Servidor wg0

```bash
WG_IF=$(ip -o -4 route show to default | awk '{print $5}')
SERVER_PRIV=$(cat /etc/wireguard/server_private.key)
CLIENT_PUB=$(cat /etc/wireguard/client_public.key)
cat >/etc/wireguard/wg0.conf <<EOF
[Interface]
Address = 10.66.66.1/24
ListenPort = 51820
PrivateKey = ${SERVER_PRIV}
PostUp = iptables -t nat -A POSTROUTING -o ${WG_IF} -j MASQUERADE; iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o ${WG_IF} -j MASQUERADE; iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT

[Peer]
PublicKey = ${CLIENT_PUB}
AllowedIPs = 10.66.66.2/32
EOF
chmod 600 /etc/wireguard/wg0.conf
```

### 5) Firewall + arrancar

```bash
ufw allow 51820/udp
ufw allow OpenSSH
ufw --force enable
systemctl enable --now wg-quick@wg0
wg show
```

### 6) Entregar perfil Windows al Monarca

```bash
CLIENT_PRIV=$(cat /etc/wireguard/client_private.key)
SERVER_PUB=$(cat /etc/wireguard/server_public.key)
cat >/root/shadow-vip.conf <<EOF
[Interface]
PrivateKey = ${CLIENT_PRIV}
Address = 10.66.66.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = ${SERVER_PUB}
Endpoint = 45.77.34.52:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF
chmod 600 /root/shadow-vip.conf
cat /root/shadow-vip.conf
```

No subas `shadow-vip.conf` ni keys a git.

### 7) Reporte al Monarca

Git (si aplicó): pull OK / push OK o error.  
WireGuard activo · 51820/udp · arise apagado · `shadow-vip.conf` pegado aquí.
