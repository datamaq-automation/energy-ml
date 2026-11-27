"""src/infrastructure/sklearn/medioambiente_split.py — División train/test del caso de episodios de CO."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from src.domain.medioambiente.exceptions import ColumnasFaltantesError
from src.domain.medioambiente.value_objects import COLUMNA_ETIQUETA, SEMILLA
from src.infrastructure.settings.logger import logger


def split_aleatorio(
    df: pd.DataFrame, tamano_test: float = 0.2, semilla: int = SEMILLA
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split aleatorio estratificado por `episodio` (80/20 por defecto, semilla 42).

    Se aplica ANTES de imputar o escalar: crear_transformador() se ajusta
    solo con el train que devuelve esta función.
    """
    if COLUMNA_ETIQUETA not in df.columns:
        raise ColumnasFaltantesError(
            "Falta la columna 'episodio': aplicá construir_etiqueta() primero.", [COLUMNA_ETIQUETA]
        )
    train, test = train_test_split(
        df,
        test_size=tamano_test,
        random_state=semilla,
        stratify=df[COLUMNA_ETIQUETA],
    )
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    logger.info(
        "Split aleatorio estratificado: train=%d filas (%.0f%%), test=%d filas, semilla=%d",
        len(train),
        100 * (1 - tamano_test),
        len(test),
        semilla,
    )
    return train, test
