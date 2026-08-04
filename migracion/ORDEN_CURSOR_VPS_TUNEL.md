# ORDEN al Cursor del VPS — montar túnel VIP (WireGuard)

Copia **todo** este mensaje al Agent del VPS (Singapur / `ShadowArmy`).

---

## Contexto (sucesión)

El Monarca decidió: el VPS **ya no corre el ejército pesado** (se ahoga la RAM con WS/Tank/Kaiser). El VPS solo es **túnel WireGuard** para que la **lap** use la IP de Singapur y Bybit no bloquee USA.

- IP servidor: `45.77.34.52`
- Repo: `/root/ShadowHarmy` (o donde esté)
- Tras el túnel: **apagar** `tmux`/`arise`/`arise_campo` pesados en este VPS.
- No subas claves privadas a git. Entrégale al Monarca solo el archivo `.conf` del cliente (por chat seguro / copiar).

Lee tono: `migracion/17_GUIA_MONARCA.md` si respondes al Monarca.

---

## Tareas (ejecutar como root)

### 1) Parar carga del ejército (liberar RAM)

```bash
tmux kill-session -t ojos 2>/dev/null || true
tmux ls 2>/dev/null || true
pkill -f 'arise_ojos_tusk|arise_campo|arise.py' 2>/dev/null || true
free -h
```

### 2) Instalar WireGuard + IP forward

```bash
apt-get update -y
apt-get install -y wireguard wireguard-tools iptables
# Interfaz pública (suele ser ens3 o eth0):
ip -o -4 route show to default | awk '{print $5}'
```

Anota la interfaz (ej. `ens3`) = `WG_IF`.

```bash
echo 'net.ipv4.ip_forward=1' >/etc/sysctl.d/99-wireguard-forward.conf
sysctl -p /etc/sysctl.d/99-wireguard-forward.conf
```

### 3) Generar claves servidor + cliente

```bash
umask 077
mkdir -p /etc/wireguard
cd /etc/wireguard
wg genkey | tee server_private.key | wg pubkey > server_public.key
wg genkey | tee client_private.key | wg pubkey > client_public.key
chmod 600 server_private.key client_private.key
```

### 4) Config servidor `/etc/wireguard/wg0.conf`

Sustituye `WG_IF` por la interfaz real (ens3/eth0). Las claves: `$(cat ...)` en el heredoc.

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

### 6) Perfil Windows para el Monarca

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
echo "==== ENTREGAR AL MONARCA: contenido de /root/shadow-vip.conf ===="
cat /root/shadow-vip.conf
```

**Entrega:** muestra al Monarca el contenido de `shadow-vip.conf` (o `scp`) — es el único secreto del cliente. No lo commits a git.

### 7) Confirmar al Monarca

Reporta en lenguaje claro:

- WireGuard `wg show` activo  
- Puerto 51820/udp abierto  
- Procesos arise apagados · RAM libre  
- Que ya puede importar `shadow-vip.conf` en WireGuard Windows  

---

## Qué NO hacer

- No dejes `arise_ojos` / forja Kaiser corriendo en el VPS “por si acaso”.  
- No uses `AllowedIPs` vacío.  
- No publiques las private keys en el repo.
