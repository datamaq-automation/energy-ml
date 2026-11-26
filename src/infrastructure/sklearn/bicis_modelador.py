"""src/infrastructure/sklearn/bicis_modelador.py — Evaluación con Random Forest y línea base."""

from __future__ import annotations

from collections.abc import Sequence
from math import sqrt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.domain.bicis.exceptions import MuestrasInsuficientesError
from src.domain.bicis.value_objects import (
    MetricasPronostico,
    MuestraPronostico,
    ResultadoEvaluacionPronosticos,
)


class BosqueAleatorioPronosticos:
    """Implementa el puerto de evaluación usando solo scikit-learn en infraestructura."""

    def evaluar(self, muestras: Sequence[MuestraPronostico]) -> ResultadoEvaluacionPronosticos:
        """Ajusta con 2024 y evalúa cada día de 2025 contra la referencia semanal."""
        entrenamiento = sorted(
            (muestra for muestra in muestras if muestra.fecha_objetivo.year == 2024),
            key=lambda muestra: muestra.fecha_objetivo,
        )
        prueba = sorted(
            (muestra for muestra in muestras if muestra.fecha_objetivo.year == 2025),
            key=lambda muestra: muestra.fecha_objetivo,
        )
        if not entrenamiento or not prueba:
            raise MuestrasInsuficientesError(
                "La evaluación requiere muestras utilizables tanto de 2024 como de 2025."
            )
        if max(m.fecha_objetivo for m in entrenamiento) >= min(m.fecha_objetivo for m in prueba):
            raise MuestrasInsuficientesError(
                "El período de prueba debe ser posterior al período de entrenamiento."
            )

        modelo = RandomForestRegressor(
            n_estimators=300, min_samples_leaf=5, random_state=42, n_jobs=1
        )
        modelo.fit(_variables(entrenamiento), [m.viajes_reales for m in entrenamiento])
        reales = [m.viajes_reales for m in prueba]
        predicciones_modelo = modelo.predict(_variables(prueba))
        predicciones_base = [m.variables.viajes_semana_anterior for m in prueba]
        return ResultadoEvaluacionPronosticos(
            linea_base=_metricas("Mismo día de la semana anterior", reales, predicciones_base),
            bosque_aleatorio=_metricas("Random Forest", reales, predicciones_modelo),
            dias_entrenamiento=len(entrenamiento),
            dias_prueba=len(prueba),
        )


def evaluar_2024_2025(
    muestras: Sequence[MuestraPronostico],
) -> ResultadoEvaluacionPronosticos:
    """Función directa para evaluaciones y pruebas unitarias."""
    return BosqueAleatorioPronosticos().evaluar(muestras)


def _variables(muestras: Sequence[MuestraPronostico]) -> list[list[int]]:
    return [
        [
            muestra.variables.dia_semana,
            muestra.variables.mes,
            muestra.variables.viajes_dia_anterior,
            muestra.variables.viajes_semana_anterior,
        ]
        for muestra in muestras
    ]


def _metricas(nombre: str, reales: list[int], predicciones: Sequence[float]) -> MetricasPronostico:
    return MetricasPronostico(
        nombre=nombre,
        mae=float(mean_absolute_error(reales, predicciones)),
        rmse=sqrt(float(mean_squared_error(reales, predicciones))),
    )
