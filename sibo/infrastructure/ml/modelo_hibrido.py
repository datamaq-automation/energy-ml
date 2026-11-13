"""Modelo híbrido y explicable para estimar el pico de gases de una comida.

Combina un RandomForest entrenado con datos simulados (para capturar interacciones
no lineales entre nutrientes) con la heurística nutricional del dominio (para que
cada predicción sea explicable). La etiqueta simulada replica el conocimiento
nutricional del servicio `puntaje_heuristico`.
"""

from __future__ import annotations

import math

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from sibo.domain.entities import Alimento
from sibo.domain.servicios import factor_fodmap, factor_porcion, puntaje_heuristico

PESO_MODELO = 0.7
PESO_HEURISTICA = 0.3
MUESTRAS_ENTRENAMIENTO = 1500
RUIDO_ENTRENAMIENTO = 3.0


class ModeloGasesHibrido:
    """Predictor de pico de gases (0-100) para una comida concreta."""

    def __init__(self, semilla: int = 42) -> None:
        self._semilla = semilla
        self._modelo = self._entrenar()

    def predecir_pico(
        self,
        alimento: Alimento,
        porcion_g: float,
        hora: float,
        sintomas: float,
    ) -> float:
        caracteristicas = _caracteristicas(alimento, porcion_g, hora, sintomas)
        prediccion = float(self._modelo.predict([caracteristicas])[0])
        heuristica = puntaje_heuristico(alimento, porcion_g, hora, sintomas)
        combinado = PESO_MODELO * prediccion + PESO_HEURISTICA * heuristica
        return round(min(max(combinado, 0.0), 100.0), 1)

    def _entrenar(self) -> RandomForestRegressor:
        rng = np.random.default_rng(self._semilla)
        n = MUESTRAS_ENTRENAMIENTO
        fodmap = rng.choice([0.1, 0.5, 0.9], size=n)
        fibra = rng.uniform(0.0, 8.0, n)
        carbohidratos = rng.uniform(0.0, 40.0, n)
        inflamatorio = rng.uniform(0.0, 10.0, n)
        desinflamatorio = rng.uniform(0.0, 10.0, n)
        porcion = rng.uniform(0.4, 3.0, n)
        hora = rng.uniform(0.0, 23.99, n)
        sintomas = rng.uniform(0.0, 10.0, n)

        radianes = hora / 24.0 * 2.0 * math.pi
        caracteristicas = np.column_stack(
            [
                fodmap,
                fibra,
                carbohidratos,
                inflamatorio,
                desinflamatorio,
                porcion,
                np.sin(radianes),
                np.cos(radianes),
                sintomas / 10.0,
            ]
        )
        objetivo = _verdad_simulada(
            fodmap, fibra, carbohidratos, inflamatorio, desinflamatorio, porcion, hora, sintomas
        )
        objetivo = np.clip(objetivo + rng.normal(0.0, RUIDO_ENTRENAMIENTO, n), 0.0, 100.0)

        modelo = RandomForestRegressor(
            n_estimators=120,
            max_depth=9,
            min_samples_leaf=3,
            random_state=self._semilla,
        )
        modelo.fit(caracteristicas, objetivo)
        return modelo


def _caracteristicas(
    alimento: Alimento,
    porcion_g: float,
    hora: float,
    sintomas: float,
) -> list[float]:
    radianes = hora / 24.0 * 2.0 * math.pi
    return [
        factor_fodmap(alimento.fodmap),
        alimento.fibra_g * porcion_g / 100.0,
        alimento.carbohidratos_g * porcion_g / 100.0,
        alimento.score_inflamatorio,
        alimento.score_desinflamatorio,
        factor_porcion(alimento, porcion_g),
        math.sin(radianes),
        math.cos(radianes),
        min(max(sintomas, 0.0), 10.0) / 10.0,
    ]


def _verdad_simulada(
    fodmap: np.ndarray,
    fibra: np.ndarray,
    carbohidratos: np.ndarray,
    inflamatorio: np.ndarray,
    desinflamatorio: np.ndarray,
    porcion: np.ndarray,
    hora: np.ndarray,
    sintomas: np.ndarray,
) -> np.ndarray:
    hora_normalizada = (hora - 12.0) / 12.0
    return (
        8.0
        + 34.0 * fodmap
        + 16.0 * np.minimum(fibra / 6.0, 1.0)
        + 14.0 * np.minimum(carbohidratos / 30.0, 1.0)
        + 22.0 * inflamatorio / 10.0
        - 12.0 * desinflamatorio / 10.0
        + 10.0 * np.minimum((porcion - 1.0) / 2.0, 1.0)
        + 8.0 * np.minimum(sintomas / 10.0, 1.0)
        + 6.0 * hora_normalizada**2
    )
