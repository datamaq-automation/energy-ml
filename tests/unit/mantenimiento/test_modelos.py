"""tests/unit/mantenimiento/test_modelos.py — Pruebas de la línea base y los modelos de mantenimiento."""

import numpy as np
import pandas as pd
import pytest

from src.infrastructure.sklearn.mantenimiento_datos import (
    split_features_target,
    split_train_test,
)
from src.infrastructure.sklearn.mantenimiento_modelos import (
    ModelMetrics,
    train_and_evaluate_all,
)


@pytest.fixture
def results() -> dict[str, ModelMetrics]:
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
    return train_and_evaluate_all(x_train, x_test, y_train, y_test)


def test_baseline_never_detects_failures(results: dict[str, ModelMetrics]) -> None:
    assert results["baseline"].recall == 0.0
    assert results["baseline"].accuracy > 0.5


@pytest.mark.parametrize("name", ["logistic", "forest"])
def test_models_beat_baseline_recall(results: dict[str, ModelMetrics], name: str) -> None:
    assert results[name].recall > results["baseline"].recall


def test_confusion_matrix_covers_all_test_rows(
    results: dict[str, ModelMetrics],
) -> None:
    m = results["forest"]
    total = m.true_negatives + m.false_positives + m.false_negatives + m.true_positives
    assert total == 80
