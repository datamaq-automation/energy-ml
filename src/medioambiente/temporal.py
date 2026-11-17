"""src/medioambiente/temporal.py — Tarea C: split temporal y detección de cambio de distribución."""

from __future__ import annotations

import pandas as pd

from src.infrastructure.settings.logger import logger
from src.medioambiente.preprocess import COLUMNAS_FEATURES

PROPORCION_TRAIN = 0.8
UMBRAL_CAMBIO = 0.5  # desviación estándar de la media de train (tamaño de efecto)


def split_temporal(
    df: pd.DataFrame, proporcion_train: float = PROPORCION_TRAIN
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entrena con el 80 % más antiguo y evalúa con el 20 % más reciente (por `fecha`).

    A diferencia del split aleatorio, el test SIQUE al train en el tiempo:
    es el único split compatible con un aviso real (no hay datos futuros
    disponibles para entrenar).
    """
    if "fecha" not in df.columns:
        raise ValueError("Falta la columna 'fecha': aplicá construir_features() primero.")
    if not 0.0 < proporcion_train < 1.0:
        raise ValueError("proporcion_train debe estar entre 0 y 1 (exclusivo).")
    ordenado = df.sort_values("fecha", kind="stable")
    corte = int(len(ordenado) * proporcion_train)
    train = ordenado.iloc[:corte].reset_index(drop=True)
    test = ordenado.iloc[corte:].reset_index(drop=True)
    logger.info(
        "Split temporal: train=%d filas (%s → %s), test=%d filas (%s → %s)",
        len(train),
        train["fecha"].min().date(),
        train["fecha"].max().date(),
        len(test),
        test["fecha"].min().date(),
        test["fecha"].max().date(),
    )
    return train, test


def comparar_splits(tabla_aleatorio: pd.DataFrame, tabla_temporal: pd.DataFrame) -> pd.DataFrame:
    """Une las tablas de métricas de ambos splits con la columna `split`."""
    return pd.concat(
        [
            tabla_aleatorio.assign(split="aleatorio"),
            tabla_temporal.assign(split="temporal"),
        ],
        ignore_index=True,
    )


def detectar_cambio_distribucion(
    train: pd.DataFrame, test: pd.DataFrame, umbral: float = UMBRAL_CAMBIO
) -> pd.DataFrame:
    """Compara cada feature entre train y test con la desviación estandarizada de la media.

    Es la forma simple de detectar un cambio tipo invierno → verano: si la
    media de una feature en test se desplaza más de `umbral` desvíos estándar
    respecto de train, se marca `cambio = True`.
    """
    filas = []
    for columna in COLUMNAS_FEATURES:
        media_train = train[columna].mean()
        media_test = test[columna].mean()
        desvio_train = train[columna].std()
        desvio = (media_test - media_train) / desvio_train if desvio_train > 0 else 0.0
        filas.append(
            {
                "feature": columna,
                "media_train": media_train,
                "media_test": media_test,
                "desvio_estandarizado": desvio,
                "cambio": bool(abs(desvio) > umbral),
            }
        )
    resultado = pd.DataFrame(filas)
    detectadas = resultado.loc[resultado["cambio"], "feature"].tolist()
    logger.info(
        "Detección de cambio de distribución (umbral=%.1fσ): %s",
        umbral,
        detectadas if detectadas else "ninguna feature cambió",
    )
    return resultado
