# 06 — Notificaciones y alertas

**Fuente principal:** `sandbox/notificaciones_alertas.md` (destilado limpio, ~2.5 KB).  
**Actualizado:** 2026-07-19 — oído principal = **Pergamino** (app); Telegram = legado / opcional.

## Principio

> Si todo es urgente, nada es urgente.

Sobrecarga → usuario silencia el canal → se pierden fallos reales.

---

## Canal oficial del Monarca (v2)

| Canal | Rol |
|-------|-----|
| **Pergamino / Cascada** (`ui/`, panel vivo) | **Oído principal** — digest Kaiser, manto, Ascensión, memoria barcos |
| **Bellion** (`estado_vivo.json`, historial) | Escriba del ejército hacia la app |
| **Telegram** | **Legado** — stubs 4.1.\*; no es el camino de crecimiento del cuartel |

---

## Jerarquía (legado Telegram — si se reactiva)

### Criticas → Telegram **con sonido** (opcional)

| Evento | Acción humana esperada |
|--------|------------------------|
| Bot iniciado / apagado inesperado | Verificar proceso |
| Error API Bybit | Revisar keys, IP, rate limit |
| Error red / desconexión prolongada | Revisar VPS/internet |
| Saldo insuficiente | Detener o fondear |

### 📋 Ejecución → Telegram **sin sonido**

| Evento | Notas |
|--------|-------|
| Fill confirmado | Solo cuando orden **completa** — no cada amend grid |

### 📊 Salud → Telegram **1×/día**

- Operativo sí/no
- API conectada
- Nº órdenes activas
- NAV resumido (opcional)

### 🖥️ Solo consola

- Reponiendo nivel…
- Limpiando orden obsoleta…
- Avisos loop 10 s
- DISPARO_SIMULADO (dev) → migrar a log Bellion en prod

---

## Función objetivo

```python
async def enviar_telegram(mensaje: str, *, critico: bool = False) -> None:
    ...
```

- `critico=True` → `disable_notification=False`
- Rate limit interno anti-spam

---

## WhatsApp vs Telegram

Manual: **Telegram preferido** (bots API madura, privacidad razonable con bot dedicado).

---

## Integración con Bellion

- Bellion decide **qué** notificar; no cada `anotar` va a Telegram.
- Mapeo evento → nivel en config YAML/JSON.

---

## Estado prototipo ShadowHarmy

**Telegram no implementado** — P1 tras P0 órdenes reales.

---

## Checklist implementación

- [ ] Bot token + chat_id en `.env`
- [ ] Wrapper con retry
- [ ] Tabla evento → nivel
- [ ] Test manual de crítica vs fill
- [ ] Documentar en dashboard consola lo no enviado
