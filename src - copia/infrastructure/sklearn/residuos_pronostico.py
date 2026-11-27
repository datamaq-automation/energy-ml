"""src/infrastructure/sklearn/residuos_pronostico.py — Validación temporal y pronóstico mensual de residuos.

Compara persistencia, regresión lineal y bosque aleatorio con pronósticos
recursivos de 3 meses sobre el total mensual de Ann Arbor.
"""

from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from src.domain.residuos.exceptions import ModeloDesconocidoError, SerieCortaError
from src.domain.residuos.services import origenes_de_validacion, pronostico_persistencia
from src.domain.residuos.value_objects import (
    BOSQUE_ALEATORIO,
    FORECAST_HORIZON,
    HORIZONTE_COMPLETO,
    LAG_MONTHS,
    MODELOS,
    MODELOS_SUPERVISADOS,
    PERSISTENCIA,
    REGRESION_LINEAL,
)


def make_features(history: list[float], index: int, date: pd.Timestamp) -> np.ndarray:
    """Build features using only observations available before the target month."""
    return np.array(
        [
            history[index - 1],
            history[index - LAG_MONTHS],
            float(np.mean(history[index - 3 : index])),
            float(index),
            np.sin(2 * np.pi * date.month / 12),
            np.cos(2 * np.pi * date.month / 12),
        ],
        dtype=float,
    )


def make_model(model_name: str) -> Pipeline | RandomForestRegressor:
    """Modelo supervisado sin entrenar (semilla 42 en el bosque)."""
    if model_name == REGRESION_LINEAL:
        return make_pipeline(StandardScaler(), LinearRegression())
    if model_name == BOSQUE_ALEATORIO:
        return RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
    raise ModeloDesconocidoError(model_name)


def forecast_model(
    model_name: str,
    observed: list[float],
    dates: pd.DatetimeIndex,
    horizon: int = FORECAST_HORIZON,
) -> list[float]:
    """Entrena con toda la historia y pronostica `horizon` meses de forma recursiva."""
    if len(observed) <= LAG_MONTHS:
        raise SerieCortaError("Se necesitan más de 12 meses para entrenar los modelos.")

    model = make_model(model_name)
    features = np.array(
        [
            make_features(observed, index, cast(pd.Timestamp, dates[index]))
            for index in range(LAG_MONTHS, len(observed))
        ]
    )
    targets = np.asarray(observed[LAG_MONTHS:], dtype=float)
    model.fit(features, targets)

    history = list(observed)
    predictions = []
    for offset in range(horizon):
        index = len(observed) + offset
        future_date = cast(pd.Timestamp, dates[-1] + pd.offsets.MonthBegin(offset + 1))
        next_value = float(
            model.predict(make_features(history, index, future_date).reshape(1, -1))[0]
        )
        next_value = max(0.0, next_value)
        predictions.append(next_value)
        history.append(next_value)
    return predictions


def evaluate_models(totals: pd.Series) -> pd.DataFrame:
    """Evaluate rolling, non-overlapping three-month forecasts on the final year."""
    values = totals.to_numpy(dtype=float)
    dates = pd.DatetimeIndex(totals.index)
    records = []
    for origin in origenes_de_validacion(len(values)):
        actual = values[origin : origin + FORECAST_HORIZON]
        history = values[:origin].tolist()

        predictions_by_model = {
            PERSISTENCIA: pronostico_persistencia(history),
            **{
                name: forecast_model(name, history, dates[:origin]) for name in MODELOS_SUPERVISADOS
            },
        }
        for model_name in MODELOS:
            for lead, (prediction, observed) in enumerate(
                zip(predictions_by_model[model_name], actual, strict=True), start=1
            ):
                records.append(
                    {
                        "modelo": model_name,
                        "horizonte_meses": lead,
                        "error": float(prediction - observed),
                    }
                )

    errors = pd.DataFrame(records)
    summaries = []
    for model_name, model_errors in errors.groupby("modelo", sort=False):
        summaries.append(
            {
                "modelo": model_name,
                "horizonte": HORIZONTE_COMPLETO,
                "MAE_toneladas": model_errors["error"].abs().mean(),
                "RMSE_toneladas": np.sqrt(np.mean(model_errors["error"] ** 2)),
                "predicciones_evaluadas": len(model_errors),
            }
        )
        for lead, lead_errors in model_errors.groupby("horizonte_meses"):
            summaries.append(
                {
                    "modelo": model_name,
                    "horizonte": f"{lead} mes(es)",
                    "MAE_toneladas": lead_errors["error"].abs().mean(),
                    "RMSE_toneladas": np.sqrt(np.mean(lead_errors["error"] ** 2)),
                    "predicciones_evaluadas": len(lead_errors),
                }
            )
    return pd.DataFrame(summaries)


def create_forecasts(totals: pd.Series) -> pd.DataFrame:
    """Pronósticos de cada modelo para los 3 meses posteriores al último observado."""
    values = totals.to_numpy(dtype=float).tolist()
    dates = pd.DatetimeIndex(totals.index)
    future_dates = pd.date_range(
        dates[-1] + pd.offsets.MonthBegin(1), periods=FORECAST_HORIZON, freq="MS"
    )
    predictions = {PERSISTENCIA: pronostico_persistencia(values)}
    for model_name in MODELOS_SUPERVISADOS:
        predictions[model_name] = forecast_model(model_name, values, dates)

    return pd.DataFrame(
        [
            {
                "mes": month.strftime("%Y-%m"),
                "modelo": model_name,
                "pronostico_toneladas": round(value, 2),
            }
            for model_name, values_by_month in predictions.items()
            for month, value in zip(future_dates, values_by_month, strict=True)
        ]
    )
