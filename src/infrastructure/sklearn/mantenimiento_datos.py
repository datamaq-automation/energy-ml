"""src/infrastructure/sklearn/mantenimiento_datos.py — Carga del CSV AI4I 2020 y split estratificado para mantenimiento."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.domain.mantenimiento.models import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    validate_no_data_leakage,
)

DEFAULT_CSV_PATH: Path = Path("datos/mantenimiento/ai4i2020.csv")
RANDOM_STATE: int = 42
TEST_SIZE: float = 0.2
FEATURE_COLUMNS: tuple[str, ...] = (*CATEGORICAL_FEATURES, *NUMERIC_FEATURES)


def load_dataset(csv_path: Path = DEFAULT_CSV_PATH) -> pd.DataFrame:
    """Lee el CSV crudo de AI4I 2020."""
    return pd.read_csv(csv_path)


def split_features_target(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Separa X (solo columnas permitidas) e y (etiqueta), validando que no haya fuga."""
    validate_no_data_leakage(FEATURE_COLUMNS)
    return data[list(FEATURE_COLUMNS)].copy(), data[TARGET_COLUMN].copy()


def split_train_test(
    features: pd.DataFrame, target: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split 80/20 estratificado por la etiqueta, con semilla fija, antes de transformar nada."""
    return train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        stratify=target,
        random_state=RANDOM_STATE,
    )
