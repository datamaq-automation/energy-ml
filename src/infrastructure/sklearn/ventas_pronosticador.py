"""src/infrastructure/sklearn/ventas_pronosticador.py — Tarea B: pistas, split temporal y tres métodos."""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from src.domain.ventas.modelos import Pronosticos


def agregar_pistas(ventas: pd.DataFrame) -> pd.DataFrame:
    """Pistas conocidas antes del día a pronosticar: venta de ayer, de hace 7 días, día y mes."""
    ventas = ventas.sort_values(["store", "item", "date"]).copy()
    por_serie = ventas.groupby(["store", "item"])["sales"]
    ventas["ayer"] = por_serie.shift(1)
    ventas["semana_pasada"] = por_serie.shift(7)
    ventas["dia"] = ventas["date"].dt.day_of_week
    ventas["mes"] = ventas["date"].dt.month
    return ventas


class SklearnPronosticadorVentas:
    """Implementa PronosticadorVentas: 'igual que ayer', regresión lineal y bosque aleatorio."""

    def __init__(self, arboles: int = 200) -> None:
        self._arboles = arboles

    def pronosticar(
        self, ventas: pd.DataFrame, pistas: tuple[str, ...], fecha_corte: str
    ) -> Pronosticos:
        """Aprende con las fechas anteriores al corte y pronostica las posteriores."""
        ventas = agregar_pistas(ventas)
        columnas = list(pistas)
        aprender = ventas[ventas["date"] < fecha_corte].dropna(subset=columnas)
        examen = ventas[ventas["date"] >= fecha_corte].dropna(subset=columnas)

        lineal = LinearRegression().fit(aprender[columnas], aprender["sales"])
        bosque = RandomForestRegressor(
            n_estimators=self._arboles, random_state=42, min_samples_leaf=50, n_jobs=-1
        ).fit(aprender[columnas], aprender["sales"])

        return Pronosticos(
            series=tuple(zip(examen["store"].astype(int), examen["item"].astype(int), strict=True)),
            fechas=tuple(examen["date"].dt.strftime("%Y-%m-%d")),
            reales=tuple(examen["sales"].astype(float)),
            por_metodo={
                "ayer": tuple(examen["ayer"].astype(float)),
                "lineal": tuple(float(v) for v in lineal.predict(examen[columnas])),
                "bosque": tuple(float(v) for v in bosque.predict(examen[columnas])),
            },
        )
