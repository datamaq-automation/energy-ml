"""src/application/crecidas/clasificar_episodios.py — Clasificación de riesgo."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score

from src.application.crecidas.construir_dataset import DatasetCrecidas

UMBRAL_EPISODIO_M = 2.0
UMBRALES_PROBABILIDAD = (0.30, 0.50, 0.70)


@dataclass(frozen=True)
class ResultadoClasificacion:
    """Métricas del clasificador y de la referencia por persistencia."""

    horizonte_dias: int
    umbral_probabilidad: float
    casos_reales: int
    casos_predichos: int
    precision: float
    sensibilidad: float
    f1: float
    falsos_positivos: int
    episodios_reales: int
    episodios_detectados: int
    sensibilidad_episodios: float
    sensibilidad_persistencia: float


def _preparar_datos(
    dataset: DatasetCrecidas,
    fraccion_entrenamiento: float,
) -> tuple[int, list[list[float]], list[int], list[list[float]], list[int]]:
    """Prepara la separación temporal y excluye objetivos solapados."""
    if not 0 < fraccion_entrenamiento < 1:
        raise ValueError("La fracción debe estar entre 0 y 1.")

    corte = round(len(dataset.fechas) * fraccion_entrenamiento)
    if corte == 0 or corte >= len(dataset.fechas):
        raise ValueError("No hay suficientes datos para evaluar.")

    fecha_inicio = dataset.fechas[corte]
    indices = [
        i for i in range(corte)
        if dataset.fechas[i] + timedelta(days=dataset.horizonte_dias)
        < fecha_inicio
    ]

    if not indices:
        raise ValueError("No hay suficientes datos de entrenamiento.")

    variables_train = [dataset.variables[i] for i in indices]
    objetivos_train = [
        int(dataset.objetivos[i] >= UMBRAL_EPISODIO_M)
        for i in indices
    ]

    if len(set(objetivos_train)) < 2:
        raise ValueError("El entrenamiento necesita ejemplos de ambas clases.")

    variables_test = dataset.variables[corte:]
    objetivos_test = [
        int(valor >= UMBRAL_EPISODIO_M)
        for valor in dataset.objetivos[corte:]
    ]

    return corte, variables_train, objetivos_train, variables_test, objetivos_test


def _entrenar_clasificador(
    variables: list[list[float]],
    objetivos: list[int],
) -> RandomForestClassifier:
    """Entrena el Random Forest con parámetros reproducibles."""
    modelo = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    modelo.fit(variables, objetivos)
    return modelo

def _identificar_episodios(
    fechas: list[date],
    niveles_tigre: dict[date, float],
) -> list[date]:
    """Identifica las fechas de inicio de episodios de nivel elevado."""
    return [
        dia
        for dia in fechas
        if dia in niveles_tigre
        and dia - timedelta(days=1) in niveles_tigre
        and niveles_tigre[dia] >= UMBRAL_EPISODIO_M
        and niveles_tigre[dia - timedelta(days=1)] < UMBRAL_EPISODIO_M
    ]


def _calcular_resultado(
    umbral: float,
    probabilidades: np.ndarray[Any, Any],
    objetivos: list[int],
    fechas: list[date],
    inicios: list[date],
    persistencia: list[int],
    horizonte: int,
) -> ResultadoClasificacion:
    """Calcula las métricas para un umbral de probabilidad."""
    predicciones = [
        int(probabilidad >= umbral)
        for probabilidad in probabilidades
    ]

    predicciones_fecha = dict(zip(fechas, predicciones, strict=True))
    persistencia_fecha = dict(zip(fechas, persistencia, strict=True))

    detectados = sum(
        predicciones_fecha[dia] == 1 for dia in inicios
    )
    detectados_persistencia = sum(
        persistencia_fecha[dia] == 1 for dia in inicios
    )

    falsos = sum(
        real == 0 and predicho == 1
        for real, predicho in zip(objetivos, predicciones, strict=True)
    )

    return ResultadoClasificacion(
        horizonte_dias=horizonte,
        umbral_probabilidad=umbral,
        casos_reales=sum(objetivos),
        casos_predichos=sum(predicciones),
        precision=float(precision_score(
            objetivos, predicciones, zero_division=0
        )),
        sensibilidad=float(recall_score(
            objetivos, predicciones, zero_division=0
        )),
        f1=float(f1_score(
            objetivos, predicciones, zero_division=0
        )),
        falsos_positivos=falsos,
        episodios_reales=len(inicios),
        episodios_detectados=detectados,
        sensibilidad_episodios=(
            detectados / len(inicios) if inicios else 0.0
        ),
        sensibilidad_persistencia=(
            detectados_persistencia / len(inicios) if inicios else 0.0
        ),
    )


def clasificar_episodios(
    dataset: DatasetCrecidas,
    niveles_tigre: dict[date, float],
    fraccion_entrenamiento: float = 0.8,
) -> list[ResultadoClasificacion]:
    """Entrena y evalúa un clasificador con separación temporal purgada."""
    (
        corte,
        variables_train,
        objetivos_train,
        variables_test,
        objetivos_test,
    ) = _preparar_datos(dataset, fraccion_entrenamiento)

    modelo = _entrenar_clasificador(variables_train, objetivos_train)
    probabilidades = modelo.predict_proba(variables_test)[
        :, list(modelo.classes_).index(1)
    ]

    fechas_objetivo = [
        fecha + timedelta(days=dataset.horizonte_dias)
        for fecha in dataset.fechas[corte:]
    ]

    inicios = _identificar_episodios(fechas_objetivo, niveles_tigre)
    persistencia = [
        int(fila[0] >= UMBRAL_EPISODIO_M)
        for fila in variables_test
    ]

    return [
        _calcular_resultado(
            umbral,
            probabilidades,
            objetivos_test,
            fechas_objetivo,
            inicios,
            persistencia,
            dataset.horizonte_dias,
        )
        for umbral in UMBRALES_PROBABILIDAD
    ]
