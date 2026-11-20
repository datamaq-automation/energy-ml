# Conclusión: predicción de fallas de máquinas (issue #4)

**Datos:** AI4I 2020 Predictive Maintenance, UCI Machine Learning Repository (licencia CC BY 4.0). Es un dataset **sintético**: sirve para practicar la metodología, no para decidir sobre una planta real. 10.000 registros, 3,4 % de fallas.

## Qué se hizo
- Se excluyeron como entrada los modos de falla (TWF, HDF, PWF, OSF, RNF), la etiqueta y los identificadores (UDI, Product ID), porque solo se conocen cuando la falla ya ocurrió (fuga de datos).
- Split 80/20 estratificado con `random_state=42`, antes de escalar o codificar.
- **Tarea B:** línea base ("nunca falla"), regresión logística y bosque aleatorio (200 árboles), ambos con clases balanceadas.
- **Tarea C:** costo hipotético: falla no detectada = 100, revisión innecesaria = 10.
- **Tarea A:** K-means sobre la telemetría, sin usar la etiqueta.

## Resultados sobre test (2000 máquinas, 68 fallas reales)

| Modelo | Accuracy | Precisión | Recall | F1 |
|---|---|---|---|---|
| Línea base | 0,966 | 0,000 | 0,000 | 0,000 |
| Regresión logística | 0,824 | 0,142 | 0,824 | 0,242 |
| Bosque aleatorio | 0,980 | 0,721 | 0,647 | 0,682 |

Con umbral 0,5. La línea base tiene 96,6 % de accuracy y no detecta ninguna falla: la accuracy sola no sirve con clases tan desbalanceadas.

| Modelo | Costo con umbral 0,5 | Umbral óptimo | Costo óptimo | Fallas no detectadas | Falsas alarmas |
|---|---|---|---|---|---|
| Línea base | 6800 | n/a | 6800 | 68 | 0 |
| Regresión logística | 4590 | 0,69 | 3220 | 17 | 152 |
| Bosque aleatorio | 2580 | 0,24 | 1650 | 9 | 75 |

## Alerta recomendada
Usar el **bosque aleatorio** y activar la alerta cuando la probabilidad de falla supere **24 %**. Con ese umbral detecta 59 de 68 fallas (recall 0,87), con 75 revisiones innecesarias. El costo esperado baja de 6800 a 1650 (un 76 % menos). El umbral no es 0,5 porque perder una falla cuesta diez veces más que una revisión de más.

## Tarea A: grupos de máquinas
Con k=3 (codo suave y silueta máxima, 0,26) aparecen tres grupos: máquinas con ambiente más caliente (5 % de fallas), con ambiente más fresco (2 %) y de alta velocidad con bajo torque (2 %). La silueta es baja: la estructura de grupos es débil. El grupo caliente merece vigilancia, pero la alerta operativa la da el modelo supervisado.

## Limitaciones
- Los costos (100 y 10) son un supuesto inventado; con otros costos cambia el umbral.
- El umbral se eligió con los mismos datos de test con que se mide el costo, así que 1650 es optimista. Lo correcto sería elegirlo con validación aparte.
- Hay solo 68 fallas en test: las métricas varían bastante con otro split.
- El dataset es sintético y el split es aleatorio, no temporal, porque no hay orden en el tiempo.
- No se estudió qué variables pesan más ni se predijo el modo de falla.

## fuente 
AI4I 2020 Predictive Maintenance Dataset [Dataset]. (2020). UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C.

