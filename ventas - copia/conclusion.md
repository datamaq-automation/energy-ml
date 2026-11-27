# Conclusión — Pronóstico de ventas diarias por tienda y producto (Issue #2)

## La pregunta del negocio

¿Podemos estimar las ventas de cada producto en cada tienda con un día de anticipación, y hacerlo mejor que una regla simple?

## Los datos

Ventas diarias de 10 tiendas y 50 productos, del 1/1/2013 al 31/12/2017 (913.000 registros, sin días faltantes). La computadora aprendió con 2013–2016 y la evaluamos con 2017, sin mezclar fechas y usando solo datos de días anteriores (sin hacer trampa).

## ¿Sirvió usar machine learning?

**Sí.** Hacer un pronosticador de ventas permite **ajustar la inversión** en mercadería: menos stock que sobra y menos ventas perdidas.

| Método | Se equivoca en promedio (MAE) | RMSE |
| :--------------- | ---------------------------: | ---: |
| Igual que ayer (regla simple) |                 11,2 unidades | 15,4 |
| Regresión lineal |                  8,0 unidades | 10,4 |
| Bosque aleatorio |              **7,4 unidades** |  **9,6** |

El bosque aleatorio es el que menos se equivoca: unas **7 unidades por día**, contra **11** de la regla "igual que ayer". La regresión lineal queda cerca y es más simple.

## ¿Qué productos son predecibles y cuáles no?

Agrupamos las 500 combinaciones de tienda + producto en 3 grupos según cuánto venden:

| Grupo | Vende por día | Error del bosque | En proporción |
| :------------ | ----: | ---: | ------: |
| Ventas altas  |    97 |  9,9 | **10%** |
| Ventas medias |    62 |  7,8 | **12%** |
| Ventas bajas  |    32 |  5,5 | **17%** |

- **Los más fáciles** de pronosticar son los de **ventas altas**.
- **Los más difíciles** son los de **ventas bajas**, porque hay más error en proporción. Cuando se vende poco, cada cliente pesa mucho y manda más el azar que los patrones (día de la semana, mes).

En todos los grupos las ventas suben de lunes a domingo, así que el mismo método sirve para los tres (como la misma receta en ollas de distinto tamaño).

## Limitación principal

Puede haber días con **picos de venta**, para arriba o para abajo, que el machine learning **no pronostica**. El pronóstico acierta el nivel de un día normal, pero no las sorpresas. Además, los datos no dicen cuándo hubo **feriados, promociones o mal clima**, así que esos días el error puede ser mayor.

## Recomendación

Usar el bosque aleatorio para planificar las compras de un día normal, y dejar un margen de stock extra en los productos de ventas bajas, que son los más difíciles de adivinar.
