"""src/domain/residuos/value_objects.py — Vocabulario y resultados inmutables del pronóstico de residuos."""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_COLUMNS = frozenset({"MaterialCategory", "CalendarYear", "Month", "NetTN_Month"})
LAG_MONTHS = 12
VALIDATION_MONTHS = 12
FORECAST_HORIZON = 3

PERSISTENCIA = "Persistencia"
REGRESION_LINEAL = "Regresión lineal"
BOSQUE_ALEATORIO = "Bosque aleatorio"
MODELOS = (PERSISTENCIA, REGRESION_LINEAL, BOSQUE_ALEATORIO)
MODELOS_SUPERVISADOS = (REGRESION_LINEAL, BOSQUE_ALEATORIO)
HORIZONTE_COMPLETO = "completo"


@dataclass(frozen=True)
class TotalMensual:
    """Suma de todas las categorías de residuos de la ciudad en un mes (`mes` = AAAA-MM)."""

    mes: str
    toneladas: float


@dataclass(frozen=True)
class MetricaValidacion:
    """Error de un modelo en la validación temporal, para un horizonte o para el bloque completo."""

    modelo: str
    horizonte: str
    mae_toneladas: float
    rmse_toneladas: float
    predicciones_evaluadas: int


@dataclass(frozen=True)
class Pronostico:
    """Toneladas pronosticadas por un modelo para un mes posterior al último observado."""

    mes: str
    modelo: str
    toneladas: float
