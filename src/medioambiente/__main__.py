"""src/medioambiente/__main__.py — Ejecuta las Tareas A, B y C en orden (python -m src.medioambiente)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from src.infrastructure.settings.logger import logger
from src.medioambiente.data import (
    CSV_FILENAME,
    DEFAULT_DATA_DIR,
    download_dataset,
    load_air_quality,
)
from src.medioambiente.preprocess import construir_etiqueta, construir_features
from src.medioambiente.split import split_aleatorio
from src.medioambiente.supervised import matriz_confusion, predecir_particion, separar_xy
from src.medioambiente.temporal import (
    comparar_splits,
    detectar_cambio_distribucion,
    split_temporal,
)
from src.medioambiente.unsupervised import (
    agrupar_meteo,
    calcular_diagnosticos_k,
    graficar_diagnosticos,
    mejor_k,
    proporcion_episodios,
    resumen_grupos,
)

DESTINO_IMAGENES = Path("docs/medioambiente/imagenes")
SEPARADOR = "=" * 72


def ejecutar_tareas(destino_imagenes: Path = DESTINO_IMAGENES) -> dict[str, Any]:
    """Corre la Tarea A, luego la B y por último la C; devuelve los resultados clave."""
    if not (DEFAULT_DATA_DIR / CSV_FILENAME).exists():
        download_dataset()
    crudo = load_air_quality()

    logger.info(SEPARADOR)
    logger.info("TAREA A — K-means sobre meteorología (sin etiqueta)")
    diagnosticos = calcular_diagnosticos_k(crudo)
    logger.info("%s", diagnosticos.round(3).to_string(index=False))
    k_elegido = mejor_k(diagnosticos)
    logger.info("Mejor k por silueta: %d", k_elegido)
    graficar_diagnosticos(diagnosticos, destino_imagenes)
    agrupado = construir_etiqueta(agrupar_meteo(crudo, k=k_elegido))
    logger.info("Grupos (medias):\n%s", resumen_grupos(agrupado).to_string())
    logger.info("Episodios por grupo:\n%s", proporcion_episodios(agrupado).to_string())

    datos = construir_etiqueta(construir_features(crudo))

    logger.info(SEPARADOR)
    logger.info("TAREA B — Modelos con split aleatorio estratificado")
    train_aleatorio, test_aleatorio = split_aleatorio(datos)
    tabla_aleatorio, _ = predecir_particion(train_aleatorio, test_aleatorio)
    logger.info("Métricas (aleatorio):\n%s", tabla_aleatorio.round(3).to_string(index=False))

    logger.info(SEPARADOR)
    logger.info("TAREA C — Split temporal (80 % más antiguo → 20 % más reciente)")
    train_temporal, test_temporal = split_temporal(datos)
    tabla_temporal, predicciones = predecir_particion(train_temporal, test_temporal)
    tabla_comparada = comparar_splits(tabla_aleatorio, tabla_temporal)
    logger.info("Tabla comparativa:\n%s", tabla_comparada.round(3).to_string(index=False))

    _, y_test = separar_xy(test_temporal)
    mejor_modelo = str(tabla_temporal.loc[tabla_temporal["f1"].idxmax(), "modelo"])
    confusion = matriz_confusion(y_test, predicciones[mejor_modelo])
    logger.info(
        "Matriz de confusión de %s sobre test temporal [[TN, FP], [FN, TP]]:\n%s",
        mejor_modelo,
        np.array2string(confusion, separator=", "),
    )
    cambio = detectar_cambio_distribucion(train_temporal, test_temporal)
    logger.info("Detección de cambio de distribución:\n%s", cambio.round(3).to_string(index=False))

    logger.info(SEPARADOR)
    logger.info("Tareas A, B y C completadas. Gráficos en %s", destino_imagenes)
    return {
        "mejor_k": k_elegido,
        "diagnosticos": diagnosticos,
        "tabla_comparada": tabla_comparada,
        "mejor_modelo": mejor_modelo,
        "matriz_confusion": confusion,
        "cambio_distribucion": cambio,
    }


def main() -> None:
    """Punto de entrada de `python -m src.medioambiente`."""
    ejecutar_tareas()


if __name__ == "__main__":
    main()
