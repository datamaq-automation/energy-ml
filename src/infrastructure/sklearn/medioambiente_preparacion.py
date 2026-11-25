"""src/infrastructure/sklearn/medioambiente_preparacion.py — Etiquetado, features anticipables y transformación."""

from __future__ import annotations

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.domain.medioambiente.exceptions import ColumnasFaltantesError
from src.domain.medioambiente.value_objects import (
    COLUMNA_CO,
    COLUMNA_ETIQUETA,
    COLUMNAS_FEATURES,
    COLUMNAS_METEO,
    UMBRAL_EPISODIO_MG_M3,
)
from src.infrastructure.settings.logger import logger


def construir_etiqueta(df: pd.DataFrame, umbral: float = UMBRAL_EPISODIO_MG_M3) -> pd.DataFrame:
    """Descarta filas sin CO(GT) y agrega la columna `episodio` (1 si CO >= umbral).

    Las filas descartadas son las que no permiten calcular la etiqueta
    (CO(GT) faltante, es decir -200 convertido a NaN).
    """
    filas_antes = len(df)
    con_co = df.dropna(subset=[COLUMNA_CO]).copy()
    con_co[COLUMNA_ETIQUETA] = (con_co[COLUMNA_CO] >= umbral).astype("int8")
    logger.info(
        "Etiqueta `episodio` construida: %d/%d filas utilizadas "
        "(%d descartadas por CO(GT) faltante), umbral >= %.1f mg/m³",
        len(con_co),
        filas_antes,
        filas_antes - len(con_co),
        umbral,
    )
    return con_co


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega las features anticipables: meteo en t-1/t-2 y calendario de la hora a predecir.

    - Los lags se calculan sobre una rejilla horaria completa (por reloj, no por
      posición): si la hora t-1 no fue observada, el lag queda en NaN.
    - No usa CO(GT) ni sensores de la misma hora.
    - Orden de uso: load_air_quality → construir_features → construir_etiqueta
      (los lags necesitan todas las horas observadas, aunque falte CO).
    """
    requeridas = ("Date", "Time", *COLUMNAS_METEO)
    ausentes = [c for c in requeridas if c not in df.columns]
    if ausentes:
        raise ColumnasFaltantesError(
            f"Faltan columnas para construir features: {ausentes}", ausentes
        )
    marca = df["Date"].astype(str).str.strip() + " " + df["Time"].astype(str).str.strip()
    salida = df.copy()
    salida["fecha"] = pd.to_datetime(marca, format="%d/%m/%Y %H.%M.%S")
    salida = salida.sort_values("fecha", kind="stable").drop_duplicates("fecha", keep="first")
    if salida.empty:
        for columna in COLUMNAS_FEATURES:
            salida[columna] = pd.Series(dtype="float64")
        return salida
    meteo = salida.set_index("fecha")[list(COLUMNAS_METEO)]
    rejilla = meteo.reindex(pd.date_range(meteo.index.min(), meteo.index.max(), freq="h"))
    lags = pd.DataFrame(index=rejilla.index)
    for columna in COLUMNAS_METEO:
        lags[f"{columna}_t1"] = rejilla[columna].shift(1)
        lags[f"{columna}_t2"] = rejilla[columna].shift(2)
    lags["hora"] = lags.index.hour
    lags["dia_semana"] = lags.index.dayofweek
    lags["mes"] = lags.index.month
    salida = salida.set_index("fecha")
    for columna in lags.columns:
        salida[columna] = lags[columna]
    return salida.reset_index()


def crear_transformador() -> Pipeline:
    """Imputación por mediana + StandardScaler.

    Ajustarlo (fit) SOLO sobre train: el test no puede influir en la
    imputación ni en la escala (regla: split antes de transformar).
    """
    return Pipeline(
        steps=[
            ("imputar", SimpleImputer(strategy="median")),
            ("escalar", StandardScaler()),
        ]
    )
