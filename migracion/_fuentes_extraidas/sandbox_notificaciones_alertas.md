# Incubación · Notificaciones Alertas

> Track B · Compostera — evolución sobre acumulación.

#### #Notificaciones_Alertas

## 💡 Notificaciones_Alertas
### 🎯 Contexto y Trigger
Define una jerarquía de notificaciones para el bot de trading, diferenciando entre alertas críticas que requieren atención inmediata (Telegram con sonido) y notificaciones informativas (Telegram sin sonido o consola).
### ⚙️ Lógica Operativa
- **Alerta Crítica:** Enviar a Telegram con sonido.
    - Inicio/Apagado del Bot: Confirmación de inicio exitoso o cierre inesperado.
    - Errores de la API o Red: Problemas de conexión, saldo insuficiente, etc.
- **Ejecución (Fill):** Enviar a Telegram sin sonido.
    - Notificación solo cuando una orden se completa con éxito.
- **Resumen de Salud:** Enviar a Telegram una vez al día.
    - Estado general del bot: Operatividad, conexión a la API, número de órdenes activas.
- **Eventos Exclusivos de Consola:**
    - Reponiendo nivel...
    - Limpiando orden [obsoleta]...
    - Avisos de revisión del loop de 10 segundos.
### ⚠️ Restricciones / Notas Tácticas
La sobrecarga de notificaciones puede llevar a la fatiga del usuario y a la desactivación de las alertas importantes. La selección cuidadosa de eventos para notificar es crucial para mantener la efectividad del sistema.

## 📂 Contexto del Intercambio

<details><summary>Intervención Monarca + contexto IA (colapsado)</summary>

**Monarca:**
¿Eso de mandar notificaciones sólo se puede a Telegram o también a WhatsApp? ¿Cuál es mejor, en temas de privacidad, por ejemplo?
¿Qué sugerencias de notificaciones me recomiendas para que me lleguen a Telegram?

**IA (explicación):**
Para un bot de trading, la regla de oro de las notificaciones es: "Si todo es urgente, nada es urgente". Si el bot te avisa cada vez que pone o cancela una orden para ajustar la grid, tu teléfono no dejará de sonar, terminarás silenciando el chat y te perderás los avisos importantes. Aquí te dejo mi sugerencia de la jerarquía ideal de notificaciones, separadas por lo que debes enviar a Telegram vs. lo que debe quedarse solo en la consola de tu PC: 1. 🚨 Alertas Críticas (Deben hacer sonar tu teléfono) Estas son cosas que requieren tu atención inmediata porque significan que el bot no está oper…

**IA (pregunta):**
¿Te gustaría que redactemos la función enviar_telegram(mensaje) para integrarla directamente en tu código y asignarla solo a los eventos importantes?

</details>