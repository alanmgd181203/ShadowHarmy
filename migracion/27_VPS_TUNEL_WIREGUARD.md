# 27 — VPS como túnel VIP (WireGuard) → ejército en la lap

**Decisión Monarca:** 2026-08-03 — el Vultr Singapur deja de ahogarse corriendo Tank/Kaiser; pasa a ser **pase VIP** (IP SG). El **cuartel / forja** corre en la lap (RAM de verdad).

| Casa | Rol |
|------|-----|
| **VPS** `45.77.34.52` | Solo WireGuard + NAT. **Apagar** arise/tmux pesados. |
| **Lap (este PC)** | `git pull` · ojos · forja Kaiser · pruebas rápidas · Cursor Agent principal |

No es “VPN Vultr de catálogo”: es **nuestro** WireGuard sobre el droplet (crédito Vultr = compute).

---

## Lado lap (Monarca / este Cursor)

1. Instalar [WireGuard para Windows](https://www.wireguard.com/install/).
2. Esperar el archivo `shadow-vip.conf` que genere el Cursor del VPS (o pegarlo).
3. WireGuard → **Add Tunnel** → Importar `shadow-vip.conf` → **Activate**.
4. Probar geo / Bybit:

```powershell
curl.exe -s https://api.ipify.org
# Debe parecerse a 45.77.34.52 (o la IP pública del droplet)

cd C:\Users\alans\Desktop\ShadowHarmy
git pull origin master
# .env: MODO_TESTNET=False · MODO_SIMULACION=True
python scripts/arise_ojos_tusk.py --segundos 90
```

5. Si ojos OK aquí: este PC es el cuartel; VPS solo túnel.

**AllowedIPs:** el perfil usa `0.0.0.0/0` (túnel completo) para que Bybit no vea USA. Luego se puede afinar.

---

## Lado VPS — orden lista para el otro Cursor

Pegar el bloque en [`ORDEN_CURSOR_VPS_TUNEL.md`](ORDEN_CURSOR_VPS_TUNEL.md).

---

## Seguridad

- No subir `.conf` con claves privadas a git.
- Puerto UDP **51820** en ufw.
- Con túnel OK, apagar procesos Python del ejército en el VPS.
