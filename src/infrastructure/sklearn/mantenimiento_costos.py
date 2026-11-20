"""src/infrastructure/sklearn/mantenimiento_costos.py — Costo de errores y umbral óptimo por modelo para mantenimiento."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.domain.mantenimiento.costos import DEFAULT_COSTS, ErrorCosts, total_cost
from src.infrastructure.sklearn.mantenimiento_modelos import (
    build_forest,
    build_logistic,
)

DEFAULT_THRESHOLD: float = 0.5
THRESHOLD_GRID: tuple[float, ...] = tuple(float(t) for t in np.arange(1, 100) / 100)


@dataclass(frozen=True)
class CostResult:
    """Costo con el umbral 0,5 y con el umbral que minimiza el costo total."""

    cost_at_default: float
    best_threshold: float | None
    best_cost: float
    false_negatives: int
    false_positives: int


def count_errors(
    y_true: np.ndarray, probabilities: np.ndarray, threshold: float
) -> tuple[int, int]:
    """Cuenta falsos negativos y falsos positivos al predecir 'falla' si prob >= umbral."""
    predicted = probabilities >= threshold
    actual = y_true == 1
    return int(np.sum(actual & ~predicted)), int(np.sum(~actual & predicted))


def find_best_threshold(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    costs: ErrorCosts,
    thresholds: Sequence[float] = THRESHOLD_GRID,
) -> tuple[float, float, int, int]:
    """Devuelve (umbral, costo, FN, FP) del umbral de menor costo; en empate, el más bajo."""
    candidates = []
    for threshold in thresholds:
        fn, fp = count_errors(y_true, probabilities, threshold)
        candidates.append((threshold, total_cost(fn, fp, costs), fn, fp))
    if not candidates:
        raise ValueError("Se necesita al menos un umbral")
    return min(candidates, key=lambda item: item[1])


def analyze_costs(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    costs: ErrorCosts = DEFAULT_COSTS,
) -> dict[str, CostResult]:
    """Costo total de la línea base y de cada modelo, con umbral 0,5 y con el óptimo."""
    y_true = y_test.to_numpy()
    failures = int(np.sum(y_true == 1))
    baseline_cost = total_cost(failures, 0, costs)
    results = {"baseline": CostResult(baseline_cost, None, baseline_cost, failures, 0)}
    for name, model in {"logistic": build_logistic(), "forest": build_forest()}.items():
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_test)[:, 1]
        fn0, fp0 = count_errors(y_true, probabilities, DEFAULT_THRESHOLD)
        threshold, cost, fn, fp = find_best_threshold(y_true, probabilities, costs)
        results[name] = CostResult(total_cost(fn0, fp0, costs), threshold, cost, fn, fp)
    return results
