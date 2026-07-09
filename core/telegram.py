"""
Telegram — stub Fase 4.1 (M3).
Implementación completa pendiente; hoy solo log en Bellion/consola.

Variables .env (cuando actives):
  TELEGRAM_BOT_TOKEN=
  TELEGRAM_CHAT_ID=
"""
import core.config as config

# Marca stub para validación checklist
STUB = True


async def enviar_telegram(mensaje: str, *, critico: bool = False) -> bool:
    """
    Envía mensaje al Monarca. critico=True → notificación con sonido.
    Retorna True si envió (o stub registró).
    """
    token = getattr(config, "TELEGRAM_BOT_TOKEN", "") or ""
    chat = getattr(config, "TELEGRAM_CHAT_ID", "") or ""

    prefijo = "🚨" if critico else "📋"
    linea = f"{prefijo} [TELEGRAM-STUB] {mensaje}"

    if not token or not chat:
        print(linea)
        return False

    # Fase 4: aquí irá httpx/aiohttp a api.telegram.org
    raise NotImplementedError(
        "Telegram configurado en .env pero envío real no implementado — Fase 4.1"
    )
