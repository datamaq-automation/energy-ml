"""src/infrastructure/sklearn/residuos_modelador.py — Implementa PronosticadorResiduos con pandas + sklearn."""

from __future__ import annotations

import pandas as pd

from src.domain.residuos.value_objects import MetricaValidacion, Pronostico, TotalMensual
from src.infrastructure.sklearn.residuos_pronostico import create_forecasts, evaluate_models


class PronosticadorResiduosSklearn:
    """Traduce las tablas de pandas a los value objects del dominio."""

    def serie_mensual(self, datos: pd.Series) -> list[TotalMensual]:
        """Un total por mes, con el mes en formato AAAA-MM."""
        return [
            TotalMensual(mes=fecha.strftime("%Y-%m"), toneladas=float(valor))
            for fecha, valor in zip(pd.DatetimeIndex(datos.index), datos.to_numpy(), strict=True)
        ]

    def validar(self, datos: pd.Series) -> list[MetricaValidacion]:
        """MAE y RMSE por modelo y horizonte en el último año."""
        return [
            MetricaValidacion(
                modelo=str(fila["modelo"]),
                horizonte=str(fila["horizonte"]),
                mae_toneladas=float(fila["MAE_toneladas"]),
                rmse_toneladas=float(fila["RMSE_toneladas"]),
                predicciones_evaluadas=int(fila["predicciones_evaluadas"]),
            )
            for fila in evaluate_models(datos).to_dict("records")
        ]

    def pronosticar(self, datos: pd.Series) -> list[Pronostico]:
        """Pronósticos de los 3 meses siguientes para cada modelo."""
        return [
            Pronostico(
                mes=str(fila["mes"]),
                modelo=str(fila["modelo"]),
                toneladas=float(fila["pronostico_toneladas"]),
            )
            for fila in create_forecasts(datos).to_dict("records")
        ]
