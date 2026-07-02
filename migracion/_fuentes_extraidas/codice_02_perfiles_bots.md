# Perfiles de Operación

## Bots Activos

### [Nombre del Bot]
- (Reglas y parámetros del bot)

#### #Perfiles_Bots
## 💡 Codigo_Cristalizado
### 🎯 Contexto y Trigger
Este bloque define la lógica de ejecución del módulo Igris dentro de cada Barco Evolucionado. Se activa cuando el barco está en estado activo (`self.activa = True`).
### ⚙️ Lógica Operativa
- Igris analiza la volatilidad actual del mercado (`vol`) en cada tick.
- Si la volatilidad supera un umbral predefinido (0.04), Igris calcula el potencial de fuga de capital debido al spread actual.
- Si el potencial de fuga excede el 1.5% del valor de la posición, Igris ejecuta una orden de cierre inmediato para evitar pérdidas significativas.
- El cierre genera un costo de reparación asociado a la operación, que se descuenta del PnL del barco.
### ⚠️ Restricciones / Notas Tácticas
La efectividad de Igris depende directamente de la precisión del modelo que estima el potencial de fuga. Un modelo impreciso podría llevar a cierres prematuros o tardíos, afectando negativamente la rentabilidad del barco.

### 💡 Codigo_Cristalizado

## 💡 Codigo_Cristalizado
### 🎯 Contexto y Trigger
Este bloque contiene la configuración final del código de trading automatizado, optimizado para minimizar riesgos y maximizar ganancias. Se activa al iniciar el proceso de ejecución.
### ⚙️ Lógica Operativa
- Cada "General" (módulo) tiene una función específica e intransferible: Iron (acumulación), Beru (corte de pérdidas), Igris/Tusk (ejecución estratégica).
- La versión v2.0.0ti ("Las Cuatro Extremidades del Cónclave") está libre de errores y advertencias del linter.
### ⚠️ Restricciones / Notas Tácticas
La efectividad depende de la precisión de los datos de mercado en tiempo real y la configuración precisa de los parámetros de cada "General". Cualquier desviación significativa puede afectar el rendimiento esperado.