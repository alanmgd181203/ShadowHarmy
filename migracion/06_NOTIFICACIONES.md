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

- Bellion decide **qué** notificar; no cada `anotar` va al oído del Pergamino.
- Mapeo evento → nivel: `core/bellion_oido.py` (crítico / ejecución / salud / ruido).
- Susurro vivo: `estado_vivo.bellion_oido` · portal Cascada `ui/BellionPanel.jsx`.
- Telegram sigue **legado** (opcional); el camino es el Pergamino.

**Validación:** `python scripts/validar_bellion_oido_smoke.py`

---

## Estado prototipo ShadowHarmy

**Oído 4.1.2 (reglas):** ✅ tabla + anillo + Cascada/panel.  
**Telegram:** no implementado — legado.  
**LLM / chat abierto:** congelado (`15_IDEAS_FUTURO`).

---

## Checklist implementación

- [x] Tabla evento → nivel (`bellion_oido`)
- [x] Susurro en Pergamino (portal Bellion)
- [ ] 4.1.3 Criticos explícitos (crash / API / desconexión larga) — plantillas finas
- [ ] 4.1.4 Fill sin ruido (solo orden completa)
- [ ] 4.1.5 Resumen salud 1×/día
- [ ] Bot token + chat_id en `.env` *(Telegram legado)*
- [ ] Wrapper Telegram con retry *(legado)*
- [ ] Test manual de crítica vs fill
- [ ] Documentar en dashboard consola lo no enviado
