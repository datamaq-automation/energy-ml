"""tests/unit/mantenimiento/test_datos.py — Pruebas de carga y split estratificado de mantenimiento."""

import numpy as np
import pandas as pd
import pytest

from src.domain.mantenimiento.models import FORBIDDEN_COLUMNS
from src.infrastructure.sklearn.mantenimiento_datos import (
    split_features_target,
    split_train_test,
)


@pytest.fixture
def machines() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame(
        {
            "UDI": range(n),
            "Product ID": [f"P{i}" for i in range(n)],
            "Type": ["L", "M", "H", "L"] * 50,
            "Air temperature [K]": rng.normal(300, 2, n),
            "Process temperature [K]": rng.normal(310, 2, n),
            "Rotational speed [rpm]": rng.normal(1500, 100, n),
            "Torque [Nm]": rng.normal(40, 5, n),
            "Tool wear [min]": rng.integers(0, 250, n),
            "Machine failure": [1 if i % 10 == 0 else 0 for i in range(n)],
            "TWF": 0,
            "HDF": 0,
            "PWF": 0,
            "OSF": 0,
            "RNF": 0,
        }
    )


def test_features_exclude_forbidden_columns(machines: pd.DataFrame) -> None:
    features, _ = split_features_target(machines)
    assert not set(features.columns) & set(FORBIDDEN_COLUMNS)


def test_split_is_80_20(machines: pd.DataFrame) -> None:
    x_train, x_test, _, _ = split_train_test(*split_features_target(machines))
    assert len(x_train) == 160
    assert len(x_test) == 40


def test_split_is_stratified(machines: pd.DataFrame) -> None:
    _, _, y_train, y_test = split_train_test(*split_features_target(machines))
    assert y_train.mean() == pytest.approx(0.1)
    assert y_test.mean() == pytest.approx(0.1)


def test_split_is_reproducible(machines: pd.DataFrame) -> None:
    first = split_train_test(*split_features_target(machines))
    second = split_train_test(*split_features_target(machines))
    assert first[0].index.equals(second[0].index)
