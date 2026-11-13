"""Aggregate Ann Arbor waste records and compare three-month forecasts."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "solid_waste.csv"
DEFAULT_OUTPUT = ROOT / "resultados"
REQUIRED_COLUMNS = {"MaterialCategory", "CalendarYear", "Month", "NetTN_Month"}
LAG_MONTHS = 12
VALIDATION_MONTHS = 12
FORECAST_HORIZON = 3


def load_monthly_totals(csv_path: Path) -> pd.Series:
    """Validate the source rows and return one citywide total per month."""
    data = pd.read_csv(csv_path)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing_columns)}")
    if data[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Hay valores vacíos en las columnas necesarias para el análisis.")

    data["CalendarYear"] = pd.to_numeric(data["CalendarYear"], errors="raise").astype(int)
    data["Month"] = pd.to_numeric(data["Month"], errors="raise").astype(int)
    data["NetTN_Month"] = pd.to_numeric(data["NetTN_Month"], errors="raise")
    if not data["Month"].between(1, 12).all():
        raise ValueError("La columna Month contiene valores fuera del rango 1–12.")
    if (data["NetTN_Month"] < 0).any():
        raise ValueError("La columna NetTN_Month contiene valores negativos.")

    category_month = ["MaterialCategory", "CalendarYear", "Month"]
    if data.duplicated(category_month).any():
        raise ValueError("Hay más de un registro por categoría y mes.")

    data["date"] = pd.to_datetime({"year": data["CalendarYear"], "month": data["Month"], "day": 1})
    categories = set(data["MaterialCategory"].unique())
    categories_per_month = data.groupby("date")["MaterialCategory"].agg(set)
    if not categories_per_month.map(lambda month_categories: month_categories == categories).all():
        raise ValueError("Las categorías de residuos no están completas en todos los meses.")

    totals = data.groupby("date")["NetTN_Month"].sum().sort_index()
    expected_dates = pd.date_range(totals.index.min(), totals.index.max(), freq="MS")
    if not totals.index.equals(expected_dates):
        raise ValueError("La serie mensual tiene meses faltantes o fechas duplicadas.")
    totals.name = "toneladas"
    return totals


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


def make_model(model_name: str):
    if model_name == "Regresión lineal":
        return make_pipeline(StandardScaler(), LinearRegression())
    if model_name == "Bosque aleatorio":
        return RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
    raise ValueError(f"Modelo desconocido: {model_name}")


def forecast_model(
    model_name: str,
    observed: list[float],
    dates: pd.DatetimeIndex,
    horizon: int = FORECAST_HORIZON,
) -> list[float]:
    if len(observed) <= LAG_MONTHS:
        raise ValueError("Se necesitan más de 12 meses para entrenar los modelos.")

    model = make_model(model_name)
    features = np.array(
        [make_features(observed, index, dates[index]) for index in range(LAG_MONTHS, len(observed))]
    )
    targets = np.asarray(observed[LAG_MONTHS:], dtype=float)
    model.fit(features, targets)

    history = list(observed)
    predictions = []
    for offset in range(horizon):
        index = len(observed) + offset
        future_date = dates[-1] + pd.offsets.MonthBegin(offset + 1)
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
    first_origin = len(values) - VALIDATION_MONTHS
    if first_origin <= LAG_MONTHS:
        raise ValueError("La serie es demasiado corta para la validación temporal solicitada.")

    model_names = ["Persistencia", "Regresión lineal", "Bosque aleatorio"]
    records = []
    for origin in range(first_origin, len(values), FORECAST_HORIZON):
        actual = values[origin : origin + FORECAST_HORIZON]
        if len(actual) != FORECAST_HORIZON:
            raise ValueError("El período de validación no contiene bloques completos de 3 meses.")
        history = values[:origin].tolist()
        if origin == 0:
            raise ValueError("No hay datos de entrenamiento para la validación.")

        predictions_by_model = {
            "Persistencia": [history[-1]] * FORECAST_HORIZON,
            "Regresión lineal": forecast_model("Regresión lineal", history, dates[:origin]),
            "Bosque aleatorio": forecast_model("Bosque aleatorio", history, dates[:origin]),
        }
        for model_name in model_names:
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
                "horizonte": "completo",
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
    values = totals.to_numpy(dtype=float).tolist()
    dates = pd.DatetimeIndex(totals.index)
    future_dates = pd.date_range(
        dates[-1] + pd.offsets.MonthBegin(1), periods=FORECAST_HORIZON, freq="MS"
    )
    predictions = {"Persistencia": [values[-1]] * FORECAST_HORIZON}
    for model_name in ("Regresión lineal", "Bosque aleatorio"):
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_DATA, help="Ruta al CSV original.")
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Directorio de resultados."
    )
    args = parser.parse_args()

    totals = load_monthly_totals(args.csv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    monthly = totals.rename_axis("mes").reset_index()
    monthly["mes"] = monthly["mes"].dt.strftime("%Y-%m")
    monthly.to_csv(args.output_dir / "serie_mensual_ciudad.csv", index=False)

    metrics = evaluate_models(totals)
    metrics.to_csv(args.output_dir / "metricas_validacion.csv", index=False)
    forecasts = create_forecasts(totals)
    forecasts.to_csv(args.output_dir / "pronostico_3_meses.csv", index=False)

    print(
        f"Serie: {len(totals)} meses, de {totals.index.min():%Y-%m} a {totals.index.max():%Y-%m}."
    )
    print(f"Validación temporal (últimos {VALIDATION_MONTHS} meses):")
    print(metrics[metrics["horizonte"] == "completo"].to_string(index=False))
    print("Pronósticos posteriores al último mes disponible:")
    print(forecasts.pivot(index="mes", columns="modelo", values="pronostico_toneladas").to_string())
    print(f"Resultados guardados en: {args.output_dir}")


if __name__ == "__main__":
    main()
