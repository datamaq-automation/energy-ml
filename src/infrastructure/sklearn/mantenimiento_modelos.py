"""src/infrastructure/sklearn/mantenimiento_modelos.py — Línea base, regresión logística y bosque aleatorio para fallas de máquinas."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.domain.mantenimiento.models import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from src.infrastructure.sklearn.mantenimiento_datos import RANDOM_STATE


@dataclass(frozen=True)
class ModelMetrics:
    """Métricas sobre la clase 'falla' (1) y la matriz de confusión."""

    accuracy: float
    precision: float
    recall: float
    f1: float
    true_negatives: int
    false_positives: int
    false_negatives: int
    true_positives: int


def build_preprocessor() -> ColumnTransformer:
    """Escala las variables numéricas y codifica 'Type'. Se ajusta solo con train."""
    return ColumnTransformer(
        [
            ("num", StandardScaler(), list(NUMERIC_FEATURES)),
            ("cat", OneHotEncoder(handle_unknown="ignore"), list(CATEGORICAL_FEATURES)),
        ]
    )


def build_baseline() -> Pipeline:
    """Línea base: predice siempre 'sin falla'."""
    dummy = DummyClassifier(strategy="constant", constant=0)
    return Pipeline([("prep", build_preprocessor()), ("model", dummy)])


def build_logistic() -> Pipeline:
    """Modelo simple: regresión logística con clases balanceadas."""
    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE)
    return Pipeline([("prep", build_preprocessor()), ("model", model)])


def build_forest() -> Pipeline:
    """Modelo comparativo: bosque aleatorio con clases balanceadas."""
    model = RandomForestClassifier(
        n_estimators=200, class_weight="balanced", random_state=RANDOM_STATE
    )
    return Pipeline([("prep", build_preprocessor()), ("model", model)])


def evaluate_model(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> ModelMetrics:
    """Calcula precisión, recall, F1 y matriz de confusión sobre la clase 'falla'."""
    predicted = model.predict(x_test)
    tn, fp, fn, tp = confusion_matrix(y_test, predicted, labels=[0, 1]).ravel()
    return ModelMetrics(
        accuracy=float(accuracy_score(y_test, predicted)),
        precision=float(precision_score(y_test, predicted, zero_division=0)),
        recall=float(recall_score(y_test, predicted, zero_division=0)),
        f1=float(f1_score(y_test, predicted, zero_division=0)),
        true_negatives=int(tn),
        false_positives=int(fp),
        false_negatives=int(fn),
        true_positives=int(tp),
    )


def train_and_evaluate_all(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict[str, ModelMetrics]:
    """Entrena con train y evalúa con test la línea base y los dos modelos."""
    models = {
        "baseline": build_baseline(),
        "logistic": build_logistic(),
        "forest": build_forest(),
    }
    return {
        name: evaluate_model(model.fit(x_train, y_train), x_test, y_test)
        for name, model in models.items()
    }
