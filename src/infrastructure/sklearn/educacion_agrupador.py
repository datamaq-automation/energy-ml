"""src/infrastructure/sklearn/educacion_agrupador.py — Tarea A: escalado, métricas de k y K-means."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.domain.educacion.modelos import K_MAX, K_MIN, SEED


def scale_features(features: pd.DataFrame) -> np.ndarray:
    """Estandariza las variables con StandardScaler (media 0, desvío 1)."""
    return StandardScaler().fit_transform(features)


def compute_k_metrics(
    scaled: np.ndarray,
    k_values: range = range(K_MIN, K_MAX + 1),
) -> tuple[list[int], list[float], list[float]]:
    """Ejecuta K-means para cada k y devuelve (ks, inercias, siluetas).

    La inercia alimenta la lectura del codo y la silueta la del score;
    ambos se calculan sobre los mismos datos escalados.
    """
    ks = list(k_values)
    if not ks:
        raise ValueError("k_values no puede estar vacío.")
    inertias: list[float] = []
    silhouettes: list[float] = []
    for k in ks:
        model = KMeans(n_clusters=k, random_state=SEED, n_init=10)
        labels = model.fit_predict(scaled)
        inertias.append(float(model.inertia_))
        silhouettes.append(float(silhouette_score(scaled, labels)))
    return ks, inertias, silhouettes


def fit_kmeans(scaled: np.ndarray, k: int) -> np.ndarray:
    """Ajusta K-means con semilla fija y devuelve una etiqueta de grupo por estudiante."""
    model = KMeans(n_clusters=k, random_state=SEED, n_init=10)
    return model.fit_predict(scaled)


class KMeansAgrupadorEstudiantes:
    """Implementa AgrupadorEstudiantes con StandardScaler + KMeans (semilla 42)."""

    def diagnosticos(self, features: pd.DataFrame) -> tuple[list[int], list[float], list[float]]:
        """Codo y silueta de cada k del rango, sobre las variables escaladas."""
        return compute_k_metrics(scale_features(features))

    def agrupar(self, features: pd.DataFrame, k: int) -> np.ndarray:
        """Asigna un grupo a cada estudiante con el k elegido (silueta máxima)."""
        return fit_kmeans(scale_features(features), k)
