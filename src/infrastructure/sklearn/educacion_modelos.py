"""src/infrastructure/sklearn/educacion_modelos.py — Tarea B: preprocesador y modelos supervisados."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.domain.educacion.modelos import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    SEED,
)


def build_preprocessor() -> ColumnTransformer:
    """Preprocesador: StandardScaler para numéricas y OneHotEncoder para categóricas.

    Ambos viven dentro del Pipeline y solo se ajustan con los datos de train
    (reglas 2 y 3 de la sección 4 del issue).
    """
    numeric_pipe = Pipeline([("scaler", StandardScaler())])
    categorical_pipe = Pipeline(
        [("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, list(NUMERIC_FEATURES)),
            ("cat", categorical_pipe, list(CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
    )


def build_logistic_regression() -> Pipeline:
    """Regresión logística con one-hot para categóricas (Tarea B.4)."""
    return Pipeline(
        steps=[
            ("pre", build_preprocessor()),
            ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
        ]
    )


def build_random_forest() -> Pipeline:
    """Bosque aleatorio con 200 árboles y pesos balanceados (Tarea B.5)."""
    return Pipeline(
        steps=[
            ("pre", build_preprocessor()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    random_state=SEED,
                ),
            ),
        ]
    )


def fit_real_models(
    x_train: pd.DataFrame,
    y_train: pd.Series,
) -> dict[str, Pipeline]:
    """Ajusta los dos modelos reales de la Tarea B (sin la línea base)."""
    builders = (
        ("logistic_regression", build_logistic_regression),
        ("random_forest", build_random_forest),
    )
    models: dict[str, Pipeline] = {}
    for name, builder in builders:
        pipeline = builder()
        pipeline.fit(x_train, y_train)
        models[name] = pipeline
    return models


class SklearnEntrenadorRiesgo:
    """Implementa EntrenadorRiesgo ajustando regresión logística y bosque aleatorio."""

    def entrenar(self, x_train: pd.DataFrame, y_train: pd.Series) -> dict[str, Pipeline]:
        """Devuelve los dos modelos supervisados ya ajustados solo con train."""
        return fit_real_models(x_train, y_train)
