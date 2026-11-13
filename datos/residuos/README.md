# Pronóstico mensual de residuos sólidos

Caso de estudio complementario para predecir los totales mensuales de residuos de toda la ciudad de Ann Arbor. Es independiente del flujo principal de identificación NILM de este repositorio.

## Datos

- Fuente: [Monthly Solid Waste Totals](https://data.a2gov.org/city-of-ann-arbor/monthly-solid-waste-totals).
- Licencia informada por el portal: [Creative Commons CC0](https://creativecommons.org/publicdomain/zero/1.0/).
- CSV original: `solid_waste.csv`.
- Diccionario de datos publicado por la ciudad: `solid-waste-metadata-documentation.pdf`.
- Objetivo: suma mensual de `NetTN_Month` para las categorías de `MaterialCategory`.
- Se conservan las unidades informadas por la fuente; no se convierten a toneladas métricas.
- No se usan porcentajes, totales trimestrales/anuales ni valores per cápita como predictores, porque se calculan con datos del período objetivo y podrían filtrar información futura.

La descarga analizada tiene 333 filas: tres categorías para cada uno de 111 meses consecutivos, desde julio de 2017 hasta septiembre de 2026. El portal reportaba 297 registros en sus metadatos cuando se descargó el archivo; por eso el análisis valida el CSV y no depende de ese contador.

## Ejecución

Desde la raíz del repositorio:

```bash
python -m pip install -r datos/residuos/requirements.txt
python datos/residuos/analisis_residuos.py
```

El programa valida las columnas necesarias, registros duplicados, categorías mensuales y continuidad de la serie. Escribe en `datos/residuos/resultados/`:

- `serie_mensual_ciudad.csv`: una fila por mes con la suma de las categorías.
- `metricas_validacion.csv`: MAE y RMSE para persistencia, regresión lineal y bosque aleatorio.
- `pronostico_3_meses.csv`: pronósticos para cada modelo y mes.

## Modelos y evaluación

Se comparan:

1. **Persistencia:** predice que cada uno de los próximos meses será igual al último mes observado.
2. **Regresión lineal.**
3. **Bosque aleatorio.**

Los modelos supervisados usan el último valor mensual, el valor de hace 12 meses, el promedio de los tres meses previos, el índice temporal y variables estacionales del mes. Para pronósticos de varios meses, las predicciones anteriores se incorporan recursivamente como entradas.

La evaluación temporal reserva los últimos 12 meses observados y los pronostica en cuatro bloques de tres meses. Cada bloque se predice usando solo la historia anterior. Las métricas se reportan globalmente y por horizonte de uno, dos y tres meses. Con 111 observaciones y 12 predicciones de validación, los resultados son preliminares y no garantizan desempeño futuro.

El último período disponible es septiembre de 2026, por lo que la salida actual cubre octubre–diciembre de 2026. Son los tres meses posteriores al último dato, no necesariamente los tres meses futuros desde la fecha de ejecución.
