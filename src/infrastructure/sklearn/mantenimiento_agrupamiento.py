"""src/infrastructure/sklearn/mantenimiento_agrupamiento.py — K-means no supervisado sobre la telemetría de mantenimiento."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.domain.mantenimiento.models import (
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    validate_no_data_leakage,
)
from src.infrastructure.sklearn.mantenimiento_datos import RANDOM_STATE

K_RANGE: tuple[int, ...] = (2, 3, 4, 5, 6)
N_INIT: int = 10


@dataclass(frozen=True)
class KMetrics:
    """Inercia (para el codo) y silueta de un valor de k."""

    k: int
    inertia: float
    silhouette: float


def scale_telemetry(data: pd.DataFrame) -> np.ndarray:
    """Escala solo las variables numéricas de telemetría; la etiqueta nunca entra."""
    validate_no_data_leakage(NUMERIC_FEATURES)
    return StandardScaler().fit_transform(data[list(NUMERIC_FEATURES)])


def fit_kmeans(scaled: np.ndarray, k: int) -> KMeans:
    """Ajusta K-means con semilla fija."""
    return KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE).fit(scaled)


def compute_k_metrics(scaled: np.ndarray, k_values: Sequence[int] = K_RANGE) -> list[KMetrics]:
    """Calcula inercia y silueta para cada k, para elegir con codo y silueta."""
    metrics: list[KMetrics] = []
    for k in k_values:
        model = fit_kmeans(scaled, k)
        silhouette = float(silhouette_score(scaled, model.labels_))
        metrics.append(KMetrics(k, float(model.inertia_), silhouette))
    return metrics


def best_k_by_silhouette(metrics: Sequence[KMetrics]) -> int:
    """Devuelve el k con mayor silueta."""
    return max(metrics, key=lambda item: item.silhouette).k


def profile_clusters(data: pd.DataFrame, scaled: np.ndarray, k: int) -> pd.DataFrame:
    """Promedio de telemetría, tamaño y proporción de fallas por grupo (solo para interpretar)."""
    labels = fit_kmeans(scaled, k).labels_
    profile = data[list(NUMERIC_FEATURES)].groupby(labels).mean()
    profile["size"] = data.groupby(labels).size()
    profile["failure_rate"] = data[TARGET_COLUMN].groupby(labels).mean()
    return profile
