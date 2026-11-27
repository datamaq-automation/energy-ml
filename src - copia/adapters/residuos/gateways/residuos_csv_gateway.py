"""src/adapters/residuos/gateways/residuos_csv_gateway.py — Registros de Ann Arbor (Monthly Solid Waste Totals).

Implementa el puerto RepositorioResiduos: valida el CSV de la ciudad, lo
reduce a un total por mes y guarda los resultados como CSV.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd

from src.domain.residuos.exceptions import DatosInvalidosError
from src.domain.residuos.value_objects import (
    REQUIRED_COLUMNS,
    MetricaValidacion,
    Pronostico,
    TotalMensual,
)

DEFAULT_DATA = Path("datos/residuos/solid_waste.csv")
DEFAULT_OUTPUT = Path("datos/residuos/resultados")


def _numerica(datos: pd.DataFrame, columna: str) -> pd.Series:
    """pd.to_numeric con errors="raise": falla ante cualquier valor no numérico."""
    return cast(pd.Series, pd.to_numeric(cast(pd.Series, datos[columna]), errors="raise"))


def load_monthly_totals(csv_path: Path) -> pd.Series:
    """Validate the source rows and return one citywide total per month."""
    data = pd.read_csv(csv_path)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise DatosInvalidosError(f"Faltan columnas requeridas: {sorted(missing_columns)}")
    if data[list(REQUIRED_COLUMNS)].isna().to_numpy().any():
        raise DatosInvalidosError("Hay valores vacíos en las columnas necesarias para el análisis.")

    data["CalendarYear"] = _numerica(data, "CalendarYear").astype(int)
    data["Month"] = _numerica(data, "Month").astype(int)
    data["NetTN_Month"] = _numerica(data, "NetTN_Month")
    if not data["Month"].between(1, 12).all():
        raise DatosInvalidosError("La columna Month contiene valores fuera del rango 1–12.")
    if (data["NetTN_Month"] < 0).to_numpy().any():
        raise DatosInvalidosError("La columna NetTN_Month contiene valores negativos.")

    category_month = ["MaterialCategory", "CalendarYear", "Month"]
    if data.duplicated(category_month).any():
        raise DatosInvalidosError("Hay más de un registro por categoría y mes.")

    data["date"] = pd.to_datetime(
        pd.DataFrame({"year": data["CalendarYear"], "month": data["Month"], "day": 1})
    )
    categories = set(data["MaterialCategory"].unique())
    categories_per_month = data.groupby("date")["MaterialCategory"].agg(set)
    completas = categories_per_month.map(lambda month_categories: month_categories == categories)
    if not completas.to_numpy().all():
        raise DatosInvalidosError(
            "Las categorías de residuos no están completas en todos los meses."
        )

    totals = cast(pd.Series, data.groupby("date")["NetTN_Month"].sum()).sort_index()
    expected_dates = pd.date_range(totals.index.min(), totals.index.max(), freq="MS")
    if not totals.index.equals(expected_dates):
        raise DatosInvalidosError("La serie mensual tiene meses faltantes o fechas duplicadas.")
    totals.name = "toneladas"
    return totals


class ResiduosCsvGateway:
    """Lee `solid_waste.csv` y escribe los tres CSV de `resultados/`."""

    def __init__(self, csv_path: Path = DEFAULT_DATA, output_dir: Path = DEFAULT_OUTPUT) -> None:
        self._csv_path = csv_path
        self._output_dir = output_dir

    def cargar(self) -> pd.Series:
        """Total mensual de la ciudad, validado."""
        return load_monthly_totals(self._csv_path)

    def guardar(
        self,
        serie: list[TotalMensual],
        metricas: list[MetricaValidacion],
        pronosticos: list[Pronostico],
    ) -> list[str]:
        """Escribe serie_mensual_ciudad, metricas_validacion y pronostico_3_meses."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        tablas = {
            "serie_mensual_ciudad.csv": pd.DataFrame(
                {"mes": [t.mes for t in serie], "toneladas": [t.toneladas for t in serie]}
            ),
            "metricas_validacion.csv": pd.DataFrame(
                {
                    "modelo": [m.modelo for m in metricas],
                    "horizonte": [m.horizonte for m in metricas],
                    "MAE_toneladas": [m.mae_toneladas for m in metricas],
                    "RMSE_toneladas": [m.rmse_toneladas for m in metricas],
                    "predicciones_evaluadas": [m.predicciones_evaluadas for m in metricas],
                }
            ),
            "pronostico_3_meses.csv": pd.DataFrame(
                {
                    "mes": [p.mes for p in pronosticos],
                    "modelo": [p.modelo for p in pronosticos],
                    "pronostico_toneladas": [p.toneladas for p in pronosticos],
                }
            ),
        }
        rutas: list[str] = []
        for nombre, tabla in tablas.items():
            ruta = self._output_dir / nombre
            tabla.to_csv(ruta, index=False)
            rutas.append(str(ruta))
        return rutas
