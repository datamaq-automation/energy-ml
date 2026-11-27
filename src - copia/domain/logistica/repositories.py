"""src/domain/logistica/repositories.py — Puertos: de dónde salen los pedidos y quién modela.

El dominio no conoce pandas: la tabla de pedidos es un tipo opaco
que solo el adaptador concreto sabe manejar.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from src.domain.logistica.value_objects import (
    ClusterMetric,
    ClusterProfile,
    SegmentRecall,
    SupervisedModelMetrics,
)

DatosCo = TypeVar("DatosCo", covariant=True)
DatosContra = TypeVar("DatosContra", contravariant=True)


class RepositorioPedidos(Protocol[DatosCo]):
    """Fuente de pedidos ya limpios de columnas con fuga de datos."""

    def cargar(self) -> DatosCo:
        """Devuelve la tabla de pedidos con la fecha del pedido desglosada."""
        ...


class ModeladorRetrasos(Protocol[DatosContra]):
    """Motor de aprendizaje automático para las Tareas A, B y C."""

    def contar_filas(self, datos: DatosContra) -> int:
        """Cantidad de pedidos cargados."""
        ...

    def agrupar(
        self, datos: DatosContra, best_k: int
    ) -> tuple[list[ClusterMetric], list[ClusterProfile]]:
        """Tarea A: K-means para varios k y perfil de negocio de los grupos de `best_k`."""
        ...

    def clasificar(
        self, datos: DatosContra, max_depth: int, segmento: str
    ) -> tuple[list[SupervisedModelMetrics], list[tuple[str, float]], list[SegmentRecall]]:
        """Tareas B y C: métricas por modelo, importancias del árbol y recall por segmento."""
        ...

    def graficar_codo(self, metricas: list[ClusterMetric], best_k: int, destino: str) -> str:
        """Guarda el gráfico de codo y silueta; devuelve la ruta."""
        ...

    def graficar_matriz(self, modelo: SupervisedModelMetrics, destino: str) -> str:
        """Guarda la matriz de confusión del modelo; devuelve la ruta."""
        ...
