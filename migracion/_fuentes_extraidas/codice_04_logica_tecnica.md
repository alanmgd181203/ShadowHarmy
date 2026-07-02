# Lógica Técnica

> Criterios de ingeniería extraídos de bloques de código.

## Protocolos

#### #Logica_Tecnica
## 💡 Codigo_Cristalizado
### 🎯 Contexto y Trigger
Este bloque contiene la lógica de ejecución del simulador de mercado criptográfico "Monarca". Se activa al ejecutar el script `simulador_infierno.py`.
### ⚙️ Lógica Operativa
- El código requiere Python instalado con la librería Pandas.
-  Se puede ejecutar en dos modos:
    - **Simulación:** Genera datos de precios ficticios y ejecuta la simulación.
    - **Modo Real:** Utiliza archivos CSV con datos históricos de precios (columna "close"). Los archivos deben llamarse `BTC_history.csv`, `ETH_history.csv`, etc.
### ⚠️ Restricciones / Notas Tácticas
La precisión del simulador en modo real depende de la calidad y exactitud de los datos históricos utilizados. El código asume que los archivos CSV tienen una estructura específica (columna "close"). Errores en la estructura de datos pueden provocar resultados inesperados.

### 💡 Codigo_Cristalizado

## 💡 Codigo_Cristalizado
### 🎯 Contexto y Trigger
Ejecutar este código cuando se sospecha de un fallo catastrófico en el sistema, para determinar si la causa es un activo específico o una acumulación de pérdidas por amputaciones menores (Beru).
### ⚙️ Lógica Operativa
- El código v2.4.0ti ("El Ojo del Oráculo") procesa datos del sistema.
- Genera un reporte en la terminal bajo la sección "DIAGNÓSTICO DEL FALLO".
- Este reporte identifica el origen del fallo: activo específico o acumulación de amputaciones (Beru).
### ⚠️ Restricciones / Notas Tácticas
El código solo identifica la causa del fallo, no ofrece soluciones para repararlo. Se requiere análisis adicional para determinar la estrategia de recuperación.