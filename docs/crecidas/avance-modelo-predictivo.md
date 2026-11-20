# TIGRE ALERTA
## Informe de avance: modelo predictivo de crecidas

**Estado:** Desarrollo experimental  
**Fecha:** 20 de noviembre de 2026

### 1. Objetivo

Desarrollar un modelo de aprendizaje automático capaz de pronosticar el nivel del río en Tigre para horizontes de 1, 2 y 3 días, utilizando registros históricos de estaciones hidrométricas del Instituto Nacional del Agua (INA).

El objetivo complementario es investigar si los datos disponibles permiten anticipar episodios de crecida y generar información que pueda utilizarse posteriormente en un sistema de alertas tempranas.

### 2. Datos utilizados

Se trabajó con registros históricos de dos estaciones:

| Estación | Serie INA | Tipo de información |
|---|---:|---|
| Tigre | 49 | Nivel del río |
| San Fernando | 52 | Nivel del río |

Los archivos originales fueron procesados mediante un repositorio CSV desarrollado en Python.

El procesamiento contempla:
- Conversión de fechas UTC a horario argentino.
- Agrupación de observaciones por día calendario.
- Cálculo de la mediana diaria.
- Identificación de fechas con registros disponibles.
- Preparación de datos para los horizontes de pronóstico.

Se obtuvieron:
- 7.499 días con observaciones de Tigre.
- 7.333 días con observaciones de San Fernando.
- 7.230 fechas coincidentes entre ambas estaciones.

Se construyeron conjuntos de datos con ocho variables predictoras: niveles de Tigre y San Fernando correspondientes al día de referencia y a los tres días anteriores.

### 3. Construcción del modelo de regresión

Se implementó un modelo de regresión lineal para estimar el nivel futuro del río Tigre.

Se evaluaron tres horizontes:
- 24 horas.
- 48 horas.
- 72 horas.

También se implementó un modelo de persistencia como referencia. Este modelo supone que el nivel futuro será igual al último nivel observado.

La evaluación utiliza una separación cronológica de los datos, evitando mezclar aleatoriamente observaciones históricas y futuras.

### 4. Resultados de regresión

En una primera evaluación temporal, los resultados fueron:

| Horizonte | MAE modelo | MAE persistencia | Mejora frente a persistencia |
|---|---:|---:|---:|
| 24 horas | 0,366 m | 0,494 m | 26,00 % |
| 48 horas | 0,423 m | 0,539 m | 21,58 % |
| 72 horas | 0,431 m | 0,570 m | 24,38 % |

Estos resultados indican que la regresión lineal reduce el error promedio respecto de la persistencia.

Sin embargo, el análisis específico de niveles elevados mostró limitaciones: el modelo tiende a subestimar los valores altos y no demostró capacidad suficiente para anticipar episodios de crecida.

Los resultados deben considerarse preliminares hasta completar la evaluación temporal corregida para todos los modelos.

### 5. Investigación de detección de episodios

A partir de las limitaciones de la regresión, se desarrolló una evaluación adicional para estudiar la detección de episodios.

Se utilizó un umbral experimental de 2 metros para identificar niveles elevados. Este valor se empleó exclusivamente con fines de investigación y no representa un umbral oficial de alerta.

Se identificaron episodios históricos y se evaluó si los modelos podían pronosticar un nivel igual o superior a 2 metros en la fecha de inicio.

La regresión lineal obtuvo los siguientes resultados:

| Horizonte | Episodios evaluados | Anticipados |
|---|---:|---:|
| 24 horas | 84 | 1 |
| 48 horas | 85 | 0 |
| 72 horas | 85 | 0 |

Esto confirmó que obtener un error promedio aceptable no garantiza detectar correctamente los episodios de crecida.

### 6. Desarrollo de un clasificador

Como alternativa, se implementó un clasificador Random Forest con ponderación de clases (`class_weight="balanced"`).

El objetivo es estimar si el nivel futuro alcanzará o superará los 2 metros.

Se evaluaron tres umbrales de probabilidad: 0,30, 0,50 y 0,70.

Los resultados exploratorios fueron:

| Horizonte | Umbral | Precisión | Sensibilidad | F1 | Episodios detectados |
|---|---:|---:|---:|---:|---:|
| 24 h | 0,30 | 31,48 % | 47,66 % | 0,379 | 33 de 84 |
| 24 h | 0,50 | 42,86 % | 19,63 % | 0,269 | 13 de 84 |
| 24 h | 0,70 | 50,00 % | 3,74 % | 0,070 | 2 de 84 |
| 48 h | 0,30 | 12,28 % | 12,96 % | 0,126 | 11 de 85 |
| 48 h | 0,50 | 0 % | 0 % | 0 | 0 de 85 |
| 48 h | 0,70 | 0 % | 0 % | 0 | 0 de 85 |
| 72 h | 0,30 | 7,79 % | 5,50 % | 0,065 | 5 de 85 |
| 72 h | 0,50 | 50 % | 0,92 % | 0,018 | 1 de 85 |
| 72 h | 0,70 | 0 % | 0 % | 0 | 0 de 85 |

Las métricas de precisión, sensibilidad y F1 corresponden a la clasificación diaria. La cantidad de episodios detectados corresponde a una evaluación adicional sobre los inicios de episodios.

En el horizonte de 24 horas, el clasificador logró detectar más episodios que la regresión. Sin embargo, también generó numerosos falsos positivos diarios.

Por lo tanto, estos resultados no permiten considerar al clasificador apto para emitir alertas operativas.

### 7. Conclusiones

El trabajo experimental permitió obtener los siguientes aprendizajes:

1. La información histórica de las estaciones de Tigre y San Fernando permite construir conjuntos de datos para pronósticos diarios.
2. La regresión lineal mejora el error promedio frente a la persistencia en los tres horizontes evaluados.
3. La mejora del error promedio no implica necesariamente una buena detección de crecidas.
4. El clasificador Random Forest mostró resultados prometedores para la detección a 24 horas, aunque con una cantidad elevada de falsos positivos.
5. El rendimiento disminuye considerablemente en los horizontes de 48 y 72 horas.
6. Es necesario continuar investigando la disponibilidad temporal de las observaciones y la capacidad real de anticipación.

### 8. Próximas tareas

Se propone continuar con las siguientes actividades:

- Implementar una separación cronológica de entrenamiento, validación y prueba final.
- Seleccionar los umbrales de probabilidad utilizando exclusivamente el conjunto de validación.
- Evaluar el rendimiento definitivo en datos no utilizados durante el desarrollo.
- Analizar falsos positivos y episodios no detectados.
- Comparar los resultados con la persistencia.
- Incorporar pruebas unitarias y de integración.
- Integrar los casos de uso en la arquitectura existente del repositorio.
- Documentar los umbrales oficiales y sus fuentes.
- Preparar la futura integración con la API de Tigre Alerta.

### 9. Consideraciones

Los 2 metros utilizados en los experimentos constituyen un umbral de análisis y no una alerta oficial.

Para Tigre se documentaron como referencias oficiales 3,30 metros para alerta y 3,80 metros para evacuación. La clasificación definitiva deberá utilizar los umbrales configurados y documentados en el dominio.

El sistema desarrollado se encuentra en etapa experimental. Los resultados no deben utilizarse todavía para tomar decisiones de seguridad o emitir alertas reales.