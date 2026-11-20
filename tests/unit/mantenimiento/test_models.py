"""tests/unit/mantenimiento/test_models.py — Pruebas de la regla anti-fuga de mantenimiento."""

import pytest

from src.domain.mantenimiento.models import (
    CATEGORICAL_FEATURES,
    FORBIDDEN_COLUMNS,
    NUMERIC_FEATURES,
    validate_no_data_leakage,
)


def test_allowed_features_pass() -> None:
    validate_no_data_leakage([*NUMERIC_FEATURES, *CATEGORICAL_FEATURES])


@pytest.mark.parametrize("column", FORBIDDEN_COLUMNS)
def test_forbidden_column_is_rejected(column: str) -> None:
    with pytest.raises(ValueError):
        validate_no_data_leakage(["Torque [Nm]", column])
