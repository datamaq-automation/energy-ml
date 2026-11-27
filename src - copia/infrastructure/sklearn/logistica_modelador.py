"""src/infrastructure/sklearn/logistica_modelador.py — Implementa ModeladorRetrasos con pandas + sklearn."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.logistica.value_objects import (
    ClusterMetric,
    ClusterProfile,
    SegmentRecall,
    SupervisedModelMetrics,
)
from src.infrastructure.sklearn.logistics_pipeline import (
    run_task_a_clustering,
    run_task_b_supervised,
    run_task_c_error_analysis,
    save_confusion_matrix_plot,
    save_elbow_and_silhouette_plot,
    split_and_preprocess,
)


class ModeladorRetrasosSklearn:
    """Motor de las Tareas A, B y C sobre la tabla de pedidos."""

    def contar_filas(self, datos: pd.DataFrame) -> int:
        """Cantidad de pedidos cargados."""
        return len(datos)

    def agrupar(
        self, datos: pd.DataFrame, best_k: int
    ) -> tuple[list[ClusterMetric], list[ClusterProfile]]:
        """K-means para k en 2..8 y perfiles de los grupos de `best_k`."""
        return run_task_a_clustering(datos, best_k=best_k)

    def clasificar(
        self, datos: pd.DataFrame, max_depth: int, segmento: str
    ) -> tuple[list[SupervisedModelMetrics], list[tuple[str, float]], list[SegmentRecall]]:
        """Split 80/20 antes de transformar, cuatro modelos y recall del árbol por segmento."""
        x_train, x_test, y_train, y_test, nombres, x_test_df = split_and_preprocess(datos)
        modelos, importancias, predicciones_arbol = run_task_b_supervised(
            x_train, x_test, y_train, y_test, nombres, tree_max_depth=max_depth
        )
        segmentos = run_task_c_error_analysis(
            x_test_df, y_test, predicciones_arbol, segment_col=segmento
        )
        return modelos, importancias, segmentos

    def graficar_codo(self, metricas: list[ClusterMetric], best_k: int, destino: str) -> str:
        """Gráfico de codo y silueta en `destino`."""
        ruta = Path(destino) / "logistica_elbow_silhouette.png"
        save_elbow_and_silhouette_plot(metricas, best_k=best_k, output_path=ruta)
        return str(ruta)

    def graficar_matriz(self, modelo: SupervisedModelMetrics, destino: str) -> str:
        """Matriz de confusión del modelo en `destino`."""
        ruta = Path(destino) / "logistica_confusion_matrix.png"
        save_confusion_matrix_plot(modelo, output_path=ruta)
        return str(ruta)
