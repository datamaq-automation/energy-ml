"""tests/unit/mantenimiento/test_costos.py — Pruebas del costo de errores y del umbral óptimo."""

import numpy as np
import pandas as pd
import pytest

from src.domain.mantenimiento.costos import DEFAULT_COSTS, ErrorCosts, total_cost
from src.infrastructure.sklearn.mantenimiento_costos import (
    CostResult,
    analyze_costs,
    find_best_threshold,
)
from src.infrastructure.sklearn.mantenimiento_datos import (
    split_features_target,
    split_train_test,
)


@pytest.fixture
def analysis() -> tuple[dict[str, CostResult], pd.Series]:
    rng = np.random.default_rng(42)
    n = 400
    torque = rng.normal(40, 5, n)
    data = pd.DataFrame(
        {
            "Type": ["L", "M", "H", "L"] * 100,
            "Air temperature [K]": rng.normal(300, 2, n),
            "Process temperature [K]": rng.normal(310, 2, n),
            "Rotational speed [rpm]": rng.normal(1500, 100, n),
            "Torque [Nm]": torque,
            "Tool wear [min]": rng.integers(0, 250, n),
            "Machine failure": (torque > 45).astype(int),
        }
    )
    x_train, x_test, y_train, y_test = split_train_test(*split_features_target(data))
    return analyze_costs(x_train, x_test, y_train, y_test), y_test


def test_total_cost_uses_both_error_types() -> None:
    assert total_cost(2, 3, DEFAULT_COSTS) == 230.0


def test_negative_costs_are_rejected() -> None:
    with pytest.raises(ValueError):
        ErrorCosts(false_negative=-1.0, false_positive=10.0)


def test_best_threshold_is_not_always_half() -> None:
    y_true = np.array([0, 0, 0, 0, 1, 1])
    probabilities = np.array([0.1, 0.2, 0.3, 0.4, 0.35, 0.9])
    threshold, cost, _, _ = find_best_threshold(
        y_true, probabilities, DEFAULT_COSTS, thresholds=(0.5, 0.35)
    )
    assert threshold == 0.35
    assert cost == 10.0


def test_baseline_cost_is_all_failures_missed(
    analysis: tuple[dict[str, CostResult], pd.Series],
) -> None:
    results, y_test = analysis
    expected = float(y_test.sum()) * DEFAULT_COSTS.false_negative
    assert results["baseline"].best_cost == pytest.approx(expected)


@pytest.mark.parametrize("name", ["logistic", "forest"])
def test_best_threshold_never_costs_more_than_default(
    analysis: tuple[dict[str, CostResult], pd.Series], name: str
) -> None:
    results, _ = analysis
    assert results[name].best_cost <= results[name].cost_at_default
