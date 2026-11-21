"""src/application/educacion/preparacion.py — Variables permitidas, etiqueta y split del Issue #5."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from src.domain.educacion.modelos import (
    CLUSTER_FEATURES,
    MODEL_FEATURES,
    SEED,
    TEST_SIZE,
)
from src.domain.educacion.reglas import etiqueta_desaprobado


def select_cluster_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extrae solo las variables permitidas para el agrupamiento (sin G2 ni G3)."""
    missing = [column for column in CLUSTER_FEATURES if column not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    return df.loc[:, list(CLUSTER_FEATURES)].copy()


def select_model_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extrae las variables permitidas para la Tarea B, sin G2 ni G3 (cero fuga)."""
    missing = [column for column in MODEL_FEATURES if column not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    return df.loc[:, list(MODEL_FEATURES)].copy()


def build_target(df: pd.DataFrame) -> pd.Series:
    """Construye la etiqueta 'desaprobado = G3 < 10', usando solo G3."""
    if "G3" not in df.columns:
        raise ValueError("G3 es obligatoria para construir la etiqueta.")
    return etiqueta_desaprobado(df["G3"]).rename("desaprobado")


def split_train_test(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split 80/20 estratificado con semilla 42, ANTES de cualquier transform.

    Ningún escalador ni codificador se ajusta aquí: viven dentro del Pipeline
    y solo ven los datos de train (reglas 2 y 3 de la sección 4).
    """
    features = select_model_features(df)
    target = build_target(df)
    return train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        stratify=target,
        random_state=SEED,
    )
