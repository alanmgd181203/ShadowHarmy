# 24 — Cuartel VPS (casa fija del ejército)

**Decisión Monarca:** 2026-08-02 — migrar el **cuartel vivo** a un VPS (ojos 24/7, Bybit fuera de USA).  
**Jess / Mac México:** queda como **respaldo**, no como casa principal.  
**Cursor:** sigues en tu laptop USA → **Remote SSH** al VPS (un solo Cursor, un solo campamento).

No hace falta IA pesada: 1 vCPU + 1–2 GB RAM (~USD 4–6/mes) basta.

---

## Qué vas a conseguir

- Ojos (Tank/Kaiser/Tusk) que **no se apagan** al cerrar una lap.
- Memoria Kaiser (`data/kaiser/samples/`) acumulándose → ETA MNT/BTC dejan de salir `sin_tasa`.
- Bybit sin 403 geo USA.
- Dejas de pelear dos Cursores (México vs local).

---

## Paso 0 — Tú (Monarca) hoy: comprar el servidor

✅ **Hecho (2026-08-02):** Vultr · Singapur · `EjércitoSombra` · IP **`45.77.34.52`** · ~1 GB RAM · Ubuntu.

Siguiente: bootstrap en el VPS (ver § Paso 2b abajo o `scripts/bootstrap_cuartel_vps.sh`).

<details><summary>Si creas otro VPS (referencia)</summary>

1. Proveedor: Vultr / DigitalOcean / Hetzner.
2. Región: Tokio o Singapur.
3. Ubuntu LTS · 1–2 GB RAM.
4. Anotar IP y acceso root/llave.
</details>

---

## Paso 2b — Bootstrap automático (recomendado)

En el VPS como **root** (Cursor Remote ya conectado):

```bash
# Sin repo aún — una sola línea:
curl -fsSL https://raw.githubusercontent.com/alanmgd181203/ShadowHarmy/master/scripts/bootstrap_cuartel_vps.sh -o /tmp/boot.sh
bash /tmp/boot.sh
```

O, si ya clonaste:

```bash
cd /root/ShadowHarmy && git pull && bash scripts/bootstrap_cuartel_vps.sh
```

Luego: copiar `.env` (llaves Bybit, `MODO_SIMULACION=True`, `TUSK_BOVEDA_MANOS=false`) y probar ojos 90 s.

## Paso 1 — Primera conexión (Windows)

En PowerShell (tu PC):

```powershell
ssh root@TU_IP
```

Si pide fingerprint: escribe `yes`. Entras con la contraseña o llave.

**Seguridad mínima (hazlo el primer día):**

```bash
# Actualizar
apt update && apt upgrade -y

# Usuario no-root (recomendado)
adduser monarca
usermod -aG sudo monarca

# Copiar tu llave SSH a monarca (desde tu PC, en otra terminal):
# ssh-copy-id monarca@TU_IP

# Firewall básico
ufw allow OpenSSH
ufw enable
```

Luego entra siempre como `monarca@TU_IP`, no como root.

---

## Paso 2 — Herramientas del ejército

Como `monarca` en el VPS:

```bash
sudo apt install -y git python3 python3-pip python3-venv tmux
git clone https://github.com/alanmgd181203/ShadowHarmy.git
cd ShadowHarmy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si no hay `requirements.txt` o falla algo: avisa en el chat y lo afinamos.

---

## Paso 3 — Secretos (`.env`) — NUNCA a git

En el VPS:

```bash
cd ~/ShadowHarmy
nano .env
```

Mínimo para **ojos mainnet** (sin manos):

```env
BYBIT_API_KEY=tu_key
BYBIT_API_SECRET=tu_secret
MODO_TESTNET=False
MODO_SIMULACION=True
ARISE_OJOS_TUSK=true
TUSK_BOVEDA_MANOS=false
```

Permisos:

```bash
chmod 600 .env
```

Copia el `.env` desde Jess/México o desde tu PC con scp (no lo pegues en Discord/chat público).

```powershell
# Desde tu PC (ejemplo)
scp .env monarca@TU_IP:~/ShadowHarmy/.env
```

---

## Paso 4 — Probar ojos una vez

```bash
cd ~/ShadowHarmy
source .venv/bin/activate
python scripts/arise_ojos_tusk.py --segundos 120
```

Si Tusk ve equity / MNT y Kaiser no truena: el cuartel habla con Bybit. Bien.

---

## Paso 5 — Ojos 24/7 (tmux)

```bash
cd ~/ShadowHarmy
source .venv/bin/activate
tmux new -s ojos
python scripts/arise_ojos_tusk.py
# Detach: Ctrl+B luego D
# Volver: tmux attach -t ojos
```

Así sigue midiendo aunque cierres SSH. Memoria en `data/kaiser/samples/` (no va a git; vive en el VPS).

Más adelante: systemd (arranque al reboot). No es obligatorio el día 1.

---

## Paso 6 — Cursor Remote SSH (tu forma de trabajar)

1. En Cursor / VS Code: extensión **Remote - SSH**.
2. Archivo config SSH (Windows: `C:\Users\alans\.ssh\config`):

```
Host shadow-vps
    HostName TU_IP
    User monarca
    IdentityFile C:\Users\alans\.ssh\id_ed25519
```

3. Cursor → Remote-SSH → Connect to Host → `shadow-vps`.
4. Abre la carpeta `~/ShadowHarmy`.
5. **Un solo chat Agent** sobre ese remoto = el campamento oficial.

Ya no hace falta Tailscale a Jess para el día a día (Jess queda respaldo).

---

## Paso 7 — Informes Monarca (desde el VPS)

Con ojos calientes unos días:

```bash
source .venv/bin/activate
python scripts/informe_sesgo_monarca.py
python scripts/informe_eta_marchas.py --equity 1525
git add migracion/INFORME_*.md data/informe_*.json
git commit -m "Informes desde cuartel VPS."
git push
```

---

## Qué NO hacer el día 1

- No activar `TUSK_BOVEDA_MANOS` ni manos de Igris/Beru.
- No poner el `.env` en git.
- No abrir puertos de panel al mundo sin firewall (si levantas panel, túnel o solo localhost + SSH).
- No migrar “todo México” de golpe: primero ojos + memoria; Igris sim después **en el mismo VPS**.

---

## Checklist rápido

| # | Qué | Quién |
|---|-----|--------|
| A | Comprar VPS Ubuntu Tokio/Singapur 1–2 GB | Monarca |
| B | SSH + usuario + ufw | Monarca (+ guía Agent) |
| C | clone + venv + pip | Agent / Monarca |
| D | `.env` ojos, sim ON, manos OFF | Monarca |
| E | `arise_ojos_tusk` 2 min OK | ambos |
| F | tmux ojos 24/7 | ambos |
| G | Cursor Remote SSH | Monarca |
| H | Informes ETA cuando haya muestras | Agent / Jess / Monarca |

---

## Relaciona

- Ritual ojos: `18_ARRANQUE_TESTNET.md` § ritual ojos · `scripts/arise_ojos_tusk.py`
- Informes: `JESS_INFORME_SESGO.md` (mismos scripts; ahora desde VPS)
- Geo Bybit: `14_ROADMAP.md` (VPS fuera USA)
